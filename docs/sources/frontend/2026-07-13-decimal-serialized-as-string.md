---
title: "Bug: campos Decimal de properties-service llegan como string al frontend"
captured-from: conversation
captured-on: 2026-07-13
participants: [raul, claude]
---

## Context

Al construir el formulario de edición de propiedades (`EditPropertyView.vue`), el precio se mostraba sin formatear (`"540000000.00"` en vez de `"540.000.000"`) pese a usar `formatMoney` (`value.toLocaleString("es-CO")`). Se investigó la causa raíz en vez de parchear el síntoma.

## Key conclusions

- **Causa raíz**: Pydantic serializa los campos `Decimal` del backend (`price`, `admin_fee`, `area_m2`, `bathrooms` en `PropertyDetailSchema`/`PropertyCardSchema`) como **string JSON** (ej. `"540000000.00"`), no como `number`. El tipo TypeScript del frontend (`PropertyDetail.price: number`) miente sobre esto — en runtime el valor es un string.
- **Por qué el bug era silencioso**: `"...".toLocaleString("es-CO")` en un string usa `Object.prototype.toLocaleString` (no `Number.prototype.toLocaleString`), que simplemente devuelve el string sin tocarlo — no explota, no da error, solo no formatea. `Intl.NumberFormat().format(valor)` sí coacciona el string a number internamente, por eso `usePropertyDetail.ts` (que usa `Intl.NumberFormat`) nunca mostró el bug.
- **Ya había precedente sin documentar**: `usePropertyMapper.ts` ya hacía `price: Number(p.price)` y `bathrooms: Number(p.bathrooms)` — alguien ya se había topado con esto antes pero no quedó registrado en ningún lado.
- **Fix aplicado**: coaccionar con `Number(...)` en el punto donde se leen estos campos desde la respuesta de la API — en `EditPropertyView.vue`, tanto al popular `form.price`/`form.admin_fee` como en los stat tiles de `area_m2`/`bathrooms`.

## Open questions

- Ninguna — el patrón de fix es claro y reproducible.

## Next steps

- **Convención a seguir en cualquier código nuevo que consuma `PropertyCardSchema`/`PropertyDetailSchema`**: envolver siempre `price`, `admin_fee`, `area_m2`, `bathrooms` en `Number(...)` al leerlos del response, sin importar lo que diga el tipo TS. Aplica a cualquier vista/composable futuro que toque estos campos directo de la API (no solo a los ya corregidos).
