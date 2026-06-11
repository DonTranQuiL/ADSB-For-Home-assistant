class SkyRadarFusionCard extends HTMLElement {
  constructor() {
    super();
    this._filters = {
      distance: 100,
      airline: 'All',
      type: 'All',
      emergency: false,
      ultraWide: false
    };
    this._sort = { by: 'distance', desc: false };
    this._expandedRows = new Set();
    this._aircraftData = [];
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Entity required");
    }
    this.config = config;
  }

  set hass(hass) {
    this._hass = hass;
    const stateObj = hass.states[this.config.entity];

    if (!this.card) {
      this._setupUI();
    }

    // --- THEME DETECTOR ---
    if (hass.themes && hass.themes.darkMode) {
      this.card.classList.add('dark-theme');
      this.card.classList.remove('light-theme');
    } else {
      this.card.classList.add('light-theme');
      this.card.classList.remove('dark-theme');
    }

    if (!stateObj) {
      this.card.querySelector('.skyradar-list').innerHTML = `<div style="padding:16px">Entity not found</div>`;
      return;
    }

    this._aircraftData = stateObj.attributes.recent_aircraft || [];

    this._updateAirlinesDropdown();
    this._renderAircraft();
  }

  _setupUI() {
    this.card = document.createElement("ha-card");
    
    this.card.innerHTML = `
      <style>
        /* =========================================
           BASE THEME (LIGHT MODE) 
           ========================================= */
        ha-card {
          overflow: hidden;
          border-radius: 18px;
          background: var(--ha-card-background, var(--card-background-color, #ffffff));
          color: var(--primary-text-color, #202124);
          font-family: var(--paper-font-body1_-_font-family, sans-serif);
          border: 1px solid var(--divider-color, rgba(0,0,0,0.1));
          transition: background 0.3s, color 0.3s;
        }

        .card-header-title {
          font-size: 20px;
          font-weight: 600;
          padding: 18px 18px 4px 18px;
          display: flex;
          align-items: center;
          gap: 10px;
          color: var(--primary-text-color);
        }

        .controls {
          display: flex;
          flex-wrap: wrap;
          gap: 16px;
          padding: 12px 18px 16px 18px;
          background: transparent;
          border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.08));
          align-items: center;
          font-size: 13px;
        }
        
        .control-group { display: flex; align-items: center; gap: 8px; }

        select, input[type="range"] {
          background: var(--card-background-color, #fff);
          border: 1px solid var(--divider-color, rgba(0, 0, 0, 0.15));
          color: var(--primary-text-color, #000);
          padding: 4px 8px; border-radius: 6px; outline: none;
        }

        /* =========================================
           LAYOUT ARCHITECTURE (STRICT VERTICAL) 
           ========================================= */
        .table-scroll { 
          width: 100%; 
          overflow-x: auto; 
          display: block; 
        }
        
        /* Renamed to bypass Home Assistant's default column/masonry injection */
        .skyradar-list {
          display: block !important; 
          width: 100%; 
          max-height: 800px; 
          overflow-y: auto;
          overflow-x: hidden;
        }

        .row-wrapper { 
          display: block !important; 
          width: 100%; 
          clear: both;
          border-bottom: 1px solid var(--divider-color, rgba(0,0,0,.05)); 
        }

        /* Default Layout (Fixed Widths) */
        .grid-row {
          display: grid;
          grid-template-columns: 90px 140px 180px 240px 140px 150px 80px 120px 70px;
          gap: 12px; align-items: center; padding: 10px 18px; transition: 0.15s; 
          min-width: 1100px; /* Forces scrollbar on small screens */
        }

        /* Ultra Wide Mode Layout (MinMax prevents squishing) */
        .ultra-wide-mode .grid-row {
          min-width: 1100px;
          grid-template-columns: 90px minmax(140px, 1.2fr) minmax(180px, 1.5fr) minmax(240px, 2fr) minmax(140px, 1.2fr) minmax(150px, 1.5fr) 80px 120px 70px;
        }

        .header-row {
          font-size: 12px; font-weight: 700; text-transform: uppercase;
          border-bottom: 1px solid var(--divider-color, rgba(0,0,0,.08));
          position: sticky; top: 0; z-index: 2;
          background: var(--ha-card-background, var(--card-background-color, #f8f9fa));
          color: var(--secondary-text-color, #5f6368);
        }

        .header-row > div { cursor: pointer; display: flex; align-items: center; gap: 4px; user-select: none; transition: color 0.2s; }
        .header-row > div:hover { color: var(--primary-color, #008cff); }
        
        .data-row { cursor: pointer; }
        .data-row:hover { background: var(--secondary-background-color, rgba(0,0,0,0.04)); }
        .emergency { border-left: 4px solid var(--error-color, #dc2626); background: rgba(220,38,38,.05); }

        ha-icon { --mdc-icon-size: 16px; opacity: 0.8; color: var(--secondary-text-color); }
        .tiny-icon { --mdc-icon-size: 14px; margin-right: 4px; }
        .header-icon { --mdc-icon-size: 26px; color: var(--primary-color); opacity: 1; }
        
        img { width: 82px; height: 52px; object-fit: cover; border-radius: 10px; }
        .fallback { width: 82px; height: 52px; display: flex; align-items: center; justify-content: center; background: var(--secondary-background-color, rgba(0,0,0,.05)); border-radius: 10px; }

        .flight { font-weight: 700; font-size: 15px; }
        .sub { color: var(--secondary-text-color, #5f6368); font-size: 12px; margin-top: 2px; display: flex; align-items: center; }
        
        .route { color: var(--primary-color, #008cff); font-weight: 700; }
        .airline { color: var(--accent-color, #ff9800); font-weight: 700; }

        .badge {
          display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 999px;
          background: rgba(0,140,255,.1); color: var(--primary-color, #008cff); font-weight: 700; font-size: 12px;
        }

        .sqk { padding: 5px 8px; border-radius: 8px; background: var(--secondary-background-color, rgba(0,0,0,.05)); font-family: monospace; }
        .sqk-emergency { padding: 5px 8px; border-radius: 8px; background: var(--error-color, #dc2626); color: white; font-weight: 700; animation: pulse 1s infinite; }
        @keyframes pulse { 50% { transform: scale(1.05); } }

        .details-drawer {
          background: var(--secondary-background-color, rgba(0,0,0,0.02));
          padding: 16px 18px; display: none;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 16px; font-size: 12px;
          border-top: 1px dashed var(--divider-color, rgba(0,0,0,0.1));
        }
        .row-wrapper.expanded .details-drawer { display: grid; }
        .row-wrapper.expanded .data-row { background: var(--secondary-background-color, rgba(0,140,255,.05)); }

        .status-good { color: var(--success-color, #4caf50); font-weight: 600; }
        .status-warn { color: var(--warning-color, #ff9800); font-weight: 600; }
        .status-danger { color: var(--error-color, #f44336); font-weight: 600; }
        .status-info { color: var(--info-color, #03a9f4); font-weight: 600; }
        .status-time { color: var(--primary-color, #9c27b0); font-weight: 600; }


        /* =========================================
           DARK MODE OVERRIDE (YOUR ORIGINAL LOOK) 
           ========================================= */
        .dark-theme {
          background: radial-gradient(circle at top left, rgba(0,90,255,.12), transparent 35%), linear-gradient(180deg, #0d1118, #141923) !important;
          color: #e2e8f0 !important;
          border: none !important;
        }
        .dark-theme .card-header-title { color: #ffffff; }
        .dark-theme .header-icon { color: #7dd3fc; }
        .dark-theme .controls { background: transparent; border-bottom: 1px solid rgba(255,255,255,.08); }
        .dark-theme select, .dark-theme input[type="range"] { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); color: white; }
        .dark-theme .header-row { background: #0d1118; border-bottom: 1px solid rgba(255,255,255,.08); color: white; }
        .dark-theme .header-row > div:hover { color: #7dd3fc; }
        
        .dark-theme .row-wrapper { border-bottom: 1px solid rgba(255,255,255,.05); }
        .dark-theme .data-row:hover { background: rgba(0,140,255,.08); }
        .dark-theme .row-wrapper.expanded .data-row { background: rgba(0,140,255,.12); }
        .dark-theme .details-drawer { background: transparent; border-top: 1px solid rgba(255,255,255,.05); }
        
        .dark-theme ha-icon { color: white; opacity: 0.7; }
        .dark-theme .fallback { background: rgba(255,255,255,.08); }
        .dark-theme .sub { color: #e2e8f0; opacity: 0.7; }
        
        .dark-theme .route { color: #7dd3fc; }
        .dark-theme .airline { color: #facc15; }
        .dark-theme .badge { background: rgba(0,150,255,.15); color: #55b8ff; }
        .dark-theme .sqk { background: rgba(255,255,255,.08); color: white; }
        .dark-theme .emergency { background: rgba(220,38,38,.08); border-left: 4px solid #dc2626; }

        .dark-theme .status-good { color: #22c55e !important; }
        .dark-theme .status-warn { color: #facc15 !important; }
        .dark-theme .status-danger { color: #ef4444 !important; }
        .dark-theme .status-info { color: #60a5fa !important; }
        .dark-theme .status-time { color: #c084fc !important; }

        /* Mobile Stacking - Applies to both Wide and Normal modes */
        @media (max-width: 1000px) {
          .header-row { display: none; }
          .grid-row { grid-template-columns: 1fr 1fr !important; padding: 16px; row-gap: 16px; min-width: 100% !important; }
          .photo-col { grid-column: 1 / -1; }
          .photo-col img, .photo-col .fallback { width: 100%; height: auto; max-height: 180px; }
          .flight-col, .aircraft-col, .route-col, .airline-col, .data-col, .vs-col, .arrival-col, .sqk-col {
             display: flex; flex-direction: column; align-items: flex-start;
          }
        }
      </style>

      <div class="card-header-title">
        <ha-icon icon="mdi:radar" class="header-icon"></ha-icon> SkyRadar Fusion
      </div>

      <div class="controls">
        <div class="control-group">
          <label>Distance (<span id="dist-val">100</span>km)</label>
          <input type="range" id="filter-dist" min="5" max="150" value="100">
        </div>
        <div class="control-group">
          <label>Airline:</label>
          <select id="filter-airline"><option value="All">All</option></select>
        </div>
        <div class="control-group">
          <label>Type:</label>
          <select id="filter-type">
            <option value="All">All</option>
            <option value="Commercial">Commercial</option>
            <option value="Military">Military</option>
          </select>
        </div>
        <div class="control-group" style="margin-left: 8px;">
           <label style="display:flex; align-items:center; gap:4px; cursor:pointer;">
             <input type="checkbox" id="filter-emerg"> Emergency Only
           </label>
        </div>
        <div class="control-group" style="margin-left: 8px;">
           <label style="display:flex; align-items:center; gap:4px; cursor:pointer;">
             <input type="checkbox" id="filter-wide"> Ultra Wide Mode
           </label>
        </div>
      </div>

      <div class="table-scroll">
        <div class="grid-row header-row">
          <div data-sort="none">Photo</div>
          <div data-sort="flight">Flight</div>
          <div data-sort="t">Aircraft</div>
          <div data-sort="airport_origin_name">Route</div>
          <div data-sort="airline">Airline</div>
          <div data-sort="distance">Flight Data</div>
          <div data-sort="baro_rate">V/S</div>
          <div data-sort="fr24_estimated_arrival">Arrival</div>
          <div data-sort="squawk">SQK</div>
        </div>
        <div class="skyradar-list" id="aircraft-list"></div>
      </div>
    `;

    this.appendChild(this.card);

    this.card.querySelector('#filter-dist').addEventListener('input', (e) => {
      this._filters.distance = e.target.value;
      this.card.querySelector('#dist-val').innerText = e.target.value;
      this._renderAircraft();
    });
    this.card.querySelector('#filter-airline').addEventListener('change', (e) => {
      this._filters.airline = e.target.value; this._renderAircraft();
    });
    this.card.querySelector('#filter-type').addEventListener('change', (e) => {
      this._filters.type = e.target.value; this._renderAircraft();
    });
    this.card.querySelector('#filter-emerg').addEventListener('change', (e) => {
      this._filters.emergency = e.target.checked; this._renderAircraft();
    });
    this.card.querySelector('#filter-wide').addEventListener('change', (e) => {
      this._filters.ultraWide = e.target.checked; 
      if (e.target.checked) this.card.classList.add('ultra-wide-mode');
      else this.card.classList.remove('ultra-wide-mode');
    });
    this.card.querySelectorAll('.header-row > div[data-sort]').forEach(el => {
      el.addEventListener('click', () => {
        const sortBy = el.getAttribute('data-sort');
        if (sortBy === 'none') return;
        if (this._sort.by === sortBy) { this._sort.desc = !this._sort.desc; } 
        else { this._sort.by = sortBy; this._sort.desc = false; }
        this._renderAircraft();
      });
    });
  }

  _updateAirlinesDropdown() {
    if (!this.card) return;
    const select = this.card.querySelector('#filter-airline');
    const currentVal = this._filters.airline;
    
    const airlines = [...new Set(this._aircraftData.map(a => this._cleanString(a.airline) || 'Private'))].sort();
    
    let options = `<option value="All">All</option>`;
    airlines.forEach(a => { options += `<option value="${a}" ${a === currentVal ? 'selected' : ''}>${a}</option>`; });
    
    if (select.innerHTML !== options) { select.innerHTML = options; }
  }

  _toggleRow(hex) {
    if (this._expandedRows.has(hex)) { this._expandedRows.delete(hex); } 
    else { this._expandedRows.add(hex); }
    this._renderAircraft();
  }

  _getSilhouetteIcon(type, category) {
    const cat = (category || "").toLowerCase();
    const t = (type || "").toUpperCase();
    if (cat.includes('military') || t.includes('F16') || t.includes('F35')) return 'mdi:fighter-jet';
    if (cat.includes('helicopter') || ['R44','EC35','H135','H145'].includes(t)) return 'mdi:helicopter';
    if (cat.includes('light')) return 'mdi:airplane-cog';
    return 'mdi:airplane';
  }

  _cleanString(val) {
    if (val === null || val === undefined) return null;
    let s = String(val).replace(/[\?]/g, '').trim();
    return s.length > 0 ? s : null;
  }

  _cleanNumber(val) {
    if (val === null || val === undefined) return null;
    let num = String(val).replace(/[^0-9.-]/g, '');
    return num.length > 0 ? num : null;
  }

  _renderAircraft() {
    const container = this.card.querySelector('#aircraft-list');
    if (!container) return;

    let filtered = this._aircraftData.filter(a => {
      const distKm = a.distance_meter ? a.distance_meter / 1000 : 0;
      if (distKm > this._filters.distance) return false;
      const airline = this._cleanString(a.airline) || 'Private';
      if (this._filters.airline !== 'All' && airline !== this._filters.airline) return false;
      const emergencySqks = ["7500","7600","7700"];
      if (this._filters.emergency && !emergencySqks.includes(String(a.squawk))) return false;
      if (this._filters.type !== 'All') {
        const isMil = (a.air_category || '').toLowerCase().includes('military');
        if (this._filters.type === 'Military' && !isMil) return false;
        if (this._filters.type === 'Commercial' && isMil) return false;
      }
      return true;
    });

    filtered.sort((a, b) => {
      let valA, valB;
      if (this._sort.by === 'distance') {
        valA = a.distance_meter || 999999; valB = b.distance_meter || 999999;
      } else {
        valA = a[this._sort.by] || ''; valB = b[this._sort.by] || '';
      }
      if (valA < valB) return this._sort.desc ? 1 : -1;
      if (valA > valB) return this._sort.desc ? -1 : 1;
      return 0;
    });

    window._skyRadarToggle = (hex) => this._toggleRow(hex);

    // Apply the 50 max limit dynamically
    const html = filtered.slice(0, 50).map(a => {
      const hex = a.hex || Math.random().toString();
      const isExpanded = this._expandedRows.has(hex);

      const altMeters = a.alt_baro ? Math.round(a.alt_baro * 0.3048) : 0;
      const speed = a.gs ? Math.round(a.gs * 1.852) : 0;
      const distKm = a.distance_meter ? (a.distance_meter / 1000) : 0;
      
      const formatTime = (ts, includeSec = false) => ts ? new Date(ts).toLocaleTimeString([],{ hour:'2-digit', minute:'2-digit', second: includeSec ? '2-digit' : undefined }) : "-";
      const spotted = formatTime(a.spotted_time, true);
      const eta = formatTime(a.fr24_estimated_arrival);
      const std = formatTime(a.fr24_scheduled_arrival);

      const altClass = altMeters > 10000 ? "status-good" : altMeters > 3000 ? "status-warn" : "status-danger";
      const distClass = distKm < 10 ? "status-good" : distKm < 25 ? "status-warn" : "status-info";
      const emergency = ["7500","7600","7700"].includes(String(a.squawk));

      const iconType = this._getSilhouetteIcon(a.t, a.air_category);

      return `
      <div class="row-wrapper ${isExpanded ? 'expanded' : ''}">
        <div class="grid-row data-row ${emergency ? 'emergency' : ''}" onclick="window._skyRadarToggle('${hex}')">
          
          <div class="photo-col">
            ${a.api_photo_url ? `<img src="${a.api_photo_url}" loading="lazy">` : `<div class="fallback"><ha-icon icon="${iconType}"></ha-icon></div>`}
          </div>

          <div class="flight-col">
            <div class="flight">${this._cleanString(a.flight) || "Unknown"}</div>
            <div class="sub">${this._cleanString(a.r) || "-"} • ${this._cleanString(a.hex) || "-"}</div>
          </div>

          <div class="aircraft-col">
            <div class="badge">
              <ha-icon icon="${iconType}" class="tiny-icon"></ha-icon> ${this._cleanString(a.t) || "UNK"}
            </div>
            <div class="sub">${this._cleanString(a.desc) || ""}</div>
          </div>

          <div class="route-col">
            <div class="route">${this._cleanString(a.fr24_route) || "-"}</div>
            <div class="sub"><ha-icon icon="mdi:airplane-takeoff" class="tiny-icon"></ha-icon> ${this._cleanString(a.airport_origin_name) || "-"}</div>
            <div class="sub"><ha-icon icon="mdi:airplane-landing" class="tiny-icon"></ha-icon> ${this._cleanString(a.airport_destination_name) || "-"}</div>
          </div>

          <div class="airline-col">
            <div class="airline">${this._cleanString(a.airline) || "Private"}</div>
            <div class="sub">${this._cleanString(a.air_category) || ""}</div>
          </div>

          <div class="data-col">
            <div class="${altClass}"><ha-icon icon="mdi:altimeter" class="tiny-icon" style="color:inherit;"></ha-icon> ${altMeters.toLocaleString()} m</div>
            <div class="sub"><ha-icon icon="mdi:speedometer" class="tiny-icon"></ha-icon> ${speed} km/h</div>
            <div class="sub ${distClass}"><ha-icon icon="mdi:map-marker-distance" class="tiny-icon" style="color:inherit;"></ha-icon> ${distKm.toFixed(1)} km</div>
            <div class="sub status-time"><ha-icon icon="mdi:clock-outline" class="tiny-icon" style="color:inherit;"></ha-icon> ${spotted}</div>
          </div>

          <div class="vs-col">
            ${a.baro_rate ? `
              <div class="${a.baro_rate > 0 ? 'status-good' : 'status-danger'}">
                <ha-icon icon="${a.baro_rate > 0 ? 'mdi:chevron-double-up' : 'mdi:chevron-double-down'}" class="tiny-icon" style="color: inherit;"></ha-icon>
                ${Math.abs(a.baro_rate)}
              </div>
              <div class="sub">fpm</div>
            ` : "-"}
          </div>

          <div class="arrival-col">
            <div><ha-icon icon="mdi:timer-outline" class="tiny-icon"></ha-icon> ${eta}</div>
            <div class="sub">STD ${std}</div>
          </div>

          <div class="sqk-col">
            <span class="${emergency ? 'sqk-emergency' : 'sqk'}">${this._cleanString(a.squawk) || "-"}</span>
          </div>

        </div>

        <div class="details-drawer">
          <div><b>Track</b><br>${this._cleanNumber(a.track) || "-"}°</div>
          <div><b>Heading</b><br>${this._cleanNumber(a.true_heading) || "-"}°</div>
          <div><b>IAS</b><br>${this._cleanNumber(a.ias) || "-"} kt</div>
          <div><b>TAS</b><br>${this._cleanNumber(a.tas) || "-"} kt</div>
          <div><b>Mach</b><br>${this._cleanNumber(a.mach) || "-"}</div>
          <div><b>Category</b><br>${this._cleanString(a.category) || "-"}</div>
        </div>

      </div>
      `;
    }).join("");

    container.innerHTML = html;
  }

  getCardSize() { return 12; }
}

customElements.define("skyradar-fusion-card", SkyRadarFusionCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "skyradar-fusion-card",
  name: "SkyRadar Fusion Card",
  description: "FR24 style aircraft dashboard with Filtering and Sorting"
});
