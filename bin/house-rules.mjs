#!/usr/bin/env node
// Git-backed task files. Ownership is cooperative; this CLI is not a lock service.
import * as fs from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { userInfo } from 'node:os';
import { randomUUID } from 'node:crypto';

const source = dirname(dirname(fileURLToPath(import.meta.url)));
const project = projectRoot();
const tasks = process.env.TASKS_DIR || relative(process.cwd(), join(project, 'tasks')) || '.';
const now = () => new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
const fail = (message) => { throw new Error(message); };
const usage = `Usage: house-rules task <command>
  new "title" [P0|P1|P2|P3]      create the next task (pending)
  claim ID [owner] [--force]     claim and activate; --force explicitly takes over
  status ID <state>              pending|active|review|blocked
  done ID [--check] [--force]    check or close; --force skips gates, never ownership
  handoff ID                     create a new handoff scaffold; fill it before closing
  release ID                     require a filled handoff, clear owner, return to pending
  index                          regenerate tasks/TASKS.md
  board                          print the current board without writing
  house-rules root               print this installation's source directory
  house-rules --version          print the package version

ID is a task ID of 3–18 digits or its full NNN-slug directory name. Run anywhere
in the target project: tasks/ is found at the Git top level (the nearest folder
containing .git), else the current directory; TASKS_DIR overrides it. Owner
defaults to AGENT_NAME, USER, USERNAME, then the operating-system username.
Commit task state and the generated board together. Claims are cooperative
ownership records, not exclusive locks across Git checkouts.`;

// The nearest folder containing .git (a directory, or a file in a linked worktree);
// without one, the current directory. tasks/ and design: paths resolve from it.
function projectRoot() {
  let directory = process.cwd();
  while (!fs.existsSync(join(directory, '.git'))) {
    const parent = dirname(directory);
    if (parent === directory) return process.cwd();
    directory = parent;
  }
  return directory;
}

function id(value) {
  if (!/^[0-9]{3,18}$/.test(value || '') || BigInt(value) === 0n)
    fail('bad task ID: expected a positive decimal ID of 3–18 digits');
  return value;
}

function agent(value) {
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(value || ''))
    fail('bad owner/agent: use letters, digits, dot, underscore or hyphen; start with a letter or digit');
  return value;
}

function currentAgent() {
  return agent(process.env.AGENT_NAME || process.env.USER || process.env.USERNAME || userInfo().username);
}

function entries(directory) {
  try { return fs.readdirSync(directory, { withFileTypes: true }); }
  catch (error) { if (error.code === 'ENOENT') return []; throw error; }
}

function taskDirectories() {
  return entries(tasks).filter((entry) => entry.isDirectory() && /^\d+-/.test(entry.name)).map((entry) => entry.name);
}

function nextId() {
  let last = 0n;
  for (const name of taskDirectories()) {
    const value = BigInt(id(name.split('-')[0]));
    if (value > last) last = value;
  }
  return id(String(last + 1n).padStart(3, '0'));
}

function freeIdHint() {
  try { return nextId(); } catch { return 'the next free ID'; }
}

// A reference is an ID or the full NNN-slug directory name; the latter stays usable
// when branches merged two tasks with the same ID.
function taskDirectory(reference) {
  const match = /^([0-9]{3,18})(-.+)?$/.exec(reference || '');
  if (!match || BigInt(match[1]) === 0n)
    fail(`bad task reference '${reference ?? ''}': expected an ID of 3–18 digits or its full NNN-slug directory name`);
  const names = taskDirectories();
  const matches = match[2] ? names.filter((name) => name === reference) : names.filter((name) => name.startsWith(`${reference}-`));
  if (!matches.length) fail(`no task ${reference} in ${tasks}/`);
  if (matches.length !== 1)
    fail(`ambiguous task ID ${reference}: ${matches.length} matching directories (${matches.join(', ')}).\n`
      + `Use the full directory name in place of the ID (for example ${matches.at(-1)}), or rename one directory `
      + `to the next free ID (${freeIdHint()}) and update its id: field, then run: house-rules task index`);
  return join(tasks, matches[0]);
}

// Frontmatter scalars: 'single' or "double" quoted, or plain with an optional # comment.
function scalar(raw) {
  const value = raw.trim();
  const single = /^'((?:[^']|'')*)'(?:\s+#.*)?$/.exec(value);
  if (single) return single[1].replaceAll("''", "'");
  const double = /^"((?:[^"\\]|\\.)*)"(?:\s+#.*)?$/.exec(value);
  if (double) return double[1].replace(/\\(.)/g, '$1');
  return value.replace(/(?:^|\s+)#.*$/, '');
}

// Deliberately a small frontmatter format, not a general YAML parser. Keep the
// original line endings and Markdown body when updating known scalar fields.
function frontmatter(file) {
  const text = fs.readFileSync(file, 'utf8');
  const match = /^(---\r?\n)([\s\S]*?)(^---\r?$)/m.exec(text);
  if (!match || match.index !== 0) fail(`missing frontmatter in ${file}`);
  const get = (key) => scalar(match[2].split(/\r?\n/).find((line) => line.startsWith(`${key}:`))?.slice(key.length + 1) ?? '');
  return { text, match, get };
}

function update(file, fields) {
  const { text, match } = frontmatter(file);
  let header = match[2];
  for (const [key, value] of Object.entries(fields)) {
    const pattern = new RegExp(`^${key}:[^\\r\\n]*`, 'm');
    if (!pattern.test(header)) fail(`missing ${key}: field in ${file}`);
    header = header.replace(pattern, () => `${key}: ${value}`);
  }
  const temporary = join(dirname(file), `.task-${randomUUID()}.tmp`);
  try {
    fs.writeFileSync(temporary, match[1] + header + text.slice(match[1].length + match[2].length),
      { flag: 'wx', mode: fs.statSync(file).mode });
    fs.renameSync(temporary, file);
  } finally { if (fs.existsSync(temporary)) fs.unlinkSync(temporary); }
}

function requireOwner(file, reference) {
  const owner = frontmatter(file).get('owner');
  const caller = currentAgent();
  if (!owner) fail(`REFUSED: task is unclaimed — run: house-rules task claim ${reference}`);
  if (owner !== caller) fail(`REFUSED: ${reference} owned by '${owner}', not '${caller}'. Take over explicitly: house-rules task claim ${reference} --force`);
  return owner;
}

function latestHandoff(directory) {
  return entries(join(directory, 'handoffs')).filter((entry) => entry.isFile() && entry.name.endsWith('.md'))
    .map((entry) => entry.name).sort().at(-1);
}

function filledHandoff(file) {
  const text = fs.readFileSync(file, 'utf8').replace(/<!--[\s\S]*?(?:-->|$)/g, '');
  const filled = new Set();
  let section;
  for (const line of text.split(/\r?\n/)) {
    if (line.startsWith('## ')) section = line.slice(3).trim();
    else if (!line.startsWith('#') && /[\p{L}\p{N}]/u.test(line)) filled.add(section);
  }
  return ['Objective', 'Completed', 'Pending', 'Blockers', 'Decisions'].every((name) => filled.has(name));
}

// The closeout and release gates: the latest handoff is filled in.
function handoffProblems(directory, reference) {
  const write = `house-rules task handoff ${reference}`;
  const latest = latestHandoff(directory);
  if (!latest) return [`no Markdown handoff in ${join(directory, 'handoffs')}; the owner writes one: ${write}`];
  const file = join(directory, 'handoffs', latest);
  const problems = [];
  if (!filledHandoff(file)) problems.push(`latest handoff ${file} needs content in Objective, Completed, Pending, Blockers and Decisions`);
  return problems;
}

function designProblems(design) {
  const path = resolve(project, design);
  if (!fs.existsSync(path)) return [`design: points at missing file '${design}'`];
  let status;
  try { status = frontmatter(path).get('status'); }
  catch (error) { return [`design doc '${design}' cannot be checked: ${error.message.replaceAll(path, design)}`]; }
  return ['implemented', 'superseded'].includes(status) ? []
    : [`design doc ${design} must be implemented or superseded after migration`];
}

function board() {
  const states = ['active', 'review', 'blocked', 'pending', 'done'];
  const names = taskDirectories();
  const byId = Map.groupBy(names, (name) => name.split('-')[0]);
  const duplicates = [...byId].filter(([, group]) => group.length > 1);
  if (duplicates.length)
    fail(duplicates.map(([value, group]) => `duplicate task ID ${value}: ${group.map((name) => join(tasks, name)).join(' and ')}`).join('\n')
      + `\nRename each extra directory to a free ID (next: ${freeIdHint()}) and update its id: field, then run: house-rules task index.`
      + '\nUntil then, refer to these tasks by their full directory names.');
  const rows = [];
  for (const name of names) {
    const directory = join(tasks, name);
    if (!fs.existsSync(join(directory, 'task.md'))) continue;
    const { get } = frontmatter(join(directory, 'task.md'));
    const value = id(get('id'));
    const state = get('status');
    if (!states.includes(state)) fail(`bad status in ${directory}/task.md: ${state}`);
    rows.push({ value, state, priority: get('priority'), fields: [value, get('title'), `**${state}**`,
      get('owner') || '-', get('priority'), get('updated').split('T')[0], latestHandoff(directory) || '-'] });
  }
  rows.sort((a, b) => states.indexOf(a.state) - states.indexOf(b.state)
    || a.priority.localeCompare(b.priority)
    || (BigInt(a.value) < BigInt(b.value) ? -1 : BigInt(a.value) > BigInt(b.value) ? 1 : a.value.localeCompare(b.value)));
  return '| id | title | status | owner | prio | updated | latest handoff |\n|---|---|---|---|---|---|---|\n'
    + rows.map((row) => `| ${row.fields.map((field) => field.replaceAll('|', '&#124;')).join(' | ')} |\n`).join('');
}

function index() {
  const rendered = board();
  fs.mkdirSync(tasks, { recursive: true });
  const file = join(tasks, 'TASKS.md');
  fs.writeFileSync(file, '# Task Board\n\n> GENERATED by `house-rules task index` — never hand-edit. Source of truth: task frontmatter\n'
    + '> (single writer: the owner). Continuation: latest Markdown file in the task’s `handoffs/`.\n\n' + rendered);
  return file;
}

// Check that the board can be regenerated before changing task.md, so a closed or
// released task never sits beside a stale board.
function transition(reference, result, change) {
  try { board(); }
  catch (error) { fail(`REFUSED: ${reference} unchanged; the board cannot be regenerated:\n  ${error.message.replaceAll('\n', '\n  ')}`); }
  change();
  try { index(); }
  catch (error) { fail(`${result}, but ${join(tasks, 'TASKS.md')} was not regenerated: ${error.message}\nFix the cause, then run: house-rules task index`); }
}

function run(args) {
  if (!args.length || args[0] === '--help' || args[0] === '-h') return console.log(usage);
  if (args.length === 1 && args[0] === 'root') return console.log(resolve(source));
  if (args.length === 1 && args[0] === '--version')
    return console.log(JSON.parse(fs.readFileSync(join(source, 'package.json'), 'utf8')).version);
  if (args.shift() !== 'task') fail(usage);
  const command = args.shift();
  if (!command || command === '--help' || command === '-h') return console.log(usage);
  if (['board', 'index'].includes(command)) {
    if (args.length) fail(usage);
    return command === 'board' ? process.stdout.write(board()) : console.log(`wrote ${index()}`);
  }
  if (command === 'new') {
    if (args.length < 1 || args.length > 2) fail(usage);
    const [title, priority = 'P2'] = args;
    if (!title.trim() || /[\p{Cc}\p{Zl}\p{Zp}]/u.test(title)) fail('title must be nonblank and contain no control characters');
    if (!/^P[0-3]$/.test(priority)) fail('priority must be P0, P1, P2 or P3');
    const value = nextId();
    const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40) || 'task';
    const directory = join(tasks, `${value}-${slug}`);
    fs.mkdirSync(tasks, { recursive: true });
    fs.mkdirSync(directory); // Refuse an existing directory instead of replacing its task.
    fs.mkdirSync(join(directory, 'handoffs'));
    const file = join(directory, 'task.md');
    const time = now();
    fs.writeFileSync(file, `---\nid: ${value}\ntitle: '${title.replaceAll("'", "''")}'\nstatus: pending\nowner:\npriority: ${priority}\ndepends_on:\nlane:\ndesign:\npr:\ncreated: ${time}\nupdated: ${time}\n---\n\n## Scope\n\n## Acceptance criteria\n\n## Decisions\n<!-- settled choices + rejected alternatives, with why -->\n`, { flag: 'wx' });
    return console.log(file);
  }
  if (!['claim', 'status', 'done', 'handoff', 'release'].includes(command)) fail(usage);
  const reference = args.shift();
  const directory = taskDirectory(reference);
  const file = join(directory, 'task.md');
  if (command === 'claim') {
    let owner, force = false;
    for (const arg of args) {
      if (arg === '--force') force = true;
      else if (arg.startsWith('--') || owner) fail(usage);
      else owner = agent(arg);
    }
    owner ||= currentAgent();
    const previous = frontmatter(file).get('owner');
    if (previous && previous !== owner && !force)
      fail(`REFUSED: ${reference} owned by '${previous}'. Take over explicitly: house-rules task claim ${reference} ${owner} --force`);
    update(file, { owner, status: 'active', updated: now() });
    return console.log(`claimed ${reference} -> ${owner}`);
  }
  if (command === 'status') {
    if (args.length !== 1) fail(usage);
    const state = args[0];
    if (state === 'done') fail(`REFUSED: 'status done' bypasses the closeout gate — use: house-rules task done ${reference}`);
    if (!['pending', 'active', 'review', 'blocked'].includes(state)) fail(`bad status: ${state}`);
    requireOwner(file, reference);
    update(file, { status: state, updated: now() });
    return console.log(`${reference} -> ${state}`);
  }
  if (command === 'done') {
    if (args.some((arg) => !['--check', '--force'].includes(arg))) fail(usage);
    const check = args.includes('--check'), force = args.includes('--force');
    if (!check) requireOwner(file, reference);
    const problems = handoffProblems(directory, reference);
    const design = frontmatter(file).get('design');
    if (design) problems.push(...designProblems(design));
    const override = `(override: house-rules task done ${reference} --force — justify in the final handoff)`;
    if (check) try { board(); } catch (error) {
      fail(`NOT CLOSEABLE: task ${reference}\n  - ${[...problems, `the board cannot be regenerated (--force does not bypass this):\n    ${error.message.replaceAll('\n', '\n    ')}`].join('\n  - ')}${problems.length ? `\n${override}` : ''}`);
    }
    if (problems.length && (check || !force)) fail(`${check ? 'NOT CLOSEABLE' : 'REFUSED'}: task ${reference}\n  - ${problems.join('\n  - ')}\n${override}`);
    if (check) return console.log(`closeable: task ${reference}`);
    transition(reference, `${reference} -> done`, () => update(file, { status: 'done', updated: now() }));
    return console.log(`${reference} -> done\nReview closeout: delivery recorded, design migrated, durable decisions promoted, and relevant verification complete.`);
  }
  if (args.length) fail(usage);
  requireOwner(file, reference);
  if (command === 'release') {
    const problems = handoffProblems(directory, reference);
    if (problems.length) fail(`REFUSED: release needs a filled latest Markdown handoff\n  - ${problems.join('\n  - ')}`);
    transition(reference, `released ${reference} -> pending (unclaimed)`, () => update(file, { owner: '', status: 'pending', updated: now() }));
    return console.log(`released ${reference} -> pending (unclaimed)`);
  }
  const owner = currentAgent();
  const time = now();
  const stamp = time.replaceAll('-', '').replace('T', '-').replaceAll(':', '').replace('Z', '');
  fs.mkdirSync(join(directory, 'handoffs'), { recursive: true });
  for (let sequence = 1; ; sequence++) {
    const handoff = join(directory, 'handoffs', `${stamp}-${owner}-${String(sequence).padStart(6, '0')}.md`);
    try {
      fs.writeFileSync(handoff, `# Handoff — task ${reference} — ${owner} — ${time}\n<!-- IMMUTABLE once committed. Next session writes a NEW file. -->\n\n## Objective\n<!-- standing goal, verbatim, incl. numeric targets -->\n\n## Completed\n<!-- with evidence pointers: run dirs, commits, file:line -->\n\n## Pending\n<!-- ordered, cheapest/highest-signal first -->\n\n## Blockers\n<!-- exact state: what runs, what waits on whom -->\n\n## Decisions\n<!-- settled this session + rejected alternatives (why) -->\n`, { flag: 'wx' });
      return console.log(handoff);
    } catch (error) { if (error.code !== 'EEXIST') throw error; }
  }
}

try { run(process.argv.slice(2)); }
catch (error) { console.error(error.message); process.exitCode = 1; }
