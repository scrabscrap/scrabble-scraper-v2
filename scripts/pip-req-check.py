#!/usr/bin/env python
""" "
removes not required pip packages with transitive dependencies
"""

import logging
import os
import platform
import re
import subprocess
import sys
from io import StringIO

from packaging.version import Version


class StrVersion:
    """ "to compare Version to a str"""

    def __init__(self, a):
        self.a = Version(a) if type(a) == str else a

    def __lt__(self, other):
        return self.a < Version(other) if type(other) == str else self.a < other

    def __le__(self, other):
        return self.a <= Version(other) if type(other) == str else self.a <= other

    def __gt__(self, other):
        return self.a > Version(other) if type(other) == str else self.a > other

    def __ge__(self, other):
        return self.a >= Version(other) if type(other) == str else self.a >= other

    def __eq__(self, other):
        return self.a == Version(other) if type(other) == str else self.a == other

    def __ne__(self, other):
        return self.a != Version(other) if type(other) == str else self.a != other


# not supported: module selection, multiple version strings, version wildcard
scanner_requirements = re.Scanner(
    [
        (r"--[\w=:-]*", lambda s, t: ("DIRECTIVE", t)),
        (r"[a-zA-Z_-][\w.-]*", lambda s, t: ("IDENT", t)),
        (r"(==)|(>)|(<)|(<=)|(>=)|(~=)", lambda s, t: ("OPERATOR", t)),
        (r"[\d]+(\.[\d]+)*", lambda s, t: ("VERSION", t)),
        (r'\;[\w=<>!. \t"\']*', lambda s, t: ("CONDITION", t)),
        (r"#[^\n\r]*", None),
        (r"([\n\r])+", lambda s, t: ("EOL", t)),
        (r"([\\][\n\r])+", None),
        (r"\s+", None),
    ]
)
WHITELIST = ("wheel", "setuptools", "pip")

# see: https://peps.python.org/pep-0508/
os_name = os.name
python_version = StrVersion(".".join(platform.python_version_tuple()[:2]))
python_full_version = StrVersion(platform.python_version())
platform_python_implementation = platform.python_implementation()
platform_machine = platform.machine()
platform_version = platform.version()
platform_system = platform.system()
sys_platform = sys.platform


def analyze(data: StringIO) -> dict:
    result = "".join(data.readlines())
    tokens, _ = scanner_requirements.scan(result)

    requirements = {}
    current = {}

    for token_type, token_value in tokens:
        logging.debug(f"{(token_type, token_value)}")

        if token_type == "IDENT":
            current["name"] = token_value.strip().lower()
        elif token_type == "VERSION":
            current["version"] = token_value.strip()
        elif token_type == "CONDITION":
            current["condition"] = token_value.lstrip(";").strip()
        elif token_type == "EOL":
            name = current.get("name")
            version = current.get("version")
            condition = current.get("condition")

            if name:
                if condition and eval(condition):
                    logging.debug(f"({condition}) = {eval(condition)}")
                    requirements[name] = version
                elif not condition:
                    requirements[name] = version

            current.clear()

    return dict(sorted(requirements.items()))


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, force=True, format="%(message)s")

    data = open("requirements.txt")
    required_reqs = analyze(data)

    data = open("requirements-devel.txt")
    devel_reqs = analyze(data)

    required_reqs.update(devel_reqs)
    required_reqs = dict(sorted(required_reqs.items()))
    logging.debug(f"{required_reqs=}")

    max_loops = 6
    while True:
        #  --exclude pip --exclude setuptools --exclude wheel
        data = StringIO(
            subprocess.check_output(["pip", "list", "--not-required", "--local", "--format", "freeze"]).decode("utf-8")
        )
        installed_reqs = analyze(data)
        logging.debug(f"{installed_reqs=}")

        to_delete = [n for n in installed_reqs.keys() if n not in required_reqs.keys() and n not in WHITELIST]
        if not max_loops or not to_delete:
            break

        for elem in to_delete:
            subprocess.check_output(["pip", "uninstall", "-y", elem])
            logging.info(f"uninstall {elem}")
        max_loops -= 1


if __name__ == "__main__":
    main()
