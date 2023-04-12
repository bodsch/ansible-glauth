 
## `glauth_behaviors`

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
