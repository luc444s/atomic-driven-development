🔥 ESCENARIOS INFERNALES (nivel producción real)
💀 1. Entrega parcial + recojo + cambio en la misma parada
Realidad
Cliente pide 10
Se entregan 6
Devuelve 4 vacíos
Pide cambio de 2 más
Tu arquitectura debe permitir:
VehicleSession
→ multiple operations en una misma parada
→ issue (entrega)
→ receive (recojo)
→ issue (extra)
Riesgo
❌ mezclar orden lógico
❌ doble conteo
❌ estados inconsistentes
💀 2. El repartidor pierde cilindros (literalmente)
Realidad
Sale con 50
Regresa con 47
No sabe dónde quedaron 3
Tu arquitectura:
conciliación
→ diferencia → lost
Riesgo
❌ sistema permite cerrar sin diferencia
❌ stock queda incorrecto
💀 3. Cliente devuelve más de lo que recibió
Realidad
Sistema dice: entregaste 10
Cliente devuelve 12
Tu arquitectura:
IC > SC
→ raw_assigned negativo
→ clamp a 0
→ alerta
Riesgo
❌ sistema acepta sin control
❌ inventario fantasma
💀 4. Carga inicial incompleta
Realidad
Se planificó cargar 100
Solo había stock para 70
Tu arquitectura:
transfer (FIXED → MOBILE)
→ falla parcial o total
Riesgo
❌ se crea carga sin stock real
❌ doble inventario (otra vez el error viejo)
💀 5. Repartidor modifica carga EN RUTA
Realidad
En mitad del día:
“agrega 5 más al camión”
Tu arquitectura:
VehicleSession sigue abierta
→ transfer adicional permitido
Riesgo
❌ rompes lifecycle
❌ duplicas operaciones
💀 6. Cliente no está
Realidad
Se llega al cliente
No hay nadie
No se entrega
Tu arquitectura:
NO debe generar movement
NO debe afectar stock
Riesgo
❌ generar SC fantasma
💀 7. Cilindro roto / dañado
Realidad
Se rompe un cilindro en ruta
Tu arquitectura:
issue / adjustment especial
→ fuera de flujo normal
Riesgo
❌ no hay forma de sacarlo del sistema
💀 8. Retorno incompleto al almacén
Realidad
Regresa el vehículo
Pero no descarga todo
Tu arquitectura:
MOBILE → FIXED transfer incompleto
Riesgo
❌ sesión se cierra con stock en vehículo
💀 9. Dos operadores usando el mismo vehículo
Realidad
Turno mañana y tarde
Mismo vehículo
Tu arquitectura:
VehicleSession única activa
Riesgo
❌ dos sesiones abiertas
❌ colisión de stock
💀 10. Error humano: registran doble entrega
Realidad
El operador hace SC dos veces
Tu arquitectura:
movements duplicados
→ assigned inflado
Riesgo
❌ no hay control de duplicados
💀 11. Intercambio directo (swap)
Realidad
Cliente da 5 vacíos
Recibe 5 llenos
Tu arquitectura:
receive + issue en misma operación
Riesgo
❌ orden incorrecto
❌ balance inconsistente
💀 12. Cliente con contrato vencido pero con cilindros
Realidad
Contrato terminó
Pero tiene 20 cilindros
Tu arquitectura:
contract = 0
assigned > 0
Riesgo
❌ sistema no lo detecta
💀 13. Cambio de vehículo en mitad de jornada
Realidad
Se malogra el camión
Se pasa la carga a otro
Tu arquitectura:
transfer MOBILE → MOBILE
o cerrar sesión + abrir otra
Riesgo
❌ no modelado → hack
💀 14. Movimiento sin registrar (el clásico)
Realidad
El repartidor entregó… pero nunca lo registró
Tu arquitectura:
assigned bajo
at_customer alto
→ inconsistencia
Riesgo
❌ sistema no detecta desviación
💀 15. Conciliación con diferencias múltiples
Realidad
faltan 2
sobran 3
hay 1 roto
Tu arquitectura:
reconciliation debe soportar:
- faltantes
- sobrantes
- ajustes
Riesgo
❌ conciliación simplista
🧠 TEST FINAL (el más importante)

Tu arquitectura es válida si:

puedes ejecutar TODOS estos escenarios SIN:
- hacks
- bypass de stock
- estados inconsistentes
