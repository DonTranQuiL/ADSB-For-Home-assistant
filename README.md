<div align="center">

# 📡 Airplanes.Live Tracker (2026 Edition)
**The high-performance, zero-bloat ADS-B airspace monitor for Home Assistant.**
</div>

<p align="center">
  <a href="https://github.com/DonTranQuiL/ADSB-For-Home-assistant/releases">
    <img src="https://img.shields.io/github/v/release/DonTranQuiL/nova-conversation?style=for-the-badge&color=007ec6" alt="Latest Release">
  </a>
  <a href="https://github.com/DonTranQuiL/ADSB-For-Home-assistant/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/DonTranQuiL/ADSB-For-Home-assistant?style=for-the-badge&color=007ec6" alt="License">
  </a>
  <a href="https://github.com/DonTranQuiL/ADSB-For-Home-assistant/actions/workflows/hass-ci.yml">
    <img src="https://github.com/DonTranQuiL/ADSB-For-Home-assistant/actions/workflows/hass-ci.yml/badge.svg" alt="Home Assistant CI" style="height:28px;">
  </a>

  <a href="https://github.com/DonTranQuiL/ADSB-For-Home-assistant/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/DonTranQuiL/ADSB-For-Home-assistant/codechecker.yml?style=for-the-badge&label=CODE%20CHECKS&color=5dbb0f" alt="Code Checks">
  </a>
  <a href="https://github.com/DonTranQuiL/ADSB-For-Home-assistant/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/DonTranQuiL/ADSB-For-Home-assistant/pytest.yml?style=for-the-badge&label=TESTS&color=5dbb0f" alt="Tests">
  </a>
  <a href="https://github.com/DonTranQuiL/ADSB-For-Home-assistant/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/DonTranQuiL/ADSB-For-Home-assistant/hacs.yaml?style=for-the-badge&label=HACS%20VALIDATION&color=5dbb0f" alt="HACS Validation">
  </a>

  <a href="https://github.com/pre-commit/pre-commit">
    <img src="https://img.shields.io/badge/pre--commit-enabled-5dbb0f?style=for-the-badge" alt="pre-commit">
  </a>
  <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/badge/code%20style-ruff-000000?style=for-the-badge" alt="Ruff">
  </a>
  <a href="https://codecov.io/gh/DonTranQuiL/ADSB-For-Home-assistant">
    <img src="https://codecov.io/gh/DonTranQuiL/ADSB-For-Home-assistant/branch/main/graph/badge.svg" alt="Coverage" style="height:28px;">
  </a>

  <a href="https://hacs.xyz/">
    <img src="https://img.shields.io/badge/HACS-CUSTOM-ff6e27?style=for-the-badge" alt="HACS">
  </a>
  <a href="https://www.home-assistant.io/">
    <img src="https://img.shields.io/badge/Home%20Assistant-2024.5%2B-007ec6?style=for-the-badge" alt="Home Assistant">
  </a>

  <a href="https://github.com/DonTranQuiL">
    <img src="https://img.shields.io/badge/maintainer-%40DonTranQuiL-007ec6?style=for-the-badge" alt="Maintainer">
  </a>
  <a href="https://ko-fi.com/DonTranQuiL">
    <img src="https://img.shields.io/badge/buy%20me%20a%20coffee-donate-ffdd00?style=for-the-badge" alt="Donate">
  </a>
  <a href="https://community.home-assistant.io/">
    <img src="https://img.shields.io/badge/community-forum-007ec6?style=for-the-badge" alt="Community">
  </a>
</p>

### 🚀 High-Performance Airspace Intelligence
Bring full, live aviation telemetry straight into Home Assistant using the open-access Airplanes.Live API feed. Engineered with an optimization-first mindset, this component gathers complete regional telemetry through **one solitary aggregated background request per cycle**. Say goodbye to Cloudflare blocks, API rate bans, and system slowdowns. 

This repository passes standard GitHub CI workflows, validating smooth installation hooks directly inside active Home Assistant core instances.

---

## 🌟 The "Next Level" Updates
This tracking suite revamps typical location-monitoring with a streamlined, database-safe framework:

* **Zero-Bloat Registry:** Traditional aircraft components span a unique tracker entity for *every single airplane* crossing your area, muddying your system database with hundreds of dead diagnostic links. This component uses a strict gatekeeping policy: maps and `device_tracker` entities are generated **only** for targets explicitly locked on your watchlist.
* **Micro-Precision Radius Control:** The scanning footprint is processed natively in **meters**. Adjust your observation barrier precisely to catch only immediate regional occurrences.
* **Automatic Category Separation:** Telemetry feeds are evaluated on-the-fly to calculate tracking states into explicit group counters (`Helicopters`, `Military`, `Commercial`, `Private`), letting you design granular cards for distinct flight subsets.
* **Interactive Options Handling:** Tweak scanning properties or add flight identifiers instantly in real-time through the native configuration window (the gear icon), avoiding uninstallation cycles.

---

## ✨ Core Features
* **Live Boundary Statistics:** Monitors structural sky properties instantly via dedicated operational sensors:
  * `Current in area`: Total active airframes within your target metric barrier.
  * `Entered area`: Counter showing objects passing *into* your radius on the current sweep.
  * `Exited area`: Counter showing objects departing your radius on the current sweep.
  * `Additional tracked`: Aggregated sum of explicit flights being dynamically targeted.
* **Dynamic Livery Images (`entity_picture`):** Maps search automatically for an available graphic matching the ICAO airframe signature (e.g., `H60`, `B738`) inside your local directory at `/local/airplanes/[ICAO_TYPE].png`.
* **Adaptive Airframe Telemetry:** Missing a profile picture? Watchlist entities automatically map onto a smart MDI icon that pivots shape in real-time depending on horizontal speed and vertical climb speed (`baro_rate`):
  * 🛫 **Climbing (`baro_rate > 250 ft/min`):** `mdi:airplane-takeoff`
  * 🛬 **Descending (`baro_rate < -250 ft/min`):** `mdi:airplane-landing`
  * 🚁 **Helicopters:** Rigidly assigned to `mdi:helicopter` for visual separation.
* **Instant Poll Control:** Leverages an automation-friendly `airplanes_live.refresh` script call. Run immediate manual lookups via dashboard button cards or audio trip triggers without waiting for the default 10-second polling clock.

---

## 🚀 Installation & Setup

1. Copy the `airplanes_live` directory cleanly inside your server's `custom_components/` folder.
2. Restart Home Assistant.
3. Open **Settings > Devices & Services > Add Integration**.
4. Type **Airplanes.Live Tracker** and initialize setup.
5. Provide your scanning parameters:
   * **Zone Tracking:** Supply your target Latitude, Longitude, and radius threshold in **meters** (Default is set to `5000` meters).
   * **Target Tracking:** Set up a worldwide focus loop for a static target outside your home airspace.

---

## ⚙️ Watchlist & Metric Management
To track explicit airframes on your card views, modify your instance directly via the integration **Configure** gear menu:

* **Add to track:** Provide a clean Callsign (e.g., `KLM1682`) or ICAO Hex signature to add a dynamic tracking card onto your environment view.
* **Remove from track:** Type the identifier code to unmount the device tracking entity safely.
* **Clear Additional tracked:** Toggle this flag to clear your tracking database instantly, cleaning up all lingering watchlist `device_tracker` assets.

---

## 📈 Service Automation Example
Trigger a force-refresh cycle the instant external sensors or acoustic ears pick up local activity:

```yaml
alias: "Airspace: Immediate Overhead Refresh"
description: "Forces a fresh polling loop from the Airplanes.Live endpoint"
trigger:
  - platform: state
    entity_id: binary_sensor.acoustic_radar_sensor
    to: "on"
action:
  - service: airplanes_live.refresh
    data: {}
