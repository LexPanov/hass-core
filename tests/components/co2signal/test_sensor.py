"""Tests Electricity Maps sensor platform."""
from datetime import timedelta
from unittest.mock import AsyncMock

from aioelectricitymaps.exceptions import (
    ElectricityMapsDecodeError,
    ElectricityMapsError,
    InvalidToken,
)
from freezegun.api import FrozenDateTimeFactory
import pytest
from syrupy import SnapshotAssertion

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import async_fire_time_changed


@pytest.mark.parametrize(
    "entity_name",
    [
        "sensor.electricity_maps_co2_intensity",
        "sensor.electricity_maps_grid_fossil_fuel_percentage",
    ],
)
@pytest.mark.usefixtures("setup_integration")
async def test_sensor(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    entity_name: str,
    snapshot: SnapshotAssertion,
) -> None:
    """Test sensor setup and update."""
    assert (entry := entity_registry.async_get(entity_name))
    assert entry == snapshot

    assert (state := hass.states.get(entity_name))
    assert state == snapshot


@pytest.mark.parametrize(
    "error",
    [
        InvalidToken,
        ElectricityMapsDecodeError,
        ElectricityMapsError,
        Exception,
    ],
)
@pytest.mark.usefixtures("setup_integration")
async def test_sensor_update_fail(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    electricity_maps: AsyncMock,
    error: Exception,
) -> None:
    """Test sensor error handling."""
    assert (state := hass.states.get("sensor.electricity_maps_co2_intensity"))
    assert state.state == "45.9862319009581"
    assert len(electricity_maps.mock_calls) == 1

    electricity_maps.latest_carbon_intensity_by_coordinates.side_effect = error
    electricity_maps.latest_carbon_intensity_by_country_code.side_effect = error

    freezer.tick(timedelta(minutes=20))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get("sensor.electricity_maps_co2_intensity"))
    assert state.state == "unavailable"
    assert len(electricity_maps.mock_calls) == 2

    # reset mock and test if entity is available again
    electricity_maps.latest_carbon_intensity_by_coordinates.side_effect = None
    electricity_maps.latest_carbon_intensity_by_country_code.side_effect = None

    freezer.tick(timedelta(minutes=20))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get("sensor.electricity_maps_co2_intensity"))
    assert state.state == "45.9862319009581"
    assert len(electricity_maps.mock_calls) == 3
