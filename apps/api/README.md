# apps/api

Backend principal de SYSTUTOR OSS.

## Alcance inicial

Esta primera version del core incluye:

- configuracion central;
- aplicacion `FastAPI`;
- kernel minimo;
- plugin registry;
- health endpoints;
- base para auditoria, eventos, tenancy y permisos;
- outbox y dispatcher interno de eventos.

## Arranque esperado

```bash
uvicorn apps.api.app.main:app --reload
```

Worker base:

```bash
dramatiq apps.api.app.kernel.events.tasks
```

Dispatcher local de prueba:

```bash
python3 -c "from apps.api.app.kernel.events.tasks import dispatch_pending_events; print(dispatch_pending_events.fn())"
```

## Regla importante

No meter logica de negocio de modulos en el kernel.
