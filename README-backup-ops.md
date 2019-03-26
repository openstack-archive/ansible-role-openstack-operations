# Backup and Restore Operations #

The `openstack-operations` role includes some foundational backup and restore Ansible tasks to help with automatically backing up and restoring OpenStack services. The current services available to backup and restore include:

* MySQL on a galera cluster
* Redis

Scenarios tested:

* TripleO, 1 Controller, 1 Compute, backup to the undercloud
* TripleO, 1 Controller, 1 Compute, backup to remote server
* TripleO, 3 Controllers, 1 Compute, backup to the undercloud
* TripleO, 3 Controllers, 1 Compute, backup to remote server

## Architecture ##

The architecture uses three main host types:

* Target Hosts - Which are the OpenStack nodes with data to backup. For example, this would any nodes with database servers running
* Backup Host - The destination to store the backup.
* Control Host - The host that executes the playbook. For example, this would be the undercloud on TripleO.

You can also unify the Backup Host and Control Host onto a single host. For example, a host that runs playbooks AND stores the backup data,

## Requirements ##

General Requirements:
* Backup Host needs access to the `rsync` package. A task in `initialize_backup_host.yml` will attempt to install it.

MySQL/Galera
* Target Hosts needs access to the `mysql` package. Tasks in the backup and restore files will attempt to install it.
* When restoring to Galera, the Control Host requires the `pacemaker_resource` module. You can obtain this module from the `ansible-pacemaker` RPM. If your operating system does not have access to this package, you can clone the [ansible-pacemaker git repo](https://github.com/redhat-openstack/ansible-pacemaker). When running a restore playbook, include the `ansible-pacemaker` module using the `-M` option (e.g. `ansible-playbook -M /usr/share/ansible-modules ...`)

Filesystem
* It has no special requirements, only the `tar` command is going to be used.

Redis
* Target Hosts needs access to the `redis` package. Tasks in the backup and restore files will attempt to install it.
* When restoring Redis, the Control Host requires the `pacemaker_resource` module. You can obtain this module from the `ansible-pacemaker` RPM. If your operating system does not have access to this package, you can clone the [ansible-pacemaker git repo](https://github.com/redhat-openstack/ansible-pacemaker). When running a restore playbook, include the `ansible-pacemaker` module using the `-M` option (e.g. `ansible-playbook -M /usr/share/ansible-modules ...`)

## Task Files ##

The following is a list of the task files used in the backup and restore process.

Initialization Tasks:
* `initialize_backup_host.yml` - Makes sure the Backup Host (destination) has an SSH key pair and rsync installed.
* `enable_ssh.yml` - Enables SSH access from the Backup Host to the Target Hosts. This is so rsync can pull the backed up data and push the data during a restore.
* `disable_ssh.yml` - Disables SSH access from the Backup Host to the Target Hosts. This ensures that access is only granted during the backup only.
* `set_bootstrap.yml` - In situations with high availability, some restore tasks (such as Pacemaker functions) only need to be carried out by one of the Target Hosts. The tasks in `set_bootstrap.yml` set a "bootstrap" node to help execute single tasks on only one Target Host. This is usually the first node in your list of targets.

Backup Tasks:
* `backup_mysql.yml` - Performs a backup of the OpenStack MySQL data and grants, archives them, and sends them to the desired backup host.
* `backup_filesystem.yml` - Creates a tar file of a list of files/directories given and sends then to a desired backup host.
* `backup_redis.yml` - Performs a backup of Redis data from one node, archives them, and sends them to the desired backup host.

Restore Tasks:
* `restore_galera.yml` - Performs a restore of the OpenStack MySQL data and grants on a containerized galera cluster. This involves shutting down the current galera cluster, creating a brand new MySQL database, then importing the data and grants from the archive. In addition, the playbook saves a copy of the old data in case the restore process fails.
* `restore_redis.yml` - Performs a restore of Redis data from one node to all nodes and resets the permissions using a redis container.

Validation Tasks:
* `validate_galera.yml` - Performs the equivalent of `clustercheck` i.e. checks the `wsrep_local_state` is 4 ("Synced").
* `validate_galera.yml` - Performs a Redis check with `redis-cli ping`.

## Variables ##

Use the following variables to customize how you want to run these tasks.

Variables for all backup tasks:
* `backup_directory` - The location on the backup host to rsync archives. If unset, defaults to the home directory of the chosen inventory user for the Backup Host. If you aim to have recurring backup jobs and store multiple iterations of the backup, you should set this to a dynamic value such as a timestamp or UUID.
* `backup_server_hostgroup` - The name of the host group containing the backup server. Ideally, this host group only contains the Backup Host. If more than one host exists in this group, the tasks pick the first host in the group. Note the following:
  * The chosen Backup Host Group must be in your inventory.
  * The Backup Host must be initialized using the `initialize_backup_host.yml`. You can do this by placing the Backup Host in a single host group called `backup` and refer to it as using `hosts: backup[0]` in a play that runs the `initialize_backup_host` tasks.
  * You can only use one Backup Host. This is because the delegation for the `synchronize` module allows only one host.

MySQL and galera backup and restore variables:
* `kolla_path` - The location of the configuration for Kolla containers. Defaults to `/var/lib/config-data/puppet-generated`.
* `mysql_bind_host` - The IP address for database server access. The tasks place a temporary firewall block on this IP address to prevent services writing to the database during the restore.
* `mysql_root_password` - The original root password to access the database. If unsent, it checks the Puppet hieradata for the password.
* `mysql_clustercheck_password` - The original password for the clustercheck user. If unsent, it checks the Puppet hieradata for the password.
* `galera_container_image` - The image to use for the temporary container to restore the galera database. If unset, it tries to determine the image from the existing galera container.

Filesystem backup variables:
* `backup_dirs` - List of the files to backup.
* `baclup_exclude` - List of the files that where not included on the backup.
* `backup_file` - The end of the backup file name.

Redis backup and restore variables:
* `redis_vip` - The VIP address of the Redis cluster.  If unsent, it checks the Puppet hieradata for the VIP.
* `redis_matherauth_password` - The master password for the Redis cluster.  If unsent, it checks the Puppet hieradata for the password.
* `redis_container_image` - The image to use for the temporary container that restores the permissions to the Redis data directory. If unset, it tries to determine the image from the existing redis container.

## Inventory and Playbooks ##

You ultimately define how to use the tasks with your own playbooks and inventory. The inventory should include the host groups and users to access each host type. For example:

~~~~
[my_backup_host]
192.0.2.200 ansible_user=backup

[my_target_host]
192.0.2.101 ansible_user=openstack
192.0.2.102 ansible_user=openstack
192.0.2.103 ansible_user=openstack

[all:vars]
backup_directory="/home/backup/my-backup-folder/"
~~~~

The process for your playbook depends largely on whether you want to backup or restore. However, the general process usually follows:

1. Initialize the backup host
2. Ensure SSH access from the backup host to your OpenStack nodes
3. Perform the backup or restore. If need be, you might need to set a bootstrap to carry out tasks to isolate on a single Target Host.
4. (Optional) If using a separate Backup Host (i.e. not the Control Host), disable SSH access from the backup host to your OpenStack nodes.

## Examples ##

The following examples show how to use the backup and restore tasks.

### Backup and restore galera and redis to a remote backup server ###

This example shows how to backup data to the `root` user on a remote backup server, and then restore it. The inventory file for both functions are the same:

~~~~
[backup]
192.0.2.250 ansible_user=root

[mysql]
192.0.2.101 ansible_user=heat-admin
192.0.2.102 ansible_user=heat-admin
192.0.2.103 ansible_user=heat-admin

[redis]
192.0.2.101 ansible_user=heat-admin
192.0.2.102 ansible_user=heat-admin
192.0.2.103 ansible_user=heat-admin

[all:vars]
backup_directory="/root/backup-test/"
~~~~

Backup Playbook:
~~~~
---
- name: Initialize backup host
  hosts: "{{ backup_hosts | default('backup') }}[0]"
  tasks:
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: initialize_backup_host

- name: Backup MySQL database
  hosts: "{{ target_hosts | default('mysql') }}[0]"
  vars:
    backup_server_hostgroup: "{{ backup_hosts | default('backup') }}"
  tasks:
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: enable_ssh
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: backup_mysql
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: disable_ssh

- name: Backup Redis database
  hosts: "{{ target_hosts | default('redis') }}[0]"
  vars:
    backup_server_hostgroup: "{{ backup_hosts | default('backup') }}"
  tasks:
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: enable_ssh
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: backup_redis
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: disable_ssh
~~~~

We do not need to include the bootstrap tasks with the backup since all tasks are performed by one of the Target Hosts.

Restore Playbook:
~~~~
---
- name: Initialize backup host
  hosts: "{{ backup_hosts | default('backup') }}[0]"
  tasks:
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: initialize_backup_host

- name: Restore MySQL database on galera cluster
  hosts: "{{ target_hosts | default('mysql') }}"
  vars:
    backup_server_hostgroup: "{{ backup_hosts | default('backup') }}"
  tasks:
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: set_bootstrap
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: enable_ssh
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: restore_galera
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: disable_ssh

- name: Restore Redis data
  hosts: "{{ target_hosts | default('redis') }}"
  vars:
    backup_server_hostgroup: "{{ backup_hosts | default('backup') }}"
  tasks:
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: set_bootstrap
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: enable_ssh
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: restore_redis
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: disable_ssh
~~~~

We include the bootstrap tasks with the backup since all Target Hosts are required for the restore but only certain operations are performed on one of the hosts.

### Backup and restore galera and redis to a combined control/backup host ###

This example shows how to back to a directory on the Control Host using the same user. In this case, we use the `stack` user for both Ansible and rsync operations. We also use the `heat-admin` user to access the OpenStack nodes. Both the backup and restore operations use the same inventory file:

~~~~
[backup]
localhost ansible_user=stack

[mysql]
192.0.2.101 ansible_user=heat-admin
192.0.2.102 ansible_user=heat-admin
192.0.2.103 ansible_user=heat-admin

[redis]
192.0.2.101 ansible_user=heat-admin
192.0.2.102 ansible_user=heat-admin
192.0.2.103 ansible_user=heat-admin

[all:vars]
backup_directory="/home/stack/backup-test/"
~~~~

Backup Playbook:
~~~~
---
- name: Initialize backup host
  hosts: "{{ backup_hosts | default('backup') }}[0]"
  tasks:
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: initialize_backup_host

- name: Backup MySQL database
  hosts: "{{ target_hosts | default('mysql') }}[0]"
  vars:
    backup_server_hostgroup: "{{ backup_hosts | default('backup') }}"
  tasks:
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: enable_ssh
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: backup_mysql

- name: Backup Redis database
  hosts: "{{ target_hosts | default('redis') }}[0]"
  vars:
    backup_server_hostgroup: "{{ backup_hosts | default('backup') }}"
  tasks:
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: backup_redis
~~~~

Restore Playbook:
~~~~
---
- name: Initialize backup host
  hosts: "{{ backup_hosts | default('backup') }}[0]"
  tasks:
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: initialize_backup_host

- name: Restore MySQL database on galera cluster
  hosts: "{{ target_hosts | default('mysql') }}"
  vars:
    backup_server_hostgroup: "{{ backup_hosts | default('backup') }}"
  tasks:
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: set_bootstrap
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: enable_ssh
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: restore_galera

- name: Restore MySQL database on galera cluster
  hosts: "{{ target_hosts | default('redis') }}"
  vars:
    backup_server_hostgroup: "{{ backup_hosts | default('backup') }}"
  tasks:
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: set_bootstrap
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: enable_ssh
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: restore_redis
~~~~

In This situation, we do not include the `disable_ssh` tasks since this would disable access from the Control Host to the OpenStack nodes for future Ansible operations.


### Backup filesystem from controller ###

Inventory file
~~~~
[backup]
undercloud-0 ansible_connection=local

[filesystem]
controller-0 ansible_user=heat-admin ansible_host=192.168.24.6
controller-1 ansible_user=heat-admin ansible_host=192.168.24.20
controller-2 ansible_user=heat-admin ansible_host=192.168.24.8

[all:vars]
backup_directory="/var/tmp/backup"
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
~~~~

Filesystem Backup Playbook:
~~~~
---
- name: Initialize backup host
  hosts: "{{ backup_hosts | default('backup') }}[0]"
  tasks:
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: initialize_backup_host

- name: Backup Filesystem
  hosts: "{{ target_hosts | default('filesystem') }}"
  become: yes
  vars:
    backup_server_hostgroup: "{{ backup_hosts | default('backup') }}"
    backup_file: "filesystem.bck.tar"
    backup_dirs:
      - /etc
      - /var/lib/nova
      - /var/lib/glance
      - /var/lib/heat-config
      - /var/lib/heat-cfntools
      - /var/lib/openvswitch
      - /var/lib/config-data
      - /var/lib/tripleo-config
      - /srv/node
      - /usr/libexec/os-apply-config/
      - /root
  tasks:
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: enable_ssh
    - import_role:
        name: ansible-role-openstack-operations
        tasks_from: backup_filesystem
~~~~

