# Changelog 2026-07-22 - Retiro de contratos por bombona y nueva spec corta

## Qué se implementó

Se retiró del runtime visible el enfoque de contratos desde la ficha de `Envases` y se formalizó una spec corta nueva para contrato por derecho/cupo.

## Cambio de criterio

- el contrato no vive dentro de cada bombona;
- el contrato representa derecho/cupo por cliente y tipo de envase;
- los seriales concretos son variables y viven en posesión/custodia operativa.

## Runtime retirado

- CTA de contrato dentro de la ficha del envase.

## Runtime mantenido

- el módulo `Contratos` sigue existiendo como módulo funcional independiente dentro de `logistics`;
- el retiro aplica solo a su exposición directa desde `Envases`.

## Documentación

- nueva spec vigente: `0023AD.3-contrato-por-derecho-cupo.md`
- `0023AD` y `0023AO` quedan con nota explícita de vigencia parcial/histórica.
