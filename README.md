# House Rules

Opinionated foundations for coding agents. Sensible defaults, fully overridable.

House Rules combines global working rules, project preferences, focused skills, and a
small Git-based task helper. Install it once; keep project-specific choices in each
repository. Explicit user choices and established project stacks override its defaults.

## What's included

- [AGENTS.md](AGENTS.md): collaboration, autonomy, verification, and communication rules.
- [PREFERENCES.md](PREFERENCES.md): Rust for durable native/systems work, TypeScript on
  Node for ordinary backends and scripts, static Svelte for browser UIs, and domain-specific
  alternatives where appropriate. Choose only the components needed.
- [STRUCTURE.md](STRUCTURE.md): default paths and naming for projects using House Rules.
- `skills/`: project bootstrap, design, implementation, experiments, diagnosis, reporting,
  and task coordination. Load only the relevant procedures.
- `bin/house-rules.mjs`: a Node CLI for the Git task protocol, with no runtime dependencies.

## Install the rules globally

Put the downloaded package or checkout in a permanent user-owned directory, for example
`~/house-rules` (not a downloads folder or an npm cache). Give your
agent the prompt in [INSTALL-AGENTS.md](INSTALL-AGENTS.md). It preserves existing native
instructions, adds a pointer to House Rules, and installs the skills in each product's
supported location. Models, permissions, plugins, and MCP connections stay in native
settings; external integrations remain owned by their products.

Do not copy the shared base into every project. Repository `AGENTS.md` and `CONTEXT.md`
hold local decisions. The `project-bootstrap` skill applies defaults automatically and
asks only about consequential unknowns. An override can be as simple as “This project
uses Python and FastAPI; retain that stack.”

## Use the task helper

The helper targets Windows, macOS, and Linux with **Node.js 22 or later**. It uses Node
filesystem APIs rather than zsh, awk, sed, or other system utilities. Git remains the
tracker; the helper only maintains Markdown files in the project where you run it.

From inside the target project, run the helper by its path in your permanent House Rules
directory:

```sh
node "/path/to/house-rules/bin/house-rules.mjs" task new "Build the first version"
node "/path/to/house-rules/bin/house-rules.mjs" task board
```

For local npm execution from a downloaded package/checkout:

```sh
npm exec --package="/path/to/house-rules" -- house-rules --help
```

Use a native Windows path on Windows. After the prepared `@jak-pan/house-rules` package
is published, the equivalent registry command will be:

```sh
npx @jak-pan/house-rules task board
```

**The npm package is not published yet.** The unscoped npm name `house-rules` belongs to an
unrelated package: use `@jak-pan/house-rules` or a local `--package` path. `npx` is for invoking the helper; its temporary cache is not a permanent
source for global instruction or skill links. See [task-protocol](skills/task-protocol/SKILL.md)
for ownership, handoffs, release, and closeout. Plain Git task files also work without
Node or the helper.

## Package and verify

`npm pack --dry-run` lists the distribution contents. `npm pack` creates an archive
containing only the files allowlisted in package.json: no machine-local configuration,
development records, or Git history. Publish that archive; the Git history is not a
publication artifact.

CI checks JavaScript syntax, CLI startup and reported version, and lists package contents
on Windows, macOS, and Linux. This is a smoke check, not proof of every operation or
native agent's discovery. The source repository intentionally keeps no development task
backlog or test suite; record maintenance decisions in commits. Projects using House Rules
still use Git task files by default and keep their own tests.

Attribution is in [NOTICE.md](NOTICE.md); the license is [MIT](LICENSE).
