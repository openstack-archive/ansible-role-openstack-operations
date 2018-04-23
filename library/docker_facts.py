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


from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            image_filter=dict(type='list', default=[]),
            volume_filter=dict(type='list', default=[]),
            container_filter=dict(type='list', default=[]),
        )
    )

    docker_bin = module.get_bin_path('docker', True)
    docker_facts = {}

    # Images
    command = [docker_bin, 'images', '-q']
    command_opts = ['-f ' + i for i in module.params['image_filter']]
    command.extend(command_opts)
    rc, out, err = module.run_command(command)
    if out == '':
        images = []
    else:
        images = out.strip().split('\n')
    docker_facts['filtered_images'] = images

    # Volumes
    command = [docker_bin, 'volume', 'ls', '-q']
    command_opts = ['-f ' + i for i in module.params['volume_filter']]
    command.extend(command_opts)
    rc, out, err = module.run_command(command)
    if out == '':
        volumes = []
    else:
        volumes = out.strip().split('\n')
    docker_facts['filtered_volumes'] = volumes

    # Containers
    command = [docker_bin, 'ps', '-q']
    command_opts = ['-f ' + i for i in module.params['container_filter']]
    command.extend(command_opts)
    rc, out, err = module.run_command(command)
    if out == '':
        containers = []
    else:
        containers = out.strip().split('\n')
    docker_facts['filtered_containers'] = containers

    results = dict(
        ansible_facts=dict(
            docker_facts=docker_facts
        )
    )

    module.exit_json(**results)


if __name__ == '__main__':
    main()
