# HackathonGemis

Funcionalidades:
- El usuario ingresa su caso en lenguaje natural y: 
    - Resumen de la situación en términos legales, debe de ser mostrado en streming
    - Norma o normativas aplicables, citadas de forma identificable, con un hipervínculo para ir a leer la norma en cuestión
    - Recomendaciones o pasos a seguir
    - Un aviso visible de que la herramienta no es un abogado como tal
- El usuario puede pedir generar un derecho de petición o tutela:
    - Puede descargar el documento después de aceptarlo
    - Puede editarlo antes de descargarlo
- Se va a alimentar de un RAG propio
- Arranque con docker, con client, server, BD

## Server

Ver [server/README.md](server/README.md) para arquitectura, puesta en marcha
e ingesta del RAG (Postgres/pgvector sobre la Constitución + memoria de
casos en MongoDB).