#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2018 Ansible Project
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: docker_facts
author:
    - Sam Doran (@samdoran)
version_added: '2.6'
short_description: Gather list of volumes, images, containers
notes:
    - When specifying mulitple filters, only assets matching B(all) filters
      will be returned.
description:
    - Gather a list of volumes, images, and containers on a running system
    - Return both filtered and unfiltered lists of volumes, images,
      and containers.
options:
    image_filter:
        description:
            - List of k=v pairs to use as a filter for images.
        type: list
        required: false
    volume_filter:
        description:
            - List of k=v pairs to use as a filter for volumes.
        type: list
        required: false
    container_filter:
        description:
            - List of k=v pairs to use as a filter for containers.
        type: list
        required: false

"""

EXAMPLES = """
- name: Gather Docker facts
  docker_facts:

- name: Gather filtered Docker facts
  docker_facts:
    image_filter:
      - dangling=true
    volume_filter:
      - dangling=true
    container_filter:
      - status=exited
      - status=dead
"""

RETURN = """
docker_facts:
  description: >
    Lists of container, volume, and image UUIDs,
    both filtered and unfiltered.
  returned: always
  type: complex
  contains:
    containers:
        description: List of container UUIDs
        returned: always
        type: list
    containers_filtered:
        description: List of UUIDs that matched the filter(s)
        returned: always
        type: list
    images:
        description: List of image UUIDs
        returned: always
        type: list
    images_filtered:
        description: List of UUIDs that matched the filter(s)
        returned: always
        type: list
    volumes:
        description: List of volume UUIDs
        returned: always
        type: list
    volumes_filtered:
        description: List of UUIDs that matched the filter(s)
        returned: always
        type: list
"""

import itertools

from ansible.module_utils.basic import AnsibleModule

DOCKER_SUBCOMMAND_LOOKUP = dict(
    images='images',
    volumes='volume ls',
    containers='ps -a'
)


def run_docker_command(
        module,
        docker_bin,
        sub_command=[],
        opts='-q',
        filters=[]):

    for item in docker_bin, sub_command, opts, filters:
        if not isinstance(item, list):
            item = item.split('\n')

    if not isinstance(docker_bin, list):
        docker_bin = docker_bin.split()

    if not isinstance(sub_command, list):
        sub_command = sub_command.split()

    if not isinstance(opts, list):
        opts = opts.split()

    if not isinstance(filters, list):
        filters = filters.split()

    filters = ['-f ' + i for i in filters]
    command = list(itertools.chain(docker_bin, sub_command, opts, filters))
    rc, out, err = module.run_command(command)

    if rc != 0:
        module.fail_json(
            msg='Error running command {}.\n\n \
                 Original error:\n\n{}'.format(command, err))

    if out == '':
        out = []
    else:
        out = out.strip().split('\n')

    return rc, out, err


def main():
    module = AnsibleModule(
        argument_spec=dict(
            image_filter=dict(type='list', default=[]),
            volume_filter=dict(type='list', default=[]),
            container_filter=dict(type='list', default=[]),
        ),

        supports_check_mode=True
    )

    docker_bin = [module.get_bin_path('docker')]

    docker_facts = {}

    for key, value in DOCKER_SUBCOMMAND_LOOKUP.items():
        docker_facts[key] = []
        docker_facts[key.rstrip('s') + '_filtered'] = []

    if docker_bin[0]:

        for key, value in DOCKER_SUBCOMMAND_LOOKUP.items():
            rc, out, err = run_docker_command(
                module, docker_bin, sub_command=value)

            docker_facts[key] = out

            rc, out, err = run_docker_command(
                module,
                docker_bin,
                sub_command=value,
                filters=module.params[key.rstrip('s') + '_filter']
            )
            docker_facts[key + '_filtered'] = out

    results = dict(
        ansible_facts=dict(
            docker=docker_facts
        )
    )

    module.exit_json(**results)


if __name__ == '__main__':
    main()
