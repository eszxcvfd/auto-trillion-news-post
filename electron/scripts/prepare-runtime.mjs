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

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    stdio: 'inherit',
    ...options,
  });
  if (result.status !== 0) {
    throw new Error(`Command failed: ${command} ${args.join(' ')}`);
  }
}

function pythonBin(name) {
  if (process.platform === 'win32') {
    return path.join(venvDir, 'Scripts', `${name}.exe`);
  }
  return path.join(venvDir, 'bin', name);
}

function queryPythonLibDir(pythonLauncher) {
  const probe = spawnSync(
    pythonLauncher,
    [
      '-c',
      'import pathlib, sysconfig; print(pathlib.Path(sysconfig.get_config_var("LIBDIR") or "").resolve())',
    ],
    { encoding: 'utf8' },
  );
  if (probe.status !== 0) {
    throw new Error(`Failed to resolve Python LIBDIR:\n${probe.stderr}`);
  }
  return probe.stdout.trim();
}

function bundleLinuxPythonLibs(pythonLauncher) {
  if (process.platform !== 'linux') {
    return;
  }

  const sourceLibDir = queryPythonLibDir(pythonLauncher);
  const targetLibDir = path.join(venvDir, 'lib');
  fs.mkdirSync(targetLibDir, { recursive: true });

  let copied = 0;
  for (const entry of fs.readdirSync(sourceLibDir)) {
    if (!/^libpython3\.\d+\.so(?:\.\d+\.\d+)?$/.test(entry)) {
      continue;
    }
    fs.copyFileSync(path.join(sourceLibDir, entry), path.join(targetLibDir, entry));
    copied += 1;
    console.log(`[prepare-runtime] bundled ${entry}`);
  }

  if (!copied) {
    throw new Error(`No libpython shared libraries found in ${sourceLibDir}`);
  }
}

function main() {
  fs.rmSync(runtimeRoot, { recursive: true, force: true });
  fs.mkdirSync(browsersDir, { recursive: true });

  const pythonLauncher = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
  // --copies embeds real Python binaries instead of CI-only symlinks.
  run(pythonLauncher, ['-m', 'venv', venvDir, '--copies']);
  bundleLinuxPythonLibs(pythonLauncher);

  const python = pythonBin('python');
  run(python, ['-m', 'pip', 'install', '--upgrade', 'pip']);
  run(python, ['-m', 'pip', 'install', '-r', path.join(repoRoot, 'requirements.txt')]);
  run(python, ['-m', 'playwright', 'install', 'chromium'], {
    env: {
      ...process.env,
      PLAYWRIGHT_BROWSERS_PATH: browsersDir,
    },
  });

  run(process.execPath, [path.join(__dirname, 'verify-portable-venv.mjs')]);

  console.log(`[prepare-runtime] venv: ${venvDir}`);
  console.log(`[prepare-runtime] browsers: ${browsersDir}`);
}

main();