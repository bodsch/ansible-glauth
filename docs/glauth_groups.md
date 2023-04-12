 
## `glauth_groups`

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
