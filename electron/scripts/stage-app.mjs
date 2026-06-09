import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..', '..');
const stageRoot = path.resolve(__dirname, '..', 'staging', 'app');

const COPY_ITEMS = [
  'main.py',
  'requirements.txt',
  'config.yaml',
  '.env.example',
  'keywords.txt',
  'src',
  'scripts/bin',
];

const SKIP_DIR_NAMES = new Set([
  '__pycache__',
  '.pytest_cache',
  'node_modules',
  '.git',
  'output',
  '.venv',
  'venv',
  'electron',
  'dist',
  'staging',
  'runtime',
]);

function shouldSkip(relPath) {
  return relPath.split(path.sep).some((part) => SKIP_DIR_NAMES.has(part));
}

function copyRecursive(src, dest) {
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    fs.mkdirSync(dest, { recursive: true });
    for (const entry of fs.readdirSync(src)) {
      const srcPath = path.join(src, entry);
      const destPath = path.join(dest, entry);
      const rel = path.relative(repoRoot, srcPath);
      if (shouldSkip(rel)) continue;
      copyRecursive(srcPath, destPath);
    }
    return;
  }
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
}

function seedKeywordsIfMissing() {
  const keywordsPath = path.join(repoRoot, 'keywords.txt');
  if (!fs.existsSync(keywordsPath)) {
    fs.writeFileSync(
      keywordsPath,
      'Payment services trillion $\nMobile payments trillion $\n',
      'utf8'
    );
  }
}

function main() {
  seedKeywordsIfMissing();
  fs.rmSync(stageRoot, { recursive: true, force: true });
  fs.mkdirSync(stageRoot, { recursive: true });

  for (const item of COPY_ITEMS) {
    const src = path.join(repoRoot, item);
    if (!fs.existsSync(src)) {
      console.warn(`[stage-app] skip missing: ${item}`);
      continue;
    }
    const dest = path.join(stageRoot, item);
    copyRecursive(src, dest);
    console.log(`[stage-app] copied ${item}`);
  }

  console.log(`[stage-app] staged to ${stageRoot}`);
}

main();