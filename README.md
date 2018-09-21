# OpenStack Operations #


Perform various common OpenStack operations by calling this role with an action and appropriate variables.

## Restart Services ##

Restarting OpenStack services is complex. This role aims to intelligently evaluate the environment and determine how a service is running, what components constitute that service, and restart those components appropriately. This allows the operator to think in terms of the service that needs restarting rather than having to remember all the details required to restart that service.

This role uses a service map located in `vars/main.yml`. The service map is a dictionary with one key per service name. Each service name key contains three additional keys that list the SystemD unit files, container names, and vhosts used by each service. It is possible to extend this list of services by defining custom services in `operations_custom_service_map`. This will be combined with the default service map and passed to the `service_map_facts` module.

The `service_map_facts` module will evalute the target system and return a list of services or containers that need to be restarted. Those lists will then be used in subsequent tasks to restart a service or a container.

## Fetch Logs ##

To fetch logs with this role, use the `fetch_logs.yml` tasks file. By default, every log file in `/var/log` matching the `*.log` pattern will be fetched from the remote and put into a folder adjacent to the playbook named for each host, preserving the directory structure as found on the remote host.

See `defaults/main.yml` for the dictionary of options to control logs that are fetched.

## Cleanup Container Items ##

**WARNING:** This will delete images, containers, and volumes from the target system(s).

To perform the most common cleanup tasks --- delete dangling images and volumes and delete exited or dead containers --- use the `container_cleanup.yml` tasks file.

This role includes modules for listing image, volume, and container IDs. The filtered lists (one each for images, containers, and volumes) returned by this module are used to determine which items to remove. Specifying multiple filters creates an `and` match, so all filters must match.

If using Docker, see these guides for [images](https://docs.docker.com/engine/reference/commandline/images/#filtering), [containers](https://docs.docker.com/engine/reference/commandline/ps/#filtering), and [volumes](https://docs.docker.com/engine/reference/commandline/volume_ls/#filtering) for filter options.

## Backup and Restore Operations ##

See [Backup and Restore Operations](README-backup-ops.md) for more details.

## Requirements ##

  - ansible >= 2.4

If using Docker:

  - docker-py >= 1.7.0
  - Docker API >= 1.20

## Role Variables ##


**Variables used for cleaning up Docker**

| Name              | Default Value       | Description          |
|-------------------|---------------------|----------------------|
| `operations_container_runtime` | `docker` | Container runtime to use. Currently supports `docker` and `podman`. |
| `operations_image_filter` | `['dangling=true']` | List of image filters. |
| `operations_volume_filter` | `['dangling=true']` | List of volume filters. |
| `operations_container_filter` | `['status=exited', 'status=dead']` | List of container filters. |

**Variables for fetching logs**

| Name              | Default Value       | Description          |
|-------------------|---------------------|----------------------|
| `operations_log_destination` | `{{ playbook_dir }}` | Path where logs will be stored when fetched from remote systems. |


**Variables for restarting services**

| Name              | Default Value       | Description          |
|-------------------|---------------------|----------------------|
| `operations_services_to_restart` | `[]` | List of services to restart on target systems. |
| `operations_custom_service_map` | `{}` | Dictionary of services and their systemd unit files, container names, and vhosts. This will be combined with the builtin list of services in `vars/main.yml`. |


## Dependencies ##

None

## Example Playbooks ##


### Restart Services ###

    - hosts: all
      tasks:
        - name: Restart a service
          import_role:
            name: openstack-operations
            tasks_from: restart_service.yml
          vars:
            operations_services_to_restart:
              - docker
              - keystone
              - mariadb


### Cleanup Container Items ###

    - name: Cleanup dangling and dead images, containers, and volumes
      hosts: all
      tasks:
        - name: Cleanup unused images, containers, and volumes
          import_role:
            name: openstack-operations
            tasks_from: container_cleanup.yml

    - name: Use custom filters for cleaning
      hosts: all
      tasks:
        - name: Cleanup unused images, containers, and volumes
          import_role:
            name: openstack-operations
            tasks_from: container_cleanup.yml
          vars:
            operations_image_filters:
              - before=image1
            operations_volume_filters:
              - label=my_volume
            operations_container_filters:
              - name=keystone



### Fetch Logs ###

    - hosts: all
      tasks:
        - name: Fetch logs
          import_role:
            name: openstack-operations
            tasks_from: fetch_logs.yml

License
-------

Apache 2.0
