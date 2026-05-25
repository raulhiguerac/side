import uuid

import pytest
from pydantic import ValidationError

from app.workers.listing_created.helpers.types import WorkerMessage

PROP_ID = uuid.uuid4()

VALID_MODEL = {
    "area_m2": 80.0,
    "bedrooms": 2,
    "bathrooms": 1.0,
    "parking_spots": 1,
    "stratum": 4,
    "property_type": "apartment",
    "year_built": 2010,
    "lat": 4.65,
    "lon": -74.05,
    "barrio_ideca": "CHAPINERO",
}


def test_valid_message_parses():
    msg = WorkerMessage(id=PROP_ID, attempts=1, model=VALID_MODEL)
    assert msg.id == PROP_ID
    assert msg.attempts == 1


def test_attempts_defaults_to_one():
    msg = WorkerMessage(id=PROP_ID, model=VALID_MODEL)
    assert msg.attempts == 1


def test_attempts_zero_is_rejected():
    with pytest.raises(ValidationError):
        WorkerMessage(id=PROP_ID, attempts=0, model=VALID_MODEL)


def test_attempts_strict_rejects_string():
    with pytest.raises(ValidationError):
        WorkerMessage(id=PROP_ID, attempts="1", model=VALID_MODEL)


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        WorkerMessage(id=PROP_ID, attempts=1, model=VALID_MODEL, extra="x")


def test_id_coerced_from_string():
    msg = WorkerMessage.model_validate(
        {"id": str(PROP_ID), "attempts": 1, "model": VALID_MODEL}
    )
    assert msg.id == PROP_ID


def test_property_id_mutable_after_parse():
    msg = WorkerMessage(id=PROP_ID, model=VALID_MODEL)
    msg.model.property_id = msg.id
    assert msg.model.property_id == PROP_ID


def test_invalid_model_raises():
    with pytest.raises(ValidationError):
        WorkerMessage(id=PROP_ID, model={"area_m2": -1})
