# psr-legal

Este repositorio cumple dos funciones:

1. **Documentos legales de PSR Pipeline** (`index.html`, `privacy-policy.html`,
   `terms-of-service.html`), servidos como sitio estático.
2. **Base del Agente Creador de Apps**, un agente autónomo que idea, construye,
   publica y monetiza web apps (freemium o gratis con publicidad):
   - `AGENTE-CREADOR-DE-APPS.md` — manual de operación del agente.
   - `agente/ESTADO.md` — memoria persistente entre ciclos (portafolio, métricas,
     acciones pendientes).
   - `.claude/agents/agente-creador-de-apps.md` — definición del agente para
     invocarlo bajo demanda desde Claude Code.

El agente corre además con una rutina diaria automática que ejecuta un ciclo de
trabajo y reporta el resultado.
