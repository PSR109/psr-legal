#!/usr/bin/env bash
# Verifica los sitios del portafolio listados en sitios.txt.
# Salida por sitio: OK (HTTP 2xx/3xx + título), CAIDO (error HTTP del sitio),
# o BLOQUEADO_POR_RED (la política de red del entorno impide llegar — no es culpa
# del sitio; ver acción humana #3 en agente/ESTADO.md).
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
fallas=0

while read -r nombre url; do
    [ -z "${nombre:-}" ] && continue
    case "$nombre" in \#*) continue ;; esac

    salida=$(curl -sS -A "$UA" -L --max-time 20 -o /tmp/vs_body.$$ -w "%{http_code} %{time_total}" "$url" 2>&1)
    rc=$?
    if [ $rc -ne 0 ]; then
        if echo "$salida" | grep -qi "CONNECT tunnel failed\|response 403"; then
            echo "🔒 $nombre BLOQUEADO_POR_RED $url (abrir política de red del entorno)"
        else
            echo "❌ $nombre CAIDO $url ($salida)"
            fallas=$((fallas+1))
        fi
        continue
    fi

    codigo=$(echo "$salida" | awk '{print $1}')
    tiempo=$(echo "$salida" | awk '{print $2}')
    titulo=$(grep -oiE '<title[^>]*>[^<]*' /tmp/vs_body.$$ 2>/dev/null | head -1 | sed -E 's/<title[^>]*>//I')
    case "$codigo" in
        2*|3*) echo "✅ $nombre OK $codigo ${tiempo}s \"${titulo:-sin título}\" $url" ;;
        *)     echo "❌ $nombre CAIDO HTTP $codigo $url"; fallas=$((fallas+1)) ;;
    esac
done < "$DIR/sitios.txt"

rm -f /tmp/vs_body.$$ 2>/dev/null
exit $fallas
