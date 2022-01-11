import multiprocessing as mp
from time import sleep
import uvicorn
from uvicorn_loguru_integration import run_uvicorn_loguru
from app.datastructures import AppConfig
from app.bootstrap.logger import set_log_level
from app.helpers import TimeoutAfter

__all__ = ["Server"]


class Server:
    def __init__(self, config: AppConfig):
        ctx = mp.get_context("spawn")
        self.config = config
        self._process = ctx.Process(
            target=self._run, name="WebServerProcess", daemon=True
        )

    def start(self):
        self._process.start()

    def shutdown(self, timeout: float = 5):
        # The uvicorn server should gracefully close on a SIGINT signal
        # TODO: The shutdown could either be a SIGINT or SIGTERM, SIGINT is handled automatically
        # by the uvicorn server, what about SIGTERM?
        try:
            with TimeoutAfter(timeout=timeout):
                while True:
                    if not self._process.is_alive():
                        break
                    sleep(0.5)
        except TimeoutError:
            self._process.terminate()
            self._process.join(timeout)
        self._process.close()

    def _run(self, hot_reload=False):
        configuration = dict(
            host=self.config.server.host_name,
            app="app.web_server.web_app:app",
            loop="uvloop",
            port=self.config.server.webserver_port,
            log_level=self.config.flags.log_level,
        )
        if hot_reload:
            configuration["reload"] = True
        set_log_level(self.config.flags.log_level)
        run_uvicorn_loguru(uvicorn.Config(**configuration))  # type: ignore
        raise SystemExit(0)
