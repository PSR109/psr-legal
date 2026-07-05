# Panoramas — Plan de lanzamiento y monetización

> Preparado por el Agente Creador de Apps (2026-07-05), adelantando el ciclo 1.
> Fuente: auditoría del repo público `PSR109/APP_Panoramas`
> (rama `claude/vacation-activity-finder-pcogyh`), su `docs/DEPLOY.md`, `package.json`
> y workflows.

## Resultado de la auditoría

La app está **lista para publicarse**. Tiene guía de despliegue propia
(`docs/DEPLOY.md`), workflow `deploy-pages.yml`, build Vite con prerender, checks
automáticos de SEO/PWA/accesibilidad/rendimiento, pipeline de precios con cron, y
todo corre en capa gratuita (Cloudflare Pages + Supabase free + OpenRouteService
~2.000 rutas/día). Lo único que falta son los pasos que requieren cuentas humanas.

## Pasos del humano (una sola vez, ~30–40 min en total)

Seguir el orden. Todo es gratis.

### 1. Cloudflare Pages (~10 min) — publica el frontend
1. Crear cuenta gratis en https://dash.cloudflare.com (si no existe).
2. Workers & Pages → Create → Pages → **Connect to Git** → autorizar GitHub y elegir
   `PSR109/APP_Panoramas`.
3. Rama de producción: `claude/vacation-activity-finder-pcogyh` (o la que sea la
   principal en ese momento).
4. Configuración de build: Framework **Vite** · Build command `npm run build` ·
   Output directory `dist`.
5. Deploy. Anotar la URL resultante (`https://<proyecto>.pages.dev`) y **pasársela al
   agente** (responder el reporte o dejarla en este archivo).

### 2. Supabase (~15 min) — backend (auth, viajes guardados)
1. Crear proyecto gratis en https://supabase.com — región **São Paulo** (mejor
   latencia para Chile).
2. SQL Editor → ejecutar en orden `supabase/migrations/0001_init.sql` y
   `0002_catalog.sql` (copiar/pegar desde el repo).
3. Copiar **Project URL** y **anon public key** → en Cloudflare Pages → Settings →
   Environment variables: `VITE_SUPABASE_URL` y `VITE_SUPABASE_ANON_KEY` → redeploy.
4. La **service role key** NUNCA va en Cloudflare: solo como secret de GitHub (paso 4).

### 3. OpenRouteService (~5 min) — rutas exactas
1. Registrarse gratis en https://openrouteservice.org → obtener API token.
2. Agregarlo en Cloudflare Pages como `VITE_ORS_API_KEY` → redeploy.

### 4. Secrets de GitHub (~5 min) — pipeline automático de precios
En `APP_Panoramas` → Settings → Secrets and variables → Actions:
- Secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `CNE_API_TOKEN`
  (token gratis en https://api.cne.cl para precios de bencina).
- Variable: `PIPELINE_ENABLED = true`.

### 5. (Opcional, después) Dominio propio
Un dominio propio (ej. `panoramas.cl` o similar, ~USD 10/año) mejora SEO y confianza,
y AdSense lo prefiere. Se conecta como CNAME al proyecto de Pages. **Es el único paso
con costo y puede esperar** hasta que la app demuestre tracción.

## Plan de monetización (lo ejecuta el agente cuando haya URL pública)

**Etapa 1 — Gratis con publicidad (base).**
Crear cuenta de Google AdSense (humano, gratis, ~15 min) **después** de que la app
esté publicada — AdSense exige un sitio vivo con contenido para aprobar. Ubicaciones
de bajo impacto: bajo los resultados de búsqueda y en la vista de detalle de cada
panorama. Nunca sobre el mapa.

**Etapa 2 — Freemium (cuando haya usuarios recurrentes).**
- Gratis: búsqueda completa, costos reales, 3 viajes guardados.
- **Panoramas Pro** (~CLP 2.000–3.000/mes vía Stripe Payment Link): viajes guardados
  ilimitados, alertas de precios de bencina y tráfico, sin publicidad.
- Requiere cuenta Stripe (humano) — pedirla solo cuando la Etapa 1 muestre tráfico.

**Etapa 3 — Crecimiento/adquisición.**
Con tracción sostenida (>5.000 usuarios/mes), el activo es doble: la audiencia y el
dataset chileno de costos de viaje (peajes, bencina, atracciones actualizados por
pipeline). Compradores naturales: portales de turismo, automotoras/TAG, medios.
El agente preparará el dossier con métricas cuando corresponda.

**Sinergias inmediatas tras el lanzamiento** (las hace el agente): apps satélite
(calculadora de peajes, costo de viaje) que capturan búsquedas y enlazan a Panoramas;
páginas SEO "qué hacer en [ciudad]"; promoción cruzada en el footer de todas las apps.

## Qué hará el agente apenas reciba la URL pública

1. Verificar que el sitio carga, el PWA instala y el SEO on-page está bien.
2. Registrar la URL en el portafolio y fijar el criterio de éxito a 30 días.
3. Pedir (acción humana) la cuenta de AdSense con instrucciones exactas.
4. Empezar la distribución gratuita: textos listos para directorios y comunidades.
