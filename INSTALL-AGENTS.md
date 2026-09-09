# Install Groundwork with an agent

This is the authoritative installation procedure. Groundwork intentionally has no
universal installer script: agent products use different instruction and Skill
locations, those locations evolve, and native Windows may require copies where
Unix-like systems can use symlinks.

The desired result is one permanent Groundwork source, preserved operator settings,
portable Groundwork-owned Skills, and a machine-local index of optional capabilities.
The source includes PREFERENCES.md: its project defaults are active immediately, with
explicit user and repository overrides. Install project-bootstrap with the other Groundwork
skills; do not require users to opt into the default profile.
External products remain responsible for installing, updating, and removing
their own skills, clients, MCP servers, credentials, and other runtime state.

## Prompt for the destination agent

Replace `<GROUNDWORK_SOURCE>` with the downloaded bundle or permanent source location, then
give the destination agent this prompt:

> Install Groundwork globally from `<GROUNDWORK_SOURCE>`. Read its
> INSTALL-AGENTS.md completely and follow it. Keep Groundwork in a permanent,
> user-owned location; preserve existing instructions and native settings;
> discover this machine's operating system, agent products, configuration
> homes, and supported Skill locations from the installed versions and current
> vendor documentation. Preview the exact files and links or copies you will
> create, install only for the products present or explicitly requested, and
> verify discovery in fresh sessions. Create Groundwork's gitignored custom/INDEX.md
> for machine-specific capabilities. Let self-installing products own their
> integrations and record only pointers to them. Never copy credentials,
> enrollment identity, caches, or source-machine paths.

## 1. Establish the source and platform

1. Put the complete Groundwork bundle in a permanent user-owned directory. Do not
   overlay an existing Groundwork directory until local changes have been compared.
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

- the permanent Groundwork source path;
- selected agent products and their resolved instruction and Skill locations;
- every Groundwork Skill found at `skills/<name>/SKILL.md`;
- whether each destination will use a directory symlink or a checked copy;
- instruction files that will change and their backup destinations;
- name conflicts, malformed existing Groundwork blocks, or policy that disables
  instructions or Skills;
- external capabilities already installed and the command or owner responsible
  for each one.

Prefer directory symlinks on platforms and products that support them. Use a
copy when symlinks are unavailable or inappropriate. A copied Skill must retain
its Groundwork source path and source revision in the installation report so updates
do not silently drift.

Never overwrite an unrelated file, directory, or symlink merely because its
name matches a Groundwork Skill. Reuse a link only when its canonical target is the
same Groundwork Skill. Update a copy only after proving it was installed from Groundwork
and has not been edited independently.

## 3. Install Groundwork-owned instructions and Skills

For each selected product:

1. Back up an existing global instruction file before changing it.
2. Add or replace exactly one block delimited by:

   ```text
   <!-- groundwork:begin -->
   <!-- groundwork:end -->
   ```

3. Inside that block, instruct the agent to read the permanent Groundwork
   `AGENTS.md` at the start of every session, load only relevant Groundwork Skills, use
   `STRUCTURE.md` for artifact placement, and keep native product configuration
   outside Groundwork. Use resolved absolute paths from this computer. Install this
   exact adapter text, replacing `<GROUNDWORK_ROOT>` with the permanent absolute
   path:

   ```markdown
   <!-- groundwork:begin -->
   # Shared operating foundation (Groundwork)

   At the start of every session, read `<GROUNDWORK_ROOT>/AGENTS.md`. It is the canonical
   source for collaboration, verification, autonomy, and durable execution
   rules. Repository-local rules supply project details and win over shared
   preferences; all work remains subject to the host's instruction hierarchy
   and access controls.

   Load only the Groundwork Skills relevant to the task. Use
   `<GROUNDWORK_ROOT>/STRUCTURE.md` when deciding artifact paths and naming. Keep
   model, permission, MCP, plugin, and hook configuration in the native tool
   settings.
   <!-- groundwork:end -->
   ```
4. Older installations use `forge:begin` / `forge:end` markers. Back up and migrate that
   block in place to the Groundwork markers; never append a second block. The permanent
   source directory need not be renamed. Preserve all content outside the managed block. Duplicate, incomplete, or
   reversed markers are a conflict requiring inspection; do not guess.
5. Preserve human-authored existing rules in place unless the operator chooses a merge.
   For consolidation, first copy them to a machine-local
   `custom/external-rules/<tool>.md`, excluding third-party managed blocks. Review the
   proposed text and duplicates, then replace only that agreed original content with
   an explicit instruction to read the external file at session start. Keep tool-specific
   rules separate when their meanings differ. Record ownership and a backup in the receipt.
   This is an ordinary referenced file, not a new native instruction-discovery feature.
   Never move another product's managed block out of the file it updates.
6. Codex loads `$CODEX_HOME/AGENTS.override.md` instead of `AGENTS.md` when it exists.
   If an override file is present, place the block there or remove the override
   deliberately; otherwise the Groundwork block is never read.
7. Install each Groundwork-owned Skill into `~/.agents/skills/` for Codex and Kimi.
   Do not use the legacy `$CODEX_HOME/skills/` location as the portable target.
8. Install the same Groundwork-owned Skills into Claude Code's native user Skill
   directory. A symlink may point directly to the Groundwork source; otherwise copy
   the complete Skill directory.
9. Do not install anything from `custom/` as though Groundwork owned it. Follow the
   ownership recorded in `custom/INDEX.md`.

Writes should be staged in the destination directory and atomically renamed
where the host supports it. If a multi-file operation fails, preserve backups,
report the partial state exactly, and either roll it back or finish it before
claiming installation success.

Do not copy the shared base into each repository. Existing repository copies are a
migration case: compare their universal section to its known source revision, preserve
local edits and decisions, and remove only the verified duplicate section after review.
Unknown or conflicting content remains until reconciled. The global source owns shared
rules; repository files own local rules.

## 4. Maintain the machine-local custom index

Create `custom/INDEX.md` under the permanent Groundwork directory when it does not
exist. The entire `custom/` directory is gitignored because it describes one
machine's tools, paths, accounts, and verification state. Start from
`CUSTOM-INDEX.example.md`.

In a downloaded npm archive, `.gitignore` may be absent. Before creating machine-local
records, add `custom/` to the permanent source's `.gitignore` if missing, preserving
existing entries. Do not copy that source ignore file into projects using Groundwork.

Keep a durable installation receipt in `custom/installations/<tool>.json` or an equivalent
small Markdown table. Record the source revision or bundle digest, native instruction
file, managed block, optional external-rule file, every link/copy destination, installed
content hashes, backup locations, helper invocation, and filesystem/runtime verification.
Do not record secrets. The receipt is the ownership evidence used for update and removal.

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
registration, credentials, updates, repair, and removal. Groundwork must not vendor a
snapshot of it or pin its release state.

## 5. Verify actual discovery

Filesystem verification:

- every Groundwork Skill destination resolves to the intended source or matches the
  checked source bytes;
- every instruction file contains exactly one current Groundwork block and retains
  its surrounding operator content;
- no custom or externally managed capability was copied into Groundwork ownership;
- `custom/INDEX.md` points to paths that exist and identifies their real owner.

Helper availability:

- The text rules and skills can be available without their executable helpers.
- Git-backed tasks remain the default. The optional helper and report linter need Node.js
  22 or later. Invoke `node "<GROUNDWORK_ROOT>/bin/groundwork.mjs" task ...` from the target
  repository, or `npm exec --package="<GROUNDWORK_ROOT>" -- groundwork task ...`. Use native
  Windows paths when appropriate; no shell utilities are required. Check the runtime only
  when selecting helpers; do not install it silently. Git task files can be edited directly.
- The npm package is prepared but not published. Do not assume registry npx commands are
  available. An npm execution cache is temporary: never use it as the permanent source
  for native instruction pointers, skill links, or installation receipts. Unpack/download
  the distribution to a stable user-owned directory for global rules and skills.
- Existing helper links to the old zsh `bin/task` need updating. Identify them from the
  installation receipt and replace only Groundwork-owned links or aliases. Do not claim a
  bare `task` or `groundwork` command is ours without verifying its resolution.
- Resolve shared references such as STRUCTURE.md from the permanent Groundwork source.

Runtime verification:

1. Start a fresh session for every selected product.
2. Ask it to identify its global instruction file, Groundwork source path, and the
   actual paths of the available Groundwork Skills.
3. Use the product's discovery view and a read-only prompt, for example: “Identify the
   loaded Groundwork base path and available skills, then explain which rules apply to this
   simple question without creating a task.” For selected helpers, run their documented
   check in a disposable fixture; do not create verification tasks in a real project.
4. Verify each external capability through its owner's supported status or
   doctor command. Do not treat a file's presence as runtime verification.
5. Do not start paid model runs merely to test installation unless the operator
   has authorized that cost.

Report filesystem and runtime verification separately.

## 6. Update and remove

To update Groundwork, compare the new source with the permanent source, preserve
local work, update it, then repeat planning and verification. Symlinked Skills
pick up source changes immediately; copied Skills require an explicit refresh.

To remove Groundwork, delete only links that still resolve into this Groundwork source and
copies proven to match the receipt for this Groundwork installation. Preserve user-owned
external rules; restore or retain their native pointer after reviewing newer changes.
Remove only the managed
Groundwork blocks from global instruction files. Restore a backup only after
comparing newer operator changes.

For an external capability listed in `custom/INDEX.md`, use its owner's update
or uninstall workflow. Removing its index entry does not uninstall it, and
deleting its files manually is not a substitute for its lifecycle command.
