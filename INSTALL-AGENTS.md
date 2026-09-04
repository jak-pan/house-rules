# Install Forge with an agent

This is the authoritative installation procedure. Forge intentionally has no
universal installer script: agent products use different instruction and Skill
locations, those locations evolve, and native Windows may require copies where
Unix-like systems can use symlinks.

The desired result is one permanent Forge source, preserved operator settings,
portable Forge-owned Skills, and a machine-local index of optional capabilities.
External products remain responsible for installing, updating, and removing
their own skills, clients, MCP servers, credentials, and other runtime state.

## Prompt for the destination agent

Replace the bundle location, then give the destination agent this prompt:

> Install Forge from the attached bundle or extracted directory. Read its
> INSTALL-AGENTS.md completely and follow it. Keep Forge in a permanent,
> user-owned location; preserve existing instructions and native settings;
> discover this machine's operating system, agent products, configuration
> homes, and supported Skill locations from the installed versions and current
> vendor documentation. Preview the exact files and links or copies you will
> create, install only for the products present or explicitly requested, and
> verify discovery in fresh sessions. Create Forge's gitignored custom/INDEX.md
> for machine-specific capabilities. Let self-installing products own their
> integrations and record only pointers to them. Never copy credentials,
> enrollment identity, caches, or source-machine paths.

## 1. Establish the source and platform

1. Put the complete Forge bundle in a permanent user-owned directory. Do not
   overlay an existing Forge directory until local changes have been compared.
2. Prefer a Git checkout or another backed-up source. The installation may work
   without Git, but an unversioned source is not safely recoverable or auditable.
3. Identify whether each agent runs natively on macOS, Linux, Windows, or inside
   WSL. Configure the environment that actually runs the agent. A WSL path does
   not configure a Windows-native desktop application.
4. Inspect current vendor documentation and the running product's configuration
   when they disagree. Do not rely on a path remembered from another computer.
5. Keep model selection, permissions, hooks, plugins, MCP configuration,
   credentials, and login state in each product's native configuration.

Current baseline locations are:

| Product | Global instructions | User Skills |
|---|---|---|
| Claude Code | `$CLAUDE_CONFIG_DIR/CLAUDE.md`, default `~/.claude/CLAUDE.md` | `$CLAUDE_CONFIG_DIR/skills/`, default `~/.claude/skills/` |
| Codex | `$CODEX_HOME/AGENTS.md`, default `~/.codex/AGENTS.md` | `~/.agents/skills/` |
| Kimi Code | `$KIMI_CODE_HOME/AGENTS.md`, default `~/.kimi-code/AGENTS.md` | `~/.agents/skills/`; `$KIMI_CODE_HOME/skills/` is Kimi-specific |

`~` means the real home directory of the operating-system user running the
agent. Use native Windows paths for Windows-native agents. Recheck these
baselines against current vendor documentation during installation.

## 2. Produce a no-write plan

Before changing anything, report:

- the permanent Forge source path;
- selected agent products and their resolved instruction and Skill locations;
- every Forge Skill found at `skills/<name>/SKILL.md`;
- whether each destination will use a directory symlink or a checked copy;
- instruction files that will change and their backup destinations;
- name conflicts, malformed existing Forge blocks, or policy that disables
  instructions or Skills;
- external capabilities already installed and the command or owner responsible
  for each one.

Prefer directory symlinks on platforms and products that support them. Use a
copy when symlinks are unavailable or inappropriate. A copied Skill must retain
its Forge source path and source revision in the installation report so updates
do not silently drift.

Never overwrite an unrelated file, directory, or symlink merely because its
name matches a Forge Skill. Reuse a link only when its canonical target is the
same Forge Skill. Update a copy only after proving it was installed from Forge
and has not been edited independently.

## 3. Install Forge-owned instructions and Skills

For each selected product:

1. Back up an existing global instruction file before changing it.
2. Add or replace exactly one block delimited by:

   ```text
   <!-- forge:begin -->
   <!-- forge:end -->
   ```

3. Inside that block, instruct the agent to read the permanent Forge
   `AGENTS.md` before non-trivial work, load only relevant Forge Skills, use
   `STRUCTURE.md` for artifact placement, and keep native product configuration
   outside Forge. Use resolved absolute paths from this computer. Install this
   exact adapter text, replacing `<FORGE_ROOT>` with the permanent absolute
   path:

   ```markdown
   <!-- forge:begin -->
   # Shared operating foundation (Forge)

   Before non-trivial work, read `<FORGE_ROOT>/AGENTS.md`. It is the canonical
   source for collaboration, verification, autonomy, and durable execution
   rules. Repository-local rules supply project details and win over shared
   preferences; all work remains subject to the host's instruction hierarchy
   and access controls.

   Load only the Forge Skills relevant to the task. Use
   `<FORGE_ROOT>/STRUCTURE.md` when deciding artifact paths and naming. Keep
   model, permission, MCP, plugin, and hook configuration in the native tool
   settings.
   <!-- forge:end -->
   ```
4. Preserve all content outside the managed block. Duplicate, incomplete, or
   reversed markers are a conflict requiring inspection; do not guess.
5. Codex loads `$CODEX_HOME/AGENTS.override.md` instead of `AGENTS.md` when it exists.
   If an override file is present, place the block there or remove the override
   deliberately; otherwise the Forge block is never read.
6. Install each Forge-owned Skill into `~/.agents/skills/` for Codex and Kimi.
   Do not use the legacy `$CODEX_HOME/skills/` location as the portable target.
7. Install the same Forge-owned Skills into Claude Code's native user Skill
   directory. A symlink may point directly to the Forge source; otherwise copy
   the complete Skill directory.
8. Do not install anything from `custom/` as though Forge owned it. Follow the
   ownership recorded in `custom/INDEX.md`.

Writes should be staged in the destination directory and atomically renamed
where the host supports it. If a multi-file operation fails, preserve backups,
report the partial state exactly, and either roll it back or finish it before
claiming installation success.

## 4. Maintain the machine-local custom index

Create `custom/INDEX.md` under the permanent Forge directory when it does not
exist. The entire `custom/` directory is gitignored because it describes one
machine's tools, paths, accounts, and verification state. Start from
`CUSTOM-INDEX.example.md`.

The index records optional Skills, plugins, MCP clients, browsers, and related
capabilities. For each entry record:

- capability name and kind;
- owning product or project;
- canonical installed path or native registry;
- install/update/uninstall authority;
- products that discover it;
- last verification date and result;
- any remaining login or consent requirement, without secrets.

Store a locally authored Skill under `custom/skills/<name>/` only when no
external product owns its lifecycle. Link or copy it into the necessary native
locations and record those projections in the index.

A self-installing product is different: keep its files in its own canonical
location and add only an index pointer. Such a product owns its runtime, any shared
Skill it installs (for example under `~/.agents/skills/`), native client adapters, MCP
registration, credentials, updates, repair, and removal. Forge must not vendor a
snapshot of it or pin its release state.

## 5. Verify actual discovery

Filesystem verification:

- every Forge Skill destination resolves to the intended source or matches the
  checked source bytes;
- every instruction file contains exactly one current Forge block and retains
  its surrounding operator content;
- no custom or externally managed capability was copied into Forge ownership;
- `custom/INDEX.md` points to paths that exist and identifies their real owner.

Runtime verification:

1. Start a fresh session for every selected product.
2. Ask it to identify its global instruction file, Forge source path, and the
   actual paths of the available Forge Skills.
3. Invoke one small, read-only Skill check.
4. Verify each external capability through its owner's supported status or
   doctor command. Do not treat a file's presence as runtime verification.
5. Do not start paid model runs merely to test installation unless the operator
   has authorized that cost.

Report filesystem and runtime verification separately.

## 6. Update and remove

To update Forge, compare the new source with the permanent source, preserve
local work, update it, then repeat planning and verification. Symlinked Skills
pick up source changes immediately; copied Skills require an explicit refresh.

To remove Forge, delete only links that still resolve into this Forge source and
copies proven to match a recorded Forge installation. Remove only the managed
Forge blocks from global instruction files. Restore a backup only after
comparing newer operator changes.

For an external capability listed in `custom/INDEX.md`, use its owner's update
or uninstall workflow. Removing its index entry does not uninstall it, and
deleting its files manually is not a substitute for its lifecycle command.
