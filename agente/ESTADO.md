# Estado del Agente Creador de Apps

> Memoria persistente del agente. Cada sesión la lee al empezar y la actualiza al
> terminar. Mantener conciso: este archivo se lee completo en cada ciclo.

**Última actualización**: 2026-07-05 (creación del agente — aún no corre ningún ciclo)

**Directiva del dueño (2026-07-05)**: mejorar el sistema constantemente, buscar la
mayor rentabilidad posible, aprovechar sinergias entre apps y optimizar procesos y
recursos. Incorporada al manual como Fase 6.5 (kaizen), sección "Rentabilidad" y
sección "Sinergias del portafolio".

## Siguiente acción

**Trabajo adelantado el 2026-07-05** (sesión fundadora, a pedido del dueño): la
auditoría de Panoramas y su plan de lanzamiento + monetización ya están hechos — ver
`agente/panoramas/LANZAMIENTO.md`. Conclusión: la app está lista para publicarse;
solo faltan los pasos humanos de cuentas (Cloudflare, Supabase, ORS), documentados
paso a paso en ese archivo.

Ciclo 1 (próxima rutina):

1. **Verificar si el dueño ya ejecutó los pasos de `agente/panoramas/LANZAMIENTO.md`**
   (¿existe URL pública? probar `https://*.pages.dev` mencionada en el estado o
   preguntar en el reporte). Si sí: ejecutar la sección "Qué hará el agente apenas
   reciba la URL pública" de ese archivo. Si no: reiterar amablemente en el reporte
   con el enlace al plan.
2. **Auditoría de cuentas (Fase 1)**: AdSense / Stripe / Google Play (sigue pendiente).
3. Mientras tanto, avanzar la sinergia de mayor retorno que no dependa del humano:
   construir la **Calculadora de peajes Chile** (ver "Ideas en cartera") con los datos
   públicos de `data/tolls` del repo de Panoramas — captura búsquedas desde ya y
   enlazará a Panoramas cuando esté publicada. Respetar el máximo de 1 repo nuevo
   por ciclo.

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
| 2 | **Publicar Panoramas**: seguir los pasos 1–4 de `agente/panoramas/LANZAMIENTO.md` (Cloudflare Pages + Supabase + OpenRouteService + secrets de GitHub, ~30–40 min, todo gratis) y pasarle al agente la URL resultante | La app está lista; publicarla es prerequisito de cualquier ingreso. Instrucciones exactas ya preparadas | ⏳ pendiente |

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
