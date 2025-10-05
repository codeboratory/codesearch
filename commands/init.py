import json
import os.path

from dataclasses import asdict
from config import default
from shared import CWD


def define_init(subparsers):
    subparsers.add_parser(
        "init",
        help="Init a repo"
    )


def handle_init(args):
    path = f"{CWD}/codesearch.json"

    if os.path.exists(path):
        print("This repo has already been initialized")
        return

    with open(path, "w") as file:
        file.write(json.dumps(asdict(default)))
