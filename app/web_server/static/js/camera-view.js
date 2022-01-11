
const Mode = {
  Still: "still",
  Video: "video",
}
Object.freeze(Mode);

class CameraView {
  /** @type {string} */
  #imageUrl;
  /** @type {Mode} */
  #mode = Mode.Still;
  /** @type {HTMLImageElement} */
  #imageEl;
  /** @type {number} */
  #still_handle;
  /** @type {string} */
  #videoWSUrl;
  /** @type {WebSocket} */
  #videoWs;
  /** @type {(function(): void)[]} */
  #onOpenSubscribers = [];
  /** @type {(function(Error): void)[]} */
  #onErrorSubscribers = [];
  /** @type {(function(): void)[]} */
  #onCloseSubscribers = [];

  /**
   * Constructor
   * @param {string} imageUrl 
   * @param {HTMLImageElement} imageEl
   * @param {string} videoWSUrl 
   */
  constructor(imageUrl, imageEl, videoWSUrl) {
    this.#imageUrl = imageUrl;
    this.#imageEl = imageEl;
    this.#imageEl.src = imageUrl;
    this.#videoWSUrl = videoWSUrl;
    this.#setStillImageTimer();
  }

  toggleVideo() {
    if (this.#mode === Mode.Still) {
      this.#mode = Mode.Video;
      clearInterval(this.#still_handle);
      this.#videoWs = new WebSocket(this.#videoWSUrl);
      /** @type {?string} */
      let imageURL;
      this.#videoWs.onmessage = (msg) => {
        const arrayBuffer = msg.data;
        if (imageURL) {
          URL.revokeObjectURL(imageURL)
        }
        imageURL = URL.createObjectURL(new Blob([arrayBuffer]));

        this.#imageEl.src = imageURL;
      };
      this.#videoWs.onopen = () => {
        this.#onOpenSubscribers.forEach(listener => {
          listener();
        })
      };
      this.#videoWs.onclose = (evt) => {
        this.#onCloseSubscribers.forEach(listener => {
          listener(evt);
        })
      }
      this.#videoWs.error = (error) => {
        console.error(error);
        this.#dispatchError(error);
      }

    } else {
      this.#mode = Mode.Still;
      this.#videoWs.close();
      this.#setStillImageTimer();
    }
  }

  /**
   * Subscribe to camera events.
   * @param {string} event 
   * @param {Listener} listener 
   */
  addListener(event, listener) {
    switch (event) {
      case 'error':
        this.#onErrorSubscribers.push(listener);
        break;
      case 'open':
        this.#onOpenSubscribers.push(listener);
        break;
      case 'close':
        this.#onCloseSubscribers.push(listener);
        break;
      default:
        throw new Error(`Unknown event ${event}`);
    }
  }

  /**
   * Dispatch error event
   * @param {Error} error 
   */
  #dispatchError(error) {
    this.#onErrorSubscribers.forEach(listener => {
      listener(error);
      this.#imageEl.src = "/static/images/black.png";
    });
  }

  #setStillImageTimer() {
    this.#still_handle = setInterval(() => {
      fetch(this.#imageUrl, { cache: "no-cache", mode: "cors" })
        .then((response => response.blob()))
        .then(blob => {
          this.#imageEl.src = URL.createObjectURL(blob);
        })
        .catch((error) => {
          console.error(error);
          this.#dispatchError(error);
        })
    }, 1000);
  }
}

export { CameraView }