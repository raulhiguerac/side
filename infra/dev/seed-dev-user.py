"""Crea el usuario dev pasando por el flujo real de registro del servicio.

Por que via HTTP y no un INSERT: RegisterAccountUseCase crea el usuario en
Keycloak y la fila en `accounts` con `account_id = sub` de Keycloak, en una sola
transaccion con compensacion. Insertar a mano obligaria a replicar ese
invariante, y a mantenerlo sincronizado con el codigo.

Por eso tambien keycloak-init NO crea este usuario: si ya existiera en Keycloak,
el registro fallaria — la policy de email solo mira la DB local, asi que pasaria
el chequeo y reventaria despues, al crear el usuario en el IdP.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

USERS_URL = os.environ["USERS_URL"]
KC_URL = os.environ["KC_URL"]
KC_REALM = os.environ["KC_REALM"]
KC_ADMIN = os.environ["KC_BOOTSTRAP_ADMIN"]
KC_ADMIN_PW = os.environ["KC_BOOTSTRAP_ADMIN_PASSWORD"]
DEV_USER = os.environ["KC_DEV_USER"]
DEV_PW = os.environ["KC_DEV_PASSWORD"]
ADMIN_ROLE = os.environ.get("ADMIN_ROLE", "admin")


def request(url, *, data=None, form=None, token=None, method=None):
    headers = {}
    body = None
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        raw = resp.read()
        return resp.status, (json.loads(raw) if raw else None)


def register_account():
    payload = {
        "account_type": "person",
        "first_name": "Dev",
        "last_name": "Seed",
        "email": DEV_USER,
        "password": DEV_PW,
    }
    try:
        _, body = request(f"{USERS_URL}/v1/auth/register", data=payload)
        print(f"  usuario dev creado: {DEV_USER} (account_id={body['account_id']})")
    except urllib.error.HTTPError as exc:
        if exc.code == 409:
            print(f"  usuario dev ya existe: {DEV_USER}")
            return
        print(f"  ERROR {exc.code} registrando {DEV_USER}: {exc.read().decode()[:300]}", file=sys.stderr)
        raise


def grant_admin_role():
    _, tok = request(
        f"{KC_URL}/realms/master/protocol/openid-connect/token",
        form={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": KC_ADMIN,
            "password": KC_ADMIN_PW,
        },
    )
    token = tok["access_token"]

    q = urllib.parse.urlencode({"username": DEV_USER, "exact": "true"})
    _, users = request(f"{KC_URL}/admin/realms/{KC_REALM}/users?{q}", token=token)
    if not users:
        raise SystemExit(f"  ERROR: {DEV_USER} no aparece en Keycloak tras el registro")
    user_id = users[0]["id"]

    _, role = request(f"{KC_URL}/admin/realms/{KC_REALM}/roles/{ADMIN_ROLE}", token=token)

    # Re-asignar un rol ya asignado es un no-op, asi que esto es idempotente.
    request(
        f"{KC_URL}/admin/realms/{KC_REALM}/users/{user_id}/role-mappings/realm",
        data=[{"id": role["id"], "name": role["name"]}],
        token=token,
    )
    print(f"  rol '{ADMIN_ROLE}' asignado a: {DEV_USER}")


print("seed-dev-user:")
register_account()
grant_admin_role()
print("seed-dev-user: ok")
