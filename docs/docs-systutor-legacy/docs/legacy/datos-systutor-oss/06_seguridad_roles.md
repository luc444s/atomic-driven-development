# 06 — Seguridad, Roles y Menú Dinámico

## 1. Esquema de Autenticación

### 1.1 Flujo de Login (OSS)

1. POST /api/v1/auth/login {username, password}
2. Validar contra tabla personas (login = Login_Persona)
3. Verificar password: en legacy MD5, en OSS usar bcrypt
4. Generar JWT con:
   - sub: persona.id
   - username: persona.login
   - rol: nivel de permiso (Administrador, Ventas, etc.)
   - almacenes: lista de almacenes asignados
5. Retornar {access_token, token_type, expires_in}

### 1.2 Migración de Passwords

⚠️ Legacy usa MD5 (inseguro). Estrategia:
1. En migración, convertir hash MD5 → indicar "requires_reset"
2. En primer login exitoso, forzar cambio de password
3. Almacenar con bcrypt: hash = bcrypt.hashpw(password, bcrypt.gensalt())

## 2. Roles y Permisos

### 2.1 Roles Legacy

La tabla Permiso tiene 5 roles fijos con acceso por opción (1=lectura, 2=escritura):
- Administrador: acceso total a todas las opciones (valor 2 en casi todo)
- Contabilidad: módulos financieros, reportes contables
- Almacén: inventario, productos, movimientos de almacén
- Sistemas: configuraciones técnicas
- Ventas: clientes, facturación, cobranza

### 2.2 En OSS

Tabla roles:
- id, nombre, descripcion, created_at

Tabla permisos:
- id, rol_id, modulo, recurso, accion (CREATE, READ, UPDATE, DELETE)

Tabla usuarios_roles:
- usuario_id, rol_id

El seed debe incluir los 5 roles legacy más cualquier rol nuevo.

## 3. Menú Dinámico

### 3.1 Estructura Legacy

3 niveles: Menu → SubMenu → SUBMENU1 (con formulario asociado)

Menús de primer nivel:
1. CONFIGURACION → MAESTROS, REPORTES
2. ALMACEN → MOVIMIENTOS, REPORTES, ESTADISTICAS
3. VENTAS → MOVIMIENTOS, REPORTES
4. FINANZAS → (no tiene submenús en los datos)
5. OPERACIONES → REPARTO, REPORTES OPERATIVOS, PLANIFICACION, RECEPCION, SERVICIOS

### 3.2 Endpoint de Menú

GET /api/v1/auth/menu → retorna estructura jerárquica filtrada por rol del usuario autenticado

```json
[
  {
    "id": 1,
    "nombre": "CONFIGURACION",
    "orden": 1,
    "submenus": [
      {
        "id": 1,
        "nombre": "MAESTROS",
        "orden": 1,
        "items": [
          {"id": 1, "nombre": "REGISTRAR EMPRESA", "formulario": "FrmRazonSocial"},
          {"id": 2, "nombre": "REGISTRAR SUCURSAL", "formulario": "FrmRegSUCURSAL"},
          {"id": 5, "nombre": "REGISTRAR USUARIO", "formulario": "FrmRegPersonal"},
          ...
        ]
      }
    ]
  }
]
```

## 4. Protección de Endpoints

```python
from functools import wraps

def require_permission(modulo: str, accion: str):
    async def dependency(current_user: Usuario = Depends(get_current_user)):
        if not current_user.tiene_permiso(modulo, accion):
            raise HTTPException(403, "Permiso denegado")
        return current_user
    return dependency

# Uso:
@router.get("/productos")
async def listar_productos(
    current_user: Usuario = Depends(require_permission("productos", "READ"))
):
    ...
```

## 5. Almacenes por Usuario

Tabla Usuario_Almacen (nueva en OSS) para asignar qué almacenes puede ver/operar cada usuario.

Endpoint: GET /api/v1/auth/almacenes → lista de almacenes asignados
