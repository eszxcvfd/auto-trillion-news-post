import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const venvDir = path.resolve(__dirname, '..', 'runtime', 'venv');

function pythonCandidates() {
  if (process.platform === 'win32') {
    return ['python.exe', 'python3.exe'];
  }
  return ['python3', 'python3.12', 'python'];
}

function binDir() {
  return process.platform === 'win32'
    ? path.join(venvDir, 'Scripts')
    : path.join(venvDir, 'bin');
}

function resolveWithoutBrokenSymlink(targetPath) {
  try {
    const stat = fs.lstatSync(targetPath);
    if (!stat.isSymbolicLink()) {
      return targetPath;
    }
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
  } catch (error) {
    throw new Error(`Invalid Python entrypoint ${targetPath}: ${error.message}`);
  }
}

function main() {
  if (!fs.existsSync(venvDir)) {
    throw new Error(`Bundled venv missing at ${venvDir}`);
  }

  const candidates = pythonCandidates()
    .map((name) => path.join(binDir(), name))
    .filter((candidate) => fs.existsSync(candidate));

  if (!candidates.length) {
    throw new Error(`No Python executable found under ${binDir()}`);
  }

  const python = resolveWithoutBrokenSymlink(candidates[0]);
  const stat = fs.statSync(python);
  if (!stat.isFile()) {
    throw new Error(`Python entrypoint is not a regular file: ${python}`);
  }

  const probe = spawnSync(python, ['-c', "import flask, playwright; print('ok')"], {
    encoding: 'utf8',
  });
  if (probe.status !== 0) {
    throw new Error(
      `Bundled Python failed self-test:\n${probe.stdout}\n${probe.stderr}`
    );
  }

  console.log(`[verify-portable-venv] ok: ${python}`);
}

main();