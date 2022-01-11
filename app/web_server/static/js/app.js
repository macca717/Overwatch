import { CameraView } from "./camera-view.js";
import { System, State } from "./state.js";
import { StatusOverlay } from "./status-overlay.js";

/** @const {number} */
const DEFAULT_SILENCE_DURATION = 15;
/** @const {number} */
const WS_PORT = 9876;
/** @const {string} */
const HOST = location.hostname;

const system = new System(HOST);
system.run();

system.addListener("error", (error) => {
  bulmaToast.toast({ message: error.message, type: "is-danger" });
});

/* Status overlay */
const cameraStatusEl = document.querySelector("#camera-status-text");
const connectionStatusEl = document.querySelector("#connection-status-text");
const systemStatusEl = document.querySelector("#system-status-text");
const timeDisplayEl = document.querySelector("#time-display");
const lastAlarmEl = document.querySelector("#last-alarm-text");
const overlay = new StatusOverlay(
  {
    cameraStatusEl: cameraStatusEl,
    connectionStatusEl: connectionStatusEl,
    systemStatusEl: systemStatusEl,
    timeDisplayEl: timeDisplayEl,
    lastAlarmEl: lastAlarmEl,
  }
)
system.addListener("onChange", (status) => {
  overlay.update(status);
});

/* Camera */

const liveView = document.querySelector("#live-img");
const videoToggleSwitch = document.querySelector("#videoToggleSwitch");
let cameraView = new CameraView(`http://${HOST}:${WS_PORT}/snapshot`, liveView, `ws://${HOST}:${WS_PORT}/raw-video`);
videoToggleSwitch.addEventListener("click", () => {
  overlay.updateCameraStatus(videoToggleSwitch.checked);
  cameraView.toggleVideo();
});



/* Controls */

const silenceBtn = document.querySelector("#silence-btn");
const unsilenceBtn = document.querySelector("#unsilence-btn");
const testBtn = document.querySelector("#test-btn");
const slider = document.querySelector("#silence-slider");
const testConfirmModal = document.querySelector("#test-confirm-modal");
const testConfirmBtn = testConfirmModal.querySelector(".confirm-btn");


[silenceBtn, unsilenceBtn, testBtn, slider].forEach(el => el.disabled = true);

const resetSliderDefault = () => {
  slider.value = DEFAULT_SILENCE_DURATION;
  slider.dispatchEvent(new Event("input"));
}

const setBtnLoading = (btnElement) => {
  btnElement.classList.add("is-loading");
  setTimeout(() => {
    btnElement.classList.remove("is-loading");
  }, 500);
}

silenceBtn.innerHTML = `Silence For ${DEFAULT_SILENCE_DURATION} minutes`;
slider.addEventListener("input", () => {
  silenceBtn.innerHTML = `Silence For ${slider.value} minutes`;
})

silenceBtn.addEventListener("click", () => {
  setBtnLoading(silenceBtn);
  system.sendSilenceCommand(slider.value)
    .then(() => {
      resetSliderDefault();
    })
    .catch(error => {
      bulmaToast.toast({ message: error.message, type: "is-danger" });
    })
});

unsilenceBtn.addEventListener("click", () => {
  setBtnLoading(unsilenceBtn);
  unsilenceBtn.disabled = true;
  system.sendUnsilenceCommand()
    .catch(error => {
      bulmaToast.toast({ message: error.message, type: "is-danger" });
    })
});

testBtn.addEventListener("click", () => {
  testConfirmModal.classList.add("is-active");
  testConfirmModal.querySelector(".cancel-btn").addEventListener("click", () => {
    testConfirmModal.classList.remove("is-active");
  });
});

testConfirmBtn.addEventListener("click", () => {
  system.sendTestCommand()
    .catch(error => {
      bulmaToast.toast({ message: error.message, type: "is-danger" });
    })
    .finally(() => {
      testConfirmModal.classList.remove("is-active");
      setBtnLoading(testBtn);
    })
});

system.addListener("onChange", (status) => {
  switch (status.state) {
    case State.ALARM:
    case State.ON:
      slider.disabled = false;
      silenceBtn.disabled = false;
      unsilenceBtn.disabled = true;
      testBtn.disabled = false;
      break;
    case State.OFF:
      slider.disabled = true;
      silenceBtn.disabled = true;
      unsilenceBtn.disabled = true;
      testBtn.disabled = false;
      break;
    case State.SILENCED:
      slider.disabled = false;
      silenceBtn.disabled = false;
      unsilenceBtn.disabled = false;
      testBtn.disabled = false;
      break;
    case State.UNKNOWN:
      [silenceBtn, unsilenceBtn, testBtn, slider].forEach(el => el.disabled = true);
      bulmaToast.toast({ message: "Attempting to reconnect...", type: "is-danger" });
      break;
    default:
      throw new Error("Unknown state: " + status.state);
  }
});

/* Settings */

class Config {
  #data;
  constructor(data) {
    this.#data = data;
    this.alerters = Object.entries(data.alerters).map(alerter => {
      return {
        name: alerter[0],
        isEnabled: alerter[1].enabled
      }
    });
  }
  get startTime() {
    return this.#data.alerting["start_time"];
  }

  set startTime(startTime) {
    this.#data.alerting["start_time"] = startTime;
  }

  get stopTime() {
    return this.#data.alerting["end_time"];
  }

  set stopTime(stopTime) {
    this.#data.alerting["end_time"] = stopTime;
  }

  /**
   * Update an alerter
   * @param {{name: string, isEnabled: boolean}} data 
   */
  updateAlerter(data) {
    if (data.name in this.#data.alerters) {
      this.#data.alerters[data.name].enabled = data.isEnabled;
    } else {
      throw new Error("Unknown alerter: " + data.name);
    }
  }

  update() {
    return new Promise((resolve, reject) => {
      system.sendUpdateConfigCommand(this.#data)
        .then(() => resolve())
        .catch(error => reject(error));
    })
  }

  /**
   * Fetch the current server configuration
   * @returns {Promise<Config>} The current server configuration
   */
  static fetch() {
    return new Promise((resolve, reject) => {
      fetch(`http://${HOST}:${WS_PORT}/config`, { mode: "cors" })
        .then(response => response.json())
        .then(data => {
          resolve(new Config(data));
        })
        .catch(error => reject(error))
    });
  }
}

const scheduleStartSlider = document.querySelector("#start-schedule-slider");
const scheduleStopSlider = document.querySelector("#stop-schedule-slider");
const startTimeEl = document.querySelector("#start-time");
const stopTimeEl = document.querySelector("#stop-time");
const updateScheduleBtn = document.querySelector("#update-settings-btn");

const alertersEl = document.querySelector("#alerters");
/** @type {?Config} */
let config = null;

const initSettings = () => {
  Config.fetch()
    .then(newConfig => {
      config = newConfig;
      config.alerters.forEach(alerter => {
        const toggle = document.createElement("div");
        toggle.className = "field";
        toggle.innerHTML = `
        <input id="${alerter.name}" type="checkbox" name="${alerter.name}" class="switch is-rounded">
        <label for="${alerter.name}" class="is-capitalized">${alerter.name}</label>
        `
        const alerterSwitch = toggle.querySelector(`#${alerter.name}`);
        alerterSwitch.checked = alerter.isEnabled;
        alerterSwitch.addEventListener("click", () => {
          config.updateAlerter({ name: alerter.name, isEnabled: alerterSwitch.checked });
          config.update()
            .catch(error => {
              bulmaToast.toast({ message: error.message, type: "is-danger" });
            })
        });
        alertersEl.appendChild(toggle);
      })
      startTimeEl.innerHTML = config.startTime;
      scheduleStartSlider.value = convertFromTimeString(config.startTime);
      stopTimeEl.innerHTML = config.stopTime;
      scheduleStopSlider.value = convertFromTimeString(config.stopTime);
    })
}

const convertToTimeString = (value) => {
  const hours = Math.floor(value / 60);
  const minutes = value % 60;
  const hoursString = (hours < 10) ? "0" + hours.toString() : hours.toString();
  const minutesString = (minutes < 10) ? "0" + minutes.toString() : minutes.toString();
  return `${hoursString}:${minutesString}`
}

const convertFromTimeString = (time) => {
  const strArray = time.split(":");
  const hours = parseInt(strArray[0]);
  const minutes = parseInt(strArray[1])
  return hours * 60 + minutes;
}


scheduleStartSlider.addEventListener("input", () => {
  startTimeEl.innerHTML = convertToTimeString(scheduleStartSlider.value);
})

scheduleStopSlider.addEventListener("input", () => {
  stopTimeEl.innerHTML = convertToTimeString(scheduleStopSlider.value);
})

updateScheduleBtn.addEventListener("click", () => {
  setBtnLoading(updateScheduleBtn);
  config.startTime = convertToTimeString(scheduleStartSlider.value);
  config.stopTime = convertToTimeString(scheduleStopSlider.value);
  config.update()
    .catch(err => bulmaToast.toast({ message: err.message, type: "is-danger" }));
})


initSettings();