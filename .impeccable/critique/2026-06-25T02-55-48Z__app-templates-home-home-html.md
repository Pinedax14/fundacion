---
target: app/templates/home/home.html
total_score: 27
p0_count: 0
p1_count: 2
p2_count: 3
timestamp: 2026-06-25T02-55-48Z
slug: app-templates-home-home-html
---
## Design Health Score

| # | Heurística | Puntuación | Hallazgo clave |
|---|---|---|---|
| 1 | Visibilidad del sistema | 3/4 | Nav active state claro, flash messages presentes |
| 2 | Match sistema/mundo real | 4/4 | Lenguaje cálido y accesible, CTAs claros |
| 3 | Control y libertad | 3/4 | Navegación siempre visible, sin estados atrapados |
| 4 | Consistencia y estándares | 3/4 | Mucho mejor post-fixes; botones pill coherentes |
| 5 | Prevención de errores | 2/4 | Galería no indica disponibilidad de mascotas |
| 6 | Reconocimiento vs. recuerdo | 3/4 | CTAs prominentes; gallery sin indicador de estado |
| 7 | Flexibilidad y eficiencia | 2/4 | Sin atajos de teclado ni búsqueda rápida desde home |
| 8 | Diseño estético y minimalista | 3/4 | Mucho más limpio post-fixes |
| 9 | Recuperación de errores | 2/4 | Flash messages para auth; sin guía post-adopción-fallida |
| 10 | Ayuda y documentación | 2/4 | Sin explicación del proceso de adopción |
| **Total** | | **27/40** | **Aceptable** |

## Anti-Patterns Verdict
Detector retornó limpio []. LLM assessment: mejorado significativamente. La paleta dark+purple/orange puede leerse como "dark SaaS" en lugar de fundación con carácter. La emoción de marca está en el copy, no en la composición visual.

## Priority Issues

**[P1] Proceso de adopción invisible** — primer visitante no sabe qué pasa al registrarse. Fix: sección de 3 pasos antes del CTA final.

**[P1] Galería sin indicador de disponibilidad** — mascotas en galería pueden estar adoptadas. Fix: filtrar por estado o añadir badge.

**[P2] CTAs del hero fuera del thumb-zone en mobile** — botones en zona alta inaccesible a una mano.

**[P2] Feature section informa pero no convence** — afirmaciones sin evidencia específica.

**[P2] Sin prueba social con cara** — número de adopciones anónimo, sin foto real ni testimonio.

## Persona Red Flags

**Jordan (Primera vez):** Abandona en registro por falta de contexto del proceso. Alta ansiedad pre-registro.

**Riley (Stress Tester):** Callejón sin salida en perfil de mascota adoptada — sin sugerencias de mascotas similares.

**Casey (Móvil):** CTAs del hero fuera de thumb-zone en pantallas grandes.
