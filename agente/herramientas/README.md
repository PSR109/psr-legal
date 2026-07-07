# Herramientas propias del Agente Creador de Apps

Regla: si haces algo manual dos veces, la tercera es un script aquí. Toda herramienta
nueva se registra en esta tabla con una línea de uso.

| Herramienta | Uso | Qué hace |
|---|---|---|
| `verificar-sitios.sh` | `bash agente/herramientas/verificar-sitios.sh` | Chequea el estado HTTP, latencia y título de todos los sitios del portafolio (`sitios.txt`). Distingue caída real de bloqueo por la política de red del entorno |
| `sitios.txt` | (config de la anterior) | Un sitio por línea: `nombre URL`. Agregar aquí cada app que se publique |

> ⚠️ **Ejecutar `verificar-sitios.sh` al inicio de CADA ciclo, sin asumir el resultado del
> ciclo anterior.** La política de red del entorno puede cambiar entre sesiones sin aviso:
> el 2026-07-05/06 `*.workers.dev` y `*.vercel.app` estaban bloqueados; el 2026-07-07 el
> mismo script los mostró accesibles (200 OK) mientras `api.cloudflare.com`/`api.vercel.com`
> seguían bloqueados. Volver a probar evita dar por perdida una capacidad que ya volvió.

## Ideas de herramientas futuras (crear cuando se necesiten 2 veces)

- `seo-check.sh`: title/description/canonical/sitemap de una URL dada.
- `reporte-ciclo.sh`: esqueleto del reporte diario desde `ESTADO.md`.
- `posicion-keyword.sh`: posición aproximada de una URL para una keyword (vía
  búsqueda web del agente, no scraping de Google).
