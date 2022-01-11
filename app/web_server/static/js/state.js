const State = {
  OFF: "off",
  ON: "on",
  ALARM: "alarm",
  SILENCED: "silenced",
  UNKNOWN: "unknown",
  ERROR: "error",
}
Object.freeze(State);

class StatusUpdate {
  /**
   * Constructor
   * @param {number} timeStamp 
   * @param {State} state 
   * @param {number} initialAlarm 
   * @param {number} silencedTill 
   */
  constructor(timeStamp, state, initialAlarm, silencedTill) {
    this.timeStamp = timeStamp;
    this.initialAlarm = initialAlarm;
    this.silencedTill = silencedTill;
    this.state;
    switch (state) {
      case "on":
        this.state = State.ON;
        break;
      case "off":
        this.state = State.OFF
        break;
      case "alarm":
        this.state = State.ALARM;
        break;
      case "silenced":
        this.state = State.SILENCED;
        break;
      case "unknown":
        this.state = State.UNKNOWN;
        break;
      default:
        throw new Error(`Unknown state: ${state}`);
    }
  }
}

class System {
  #lastUpdate = 0.0;
  #state = State.UNKNOWN;
  /** @type {?WebSocket} */
  #statusConnection = null;
  #configListeners = [];
  /** @type {(function(Error): void)[]} */
  #errorListeners = [];
  /** @type {(function(State): void)[]} */
  #onChangeListeners = [];
  #host;
  /**
   * Constructor
   * @param {string} host Host name
   */
  constructor(host) {
    this.#host = host;
    // Start Watchdog
    setInterval(() => {
      this.#checkWatchdog();
    }, 2000);
  }

  run() {
    this.#initWebsocket();
    this.#initConfigUpdate();
  }

  /**
   * Send a silence command
   * @param {number} durationSeconds Silence duration in seconds
   * @returns {Promise<void>} On success
   */
  sendSilenceCommand(durationSeconds) {
    return new Promise((resolve, reject) => {
      if (this.#state in [State.ON, State.SILENCED]) {
        reject(new Error("The system is not in the 'ON' state"));
      } else {
        try {
          const command = JSON.stringify(
            {
              command: "silence",
              data: {
                "silenceFor": parseInt(durationSeconds) * 60
              }
            }
          )
          this.#sendMessage(command);
          resolve();
        } catch (error) {
          reject(new Error(error));
        }
      }
    });
  }

  /**
   * Send a silence command
   * @returns {Promise<void>} On success
   */
  sendUnsilenceCommand() {
    return new Promise((resolve, reject) => {
      if (this.#state !== State.SILENCED) {
        reject(new Error("The system is not in the 'SILENCED' state"));
      }
      else {
        try {
          const command = JSON.stringify(
            {
              command: "silence",
              data: { "silenceFor": 0 }
            }
          )
          this.#sendMessage(command);
          resolve();
        } catch (error) {
          reject(new Error(error));
        }
      }
    })
  }

  /**
   * Send a test command
   * @returns {Promise<void>} On success
   */
  sendTestCommand() {
    return new Promise((resolve, reject) => {
      try {
        const command = JSON.stringify(
          {
            command: "test",
            data: {
              excluded: []
            }
          }
        )
        this.#sendMessage(command);
        resolve();
      } catch (error) {
        reject(new Error(error));
      }
    })
  }

  /**
   * Send an update command
   * @param {Object} data 
   * @returns {Promise<void>} On success
   */
  sendUpdateConfigCommand(data) {
    return new Promise((resolve, reject) => {
      try {
        const command = JSON.stringify({
          command: "config_update",
          data: {
            config: data
          }
        })
        this.#sendMessage(command);
        resolve()
      }
      catch (error) {
        reject(new Error(error));
      }
    })
  }

  /**
   * Add an event listener
   * @param {string} event 
   * @param {(function(): void| function(StatusUpdate): void)} func 
   */
  addListener(event, func) {
    switch (event) {
      case "onChange":
        this.#onChangeListeners.push(func);
        break;
      case "error":
        this.#errorListeners.push(func);
        break;
      default:
        throw new Error(`Unknown event ${event}`)
    }
  }
  #initWebsocket() {
    this.#statusConnection = new WebSocket(`ws://${this.#host}:9876/`);
    this.#statusConnection.onmessage = (message) => {
      try {
        const data = JSON.parse(message.data);
        if ("error" in data) {
          // TODO: The error is a messy object
          throw new Error(JSON.stringify(data.error));
        } else if ("status" in data) {
          //TODO: Needed?
        } else if ("state" in data) {
          const { timeStamp, state, initialAlarm, silencedTill } = data;
          const newStatus = new StatusUpdate(timeStamp, state, initialAlarm, silencedTill);
          this.#state = newStatus.state;
          this.#handleOnChange(newStatus);
          this.#lastUpdate = newStatus.timeStamp;
        } else {
          throw new Error(`Unkown message: ${data}`);
        }
      } catch (error) {
        this.#handleError(error);
      }
    }
    this.#statusConnection.onerror = (evt) => {
      console.error(evt);
      this.#handleError(new Error("Websocket connection error"));
    }
  }

  #initConfigUpdate() {

  }

  #checkWatchdog() {
    const now = Math.round(new Date().getTime() / 1000) // milliseconds to seconds
    if (now - this.#lastUpdate >= 3.0) {
      this.#state = State.UNKNOWN;
      this.#handleOnChange({ state: State.UNKNOWN });
      this.#initWebsocket();
    }
  }

  #sendMessage(message) {
    if (this.#statusConnection.readyState !== 1) {
      throw new Error("The connnection is closed");
    }
    this.#statusConnection.send(message);
  }

  #handleError(error) {
    console.error(error);
    this.#errorListeners.forEach(callback => callback(error));
  }

  #handleOnChange(state) {
    this.#onChangeListeners.forEach(callback => callback(state));
  }

}

export { System, StatusUpdate, State }