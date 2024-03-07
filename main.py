#!/usr/bin/env python

import argparse
import importlib
import os
import sys
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'runtime/data')

sys.path.append(BASE_DIR)

from gpuhunter.utils.logging import get_logger

logger = get_logger(__name__, os.path.join(BASE_DIR, "runtime/logs"))


def get_command_names():
    commands_dir = os.path.join(BASE_DIR, "gpuhunter/commands")
    command_names = [
        filename.stem
        for filename in Path(commands_dir).glob("*.py")
        if filename.is_file() and not filename.name.startswith("_")
    ]
    return command_names


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="AutoDL GPU Hunter",
    )
    subparsers = parser.add_subparsers(help="sub-command help", dest="command_name")
    modules_map = {}
    for command_name in get_command_names():
        module = importlib.import_module(f"gpuhunter.commands.{command_name}")
        command_parser = subparsers.add_parser(
            command_name,
            help=module.get_help(),
        )
        module.add_arguments(command_parser)
        modules_map[command_name] = module
    options = parser.parse_args(sys.argv[1:])
    module = modules_map[options.command_name or "app"]
    del options.command_name
    module.main(**vars(options))
