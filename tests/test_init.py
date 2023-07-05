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
    assert ComeliteSerialBridgeAPi
    assert ComelitSerialBridgeObject
    assert ComelitVedoObject
    assert ComelitError
    assert CannotConnect
    assert CannotAuthenticate
    assert CannotRetrieveData
