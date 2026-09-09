import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const cli = fileURLToPath(new URL("../bin/task", import.meta.url));

function fixture(t) {
  mkdirSync(resolve(".tmp"), { recursive: true });
  const root = mkdtempSync(resolve(".tmp/task-test-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  mkdirSync(join(root, "tools"));
  const fakeDate = join(root, "tools/date");
  writeFileSync(fakeDate, '#!/bin/zsh\ncase "$*" in\n*%Y%m%d*) print 20260909-120000;;\n*) print 2026-09-09T12:00:00Z;;\nesac\n');
  chmodSync(fakeDate, 0o755);
  const runAs = (agent, ...args) => {
    const result = spawnSync("zsh", [cli, ...args], {
      cwd: root, encoding: "utf8",
      env: { ...process.env, TASKS_DIR: "tasks", AGENT_NAME: agent, PATH: `${root}/tools:${process.env.PATH}` },
    });
    assert.ifError(result.error);
    return { status: result.status, output: result.stdout + result.stderr };
  };
  return { root, run: (...args) => runAs("tester", ...args), runAs };
}

function fillHandoff(root, file) {
  writeFileSync(join(root, file), "# Handoff\n\n## Objective\nFinish the repair.\n\n## Completed\nTests passed: tests/task.test.mjs.\n\n## Pending\nNone.\n\n## Blockers\nNone.\n\n## Decisions\nKeep Git as the tracker.\n");
}

function ok(result) { assert.equal(result.status, 0, result.output); return result.output.trim(); }

test("same-second handoffs preserve earlier evidence and sort in creation order", (t) => {
  const { root, run } = fixture(t);
  ok(run("new", "First"));
  ok(run("claim", "001"));
  const first = ok(run("handoff", "001"));
  writeFileSync(join(root, first), "preserved evidence\n");
  const second = ok(run("handoff", "001"));
  assert.notEqual(first, second);
  assert.equal(readFileSync(join(root, first), "utf8"), "preserved evidence\n");
  assert.deepEqual([first, second].sort(), [first, second]);
  assert.match(ok(run("board")), new RegExp(second.split("/").at(-1).replaceAll(".", "\\.")));
});

test("allocation and board include task IDs above 999", (t) => {
  const { root, run } = fixture(t);
  mkdirSync(join(root, "tasks/999-prior"), { recursive: true });
  assert.match(ok(run("new", "Thousand")), /^tasks\/1000-/);
  assert.match(ok(run("new", "Next")), /^tasks\/1001-/);
  const board = ok(run("board"));
  assert.match(board, /\| 1000 \| Thousand \|/);
  assert.match(board, /\| 1001 \| Next \|/);
});

test("ambiguous task IDs refuse mutation", (t) => {
  const { root, run } = fixture(t);
  const file = ok(run("new", "First"));
  const original = readFileSync(join(root, file), "utf8");
  mkdirSync(join(root, "tasks/001-duplicate"));
  const result = run("claim", "001");
  assert.notEqual(result.status, 0);
  assert.match(result.output, /ambiguous/i);
  assert.equal(readFileSync(join(root, file), "utf8"), original);
});

for (const [name, args] of [
  ["newline in title", ["new", "Good\nstatus: done"]],
  ["control character in title", ["new", "Good\rBad"]],
  ["blank title", ["new", "   "]],
  ["invalid priority", ["new", "Good", "P4"]],
  ["injected priority", ["new", "Good", "P2\nowner: intruder"]],
  ["extra argument", ["new", "Good", "P2", "extra"]],
]) {
  test(`${name} is rejected before creating a task`, (t) => {
    const { root, run } = fixture(t);
    assert.notEqual(run(...args).status, 0);
    assert.deepEqual(readdirSync(root), ["tools"]);
  });
}

test("invalid IDs and owner injection cannot mutate task frontmatter", (t) => {
  const { root, run } = fixture(t);
  const file = ok(run("new", "First"));
  const original = readFileSync(join(root, file), "utf8");
  for (const args of [["claim", "001", "bob\nstatus: done"], ["claim", "001", "bob\\nstatus: done"], ["claim", "001", "--unknown"], ["claim", "../001"], ["handoff", "001\n"], ["status", "*", "active"]]) {
    assert.notEqual(run(...args).status, 0, JSON.stringify(args));
    assert.equal(readFileSync(join(root, file), "utf8"), original);
  }
});

test("ordinary lifecycle preserves punctuation in titles and board columns", (t) => {
  const { root, run } = fixture(t);
  const file = ok(run("new", "Bob's scripts: C:\\new | review #1", "P1"));
  ok(run("claim", "001"));
  assert.notEqual(run("done", "001", "--check").status, 0);
  fillHandoff(root, ok(run("handoff", "001")));
  ok(run("done", "001", "--check"));
  ok(run("done", "001"));
  const board = ok(run("board"));
  const row = board.split("\n").find((line) => line.startsWith("| 001 |"));
  assert.equal(row.split("|").length, 9, row);
  assert.match(row, /Bob's scripts: C:\\new &#124; review #1/);
  assert.match(row, /\*\*done\*\* \| tester \| P1 \|/);
  assert.match(readFileSync(join(root, file), "utf8"), /^status: done$/m);
  const before = readFileSync(join(root, "tasks/TASKS.md"), "utf8");
  ok(run("index"));
  assert.equal(readFileSync(join(root, "tasks/TASKS.md"), "utf8"), before);
});

test("nonowners cannot mutate task state or handoffs, including forced closeout", (t) => {
  const { root, run, runAs } = fixture(t);
  const file = ok(run("new", "Owned"));
  ok(run("claim", "001"));
  fillHandoff(root, ok(run("handoff", "001")));
  const original = readFileSync(join(root, file), "utf8");
  const handoffs = readdirSync(join(root, "tasks/001-owned/handoffs"));
  for (const args of [["status", "001", "blocked"], ["handoff", "001"], ["done", "001"], ["done", "001", "--force"], ["release", "001"]]) {
    const result = runAs("other", ...args);
    assert.notEqual(result.status, 0, JSON.stringify(args));
    assert.match(result.output, /owned by 'tester'/);
    assert.equal(readFileSync(join(root, file), "utf8"), original);
    assert.deepEqual(readdirSync(join(root, "tasks/001-owned/handoffs")), handoffs);
  }
  ok(runAs("other", "done", "001", "--check"));
  assert.equal(readFileSync(join(root, file), "utf8"), original);
});

test("unclaimed tasks require a claim before mutation", (t) => {
  const { run } = fixture(t);
  ok(run("new", "Unclaimed"));
  for (const args of [["status", "001", "active"], ["handoff", "001"], ["done", "001", "--force"], ["release", "001"]]) {
    const result = run(...args);
    assert.notEqual(result.status, 0, JSON.stringify(args));
    assert.match(result.output, /claim/i);
  }
});

test("closeout and release require filled sections in the latest Markdown handoff", (t) => {
  const { root, run } = fixture(t);
  ok(run("new", "Gate"));
  ok(run("claim", "001"));
  fillHandoff(root, ok(run("handoff", "001")));
  const latest = ok(run("handoff", "001"));
  const scaffold = readFileSync(join(root, latest), "utf8");
  for (const content of ["", "junk\n", scaffold, scaffold + "Unstructured evidence\n", "## Objective\nFinished.\n"]) {
    writeFileSync(join(root, latest), content);
    for (const args of [["done", "001", "--check"], ["done", "001"], ["release", "001"]]) {
      const result = run(...args);
      assert.notEqual(result.status, 0, JSON.stringify({ args, content }));
      assert.match(result.output, /handoff/i);
    }
  }
  fillHandoff(root, latest);
  ok(run("done", "001", "--check"));
});

test("release clears ownership, preserves handoffs and allows an ordinary new claim", (t) => {
  const { root, run, runAs } = fixture(t);
  const file = ok(run("new", "Release"));
  ok(run("claim", "001"));
  ok(run("status", "001", "blocked"));
  const handoff = ok(run("handoff", "001"));
  fillHandoff(root, handoff);
  const evidence = readFileSync(join(root, handoff), "utf8");
  ok(run("release", "001"));
  const released = readFileSync(join(root, file), "utf8");
  assert.match(released, /^owner: *$/m);
  assert.match(released, /^status: pending$/m);
  assert.equal(readFileSync(join(root, handoff), "utf8"), evidence);
  assert.match(readFileSync(join(root, "tasks/TASKS.md"), "utf8"), /\*\*pending\*\* \| - \|/);
  ok(runAs("other", "claim", "001"));
  assert.match(readFileSync(join(root, file), "utf8"), /^owner: other$/m);
});

test("owner can explicitly override closeout gates and takeover stays explicit", (t) => {
  const { run, runAs } = fixture(t);
  ok(run("new", "Override"));
  ok(run("claim", "001"));
  assert.notEqual(runAs("other", "claim", "001").status, 0);
  ok(runAs("other", "claim", "001", "--force"));
  assert.notEqual(run("done", "001", "--force").status, 0);
  ok(runAs("other", "done", "001", "--force"));
});
