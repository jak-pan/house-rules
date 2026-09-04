# Machine-local capability index

Copy this file to `custom/INDEX.md` during installation. The destination is
gitignored and belongs to one machine; never put credentials, tokens, private
enrollment material, or copied account configuration in it.

## Host

| Field | Value |
|---|---|
| Operating environment | `<macOS, Linux, Windows, or WSL>` |
| Forge source | `<absolute path>` |
| Updated | `<YYYY-MM-DD>` |

## Capabilities

| Capability | Kind | Owner | Canonical location | Lifecycle command or authority | Discovered by | Last verification |
|---|---|---|---|---|---|---|
| `<self-installing tool>` | Skill + client + MCP | `<its vendor>` | `~/.agents/skills/<name>` plus native client registrations | the vendor's supported install/update/uninstall workflow | `<actual agents>` | `<date and result>` |
| `<name>` | `<Skill, plugin, MCP, browser, or other>` | `<owning product/project or local>` | `<resolved path or native registry>` | `<supported command or responsible owner>` | `<actual agents>` | `<date and result>` |

## Local Skills

Only Skills with no external lifecycle owner belong under
`custom/skills/<name>/`. Record every native symlink or copy here so it can be
updated or removed without guessing.

| Skill | Source | Native projections | Installation mode | Last verification |
|---|---|---|---|---|
| `<name>` | `<absolute custom/skills path>` | `<resolved agent paths>` | `<symlink or copy>` | `<date and result>` |

## Pending operator actions

- `<login, exact consent, or unresolved ownership conflict; never include a secret>`
