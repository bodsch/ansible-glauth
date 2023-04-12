
# Ansible Role:  `glauth` 

Ansible role to install and configure [glauth](https://github.com/glauth/glauth).

[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/bodsch/ansible-glauth/main.yml?branch=main)][ci]
[![GitHub issues](https://img.shields.io/github/issues/bodsch/ansible-glauth)][issues]
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/bodsch/ansible-glauth)][releases]
[![Ansible Quality Score](https://img.shields.io/ansible/quality/50067?label=role%20quality)][quality]

[ci]: https://github.com/bodsch/ansible-glauth/actions
[issues]: https://github.com/bodsch/ansible-glauth/issues?q=is%3Aopen+is%3Aissue
[releases]: https://github.com/bodsch/ansible-glauth/releases
[quality]: https://galaxy.ansible.com/bodsch/glauth

If `latest` is set for `glauth_version`, the role tries to install the latest release version.  
**Please use this with caution, as incompatibilities between releases may occur!**

The binaries are installed below `/usr/local/bin/glauth/${glauth_version}` and later linked to `/usr/bin`. 
This should make it possible to downgrade relatively safely.

The downloaded archive is stored on the Ansible controller, unpacked and then the binaries are copied to the target system.
The cache directory can be defined via the environment variable `CUSTOM_LOCAL_TMP_DIRECTORY`. 
By default it is `${HOME}/.cache/ansible/glauth`.
If this type of installation is not desired, the download can take place directly on the target system. 
However, this must be explicitly activated by setting `glauth_direct_download` to `true`.

## Requirements & Dependencies

Ansible Collections

- [bodsch.core](https://github.com/bodsch/ansible-collection-core)
- [bodsch.scm](https://github.com/bodsch/ansible-collection-scm)

```bash
ansible-galaxy collection install bodsch.core
ansible-galaxy collection install bodsch.scm
```
or
```bash
ansible-galaxy collection install --requirements-file collections.yml
```


## Operating systems

Tested on

* Arch Linux
* Debian based
    - Debian 10 / 11
    - Ubuntu 20.10


## Contribution

Please read [Contribution](CONTRIBUTING.md)

## Development,  Branches (Git Tags)

The `master` Branch is my *Working Horse* includes the "latest, hot shit" and can be complete broken!

If you want to use something stable, please use a [Tagged Version](https://github.com/bodsch/ansible-glauth/tags)!

## Configuration

```yaml
glauth_version: 2.1.0

glauth_release_download_url: https://github.com/glauth/glauth/releases
glauth_release_api_url: https://api.github.com/repos/glauth/glauth/releases

glauth_system_user: glauth
glauth_system_group: glauth
glauth_config_dir: /etc/glauth
glauth_data_dir: /var/lib/glauth

glauth_direct_download: false

glauth_service: {}

glauth_config: {}

glauth_backends: {}

glauth_users: {}

glauth_groups: {}

glauth_behaviors: {}

glauth_api: {}
```
## Config for this role

| parameter                    | type      | default                                      | description |
| :---                         | :---      | :---                                         | :---        |
| `glauth_version`             | `string`  | `2.1.0`                                      | The version of glauth to install. Use `latest` to install the latest release version, but use with caution. |
| `glauth_system_user`         | `string`  | `glauth`                                     | User as which glauth shall run |
| `glauth_system_group`        | `string`  | `glauth`                                     | Group as which glauth shall run |
| `glauth_config_dir`          | `string`  | `/etc/glauth`                                | Directory with configuration for glauth |
| `glauth_data_dir`            | `string`  | `/var/lib/glauth`                            | Plugins will be installed into a subdirectory plugins/ of this directory |
| `glauth_install_path`        | `string`  | `/usr/local/bin/glauth/{{ glauth_version }}` | Location to install glauth to, it will be linked to `/usr/bin/glauth`, though |
| `glauth_direct_download`     | `bool`    | `false`                                      | Either download and unpack glauth on the local machine (`false`, or download it directly on the target host (`true`) |
| `glauth_local_tmp_directory` | `string`  | environment variable `CUSTOM_LOCAL_TMP_DIRECTORY`<br/>or `~/.cache/ansible/glauth/{{ glauth_version }}` | Path where to locally download glauth to |


- [glauth_service](docs/glauth_service.md)
- [glauth_config](docs/glauth_config.md)
- [glauth_backends](docs/glauth_backends.md)
- [glauth_users](docs/glauth_users.md)
- [glauth_groups](docs/glauth_groups.md)
- [glauth_behaviors](docs/glauth_behaviors.md)
- [glauth_api](docs/glauth_api.md)


---

## Author and License

- Bodo Schulz

## License

[Apache](LICENSE)

**FREE SOFTWARE, HELL YEAH!**
