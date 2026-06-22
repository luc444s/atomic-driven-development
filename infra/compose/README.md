# infra/compose

Documentacion complementaria del entorno local y de despliegue liviano.

En este proyecto, Termux es el entorno local primario.

Por eso, `docker-compose.yml` no es el flujo principal de desarrollo diario dentro de Termux.

Uso recomendado de esta carpeta:

- soporte secundario para entornos fuera de Termux;
- levantamiento auxiliar de PostgreSQL y Redis cuando aplique;
- referencia de infraestructura reproducible para CI, staging o maquinas de apoyo.
