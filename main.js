// main.js - Electron main process
const { app, BrowserWindow, Menu, dialog, shell } = require('electron');
const path = require('path');
const { startServer } = require('./server');

let mainWindow = null;
let serverInfo = null;

function createWindow(port) {
  // 获取屏幕尺寸
  const { screen } = require('electron');
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize;
  
  // 计算窗口尺寸（屏幕的80%，但不小于最小尺寸）
  const windowWidth = Math.max(1200, Math.floor(screenWidth * 0.8));
  const windowHeight = Math.max(900, Math.floor(screenHeight * 0.8));
  
  mainWindow = new BrowserWindow({
    width: windowWidth,
    height: windowHeight,
    minWidth: 1000,
    minHeight: 800,
    center: true, // 窗口居中显示
    title: 'XMind ⇄ Markdown 转换器 v1.1.0',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true
    }
  });
  mainWindow.loadURL(`http://localhost:${port}/index.html`);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

async function init() {
  serverInfo = await startServer(0); // random free port
  createWindow(serverInfo.port);
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (mainWindow === null && serverInfo) createWindow(serverInfo.port);
});

app.whenReady().then(() => {
  // Basic menu with Copy/Paste and DevTools toggle in development
  const isMac = process.platform === 'darwin';
  const template = [
    ...(isMac ? [{ role: 'appMenu' }] : []),
    { role: 'fileMenu' },
    { role: 'editMenu' },
    { role: 'viewMenu' },
    { role: 'windowMenu' },
    { role: 'help', submenu: [{ label: '打开主页', click: () => mainWindow && shell.openExternal('https://xmind.net') }] }
  ];
  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
  init();
});

app.on('before-quit', () => {
  if (serverInfo && serverInfo.server) {
    try { serverInfo.server.close(); } catch {}
  }
});