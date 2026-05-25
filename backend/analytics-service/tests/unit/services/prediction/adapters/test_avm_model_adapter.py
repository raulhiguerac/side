import uuid
from unittest.mock import MagicMock

import numpy as np
import pytest

from app.models.prediction import PropertyType
from app.services.prediction.adapters.avm_model_adapter import AVMModelAdapter
from app.services.prediction.schemas.prediction import PredictionRequest

REQ = PredictionRequest(
    area_m2=80.0,
    bedrooms=2,
    bathrooms=1.0,
    parking_spots=1,
    stratum=4,
    property_type=PropertyType.apartment,
    year_built=2010,
    lat=4.65,
    lon=-74.05,
    barrio_ideca="CHAPINERO",
    property_id=uuid.uuid4(),
)


def make_adapter(price, version="v1"):
    client = MagicMock()
    client.get_version.return_value = version
    client.online_predict.return_value = price
    client.batch_predict.return_value = [price, price]
    return AVMModelAdapter(client=client)


class TestOnlinePredict:
    def test_returns_float_and_version(self):
        adapter = make_adapter(np.float64(500_000_000))
        price, version = adapter.online_predict(record=REQ)
        assert isinstance(price, float)
        assert version == "v1"

    def test_casts_np_float64_to_python_float(self):
        adapter = make_adapter(np.float64(123456.789))
        price, _ = adapter.online_predict(record=REQ)
        assert type(price) is float

    def test_excludes_property_id_from_model_input(self):
        adapter = make_adapter(1.0)
        adapter.online_predict(record=REQ)
        sent = adapter.client.online_predict.call_args[1]["record"]
        assert "property_id" not in sent

    def test_fetches_production_alias(self):
        adapter = make_adapter(1.0)
        adapter.online_predict(record=REQ)
        adapter.client.get_version.assert_called_once_with(
            model_name="bogota-avm", alias="production"
        )


class TestBatchPredict:
    def test_returns_list_of_floats_and_version(self):
        adapter = make_adapter(np.float64(500_000_000))
        prices, version = adapter.batch_predict(records=[REQ, REQ])
        assert all(type(p) is float for p in prices)
        assert len(prices) == 2
        assert version == "v1"

    def test_casts_all_np_float64(self):
        client = MagicMock()
        client.get_version.return_value = "v1"
        client.batch_predict.return_value = [np.float64(1.0), np.float64(2.0)]
        adapter = AVMModelAdapter(client=client)
        prices, _ = adapter.batch_predict(records=[REQ, REQ])
        assert all(type(p) is float for p in prices)

    def test_excludes_property_id_from_all_records(self):
        adapter = make_adapter(1.0)
        adapter.batch_predict(records=[REQ, REQ])
        records_sent = adapter.client.batch_predict.call_args[1]["records"]
        assert all("property_id" not in r for r in records_sent)
