#!.venv/bin/python

from pathlib import Path
import sys

app_path = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(app_path))

from app.config import load_config_from_file, TomlConfigSerializer
from app.datastructures import Flags
from app.web_server.server_process import Server


if __name__ == "__main__":
    flags = Flags(
        config_path=str(app_path / "test_config.toml"),
        silent=True,
        log_level="debug",
        file=None,
        test=False,
    )
    config = load_config_from_file(flags, TomlConfigSerializer())
    server = Server(config)
    server._run(hot_reload=True)
