"""Tests for the HACS review fixes (removal, recreation, refresh, recorder)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.skyradar_fusion import device_tracker as dt
from custom_components.skyradar_fusion.const import DOMAIN
from custom_components.skyradar_fusion.sensor import SkyRadarFusionOverviewSensor
from custom_components.skyradar_fusion.text import SkyRadarFusionRemoveText


def test_overview_attributes_not_recorded():
    assert {"flights_list", "recent_aircraft"} <= set(
        SkyRadarFusionOverviewSensor._unrecorded_attributes
    )


@pytest.mark.asyncio
async def test_remove_matches_exact_unique_id(hass):
    entry = MockConfigEntry(domain=DOMAIN, entry_id="rm_test")
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    for hex_id in ("KLM123", "TRACKER9", "A1B2"):
        registry.async_get_or_create(
            "device_tracker",
            DOMAIN,
            f"skyradar_fusion_{hex_id}",
            config_entry=entry,
            suggested_object_id=f"skyradar_fusion_{hex_id.lower()}",
        )

    coord = MagicMock()
    coord.config_entry = entry
    coord.async_request_refresh = AsyncMock()
    text = SkyRadarFusionRemoveText(coord)
    text.hass = hass
    text.async_write_ha_state = MagicMock()

    # A short value that matches every entity_id prefix must not remove anything.
    await text.async_set_value("track")
    assert len(er.async_entries_for_config_entry(registry, "rm_test")) == 3

    await text.async_set_value("klm 123")
    remaining = {
        e.unique_id for e in er.async_entries_for_config_entry(registry, "rm_test")
    }
    assert remaining == {"skyradar_fusion_TRACKER9", "skyradar_fusion_A1B2"}
    coord.remove_track.assert_called_with("KLM123")


@pytest.mark.asyncio
async def test_tracker_recreated_after_removal(hass):
    entry = MockConfigEntry(domain=DOMAIN, entry_id="re_test", options={})
    coord = MagicMock()
    coord.config_entry = entry
    coord.data = {"tracked_aircraft": [{"hex": "KLM123", "flight": "KLM123"}]}
    listeners = []
    coord.async_add_listener = lambda cb: listeners.append(cb) or (lambda: None)
    hass.data.setdefault(DOMAIN, {})["re_test"] = coord
    added = []

    await dt.async_setup_entry(hass, entry, lambda ents: added.extend(ents))
    assert len(added) == 1

    listeners[0]()
    assert len(added) == 1  # still exists, not duplicated

    # Simulate removal (registry removal or the clear button).
    await added[0].async_will_remove_from_hass()
    listeners[0]()
    assert len(added) == 2
    assert added[1].unique_id == "skyradar_fusion_KLM123"
