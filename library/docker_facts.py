#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

import itertools

from ansible.module_utils.basic import AnsibleModule


def run_docker_command(module, sub_command=[], opts='-q', filters=[]):
    docker_bin = [module.get_bin_path('docker', True)]

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
        module.fail_json(msg=err)

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
        )
    )

    docker_facts = {}

    # Images
    rc, images, err = run_docker_command(module, sub_command='images')
    docker_facts['images'] = images

    rc, images, err = run_docker_command(module, sub_command='images', filters=module.params['image_filter'])
    docker_facts['filtered_images'] = images

    # Volumes
    rc, volumes, err = run_docker_command(module, sub_command='volume ls', filters=module.params['volume_filter'])
    docker_facts['volumes'] = volumes

    rc, volumes, err = run_docker_command(module, sub_command='volume ls')
    docker_facts['filtered_volumes'] = volumes

    # Containers
    rc, containers, err = run_docker_command(module, sub_command='ps')
    docker_facts['containers'] = containers

    rc, containers, err = run_docker_command(module, sub_command='ps -a', filters=module.params['container_filter'])
    docker_facts['filtered_containers'] = containers

    results = dict(
        ansible_facts=dict(
            docker=docker_facts
        )
    )

    module.exit_json(**results)


if __name__ == '__main__':
    main()
