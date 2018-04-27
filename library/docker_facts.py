#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2018 Ansible Project
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

DOCKER_SUBCOMMAND_LOOKUP = dict(
    images='images',
    volumes='volume ls',
    containers='ps -a'
)


def run_docker_command(
        module, docker_bin, sub_command=[], opts='-q', filters=[]):

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
        docker_facts[key.rstrip('s') + '_filter'] = []

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
