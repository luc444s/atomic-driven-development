# Anotacion

## Ubicacion en crear envase

En el legacy, `ubicacion` en crear envase servia para registrar la ubicacion fisica del cilindro dentro del almacen.

Evidencia documental:

- `docs/docs-systutor-legacy/docs/legacy/forms/FrmCatBombonas_mapeo_dropdowns.md`
  - el combo `C` se cargaba con `mostrar_ubicacion_almacen`
  - venia de `CUbicacion`
  - su proposito era seleccionar la ubicacion fisica del cilindro en el almacen
- `docs/database/modulo_productos/12_clases_vb_adicionales.md`
  - confirma que `CUbicacion` en `FrmCatBombonas` se usaba para ubicacion fisica de cilindros
- `docs/docs-systutor-legacy/docs/legacy/datos-systutor-oss/05_flujos_criticos.md`
  - despues de `RECEPCIONADO -> EN_ALMACEN_VACIO` aparece “Registrar ubicacion fisica”

## Conclusion arquitectonica

No se considera parte esencial de `logistics envase` en el estado actual.

Motivos:

- si `ubicacion` significa posicion fisica interna dentro del almacen, se parece mas a `stock` o a un submodulo de layout/warehouse operations;
- `logistics envase` deberia concentrarse en identidad del envase, estado del cilindro, trazabilidad, producto/gas, marca/condicion, ADR tecnico cuando aplique, movimientos y custodia;
- `ubicacion en almacen` no cambia la identidad del envase;
- `ubicacion en almacen` no cambia su estado logistico principal;
- `ubicacion en almacen` no es critica para crear el envase;
- normalmente depende de una estructura mas detallada de almacen: zona, rack, fila, columna o posicion fisica.

## Decision practica

- para `crear envase`: no meter `ubicacion`;
- para una fase futura: solo evaluarlo si existe un subflujo real de ubicacion fisica en almacen;
- si se implementa luego, modelarlo como capacidad de almacen o inventario, no como dato maestro del envase.
- al crear un envase, el estado inicial si depende de la eleccion operativa de `lleno` o `vacio` en ese almacen.

## Resumen

- en el legacy existia;
- no es obligatorio arrastrarlo al core actual de `logistics envase`;
- lo correcto hoy es tratarlo como una capacidad futura de almacen, no como parte base del alta de envase.
- en cambio, al alta del envase si corresponde definir si entra como `lleno` o `vacio` en ese almacen, porque eso afecta su estado logistico inicial.

## Alta de envase

Al crear un envase, los datos que si deben entrar en el flujo base son:

- categoria;
- linea;
- sublinea;
- capacidad;
- contenido;
- a quien pertenece.

Regla operativa:

- al seleccionar gas o producto en crear envases, deben llenarse automaticamente los datos relacionados para acelerar el guardado;
- entre esos datos autocompletados entran rubro, linea, sublinea, contenido, capacidad, grupo y campos similares derivados del producto;
- la descripcion debe crearse automaticamente;
- la descripcion no debe ser escrita manualmente por un usuario;
- el objetivo es reducir captura manual y guardar la informacion de manera mas rapida y consistente.

## Criterio de UX

- el usuario no debe reconstruir manualmente la ficha del envase si el producto ya contiene esos metadatos;
- el producto seleccionado debe actuar como fuente de defaults para completar la mayor parte del formulario;
- el formulario debe priorizar velocidad de registro y consistencia sobre edicion libre de texto.

## Registro de bombonas y movimiento asociado

En el registro de bombonas, al mismo tiempo se debe generar el movimiento del envase.

Reglas:

- si el envase se crea como `vacio`, el ingreso se considera desde cliente;
- si el envase se crea como `lleno` en almacen, el movimiento se considera desde proveedor;
- el alta del envase no es solo creacion de ficha, tambien debe dejar trazado el movimiento inicial correspondiente;
- ademas de generar un movimiento `lleno` o `vacio`, cada movimiento debe tener un numero relacionado;
- ese numero relacionado debe guardar el documento de origen del movimiento.

Ejemplos:

- si se estan creando envases recien comprados, se debe colocar el numero de documento de la compra;
- si se estan registrando envases vacios que ingresan desde cliente, se debe colocar el numero del documento del movimiento por el cual ingreso desde el cliente.

## Implicacion funcional

- el alta de envase debe capturar o derivar el contexto documental del movimiento inicial;
- no basta con persistir el cilindro, tambien debe quedar clara la procedencia operativa del ingreso;
- la relacion entre estado inicial del envase y tipo de origen del movimiento forma parte de la trazabilidad base.

## Ownership segun condicion del envase

Segun la condicion del envase, tambien se debe registrar quien es el dueno operativo del cilindro.

Reglas:

- si la condicion corresponde a cilindro propio, el envase debe quedar registrado como propio;
- si el envase pertenece a un cliente, se debe registrar el nombre del cliente;
- si el envase pertenece a un proveedor, se debe registrar el nombre del proveedor;
- esta informacion forma parte del alta del envase y no debe quedar ambigua.

## Observacion del envase

`observacion` existe como una caracteristica aparte y debe tratarse por separado del flujo base.

Lectura funcional actual:

- `observacion` se entiende como un resumen o una especie de partida de nacimiento del envase;
- no esta cerrada todavia su implementacion exacta;
- queda marcada como punto en duda y no debe mezclarse automaticamente con la descripcion ni con los campos base del alta hasta que se defina mejor.

## Sobre `gas_group_id`

`gas_group_id` hoy no representa un grupo del catalogo nuevo.

Lectura correcta actual:

- `gas_group_id` apunta a `lg_gas_products.id`;
- `lg_gas_products` es un catalogo transitorio de productos gas dentro de `logistics`;
- por lo tanto, `gas_group_id` hoy funciona mas como referencia al producto gas del envase que como un grupo real;
- no esta relacionado con `prod_groups` del plugin `productos`.

Conclusion:

- el nombre `gas_group_id` es engañoso;
- no debe interpretarse como grupo del catalogo maestro;
- arquitectonicamente, el destino correcto futuro es `prod_products`, no `prod_groups`.

## Cierre quirurgico pendiente

Necesitamos terminar de manera quirurgica el flujo de envases.

Alcance final anotado:

- cerrar `envases`;
- incluir el kardex de gas;
- automatizar el llenado de linea, sublinea, grupo y campos relacionados;
- no abrir mas alcance fuera de eso.

## Logica del submodulo de envases

El submodulo de `envases` no es solo una ficha. Representa la entidad del cilindro dentro de `logistics` y su vida operativa.

Capas actuales del submodulo:

- ficha del envase;
- estado actual del cilindro;
- trazabilidad de estados;
- PH / hydrotest;
- garantias;
- retimbrados;
- ownership / custodia;
- impresion de etiquetas;
- servicios;
- escaneo operativo.

Logica base actual:

- se crea un cilindro en `lg_cylinders`;
- se le asigna un estado inicial;
- se registra inmediatamente una traza en `lg_cylinder_state_log`;
- luego el envase puede cambiar de estado segun transiciones permitidas;
- sobre ese envase se registran eventos y datos complementarios como PH, retimbrado, ownership, etiquetas y servicios.

## Lectura funcional correcta del alta de envase

El usuario no deberia llenar una ficha grande manualmente.

El flujo esperado es:

- elegir el producto o gas base;
- dejar que el sistema autocompleta linea, sublinea, grupo, contenido, capacidad y similares;
- generar automaticamente la descripcion;
- no pedir `ubicacion` fisica en el alta base;
- definir si el envase entra como `lleno` o `vacio`;
- definir ownership;
- generar el movimiento inicial con su documento relacionado.

## Paso a paso de uso para una persona

1. entrar al modulo de `Envases`;
2. pulsar `Nuevo envase`;
3. elegir el gas o producto base;
4. el sistema autocompleta rubro, linea, sublinea, grupo, capacidad, contenido, descripcion y datos derivados del producto;
5. completar solo lo minimo no derivado:
   - serie o matricula si corresponde;
   - a quien pertenece;
   - condicion del envase;
   - si entra como lleno o vacio;
   - documento relacionado del ingreso;
6. definir el origen operativo del alta:
   - si entra vacio, el ingreso viene desde cliente;
   - si entra lleno en almacen, viene desde proveedor;
7. guardar;
8. el sistema debe hacer dos cosas juntas:
   - crear la ficha del envase;
   - generar el movimiento inicial del envase; 
9. una vez creado, el usuario puede seguir operando el envase.

## Operacion del envase despues del alta

Despues del alta, el usuario debe poder:

- ver estado actual;
- ver transiciones permitidas;
- cambiar de estado;
- consultar historial;
- registrar PH;
- registrar garantia;
- registrar retimbrado;
- registrar servicios;
- imprimir etiqueta;
- revisar ownership o custodia;
- usar escaneo en operaciones reales.

## Resumen operativo

La logica del submodulo es:

- crear envase;
- trazar su estado inicial;
- registrar su movimiento de origen;
- operar luego todo su ciclo de vida logistico.




















Anotacion MILTON

LO QUE SE VA AMEJORAR
1.-  INTERFAZ RAPIDA PARA CREAR ENVASES, SE LIMITARA A SERIAL, y de fallback elegira la matricula, se usara un combo box
se llamara en automatico los datos de pruductos, ya esta predefinidos los nombres, ademas de 
retimbrado tendra infuencia directa en el peso de la bombona, esto afecta a jornadas de manera directa,
preparar sobre grab2 relacionados a cilindros
optimizar vistas

en carta porte se mostrara la denoominacion de mercancia EJEMPLO UN 1072 OXIGENO COMPRIMIDO, Que quedara predefinido, cargamos los gases con la capacidad real y la presion real


A futuro, control de gases liquido, que es produccion




