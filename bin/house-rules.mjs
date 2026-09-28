#!/usr/bin/env node
// Git-backed task files. Ownership is cooperative; this CLI is not a lock service.
import * as fs from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { userInfo } from 'node:os';
import { randomUUID } from 'node:crypto';

const source = dirname(dirname(fileURLToPath(import.meta.url)));
const tasks = process.env.TASKS_DIR || 'tasks';
const now = () => new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
const fail = (message) => { throw new Error(message); };
const usage = `Usage: house-rules task <command>
  new "title" [P0|P1|P2|P3]    create the next task (pending)
  claim ID [owner] [--force]   claim and activate; --force explicitly takes over
  status ID <state>           pending|active|review|blocked
  done ID [--check] [--force]  check or close; --force skips gates, never ownership
  handoff ID                  create a new handoff scaffold; fill it before closing
  release ID                  require a filled handoff, clear owner, return to pending
  index                       regenerate tasks/TASKS.md
  board                       print the current board without writing
  house-rules root            print this installation's source directory
  house-rules --version       print the package version

Run from the target project. TASKS_DIR defaults to tasks. Owner defaults to
AGENT_NAME, USER, USERNAME, then the operating-system username. Task IDs contain
3–18 digits. Commit task state and the generated board together. Claims are
cooperative ownership records, not exclusive locks across Git checkouts.`;

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

function taskDirectory(value) {
  id(value);
  const matches = entries(tasks).filter((entry) => entry.isDirectory() && entry.name.startsWith(`${value}-`));
  if (!matches.length) fail(`no task ${value} in ${tasks}/`);
  if (matches.length !== 1) fail(`ambiguous task ID ${value}: ${matches.length} matching directories`);
  return join(tasks, matches[0].name);
}

// Deliberately a small frontmatter format, not a general YAML parser. Keep the
// original line endings and Markdown body when updating known scalar fields.
function frontmatter(file) {
  const text = fs.readFileSync(file, 'utf8');
  const match = /^(---\r?\n)([\s\S]*?)(^---\r?$)/m.exec(text);
  if (!match || match.index !== 0) fail(`missing frontmatter in ${file}`);
  const get = (key) => {
    let value = match[2].split(/\r?\n/).find((line) => line.startsWith(`${key}:`))?.slice(key.length + 1).trim() || '';
    if (value.startsWith("'") && value.endsWith("'")) value = value.slice(1, -1).replaceAll("''", "'");
    return value;
  };
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

function requireOwner(file, value) {
  const owner = frontmatter(file).get('owner');
  const caller = currentAgent();
  if (!owner) fail(`REFUSED: task is unclaimed — run: house-rules task claim ${value}`);
  if (owner !== caller) fail(`REFUSED: ${value} owned by '${owner}', not '${caller}'. Take over explicitly: house-rules task claim ${value} --force`);
}

function latestHandoff(directory) {
  return entries(join(directory, 'handoffs')).filter((entry) => entry.isFile() && entry.name.endsWith('.md'))
    .map((entry) => entry.name).sort().at(-1);
}

function filledHandoff(directory) {
  const latest = latestHandoff(directory);
  if (!latest) return false;
  const text = fs.readFileSync(join(directory, 'handoffs', latest), 'utf8').replace(/<!--[\s\S]*?(?:-->|$)/g, '');
  const filled = new Set();
  let section;
  for (const line of text.split(/\r?\n/)) {
    if (line.startsWith('## ')) section = line.slice(3).trim();
    else if (!line.startsWith('#') && /[\p{L}\p{N}]/u.test(line)) filled.add(section);
  }
  return ['Objective', 'Completed', 'Pending', 'Blockers', 'Decisions'].every((name) => filled.has(name));
}

function board() {
  const states = ['active', 'review', 'blocked', 'pending', 'done'];
  const rows = [];
  for (const entry of entries(tasks)) {
    if (!entry.isDirectory() || !/^\d+-/.test(entry.name)) continue;
    const directory = join(tasks, entry.name);
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
    let last = 0n;
    for (const entry of entries(tasks)) {
      if (!entry.isDirectory() || !/^\d+-/.test(entry.name)) continue;
      const value = BigInt(id(entry.name.split('-')[0]));
      if (value > last) last = value;
    }
    const value = id(String(last + 1n).padStart(3, '0'));
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
  const value = id(args.shift());
  const directory = taskDirectory(value);
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
      fail(`REFUSED: ${value} owned by '${previous}'. Take over explicitly: house-rules task claim ${value} ${owner} --force`);
    update(file, { owner, status: 'active', updated: now() });
    return console.log(`claimed ${value} -> ${owner}`);
  }
  if (command === 'status') {
    if (args.length !== 1) fail(usage);
    const state = args[0];
    if (state === 'done') fail(`REFUSED: 'status done' bypasses the closeout gate — use: house-rules task done ${value}`);
    if (!['pending', 'active', 'review', 'blocked'].includes(state)) fail(`bad status: ${state}`);
    requireOwner(file, value);
    update(file, { status: state, updated: now() });
    return console.log(`${value} -> ${state}`);
  }
  if (command === 'done') {
    if (args.some((arg) => !['--check', '--force'].includes(arg))) fail(usage);
    const check = args.includes('--check'), force = args.includes('--force');
    if (!check) requireOwner(file, value);
    const problems = [];
    if (!filledHandoff(directory)) problems.push('latest Markdown handoff needs content in Objective, Completed, Pending, Blockers and Decisions');
    const design = frontmatter(file).get('design');
    if (design) {
      if (!fs.existsSync(design)) problems.push(`design: points at missing file '${design}'`);
      else if (!['implemented', 'superseded'].includes(frontmatter(design).get('status')))
        problems.push(`design doc ${design} must be implemented or superseded after migration`);
    }
    if (problems.length && (check || !force)) fail(`${check ? 'NOT CLOSEABLE' : 'REFUSED'}: task ${value}\n  - ${problems.join('\n  - ')}\n(override: house-rules task done ${value} --force — justify in the final handoff)`);
    if (check) return console.log(`closeable: task ${value}`);
    update(file, { status: 'done', updated: now() });
    index();
    return console.log(`${value} -> done\nReview closeout: delivery recorded, design migrated, durable decisions promoted, and relevant verification complete.`);
  }
  if (args.length) fail(usage);
  requireOwner(file, value);
  if (command === 'release') {
    if (!filledHandoff(directory)) fail('REFUSED: release needs a filled latest Markdown handoff (Objective, Completed, Pending, Blockers, Decisions)');
    update(file, { owner: '', status: 'pending', updated: now() });
    index();
    return console.log(`released ${value} -> pending (unclaimed)`);
  }
  const owner = currentAgent();
  const time = now();
  const stamp = time.replaceAll('-', '').replace('T', '-').replaceAll(':', '').replace('Z', '');
  fs.mkdirSync(join(directory, 'handoffs'), { recursive: true });
  for (let sequence = 1; ; sequence++) {
    const handoff = join(directory, 'handoffs', `${stamp}-${owner}-${String(sequence).padStart(6, '0')}.md`);
    try {
      fs.writeFileSync(handoff, `# Handoff — task ${value} — ${owner} — ${time}\n<!-- IMMUTABLE once committed. Next session writes a NEW file. -->\n\n## Objective\n<!-- standing goal, verbatim, incl. numeric targets -->\n\n## Completed\n<!-- with evidence pointers: run dirs, commits, file:line -->\n\n## Pending\n<!-- ordered, cheapest/highest-signal first -->\n\n## Blockers\n<!-- exact state: what runs, what waits on whom -->\n\n## Decisions\n<!-- settled this session + rejected alternatives (why) -->\n`, { flag: 'wx' });
      return console.log(handoff);
    } catch (error) { if (error.code !== 'EEXIST') throw error; }
  }
}

try { run(process.argv.slice(2)); }
catch (error) { console.error(error.message); process.exitCode = 1; }
