import { State, StatusUpdate } from "./state.js";

/**
 * @typedef {Object} Components
 * @property {HTMLElement} cameraStatusEl
 * @property {HTMLElement} connectionStatusEl
 * @property {HTMLElement} systemStatusEl
 * @property {HTMLElement} timeDisplayEl
 * @property {HTMLElement} lastAlarmEl
 */

const UNKNOWN_STATUS = new StatusUpdate(0, State.UNKNOWN, 0, 0);


class StatusOverlay {
  #cameraStatusEl;
  #connectionStatusEl;
  #systemStatusEl;
  #timeDisplayEl;
  #lastAlarmEl;
  #currentStatus = UNKNOWN_STATUS;
  #videoActive = false;
  /** @type {?number} */
  #cameraTextIntervalHandle = null;
  static LAST_ALARM_MAX_S = 60 * 30; // 30 minutes
  /**
   * Constructor
   * @param {Components} components Overlay components
   */
  constructor(components) {
    this.#cameraStatusEl = components.cameraStatusEl;
    this.#connectionStatusEl = components.connectionStatusEl;
    this.#systemStatusEl = components.systemStatusEl;
    this.#timeDisplayEl = components.timeDisplayEl;
    this.#lastAlarmEl = components.lastAlarmEl;
    this.update(UNKNOWN_STATUS);
    this.#timeDisplayEl.innerHTML = dateToTimeString(new Date());
    setInterval(() => {
      this.#timeDisplayEl.innerHTML = dateToTimeString(new Date());
    }, 1000);
  }

  /**
   * 
   * @param {StatusUpdate} status New status 
   */
  update(status) {
    this.#currentStatus = status;
    this.updateCameraStatus(this.#videoActive);
    this.#updateConnectionStatus(status);
    this.#updateSystemStatus(status);
    this.#updateLastAlarm(status);
  }

  /**
   * Update camera status
   * @param {boolean} videoActive 
   */
  updateCameraStatus(videoActive) {
    this.#videoActive = videoActive;
    if (this.#currentStatus.state !== State.UNKNOWN) {
      if (!videoActive) {
        if (this.#cameraTextIntervalHandle) {
          clearInterval(this.#cameraTextIntervalHandle);
          this.#cameraTextIntervalHandle = null;
        }
        this.#cameraStatusEl.innerHTML = "";
      } else {
        if (this.#cameraTextIntervalHandle === null) {
          this.#cameraStatusEl.innerHTML = "Live";
          this.#cameraTextIntervalHandle = setInterval(() => {
            if (this.#cameraStatusEl.innerHTML === "Live") {
              this.#cameraStatusEl.innerHTML = "";
            } else {
              this.#cameraStatusEl.innerHTML = "Live";
            }
          }, 1000);
        }
      }
    }
  }
  /**
   * Update the connection status
   * @param {StatusUpdate} status 
   */
  #updateConnectionStatus(status) {
    if (status.state === State.UNKNOWN) {
      this.#connectionStatusEl.innerHTML = "OFFLINE";
    } else {
      this.#connectionStatusEl.innerHTML = "";
    }
  }

  /**
   * Update the system status
   * @param {StatusUpdate} status 
   */
  #updateSystemStatus(status) {
    switch (status.state) {
      case State.ON: {
        this.#systemStatusEl.innerHTML = `
        <span class="icon is-medium">
          <svg width="90%" height="90%">
            <use xlink:href="/static/images/on.svg#bell"/>
          </svg>
        </span>
        `;
        this.#systemStatusEl.style.color = "green";
      }
        break;
      case State.OFF: {
        this.#systemStatusEl.innerHTML = `
        <span class="icon is-medium">
          <svg width="90%" height="90%">
            <use xlink:href="/static/images/silenced.svg#silenced-bell"/>
          </svg>
        </span>
        `;
        this.#systemStatusEl.style.color = "white";
      }
        break;
      case State.ALARM: {
        this.#systemStatusEl.innerHTML = `
        <span class="icon is-medium">
          <svg width="90%" height="90%">
            <use xlink:href="/static/images/on.svg#bell"/>
          </svg>
        </span>
        `;
        this.#systemStatusEl.style.color = "red";
      }
        break;
      case State.SILENCED: {
        let silencedTill = new Date(status.silencedTill * 1000);
        this.#systemStatusEl.innerHTML = `
        <span class="icon is-medium">
          <svg width="90%" height="90%">
            <use xlink:href="/static/images/silenced.svg#silenced-bell"/>
          </svg>
        </span>
        ${dateToTimeString(silencedTill)}
        `;
        this.#systemStatusEl.style.color = "yellow";
      }
        break;
      case State.Error:
        break;
      case State.UNKNOWN:
        break;
      default:
        throw new Error("Unknown state: " + status.state);
    }
  }

  /**
   * Update the last alarm display
   * @param {StatusUpdate} status 
   */
  #updateLastAlarm(status) {
    const now = Date.now() / 1000.0;
    const seconds_ago = Math.abs(status.initialAlarm - now).toFixed(0);
    if (seconds_ago < StatusOverlay.LAST_ALARM_MAX_S) {
      this.#lastAlarmEl.innerHTML = secondsToTineString(seconds_ago);
      this.#lastAlarmEl.style.color = "red";
    } else {
      this.#lastAlarmEl.innerHTML = "";
    }
  }
}


/* Helpers */


/**
 * Convert Date object to time string representation
 * @param {Date} date 
 */
const dateToTimeString = (date) => {
  const hours = date.getHours();
  const minutes = date.getMinutes();
  let hoursStr = hours.toString();
  let minutesStr = minutes.toString();
  if (hours < 10) {
    hoursStr = "0" + hoursStr;
  }
  if (minutes < 10) {
    minutesStr = "0" + minutesStr;
  }
  return hoursStr + ":" + minutesStr;
}


/**
 * Convert seconds to a string representation (MM:SS)
 * @param {number} seconds 
 */
const secondsToTineString = (elapsedSeconds) => {
  let minutes = Math.floor(elapsedSeconds / 60);
  let seconds = Math.floor(elapsedSeconds % 60);
  const secondsStr = (seconds < 10 ? "0" + seconds : seconds);
  return minutes + ":" + secondsStr;
}

export { StatusOverlay };