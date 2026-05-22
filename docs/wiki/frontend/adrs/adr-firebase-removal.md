---
title: ADR-0004 — Remover Firebase del frontend
status: stable
last-verified: 2026-05-21
owners: [frontend]
related: [[frontend]], [[frontend-architecture]], [[adr-auth-keycloak-jwt]]
sources: [../../../sources/frontend/2026-05-21-foundational-qa.md]
decision-date: 2026-05-21
decision-status: accepted
---

# ADR-0004 — Remover Firebase del frontend

## Contexto

`package.json` tiene `firebase: ^10.12.2` como dependencia, usada únicamente en [`LoginView.loginWithGoogle()`](frontend/src/views/auth/LoginView.vue#L301-L326):

```ts
const auth = getAuth();
const provider = new GoogleAuthProvider();
const result = await signInWithPopup(auth, provider);
const idToken = await result.user.getIdToken();
// envía idToken al backend
await axios.post("http://localhost:8000/v1/auth/login/google", { token: idToken }, ...);
```

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

## Trigger de re-evaluación

Solo si Keycloak resultara insuficiente (no es escenario realista), o si se necesita auth offline-first (PWA con auth without server reachability), Firebase podría volver — pero esos casos no están en el roadmap.

## Claims

- `firebase: ^10.12.2` está en `dependencies` del `package.json` ([package.json:17](frontend/package.json#L17)).
- Firebase se inicializa on-demand en `LoginView.loginWithGoogle`, no globalmente — el `initializeApp(firebaseConfig)` en `main.ts` está comentado ([main.ts:14](frontend/src/main.ts#L14), [LoginView.vue:303-305](frontend/src/views/auth/LoginView.vue#L303-L305)).
- El endpoint backend invocado es `POST /v1/auth/login/google` con body `{ token: idToken }` ([LoginView.vue:310-314](frontend/src/views/auth/LoginView.vue#L310-L314)).
- Keycloak (configurado en el compose, ver [[architecture]]) soporta Identity Brokering con Google nativo — no requiere SDK adicional en el frontend.
