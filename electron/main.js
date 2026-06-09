const { app, BrowserWindow, dialog, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const net = require('net');
const http = require('http');
const log = require('electron-log');

if (process.platform === 'linux') {
  app.commandLine.appendSwitch('no-sandbox');
  app.commandLine.appendSwitch('disable-setuid-sandbox');
  app.commandLine.appendSwitch('disable-gpu-sandbox');
}

let mainWindow = null;
let pythonProcess = null;
let serverPort = null;

const APP_TITLE = 'Trillion News Post';

function isPackaged() {
  return app.isPackaged;
}

function projectRoot() {
  return isPackaged()
    ? path.join(process.resourcesPath, 'app')
    : path.join(__dirname, '..');
}

function userDataRoot() {
  return app.getPath('userData');
}

function resolvePackagedPython() {
  const binDir = process.platform === 'win32'
    ? path.join(process.resourcesPath, 'python-venv', 'Scripts')
    : path.join(process.resourcesPath, 'python-venv', 'bin');
  const names = process.platform === 'win32'
    ? ['python.exe', 'python3.exe']
    : ['python3', 'python3.12', 'python'];

  for (const name of names) {
    const candidate = path.join(binDir, name);
    if (!fs.existsSync(candidate)) {
      continue;
    }
    try {
      const stat = fs.lstatSync(candidate);
      if (stat.isSymbolicLink()) {
        const target = fs.readlinkSync(candidate);
        const resolved = path.isAbsolute(target)
          ? target
          : path.resolve(path.dirname(candidate), target);
        if (fs.existsSync(resolved)) {
          return candidate;
        }
        continue;
      }
      return candidate;
    } catch (error) {
      log.warn('Skipping invalid bundled Python candidate', candidate, error);
    }
  }

  return path.join(binDir, process.platform === 'win32' ? 'python.exe' : 'python3');
}

function pythonExecutable() {
  if (isPackaged()) {
    return resolvePackagedPython();
  }

  const candidates = [
    path.join(__dirname, '..', '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python3'),
    path.join(__dirname, '..', '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python'),
  ];
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }
  return process.platform === 'win32' ? 'python' : 'python3';
}

function playwrightBrowsersPath() {
  if (isPackaged()) {
    return path.join(process.resourcesPath, 'playwright-browsers');
  }
  return process.env.PLAYWRIGHT_BROWSERS_PATH || '';
}

function ensureOperatorEnv() {
  const dataRoot = userDataRoot();
  const outputDir = path.join(dataRoot, 'output');
  const imageDir = path.join(outputDir, 'Ảnh Trillion $ news');
  const postDir = path.join(outputDir, 'posts');
  const logDir = path.join(outputDir, 'logs');
  const excelFile = path.join(outputDir, 'Trillion $ news.xlsx');

  for (const dir of [outputDir, imageDir, postDir, logDir]) {
    fs.mkdirSync(dir, { recursive: true });
  }

  const envPath = path.join(dataRoot, '.env');
  const examplePath = path.join(projectRoot(), '.env.example');
  if (!fs.existsSync(envPath) && fs.existsSync(examplePath)) {
    fs.copyFileSync(examplePath, envPath);
    log.info('Seeded operator .env from .env.example at', envPath);
  }

  const keywordsPath = path.join(dataRoot, 'keywords.txt');
  const bundledKeywords = path.join(projectRoot(), 'keywords.txt');
  if (!fs.existsSync(keywordsPath) && fs.existsSync(bundledKeywords)) {
    fs.copyFileSync(bundledKeywords, keywordsPath);
    log.info('Seeded operator keywords at', keywordsPath);
  }

  const env = {
    ...process.env,
    ENV_FILE: envPath,
    KEYWORDS_FILE: keywordsPath,
    OUTPUT_DIR: outputDir,
    EXCEL_FILE: excelFile,
    IMAGE_DIR: imageDir,
    POST_DIR: postDir,
    LOG_DIR: logDir,
  };

  const browsersPath = playwrightBrowsersPath();
  if (browsersPath) {
    env.PLAYWRIGHT_BROWSERS_PATH = browsersPath;
  }

  if (isPackaged() && process.platform === 'linux') {
    const libDir = path.join(process.resourcesPath, 'python-venv', 'lib');
    if (fs.existsSync(libDir)) {
      env.LD_LIBRARY_PATH = [libDir, env.LD_LIBRARY_PATH].filter(Boolean).join(path.delimiter);
    }
  }

  return { env, envPath, outputDir };
}

function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, '127.0.0.1', () => {
      const address = server.address();
      const port = typeof address === 'object' && address ? address.port : 8080;
      server.close(() => resolve(port));
    });
    server.on('error', reject);
  });
}

function waitForServer(port, timeoutMs = 90000) {
  const started = Date.now();
  return new Promise((resolve, reject) => {
    const attempt = () => {
      const req = http.get(`http://127.0.0.1:${port}/`, (res) => {
        res.resume();
        resolve();
      });
      req.on('error', () => {
        if (Date.now() - started > timeoutMs) {
          reject(new Error(`Web UI did not start on port ${port}`));
          return;
        }
        setTimeout(attempt, 500);
      });
      req.setTimeout(2500, () => {
        req.destroy();
      });
    };
    attempt();
  });
}

function stopPythonProcess() {
  if (!pythonProcess) {
    return;
  }
  try {
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', String(pythonProcess.pid), '/f', '/t']);
    } else {
      pythonProcess.kill('SIGTERM');
    }
  } catch (error) {
    log.warn('Failed to stop python process cleanly', error);
  }
  pythonProcess = null;
}

async function startPythonBackend(port) {
  const python = pythonExecutable();
  if (isPackaged() && !fs.existsSync(python)) {
    throw new Error(`Bundled Python runtime not found at ${python}`);
  }

  const { env } = ensureOperatorEnv();
  const cwd = projectRoot();
  const args = [path.join(cwd, 'main.py'), 'web', '--port', String(port)];

  log.info('Starting backend', python, args.join(' '));

  pythonProcess = spawn(python, args, {
    cwd,
    env,
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  pythonProcess.stdout.on('data', (chunk) => log.info('[python]', chunk.toString().trimEnd()));
  pythonProcess.stderr.on('data', (chunk) => log.warn('[python]', chunk.toString().trimEnd()));
  pythonProcess.on('exit', (code, signal) => {
    log.info('Python backend exited', { code, signal });
    pythonProcess = null;
    if (mainWindow && !mainWindow.isDestroyed()) {
      dialog.showErrorBox(
        APP_TITLE,
        `The local Web UI backend stopped unexpectedly (code ${code ?? 'unknown'}).`
      );
    }
  });
}

function createMainWindow(port) {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1100,
    minHeight: 700,
    title: APP_TITLE,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.loadURL(`http://127.0.0.1:${port}/`);

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

async function bootstrap() {
  try {
    serverPort = await findFreePort();
    await startPythonBackend(serverPort);
    await waitForServer(serverPort);
    createMainWindow(serverPort);
  } catch (error) {
    log.error('Failed to bootstrap desktop app', error);
    dialog.showErrorBox(
      APP_TITLE,
      `${error.message}\n\nCheck electron-log for details.`
    );
    app.quit();
  }
}

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(bootstrap);

  app.on('before-quit', () => {
    stopPythonProcess();
  });

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      app.quit();
    }
  });

  app.on('activate', async () => {
    if (BrowserWindow.getAllWindows().length === 0 && serverPort) {
      createMainWindow(serverPort);
    }
  });
}