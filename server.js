// server.js - Express backend for XMind ⇄ Markdown converter
const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const os = require('os');
const crypto = require('crypto');
const JSZip = require('jszip');

// In-memory store for latest binary (md_to_xmind) to support download
let lastBinary = null;
let lastFilename = null;
let lastTextBuffer = null; // Buffer for latest text content (markdown)
let lastContentType = 'text/markdown; charset=utf-8';

const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 16 * 1024 * 1024 } });

function safeJSONParse(str) {
  try { return JSON.parse(str); } catch { return null; }
}

function parseXMindXML(xmlStr) {
  try {
    // Simple XML parsing for XMind format
    // This is a basic implementation that handles common XMind XML structure
    const sheets = [];
    
    // Extract sheet elements
    const sheetMatches = xmlStr.match(/<sheet[^>]*>([\s\S]*?)<\/sheet>/gi);
    if (!sheetMatches) return null;
    
    for (const sheetMatch of sheetMatches) {
      // Extract root topic
      const topicMatch = sheetMatch.match(/<topic[^>]*>([\s\S]*?)<\/topic>/i);
      if (!topicMatch) continue;
      
      const rootTopic = parseXMLTopic(topicMatch[0]);
      if (rootTopic) {
        sheets.push({ rootTopic });
      }
    }
    
    return sheets.length > 0 ? sheets : null;
  } catch (error) {
    console.error('XML parsing error:', error);
    return null;
  }
}

function parseXMLTopic(topicXML) {
  try {
    // Extract title
    const titleMatch = topicXML.match(/<title>([^<]*)<\/title>/i);
    const title = titleMatch ? titleMatch[1] : '未命名主题';
    
    // Extract notes
    const notesMatch = topicXML.match(/<notes>([\s\S]*?)<\/notes>/i);
    let note = '';
    if (notesMatch) {
      const plainMatch = notesMatch[1].match(/<plain>([\s\S]*?)<\/plain>/i);
      if (plainMatch) {
        note = plainMatch[1].replace(/<[^>]*>/g, '').trim();
      }
    }
    
    // Extract children topics
    const children = { attached: [] };
    const childMatches = topicXML.match(/<topics[^>]*>([\s\S]*?)<\/topics>/gi);
    
    if (childMatches) {
      for (const childMatch of childMatches) {
        const subTopicMatches = childMatch.match(/<topic[^>]*>([\s\S]*?)<\/topic>/gi);
        if (subTopicMatches) {
          for (const subTopicMatch of subTopicMatches) {
            const childTopic = parseXMLTopic(subTopicMatch);
            if (childTopic) {
              children.attached.push(childTopic);
            }
          }
        }
      }
    }
    
    const topic = { title };
    if (note) {
      topic.notes = { plain: { content: note } };
    }
    if (children.attached.length > 0) {
      topic.children = children;
    }
    
    return topic;
  } catch (error) {
    console.error('Topic parsing error:', error);
    return null;
  }
}

function convertMdToMd(content) {
  const lines = content.split('\n');
  // Parse headers: list of [lineIndex, level, title]
  const headers = [];
  lines.forEach((line, i) => {
    const m = line.trim().match(/^(#{1,6})\s+(.+)$/);
    if (m) headers.push([i, m[1].length, m[2].trim()]);
  });
  function findParentH2(h3IndexInHeaders) {
    for (let i = h3IndexInHeaders - 1; i >= 0; i--) {
      if (headers[i][1] === 2) return headers[i][2];
    }
    return '未分类';
  }
  const result = [];
  for (let i = 0; i < lines.length; i++) {
    let isH2 = false, isH3 = false, parentH2 = '';
    for (let j = 0; j < headers.length; j++) {
      const [lineNum, level] = headers[j];
      if (lineNum === i) {
        if (level === 2) isH2 = true;
        if (level === 3) { isH3 = true; parentH2 = findParentH2(j); }
        break;
      }
    }
    if (isH2) continue; // skip original H2
    if (isH3) {
      result.push(`## ${parentH2}`);
      result.push(lines[i]);
    } else {
      result.push(lines[i]);
    }
  }
  return result.join('\n');
}

function parseMarkdownToStructure(content) {
  const lines = content.split('\n');
  const structure = { title: 'Markdown 思维导图', children: [] };
  const pathStack = [structure];
  let firstH1Found = false;
  
  for (let raw of lines) {
    const line = raw.replace(/\r$/, '').trimEnd();
    if (!line.trim()) continue;

    const h = line.trim().match(/^(#{1,6})\s+(.+)$/);
    if (h) {
      const level = h[1].length;
      const title = h[2].trim();
      
      // 如果是第一个一级标题，直接设为根节点标题，不添加到 children
      if (level === 1 && !firstH1Found) {
        structure.title = title;
        firstH1Found = true;
        // 重置路径栈，准备处理后续内容
        pathStack.length = 1; // 保持只有 structure
        continue;
      }
      
      const node = { title, children: [] };
      // 所有标题都需要上移一级：一级变根节点，二级变一级，三级变二级，以此类推
      let adjustedLevel;
      if (level === 1) {
        // 后续的一级标题作为一级分支
        adjustedLevel = 1;
      } else {
        // 其他级别标题上移一级
        adjustedLevel = level - 1;
      }
      
      // 确保 adjustedLevel 至少为 1（作为根节点的直接子节点）
      if (adjustedLevel < 1) adjustedLevel = 1;
      
      while (pathStack.length > adjustedLevel) pathStack.pop();
      if (pathStack.length === 0) pathStack.push(structure);
      (pathStack[pathStack.length - 1].children).push(node);
      pathStack.push(node);
      continue;
    }

    const lm = line.match(/^(\s*)([-*+])\s+(.+)$/);
    if (lm) {
      const indent = lm[1].length;
      const title = lm[3].trim();
      const level = Math.floor(indent / 2) + 1; // two spaces per level
      const node = { title, children: [] };
      
      // 如果已经找到第一个一级标题，列表项层级不需要额外调整
      const adjustedLevel = level;
      
      while (pathStack.length > adjustedLevel) pathStack.pop();
      if (pathStack.length === 0) pathStack.push(structure);
      (pathStack[pathStack.length - 1].children).push(node);
      pathStack.push(node);
      continue;
    }

    // plain text -> note (if no children) or child text node
    if (pathStack.length > 1) {
      const current = pathStack[pathStack.length - 1];
      if (!current.children || current.children.length === 0) {
        current.note = current.note ? (current.note + '\n' + line) : line;
      } else {
        current.children.push({ title: line, children: [] });
      }
    }
  }
  return structure;
}

function buildXMindZipFromStructure(structure) {
  const zip = new JSZip();
  const uid = () => crypto.randomUUID ? crypto.randomUUID() : crypto.randomBytes(16).toString('hex');

  function buildTopic(node) {
    const topic = { id: uid(), class: 'topic', title: node.title || '' };
    if (node.note) {
      topic.notes = { plain: { content: node.note } };
    }
    const children = (node.children || []).map(buildTopic);
    if (children.length) topic.children = { attached: children };
    return topic;
  }

  const root = buildTopic({ title: structure.title || '思维导图', children: structure.children || [] });
  const sheet = { id: uid(), class: 'sheet', title: structure.title || '思维导图', rootTopic: root };
  const content = [sheet];
  const metadata = {
    dataStructureVersion: '2',
    creator: { name: 'XMindConverter', version: '1.0' },
    layoutEngineVersion: '3',
    familyId: `local-${uid()}`
  };
  const manifest = { 'file-entries': { 'content.json': {}, 'metadata.json': {} } };

  zip.file('content.json', JSON.stringify(content, null, 0));
  zip.file('metadata.json', JSON.stringify(metadata, null, 0));
  zip.file('manifest.json', JSON.stringify(manifest, null, 0));

  return zip.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' });
}

function xmindZipToMarkdown(buffer, format = 'header') {
  const zip = new JSZip();
  return zip.loadAsync(buffer).then(async z => {
    // Try content.json first (XMind 2020+)
    let file = z.file('content.json') || z.file('Content.json');
    let data;
    
    if (file) {
      // Parse JSON format
      const jsonStr = await file.async('string');
      data = safeJSONParse(jsonStr);
      if (!data) throw new Error('content.json 解析失败');
    } else {
      // Try content.xml (older XMind versions)
      file = z.file('content.xml') || z.file('Content.xml');
      if (!file) throw new Error('不支持的 XMind 格式：缺少 content.json 或 content.xml');
      
      const xmlStr = await file.async('string');
      data = parseXMindXML(xmlStr);
      if (!data) throw new Error('content.xml 解析失败');
    }

    const sheets = Array.isArray(data) ? data : [data];
    const outputs = [];

    function getChildren(topic) {
      const ch = topic.children || {};
      const list = ch.attached || ch.detached || [];
      return list;
    }

    function getNote(topic) {
      if (topic.notes && topic.notes.plain && typeof topic.notes.plain.content === 'string') return topic.notes.plain.content;
      if (typeof topic.note === 'string') return topic.note;
      return '';
    }

    function toHeaderMd(topic, level = 1, out = []) {
      const title = topic.title || '未命名主题';
      if (level <= 6) out.push('#'.repeat(level) + ' ' + title);
      else out.push('  '.repeat(level - 7) + '- ' + title);
      const note = getNote(topic).trim();
      if (note) {
        out.push('');
        for (const line of note.split('\n')) out.push('> ' + line);
        out.push('');
      }
      for (const child of getChildren(topic)) toHeaderMd(child, level + 1, out);
      if (level <= 3) out.push('');
      return out;
    }

    function toListMd(topic, level = 0, out = []) {
      const title = topic.title || '未命名主题';
      if (level === 0) { out.push('# ' + title); out.push(''); }
      else { out.push('  '.repeat(level - 1) + '- ' + title); }
      const note = getNote(topic).trim();
      if (note) {
        for (const line of note.split('\n')) out.push('  '.repeat(level) + '> ' + line);
      }
      for (const child of getChildren(topic)) toListMd(child, level + 1, out);
      return out;
    }

    for (const sheet of sheets) {
      const topic = sheet.rootTopic || sheet.topic;
      if (!topic) continue;
      const out = (format === 'list') ? toListMd(topic, 0, []) : toHeaderMd(topic, 1, []);
      outputs.push(out.join('\n'));
    }

    return outputs.join('\n');
  });
}

function createApp() {
  const app = express();
  app.use(express.json({ limit: '20mb' }));
  app.use(express.urlencoded({ extended: true }));
  // Static serve index.html and assets from current directory
  app.use(express.static(__dirname));

  // Normalize possibly mis-decoded filename (latin1 -> utf8) from multipart headers
  function normalizeFilename(name) {
    try {
      if (!name) return name;
      // If ASCII only, return as-is
      if (/^[\x00-\x7F]+$/.test(name)) return name;
      const converted = Buffer.from(name, 'latin1').toString('utf8');
      // If conversion produced replacement chars, fallback to original
      if (converted.includes('\uFFFD')) return name;
      return converted;
    } catch (e) {
      return name;
    }
  }

  app.post('/api/convert', upload.single('file'), async (req, res) => {
    try {
      // Normalize direction to a safe, comparable lower-case string
      const directionRaw = req.body && typeof req.body.direction !== 'undefined' ? req.body.direction : '';
      const direction = (Array.isArray(directionRaw) ? directionRaw[0] : String(directionRaw || '')).toLowerCase().trim();
      const format = (req.body.format || 'header').trim();
      if (!req.file) return res.json({ success: false, error: '未收到文件' });
      const originalNameRaw = req.file.originalname || 'file';
      const originalName = normalizeFilename(originalNameRaw);
      const base = path.parse(originalName).name;

      if (direction === 'xmind_to_md') {
        const md = await xmindZipToMarkdown(req.file.buffer, format);
        const filename = base + (format === 'list' ? '_list.md' : '.md');
        lastTextBuffer = Buffer.from(md, 'utf8');
        lastContentType = 'text/markdown; charset=utf-8';
        lastFilename = filename;
        return res.json({ success: true, content: md, filename });
      }

      if (direction === 'md_to_md') {
        console.log('Processing md_to_md conversion');
        console.log('File buffer length:', req.file.buffer.length);
        console.log('File mimetype:', req.file.mimetype);
        console.log('Original filename:', originalName);
        
        const text = req.file.buffer.toString('utf-8');
        console.log('Decoded text length:', text.length);
        console.log('First 100 chars:', text.substring(0, 100));
        
        const converted = convertMdToMd(text);
        console.log('Converted text length:', converted.length);
        console.log('Converted first 100 chars:', converted.substring(0, 100));
        
        const filename = base + '（转换版）.md';
        lastTextBuffer = Buffer.from(converted, 'utf8');
        lastContentType = 'text/markdown; charset=utf-8';
        lastFilename = filename;
        return res.json({ success: true, content: converted, filename });
      }

      if (direction === 'md_to_xmind') {
        const text = req.file.buffer.toString('utf-8');
        const struct = parseMarkdownToStructure(text);
        const buffer = await buildXMindZipFromStructure(struct);
        lastBinary = buffer;
        const filename = base + '.xmind';
        lastFilename = filename;
        // 清空文本缓存
        lastTextBuffer = null;
        return res.json({ success: true, filename });
      }

      // Accept several aliases for one-click optimize to be resilient
      if (['one_click_optimize', 'one-click-optimize', 'one_click', 'oneclick', 'optimize_xmind'].includes(direction)) {
        // 一键优化：XMind → MD → MD（增加二级）→ XMind
        try {
          // 步骤1：XMind → MD
          const md = await xmindZipToMarkdown(req.file.buffer, 'header');
          
          // 步骤2：MD → MD（增加二级）
          const optimizedMd = convertMdToMd(md);
          
          // 步骤3：MD → XMind
          const struct = parseMarkdownToStructure(optimizedMd);
          const buffer = await buildXMindZipFromStructure(struct);
          
          lastBinary = buffer;
          const filename = base + '（优化版）.xmind';
          lastFilename = filename;
          // 清空文本缓存
          lastTextBuffer = null;
          return res.json({ success: true, filename });
        } catch (error) {
          console.error('一键优化转换失败:', error);
          return res.json({ success: false, error: '一键优化转换失败: ' + (error && error.message ? error.message : String(error)) });
        }
      }

      return res.json({ success: false, error: '未知的转换方向: ' + direction });
    } catch (e) {
      console.error(e);
      return res.json({ success: false, error: e.message || '转换失败' });
    }
  });

  // GET download: let browser handle Content-Disposition
  app.get('/api/download', async (req, res) => {
    try {
      if (!lastFilename) return res.status(410).send('没有可下载的内容，请先进行转换');

      const safeFilename = lastFilename.replace(/[\\/:*?"<>|]/g, '_');
      const encodedFilename = encodeURIComponent(safeFilename);

      // ASCII fallback for `filename` (remove non-ASCII)
      const asciiFallback = safeFilename.replace(/[^\x00-\x7F]/g, '_');

      res.setHeader('Content-Disposition', `attachment; filename="${asciiFallback}"; filename*=UTF-8''${encodedFilename}`);

      if (lastBinary) {
        res.setHeader('Content-Type', 'application/octet-stream');
        return res.end(lastBinary);
      }

      if (lastTextBuffer) {
        res.setHeader('Content-Type', lastContentType || 'text/plain; charset=utf-8');
        return res.end(lastTextBuffer);
      }

      return res.status(410).send('没有可下载的内容，请先进行转换');
    } catch (e) {
      console.error(e);
      res.status(500).send('下载失败');
    }
  });

  // Fallback to index.html
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
  });

  return app;
}

async function startServer(port = process.env.PORT || 4400) {
  const app = createApp();
  return new Promise(resolve => {
    const server = app.listen(port, () => {
      const actualPort = server.address().port;
      console.log(`XMind ⇄ Markdown 本地服务已启动: http://localhost:${actualPort}/`);
      resolve({ server, port: actualPort });
    });
  });
}

if (require.main === module) {
  startServer();
}

module.exports = { startServer };