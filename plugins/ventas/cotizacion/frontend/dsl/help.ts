export const COTIZACION_HELP = `Comandos de cotización
======================

Sintaxis general
----------------
  cotizar cliente "<nombre>" <cantidad> "<producto>" [fecha] [hora] [vehiculo "<placa>"] [condicion <notas>]
  preview cotizar ...   # previsualiza sin guardar

Ejemplos
--------
  cotizar cliente "Bohdan" 400 "Bombona1" mañana 14h
  cotizar cliente "Gas del Norte" 500 "Tanque 10kg" hoy vehiculo "IHUI-329I4G"
  preview cotizar cliente "Bohdan" 400 "Bombona1" mañana 14h

Campos obligatorios
-------------------
  cliente    Nombre del cliente. Usá comillas si tiene espacios.
  cantidad   Número entero (ej: 400).
  producto   Nombre del producto. Usá comillas si tiene espacios.

Campos opcionales
-----------------
  fecha      hoy | mañana | pasado mañana | lunes ... domingo | YYYY-MM-DD
  hora       mañana (06:00) | tarde (14:00) | noche (20:00) | HH:MM | HHh
  vehiculo   Patente del vehículo, entre comillas.
  condicion  Notas libres de condiciones de entrega.

Comandos especiales de la terminal
----------------------------------
  cotizar --help        Muestra esta ayuda
  neofetch | sysinfo    Muestra información del sistema
  history               Muestra el historial de comandos
  clear                 Limpia la terminal

Autocompletado
--------------
  Escribí al menos 2 caracteres para buscar clientes, productos y vehículos.
  Los nombres con espacios se insertan automáticamente entre comillas.
`;

export function isHelpCommand(command: string): boolean {
  const trimmed = command.trim().toLowerCase();
  return trimmed === "cotizar --help" || trimmed === "preview cotizar --help";
}
