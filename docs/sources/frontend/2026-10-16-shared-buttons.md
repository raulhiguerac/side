---
title: Botones compartidos del frontend (BaseButton, IconButton, ChoiceChip, OptionCard)
captured-from: conversation
captured-on: 2026-10-16
participants: [raul, claude]
---

## Context
Una revisión de todo el front encontró unos 90 `<button>` con estilos escritos a mano y solo 21 usos de `PrimaryButton`, que no tenía variantes. Se reemplazaron por cuatro componentes compartidos (PR #31). Lint, vue-tsc y build pasan; nada se probó en el navegador.

## Key conclusions
- **`BaseButton`** reemplaza a `PrimaryButton`, que se borró. Variantes `primary`, `secondary`, `ghost`, `danger`, `danger-soft` y `link`; tamaños `sm`, `md`, `lg` (pie de modales, `py-3`) y `xl` (CTA de auth, `h-12 text-base`, el antiguo `lg` de `PrimaryButton`). Props `loading`, `block`, `disabled`, `to`.
- `BaseButton` tiene `type="button"` por defecto: un botón dentro de un `<form>` no lo envía sin pedirlo. Con `to` se dibuja como `RouterLink`, para links con aspecto de botón.
- Todos son `rounded-xl` y el hover del primario usa `brand-primary-dark`, no `green-500/600`. Los cuatro componentes tienen anillo de foco visible (`focus-visible:ring`).
- **`IconButton`** exige `label`, que va al `aria-label` y al `title`: un botón de solo icono no puede quedar sin nombre accesible. Variantes `surface` (círculo blanco sobre fotos) y `plain`; `danger` cambia el hover a rojo.
- **`ChoiceChip`** (opción chica: estrato, moneda, días de promoción, estado del inmueble, tipo en filtros, perfiles de "Cerca del lugar") y **`OptionCard`** (tarjeta grande: tipo de inmueble, tipo de anuncio, intención y tipo del onboarding, tipo de cuenta) llevan `aria-pressed`. `OptionCard` solo fija marco y estado (`rounded-2xl border-2`); el contenido y su distribución van en el slot. Los grupos se arman con `v-for` en cada pantalla, sin componente de grupo.
- Un solo estilo de seleccionado para los chips: fondo verde claro y borde verde. Estrato, moneda y tipo en filtros antes iban en verde sólido.
- `AdminActionBar` mapea sus variantes (`default`, `primary`, `danger`) a `secondary`, `primary` y `danger-soft` de `BaseButton`; el pie de `AdminFormModal` también usa `BaseButton`.
- El `<form>` de `RegisterView` no tiene handler de submit y sus botones no declaraban `type`: eran submit implícitos. Con el `type="button"` por defecto eso desaparece.
- Una clase pasada desde el padre no pisa una del componente en el mismo grupo (`justify-start` contra `justify-center`): en Tailwind manda el orden del CSS generado, no el del atributo. La variación de layout va por props, no por clases que choquen.
- **Fuera a propósito:** pestañas (`FilterTabs`, pestañas de ciudad del onboarding), botones de la navbar, el switch de visibilidad, los "mostrar contraseña" (van con un futuro `PasswordInput`), el contador `−`/`+` del AVM, el acordeón de "Cerca del lugar", la portada del panel admin y los CTAs del hero del home (van en pareja con un botón de borde blanco sobre fondo oscuro que necesitaría su propia variante).

## Open questions
- ¿Una variante para botones sobre fondo oscuro (hero del home), para migrar esos CTAs?
- ¿`PasswordInput` y `BaseInput` como siguiente paso del sistema de componentes?

## Next steps
- Probar en navegador: registro completo, crear y editar propiedad, AVM, onboarding, ajustes de cuenta, admin y galería de fotos.
