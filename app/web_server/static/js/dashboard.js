import { Metrics, LoopTimePlot, CpuUsagePlot, MemoryUsagePlot } from "./metrics.js"


const host = location.hostname;


const metrics = new Metrics(`ws://${host}:9876/metrics`);


// Plotting

const mainCpuPlot = new CpuUsagePlot("main-cpu-plot");
metrics.addListener((data => {
    mainCpuPlot.update(data.sysCpuPercent);
}))

const mainMemoryPlot = new MemoryUsagePlot("main-mem-plot");
metrics.addListener((data => {
    mainMemoryPlot.update(data.sysMemPercent);
}))

const capLoopTimePlot = new LoopTimePlot('loop-time-plot');
metrics.addListener((data => {
    capLoopTimePlot.update(data.loopAvgS * 1000.0);
}))

const capCpuPlot = new CpuUsagePlot('cpu-time-plot');
metrics.addListener((data => {
    capCpuPlot.update(data.capCpuPercent);
}))

const capMemPlot = new MemoryUsagePlot('mem-time-plot');
metrics.addListener((data => {
    capMemPlot.update(data.capMemPercent);
}))