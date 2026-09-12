"""Regression: FlightRadarAPI 1.6+ renamed FlightRadar24 -> FlightRadarAPI."""

import importlib
import sys
import types


def test_import_flightradar24_api_prefers_new_module(monkeypatch):
    # Build a fake FlightRadarAPI package providing FlightRadar24API
    mod = types.ModuleType("FlightRadarAPI")
    class FlightRadar24API:  # noqa: N801 - upstream class name
        pass
    mod.FlightRadar24API = FlightRadar24API
    monkeypatch.setitem(sys.modules, "FlightRadarAPI", mod)
    monkeypatch.delitem(sys.modules, "FlightRadar24", raising=False)

    # Import helper from api without pulling Home Assistant
    # Load module file directly with stubbed relative import
    import pathlib
    api_path = pathlib.Path(__file__).resolve().parents[1] / "custom_components/skyradar_fusion/api.py"
    # Ensure package stubs
    pkg = types.ModuleType("custom_components")
    sub = types.ModuleType("custom_components.skyradar_fusion")
    const = types.ModuleType("custom_components.skyradar_fusion.const")
    const.API_BASE_URL = "https://example.test"
    monkeypatch.setitem(sys.modules, "custom_components", pkg)
    monkeypatch.setitem(sys.modules, "custom_components.skyradar_fusion", sub)
    monkeypatch.setitem(sys.modules, "custom_components.skyradar_fusion.const", const)

    spec = importlib.util.spec_from_file_location(
        "custom_components.skyradar_fusion.api", api_path
    )
    api = importlib.util.module_from_spec(spec)
    # stub aiohttp for import
    monkeypatch.setitem(sys.modules, "aiohttp", types.ModuleType("aiohttp"))
    sys.modules["aiohttp"].ClientSession = object
    spec.loader.exec_module(api)

    cls = api._import_flightradar24_api()
    assert cls is FlightRadar24API
