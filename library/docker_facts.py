#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2018 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
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

- name: Remove containers that matched filters
  docker_container:
    name: "{{ item }}"
    state: absent
  loop: "{{ docker.containers_filtered | map(attribute='id') | list }}"

"""

RETURN = """
docker:
  description: >
    Lists of container, volume, and image IDs,
    both filtered and unfiltered.
  returned: always
  type: complex
  contains:
    containers:
        description: List of dictionaries of container name, state, and ID
        returned: always
        type: complex
    containers_filtered:
        description: >
            List of dictionaries of container name, state, and ID
            that matched the filter(s)
        returned: always
        type: complex
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

from ansible.module_utils.docker_common import AnsibleDockerClient


def _list_or_dict(value):
    if isinstance(value, list):
        return value
    elif isinstance(value, dict):
        return value
    raise TypeError


def _to_dict(client, filters):
    filter_dict = {}
    if isinstance(filters, list):
        for item in filters:
            a = item.split('=')
            filter_dict[a[0]] = a[1]
        return filter_dict
    elif isinstance(filters, str):
        a = filters.split('=')
        filter_dict[a[0]] = a[1]
        return filter_dict
    elif isinstance(filters, dict):
        return filters


def get_facts(client, docker_type, filters=None):
    result = []
    function_to_call = globals()['get_{}'.format(docker_type)]
    if filters and len(filters) > 1:
        for f in filters:
            result.extend(function_to_call(client, f))
    else:
        result = function_to_call(client, filters)
    return result


def get_images(client, filters=None):
    result = []
    if filters:
        filters = _to_dict(client, filters)
    images = client.images(filters=filters)
    if images:
        images = [i['Id'].strip('sha256:') for i in images]
        result = images
    return result


def get_containers(client, filters=None):
    result = []
    if filters:
        filters = _to_dict(client, filters)
    containers = client.containers(filters=filters)
    if containers:
        containers = [c['Id'].strip('sha256:') for c in containers]
        result = containers
    return result


def get_volumes(client, filters=None):
    result = []
    if filters:
        filters = _to_dict(client, filters)
    volumes = client.volumes(filters=filters)
    if volumes['Volumes']:
        volumes = [v['Name'] for v in volumes['Volumes']]
        result = volumes
    return result


def main():
    argument_spec = dict(
        image_filter=dict(type=list, default=[]),
        volume_filter=dict(type=list, default=[]),
        container_filter=dict(type=list, default=[]),
    )

    docker_client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    docker_facts = {}

    types_to_get = ['volumes', 'images', 'containers']

    for t in types_to_get:
        singular = t.rstrip('s')
        filter_key = '{}_filter'.format(singular)

        docker_facts[t] = get_facts(docker_client, t)

        filters = docker_client.module.params[filter_key]

        # Ensure we got a list of k=v filters
        if filters and len(filters[0]) <= 1:
            docker_client.module.fail_json(
                msg='The supplied {filter_key} does not appear to be a list of'
                ' k=v filters: {filter_value}'.format(
                    filter_key=filter_key, filter_value=filters)
            )
        else:
            docker_facts['{}_filtered'.format(t)] = get_facts(
                docker_client, t,
                filters=docker_client.module.params[filter_key])

    results = dict(
        ansible_facts=dict(
            docker=docker_facts
        )
    )

    docker_client.module.exit_json(**results)


if __name__ == '__main__':
    main()
