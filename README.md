OpenStack Operations
=========

Perform various common OpenStack operations by calling this role with an action and appropriate variables.

Requirements
------------

None

Role Variables
--------------

**Variables used for cleaning up Docker**

| Name              | Default Value       | Description          |
|-------------------|---------------------|----------------------|
| `operations_docker_cleanup` | [see `defaults/main.yml`] | Filters used to determine which items will be removed. Uses Docker filter syntax. See Docker guides for [images](https://docs.docker.com/engine/reference/commandline/images/#filtering), [containers](https://docs.docker.com/engine/reference/commandline/ps/#filtering), and [volumes](https://docs.docker.com/engine/reference/commandline/volume_ls/#filtering) for filter options. |

**Variables for fetching logs**

| Name              | Default Value       | Description          |
|-------------------|---------------------|----------------------|
| `operations_log_destination` | `{{ playbook_dir }}` | Path where logs will be stored when fetched from remote systems. |

**Variables for restarting services**

| Name              | Default Value       | Description          |
|-------------------|---------------------|----------------------|
| `operations_service_names` | `[]` | List of services to restart on target systems. |

Dependencies
------------

None

Example Playbook
----------------

    - hosts: all
      tasks:
        - name: Restart a service
          import_role:
            name: openstack-operations
            tasks_from: restart_service.yml
          vars:
            operations_task: restart_service
            operations_service_names:
              - docker
              - keystone
              - mariadb

        - name: Cleanup unused Docker images, containers, and volumes
          import_role:
            name: openstack-operations
            tasks_from: cleanup_docker.yml

        - name: Fetch logs
          import_role:
            name: openstack-operations
            tasks_from: fetch_logs.yml

License
-------

Apache 2.0
