# Install House Rules with an agent

This is the authoritative installation procedure. House Rules intentionally has no
universal installer script: agent products use different instruction and Skill
locations, those locations evolve, and native Windows may require copies where
Unix-like systems can use symlinks.

The desired result is one permanent House Rules source, preserved operator settings,
portable House Rules Skills, and a machine-local index of optional capabilities.
The source includes PREFERENCES.md: its project defaults are active immediately, with
explicit user and repository overrides. Install project-bootstrap with the other House Rules
skills; do not require users to opt into the default profile.
External products remain responsible for installing, updating, and removing
their own skills, clients, MCP servers, credentials, and other runtime state.

## Prompt for the destination agent

Replace `<HOUSE_RULES_SOURCE>` with the downloaded bundle or permanent source location, then
give the destination agent this prompt:

> Install House Rules globally from `<HOUSE_RULES_SOURCE>`. Read its
> INSTALL-AGENTS.md completely and follow it. Keep House Rules in a permanent,
> user-owned location; preserve existing instructions and native settings;
> discover this machine's operating system, agent products, configuration
> homes, and supported Skill locations from the installed versions and current
> vendor documentation. Preview the exact files and links or copies you will
> create, install only for the products present or explicitly requested, and
> verify discovery in fresh sessions. Create the gitignored custom/INDEX.md in House Rules
> for machine-specific capabilities. Let self-installing products own their
> integrations and record only pointers to them. Never copy credentials,
> enrollment identity, caches, or source-machine paths.

## 1. Establish the source and platform

1. Put the complete House Rules bundle in a permanent user-owned directory. Do not
   overlay an existing House Rules directory until local changes have been compared.
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
| Kimi Code | `$KIMI_CODE_HOME/AGENTS.md`, default `~/.kimi-code/AGENTS.md` | `~/.agents/skills/` (Kimi also scans `$KIMI_CODE_HOME/skills/`; do not install there) |

Verified 2026-09-28 with Claude Code 2.1, Codex CLI 0.153 and Kimi Code 0.41. `~` means
the real home directory of the operating-system user running the agent. Use native
Windows paths for Windows-native agents. Recheck these baselines against current vendor
documentation during installation.

A product may run with several configuration homes, for example Codex accounts launched
with different `CODEX_HOME` folders. Find each one: ask the operator and check launchers,
shell aliases and wrapper apps that set the variable. A folder is a Codex home only if it
contains `config.toml` or `auth.json`. Every home gets its own managed block, override
check and receipt. `~/.agents/skills/` is shared by all Codex homes and Kimi: install it
once and remove it only when no configured product still uses House Rules.

## 2. Produce a no-write plan

Before changing anything, report:

- the permanent House Rules source path;
- selected agent products, every configuration home, and their resolved instruction and
  Skill locations;
- every House Rules Skill found at `skills/<name>/SKILL.md`;
- whether each destination will use a directory symlink or a checked copy;
- instruction files that will change and their backup destinations;
- stale entries to remove (§3 steps 5 and 8), name conflicts, malformed existing blocks,
  or policy that disables instructions or Skills;
- external capabilities already installed and the command or owner responsible
  for each one.

Prefer directory symlinks on platforms and products that support them. Use a
copy when symlinks are unavailable or inappropriate; native Windows needs Developer Mode
or elevation for symlinks. A copied Skill must retain its House Rules source path and
source revision in the installation report so updates do not silently drift.

Never overwrite an unrelated file, directory, or symlink merely because its
name matches a House Rules Skill. A link is owned by House Rules when its target as
written, even if that target no longer exists, is `<root>/skills/<same name>` for the
current source root or a previous root recorded in a receipt. A copy is owned only when
it matches a receipt. Reuse or replace only owned entries; report any other same-name
entry as a conflict.

## 3. Install House Rules instructions and Skills

For each selected product and configuration home:

1. Back up an existing global instruction file before changing it. If the file is a
   symlink, edit its resolved target; never replace the link itself.
2. Add or replace exactly one block delimited by:

   ```text
   <!-- house-rules:begin -->
   <!-- house-rules:end -->
   ```

3. Inside that block, instruct the agent to read the permanent House Rules
   `AGENTS.md` at the start of every session, load only relevant House Rules Skills, use
   `STRUCTURE.md` for artifact placement, and keep native product configuration
   outside House Rules. Use resolved absolute paths from this computer. Install this
   exact adapter text, replacing `<HOUSE_RULES_ROOT>` with the permanent absolute
   path:

   ```markdown
   <!-- house-rules:begin -->
   # Shared operating foundation (House Rules)

   At the start of every session, read `<HOUSE_RULES_ROOT>/AGENTS.md`. It is the canonical
   source for collaboration, verification, autonomy, and durable execution
   rules. Repository-local rules supply project details and win over shared
   preferences; all work remains subject to the host's instruction hierarchy
   and access controls.

   Load only the House Rules Skills relevant to the task. Use
   `<HOUSE_RULES_ROOT>/STRUCTURE.md` when deciding artifact paths and naming. Keep
   model, permission, MCP, plugin, and hook configuration in the native tool
   settings.
   <!-- house-rules:end -->
   ```
4. Older installations use the project's earlier names: `<!-- forge:begin -->` /
   `<!-- forge:end -->` or `<!-- groundwork:begin -->` / `<!-- groundwork:end -->`.
   Back up and migrate that block in place to the House Rules markers; never append a
   second block. Count all three marker families together: a file with more than one
   block, or with incomplete or reversed markers, is a conflict requiring inspection;
   do not guess. Preserve all content outside the managed block.
5. Put the block only in each product's global instruction file. Claude Code also loads
   `AGENTS.md` and `CLAUDE.md` from the parent folders of its working directory, so a
   House Rules, Forge or Groundwork block in `~/AGENTS.md`, `~/CLAUDE.md` or a
   workspace parent folder loads a second copy. Search those locations; back up and
   remove such a block instead of migrating it.
6. Preserve human-authored existing rules in place unless the operator chooses a merge.
   For consolidation, first copy them to a machine-local
   `custom/external-rules/<tool>.md`, excluding third-party managed blocks. Review the
   proposed text and duplicates, then replace only that agreed original content with
   an explicit instruction to read the external file at session start. Keep tool-specific
   rules separate when their meanings differ. Record ownership and a backup in the receipt.
   This is an ordinary referenced file, not a new native instruction-discovery feature.
   Never move another product's managed block out of the file it updates.
7. Codex loads `$CODEX_HOME/AGENTS.override.md` instead of `AGENTS.md` when it exists.
   If an override file is present in a home, place the block there; otherwise the House
   Rules block is never read. Delete or rename an override only with operator approval
   and a backup.
8. Install each House Rules Skill into `~/.agents/skills/` for Codex and Kimi. Then
   check the other folders those products scan — `$CODEX_HOME/skills/` in every Codex
   home and `$KIMI_CODE_HOME/skills/` — for entries with a House Rules Skill name.
   Codex reads `$CODEX_HOME/skills/` first and keeps the first Skill of each name, so a
   stale entry there hides the new one. Record each owned entry (ownership rule in §2)
   in the receipt, then remove it. Report other same-name entries as conflicts. Never
   touch `$CODEX_HOME/skills/.system/`.
9. Install the same House Rules Skills into Claude Code's native user Skill
   directory. A symlink may point directly to the House Rules source; otherwise copy
   the complete Skill directory.
10. Do not install anything from `custom/` as though House Rules owned it. Follow the
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

Create `custom/INDEX.md` under the permanent House Rules directory when it does not
exist. The entire `custom/` directory is gitignored because it describes one
machine's tools, paths, accounts, and verification state. Start from
`CUSTOM-INDEX.example.md`.

Keep one durable installation receipt per product home in `custom/installations/` (JSON
or a small Markdown table) and list the receipts in `custom/INDEX.md`. Record the source
root and any previous roots, the source revision (`git rev-parse HEAD`), native instruction file, managed block, optional external-rule file,
every link/copy destination, installed content hashes, backup locations, helper
invocation, and filesystem/runtime verification. Do not record secrets. The receipt is
the ownership evidence used for update and removal.

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
registration, credentials, updates, repair, and removal. House Rules must not vendor a
snapshot of it or pin its release state.

## 5. Verify actual discovery

Filesystem verification:

- every House Rules Skill destination resolves to the intended source or matches the
  checked source bytes;
- every instruction file contains exactly one House Rules block (counting old `forge:`
  and `groundwork:` markers too) and retains its surrounding operator content;
- no other scanned Skill folder or parent-folder instruction file holds a stale House
  Rules, Forge or Groundwork entry;
- no custom or externally managed capability was copied into House Rules ownership;
- `custom/INDEX.md` points to paths that exist and identifies their real owner.

Helper availability:

- The text rules and skills can be available without their executable helpers.
- Git-backed tasks remain the default. The optional helper and report linter need Node.js
  22 or later. Invoke `node "<HOUSE_RULES_ROOT>/bin/house-rules.mjs" task ...` from the target
  repository. Use native Windows paths when appropriate; no shell utilities are required.
  Check the runtime only when selecting helpers; do not install it silently. Git task
  files can be edited directly.
- Existing helper links to the old zsh `bin/task` need updating. Identify them from the
  installation receipt and replace only House Rules links or aliases. Do not claim a
  bare `task` or `house-rules` command is ours without verifying its resolution.
- Resolve shared references such as STRUCTURE.md from the permanent House Rules source.

Runtime verification:

1. Prefer discovery views that make no model call. For Codex, run
   `CODEX_HOME=<home> codex debug prompt-input` for every home: the output must contain
   exactly one `Shared operating foundation (House Rules)` heading, list each House Rules
   Skill once, and contain no Forge or Groundwork text. For Claude Code, check `/memory`
   in a fresh session. Claude Code drops HTML comments from loaded instructions, so check
   the heading rather than the markers.
2. Where no such view exists, or the operator asks for it, start a fresh session with a
   read-only prompt, for example: “Identify the loaded House Rules base path and available
   skills, then explain which rules apply to this simple question without creating a
   task.” These are model runs: start them only when the operator has authorized that
   cost, and treat the model's self-description as supporting evidence.
3. For selected helpers, run their documented check in a disposable fixture; do not
   create verification tasks in a real project.
4. Verify each external capability through its owner's supported status or
   doctor command. Do not treat a file's presence as runtime verification.

Report filesystem and runtime verification separately.

## 6. Update and remove

`custom/` holds this machine's index, receipts, backups and any external rules, inside the
source folder. Never use a temporary folder such as a downloads folder or a package-manager
cache as the source.

To update, pull the Git checkout, then repeat planning and verification. Compare the Skill list with the receipt:
link new Skills and remove owned links to Skills that no longer exist. Symlinked Skills
pick up source changes immediately; copied Skills require an explicit refresh.

If the source folder moves, update every managed block and owned link, search instruction
files and repository `AGENTS.md` files for the old root path, and record the old root in
the receipts.

To remove House Rules:

1. Replace each native pointer to `custom/external-rules/<tool>.md` with that file's
   current content, after comparing it with the backup.
2. Delete only owned links (ownership rule in §2, including broken links) and copies
   proven to match a receipt.
3. Remove only the managed House Rules blocks from global instruction files. Restore a
   backup only after comparing newer operator changes.
4. Copy `custom/` elsewhere if the operator wants its backups and receipts, then delete
   the source folder.

For an external capability listed in `custom/INDEX.md`, use its owner's update
or uninstall workflow. Removing its index entry does not uninstall it, and
deleting its files manually is not a substitute for its lifecycle command.
