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
  return {
    root,
    run(...args) {
      const result = spawnSync("zsh", [cli, ...args], {
        cwd: root, encoding: "utf8",
        env: { ...process.env, TASKS_DIR: "tasks", AGENT_NAME: "tester", PATH: `${root}/tools:${process.env.PATH}` },
      });
      assert.ifError(result.error);
      return { status: result.status, output: result.stdout + result.stderr };
    },
  };
}

function ok(result) { assert.equal(result.status, 0, result.output); return result.output.trim(); }

test("same-second handoffs preserve earlier evidence and sort in creation order", (t) => {
  const { root, run } = fixture(t);
  ok(run("new", "First"));
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
  ok(run("claim", "001", "test-agent"));
  assert.notEqual(run("done", "001", "--check").status, 0);
  ok(run("handoff", "001"));
  ok(run("done", "001", "--check"));
  ok(run("done", "001"));
  const board = ok(run("board"));
  const row = board.split("\n").find((line) => line.startsWith("| 001 |"));
  assert.equal(row.split("|").length, 9, row);
  assert.match(row, /Bob's scripts: C:\\new &#124; review #1/);
  assert.match(row, /\*\*done\*\* \| test-agent \| P1 \|/);
  assert.match(readFileSync(join(root, file), "utf8"), /^status: done$/m);
  const before = readFileSync(join(root, "tasks/TASKS.md"), "utf8");
  ok(run("index"));
  assert.equal(readFileSync(join(root, "tasks/TASKS.md"), "utf8"), before);
});
