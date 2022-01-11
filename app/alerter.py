import asyncio
from importlib import import_module
from inspect import isclass
from pkgutil import iter_modules
from pathlib import Path
from typing import Any, Awaitable, cast, Dict, List
from loguru import logger
from app.alert_plugins import AlerterPlugin
from app.datastructures import (
    AlertData,
    AppConfig,
    CommandRequest,
    ConfigUpdateData,
    SystemCommand,
    SystemStatus,
    State,
)
from app.events import Event, Publisher, Topic


__all__ = ["Alerter"]


class Alerter:
    def __init__(self, config: AppConfig, publisher: Publisher):
        self.config = config
        if self.config.alerters:
            self.plugins = load_plugins(
                "app/alert_plugins/", self.config.alerters, "app.alert_plugins"
            )
        else:
            self.plugins = []
        self.publisher = publisher
        self.pending_alerts: List[Awaitable[None]] = []
        self._system_state = State.OFF
        self._subscribe()

    def _subscribe(self):
        self.publisher.subscribe(Topic.SYSTEM_ALARM, self._alarm_handler)
        self.publisher.subscribe(
            Topic.SYSTEM_CONFIG_UPDATE, self._config_update_handler
        )
        self.publisher.subscribe(
            Topic.SYSTEM_STATUS_UPDATE, self._status_update_handler
        )

    def _config_update_handler(self, event: Event):
        logger.debug("Updating plugin configs")
        new_config: AppConfig = event.data
        self.config = new_config
        if self.config.alerters:
            self.plugins = load_plugins(
                "app/alert_plugins/", self.config.alerters, "app.alert_plugins"
            )

    def _alarm_handler(self, evt: Event):
        loop = asyncio.get_event_loop()
        alert_data: AlertData = evt.data
        to_run: List[AlerterPlugin] = []
        for plugin in self.plugins:
            if alert_data.is_test:
                not_in_exclusions = plugin.name not in alert_data.exclusion_list
                if plugin.in_test_grp and not_in_exclusions:
                    to_run.append(plugin)
            else:
                to_run.append(plugin)
        for plugin in to_run:
            self.pending_alerts.append(
                loop.run_in_executor(None, plugin.raise_alert, alert_data.msg)
            )

    def _status_update_handler(self, event: Event):
        state: State = cast(SystemStatus, event.data).state
        if self._system_state != state:
            self._system_state = state
            if self._system_state == State.ON:
                self._re_enable_all_alerters()

    async def run(self):
        while True:
            for future in self.pending_alerts:
                try:
                    await future
                    logger.debug("Pending alerter completed")
                except Exception as ex:  # pylint: disable=broad-except
                    logger.error(ex)
            self.pending_alerts = []
            await asyncio.sleep(1)

    def _re_enable_all_alerters(self):
        reload_required = False
        new_config = self.config.copy()
        if new_config.alerters:
            for alerter_config in new_config.alerters.values():
                if not alerter_config["enabled"]:
                    logger.debug("Re-enabling alerters")
                    reload_required = True
                    alerter_config["enabled"] = True
        if reload_required:
            self.publisher.send_message(
                Topic.COMMAND_REQUEST,
                Event(
                    data=CommandRequest(
                        uuid=None,
                        command=SystemCommand.CONFIG_UPDATE,
                        data=ConfigUpdateData(config=new_config),
                    )
                ),
            )


def load_plugins(
    path: str, config: Dict[str, Any], plugin_module: str
) -> List[AlerterPlugin]:
    """Dynamically load alerting plugins

    Args:
        path (str): Path to plugin directory
        config (Dict[str, Any]): Alerter config dictionary
        plugin_module (str): Plugin module namespace(e.g foo.bar)

    Returns:
        List[AlerterPlugin]: Loaded plugins
    """
    modules = {}
    package_dir = str(Path(path).resolve())
    for (_, module_name, _) in iter_modules([package_dir]):

        module = import_module(f"{plugin_module}.{module_name}")
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)

            if isclass(attribute) and issubclass(attribute, AlerterPlugin):
                modules[attribute_name] = attribute

    user_plugins: List[AlerterPlugin] = []
    for name, alerter in modules.items():
        # The base plugin is loaded, don't instantiate
        if name != AlerterPlugin.__name__:
            try:
                instance: AlerterPlugin = alerter(config=config)
                user_plugins.append(instance)
                logger.info(f"Loaded plugin {name}")
            except KeyError:
                logger.warning(f"Failed to load plugin {name}, missing config")
    return user_plugins
