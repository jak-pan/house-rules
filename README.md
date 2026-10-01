# House Rules

Opinionated foundations for coding agents. Sensible defaults, fully overridable.

House Rules combines global working rules, project preferences, and focused skills.
Install it once; keep project-specific choices in each repository. Explicit user choices
and established project stacks override its defaults.

## What's included

- [AGENTS.md](AGENTS.md): collaboration, autonomy, verification, and communication rules.
- [PREFERENCES.md](PREFERENCES.md): Rust for durable native/systems work, TypeScript on
  Node for ordinary backends and scripts, static Svelte for browser UIs, and domain-specific
  alternatives where appropriate. Choose only the components needed.
- [STRUCTURE.md](STRUCTURE.md): default paths and naming for projects using House Rules.
- `skills/`: project bootstrap, design, implementation, the PR change loop, upstream
  contributions, experiments, diagnosis, reporting, and work tracking. Load only the
  relevant procedures. The audit-report skill includes an optional structural linter that
  needs Node.js 22 or later; nothing else needs Node.

## Install the rules globally

Clone the repository to a permanent user-owned directory:

```sh
git clone https://github.com/jak-pan/house-rules.git ~/house-rules
```

Then give your agent the prompt in [INSTALL-AGENTS.md](INSTALL-AGENTS.md). It preserves existing native
instructions, adds a pointer to House Rules, and installs the skills in each product's
supported location. Models, permissions, plugins, and MCP connections stay in native
settings; external integrations remain owned by their products.

Do not copy the shared base into every project. Repository `AGENTS.md` and `CONTEXT.md`
hold local decisions. The `project-bootstrap` skill applies defaults automatically and
asks only about consequential unknowns. An override can be as simple as “This project
uses Python and FastAPI; retain that stack.”

## Track work

By default, work is recorded in Git: claims, handoffs, and experiment attempts are
commits on each item's work branch, so tracking works offline. When the Git host is
reachable, they are mirrored to issues on its project board. The
[work-tracking](skills/work-tracking/SKILL.md) skill covers claims, handoffs, offline
sync, branches, and pull requests; on GitHub, agents use `gh` with the `project` token
scope.

## Verify

CI checks the report linter's JavaScript syntax. This is a
smoke check, not proof of the linter's behavior or of any agent's discovery. The source
repository also has local preparer/panel integration tests using temporary Git repositories
and stub CLIs, with no network or model calls. Run them before committing preparer changes:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/pr-ready/scripts -p test_prepare.py
bash -n skills/pr-ready/scripts/review-panel.sh
```

These tests currently run locally, not in CI. Projects using House Rules keep their own tests.

Approved changes to House Rules land on `main`; never leave one parked on a side branch and
report it as done. Commit with the maintainer's GitHub noreply identity and UTC timestamps
(`TZ=UTC git commit`).

Attribution is in [NOTICE.md](NOTICE.md); the license is [MIT](LICENSE).
