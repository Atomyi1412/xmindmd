# XMind ⇄ Markdown 转换器 v1.1.0

一个基于 Electron 的桌面应用，支持 XMind 思维导图与 Markdown 文档之间的双向转换。

## 功能特性

- 🔄 **双向转换**：支持 XMind → Markdown 和 Markdown → XMind 的转换
- 📝 **Markdown 重构**：支持 Markdown 文档的结构重组
- 🎨 **多主题支持**：内置 12 套精美配色主题
- 💻 **跨平台**：支持 macOS 和 Windows 系统
- 🚀 **本地运行**：无需联网，保护数据隐私
- 📦 **一键安装**：提供 DMG 和 NSIS 安装包

## 支持格式

### 输入格式
- XMind 文件 (.xmind)
- Markdown 文件 (.md)

### 输出格式
- XMind 思维导图 (.xmind)
- Markdown 文档 (.md)

## 安装使用

### 下载安装包

从 [Releases](../../releases) 页面下载对应平台的安装包：

- **macOS**: `XMind ⇄ Markdown 转换器-1.1.0-arm64.dmg`
- **Windows**: `XMind ⇄ Markdown 转换器 Setup 1.1.0.exe`

### 开发环境

```bash
# 克隆项目
git clone <repository-url>
cd xmindmd

# 安装依赖
npm install

# 启动开发模式
npm run dev

# 构建安装包
npm run build:mac    # macOS DMG
npm run build:win    # Windows NSIS
npm run build:all    # 所有平台
```

## 技术栈

- **前端**: HTML5 + CSS3 + JavaScript
- **后端**: Node.js + Express
- **桌面**: Electron
- **构建**: electron-builder
- **样式**: Tailwind CSS
- **文件处理**: JSZip, Multer

## 项目结构

```
├── index.html          # 主界面
├── themes.html         # 主题配置页面
├── main.js            # Electron 主进程
├── server.js          # Express 后端服务
├── package.json       # 项目配置
├── *.py              # Python 转换脚本
└── dist/             # 构建输出目录
```

## 转换原理

### XMind → Markdown
1. 解析 XMind 文件的 JSON/XML 结构
2. 提取主题层级关系
3. 转换为 Markdown 标题和列表格式
4. 保留备注信息

### Markdown → XMind
1. 解析 Markdown 标题层级
2. 构建思维导图节点树
3. 生成 XMind 格式的 ZIP 文件
4. 包含元数据和样式信息

## 许可证

MIT License

## 更新日志

### v1.0.0 (2024-01-09)
- 🎉 首次发布
- ✨ 支持 XMind ⇄ Markdown 双向转换
- 🎨 内置 12 套配色主题
- 📦 提供 macOS 和 Windows 安装包
- 🔧 完整的本地化界面

---

如有问题或建议，欢迎提交 [Issue](../../issues) 或 [Pull Request](../../pulls)。