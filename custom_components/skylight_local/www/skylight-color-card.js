const COLOR_SWATCHES = [
  "#B7C5FF", "#C5D8FF", "#D1E8FF", "#E1F6FF", "#EFFFF6", "#E9FFE5", "#E8FFD1", "#E6FFC1", "#E3FF89", "#CFFF21",
  "#BAB7FF", "#C5C9FF", "#D1D8FF", "#E5ECFF", "#FFFFFF", "#FBFFEB", "#F9FFD5", "#FBFFC1", "#FCFF89", "#E7FF01",
  "#BBA3FF", "#CAC1FF", "#D8D1FF", "#EEE5FF", "#FFF3FC", "#FFF5EB", "#FFF9C9", "#FFF2C1", "#FFF189", "#FFFF00",
  "#CA8FFF", "#CDB7FF", "#DEC5FF", "#F2DDFF", "#FFE7F9", "#FFEDE2", "#FFEAC9", "#FFE4C1", "#FFE389", "#FFED01",
  "#D881FF", "#D5ABFF", "#E4BDFF", "#F5D1FF", "#FFD8FF", "#FFE1EB", "#FFD9D1", "#FFD5CD", "#FFD69F", "#FFD501",
  "#E164FF", "#E696FF", "#F5B4FF", "#FFC3FF", "#FFCDFF", "#FFD1F5", "#FFC9E3", "#FFC5D8", "#FFC6AF", "#FFC000",
];

const PRESET_ROWS = ["A", "B", "C", "D", "E", "F"];

// H-BAR-F spectrum profile
const H_BAR_F_SPECTRUM = {
  wavelengths: [447, 447, 447, 520, 520, 615, 650],
  amplitudes: [
    [20, 0, 0, 30, 0, 18, 0],
    [60, 0, 0, 10, 0, 18, 0],
    [0, 0, 0, 10, 0, 54, 12],
    [0, 0, 0, 30, 0, 18, 12],
  ],
  widths: [
    [25, 25, 25, 60, 60, 25, 60],
    [25, 25, 25, 60, 60, 25, 60],
    [25, 25, 25, 50, 60, 25, 60],
    [25, 25, 25, 50, 60, 25, 60],
  ],
};

function presetFromColorCode(value) {
  const code = Number(value);
  if (!Number.isInteger(code) || code < 0 || code >= 60) return null;
  return `${PRESET_ROWS[Math.floor(code / 10)]}${(code % 10) + 1}`;
}

class SkylightColorCard extends HTMLElement {
  connectedCallback() {
    if (!this._scheduleTimer) {
      this._scheduleTimer = window.setInterval(() => this._update(), 60_000);
    }
    if (!this._powerRefreshTimer) {
      this._powerRefreshTimer = window.setInterval(() => this._refreshPower(), 5_000);
    }
  }

  disconnectedCallback() {
    window.clearInterval(this._scheduleTimer);
    this._scheduleTimer = null;
    window.clearInterval(this._powerRefreshTimer);
    this._powerRefreshTimer = null;
    this._clearPendingIntensity();
  }

  setConfig(config) {
    if (!config.entity || !config.power_entity) {
      throw new Error("Configure the preset select entity and power number entity.");
    }
    this.config = {
      name: "Color management",
      device_name: "H-BAR FM",
      mode_entity: null,
      ...config,
    };
    this._build();
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  async _refreshPower() {
    if (!this._hass || document.visibilityState === "hidden" || this._refreshingPower
      || this._intensityDragging || this._pendingIntensity != null || this._currentMode() === "auto") return;
    this._refreshingPower = true;
    try {
      await this._hass.callService("homeassistant", "update_entity", {
        entity_id: this._manualIntensityEntity(),
      });
    } catch (error) {
      console.warn("Unable to refresh Skylight power from the lamp", error);
    } finally {
      this._refreshingPower = false;
    }
  }

  getCardSize() {
    return 5;
  }

  _build() {
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }
    this.shadowRoot.replaceChildren();

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card {
          overflow: hidden;
          border-radius: 0;
          background: #fff;
          color: #111;
          box-shadow: none;
        }
        .topbar {
          display: flex;
          align-items: center;
          justify-content: space-around;
          min-height: 58px;
          padding: 0 12px;
          color: white;
          background: #2196ed;
          font-size: 17px;
          font-weight: 700;
          letter-spacing: .01em;
        }
        .title { flex: 1; text-align: center; }
        .device { flex: 1; text-align: center; white-space: nowrap; }
        .content { padding: 34px 12px 0; }
        .section-title {
          margin: 0 0 8px;
          color: #596a7e;
          font-size: 12px;
          font-weight: 700;
          letter-spacing: .08em;
          text-transform: uppercase;
        }
        .palette {
          display: grid;
          grid-template-columns: 22px repeat(10, minmax(0, 1fr));
          gap: 1px;
          align-items: stretch;
          user-select: none;
        }
        .axis, .row-label {
          display: grid;
          place-items: center;
          color: #999;
          font-size: 12px;
          font-weight: 500;
        }
        .swatch {
          position: relative;
          min-width: 0;
          aspect-ratio: 1;
          padding: 0;
          border: 0;
          border-radius: 0;
          background: var(--swatch);
          cursor: pointer;
          transition: transform .12s ease, box-shadow .12s ease;
          -webkit-tap-highlight-color: transparent;
        }
        .swatch:hover { z-index: 1; transform: scale(1.08); }
        .swatch:focus-visible { outline: 2px solid #178fe2; outline-offset: 2px; }
        .swatch[aria-pressed="true"] {
          z-index: 2;
          box-shadow: inset 0 0 0 4px #fff000;
        }
        .marker-icon {
          position: absolute;
          inset: 0;
          display: grid;
          place-items: center;
          color: var(--marker-color);
          pointer-events: none;
        }
        .marker-icon svg { display: block; width: 62%; height: 62%; overflow: visible; }
        .intensity-title { margin: 30px 0 14px; text-align: center; font-size: 18px; font-weight: 600; }
        .intensity {
          display: grid;
          grid-template-columns: 44px minmax(0, 1fr) 44px;
          align-items: center;
          gap: 8px;
          margin: 0 2px 38px;
        }
        .step {
          width: 38px;
          height: 38px;
          border: 2px solid #111;
          border-radius: 50%;
          color: #111;
          background: white;
          font-size: 27px;
          line-height: 1;
          cursor: pointer;
        }
        .step:disabled, input[type="range"]:disabled { opacity: .45; cursor: not-allowed; }
        .range-wrap { min-width: 0; }
        .range-label { display: none; }
        input[type="range"] {
          display: block;
          width: 100%;
          height: 34px;
          margin: 0;
          accent-color: #188fe2;
          cursor: pointer;
          appearance: none;
          border: 2px solid #111;
          border-radius: 24px;
          background: linear-gradient(90deg,#111,#fff);
        }
        input[type="range"]::-webkit-slider-thumb { appearance:none; width:16px; height:42px; border:2px solid #111; border-radius:7px; background:linear-gradient(#fff,#a8b5c0); }
        .modebar { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); margin:0 -12px; background:#2196ed; }
        .mode { min-height:54px; padding:8px 3px; border:0; color:#eef7ff; background:transparent; font-size:16px; font-weight:400; cursor:pointer; }
        .mode:hover, .mode[aria-pressed="true"] { color:#9dff7f; background:transparent; font-weight:700; }
        .mode:disabled { opacity:.4; cursor:not-allowed; }
        .mode[data-mode="superior"], .mode[data-mode="demo"], .mode[data-mode="off"], .mode[data-mode="clone"] { grid-row:2; }
        .mode[data-mode="superior"] { grid-column:3; }
        .mode[data-mode="demo"] { grid-column:1; }
        .mode[data-mode="off"] { grid-column:2; }
        .mode[data-mode="clone"] { grid-column:3; }
        .app-modes { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); margin:0 -12px; background:#2196ed; }
        .app-modes .mode { grid-row:auto!important; grid-column:auto!important; }
        .spectrum { margin: 0 8px 26px; }
        .spectrum[hidden] { display:none; }
        .spectrum svg { display:block; width:100%; height:auto; overflow:visible; }
        .schedule { margin: 0 8px 28px; }
        .schedule[hidden] { display:none; }
        .schedule-title { margin: 0 0 8px; text-align:center; font-size:16px; font-weight:600; }
        .schedule svg { display:block; width:100%; height:auto; overflow:visible; }
        .error { padding: 18px; color: #a94442; font-size: 14px; }
        @media (max-width: 360px) {
          .content { padding: 14px 12px 12px; }
          .palette { grid-template-columns: 18px repeat(10, minmax(0, 1fr)); gap: 2px; }
          .axis, .row-label { font-size: 9px; }
        }
      </style>
      <ha-card>
          <div class="topbar"><span class="device"></span><span class="title"></span></div>
        <div class="content">
          <div class="section-title">Color palette</div>
          <div class="palette" role="grid" aria-label="Preset color selection"></div>
          <div class="intensity-title">Intensity: <span class="intensity-value-heading">—</span></div>
          <div class="intensity">
            <button class="step decrease" type="button" aria-label="Decrease intensity">−</button>
            <div class="range-wrap">
              <div class="range-label"><span class="intensity-label">Manual power</span><span class="intensity-value">30%</span></div>
          <input class="range" type="range" min="0" max="100" step="1" aria-label="Lamp intensity">
            </div>
            <button class="step increase" type="button" aria-label="Increase intensity">+</button>
          </div>
          <div class="spectrum" hidden aria-label="H-BAR-F light spectrum">
            <svg class="spectrum-svg" viewBox="0 0 420 230" role="img" aria-label="Lamp spectrum from 400 to 700 nanometers"></svg>
          </div>
          <div class="schedule" hidden aria-label="Lamp daily schedule">
            <div class="schedule-title">Daily schedule</div>
            <svg class="schedule-svg" viewBox="0 0 420 220" role="img" aria-label="Scheduled lamp intensity from 0:00 to 24:00"></svg>
          </div>
          <div class="app-modes" role="group" aria-label="Lamp mode">
            <button class="mode" type="button" data-mode="auto">Auto</button>
            <button class="mode" type="button" data-mode="manual">Manual</button>
            <button class="mode" type="button" data-mode="superior" disabled>Master</button>
            <button class="mode" type="button" data-mode="demo">Demo</button>
            <button class="mode" type="button" data-mode="off">Off</button>
            <button class="mode" type="button" data-mode="clone" disabled>Clone</button>
          </div>
        </div>
      </ha-card>
    `;

    this._palette = this.shadowRoot.querySelector(".palette");
    this._intensityInput = this.shadowRoot.querySelector(".range");
    this._intensityValue = this.shadowRoot.querySelector(".intensity-value");
    this._intensityHeading = this.shadowRoot.querySelector(".intensity-value-heading");
    this._intensityLabel = this.shadowRoot.querySelector(".intensity-label");
    this._scheduleRaw = null;
    this._modeEntityExplicit = Boolean(this.config.mode_entity);
    this.shadowRoot.querySelector(".title").textContent = this.config.name;
    this.shadowRoot.querySelector(".device").textContent = this.config.device_name;

    const blank = document.createElement("span");
    blank.className = "axis";
    blank.setAttribute("aria-hidden", "true");
    this._palette.appendChild(blank);
    for (let column = 1; column <= 10; column += 1) {
      const label = document.createElement("span");
      label.className = "axis";
      label.textContent = String(column);
      this._palette.appendChild(label);
    }

    const icon = (paths, fill = "currentColor") => `<svg viewBox="0 0 24 24" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">${paths.replaceAll("__FILL__", fill)}</svg>`;
    const leafGradientId = `skylight-leaf-${Math.random().toString(36).slice(2)}`;
    const markers = {
      A4: { color: "#bdbdbd", svg: icon('<path fill="__FILL__" d="M1.5 19.5 7.2 8.1a1.5 1.5 0 0 1 2.7 0l1.8 3.6 1.1-2.1a1.5 1.5 0 0 1 2.7 0l5.5 9.9H1.5Z"/><path fill="#fff" d="m6.2 11.7 1.9-3.5 1.7 3.5-1.7-.9-1.9.9Zm6.7 1.4 1.2-2.4 1.7 3-1.5-.7-1.4.1Z"/>') },
      A7: { color: "#75a976", svg: icon('<path fill="__FILL__" d="M21.5 2.6C14.2 2.8 7.8 4.3 4.4 7.7 1.4 10.7 1.8 15.1 4.1 17.7c2.6 2.8 6.7 2 9.7-1.2C17.8 12.3 20.2 7.2 21.5 2.6Z"/><path d="M4 18.8C8.5 13.9 13.1 9.4 20.8 3.7" fill="none" stroke="#fff" stroke-width="1.15" stroke-linecap="round"/>' ) },
      C1: { color: "#777dc4", svg: icon('<path fill="__FILL__" d="M20.6 15.6A8.8 8.8 0 0 1 8.4 3.4 9.7 9.7 0 1 0 20.6 15.6Z"/>') },
      C5: { color: "#ffc936", svg: icon('<path fill="__FILL__" d="M6 3h12v5c0 3.7-1.7 6.1-4 7v2.5h3.5V21h-11v-3.5H10V15c-2.3-.9-4-3.3-4-7V3Z"/><path d="M6 5H3.5v3c0 2.4 1.2 4 3.5 4.7M18 5h2.5v3c0 2.4-1.2 4-3.5 4.7" fill="none" stroke="__FILL__" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>' ) },
      D6: { color: "#8ad982", svg: icon(`<defs><linearGradient id="${leafGradientId}" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#b8ff48"/><stop offset=".55" stop-color="#78da67"/><stop offset="1" stop-color="#ff967d"/></linearGradient></defs><path fill="url(#${leafGradientId})" d="M21.3 2.8C13.9 3 7.2 4.4 4.2 8.5c-2.5 3.4-.8 7.5 2.7 8.2 3.4.7 6.5-2.3 8.5-5.1 1.4-2 2.8-3.5 5.2-5.2-1.4 2.7-3 5.2-5.8 7.8-2.5 2.3-5.6 3.7-9.2 4.1v2c5-.3 9.1-2.4 12-5.8 3.5-4.1 4.6-8.3 3.7-11.7Z"/>`) },
      E9: { color: "#fff22b", svg: icon('<path fill="__FILL__" d="M11 1h2v4h-2zm0 18h2v4h-2zM1 11h4v2H1zm18 0h4v2h-4zM3.2 4.6l1.4-1.4 2.8 2.8L6 7.4zm12.6 12.6 1.4-1.4 2.8 2.8-1.4 1.4zM18 3.2l1.4 1.4L16.6 7.4l-1.4-1.4zM5 16.2l1.4 1.4-2.8 2.8-1.4-1.4z"/><circle fill="__FILL__" cx="12" cy="12" r="5.2"/>') },
      F1: { color: "#d779a7", svg: icon('<path fill="__FILL__" d="M12 1.5c1.7 0 2.3 2.1 3.2 3.5 1.4-.9 3.4-1.4 4.6-.2 1.2 1.2.7 3.2-.2 4.6 1.4.9 3.5 1.5 3.5 3.2s-2.1 2.3-3.5 3.2c.9 1.4 1.4 3.4.2 4.6-1.2 1.2-3.2.7-4.6-.2-.9 1.4-1.5 3.5-3.2 3.5s-2.3-2.1-3.2-3.5c-1.4.9-3.4 1.4-4.6.2-1.2-1.2-.7-3.2.2-4.6-1.4-.9-3.5-1.5-3.5-3.2s2.1-2.3 3.5-3.2c-.9-1.4-1.4-3.4-.2-4.6 1.2-1.2 3.2-.7 4.6.2C9.7 3.6 10.3 1.5 12 1.5Z"/><circle cx="12" cy="12" r="3.4" fill="#fff"/><circle cx="12" cy="12" r="1.7" fill="__FILL__"/>' ) },
      F7: { color: "#bd9294", svg: icon('<path fill="__FILL__" d="M21.5 2.6C14.2 2.8 7.8 4.3 4.4 7.7 1.4 10.7 1.8 15.1 4.1 17.7c2.6 2.8 6.7 2 9.7-1.2C17.8 12.3 20.2 7.2 21.5 2.6Z"/><path d="M4 18.8C8.5 13.9 13.1 9.4 20.8 3.7" fill="none" stroke="#fff" stroke-width="1.15" stroke-linecap="round"/>' ) },
    };
    PRESET_ROWS.forEach((row, rowIndex) => {
      const rowLabel = document.createElement("span");
      rowLabel.className = "row-label";
      rowLabel.textContent = row;
      this._palette.appendChild(rowLabel);

      for (let column = 1; column <= 10; column += 1) {
        const effect = `${row}${column}`;
        const colorIndex = rowIndex * 10 + column - 1;
        const button = document.createElement("button");
        button.className = "swatch";
        button.type = "button";
        button.dataset.effect = effect;
        const marker = markers[effect];
        if (marker) {
          button.style.setProperty("--marker-color", marker.color);
          const markerIcon = document.createElement("span");
          markerIcon.className = "marker-icon";
          markerIcon.innerHTML = marker.svg;
          markerIcon.setAttribute("aria-hidden", "true");
          button.appendChild(markerIcon);
        }
        button.style.setProperty("--swatch", COLOR_SWATCHES[colorIndex]);
        button.title = effect;
        button.setAttribute("role", "gridcell");
        button.setAttribute("aria-label", `Color ${effect}`);
        button.setAttribute("aria-pressed", "false");
        button.addEventListener("click", () => this._selectEffect(effect));
        this._palette.appendChild(button);
      }
    });

    this.shadowRoot.querySelectorAll(".mode").forEach((button) => {
      button.addEventListener("click", () => this._selectMode(button.dataset.mode));
    });
    this.shadowRoot.querySelector(".decrease").addEventListener("click", () => this._changeIntensity(-5));
    this.shadowRoot.querySelector(".increase").addEventListener("click", () => this._changeIntensity(5));
    this._intensityInput.addEventListener("input", (event) => {
      this._intensityDragging = true;
      this._showIntensity(Number(event.target.value));
    });
    this._intensityInput.addEventListener("change", (event) => {
      this._intensityDragging = false;
      this._sendIntensity(Number(event.target.value));
    });
  }

  _update() {
    if (!this._hass || !this._palette) return;
    const state = this._hass.states[this.config.entity];
    if (!state) {
      this._showError(`Entity ${this.config.entity} was not found.`);
      return;
    }

    const attributes = state.attributes || {};
    const availableEffects = new Set(attributes.options || []);
    const objectId = this.config.entity.split(".")[1].replace(/_preset$/, "");
    const colorEntity = this.config.color_entity || `sensor.${objectId}_manual_color`;
    const colorState = this._hass.states[colorEntity];
    const reportedPreset = colorState ? presetFromColorCode(colorState.state) : null;
    const currentEffect = reportedPreset || state.state;
    const modeEntity = this._findModeEntity();
    const modeState = modeEntity ? this._hass.states[modeEntity]?.state : null;
    const currentMode = modeState || "manual";
    const autoMode = currentMode === "auto";
    this._intensityInput.disabled = autoMode;
    this._intensityInput.title = autoMode ? "Switch to Manual mode to adjust intensity." : "";
    this.shadowRoot.querySelectorAll(".step").forEach((button) => {
      button.disabled = autoMode;
      button.title = autoMode ? "Switch to Manual mode to adjust intensity." : "";
    });
    const scheduleEntity = this.config.schedule_entity || `sensor.${objectId}_schedule_data`;
    const scheduleState = this._hass.states[scheduleEntity] || Object.entries(this._hass.states)
      .find(([entityId]) => entityId.startsWith("sensor.") && entityId.endsWith(`_${objectId}_schedule_data`))?.[1];
    this._scheduleRaw = scheduleState?.attributes?.raw_schedule || null;
    const intensityState = this._hass.states[this._manualIntensityEntity()]
      || this._hass.states[this.config.power_entity];
    const reportedIntensity = intensityState ? Number(intensityState.state) : NaN;
    const manualIntensity = Number.isFinite(reportedIntensity)
      ? Math.max(0, Math.min(100, reportedIntensity))
      : null;
    if (currentMode === "auto") {
      this._clearPendingIntensity();
    } else if (this._pendingIntensity != null && manualIntensity != null
      && Math.abs(manualIntensity - this._pendingIntensity) <= 1) {
      this._clearPendingIntensity();
    }
    const intensity = currentMode === "auto"
      ? (this._currentScheduledIntensity() ?? manualIntensity)
      : (this._pendingIntensity ?? manualIntensity);
    const channelValues = [0, 1, 2, 3].map((channel) => {
      const channelState = this._hass.states[`sensor.${objectId}_pwm_channel_${channel}`];
      const value = channelState ? Number(channelState.state) : NaN;
      return Number.isFinite(value) ? Math.max(0, Math.min(100, value)) : null;
    });

    this.shadowRoot.querySelector(".error")?.remove();
    this.shadowRoot.querySelector(".content").hidden = false;
    const activePreset = currentEffect;
    this._intensityLabel.textContent = "Intensity";
    this.shadowRoot.querySelector(".intensity-value-heading").textContent = intensity == null
      ? "—"
      : `${Math.round(intensity)}%`;
    if (!this._intensityDragging && intensity != null) this._showIntensity(intensity);
    this._renderSpectrum(channelValues, intensity ?? 0);
    this._renderSchedule();

    this._palette.querySelectorAll(".swatch").forEach((button) => {
      const supported = availableEffects.has(button.dataset.effect);
      button.disabled = !supported;
      button.setAttribute("aria-pressed", String(button.dataset.effect === activePreset));
    });

    this.shadowRoot.querySelectorAll(".mode").forEach((button) => {
      const supported = !["superior", "clone"].includes(button.dataset.mode);
      button.disabled = !modeEntity || !supported;
      button.setAttribute("aria-pressed", String(button.dataset.mode === currentMode));
      button.title = !supported
        ? "This mode is not supported by the integration yet."
        : button.disabled && !modeEntity
          ? "Set mode_entity in the card configuration to control this mode."
          : "";
    });
  }

  _showError(message) {
    const content = this.shadowRoot.querySelector(".content");
    content.hidden = true;
    let error = this.shadowRoot.querySelector(".error");
    if (!error) {
      error = document.createElement("div");
      error.className = "error";
      this.shadowRoot.querySelector("ha-card").appendChild(error);
    }
    error.textContent = message;
  }

  _findModeEntity() {
    if (this.config.mode_entity) return this.config.mode_entity;
    const objectId = this.config.entity.split(".")[1];
    const baseName = objectId.replace(/_preset$/, "");
    const candidate = `select.${baseName}_mode`;
    return this._hass.states[candidate] ? candidate : null;
  }

  _currentMode() {
    const modeEntity = this._findModeEntity();
    return modeEntity ? this._hass.states[modeEntity]?.state : null;
  }

  _currentScheduledIntensity() {
    if (!this._scheduleRaw) return null;
    const points = this._scheduleRaw.split(":").filter(Boolean).map((row) => {
      const [hour, minute, , , intensity] = row.split(";").map(Number);
      if (![hour, minute, intensity].every(Number.isFinite)
        || hour < 0 || hour > 23 || minute < 0 || minute > 59
        || intensity < 0 || intensity > 100) return null;
      return { minute: hour * 60 + minute, intensity };
    }).filter(Boolean).sort((a, b) => a.minute - b.minute);
    if (points.length < 2) return null;

    const now = new Date();
    const minuteNow = now.getHours() * 60 + now.getMinutes();
    let previous = points.filter((point) => point.minute <= minuteNow).at(-1);
    let next = points.find((point) => point.minute > minuteNow);
    if (!previous) previous = { ...points.at(-1), minute: points.at(-1).minute - 1440 };
    if (!next) next = { ...points[0], minute: points[0].minute + 1440 };
    const fraction = (minuteNow - previous.minute) / (next.minute - previous.minute);
    return Math.round(previous.intensity + (next.intensity - previous.intensity) * fraction);
  }

  _manualIntensityEntity() {
    if (this.config.manual_intensity_entity) return this.config.manual_intensity_entity;
    const baseName = this.config.entity.split(".")[1].replace(/_preset$/, "");
    return `sensor.${baseName}_manual_intensity`;
  }

  _currentEffect() {
    const state = this._hass.states[this.config.entity];
    return state?.state || "A1";
  }

  _selectEffect(effect) {
    this._hass.callService("select", "select_option", {
      entity_id: this.config.entity,
      option: effect,
    });
  }

  _currentIntensity() {
    return Number(this._intensityInput.value || 30);
  }

  _showIntensity(value) {
    const percent = Math.max(0, Math.min(100, Math.round(value)));
    this._intensityInput.value = String(percent);
    this._intensityValue.textContent = `${percent}%`;
    this._intensityHeading.textContent = `${percent}%`;
  }

  _renderSchedule() {
    const container = this.shadowRoot?.querySelector(".schedule");
    const svg = this.shadowRoot?.querySelector(".schedule-svg");
    if (!container || !svg || !this._scheduleRaw) {
      if (container) container.hidden = true;
      return;
    }

    const points = this._scheduleRaw.split(":").filter(Boolean).map((row) => {
      const [hour, minute, , colorCode, intensity] = row.split(";").map(Number);
      if (![hour, minute, colorCode, intensity].every(Number.isFinite)
        || hour < 0 || hour > 23 || minute < 0 || minute > 59
        || colorCode < 0 || colorCode >= COLOR_SWATCHES.length
        || intensity < 0 || intensity > 100) return null;
      return {
        minuteOfDay: hour * 60 + minute,
        intensity,
        color: COLOR_SWATCHES[colorCode],
      };
    }).filter(Boolean).sort((a, b) => a.minuteOfDay - b.minuteOfDay);

    if (points.length < 2) {
      container.hidden = true;
      return;
    }

    const left = 50;
    const right = 408;
    const top = 14;
    const bottom = 174;
    const width = right - left;
    const height = bottom - top;
    const xFor = (minute) => left + (minute / 1440) * width;
    const yFor = (value) => bottom - (Math.max(0, Math.min(100, value)) / 100) * height;
    const grid = [0, 20, 40, 60, 80, 100].map((value) => {
      const y = yFor(value);
      return `<line x1="${left}" y1="${y}" x2="${right}" y2="${y}" stroke="#d3d3d3" stroke-width=".7"/><line x1="${left - 7}" y1="${y}" x2="${left}" y2="${y}" stroke="#777"/><text x="${left - 10}" y="${y + 4}" text-anchor="end">${value}%</text>`;
    }).join("");
    const timeTicks = [0, 4, 8, 12, 16, 20, 24].map((hour) => {
      const x = left + (hour / 24) * width;
      const label = `${hour}:00`;
      return `<line x1="${x}" y1="${bottom}" x2="${x}" y2="${bottom + 6}" stroke="#154cff"/><text x="${x}" y="${bottom + 24}" text-anchor="middle">${label}</text>`;
    }).join("");
    const segments = points.slice(1).map((point, index) => {
      const previous = points[index];
      const x1 = xFor(previous.minuteOfDay);
      const y1 = yFor(previous.intensity);
      const x2 = xFor(point.minuteOfDay);
      const y2 = yFor(point.intensity);
      const gradientId = `schedule-segment-${index}`;
      return `<defs><linearGradient id="${gradientId}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" gradientUnits="userSpaceOnUse"><stop stop-color="${previous.color}"/><stop offset="1" stop-color="${point.color}"/></linearGradient></defs><line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="url(#${gradientId})" stroke-width="3"/><line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#777" stroke-width="1.1" opacity=".8"/>`;
    }).join("");
    const nodes = points.map((point) => `<circle cx="${xFor(point.minuteOfDay)}" cy="${yFor(point.intensity)}" r="7" fill="${point.color}" stroke="#777" stroke-width="1.2"/>`).join("");
    const now = new Date();
    const minuteNow = now.getHours() * 60 + now.getMinutes();
    const nowX = xFor(minuteNow);
    const currentLabel = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;

    svg.innerHTML = `<g font-family="Arial, sans-serif" font-size="11" fill="#111">${grid}<line x1="${left}" y1="${top}" x2="${left}" y2="${bottom}" stroke="#154cff" stroke-width="1.3"/><line x1="${left}" y1="${bottom}" x2="${right}" y2="${bottom}" stroke="#154cff" stroke-width="1.3"/>${timeTicks}</g><g>${segments}${nodes}</g><line x1="${nowX}" y1="${top}" x2="${nowX}" y2="${bottom}" stroke="#24aa65" stroke-width="2"/><text x="${Math.min(right - 3, Math.max(left + 3, nowX))}" y="10" text-anchor="${nowX > right - 35 ? "end" : "middle"}" font-family="Arial, sans-serif" font-size="10" font-weight="700" fill="#16884d">${currentLabel}</text>`;
    container.hidden = false;
  }

  _renderSpectrum(channels, intensity) {
    const container = this.shadowRoot.querySelector(".spectrum");
    if (channels.some((value) => value == null)) {
      container.hidden = true;
      return;
    }

    const svg = this.shadowRoot.querySelector(".spectrum-svg");
    const left = 44;
    const right = 408;
    const top = 12;
    const bottom = 177;
    const width = right - left;
    const height = bottom - top;
    const values = [];
    let maxValue = 0;

    for (let sample = 0; sample <= width; sample += 1) {
      const wavelength = 400 + (sample / width) * 300;
      let value = 0;
      for (let channel = 0; channel < 4; channel += 1) {
        for (let band = 0; band < 7; band += 1) {
          const amplitude = (channels[channel] / 100) * (H_BAR_F_SPECTRUM.amplitudes[channel][band] / 100);
          const spread = H_BAR_F_SPECTRUM.widths[channel][band] * 0.6017;
          const distance = wavelength - H_BAR_F_SPECTRUM.wavelengths[band];
          value += amplitude * Math.exp(-(distance * distance) / (spread * spread));
        }
      }
      values.push(value);
      if (value > maxValue) maxValue = value;
    }

    if (maxValue <= 0) {
      container.hidden = true;
      return;
    }

    const peakPercent = Math.max(0, Math.min(100, Number(intensity) || 0)) * 0.8;
    const points = values.map((value, index) => {
      const x = left + index;
      const y = bottom - (value / maxValue) * (peakPercent / 100) * height;
      return `${index === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
    }).join(" ");
    const area = `${points} L${right} ${bottom} L${left} ${bottom} Z`;
    const grid = [0, 25, 50, 75, 100].map((tick) => {
      const y = bottom - (tick / 100) * height;
      return `<line x1="${left}" y1="${y}" x2="${right}" y2="${y}" class="grid"/><line x1="${left - 7}" y1="${y}" x2="${left}" y2="${y}" class="tick"/><text x="${left - 10}" y="${y + 4}" text-anchor="end">${tick}%</text>`;
    }).join("");
    const wavelengths = [400, 450, 500, 550, 600, 650, 700].map((tick) => {
      const x = left + ((tick - 400) / 300) * width;
      return `<line x1="${x}" y1="${bottom}" x2="${x}" y2="${bottom + 6}" class="tick"/><text x="${x}" y="${bottom + 24}" text-anchor="middle">${tick}</text>`;
    }).join("");

    svg.innerHTML = `<defs><linearGradient id="spectrum-fill" x1="0" x2="1"><stop offset="0%" stop-color="#5424a8"/><stop offset="17%" stop-color="#0877d1"/><stop offset="38%" stop-color="#00c7c7"/><stop offset="52%" stop-color="#19c856"/><stop offset="67%" stop-color="#e4d700"/><stop offset="82%" stop-color="#ff8a00"/><stop offset="100%" stop-color="#d60000"/></linearGradient></defs><g class="axes">${grid}<line x1="${left}" y1="${top}" x2="${left}" y2="${bottom}" class="axis-line"/><line x1="${left}" y1="${bottom}" x2="${right}" y2="${bottom}" class="axis-line"/>${wavelengths}<text x="${(left + right) / 2}" y="226" text-anchor="middle">Wavelength [nm]</text></g><path d="${area}" fill="url(#spectrum-fill)" stroke="#111" stroke-width="1.2" stroke-linejoin="round"/>`;
    svg.querySelectorAll("text").forEach((node) => {
      node.setAttribute("font-size", "11");
      node.setAttribute("font-family", "Arial, sans-serif");
      node.setAttribute("fill", "currentColor");
    });
    svg.querySelectorAll(".grid").forEach((node) => {
      node.setAttribute("stroke", "#d3d3d3");
      node.setAttribute("stroke-width", "0.6");
    });
    svg.querySelectorAll(".tick").forEach((node) => {
      node.setAttribute("stroke", "#154cff");
      node.setAttribute("stroke-width", "1");
    });
    svg.querySelectorAll(".axis-line").forEach((node) => {
      node.setAttribute("stroke", "#154cff");
      node.setAttribute("stroke-width", "1.3");
    });
    container.hidden = false;
  }

  _changeIntensity(delta) {
    if (this._currentMode() === "auto") return;
    const next = Math.max(0, Math.min(100, (this._pendingIntensity ?? this._currentIntensity()) + delta));
    this._showIntensity(next);
    this._sendIntensity(next);
  }

  _sendIntensity(brightness) {
    if (this._currentMode() === "auto") return;
    const percent = Math.max(0, Math.min(100, Math.round(brightness)));
    this._clearPendingIntensity();
    this._pendingIntensity = percent;
    this._showIntensity(percent);
    this._pendingIntensityTimer = window.setTimeout(() => {
      this._clearPendingIntensity();
      this._update();
    }, 20_000);
    this._hass.callService("number", "set_value", {
      entity_id: this.config.power_entity,
      // number.set_value validates this as a JSON number; passing a string
      // can be rejected by Home Assistant before the integration sees it.
      value: percent,
    }).catch((error) => {
      console.error("Unable to set Skylight intensity", error);
      this._clearPendingIntensity();
      this._update();
    });
  }

  _clearPendingIntensity() {
    if (this._pendingIntensityTimer) {
      window.clearTimeout(this._pendingIntensityTimer);
      this._pendingIntensityTimer = null;
    }
    this._pendingIntensity = null;
  }

  _selectMode(mode) {
    if (mode === "manual") {
      if (this._findModeEntity()) {
        this._hass.callService("select", "select_option", {
          entity_id: this._findModeEntity(),
          option: "manual",
        });
      }
    } else if (mode === "off") {
      const modeEntity = this._findModeEntity();
      if (modeEntity) {
        this._hass.callService("select", "select_option", {
          entity_id: modeEntity,
          option: "off",
        });
      }
    } else {
      const modeEntity = this._findModeEntity();
      if (!modeEntity) return;
      this._hass.callService("select", "select_option", {
        entity_id: modeEntity,
        option: mode,
      });
    }
  }

}

if (!customElements.get("skylight-color-card")) {
  customElements.define("skylight-color-card", SkylightColorCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "skylight-color-card")) {
  window.customCards.push({
    type: "skylight-color-card",
    name: "Skylight color palette",
    description: "Color grid and intensity control for Skylight lamps",
    preview: true,
  });
}
