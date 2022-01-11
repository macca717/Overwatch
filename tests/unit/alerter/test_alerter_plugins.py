from typing import List
import pytest
from app.alerter import load_plugins
from app.alert_plugins import AlerterPlugin

# pylint:disable=redefined-outer-name


@pytest.fixture(scope="class")
def config_dict():
    return {
        "test_alerter_one": {"test_grp": True, "enabled": True},
        "test_alerter_two": {"test_grp": False, "enabled": True},
        "test_alerter_three": {"test_grp": False, "enabled": True},
    }


@pytest.fixture(scope="class")
def plugins(config_dict):
    return load_plugins(
        "tests/unit/alerter/plugins", config=config_dict, plugin_module="plugins"
    )


class TestPluginLoader:
    def test_plugin_loader(self, plugins):
        assert len(plugins) == 3

    def test_plugin_loader_types(self, plugins):
        for plugin in plugins:
            assert isinstance(plugin, AlerterPlugin)

    def test_plugin_loader_correct_init(self, plugins: List[AlerterPlugin]):
        plugin_one = filter(lambda plugin: plugin.name == "test_alerter_one", plugins)
        assert list(plugin_one)[0].in_test_grp is True
