# Revisión de contratos entre servicios — diseño

Bugs que no se ven revisando un servicio solo: lo que uno envía no es lo que el otro espera.

Contexto: #[[file:docs/wiki/_shared/architecture.md]]

Para cada frontera, comparar el que llama (cliente HTTP, productor, tipo del front) contra el que responde (ruta, schema, consumer): campos, opcionales, `null`, unidades, errores y timeouts.
