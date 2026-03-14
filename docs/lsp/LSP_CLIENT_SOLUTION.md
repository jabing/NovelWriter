# 🎯 最简单的解决方案：使用 pygls 官方示例

经过多次尝试通用 LSP 客户端扩展，我发现它们配置复杂且不稳定。
**最可靠的方法**是使用 pygls 官方提供的 VS Code 扩展示例。

---

## ⚡ 快速方案（10 分钟）

### 步骤 1：获取 pygls 示例

```powershell
# 在 PowerShell 中
cd C:\dev_projects
git clone https://github.com/openlawlibrary/pygls.git
```

### 步骤 2：修改示例连接到 NovelWriter LSP

编辑文件：`C:\dev_projects\pygls\examples\json-extension\client\src\extension.ts`

找到第 15-20 行，修改为：

```typescript
// 原来的代码（连接到 JSON 服务器）
const serverOptions: ServerOptions = {
    command: "python",
    args: ["-m", "pygls", "examples/servers/json_server.py"],
    transport: TransportKind.stdio
};

// 修改为连接到 NovelWriter LSP
const serverOptions: ServerOptions = {
    command: "python",
    args: ["-m", "novelwriter_lsp"],
    transport: TransportKind.stdio,
    options: {
        cwd: "C:\\dev_projects\\NovelWriter\\LSP"
    }
};
```

找到第 30 行左右的 `documentSelector`，修改为：

```typescript
// 原来的代码
const documentSelector: DocumentSelector = [{ scheme: 'file', language: 'json' }];

// 修改为处理 Markdown 文件
const documentSelector: DocumentSelector = [
    { scheme: 'file', language: 'markdown' }
];
```

### 步骤 3：安装依赖

```powershell
cd C:\dev_projects\pygls\examples\json-extension\client
npm install
npm run compile
```

### 步骤 4：启动扩展

1. 在 VS Code 中打开：`C:\dev_projects\pygls\examples\json-extension`
2. 按 `F5` 启动调试
3. 会打开一个新的 VS Code 窗口（扩展开发宿主）
4. 在新窗口中打开：`C:\dev_projects\NovelWriter\LSP\test_lsp_connection.md`
5. **测试功能**：
   - 光标放在 `@Character: John Doe` 上
   - 按 `F12`（Go to Definition）
   - **应该成功跳转！**

---

## 🔍 验证步骤

在扩展开发宿主窗口中：

1. **查看日志**：
   - 按 `Ctrl+Shift+U`
   - 选择 "Output" → "NovelWriter LSP"
   - 应该看到：
     ```
     Starting NovelWriter LSP Server v0.1.0
     Document opened: file:///c:/dev_projects/NovelWriter/LSP/test_lsp_connection.md
     Parsing document...
     Updated index with symbol: character - John Doe
     ```

2. **测试所有功能**：
   - ✅ Go to Definition (`F12`)
   - ✅ Find References (`Shift+F12`)
   - ✅ Document Symbols (`Ctrl+Shift+O`)
   - ✅ Hover（鼠标悬停显示符号信息）
   - ✅ Diagnostics（Problems 面板）

---

## 📋 为什么选择这个方案？

| 方案 | 优点 | 缺点 |
|------|------|------|
| **pygls 官方示例** ⭐ | • 官方维护<br>• 完全兼容 pygls<br>• 有完整文档<br>• 稳定可靠 | • 需要修改几行代码 |
| 通用 LSP 扩展 | • 理论上配置即可 | • 配置复杂<br>• 文档不清<br>• 兼容性问题 |
| 自己写扩展 | • 完全自定义 | • 开发时间长 |

---

## 🚀 完成后

一旦测试成功，你可以：

1. **继续使用开发版本**：每次测试时按 `F5` 启动
2. **打包扩展**：创建 `.vsix` 文件安装到 VS Code
3. **发布扩展**：发布到 VS Code Marketplace

---

## ❓ 常见问题

### Q: 为什么通用扩展不工作？
**A**: 通用扩展需要精确的配置键名，不同版本可能不同。pygls 示例是专门为 pygls 设计的，100% 兼容。

### Q: 我需要学习 TypeScript 吗？
**A**: 只需要修改几行配置，不需要深入理解。这是最简单的路径。

### Q: 可以打包成独立扩展吗？
**A**: 可以！使用 `vsce package` 命令打包成 `.vsix` 文件，然后在任何 VS Code 中安装。

---

## 🎉 现在就试试！

1. 克隆 pygls 仓库
2. 修改 2 处配置
3. 运行 `npm install && npm run compile`
4. 在 VS Code 中按 `F5`

**10 分钟内你就能看到 LSP 功能工作！**
