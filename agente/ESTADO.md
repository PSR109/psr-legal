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
   como fuente del entorno, leerlo vía web/raw.githubusercontent.com). Determinar:
   ¿está desplegada y en qué URL? (el dueño dice que está publicada; buscar la URL en
   `docs/DEPLOY.md`, workflows de deploy, o preguntar en el reporte), ¿qué falta para
   considerarla lanzada?, ¿los servicios que usa (Supabase, OpenRouteService,
   Cloudflare Pages) están dentro de capa gratuita?
2. **Plan de monetización de Panoramas**: gratis con ads como base; evaluar freemium
   (ej. viajes guardados ilimitados, alertas de precios/tráfico como plan pago).
   Dejar el plan escrito en esta sección del estado.
3. **Auditoría de cuentas (Fase 1)**: AdSense / Stripe / Google Play.
4. Si queda tiempo: aplicar sinergias inmediatas a Panoramas (legales desde la
   plantilla, SEO on-page, footer de promoción cruzada).

## Portafolio

| App | Repo | URL | Modelo | Estado | Criterio de éxito | Métrica actual |
|---|---|---|---|---|---|---|
| **Panoramas** (insignia) | [PSR109/APP_Panoramas](https://github.com/PSR109/APP_Panoramas) | por confirmar (dueño indica que está publicada) | Ads + freemium (por definir en ciclo 1) | Heredada del dueño — en desarrollo avanzado | Definir en ciclo 1 tras auditoría | — |

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
| 2 | Confirmar la URL pública donde está desplegada Panoramas (responder al reporte del agente con la URL) | El agente no la encontró; la necesita para SEO, ads y medición | ⏳ pendiente |

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
