import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const venvDir = path.resolve(__dirname, '..', 'runtime', 'venv');

function pythonCandidates() {
  if (process.platform === 'win32') {
    return [path.join(venvDir, 'python.exe'), path.join(venvDir, 'python3.exe')];
  }
  return [
    path.join(venvDir, 'bin', 'python3'),
    path.join(venvDir, 'bin', 'python3.12'),
    path.join(venvDir, 'bin', 'python'),
  ];
}

function resolvePythonEntrypoint(targetPath) {
  const stat = fs.lstatSync(targetPath);
  if (stat.isSymbolicLink()) {
    const linkTarget = fs.readlinkSync(targetPath);
    const resolved = path.isAbsolute(linkTarget)
      ? linkTarget
      : path.resolve(path.dirname(targetPath), linkTarget);
    if (!fs.existsSync(resolved)) {
      throw new Error(`Broken symlink: ${targetPath} -> ${linkTarget}`);
    }
    if (!resolved.startsWith(venvDir)) {
      throw new Error(`External symlink is not portable: ${targetPath} -> ${resolved}`);
    }
    return resolved;
  }
  return targetPath;
}

function runtimeEnv() {
  const env = { ...process.env };
  if (process.platform === 'linux') {
    const libDir = path.join(venvDir, 'lib');
    if (fs.existsSync(libDir)) {
      env.LD_LIBRARY_PATH = [libDir, env.LD_LIBRARY_PATH].filter(Boolean).join(path.delimiter);
    }
  }
  return env;
}

function main() {
  if (!fs.existsSync(venvDir)) {
    throw new Error(`Bundled Python runtime missing at ${venvDir}`);
  }

  const candidates = pythonCandidates().filter((candidate) => fs.existsSync(candidate));
  if (!candidates.length) {
    throw new Error(`No Python executable found under ${venvDir}`);
  }

  const python = resolvePythonEntrypoint(candidates[0]);
  const stat = fs.statSync(python);
  if (!stat.isFile()) {
    throw new Error(`Python entrypoint is not a regular file: ${python}`);
  }

  const probe = spawnSync(
    python,
    ['-c', "import sys, flask, playwright; print(sys.executable); print('ok')"],
    {
      encoding: 'utf8',
      env: runtimeEnv(),
    },
  );
  if (probe.status !== 0) {
    throw new Error(
      `Bundled Python failed self-test:\n${probe.stdout}\n${probe.stderr}`
    );
  }

  if (probe.stdout.includes('/opt/hostedtoolcache/')) {
    throw new Error('Bundled Python still depends on CI-only hostedtoolcache paths');
  }

  console.log(`[verify-portable-venv] ok: ${python.trim()}`);
}

main();