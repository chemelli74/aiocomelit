from aiocomelit.api import (
    ComeliteSerialBridgeAPi,
    ComelitSerialBridgeObject,
    ComelitVedoObject,
)
from aiocomelit.exceptions import (
    CannotAuthenticate,
    CannotConnect,
    CannotRetrieveData,
    ComelitError,
)


def test_objects_can_be_imported():
    assert type(ComeliteSerialBridgeAPi)
    assert type(ComelitSerialBridgeObject)
    assert type(ComelitVedoObject)
    assert type(ComelitError)
    assert type(CannotConnect)
    assert type(CannotAuthenticate)
    assert type(CannotRetrieveData)
