import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const electronRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(electronRoot, '..');
const runtimeRoot = path.join(electronRoot, 'runtime');
const venvDir = path.join(runtimeRoot, 'venv');
const browsersDir = path.join(runtimeRoot, 'playwright-browsers');

const STANDALONE_TAG = '20260602';
const STANDALONE_VERSION = '3.12.13';

const STANDALONE_ASSETS = {
  linux: `cpython-${STANDALONE_VERSION}+${STANDALONE_TAG}-x86_64-unknown-linux-gnu-install_only.tar.gz`,
  win32: `cpython-${STANDALONE_VERSION}+${STANDALONE_TAG}-x86_64-pc-windows-msvc-install_only.tar.gz`,
};

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    stdio: 'inherit',
    ...options,
  });
  if (result.status !== 0) {
    throw new Error(`Command failed: ${command} ${args.join(' ')}`);
  }
}

function pythonBin(name = 'python3') {
  if (process.platform === 'win32') {
    return path.join(venvDir, 'python.exe');
  }
  const binName = name === 'python' ? 'python3' : name;
  return path.join(venvDir, 'bin', binName);
}

function standaloneArchiveUrl() {
  const asset = STANDALONE_ASSETS[process.platform];
  if (!asset) {
    throw new Error(`Unsupported packaging platform: ${process.platform}`);
  }
  return `https://github.com/astral-sh/python-build-standalone/releases/download/${STANDALONE_TAG}/${encodeURIComponent(asset)}`;
}

function downloadStandalonePython(archivePath) {
  const url = standaloneArchiveUrl();
  console.log(`[prepare-runtime] downloading ${url}`);
  run('curl', ['-fL', url, '-o', archivePath]);
}

function extractStandalonePython() {
  fs.mkdirSync(venvDir, { recursive: true });
  // Use paths relative to runtimeRoot so Git Bash tar on Windows can extract safely.
  run('tar', ['-xzf', 'python-standalone.tar.gz', '-C', 'venv', '--strip-components=1', 'python'], {
    cwd: runtimeRoot,
  });
}

function installPythonDependencies(python) {
  run(python, ['-m', 'pip', 'install', '--upgrade', 'pip']);
  run(python, ['-m', 'pip', 'install', '-r', path.join(repoRoot, 'requirements.txt')]);
  run(python, ['-m', 'playwright', 'install', 'chromium'], {
    env: {
      ...process.env,
      PLAYWRIGHT_BROWSERS_PATH: browsersDir,
    },
  });
}

function main() {
  fs.rmSync(runtimeRoot, { recursive: true, force: true });
  fs.mkdirSync(browsersDir, { recursive: true });

  const archivePath = path.join(runtimeRoot, 'python-standalone.tar.gz');
  fs.mkdirSync(runtimeRoot, { recursive: true });

  downloadStandalonePython(archivePath);
  extractStandalonePython();
  fs.rmSync(archivePath, { force: true });

  const python = pythonBin();
  if (!fs.existsSync(python)) {
    throw new Error(`Standalone Python missing at ${python}`);
  }

  installPythonDependencies(python);
  run(process.execPath, [path.join(__dirname, 'verify-portable-venv.mjs')]);

  console.log(`[prepare-runtime] standalone python: ${python}`);
  console.log(`[prepare-runtime] browsers: ${browsersDir}`);
}

main();