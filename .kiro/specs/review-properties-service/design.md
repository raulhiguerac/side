# Revisión de properties-service — diseño

Dominios `listing` (CRUD del dueño, imágenes con URLs prefirmadas, visibilidad), `search` (feed con cursor opaco y ads, mapa con H3 en dos resoluciones) y `admin` (listado, moderación, promociones, precio estimado, import bulk async con worker). Depende de catalog (geo al escribir) y de users (resolver dueños en el bulk).

Contexto: #[[file:docs/wiki/properties-service/properties-service.md]]

Orden: primero el bulk y las escrituras que tocan cache y verificación (corrompen datos o muestran lo que no se debe), después el feed, al final las lecturas admin.
