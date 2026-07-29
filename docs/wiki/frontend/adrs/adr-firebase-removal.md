---
title: ADR-0004 — Remover Firebase del frontend
status: stable
last-verified: 2026-07-28
owners: [frontend]
related:
  - "[[frontend]]"
  - "[[frontend-architecture]]"
  - "[[adr-auth-keycloak-jwt]]"
  - "[[open-items]]"
sources: [../../../sources/frontend/2026-05-21-foundational-qa.md, ../../../sources/frontend/2026-07-28-admin-panel-groundwork.md]
decision-date: 2026-05-21
decision-status: accepted
executed-on: 2026-07-28
---

# ADR-0004 — Remover Firebase del frontend

## Contexto

`package.json` tiene `firebase: ^10.12.2` como dependencia, usada únicamente en `LoginView.loginWithGoogle()`:

```ts
const auth = getAuth();
const provider = new GoogleAuthProvider();
const result = await signInWithPopup(auth, provider);
const idToken = await result.user.getIdToken();
// envía idToken al backend
await usersApi.post("/v1/auth/login/google", { token: idToken });
```

(La llamada al backend usaba `axios.post` con URL hardcodeada `http://localhost:8000`; tras la centralización de axios en instancias por servicio, ahora usa `usersApi.post` con path relativo — mismo endpoint y shape, solo cambió el transporte.)

El flujo era: Firebase maneja el popup de Google → devuelve un `idToken` de Firebase → backend lo valida y crea/vincula la cuenta del usuario.

**Esto era un spike**: el autor lo intentó como POC de "social login" pero **no terminó de cuajar**. El stack ya tiene **Keycloak** como Identity Provider central (ver `[[adr-auth-keycloak-jwt]]`), y Keycloak soporta **Identity Brokering** con Google nativamente — sin necesidad de Firebase.

Mantener Firebase agrega:
- Bundle size significativo (firebase 10 son ~150KB+ minified gzipped).
- Otra identity store que mantener configurada.
- Acoplamiento al ecosistema Google.
- Duplicación de la responsabilidad de auth (Firebase Y Keycloak hacen lo mismo).

## Decisión

**Eliminar Firebase del frontend completamente.** Google sign-in se implementará vía **Keycloak Identity Brokering** cuando se priorice.

## Alternativas consideradas

- **Mantener Firebase para Google sign-in solamente**: dos identity stores, dos puntos de configuración, no agrega valor.
- **Migrar a NextAuth/Auth.js**: alternativa OAuth client-side, pero sigue duplicando lo que Keycloak ya hace.
- **Postponer la decisión**: deuda silenciosa que crece con cada feature que toca auth.

## Plan de remoción

Pasos concretos:

1. **`LoginView.vue`** — borrar:
   - Import `import { getAuth, GoogleAuthProvider, signInWithPopup } from "firebase/auth"`.
   - Función `loginWithGoogle()`.
   - Botón "Continuar con Google" del template.
   - Divider "O continuar con".

2. **`main.ts`** — borrar:
   - Comment `// initializeApp(firebaseConfig);` (ya estaba comentado).
   - Cualquier import residual.

3. **`package.json`** — borrar dep `firebase: ^10.12.2`.

4. **Backend (`users-service`)**:
   - Si `/v1/auth/login/google` solo lo consumía esta integración: eliminar el endpoint, el UC, los tests asociados.
   - Si lo consume algo más (un script, mobile app futura): mantener pero documentar que el frontend ya no lo usa.

5. **Variables de entorno y secretos**:
   - Si hay un `firebaseConfig` en algún lado: eliminar.
   - Sin claves de Firebase para rotar (eran de un POC).

6. **Cuando Google sign-in vuelva a entrar en scope**:
   - Configurar Identity Broker en el realm de Keycloak (Identity Providers → Add Provider → Google).
   - El frontend solo necesita un botón que redirige a la URL de auth de Keycloak con `provider=google`. Sin SDK extra.

## Consecuencias

- ✅ Bundle más liviano (~150KB+ menos minified).
- ✅ Una sola identity store (Keycloak), menos config drift.
- ✅ Menos secretos para administrar.
- ✅ Cuando vuelva Google sign-in, será via Keycloak — patrón consistente con email/password.
- ❌ Pérdida temporal del botón "Continuar con Google" hasta que Keycloak Brokering esté configurado.
- ❌ Trabajo de cleanup (~1 hora de remover imports/deps + smoke test login normal).

## Ejecución (2026-07-28)

Ejecutado 14 meses después de decidido, al auditar dependencias del frontend. Al hacerlo aparecieron **tres cosas que este ADR daba por ciertas y no lo eran** — todas en la dirección de que el flujo estaba más muerto de lo que se creía:

1. **Firebase nunca se inicializaba, ni siquiera on-demand.** Este ADR afirmaba que `LoginView.loginWithGoogle` lo inicializaba al vuelo; en realidad llamaba `getAuth()` sin ningún `initializeApp` previo y sin que existiera un `firebaseConfig` en el repo. Cualquier click en el botón tiraba `No Firebase App '[DEFAULT]' has been created`.
2. **El endpoint backend nunca existió.** El paso 4 del plan de remoción contemplaba borrar `POST /v1/auth/login/google` de users-service; no hay tal ruta, ni UC, ni test. No hubo nada que borrar.
3. **`RegisterView` tenía su propio botón de Google**, que este ADR no mencionaba. No tenía handler — era decorativo.

O sea que la "pérdida temporal del botón" listada en las consecuencias no fue tal: no había funcionalidad que perder.

**Desvío deliberado respecto del plan**: los botones y sus dividers quedaron **comentados** en `LoginView` y `RegisterView`, no borrados, con una nota de por qué. El markup es la parte que sirve tal cual cuando entre el Identity Brokering; el handler sí se eliminó, porque no puede sobrevivir a la baja de la dependencia.

## Trigger de re-evaluación

Solo si Keycloak resultara insuficiente (no es escenario realista), o si se necesita auth offline-first (PWA con auth without server reachability), Firebase podría volver — pero esos casos no están en el roadmap.

## Claims

- `firebase` ya no figura en `package.json` ni en el lockfile; tampoco hay imports de `firebase/*` en `src/` ([package.json](frontend/package.json)).
- `main.ts` no tiene ninguna línea de firebase — el `// initializeApp(firebaseConfig)` comentado se eliminó ([main.ts](frontend/src/main.ts)).
- `LoginView.vue` ya no define `loginWithGoogle`; el botón de Google y su divider quedan como bloque comentado en el template ([views/auth/LoginView.vue](frontend/src/views/auth/LoginView.vue)).
- `RegisterView.vue` tenía un botón de Google sin `@click`, hoy también comentado ([views/auth/RegisterView.vue](frontend/src/views/auth/RegisterView.vue)).
- No existe ninguna ruta `/v1/auth/login/google` en users-service ([backend/users-service/src/app](backend/users-service/src/app)).
- Keycloak (configurado en el compose, ver [[architecture]]) soporta Identity Brokering con Google nativo — no requiere SDK adicional en el frontend.
