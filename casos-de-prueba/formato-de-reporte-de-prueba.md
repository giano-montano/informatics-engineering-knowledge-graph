# Formato de reporte de prueba manual

## Propósito

Da una forma común a los reportes de las pruebas que se ejecutan a mano, para
que cada uno diga lo mismo en el mismo orden y se pueda comparar con los demás.

## Ejemplo (borrador)

```markdown
# Reporte CP-15 · Enlace con CS2023

**Fecha:** AAAA-MM-DD · **Evaluador:** … · **Grafo:** corrida de medición del AAAA-MM-DD
**Guía aplicada:** guia-de-evaluacion-de-relaciones.md, versión …

## Alcance

Qué se juzgó: cuántas aristas, cómo se obtuvieron (consulta o muestra con su semilla).

## Juicios

| # | Arista | Juicio | Motivo |
|---|---|---|---|
| 1 | (Tema «Árboles B») -[:PART_OF]-> (KU «…») | correcta | |
| 2 | … | incorrecta | … |

## Resumen

| Juicio | Cantidad | % |
|---|---|---|
| Correcta | | |
| Aceptable | | |
| Incorrecta | | |

## Observaciones

Patrones en los errores, casos dudosos y cómo se resolvieron.
```
