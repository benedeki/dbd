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

from dbd.abstract.abstract_destination_system import AbstractDestinationSystem
from dbd.abstract.abstract_record_keeper import AbstractRecordKeeper
from dbd.abstract.abstract_source_provider import AbstractSourceProvider
from dbd.core.driver import Driver
from dbd.core.expandable_config import ExpandableConfig


class Action(Enum):
    INSTALL = "install"
    HELP = "help"


def _load_parameters() -> tuple[Action, str, dict[str, str]]:
    if len(sys.argv) < 1:
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
            if not key:
                raise ValueError(f"Invalid command-line parameter: '{parameter}'")
            if not separator:
                if index + 1 >= len(parameters):
                    raise ValueError(f"Missing value for command-line parameter: '{parameter}'")
                value = parameters[index + 1]
                index += 1
            key = key.removeprefix("--")
            clis[key] = value
            index += 1
        else:
            raise ValueError(f"Unexpected command-line argument: '{parameter}'")
    return action, config_file, clis


def _load_classes(config: ExpandableConfig) -> tuple[
    AbstractRecordKeeper, AbstractSourceProvider, AbstractDestinationSystem
]:
    raise NotImplementedError


def main():
    action, config_file, clis = _load_parameters()
    config = ExpandableConfig.from_file(config_file)
    record_keeper, source_provider, destination_system = _load_classes(config)
    driver = Driver(config, record_keeper, source_provider, destination_system)
    match action:
        case Action.INSTALL:
            driver.install()
        case _:
            raise NotImplementedError


if __name__ == '__main__':
    main()
