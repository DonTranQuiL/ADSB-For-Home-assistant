"""Regression: FlightRadarAPI 1.6+ renamed FlightRadar24 -> FlightRadarAPI."""

from __future__ import annotations

import sys
import types

import pytest

from custom_components.skyradar_fusion.api import (
    SkyRadarFusionAPI,
    _import_flightradar24_api,
)


def _install_module(monkeypatch: pytest.MonkeyPatch, module_name: str):
    mod = types.ModuleType(module_name)

    class FlightRadar24API:
        def __init__(self):
            self.ready = True

    mod.FlightRadar24API = FlightRadar24API
    monkeypatch.setitem(sys.modules, module_name, mod)
    return FlightRadar24API


def test_import_helper_prefers_flightradarapi_module(monkeypatch: pytest.MonkeyPatch):
    cls = _install_module(monkeypatch, "FlightRadarAPI")
    monkeypatch.delitem(sys.modules, "FlightRadar24", raising=False)
    assert _import_flightradar24_api() is cls


def test_import_helper_falls_back_to_flightradar24_module(
    monkeypatch: pytest.MonkeyPatch,
):
    # New package present but missing the symbol => ImportError, then legacy path.
    monkeypatch.setitem(sys.modules, "FlightRadarAPI", types.ModuleType("FlightRadarAPI"))
    legacy = _install_module(monkeypatch, "FlightRadar24")
    assert _import_flightradar24_api() is legacy


def test_fr24_client_is_lazy(monkeypatch: pytest.MonkeyPatch):
    cls = _install_module(monkeypatch, "FlightRadarAPI")
    monkeypatch.delitem(sys.modules, "FlightRadar24", raising=False)

    api = SkyRadarFusionAPI(session=object())
    assert api._fr24 is None
    client = api.fr24
    assert isinstance(client, cls)
    assert api.fr24 is client
