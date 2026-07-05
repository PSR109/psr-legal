# Plantilla base PWA del portafolio

Punto de partida obligatorio para toda app nueva del Agente Creador de Apps.
Copiar estos archivos al repo de la app y reemplazar todos los marcadores `{{...}}`.

| Archivo | Qué es |
|---|---|
| `index.html` | Página principal: SEO on-page, slots de AdSense comentados, registro del service worker, footer con promoción cruzada |
| `manifest.webmanifest` | Manifiesto PWA (nombre, colores, iconos) |
| `sw.js` | Service worker con caché offline básica (cache-first para estáticos) |
| `privacidad.html` | Política de privacidad genérica para apps estáticas con ads |
| `terminos.html` | Términos de servicio genéricos |

Marcadores a reemplazar: `{{APP_NOMBRE}}`, `{{APP_DESCRIPCION}}` (≤155 caracteres,
con la keyword principal), `{{APP_URL}}`, `{{KEYWORD_PRINCIPAL}}`, `{{FECHA}}`,
`{{ADSENSE_CLIENT}}` (descomentar los bloques de ads solo cuando exista la cuenta).

Además crear en el repo de la app: `sitemap.xml`, `robots.txt`, e iconos
`icon-192.png` / `icon-512.png` (pueden generarse como SVG→PNG simples).

**Regla de retro-porte**: cualquier mejora generalizable descubierta construyendo una
app (SEO, UI, rendimiento, service worker) se aplica también aquí en el mismo ciclo.
