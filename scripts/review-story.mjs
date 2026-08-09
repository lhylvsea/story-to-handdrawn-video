import {createHash} from 'node:crypto';
import {existsSync, mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {basename, resolve} from 'node:path';

const parseArgs = (tokens) => {
  const parsed = {};
  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (!token.startsWith('--')) continue;
    const key = token.slice(2);
    const next = tokens[index + 1];
    if (next && !next.startsWith('--')) {
      parsed[key] = next;
      index += 1;
    } else {
      parsed[key] = true;
    }
  }
  return parsed;
};

const usage = () => {
  console.log(`Usage:
  node scripts/review-story.mjs --mode create --source article.txt --draft story-draft.txt --output review
  node scripts/review-story.mjs --mode approve --manifest review/story-review.json --draft story-draft.txt
  node scripts/review-story.mjs --mode check --approval review/story-review.approval.json --draft story-draft.txt`);
};

const args = parseArgs(process.argv.slice(2));
const mode = String(args.mode || 'create');

const requirePath = (value, label) => {
  if (!value) throw new Error(`${label} is required`);
  return resolve(String(value));
};

const readUtf8 = (path, label) => {
  if (!existsSync(path)) throw new Error(`${label} does not exist: ${path}`);
  return readFileSync(path, 'utf8').replace(/\r\n?/g, '\n').trim();
};

const sha256 = (value) => createHash('sha256').update(value, 'utf8').digest('hex');

const reviewUnits = (value) => {
  const lines = value.split('\n').map((line) => line.trim()).filter(Boolean);
  if (lines.length > 1) return lines;
  return value.match(/[^。！？!?]+[。！？!?]?/gu)?.map((unit) => unit.trim()).filter(Boolean) || [];
};

const lcsDiff = (source, draft) => {
  const cells = source.length * draft.length;
  if (cells > 2_000_000) {
    return [
      ...source.map((value) => ({type: 'delete', value})),
      ...draft.map((value) => ({type: 'add', value})),
    ];
  }

  const table = Array.from({length: source.length + 1}, () => new Uint32Array(draft.length + 1));
  for (let sourceIndex = source.length - 1; sourceIndex >= 0; sourceIndex -= 1) {
    for (let draftIndex = draft.length - 1; draftIndex >= 0; draftIndex -= 1) {
      table[sourceIndex][draftIndex] =
        source[sourceIndex] === draft[draftIndex]
          ? table[sourceIndex + 1][draftIndex + 1] + 1
          : Math.max(table[sourceIndex + 1][draftIndex], table[sourceIndex][draftIndex + 1]);
    }
  }

  const operations = [];
  let sourceIndex = 0;
  let draftIndex = 0;
  while (sourceIndex < source.length || draftIndex < draft.length) {
    if (
      sourceIndex < source.length &&
      draftIndex < draft.length &&
      source[sourceIndex] === draft[draftIndex]
    ) {
      operations.push({type: 'context', value: source[sourceIndex]});
      sourceIndex += 1;
      draftIndex += 1;
    } else if (
      draftIndex >= draft.length ||
      (sourceIndex < source.length && table[sourceIndex + 1][draftIndex] >= table[sourceIndex][draftIndex + 1])
    ) {
      operations.push({type: 'delete', value: source[sourceIndex]});
      sourceIndex += 1;
    } else {
      operations.push({type: 'add', value: draft[draftIndex]});
      draftIndex += 1;
    }
  }
  return operations;
};

const renderDiff = (operations) => {
  const lines = ['--- source', '+++ proposed video copy', '@@'];
  for (const operation of operations) {
    const prefix = operation.type === 'delete' ? '-' : operation.type === 'add' ? '+' : ' ';
    lines.push(`${prefix}${operation.value}`);
  }
  return `${lines.join('\n')}\n`;
};

const relativeDisplayPath = (path) => {
  const cwd = process.cwd();
  const relative = path.startsWith(cwd) ? path.slice(cwd.length + 1) : path;
  return relative.replaceAll('\\', '/');
};

const createReview = () => {
  const sourcePath = requirePath(args.source, '--source');
  const draftPath = requirePath(args.draft, '--draft');
  const outputDir = resolve(String(args.output || 'review'));
  const sourceText = readUtf8(sourcePath, 'Source file');
  const draftText = readUtf8(draftPath, 'Draft file');
  if (!sourceText) throw new Error('Source file is empty');
  if (!draftText) throw new Error('Draft file is empty');

  mkdirSync(outputDir, {recursive: true});
  const sourceUnits = reviewUnits(sourceText);
  const draftUnits = reviewUnits(draftText);
  const operations = lcsDiff(sourceUnits, draftUnits);
  const sourceHash = sha256(sourceText);
  const draftHash = sha256(draftText);
  const reviewId = sha256(`${sourceHash}\n${draftHash}`).slice(0, 12);
  const diffPath = resolve(outputDir, 'story-review.diff');
  const reportPath = resolve(outputDir, 'story-review.md');
  const manifestPath = resolve(outputDir, 'story-review.json');

  const diff = renderDiff(operations);
  const report = `# Story content review

- Status: \`pending\`
- Review id: \`${reviewId}\`
- Source: \`${relativeDisplayPath(sourcePath)}\`
- Draft: \`${relativeDisplayPath(draftPath)}\`
- Source SHA-256: \`${sourceHash}\`
- Draft SHA-256: \`${draftHash}\`
- Source units: ${sourceUnits.length}
- Proposed video beats: ${draftUnits.length}

This review is a content gate. Check names, dates, figures, quotations, policy wording, causal claims, omissions, and any inference added during compression. Do not generate images, audio, or a final video until the draft is explicitly approved.

## Proposed video copy

${draftText}

## Source-to-draft diff

\`\`\`diff
${diff}\`\`\`

## Approval checklist

- [ ] Key facts and proper nouns match the source.
- [ ] Dates, numbers, quotations, and policy terms were checked.
- [ ] Omissions and compressions are intentional.
- [ ] No unsupported inference is presented as a source conclusion.
- [ ] The proposed wording is ready for storyboard captions and narration.

## Next commands

\`\`\`bash
# After editing the draft, recreate this report and diff.
python3 scripts/run_story_video.py --mode review --source ${relativeDisplayPath(sourcePath)} --input ${relativeDisplayPath(draftPath)} --review-dir ${relativeDisplayPath(outputDir)}

# Only after the user confirms the current draft.
python3 scripts/run_story_video.py --mode approve --input ${relativeDisplayPath(draftPath)} --review-manifest ${relativeDisplayPath(manifestPath)}

# Pass the approval file to generation.
python3 scripts/run_story_video.py --mode generate --input ${relativeDisplayPath(draftPath)} --approved-review ${relativeDisplayPath(resolve(outputDir, 'story-review.approval.json'))}
\`\`\`
`;

  const manifest = {
    version: 1,
    status: 'pending',
    review_id: reviewId,
    source_path: sourcePath,
    draft_path: draftPath,
    source_sha256: sourceHash,
    draft_sha256: draftHash,
    source_units: sourceUnits.length,
    draft_units: draftUnits.length,
    diff_path: diffPath,
    report_path: reportPath,
  };

  writeFileSync(diffPath, diff, 'utf8');
  writeFileSync(reportPath, report, 'utf8');
  writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
  console.log(`Review report: ${reportPath}`);
  console.log(`Review diff: ${diffPath}`);
  console.log(`Review manifest: ${manifestPath}`);
  console.log('Status: pending user approval');
};

const readManifest = (path, label) => {
  const manifestPath = requirePath(path, label);
  if (!existsSync(manifestPath)) throw new Error(`${label} does not exist: ${manifestPath}`);
  return {path: manifestPath, value: JSON.parse(readFileSync(manifestPath, 'utf8'))};
};

const verifyDraftHash = (manifest, draftPath) => {
  const currentDraft = readUtf8(draftPath, 'Draft file');
  const currentHash = sha256(currentDraft);
  if (currentHash !== manifest.draft_sha256) {
    throw new Error(
      `Draft changed after review. Recreate the review before approval (expected ${manifest.draft_sha256}, got ${currentHash}).`,
    );
  }
  return currentHash;
};

const approveReview = () => {
  const {path: manifestPath, value: manifest} = readManifest(args.manifest, '--manifest');
  if (manifest.status !== 'pending') throw new Error(`Review status must be pending, got ${manifest.status}`);
  const draftPath = resolve(String(args.draft || manifest.draft_path));
  const currentHash = verifyDraftHash(manifest, draftPath);
  const approvalPath = resolve(String(args.output || manifestPath.replace(/\.json$/u, '.approval.json')));
  const approval = {
    version: 1,
    status: 'approved',
    review_id: manifest.review_id,
    manifest_path: manifestPath,
    draft_path: draftPath,
    draft_sha256: currentHash,
    approved_at: new Date().toISOString(),
  };
  writeFileSync(approvalPath, `${JSON.stringify(approval, null, 2)}\n`, 'utf8');
  console.log(`Approval record: ${approvalPath}`);
  console.log('Status: approved');
};

const checkApproval = () => {
  const {value: approval} = readManifest(args.approval, '--approval');
  if (approval.status !== 'approved') throw new Error(`Approval status is not approved: ${approval.status}`);
  const draftPath = resolve(String(args.draft || approval.draft_path));
  verifyDraftHash(approval, draftPath);
  console.log(`Approval valid for ${basename(draftPath)}.`);
};

try {
  if (mode === 'create') createReview();
  else if (mode === 'approve') approveReview();
  else if (mode === 'check') checkApproval();
  else {
    usage();
    process.exitCode = 1;
  }
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
}
