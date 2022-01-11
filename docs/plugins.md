# Alerter Plugin System

## Overview

The application employs a plugin system to configure user defined alerters that raise an alert when motion is detected. The plugins are written in python and must be located in the "app/alert_plugins" directory. The user defined alerter must derive from the base alerter found in "app/alert_plugins/base.py". Custom logic to run when an alaert is raised is implemented in the *run* method of the custom alerter.

Alerter plugins are run in a separate thread to avoid blocking the main process. The "base.py" file also imports a "retry" decorator to retry alert logic (Useful for external API calls and temporary network issues). A minimal alerter class can be found below.

## Configuration
Plugin configuration is loaded from the main configuration file ("config.toml"), the configuration is stored in the section "[alerters.*name*]". The configuration must contain the following keys:
- "test-grp" (Boolean, used to indicate if the plugin will raise an alert during a test)
- "enabled" (Boolean, used to indicate if the plugin is enabled)

Further user defined keys can be added as neccessary, these values can be accessed via the custom class in the "config" dictionary. The key for the alerter config is the name defined in the toml configuration section "[alerters.*name*]"
Common files and assets required by the plugin can be stored in the *app/alerter_plugins/common* directory.

### Example Configuration Section
```toml
[alerters.my_alerter]
enabled = true
test_grp = true
api = "123456789qwerty"

```
### Example User Defined Alerter
```python
from typing import Any, Dict
from loguru import logger
from .base import AlerterPlugin, retry


class MyAlerter(AlerterPlugin):
    """Example Alerter

    Prints an alert to the console
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        # self._name must match the name defined in the toml configuration section
        self._name = "my_alerter"
        self._test_grp = config[self._name]["test_grp"]
        self._enabled = config[self._name]["enabled"]
        self._api = config[self._name]["api"]

    @property
    def name(self) -> str:
        return self._name

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def in_test_grp(self) -> bool:
        return self._test_grp

    @retry(Exception, tries=3, logger=logger)
    def run(self, msg: str) -> None:
        # Custom logic here ...
        print(f"My alerter: The API key is {self._api}")

```

THe application uses the third party library [Apprise](https://pypi.org/project/apprise/) for communicating with external services. User defined plugins can utilise this library if required.
