import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const linter = fileURLToPath(new URL("./lint-report-set.mjs", import.meta.url));
const anchor = '<a id="evidence-sec-e01"></a>';
const heading = "### [[EVIDENCE:SEC-E01]] [1] Source inspection";
const report = `# Review
Status: DRAFT
Classification: INTERNAL
Date: 2026-09-09
Version: 0.1
Report contract: 1.0
Report owner: [[OWNER:UNASSIGNED; role=Reviewer]]
Evidence cut-off: 2026-09-09

SEC-01: Observed behavior. [1](#evidence-sec-e01)
[[QUESTION:Q-001]]

## Embedded evidence
[[EVIDENCE-APPENDIX:OPEN]]

${anchor}

${heading}

**Supports:** SEC-01
**Type and cut-off:** FACT; 2026-09-09.
**Method or origin:** Source inspection.
**Embedded record:** The observed behavior.
**Limits:** No runtime reproduction.
`;

function lint(markdown) {
  const scratch = resolve(".tmp");
  mkdirSync(scratch, { recursive: true });
  const directory = mkdtempSync(join(scratch, "report-anchor-test-"));
  try {
    writeFileSync(join(directory, "audit-report-set.json"), JSON.stringify({
      contractVersion: "1.0",
      questionBindingFile: "question-bindings.json",
      reports: [{ file: "report.md", kind: "specialist", claimPrefix: "SEC" }],
    }));
    writeFileSync(join(directory, "question-bindings.json"), JSON.stringify({
      schemaVersion: 1, scopeId: "anchor-regression", questionIds: ["Q-001"],
    }));
    writeFileSync(join(directory, "report.md"), markdown);
    const result = spawnSync(process.execPath, [linter, join(directory, "audit-report-set.json")], { encoding: "utf8" });
    assert.ifError(result.error);
    return { status: result.status, output: result.stdout + result.stderr };
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

test("explicit evidence anchor attached to its record passes", () => {
  const result = lint(report);
  assert.equal(result.status, 0, result.output);
});

for (const [name, markdown, error] of [
  ["missing", report.replace(anchor, ""), /requires explicit anchor/],
  ["mismatched", report.replace(anchor, '<a id="evidence-sec-e02"></a>'), /requires explicit anchor/],
  ["duplicate", report.replace(anchor, `${anchor}\n\n${anchor}`), /duplicate evidence anchor/],
  ["detached by prose", report.replace(anchor, `${anchor}\n\nIntervening text.`), /requires explicit anchor/],
  ["placed after record heading", report.replace(`${anchor}\n\n${heading}`, `${heading}\n\n${anchor}`), /requires explicit anchor/],
  ["placed in body", report.replace(anchor, "").replace("## Embedded evidence", `${anchor}\n\n## Embedded evidence`), /requires explicit anchor/],
  ["inside code fence", report.replace(anchor, `\`\`\`html\n${anchor}\n\`\`\``), /requires explicit anchor/],
  ["inside HTML comment", report.replace(anchor, `<!--\n${anchor}\n-->`), /requires explicit anchor/],
]) {
  test(`${name} evidence anchor is rejected`, () => {
    const result = lint(markdown);
    assert.equal(result.status, 1, result.output);
    assert.match(result.output, error);
  });
}

test("anchor validation preserves substantive evidence gates", () => {
  const result = lint(report.replace("**Limits:** No runtime reproduction.", ""));
  assert.equal(result.status, 1, result.output);
  assert.match(result.output, /evidence SEC-E01 is missing Limits/);
});
