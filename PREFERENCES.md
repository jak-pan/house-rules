# Project defaults

These preferences apply by default when Forge is installed. Explicit user choices and
repository instructions override them; an existing coherent project stack takes
precedence over defaults for new projects. Overrides need no separate approval ritual.
Record consequential choices and their rationale in the project, and preserve the host's
instruction hierarchy, access controls, and the authority boundaries in AGENTS.md.

## Choose only the components needed

| Need | Default | Why / when to override |
|---|---|---|
| Durable native or systems application, demanding long-lived service | Rust | Prefer native deployment and explicit types/resource control. Choose another stack when its ecosystem or project constraints fit better. Storage durability still requires recovery, migrations, and backups. |
| Ordinary web backend | TypeScript on Node.js | Reuse a language and tooling across backend, browser, and scripts. Use Rust when the service's requirements justify it. |
| Scripts and web libraries | Node.js, with TypeScript where useful | Reuse the project's runtime, dependencies, and types. In a Rust-only project, use existing Rust tooling or simple shell instead of adding Node for one script. |
| Browser frontend and visual prototype | Static Svelte + TypeScript, Vite, plain CSS | Simple asset deployment. Add SSR or a framework/service when a concrete product need justifies it; keep an existing UI stack. |
| Data analysis or scientific work | Python or the established domain ecosystem | Libraries and workflow can justify a different language, including Clojure. These can be maintained and shipped; they are not confined to throwaway code. |
| Mobile application | Native or Flutter | Choose for target platforms and team constraints; a web wrapper is acceptable when it meets the actual product needs. |
| Service deployment | Portable deployment, with OCI containers when useful | Preserve a practical VPS/cloud path by default; managed or platform-specific services are valid project choices. Static sites and small scripts need no container. |

Prefer one language when it meets the requirements. Before adding another, state the
concrete benefit and build/deployment/maintenance cost. A full Rust + Node + Svelte stack
is not required for a small tool. Reuse the pinned project toolchain; for new Node work,
prefer a supported LTS release, ESM, pnpm, and minimal dependencies. Do not require the
`ts-node` package merely because TypeScript executes on Node.

## Architecture and storage

Prefer one canonical representation of each datum and rebuildable derived indexes.
For document/vault products, start with Markdown and structured metadata; use an
append-only log when event history is intrinsic. For transactional application state,
a database can itself be canonical. Choose the storage and rebuild equivalence required
by the product; do not force every application into a Markdown vault.

Build for the agreed final product, using the simplest tenancy/deployment model that
meets it. Do not add multi-tenancy solely because a future product might need it.
Rust-specific tooling defaults live in `skills/rust-canon/SKILL.md`; architecture
procedures live in `skills/design-canon/SKILL.md`.

For a new project, use `project-bootstrap` to inspect constraints and settle only the
important unknowns. Ordinary feature work uses the project's recorded choices.
