# Copyright 2026 David Benedeki, All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from enum import Enum
from importlib import import_module
from typing import Any

from dbd.abstract.abstract_destination_system import AbstractDestinationSystem
from dbd.abstract.abstract_record_keeper import AbstractRecordKeeper
from dbd.abstract.abstract_source_provider import AbstractSourceProvider
from dbd.core.driver import Driver
from dbd.core.expandable_config import ExpandableConfig
from dbd.core.simple_config import SimpleConfig


class Action(Enum):
    """Command-line actions supported by dbd."""

    INSTALL = "install"
    HELP = "help"


def _load_parameters() -> tuple[Action, str, dict[str, str]]:
    """Parse command-line arguments.

    :return: A tuple containing the requested action, configuration file path,
        and command-line configuration overrides. The path is empty and the
        overrides are empty for the help action.
    :raises ValueError: If the arguments are missing or invalid.
    """
    if len(sys.argv) < 2:
        raise ValueError("No command-line arguments provided.")
    if sys.argv[1] in ('-h', '--help'):
        action = Action.HELP
    else:
        action = Action(sys.argv[1])
    if action  == Action.HELP:
        return action, "", {}
    if len(sys.argv) < 3:
        raise ValueError("Configuration file path not provided.")

    config_file = sys.argv[2]
    parameters = sys.argv[3:]
    clis: dict[str, str] = {}
    index = 0
    while index < len(parameters):
        parameter = parameters[index]
        if parameter.startswith("--"):
            key, separator, value = parameter.partition("=")
            key = key.removeprefix("--")
            if not key:
                raise ValueError(f"Invalid command-line parameter: '{parameter}'")
            if not separator:
                if index + 1 >= len(parameters):
                    raise ValueError(f"Missing value for command-line parameter: '{parameter}'")
                value = parameters[index + 1]
                index += 1
            clis[key] = value
            index += 1
        else:
            raise ValueError(f"Unexpected command-line argument: '{parameter}'")
    return action, config_file, clis


def _load_classes(config: ExpandableConfig) -> tuple[
    AbstractRecordKeeper, AbstractSourceProvider, AbstractDestinationSystem
]:
    """Create and initialize the configured deployment components.

    :param config: Expanded configuration used to select and initialize the
        component implementations.
    :return: A tuple containing the record keeper, source provider, and destination system.
    :raises KeyError: If a required component configuration value is missing.
    :raises ImportError: If a configured implementation module cannot be imported.
    :raises AttributeError: If a configured implementation class is not present.
    """
    # TODO: Better configuration reade once #29 is implemented (avoid sub-config creation)
    # the secret reader configuration is needed expanded to be able to read secrets for the other components
    config.expand(branch = "secret_reader")
    # the above also means, that secret reader configuration cannot contain `SECRET` expander

    sub_config = config.get_as_config("secret_reader", {})
    secret_reader = _load_one_class(sub_config, "secret_reader", "SecretReader")
    config.expand(secret_reader)

    sub_config = config.get_as_config("record_keeper", {})
    record_keeper = _load_one_class(sub_config, "record_keeper", "RecordKeeper")

    sub_config = config.get_as_config("source_provider", {})
    source_provider = _load_one_class(sub_config, "source_provider", "SourceProvider")

    sub_config = config.get_as_config("destination_system", {})
    destination_system = _load_one_class(sub_config, "destination_system", "DestinationSystem")

    return record_keeper, source_provider, destination_system


def _load_one_class(config: SimpleConfig, default_source_file: str, default_class_name: str) -> Any:
    """Load and instantiate one dynamically configured component.

    :param config: Configuration containing the implementation type, optional
        module and class overrides, and nested constructor configuration.
    :param default_source_file: Module name used when the configuration does
        not specify ``source_file_override``.
    :param default_class_name: Class name used when the configuration does not
        specify ``class_override``.
    :return: An instance of the configured implementation.
    :raises KeyError: If a required configuration value is missing.
    :raises ImportError: If the implementation module cannot be imported.
    :raises AttributeError: If the implementation class is not present.
    """
    result_type = config.get_as_str("type")
    result_source_file = config.get_as_str("source_file_override", default_source_file)
    result_class_name = config.get_as_str("class_override", default_class_name)
    result_module = import_module(
        f"dbd.implementations.{result_type}.{result_source_file}"
    )
    result_class = getattr(result_module, result_class_name)
    sub_config = config.get_as_config("config")
    result = result_class(sub_config)
    return result

def main() -> None:
    """Load configuration and execute the requested deployment action.

    :return: None.
    :raises ValueError: If the command-line arguments are invalid.
    :raises NotImplementedError: If the requested action or component loading
        is not implemented.
    """
    action, config_file, clis = _load_parameters()
    config = ExpandableConfig(config_file, clis)
    record_keeper, source_provider, destination_system = _load_classes(config)
    driver = Driver(config, record_keeper, source_provider, destination_system)
    match action:
        case Action.INSTALL:
            driver.install()
        case _:
            raise NotImplementedError


if __name__ == '__main__':
    main()
