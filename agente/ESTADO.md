# Estado del Agente Creador de Apps

> Memoria persistente del agente. Cada sesión la lee al empezar y la actualiza al
> terminar. Mantener conciso: este archivo se lee completo en cada ciclo.

**Última actualización**: 2026-07-05 (creación del agente — aún no corre ningún ciclo)

**Directiva del dueño (2026-07-05)**: mejorar el sistema constantemente, buscar la
mayor rentabilidad posible, aprovechar sinergias entre apps y optimizar procesos y
recursos. Incorporada al manual como Fase 6.5 (kaizen), sección "Rentabilidad" y
sección "Sinergias del portafolio".

## Siguiente acción

Ciclo 1 — el dueño incorporó su app existente **Panoramas** al portafolio (directiva:
"aprovecha lo que ya hay"). Por la regla de rentabilidad (escalar lo que ya existe
gana a construir de cero), el ciclo 1 se dedica a Panoramas, más la auditoría de
cuentas de la Fase 1:

1. **Auditar Panoramas**: revisar el repo `PSR109/APP_Panoramas` (público — si no está
   como fuente del entorno, leerlo vía web/raw.githubusercontent.com). Confirmado el
   2026-07-05: la app **no está publicada en internet** — el dueño la corre localmente
   en su PC, pero el código está al día en GitHub (commits del mismo día en la rama
   `claude/vacation-activity-finder-pcogyh`). Determinar qué falta para desplegarla
   según `docs/DEPLOY.md` (Cloudflare Pages + Supabase) y si sus servicios caben en
   capa gratuita.
1b. **Preparar el despliegue de Panoramas**: dejar todo listo para publicarla
   (configuración, build, workflow) y reducir la parte humana al mínimo — idealmente
   solo "conectar la cuenta de Cloudflare Pages al repo" con instrucciones exactas
   paso a paso. Publicarla es la acción de mayor retorno del portafolio: sin URL
   pública no hay tráfico ni ingresos posibles.
2. **Plan de monetización de Panoramas**: gratis con ads como base; evaluar freemium
   (ej. viajes guardados ilimitados, alertas de precios/tráfico como plan pago).
   Dejar el plan escrito en esta sección del estado.
3. **Auditoría de cuentas (Fase 1)**: AdSense / Stripe / Google Play.
4. Si queda tiempo: aplicar sinergias inmediatas a Panoramas (legales desde la
   plantilla, SEO on-page, footer de promoción cruzada).

## Portafolio

| App | Repo | URL | Modelo | Estado | Criterio de éxito | Métrica actual |
|---|---|---|---|---|---|---|
| **Panoramas** (insignia) | [PSR109/APP_Panoramas](https://github.com/PSR109/APP_Panoramas) | sin publicar (corre local en el PC del dueño; código al día en GitHub) | Ads + freemium (por definir en ciclo 1) | Heredada del dueño — en desarrollo avanzado, pendiente de despliegue | Definir en ciclo 1 tras auditoría | — |

### Notas de Panoramas (auditoría preliminar, 2026-07-05)

- Buscador de panoramas/actividades vacacionales en Chile: filtra por categoría
  (naturaleza, playas, ski, termas, gastronomía), distancia y presupuesto, y calcula
  el **costo real** del viaje: bencina, peajes (con alternativas sin peaje), entradas
  y predicción de tráfico. Bilingüe ES/EN.
- Stack: React + Vite + TypeScript + Tailwind, Leaflet/OpenStreetMap, Supabase
  (Postgres, Auth, RLS), OpenRouteService (capa gratis), Cloudflare Pages; incluye
  pipeline de actualización de precios con cron de GitHub Actions.
- Rama por defecto: `claude/vacation-activity-finder-pcogyh` (ojo: no es `main`).
- **Sinergia clave detectada**: sus datos y librerías (peajes, bencina, rutas) dan
  para apps satélite baratas — ver "Ideas en cartera".

## Cuentas de monetización

| Cuenta | Estado | Nota |
|---|---|---|
| Google AdSense | ❓ desconocido | Auditar en ciclo 1 |
| Stripe | ❓ desconocido | Auditar en ciclo 1 |
| Google Play Developer | ❓ desconocido | No necesaria mientras el portafolio sea solo web |

## Acciones pendientes del humano

| # | Acción | Por qué | Estado |
|---|---|---|---|
| 1 | Dar acceso del agente al repo `APP_Panoramas`: en la configuración del entorno de Claude Code, agregar `PSR109/APP_Panoramas` como fuente (o aprobar el diálogo de `add_repo` cuando el agente lo pida) | Sin esto el agente solo puede leer el repo por la web, no puede hacer commits ni deploys de Panoramas | ⏳ pendiente |
| 2 | Cuando el agente deje listo el despliegue de Panoramas: crear/conectar la cuenta gratuita de Cloudflare Pages al repo siguiendo las instrucciones que el agente entregará | La app hoy solo corre en el PC del dueño; publicarla es prerequisito de cualquier ingreso | ⏳ pendiente |

## Ideas en cartera (sinergias con Panoramas)

Apps satélite baratas que reutilizan los datos/librerías de Panoramas y le devuelven
tráfico con enlaces cruzados — candidatas para cuando Panoramas esté lanzada:

- **Calculadora de peajes Chile**: ruta A→B con costo de peajes/TAG. Keyword con
  búsqueda recurrente, construible como PWA estática con los datos de `data/tolls`.
- **Calculadora de costo de viaje en auto** (bencina + peajes): reutiliza `lib/fuel` y
  `lib/tolls`. Nicho de búsqueda amplio ("cuánto cuesta ir de X a Y").
- **¿Qué hacer este fin de semana en [ciudad]?**: páginas SEO estáticas por ciudad
  generadas desde los datos de atracciones, apuntando a Panoramas para el detalle.

## Mejoras del sistema

| Fecha | Mejora | Justificación |
|---|---|---|
| 2026-07-05 | Fase 6.5 (kaizen), reglas de rentabilidad y sinergias agregadas al manual; plantilla base `agente/plantillas/pwa-base/` creada | Directiva del dueño: mejora continua, máxima rentabilidad, sinergias y optimización de recursos |

## Ideas evaluadas

_(vacío)_

## Lecciones aprendidas

_(vacío)_

## Historial de ciclos

_(vacío — el ciclo 1 corre con la primera ejecución de la rutina diaria)_
