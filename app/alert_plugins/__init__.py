"""Plugin Module

This module is the basis of of the plugin system

All user plugins that are placed in this directory and derive from from the base Plugin
class will be loaded by the plugin system.

The module contains a retry function that can be used to decorate the plugins run function in case
of error.

Example:
    >>> @retry(Exception, tries=3, delay=10)
        def run(self, msg: str) -> None:
            print(msg)

"""

from .base import *
