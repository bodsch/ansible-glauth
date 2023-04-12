 
## `glauth_backends`

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
