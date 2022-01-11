from statistics import mean
from time import time
from typing import Callable, List
import psutil
from app.datastructures import MetricsData


def calc_or_default(f: Callable[[List[float]], float], values: List[float]) -> float:
    """Helper function"""
    if len(values) > 0:
        return f(values)
    return 0.0


def get_list_avg(values: List[float]):
    return calc_or_default(mean, values)


def get_list_max(values: List[float]) -> float:
    return calc_or_default(max, values)


def get_list_min(values: List[float]) -> float:
    return calc_or_default(min, values)


def calc_metrics(
    sys_process: psutil.Process,
    cap_process: psutil.Process,
    cap_loop_times: List[float],
) -> MetricsData:
    """Calculate System Metrics

    Args:
        sys_process (psutil.Process): Main system process object
        cap_process (psutil.Process): Capture process object
        cap_loop_times (List[float]): Image frame loop times

    Returns:
        MetricsData: Computed metrics
    """
    data = MetricsData(
        time_stamp=time(),
        sys_cpu_percent=sys_process.cpu_percent(),
        sys_mem_percent=sys_process.memory_percent(),
        cap_cpu_percent=cap_process.cpu_percent(),
        cap_mem_percent=cap_process.memory_percent(),
        loop_avg_s=get_list_avg(cap_loop_times),
        loop_max_s=get_list_max(cap_loop_times),
        loop_min_s=get_list_min(cap_loop_times),
        socket_connections=len(sys_process.connections()),
    )
    return data
