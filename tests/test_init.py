from aiocomelit.api import (
    ComeliteSerialBridgeApi,
    ComelitSerialBridgeObject,
    ComelitVedoApi,
    ComelitVedoObject,
)
from aiocomelit.exceptions import (
    CannotAuthenticate,
    CannotConnect,
    CannotRetrieveData,
    ComelitError,
)


def test_objects_can_be_imported():
    assert type(ComeliteSerialBridgeApi)
    assert type(ComelitSerialBridgeObject)
    assert type(ComelitVedoApi)
    assert type(ComelitVedoObject)
    assert type(ComelitError)
    assert type(CannotConnect)
    assert type(CannotAuthenticate)
    assert type(CannotRetrieveData)
