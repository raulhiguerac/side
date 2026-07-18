---
title: Impresiones, feed personalizado y estrategia de supply
captured-from: conversation
captured-on: 2026-05-31
participants: [raul, claude]
---

## Context
Discusión de producto durante el desarrollo del feed view — qué falta para que el feed sea un diferenciador real y cómo conseguir supply inicial de listings.

## Key conclusions

### Arquitectura de impresiones y personalización
- Registrar impresiones por listing (quién vio qué) como evento Kafka `listing.impressed` consumido por analytics-ms.
- Con historial de impresiones se puede entrenar un recomendador para promoted listings — mostrarlos a perfiles con mayor probabilidad de conversión, no al azar.
- Feed hoy filtra por preferencias declaradas (onboarding). Con comportamiento (views, tiempo, retorno) se puede alimentar un recomendador colaborativo o content-based para mejorar el ranking.
- El bbox del mapa estilo Airbnb es señal implícita de zona de interés — alimenta el recomendador sin que el usuario haga nada explícito.
- Cadena lógica: impresiones → recomendador de promociones → feed por comportamiento → targeting de promoted listings a personas correctas.

### Diferenciadores del producto
- AVM propio: mayoría de portales LATAM muestran precio del dueño sin referencia de mercado — el AVM cambia la dinámica de negociación para el comprador.
- Feed personalizado desde onboarding: no es un listado genérico filtrable como Metrocuadrado.
- Precio estimado visible en el listing es el mayor diferenciador para el comprador.
- Notificaciones ("llegó una nueva en Chapinero que encaja contigo") son el mayor driver de retención en el vertical inmobiliario.

### Estrategia de supply para lanzamiento
- Riesgo principal no es técnico: es conseguir supply inicial de listings verificados.
- Plan acordado: acercarse a personas que ya tienen listings reales llegando con el MVP funcionando.
- Pitch: "Tu listing en Metrocuadrado es uno entre miles sin contexto de precio. Acá el comprador llega ya filtrado por sus preferencias y con un estimado de mercado para comparar."
- El AVM les da valor inmediato: saben si su precio está bien puesto antes de publicar.

## Open questions
- ¿Los listings iniciales son venta, arriendo o los dos? (sin respuesta aún)
- Diseño del evento `listing.impressed`: ¿anónimo con fingerprint o solo usuarios autenticados?

## Next steps
- Implementar tracking de impresiones en properties-service (candidato a Kafka event).
- Hablar con propietarios de listings reales llegando con el MVP.
- Mapa estilo Airbnb con bbox → actualización del feed es la siguiente feature crítica de UX.
