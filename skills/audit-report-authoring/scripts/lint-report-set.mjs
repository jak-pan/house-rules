#!/usr/bin/env node

import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

const configPath = resolve(process.argv[2] ?? "audit-report-set.json");
const root = dirname(configPath);
const errors = [];
const evidenceOwners = new Map();
const stableId = /^[A-Za-z0-9][A-Za-z0-9._:-]{1,127}$/;

function fail(file, message, line = 0) {
  errors.push(`${file}${line ? `:${line}` : ""}: ${message}`);
}

function lineNumber(text, index) {
  return text.slice(0, index).split("\n").length;
}

function headingSlugs(text) {
  const slugs = new Set();
  const counts = new Map();
  for (const match of text.matchAll(/^#{1,6}\s+(.+)$/gm)) {
    const base = match[1]
      .replace(/\[\[.*?\]\]/g, "")
      .replace(/`/g, "")
      .toLowerCase()
      .replace(/[^\p{L}\p{N}\s-]/gu, "")
      .trim()
      .replace(/\s+/g, "-");
    const count = counts.get(base) ?? 0;
    counts.set(base, count + 1);
    slugs.add(count ? `${base}-${count}` : base);
  }
  return slugs;
}

// This is the report contract's narrow anchor syntax, not a general HTML parser.
function declaredEvidenceAnchors(text) {
  const lines = text.replace(/<!--[\s\S]*?(?:-->|$)/g, comment => comment.replace(/[^\n]/g, " ")).split("\n");
  const anchors = [];
  let fence = null;
  for (const [index, line] of lines.entries()) {
    const delimiter = line.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
    if (fence) {
      if (delimiter && delimiter[1][0] === fence[0] && delimiter[1].length >= fence.length && !delimiter[2].trim()) fence = null;
      continue;
    }
    if (delimiter) {
      fence = delimiter[1];
      continue;
    }
    const declaration = line.match(/^<a id="(evidence-[a-z][a-z0-9]*-e\d{2})"><\/a>\r?$/);
    if (!declaration) continue;
    let headingLine = index + 1;
    while (headingLine < lines.length && !lines[headingLine].trim()) headingLine++;
    anchors.push({ id: declaration[1], line: index + 1, headingLine: headingLine + 1 });
  }
  return anchors;
}

function readJson(path, label) {
  if (!existsSync(path)) throw new Error(`${label} does not exist: ${path}`);
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    throw new Error(`${label} is not valid JSON: ${error.message}`);
  }
}

const config = readJson(configPath, "Report-set config");
if (!/^\d+\.\d+$/.test(config.contractVersion ?? "")) {
  throw new Error("contractVersion must use major.minor form");
}
if (!Array.isArray(config.reports) || !config.reports.length) {
  throw new Error("reports must be a non-empty array");
}
if (typeof config.questionBindingFile !== "string" || !/^[^/]+\.json$/.test(config.questionBindingFile)) {
  throw new Error("questionBindingFile must be a JSON filename beside the config");
}

const reportFiles = new Set();
const claimPrefixes = new Set();
for (const report of config.reports) {
  if (typeof report.file !== "string" || !/^[^/]+\.md$/.test(report.file)) {
    throw new Error(`report file must be a Markdown filename beside the config: ${report.file}`);
  }
  if (!new Set(["master", "specialist"]).has(report.kind)) {
    throw new Error(`report kind must be master or specialist: ${report.file}`);
  }
  if (!/^[A-Z][A-Z0-9]{0,7}$/.test(report.claimPrefix ?? "")) {
    throw new Error(`invalid claimPrefix for ${report.file}`);
  }
  if (reportFiles.has(report.file)) throw new Error(`duplicate report file ${report.file}`);
  if (claimPrefixes.has(report.claimPrefix)) throw new Error(`duplicate claimPrefix ${report.claimPrefix}`);
  reportFiles.add(report.file);
  claimPrefixes.add(report.claimPrefix);
}

const binding = readJson(join(root, config.questionBindingFile), "Question binding");
if (binding.schemaVersion !== 1 || typeof binding.scopeId !== "string" || !binding.scopeId.trim()) {
  throw new Error("question binding requires schemaVersion 1 and a non-empty scopeId");
}
if (!Array.isArray(binding.questionIds) || !binding.questionIds.length) {
  throw new Error("question binding requires a non-empty questionIds array");
}
const questionIds = new Set(binding.questionIds);
if (questionIds.size !== binding.questionIds.length) throw new Error("question binding contains duplicate IDs");
for (const id of questionIds) if (typeof id !== "string" || !stableId.test(id)) throw new Error(`invalid question ID: ${id}`);

for (const report of config.reports) {
  const path = join(root, report.file);
  if (!existsSync(path)) {
    fail(report.file, "configured report does not exist");
    continue;
  }
  const text = readFileSync(path, "utf8");
  const lines = text.split("\n");
  const appendixStart = text.indexOf("[[EVIDENCE-APPENDIX:OPEN]]");
  const body = appendixStart < 0 ? text : text.slice(0, appendixStart);
  const appendix = appendixStart < 0 ? "" : text.slice(appendixStart);

  if (!/^#\s+\S/m.test(text)) fail(report.file, "missing level-one title");
  for (const [label, pattern] of [
    ["Status", /^Status:\s+\S/m],
    ["Classification", /^Classification:\s+\S/m],
    ["Date", /^Date:\s+\d{4}-\d{2}-\d{2}\s*$/m],
    ["Version", /^Version:\s+\d+\.\d+\s*$/m],
    ["Report contract", new RegExp(`^Report contract:\\s+${config.contractVersion.replace(".", "\\.")}\\s*$`, "m")],
    ["Report owner", /^Report owner:\s+\[\[OWNER:[^\]]+\]\]\s*$/m],
    ["evidence or technical cut-off", /^(?:Evidence|Technical) cut-off:\s+\d{4}-\d{2}-\d{2}\s*$/m],
  ]) {
    if (!pattern.test(text)) fail(report.file, `missing or invalid ${label} metadata`);
  }

  const ownerPattern = /\[\[OWNER:([^;\]]+);\s*role=([^\]]+)\]\]/g;
  const ownerOpenings = [...text.matchAll(/\[\[OWNER:/g)].length;
  const validOwners = [...text.matchAll(ownerPattern)];
  if (ownerOpenings !== validOwners.length) fail(report.file, "contains an unclosed or malformed OWNER tag");
  for (const match of text.matchAll(/\[\[OWNER:[^\]]*\]\]/g)) {
    ownerPattern.lastIndex = 0;
    if (!ownerPattern.test(match[0])) fail(report.file, "malformed OWNER tag", lineNumber(text, match.index));
  }
  for (const [index, line] of lines.entries()) {
    if (/^\|.*\b(?:Accountable owner|Decision owner)\b.*\|\s*$/i.test(line)) {
      fail(report.file, "workflow ownership column belongs in the canonical question/decision system", index + 1);
    }
  }

  const questionPattern = /\[\[QUESTION:([^\]]+)\]\]/g;
  const questionTags = [...text.matchAll(questionPattern)];
  if ([...text.matchAll(/\[\[QUESTION:/g)].length !== questionTags.length) {
    fail(report.file, "contains an unclosed QUESTION tag");
  }
  for (const match of questionTags) {
    const id = match[1];
    if (!stableId.test(id)) fail(report.file, `malformed question ID ${id}`, lineNumber(text, match.index));
    else if (!questionIds.has(id)) fail(report.file, `question ID is not bound to scope ${binding.scopeId}: ${id}`, lineNumber(text, match.index));
  }
  if (report.kind === "specialist" && !questionTags.length) fail(report.file, "specialist report contains no canonical question references");

  if (appendixStart < 0) fail(report.file, "missing [[EVIDENCE-APPENDIX:OPEN]] marker");
  const evidencePattern = /\[\[EVIDENCE:([A-Z][A-Z0-9]*-E\d{2})\]\]/g;
  const evidenceTags = [...text.matchAll(evidencePattern)];
  if ([...text.matchAll(/\[\[EVIDENCE:/g)].length !== evidenceTags.length) {
    fail(report.file, "contains an unclosed or malformed EVIDENCE tag");
  }
  if (!evidenceTags.length) fail(report.file, "contains no embedded evidence records");

  const anchors = declaredEvidenceAnchors(text);
  const anchorIds = new Set();
  for (const anchor of anchors) {
    if (anchorIds.has(anchor.id)) fail(report.file, `duplicate evidence anchor ${anchor.id}`, anchor.line);
    anchorIds.add(anchor.id);
    const id = anchor.id.slice("evidence-".length).toUpperCase();
    const attached = evidenceTags.some((match) => match[1] === id
      && match.index >= appendixStart && appendixStart >= 0
      && lineNumber(text, match.index) === anchor.headingLine
      && lines[anchor.headingLine - 1].startsWith(`### [[EVIDENCE:${id}]] `));
    if (!attached) fail(report.file, `evidence anchor ${anchor.id} must immediately precede its matching appendix record (blank lines allowed)`, anchor.line);
  }

  const numberByEvidence = new Map();
  for (const match of evidenceTags) {
    const id = match[1];
    const prior = evidenceOwners.get(id);
    if (prior) fail(report.file, `evidence ID ${id} duplicates ${prior}`, lineNumber(text, match.index));
    else evidenceOwners.set(id, report.file);
    const expected = numberByEvidence.size + 1;
    numberByEvidence.set(id, expected);
    const heading = lines[lineNumber(text, match.index) - 1] ?? "";
    const anchorId = `evidence-${id.toLowerCase()}`;
    if (!anchors.some((anchor) => anchor.id === anchorId && anchor.headingLine === lineNumber(text, match.index))) {
      fail(report.file, `evidence ${id} requires explicit anchor <a id="${anchorId}"></a> immediately before its heading`, lineNumber(text, match.index));
    }
    if (!heading.startsWith(`### [[EVIDENCE:${id}]] [${expected}] `)) {
      fail(report.file, `evidence ${id} must be numbered [${expected}] in appendix order`, lineNumber(text, match.index));
    }
    const recordEnd = evidenceTags[expected]?.index ?? text.length;
    const record = text.slice(match.index, recordEnd);
    for (const field of ["Supports", "Type and cut-off", "Method or origin", "Embedded record", "Limits"]) {
      const pattern = new RegExp(`^\\*\\*${field.replace(" ", "\\s+")}:\\*\\*\\s+\\S`, "m");
      if (!pattern.test(record)) fail(report.file, `evidence ${id} is missing ${field}`, lineNumber(text, match.index));
    }
  }

  const citedEvidence = new Set();
  for (const match of body.matchAll(/\[(\d+)\]\(#evidence-([a-z][a-z0-9]*-e\d{2})\)/g)) {
    const number = Number(match[1]);
    const id = match[2].toUpperCase();
    const expected = numberByEvidence.get(id);
    if (!expected) fail(report.file, `citation [${number}] targets missing evidence ${id}`, lineNumber(text, match.index));
    else if (number !== expected) fail(report.file, `citation [${number}] targets ${id}, numbered [${expected}]`, lineNumber(text, match.index));
    citedEvidence.add(id);
  }
  for (const [id, number] of numberByEvidence) {
    if (!citedEvidence.has(id)) fail(report.file, `evidence [${number}] ${id} is not cited from the body`);
  }

  const claimPattern = new RegExp(`\\b${report.claimPrefix}-\\d{2}\\b`, "g");
  const bodyClaims = new Set(body.match(claimPattern) ?? []);
  const supportText = [...appendix.matchAll(/^\*\*Supports:\*\*\s+(.+)$/gm)].map((match) => match[1]).join("\n");
  const supportedClaims = new Set(supportText.match(claimPattern) ?? []);
  for (const claim of bodyClaims) if (!supportedClaims.has(claim)) fail(report.file, `finding ${claim} is not named in an evidence Supports field`);

  for (const match of text.matchAll(/\[[^\]]+\]\(([^)]+)\)/g)) {
    const target = match[1].trim();
    if (/^https?:\/\//.test(target)) {
      if (appendixStart < 0 || match.index < appendixStart) {
        fail(report.file, `public source URL appears outside embedded evidence: ${target}`, lineNumber(text, match.index));
      }
      continue;
    }
    if (/^[a-z]+:\/\//i.test(target)) {
      fail(report.file, `unsupported external link scheme: ${target}`, lineNumber(text, match.index));
      continue;
    }
    const [file, fragment = ""] = target.split("#", 2);
    const linkedFile = file || report.file;
    if (!reportFiles.has(linkedFile)) {
      fail(report.file, `link leaves the configured report set: ${target}`, lineNumber(text, match.index));
      continue;
    }
    const linkedPath = join(root, linkedFile);
    if (!existsSync(linkedPath)) {
      fail(report.file, `linked report does not exist: ${linkedFile}`, lineNumber(text, match.index));
      continue;
    }
    if (fragment) {
      const linkedText = readFileSync(linkedPath, "utf8");
      const evidenceAnchors = new Set(declaredEvidenceAnchors(linkedText).map((entry) => entry.id));
      const exists = fragment.startsWith("evidence-")
        ? evidenceAnchors.has(fragment)
        : headingSlugs(linkedText).has(fragment);
      if (!exists) {
        fail(report.file, `missing fragment #${fragment} in ${linkedFile}`, lineNumber(text, match.index));
      }
    }
  }

  for (const match of body.matchAll(/(?<!\]\()https?:\/\/\S+/g)) {
    fail(report.file, `public source URL appears outside embedded evidence: ${match[0]}`, lineNumber(text, match.index));
  }

  // Workspace locators: parent-relative, macOS/Linux home, home shorthand, Windows drive, file URL.
  for (const match of text.matchAll(/(?:^|[ \t(`])(?:\.\.[\\/]|\/Users\/|\/home\/|~[\\/]|[A-Za-z]:[\\/]|file:\/\/)/gm)) {
    fail(report.file, "contains an inaccessible workspace locator", lineNumber(text, match.index));
  }

  for (const match of text.matchAll(/\*\*DECISION\s+—[^*]*\*\*/g)) {
    const start = text.lastIndexOf("\n", match.index) + 1;
    const end = text.indexOf("\n", match.index);
    const line = text.slice(start, end < 0 ? text.length : end);
    if (!/\d{4}-\d{2}-\d{2}/.test(match[0])) fail(report.file, "DECISION lacks ISO date", lineNumber(text, match.index));
    if (!line.includes("[[OWNER:")) fail(report.file, "DECISION lacks an OWNER tag", lineNumber(text, match.index));
  }
}

if (errors.length) {
  console.error(`Report contract failed with ${errors.length} error(s):`);
  for (const error of errors) console.error(`  - ${error}`);
  process.exit(1);
}

console.log(`Report contract passed: ${config.reports.length} reports, ${questionIds.size} bound questions, ${evidenceOwners.size} evidence records.`);
