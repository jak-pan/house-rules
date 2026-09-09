#!/usr/bin/env node
import { copyFileSync, chmodSync, existsSync, lstatSync, mkdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, isAbsolute, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

// An explicit file list prevents local records and future unreviewed files entering a release.
export function exportPublic(source, destination) {
  const root = realpathSync(source);
  const target = resolve(destination);
  if (existsSync(target)) throw new Error('Export destination already exists; choose a new directory.');
  const paths = readFileSync(join(root, 'PUBLIC-FILES.txt'), 'utf8').split(/\r?\n/)
    .map(line => line.trim()).filter(line => line && !line.startsWith('#'));
  if (!paths.length || new Set(paths).size !== paths.length) throw new Error('Public file list is empty or contains duplicates.');
  const files = paths.map(path => {
    if (isAbsolute(path) || path.includes('\\') || path.split('/').some(part => !part || part === '.' || part === '..')) {
      throw new Error(`Invalid public path: ${path}`);
    }
    const full = join(root, path);
    const stat = lstatSync(full);
    const resolved = relative(root, realpathSync(full));
    if (!stat.isFile() || stat.isSymbolicLink() || resolved === '..' || resolved.startsWith(`..${sep}`) || isAbsolute(resolved)) {
      throw new Error(`Public entry must be a regular file inside the source: ${path}`);
    }
    return { path, full, mode: stat.mode & 0o777, sha256: createHash('sha256').update(readFileSync(full)).digest('hex') };
  });
  mkdirSync(target); // All source entries are checked before writing; never overwrite an export.
  for (const file of files) {
    const output = join(target, file.path);
    mkdirSync(dirname(output), { recursive: true });
    copyFileSync(file.full, output);
    chmodSync(output, file.mode);
    if (createHash('sha256').update(readFileSync(output)).digest('hex') !== file.sha256) {
      throw new Error(`Source changed during export: ${file.path}. Export is incomplete.`);
    }
  }
  const manifest = { formatVersion: 1, files: files.map(({ path, sha256 }) => ({ path, sha256 })) };
  writeFileSync(join(target, 'MANIFEST.json'), JSON.stringify(manifest, null, 2) + '\n', { flag: 'wx' });
  return manifest;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    if (process.argv.length !== 3) throw new Error('Usage: node scripts/export-public.mjs <new-output-directory>');
    const source = resolve(dirname(fileURLToPath(import.meta.url)), '..');
    const result = exportPublic(source, process.argv[2]);
    console.log(`Exported ${result.files.length} reviewed files; inspect MANIFEST.json before publication.`);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
