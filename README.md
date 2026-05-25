<div align="center">

# 📡 Airplanes.Live Tracker (2026 Edition)
**The high-performance, zero-bloat, real-time ADS-B airspace intelligence monitor for Home Assistant.**

# I DID A MASSIVE OVERHAUL !!! ADDED FR24 DATA !

[![Latest Release](https://img.shields.io/github/v/release/DonTranQuiL/ADSB-For-Home-assistant?style=for-the-badge&color=007ec6)](https://github.com/DonTranQuiL/ADSB-For-Home-assistant/releases)
[![License](https://img.shields.io/github/license/DonTranQuiL/ADSB-For-Home-assistant?style=for-the-badge&color=007ec6)](https://github.com/DonTranQuiL/ADSB-For-Home-assistant/blob/main/LICENSE)
[![Home Assistant CI](https://img.shields.io/github/actions/workflow/status/DonTranQuiL/ADSB-For-Home-assistant/hass-ci.yml?label=Home%20Assistant%20CI&style=for-the-badge)](https://github.com/DonTranQuiL/ADSB-For-Home-assistant/actions/workflows/hass-ci.yml)
[![Code Checks](https://img.shields.io/github/actions/workflow/status/DonTranQuiL/ADSB-For-Home-assistant/codechecker.yml?style=for-the-badge&label=CODE%20CHECKS&color=5dbb0f)](https://github.com/DonTranQuiL/ADSB-For-Home-assistant/actions)
[![Tests](https://img.shields.io/github/actions/workflow/status/DonTranQuiL/ADSB-For-Home-assistant/pytest.yml?style=for-the-badge&label=TESTS&color=5dbb0f)](https://github.com/DonTranQuiL/ADSB-For-Home-assistant/actions)
[![HACS Validation](https://img.shields.io/github/actions/workflow/status/DonTranQuiL/ADSB-For-Home-assistant/hacs.yaml?style=for-the-badge&label=HACS%20VALIDATION&color=5dbb0f)](https://github.com/DonTranQuiL/ADSB-For-Home-assistant/actions)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-5dbb0f?style=for-the-badge)](https://github.com/pre-commit/pre-commit)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000?style=for-the-badge)](https://github.com/astral-sh/ruff)
[![HACS Custom](https://img.shields.io/badge/HACS-CUSTOM-ff6e27?style=for-the-badge)](https://hacs.xyz/)
[![Home Assistant Version](https://img.shields.io/badge/Home%20Assistant-2025.1%2B-007ec6?style=for-the-badge)](https://www.home-assistant.io/)
[![Maintainer](https://img.shields.io/badge/maintainer-%40DonTranQuiL-007ec6?style=for-the-badge)](https://github.com/DonTranQuiL)
[![Donate](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-ffdd00?style=for-the-badge)](https://ko-fi.com/DonTranQuiL)
[![Community Forum](https://img.shields.io/badge/community-forum-007ec6?style=for-the-badge)](https://community.home-assistant.io/t/ads-b-tracker-for-home-assistant/1011081)
[![CodeQL](https://img.shields.io/github/actions/workflow/status/DonTranQuiL/ADSB-For-Home-assistant/codeql.yml?label=CodeQL&style=for-the-badge)](https://github.com/DonTranQuiL/ADSB-For-Home-assistant/actions/workflows/codeql.yml)

</div>

### 🚀 High-Performance Airspace Intelligence
Bring ultra-fast, live aviation telemetric streams directly into Home Assistant using the open-access Airplanes.Live API feed. Engineered with a strict optimization-first mindset, this component consolidates all regional lookups into **one single aggregated network request per polling cycle**. Say goodbye to Cloudflare blocks, aggressive API rate bans, and home automation host slowdowns.

---

## 📥 How to Install (via HACS)

The most efficient deployment method is through **HACS** (Home Assistant Community Store):

1. Open **HACS** in your sidebar and navigate into the **Integrations** panel.
2. Click the three dots (`...`) located in the upper right quadrant and select **Custom repositories**.
3. Input the repository web link: `https://github.com/DonTranQuiL/ADSB-For-Home-assistant`
4. Set the Category selector dropdown to **Integration** and hit **Add**.
5. Locate the newly added **Airplanes.Live Tracker** repository card and hit **Download**.
6. ⚠️ **Restart your Home Assistant instance**.
7. Navigate to **Settings > Devices & Services > Add Integration**, lookup **Airplanes.Live Tracker**, and configure your primary boundary coordinates.

---

## 🌟 Architectural Features

### 📸 Dynamic Photo API Integration (Powered by Planespotters.net)
No more manual photo scraping! This integration natively communicates with the public **Planespotters.net API**. When tracking an active target, it runs an automated cross-reference check:
1. It queries the live database using the aircraft’s **Registration Tail Number (`r`)**.
2. If the tail registration yields empty results, it triggers an instant **ICAO Mode-S Hex Code (`hex`) Fallback Routine** to locate the frame.
3. Once found, it injects the live asset URL (`thumbnail_large`) directly into the `entity_picture` attribute, presenting real-world hull images straight onto your Home Assistant Map component.

---

## Tracking feature and live feed on your maps, with the image of the plane!
### 1️⃣ Add a Callsign to Track
Enter any live callsign into the tracking field and it will instantly appear inside your additional tracked targets.

<p align="center">
  <img src="https://github.com/user-attachments/assets/7c493baa-f350-4b65-be2b-1624100b0cff"
       width="320"
       alt="Add callsign to tracking list">
</p>

---

### 2️⃣ Add the Aircraft Entity to Your Map
Tracked aircraft entities always follow this format:

```text
tracker.airplanes_live_CALLSIGN
```

Add the entity directly into a Lovelace Map card. The tracked entities are not visible in the integration as a seperate entity! 

<p align="center">
  <img src="https://github.com/user-attachments/assets/ac3420f7-4a3e-4f36-89da-41e08cb9265e"
       width="300"
       alt="Map entity example">
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/0a723c32-a90e-4ed2-8d8d-53ecb442d883"
       width="500"
       alt="Tracked aircraft on map">
</p>



---

### 🧠 Intelligent In-Memory Photo Caching
To adhere to API terms and prevent network throttling (DDoS behaviors), the integration incorporates a smart asynchronous **Photo Cache Layer** within the DataUpdateCoordinator. Each unique airframe photo is queried **exactly once** during its airspace presence. Subsequent telemetry sweeps pull the asset directly out of volatile memory, conserving system bandwidth and maximizing frontend rendering speeds.

### 🧹 Real-Time Zero-Bloat Entity Cleanup
Standard aviation integrations spin up permanent entities for every flying hull crossing your boundary, corrupting the Home Assistant Entity Registry and Recorder database with hundreds of dead historical links. This component enforces a strict **Zero-Bloat Gatekeeping Policy**:
* Individual `device_tracker` entities are generated **only** for targets explicitly locked on your watchlist.
* The moment you stop tracking a flight, the integration dynamically hooks into the Home Assistant Core `entity_registry` and **permanently purges** the tracker entity. No lingering `Unavailable` states, no ghost entities, and a pristine database.

### ⏳ Seamless Lovelace UI Controls (No Reload Hiccups)
Unlike old frameworks that save watchlists inside the underlying integration options—which triggers a jarring reload of all platforms every time a setting changes—this architecture handles your tracking lists completely in memory. Using dedicated frontend `text` and `button` entities, you can add or remove targets straight from your dashboard view. It updates the state machines immediately, bypassing core integration reload cycles entirely.

### 💾 Safe State Restoration across Reboots
Because the tracking lists are stored dynamically in memory to ensure UI speed, the integration features a specialized **`RestoreSensor` (`sensor.additional_tracked`)**. This module acts as an encrypted state bucket. On server reboots or system crashes, it parses historical database records, reads the active tracking arrays, and instantly rebuilds your watchlist on startup.

---

## ✨ Core Platforms & Sensors

### 📊 Local Airspace Telemetry
When configured in **Zone Tracking Mode**, the integration maps local coordinates against the API feed using native metric haversine math to break down immediate regional traffic:
* `sensor.current_in_area`: Total count of active airframes currently inside your metric barrier. Includes deep attribute lists mapping closest flight codes, minimum relative distances, and specific Hull Types.
* `sensor.entered_area`: Real-time sweep counter indicating how many airframes passed *into* your operational boundary on the last tick.
* `sensor.exited_area`: Sweep counter identifying airframes leaving your metric airspace footprint.
* `sensor.[Category]_s_in_area`: Dynamic classification trackers splitting local airspace counts on-the-fly into dedicated subset entities (`Helicopters`, `Military`, `Commercial`, `Private`). Great for triggering conditional Lovelace conditional cards or warnings!

### 🌍 Global Strategic Radars (Configurable Toggles)
Tap into worldwide events directly through the integration options menu:
* **Global Emergency Radar (Squawk 7700):** When enabled, spins up `sensor.global_emergencies_7700`. It continually monitors the entire planet for active transponders broadcasting an active emergency, computing the real-time distance relative to your home coordinates.
* **Global Military Radar:** When enabled, provisions `sensor.global_military`. Monitors active tactical airframes across the globe, listing absolute frame data and real-time distance matrices.
* ** The radius is in KM, so 5000 is 5km.

### 🛠️ Core Diagnostic Suite
Tucked away safely inside the native Home Assistant `Diagnostic` entity category, you can monitor tracking pipeline integrity in real-time:
* `sensor.airplanes_live_consecutive_errors`: Integer counter displaying consecutive API network timeout or fetch failures.
* `sensor.airplanes_live_last_update_status`: State string exposing the explicit health status of the network endpoint loop (`Success`, `Pending`, `Failed`).
* `sensor.airplanes_live_last_update_time`: Precise ISO Timestamp showing the last successful data retrieval.

---

## 🏎️ Adaptive Telemetry & ICAO Fallback Icons
Missing a profile picture on Planespotters? Target tracking entities automatically bind to a highly reactive Material Design Icon suite that alters visual representation based on immediate telemetric parameters and vertical climb speeds (`baro_rate`):
* 🛫 **Climbing (`baro_rate > 250 ft/min`):** Transforms to `mdi:airplane-takeoff`
* 🛬 **Descending (`baro_rate < -250 ft/min`):** Transforms to `mdi:airplane-landing`
* 🚁 **Rotorcraft / Helicopters:** Hard-locked onto `mdi:helicopter` for clean visual scanning.
* 🎈 **Balloons / Gliders:** Dynamically swaps indicators to specialized icons (`mdi:hot-air-balloon` or `mdi:paper-airplane`).

---


## 🗺️ Local Liveries Asset Mapping (Custom Fallback)
If the external photo API draws a blank for specific experimental hulls or secure assets, the system falls back onto your local file server structure using an advanced asynchronous non-blocking frontend asset path (`/airplanes_live_assets/`).
1. Navigate inside your core file system to `/config/custom_components/airplanes_live/`
2. Create a folder hierarchy named `www/planes/`
3. Drop transparent `.png` files inside that folder, matching the official uppercase ICAO type signature (e.g., `/planes/B77W.png` or `/planes/A320.png`).
4. The tracking maps will cleanly prioritize these assets before resorting to default MDI icon mappings.

---

## ⚙️ Interactive Lovelace Dashboard Configurations
Take advantage of the integrated `text` and `button` controllers to build complete airfield operational panels directly inside your standard Lovelace grid setups:

### Lovelace Card Control Example
```yaml
type: entities
title: "Airspace Watchlist Controls"
show_header_toggle: false
entities:
  - entity: text.airplanes_live_tracker_add_to_track
    name: "🚀 Target Flight Lock"
  - entity: text.airplanes_live_tracker_remove_from_track
    name: "🗑️ Release Flight Lock"
  - entity: button.airplanes_live_tracker_clear_additional_tracked
    name: "🧹 Wipe Target Registry"
