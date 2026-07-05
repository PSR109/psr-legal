# Sim Setups — Auditoría y plan de lanzamiento/monetización

> Preparado por el Agente Creador de Apps (2026-07-05), adelantando trabajo a pedido
> del dueño. Fuente: repo público `PSR109/patagonia-sim-setups` (rama `main`).

## Auditoría

- **Qué es**: generador educativo de setups de autos para simuladores. El usuario
  elige juego, auto, pista y condiciones (o describe el problema de manejo) y recibe
  un setup con la explicación de cada ajuste. Login gratis con favoritos, notas y
  registro de tiempos. Bilingüe (español por defecto, inglés opcional).
- **Stack**: Next.js 16 + React 19 + TypeScript + Tailwind v4; Prisma 6 con SQLite;
  auth propia (bcrypt + JWT en cookies httpOnly). Datos de setups como módulos TS.
- **Estado**: funcional y **ya desplegada** en https://patagonia-sim-setups.vercel.app
  (rama `main`, 47 commits). ACC completamente implementado como plantilla de
  referencia; 5 simuladores mapeados.

### ⚠️ Riesgo técnico crítico: SQLite en Vercel

El filesystem de Vercel es efímero: la base SQLite (cuentas, favoritos, notas,
tiempos) **se borra en cada deploy y no se comparte entre instancias**. Hoy cualquier
usuario que se registre perderá su cuenta. **Arreglarlo antes de captar usuarios** —
migrar a una BD gestionada con capa gratuita real; opciones en orden de menor
fricción con Prisma: Turso (libSQL, casi drop-in para SQLite), Neon (Postgres) o
Supabase (Postgres — misma plataforma que ya usa Panoramas: una cuenta menos que
administrar). Es la primera tarea de ingeniería del agente cuando tenga acceso al
repo.

## 🔑 Atajo de monetización descubierto: patagoniasimracing.cl

El dueño **ya posee el dominio `patagoniasimracing.cl`** (su email corporativo vive
ahí). AdSense no acepta `*.vercel.app` ni `*.workers.dev`, pero **sí acepta
subdominios de un dominio propio**. Entonces, sin comprar nada:

- `setups.patagoniasimracing.cl` → CNAME al proyecto de Vercel (Sim Setups)
- `panoramas.patagoniasimracing.cl` → dominio custom del Worker de Cloudflare
  (Panoramas)

Esto **elimina el costo y la espera del dominio nuevo** para empezar con AdSense en
AMBAS apps. Un dominio propio dedicado (ej. para Panoramas) sigue siendo mejor a
largo plazo para SEO y venta del activo, pero puede esperar a que haya tracción.

### Pasos del humano (~15 min, gratis)

1. En el panel DNS de `patagoniasimracing.cl` (Cloudflare o xHost): crear
   `setups` como CNAME → `cname.vercel-dns.com`, y en Vercel → proyecto
   `patagonia-sim-setups` → Settings → Domains → agregar
   `setups.patagoniasimracing.cl`.
2. En Cloudflare → Workers → proyecto `panoramas` → Custom Domains → agregar
   `panoramas.patagoniasimracing.cl` (si el DNS del dominio está en Cloudflare, es
   un clic).
3. Crear la cuenta de AdSense en https://adsense.google.com y agregar
   `patagoniasimracing.cl` como sitio (cubre los subdominios).
4. Avisar al agente: él integra los bloques de anuncios en ambas apps.

## Plan de monetización

**Etapa 1 — Ads (tras los pasos de arriba).** Bloques bajo el setup generado y en la
lista de setups. Nicho global: RPM de sim racing en EN es varias veces el de tráfico
CL genérico.

**Etapa 2 — Freemium "PSR Pro"** (cuando haya usuarios recurrentes, vía Stripe):
- Gratis: generador completo, 5 favoritos, notas básicas.
- Pro (~USD 3–5/mes): favoritos/notas ilimitados, historial de tiempos con gráficos,
  comparador de setups, y análisis de telemetría (sinergia con `psr-analyzer-pro`).
- Referencia de mercado que valida el precio: onRails, GO Setups, Track Titan y
  simracingsetup.com cobran suscripciones/setups en este mismo nicho.

**Etapa 3 — Crecimiento.** El SEO es la palanca: páginas por juego/auto/pista
("ACC Monza setup", "iRacing GT3 setup Spa") tienen volumen de búsqueda global
enorme y encajan con la estructura de datos TS que ya tiene la app.

## Mejoras de producto priorizadas (las hace el agente con acceso al repo)

1. Migrar SQLite → BD gestionada (bloqueante de todo lo demás).
2. **Inglés por defecto** (hoy es español): el mercado y el RPM están en inglés;
   ES queda como opción. Ajustar metadatos SEO por idioma.
3. Páginas SEO estáticas por juego/auto/pista con el setup base y explicación.
4. Slots de AdSense listos (comentados hasta que la cuenta esté aprobada).
5. Promoción cruzada en el footer (Panoramas + hub PSR) y distribución vía el
   pipeline de redes del dueño (PSR Pipeline: Instagram/TikTok/Threads).

## Acción de acceso pendiente

Igual que con Panoramas: agregar `PSR109/patagonia-sim-setups` como fuente del
entorno de Claude Code (o aprobar `add_repo`) para que el agente pueda hacer commits.
Y permitir `*.vercel.app` + `*.workers.dev` en la política de red del entorno para
verificar los sitios en vivo.
