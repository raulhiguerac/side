"""Wiring de las rutas de moderación: ruta → use case.

Los use cases ya están cubiertos por sus tests unitarios. Lo que se prueba acá
es lo que aquellos no pueden ver: que el `principal` llegue al UC, que el
`model_validator` de `VerifyPropertyRequest` corte en el borde HTTP, y que las
tres acciones respondan 204 sin cuerpo.
"""

import uuid

import pytest

from app.api.deps.admin import get_set_status_uc, get_verify_property_uc
from tests.unit.api.conftest import ADMIN, ADMIN_ID

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

STATUS_URL = f"/v1/admin/properties/{PROP_ID}/status"
VERIFICATION_URL = f"/v1/admin/properties/{PROP_ID}/verification"


# ---------------------------------------------------------------------------
# PATCH /status
# ---------------------------------------------------------------------------

def test_set_status_returns_204_and_passes_principal(admin_client, override_uc):
    uc = override_uc(get_set_status_uc)

    response = admin_client.patch(STATUS_URL, json={"status": "active"})

    assert response.status_code == 204
    assert response.content == b""
    uc.execute.assert_awaited_once()
    kwargs = uc.execute.await_args.kwargs
    assert kwargs["principal"] == ADMIN
    assert kwargs["property_id"] == PROP_ID
    assert kwargs["target_status"] == "active"


def test_set_status_rejects_unknown_status(admin_client, override_uc):
    uc = override_uc(get_set_status_uc)

    response = admin_client.patch(STATUS_URL, json={"status": "vendida"})

    assert response.status_code == 422
    uc.execute.assert_not_awaited()


# ---------------------------------------------------------------------------
# PATCH /verification
# ---------------------------------------------------------------------------

def test_verify_returns_204_and_passes_principal(admin_client, override_uc):
    uc = override_uc(get_verify_property_uc)

    response = admin_client.patch(VERIFICATION_URL, json={"verification_status": "verified"})

    assert response.status_code == 204
    assert response.content == b""
    kwargs = uc.execute.await_args.kwargs
    assert kwargs["principal"].sub == ADMIN_ID
    assert kwargs["property_id"] == PROP_ID
    assert kwargs["request"].verification_status == "verified"


def test_rejecting_carries_the_reason_through(admin_client, override_uc):
    uc = override_uc(get_verify_property_uc)

    response = admin_client.patch(
        VERIFICATION_URL,
        json = {
            "verification_status": "rejected",
            "rejection_reason": "las fotos no corresponden al inmueble",
        },
    )

    assert response.status_code == 204
    assert uc.execute.await_args.kwargs["request"].rejection_reason == (
        "las fotos no corresponden al inmueble"
    )


# ---------------------------------------------------------------------------
# El validador del schema corta antes del use case
# ---------------------------------------------------------------------------

def test_rejecting_without_reason_is_422(admin_client, override_uc):
    """Es la regla que obliga al front a pedir el motivo antes de mandar."""
    uc = override_uc(get_verify_property_uc)

    response = admin_client.patch(VERIFICATION_URL, json={"verification_status": "rejected"})

    assert response.status_code == 422
    uc.execute.assert_not_awaited()


@pytest.mark.parametrize("target", ["verified", "pending"])
def test_reason_without_rejection_is_422(admin_client, override_uc, target):
    uc = override_uc(get_verify_property_uc)

    response = admin_client.patch(
        VERIFICATION_URL,
        json = {
            "verification_status": target,
            "rejection_reason": "sobra",
        },
    )

    assert response.status_code == 422
    uc.execute.assert_not_awaited()


def test_unknown_field_is_422(admin_client, override_uc):
    """`StrictBase` usa `extra="forbid"`: un campo de más no se ignora."""
    uc = override_uc(get_verify_property_uc)

    response = admin_client.patch(
        VERIFICATION_URL,
        json = {
            "verification_status": "verified",
            "verified_by": str(uuid.uuid4()),
        },
    )

    assert response.status_code == 422
    uc.execute.assert_not_awaited()
