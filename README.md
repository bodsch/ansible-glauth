
# Ansible Role:  `glauth` 

Ansible role to install and configure [glauth](https://github.com/glauth/glauth).

[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/bodsch/ansible-glauth/CI)][ci]
[![GitHub issues](https://img.shields.io/github/issues/bodsch/ansible-glauth)][issues]
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/bodsch/ansible-glauth)][releases]

[ci]: https://github.com/bodsch/ansible-glauth/actions
[issues]: https://github.com/bodsch/ansible-glauth/issues?q=is%3Aopen+is%3Aissue
[releases]: https://github.com/bodsch/ansible-glauth/releases


If `latest` is set for `glauth_version`, the role tries to install the latest release version.  
**Please use this with caution, as incompatibilities between releases may occur!**

The binaries are installed below `/usr/local/bin/glauth/${glauth_version}` and later linked to `/usr/bin`. 
This should make it possible to downgrade relatively safely.

The Prometheus archive is stored on the Ansible controller, unpacked and then the binaries are copied to the target system.
The cache directory can be defined via the environment variable `CUSTOM_LOCAL_TMP_DIRECTORY`. 
By default it is `${HOME}/.cache/ansible/glauth`.
If this type of installation is not desired, the download can take place directly on the target system. 
However, this must be explicitly activated by setting `glauth_direct_download` to `true`.


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

```

### `glauth_service`

| parameter | glauth version | type    | default | description |
| :---      | :---           | :---    | :---    | :---        |
| ``        | 2.1            | ``      | `-`     |             |
| ``        | 2.1            | ``      | `-`     |             |
| ``        | 2.1            | ``      | `-`     |             |
| ``        | 2.1            | ``      | `-`     |             |
| ``        | 2.1            | ``      | `-`     |             |

```yaml
glauth_service: {}
```

### `glauth_config`

| parameter          | glauth version | type     | default | description |
| :---               | :---           | :---     | :---    | :---        |
| `debug`            | 2.1            | `bool`   | `false` |             |
| `syslog`           | 2.1            | `bool`   | `true`  |             |
| `watch_config`     | 2.1            | `bool`   | `true`  | Enable hot-reload of configuration on changes<br>**does NOT work [ldap], [ldaps], [backend] or [api] sections** |
| `yubikey.clientid` | 2.1            | `string` | `-`     |             |
| `yubikey.secret`   | 2.1            | `string` | `-`     |             |

```yaml
glauth_config: {}
```

### `glauth_backends`

| parameter        | glauth version | type     | default | description |
| :---             | :---           | :---     | :---    | :---        |
| `base_dn`        | 2.1            | `string` | `-`     |             |
| `name_format`    | 2.1            | `string` | `-`     |             |
| `group_format`   | 2.1            | `string` | `-`     |             |
| `insecure`       | 2.1            | `bool`   | `-`     |             |
| `servers`        | 2.1            | `list`   | `-`     |             |
| `sshkeyattr`     | 2.1            | `string` | `-`     |             |
| `use_graph_api`  | 2.1            | `bool`   | `-`     |             |
| `plugin`         | 2.1            | `string` | `-`     |             |
| `plugin_handler` | 2.1            | `string` | `-`     |             |
| `database`       | 2.1            | `string` | `-`     |             |
| `anonymous_dse`  | 2.1            | `string` | `-`     |             |


```yaml
glauth_backends:
  config:
    base_dn: "dc=molecule,dc=lan"
    name_format: "cn"
    group_format: "ou"
```

### `glauth_frontends`

| parameter         | glauth version | type      | default  | description |
| :---              | :---           | :---      | :---     | :---        |
| `allowed_base_dn` | 2.1            | `string`  | `-`      |             |
| `listen.address`  | 2.1            | `string`  | `0.0.0.0`|             |
| `listen.port`     | 2.1            | `int`     | `5555`   |             |
| `tls.enabled`     | 2.1            | `bool`    | `-`      |             |
| `tls.cert_file`   | 2.1            | `string`  | `-`      |             |
| `tls.key_file`    | 2.1            | `string`  | `-`      |             |

```yaml
glauth_frontends: {}
```

### `glauth_users`

| parameter          | glauth version | type     | default | description |
| :---               | :---           | :---     | :---    | :---        |
| `enabled`          | 2.1            | `bool`   | `-`     |             |
| `given_name`       | 2.1            | `string` | `-`     | First Name  |
| `sn`               | 2.1            | `string` | `-`     | Last Name   |
| `mail`             | 2.1            | `string` | `-`     |             |
| `uid`              | 2.1            | `int`    | `-`     | User ID     |
| `primary_group`    | 2.1            | `int`    | `-`     |             |
| `other_groups`     | 2.1            | `list`   | `-`     |             |
| `pass.sha256`      | 2.1            | `string` | `-`     |             |
| `pass.sha256_apps` | 2.1            | `list`   | `-`     | Specify an array of app passwords which can also succesfully bind - these bypass the OTP check. Hash the same way as password.            |
| `pass.bcrypt`      | 2.1            | `string` | `-`     |             |
| `pass.bcrypt_apps` | 2.1            | `list`   | `-`     | Specify an array of app passwords which can also succesfully bind - these bypass the OTP check. Hash the same way as password.            |
| `ssh_keys`         | 2.1            | `list`   | `-`     |             |
| `otp_secret`       | 2.1            | `string` | `-`     |             |
| `yubikey`          | 2.1            | `string` | `-`     |             |
| `login_shell`      | 2.1            | `string` | `-`     |             |
| `home_dir`         | 2.1            | `string` | `-`     |             |
| `capabilities`     | 2.1            | `dict`   | `-`     |             |
| `custom_attrs`     | 2.1            | `dict`   | `-`     |             |


#### create sha256 password

```bash
echo -n "PASSWORD" | openssl dgst -sha256
(stdin)= 0be64ae89ddd24e225434de95d501711339baeee18f009ba9b4369af27d30d60
```

#### create sha256 password

```bash
pip install bcrypt
python -c 'import bcrypt; print(bcrypt.hashpw(b"password", bcrypt.gensalt(rounds=10)))'
b'$2b$10$8GTQxz.fgT3XNj2W7ruhmuXS/YMlakp/ZL5UkbDz1y2uIrbYNSwim'
```



#### `capabilities`

[see upstream doku](https://glauth.github.io/docs/capabilities.html)

| parameter | glauth version | type    | default | description |
| :---      | :---           | :---    | :---    | :---        |
| `object`  | 2.1            | ``      | `-`     |             |

#### `custom_attrs`

[see upstream doku](https://glauth.github.io/docs/custom-attributes.html)

| parameter | glauth version | type    | default | description |
| :---      | :---           | :---    | :---    | :---        |
| ``        | 2.1            | ``      | `-`     |             |
| ``        | 2.1            | ``      | `-`     |             |


```yaml
glauth_users:
  admin:
    enabled: true
    given_name: Admin
    mail: "admin@matrix.lan"
    uid: 3000
    primary_group: 3000
    pass:
      sha256: "6b7556f632dc73ea7470a0116d6e55880fda6ca50575b72c7cc5f13df53a2623"
    login_shell: "/bin/bash"
    capabilities:
      "search":
        object: "dc=molecule,dc=lan"

  bodsch:
    given_name: "B."
    sn: "Schulz"
    uid: 6000
    primary_group: 6000
    pass:
      sha256: "6b7556f632dc73ea7470a0116d6e55880fda6ca50575b72c7cc5f13df53a2623"
      sha256_apps:
        - "fc6be9b218afa2ce37409580b8a4907feb6c1ea878d1222e4d2b84e81c1c0e47"
        - "cd2eb0837c9b4c962c22d2ff8b5441b7b45805887f051d39bf133b583baf6860"
    ssh_keys:
      - "ssh-ed25519 ... bodsch@matrix.lan"
    login_shell: "/bin/bash"
    home_dir: "/home/bodsch"
    capabilities:
      "search":
        object: "dc=molecule,dc=lan"
```

### `glauth_groups`

| parameter        | glauth version | type    | default | description |
| :---             | :---           | :---    | :---    | :---        |
| `gid`            | 2.1            | `int`   | `-`     |             |
| `include_groups` | 2.1            | `list`  | `-`     |             |

```yaml
glauth_groups:
  admins:
    gid: 3000
  vpn:
    gid: 3001
  users:
    gid: 6000
    include_groups:
      - 3001
```

### `glauth_behaviors`

| parameter                   | glauth version | type    | default | description |
| :---                        | :---           | :---    | :---    | :---        |
| `ignore_capabilities`       | 2.1            | `bool`  | `false` | Ignore all capabilities restrictions, for instance allowing every user to perform a search |
| `limit_failed_binds`        | 2.1            | `bool`  | `true`  | Enable a "fail2ban" type backoff mechanism temporarily banning repeated failed login attempts |
| `number_of_failed_binds`    | 2.1            | `int`   | `3`     | How many failed login attempts are allowed before a ban is imposed |
| `period_of_failed_binds`    | 2.1            | `int`   | `10`    | How long (in seconds) is the window for failed login attempts |
| `block_failed_binds_for`    | 2.1            | `int`   | `60`    | How long (in seconds) is the ban duration |
| `prune_source_table_every`  | 2.1            | `int`   | `600`   | Clean learnt IP addresses every N seconds |
| `prune_sources_older_than`  | 2.1            | `int`   | `600`   | Clean learnt IP addresses not seen in N seconds |

```yaml

glauth_behaviors:
  ignore_capabilities: false
  limit_failed_binds: true
  number_of_failed_binds: 3
  period_of_failed_binds: 10
  block_failed_binds_for: 60
  prune_source_table_every: 600
  prune_sources_older_than: 600
```

### `glauth_api`

| parameter        | glauth version | type      | default     | description |
| :---             | :---           | :---      | :---        | :---        |
| `enabled`        | 2.1            | `bool`    | `false`     |             |
| `internals`      | 2.1            | `bool`    | `true`      |             |
| `listen.address` | 2.1            | `string`  | `127.0.0.1` |             |
| `listen.port`    | 2.1            | `int`     | `5555`      |             |
| `tls.cert_file`  | 2.1            | `string`  | `-`         |             |
| `tls.key_file`   | 2.1            | `string`  | `-`         |             |
| `secret_token`   | 2.1            | `string`  | `-`         |             |

```yaml
glauth_api:
  enabled: true
  listen:
    address: "0.0.0.0"
```




---

## Author and License

- Bodo Schulz

## License

[Apache](LICENSE)

`FREE SOFTWARE, HELL YEAH!`
