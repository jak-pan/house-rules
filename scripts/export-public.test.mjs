import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { exportPublic } from './export-public.mjs';

function fixture(t) {
  const scratch = resolve('.tmp'); mkdirSync(scratch, { recursive: true });
  const dir = mkdtempSync(join(scratch, 'public-export-test-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const source = join(dir, 'source'); mkdirSync(source);
  writeFileSync(join(source, 'README.md'), 'Public instructions\n');
  writeFileSync(join(source, 'PUBLIC-FILES.txt'), 'README.md\n');
  return { dir, source, target: join(dir, 'export') };
}
test('exports declared files and hashes, excluding private and unexpected files', t => {
  const { source, target } = fixture(t);
  for (const name of ['tasks', '.git', 'custom']) { mkdirSync(join(source, name)); writeFileSync(join(source, name, 'private.txt'), 'private'); }
  writeFileSync(join(source, 'unexpected.txt'), 'not reviewed');
  const result = exportPublic(source, target);
  assert.deepEqual(result.files.map(f => f.path), ['README.md']);
  for (const name of ['tasks', '.git', 'custom', 'unexpected.txt']) assert.equal(existsSync(join(target, name)), false);
  assert.deepEqual(JSON.parse(readFileSync(join(target, 'MANIFEST.json'), 'utf8')), result);
});
test('never overwrites an existing export', t => {
  const { source, target } = fixture(t); mkdirSync(target); writeFileSync(join(target, 'kept'), 'original');
  assert.throws(() => exportPublic(source, target), /already exists/);
  assert.equal(readFileSync(join(target, 'kept'), 'utf8'), 'original');
});
test('rejects traversal and symlinks before creating an export', t => {
  const { source, target, dir } = fixture(t); writeFileSync(join(dir, 'private'), 'private');
  writeFileSync(join(source, 'PUBLIC-FILES.txt'), '../private\n');
  assert.throws(() => exportPublic(source, target), /Invalid public path/);
  symlinkSync(join(dir, 'private'), join(source, 'linked'));
  writeFileSync(join(source, 'PUBLIC-FILES.txt'), 'linked\n');
  assert.throws(() => exportPublic(source, target), /regular file/);
  assert.equal(existsSync(target), false);
});
