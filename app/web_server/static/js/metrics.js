import { PRIMARY_COLOR } from "./constants.js"

/** @typedef {function(): void} Listener */
class Metrics {
  /**
   * Constructor
   * @param {string} metricsWSURL 
   */
  constructor(metricsWSURL) {
    this.wsURL = metricsWSURL;
    /** @type {Listener[]} */
    this.listeners = [];
    this.conn = new WebSocket(this.wsURL);
    this.conn.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      this.listeners.forEach(cb => {
        if (cb) {
          cb(data);
        }
      });
    };
    this.conn.onerror = (err) => {
      //TODO:
      console.error(err);
    };
  }

  /**
   * Add a callback function
   * @param {Listener} callback 
   */
  addListener(callback) {
    this.listeners.push(callback);
  }
}


class BasePlot {
  constructor() {
    this.data = [];
    this.maxLength = 600;
  }
  update(data) {
    this.data.push(data);
    if (this.data.length > this.maxLength) {
      this.data.shift();
    }
  }
}

class LoopTimePlot extends BasePlot {
  constructor(plotID) {
    super();
    this.plotID = plotID;
    Plotly.newPlot(plotID, [{
      y: this.data,
      mode: 'lines',
      line: { color: PRIMARY_COLOR },
      fill: 'tozeroy',
    }], {
      title: "Loop Time",
      yaxis: {
        range: [0, 1000],
        autorange: true,
        title: {
          text: "ms"
        }
      },
      xaxis: {
        title: {
          text: "Time (s)"
        }
      },
    }, {
      responsive: true,
      displayModeBar: false
    });
  }
  update(data) {
    super.update(data);
    Plotly.update(this.plotID,
      {
        x: [new Date()],
        y: [this.data]
      }
    );
  }
}

class CpuUsagePlot extends BasePlot {
  constructor(plotID) {
    super();
    this.plotID = plotID;
    Plotly.newPlot(this.plotID, [{
      y: [1],
      mode: 'lines',
      line: { color: PRIMARY_COLOR },
      fill: 'tozeroy',
    }], {
      title: "CPU Usage",
      yaxis: {
        range: [0, 100],
        autorange: false,
        title: {
          text: "%"
        }
      },
      xaxis: {
        title: {
          text: "Time (s)"
        }
      },
    }, {
      responsive: true,
      displayModeBar: false
    });
  }
  update(data) {
    super.update(data);
    Plotly.update(this.plotID, {
      y: [this.data]
    })
  }
}

class MemoryUsagePlot extends BasePlot {
  constructor(plotID) {
    super();
    this.plotID = plotID;
    Plotly.newPlot(this.plotID, [{
      y: [1],
      mode: 'lines',
      line: { color: PRIMARY_COLOR },
      fill: 'tozeroy',
    }], {
      title: "Memory Usage",
      yaxis: {
        range: [0, 100],
        autorange: true,
        title: {
          text: "%"
        }
      },
      xaxis: {
        title: {
          text: "Time (s)"
        }
      },
    }, {
      responsive: true,
      displayModeBar: false
    });
  }
  update(data) {
    super.update(data);
    Plotly.update(this.plotID, {
      y: [this.data]
    })
  }
}

export { Metrics, LoopTimePlot, CpuUsagePlot, MemoryUsagePlot }