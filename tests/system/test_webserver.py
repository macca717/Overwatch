import time
import pytest
from app.web_server import Server

pytestmark = pytest.mark.system


def test_webserver_shutdown(test_config):
    web = Server(test_config)
    web.start()
    time.sleep(10)
    web.shutdown()
