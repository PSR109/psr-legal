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

1. **Panoramas está publicada**: https://panoramas.contacto-d1f.workers.dev/
   (confirmada por el dueño el 2026-07-05). ⚠️ La política de red de este entorno
   **bloquea `*.workers.dev`**, así que el agente no puede verificar ni monitorear el
   sitio desde aquí (ver acción humana #3). Hallazgo clave: **AdSense no acepta
   subdominios de plataformas** como `workers.dev`/`pages.dev` — para mostrar ads se
   necesita dominio propio (ver acción humana #4). Mientras tanto, avanzar lo que no
   depende del humano: SEO on-page de Panoramas (vía repo), textos de distribución
   listos para copiar/pegar, y la calculadora de peajes.
2. **Auditoría de cuentas (Fase 1)**: AdSense / Stripe / Google Play (sigue pendiente).
3. **Auditar `PSR109/patagonia-sim-setups`** como candidata a segunda app insignia
   (investigación 2026-07-05: nicho global con mercado pagado comprobado — ver "Ideas
   en cartera"). Determinar: estado del código, qué falta para publicarla, y plan de
   lanzamiento como el de Panoramas. También mirar `psr-analyzer-pro` de pasada.
4. **SEO de contenido dentro de Panoramas** (no apps aparte): páginas "termas cerca de
   [ciudad]", "panoramas con niños en [ciudad]", "qué hacer este fin de semana en
   [ciudad]" — capturan búsquedas y alimentan la app principal. Requiere acceso al
   repo (acción humana #1) o entregar el contenido listo en `agente/panoramas/`.

## Portafolio

| App | Repo | URL | Modelo | Estado | Criterio de éxito | Métrica actual |
|---|---|---|---|---|---|---|
| **Panoramas** (insignia) | [PSR109/APP_Panoramas](https://github.com/PSR109/APP_Panoramas) | **https://panoramas.contacto-d1f.workers.dev/** (✅ publicada 2026-07-05) | Ads (requiere dominio propio) + freemium | Publicada — pendiente verificación, dominio y monetización | 100 visitas orgánicas/semana a los 30 días del dominio propio | — |

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
| 2 | ~~Publicar Panoramas~~ | Hecho: https://panoramas.contacto-d1f.workers.dev/ | ✅ completada 2026-07-05 |
| 3 | Permitir que el agente vea el sitio: en claude.ai/code → configuración de este entorno → política de red, permitir `*.workers.dev` (o cambiar a política confiable/amplia) | El entorno bloquea `workers.dev`; sin esto el agente no puede verificar el sitio ni medir que siga vivo | ⏳ pendiente |
| 4 | **Dominio propio para Panoramas** (~USD 10/año, único costo del portafolio): comprarlo idealmente en Cloudflare Registrar (precio de costo) y conectarlo al proyecto en el panel de Cloudflare. Sugerencias: `panoramas.app`, `panoramaschile.cl`, `mipanorama.cl` — decide el dueño | **AdSense no acepta subdominios `workers.dev`/`pages.dev`**: sin dominio propio no hay publicidad posible. Además mejora SEO y confianza | ⏳ pendiente — desbloquea TODOS los ingresos por ads |
| 5 | Con el dominio activo: crear cuenta de Google AdSense en https://adsense.google.com con la cuenta Google del dueño, agregar el dominio como sitio y avisar al agente | El agente dejará entonces los bloques de anuncios integrados en la app | ⏳ bloqueada por #4 |

## Ideas en cartera

**Prioridad 1 — Sim Setups (segunda insignia, ya construida).** El dueño ya tiene
`PSR109/patagonia-sim-setups` ("app generadora y educativa de setups de autos para 7
simuladores", TypeScript) y `PSR109/psr-analyzer-pro`. Investigación 2026-07-05: el
nicho sim racing tiene **mercado pagado comprobado** (onRails/virtualracecarengineer,
GO Setups, Track Titan, simracingsetup.com venden setups y suscripciones) → freemium
validado, audiencia global en inglés (mejor RPM de ads que Chile), y sinergia directa
con la marca Patagonia SimRacing y su pipeline de contenido en redes (PSR Pipeline).
Costo de entrada ≈ 0 porque la app ya existe. Siguiente paso: auditoría (ciclo 1).

**Prioridad 2 — Contenido SEO dentro de Panoramas** (no apps aparte): páginas por
ciudad/categoría ("termas cerca de Santiago con precios", "panoramas con niños en
[ciudad]") generadas desde los datos de atracciones. Refuerzan la insignia en vez de
fragmentar el portafolio.

## Ideas evaluadas

| Idea | Veredicto | Motivo (2026-07-05) |
|---|---|---|
| Calculadora de peajes Chile (app aparte) | ❌ descartada | Nicho saturado: chilepeajes.cl, peajeschile.com, inforutas.cl, peajeruta.cl, todotag.cl, tagchile.com, TollGuru — sin ángulo diferenciador para una app nueva. Como *función/página de Panoramas* sigue siendo válida |
| Calculadora de costo de viaje en auto (app aparte) | ❌ descartada | Mismo nicho saturado (servidos.ar, tagchile.com, etc.). Es exactamente el corazón de Panoramas: reforzar ahí, no duplicar |
| Calculadora de sueldo líquido Chile | ❌ descartada | 10+ competidores idénticos (Buk, Talana, misueldo.cl, cuantogano.cl…) — imposible destacar sin inversión en SEO |

## Mejoras del sistema

| Fecha | Mejora | Justificación |
|---|---|---|
| 2026-07-05 | Fase 6.5 (kaizen), reglas de rentabilidad y sinergias agregadas al manual; plantilla base `agente/plantillas/pwa-base/` creada | Directiva del dueño: mejora continua, máxima rentabilidad, sinergias y optimización de recursos |

## Lecciones aprendidas

_(vacío)_

## Historial de ciclos

_(vacío — el ciclo 1 corre con la primera ejecución de la rutina diaria)_
