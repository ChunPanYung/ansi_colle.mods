# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cmp_pkg
short_description: Given a package version, it will compare to installed version.
version_added: "2.0.0"
description:
  - This is my longer description explaining my test module.

options:
    name:
        description:
            - command use to get version number.
            - Example, bash --version
        aliases: [ get_command_version ]
        required: true
        type: list
        elements: str
    regexp:
        description: Regexp to use for extracting only the version number.
        default: '\d+\.\d+\.\d+'
        type: str
    desired_version:
        description: desired version for current installation.
        required: true
        type: str
    index:
        description:
            - Which version number selected from after running command.
            - if more than 1 matched version are returned.
            - Default is 0.
            - First occurence is 0, second is 1, and third is 2 etc.
        default: 0
        type: int
extends_documentation_fragment:
    - ansi_colle.mods.attributes
attributes:
    check_mode:
        support: full
    diff_mode:
        support: none
    platform:
        platforms: linux

author:
    - Chun Pan Yung
"""

EXAMPLES = r"""
- name: Check package verison
  ansi_colle.mods.cmp_pkg:
    name: ansible --version
    desired_version: '2.14.1'

- name: Get the second version number after executing command with regexp.
  ansi_colle.mods.cmp_pkg:
    get_command_version: ansible -v
    index: 1
    desired_version: 3.12.1

- name: Return code 0 if command version cannot be found
  ansi_colle.mods.cmp_pkg:
    name: not_existing_commands
"""

RETURN = r"""
msg:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'Desired version matches the installed version.'
rc:
    description:
        - return 0 if desired version is equal to installed version.
        - return -1 if desired version cannot be validated.
        - return 1 if it cannot get version from command.
        - return 2 if desired version is greater than installed version.
        - return -2 if desired version is less than installed version.
        - return 3 if no desired version is installed.
    type: int
    returned: always
    sample: 0
version_list:
    description: List of version numbers returned after running cmd with regexp.
    type: list
    returned: always
    sample: ['2.14.1', '3.11.9', '3.1.12']
"""

import shlex  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402

from ansible.module_utils.basic import AnsibleModule  # noqa: E402
from ansible.module_utils.compat.version import LooseVersion  # noqa: E402


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type="str", required=True, aliases=["get_command_version"]),
        desired_version=dict(type="str", required=True),
        regexp=dict(type="str", default=r"\d+\.\d+\.\d+"),
        index=dict(type="int", default=0),
    )

    result = dict(msg="", rc=0, failed=False, version_list=[])

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    command_version: list = shlex.split(module.params["name"])
    # command_version list should only contains 2 items, ex: bash --version
    if len(command_version) != 2:
        name: str = module.params["name"]
        result["rc"] = -1
        result["msg"] = f"'name' parameter should only contains 2 items: {name}"
        module.fail_json(**result)

    # Early return if command does not exist
    if not shutil.which(command_version[0]):
        result["msg"] = "No desired version is installed."
        result["rc"] = 3
        module.exit_json(**result)

    _, stdout, _ = module.run_command(command_version)

    # Return list of version after re.findall() function
    regexp: str = module.params["regexp"]

    version_list: list = []
    try:
        version_list = re.findall(regexp, stdout)
        result["version_list"] = version_list
    except TypeError:
        result["rc"] = 1
        module.fail_json(msg=f"Error getting version from command: {stdout}")

    # Get only selected version
    index: int = module.params["index"]
    installed_version = version_list[index]

    # Make sure desired_version followed regexp given
    desired_version = re.match(regexp, module.params["desired_version"])
    if not desired_version:
        version = module.params["desired_version"]
        result["rc"] = -1
        module.fail_json(msg=f"Error validate desired version: {version}")
        module.exit_json(**result)

    if desired_version < LooseVersion(installed_version):
        result["msg"] = (
            "Desired version({}) is less than installed version({}).".format(
                desired_version, installed_version
            )
        )
        result["rc"] = -2
    elif desired_version > LooseVersion(installed_version):
        result["msg"] = (
            "Desired version({}) is greater than installed version({}).".format(
                desired_version, installed_version
            )
        )
        result["rc"] = 2
    else:
        result["msg"] = "Desired version({}) matches the installed version({}).".format(
            desired_version, installed_version
        )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
