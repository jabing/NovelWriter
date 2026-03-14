# 真正的解决方案：连接 NovelWriter LSP 到 VS Code

## ❌ 问题：之前的信息有误

**VS Code Marketplace 上没有通用的 LSP 客户端扩展**，你需要 **创建自己的 VS Code 扩展**。

---

## ✅ 实际可行的 3 个方案

### 方案 A：使用 pygls 官方示例（最快，5分钟）⚡

**pygls 官方提供了完整的 VS Code 扩展示例**，可以直接修改使用！

#### 步骤 1：克隆 pygls 仓库

```bash
cd C:\dev_projects
git clone https://github.com/openlawlibrary/pygls.git
cd pygls
```

#### 步骤 2：修改示例扩展连接到你的服务器

编辑 `examples/json-extension/client/src/extension.ts`：

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

#### 步骤 3：修改文件类型关联

在同一个文件中，找到 `documentSelector`，修改为：

```typescript
const documentSelector: DocumentSelector = [
    { scheme: 'file', language: 'markdown' },  // .md 文件
    { scheme: 'file', pattern: '**/*.nwl' }     // .nwl 文件（如果你定义了）
];
```

#### 步骤 4：安装扩展依赖

```bash
cd examples/json-extension/client
npm install
```

#### 步骤 5：启动扩展

1. 在 VS Code 中打开 `examples/json-extension` 文件夹
2. 按 `F5` 启动调试
3. 会打开一个新的 VS Code 窗口（扩展开发宿主）
4. 在新窗口中打开你的 `.md` 文件
5. **LSP 功能应该工作了！**

---

### 方案 B：创建最小化扩展（推荐，专业）🛠️

**基于 Microsoft 官方模板** 创建你自己的扩展。

#### 步骤 1：使用模板

```bash
# 在 GitHub 上使用模板创建仓库
# 访问：https://github.com/microsoft/vscode-python-tools-extension-template
# 点击 "Use this template"
```

#### 步骤 2：克隆你的新仓库

```bash
cd C:\dev_projects\NovelWriter
git clone https://github.com/YOUR_USERNAME/novelwriter-vscode-extension.git
cd novelwriter-vscode-extension
```

#### 步骤 3：修改 `extension.ts`

找到 `src/extension.ts`，修改服务器启动配置：

```typescript
import * as path from 'path';
import { workspace, ExtensionContext } from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    TransportKind
} from 'vscode-languageclient/node';

let client: LanguageClient;

export function activate(context: ExtensionContext) {
    // 服务器配置
    const serverOptions: ServerOptions = {
        command: "python",
        args: ["-m", "novelwriter_lsp"],
        transport: TransportKind.stdio,
        options: {
            cwd: "C:\\dev_projects\\NovelWriter\\LSP"
        }
    };

    // 客户端选项
    const clientOptions: LanguageClientOptions = {
        documentSelector: [
            { scheme: 'file', language: 'markdown' },
            { scheme: 'file', pattern: '**/*.nwl' }
        ],
        synchronize: {
            configurationSection: 'novelwriter',
            fileEvents: workspace.createFileSystemWatcher('**/.md')
        }
    };

    // 创建客户端
    client = new LanguageClient(
        'novelwriterLsp',
        'NovelWriter LSP',
        serverOptions,
        clientOptions
    );

    // 启动客户端
    client.start();
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}
```

#### 步骤 4：修改 `package.json`

```json
{
    "name": "novelwriter-lsp-client",
    "displayName": "NovelWriter LSP Client",
    "description": "LSP client for NovelWriter",
    "version": "0.0.1",
    "engines": {
        "vscode": "^1.85.0"
    },
    "categories": ["Programming Languages"],
    "activationEvents": [
        "onLanguage:markdown"
    ],
    "main": "./out/extension.js",
    "contributes": {
        "languages": [{
            "id": "markdown",
            "extensions": [".md", ".markdown"],
            "aliases": ["Markdown", "markdown"]
        }],
        "configuration": {
            "type": "object",
            "title": "NovelWriter LSP",
            "properties": {}
        }
    },
    "scripts": {
        "vscode:prepublish": "npm run compile",
        "compile": "tsc -p ./",
        "watch": "tsc -watch -p ./"
    },
    "devDependencies": {
        "@types/node": "^20.0.0",
        "@types/vscode": "^1.85.0",
        "typescript": "^5.3.0",
        "vscode-languageclient": "^9.0.0"
    }
}
```

#### 步骤 5：安装和运行

```bash
npm install
npm run compile
```

在 VS Code 中按 `F5` 启动调试。

---

### 方案 C：使用其他编辑器（临时测试）📝

如果你只是想测试 LSP 功能，可以使用支持 LSP 的其他编辑器：

#### Neovim + nvim-lspconfig

1. **安装 Neovim**：https://neovim.io/
2. **安装 nvim-lspconfig 插件**
3. **配置 LSP 客户端**：

在 `init.vim` 或 `init.lua` 中：

```lua
local lspconfig = require('lspconfig')

lspconfig.novelwriter.setup {
    cmd = {"python", "-m", "novelwriter_lsp"},
    filetypes = {"markdown"},
    root_dir = function(fname)
        return vim.fn.getcwd()
    end,
    settings = {},
}
```

---

## 🎯 推荐方案

**根据你的需求选择**：

| 方案 | 时间 | 复杂度 | 推荐场景 |
|------|------|--------|----------|
| **A: pygls 示例** | 5分钟 | ⭐ | 快速测试，立即验证功能 |
| **B: 创建扩展** | 30分钟 | ⭐⭐⭐ | 长期使用，专业开发 |
| **C: 其他编辑器** | 10分钟 | ⭐⭐ | 临时测试，已有其他编辑器 |

---

## 🚀 最快方案：使用 pygls 示例（详细步骤）

### 完整操作步骤

#### 1. 获取 pygls 示例代码

```powershell
# 在 PowerShell 中
cd C:\dev_projects
git clone https://github.com/openlawlibrary/pygls.git
cd pygls\examples\json-extension\client
```

#### 2. 安装依赖

```powershell
npm install
```

#### 3. 修改配置

用 VS Code 打开 `C:\dev_projects\pygls\examples\json-extension`，编辑 `client\src\extension.ts`：

```typescript
// 找到这行（约第 15-20 行）
const serverOptions: ServerOptions = {
    command: "python",
    args: ["-m", "pygls", "examples/servers/json_server.py"],
    transport: TransportKind.stdio
};

// 修改为：
const serverOptions: ServerOptions = {
    command: "python",
    args: ["-m", "novelwriter_lsp"],
    transport: TransportKind.stdio,
    options: {
        cwd: "C:\\dev_projects\\NovelWriter\\LSP"
    }
};

// 找到 documentSelector（约第 30 行），修改为：
const documentSelector: DocumentSelector = [
    { scheme: 'file', language: 'markdown' }
];
```

#### 4. 重新编译

```powershell
npm run compile
```

#### 5. 启动扩展

1. 在 VS Code 中打开 `C:\dev_projects\pygls\examples\json-extension`
2. 按 `F5`（或点击 "Run and Debug"）
3. 会打开一个新的 VS Code 窗口
4. 在新窗口中打开 `C:\dev_projects\NovelWriter\LSP\test_lsp_connection.md`
5. **测试功能**：
   - 光标放在 `@Character: John Doe` 上
   - 按 `F12` → 应该跳转到定义
   - 按 `Ctrl+Shift+U` → 查看 Output 面板
   - 应该看到 LSP 日志

---

## 🔍 验证连接

在扩展开发宿主窗口中：

1. **打开 Output 面板**：`Ctrl+Shift+U`
2. **选择下拉菜单**："NovelWriter LSP" 或 "LSP"
3. **查看日志**，应该看到类似：
   ```
   Starting NovelWriter LSP Server v0.1.0
   Document opened: file:///c:/dev_projects/NovelWriter/LSP/test_lsp_connection.md
   Parsing document: file:///c:/dev_projects/NovelWriter/LSP/test_lsp_connection.md
   Updated index with symbol: character - John Doe
   Parsed 1 symbols from file:///c:/dev_projects/NovelWriter/LSP/test_lsp_connection.md
   ```

4. **测试功能**：
   - ✅ Go to Definition (`F12`)
   - ✅ Find References (`Shift+F12`)
   - ✅ Document Symbols (`Ctrl+Shift+O`)
   - ✅ Hover（鼠标悬停）
   - ✅ Diagnostics（Problems 面板）

---

## 📚 参考资源

- **pygls 官方文档**：https://pygls.readthedocs.io/
- **pygls GitHub**：https://github.com/openlawlibrary/pygls
- **Microsoft LSP 指南**：https://code.visualstudio.com/api/language-extensions/language-server-extension-guide
- **VS Code Python 工具模板**：https://github.com/microsoft/vscode-python-tools-extension-template

---

## ❓ 常见问题

### Q: 为什么不能直接安装一个扩展？

**A**: LSP 客户端需要知道：
- 如何启动你的服务器（命令、参数）
- 处理哪些文件类型
- 服务器在哪里

每个 LSP 服务器都不同，所以没有通用的客户端。

### Q: 我必须学习 TypeScript 吗？

**A**: 对于快速测试（方案 A），只需要修改几行配置。对于专业扩展（方案 B），是的，需要一些 TypeScript。

### Q: 可以用纯 Python 写扩展吗？

**A**: 不行，VS Code 扩展必须用 JavaScript/TypeScript。但服务器端可以用任何语言（你已经用 Python 写了）。

---

## 🎉 下一步

1. **选择方案**：推荐从方案 A（pygls 示例）开始
2. **按照步骤操作**：上面的详细步骤已经包含所有命令
3. **测试功能**：在扩展开发宿主中验证所有 LSP 功能
4. **如果满意**：考虑创建自己的扩展（方案 B）

需要帮助吗？随时问我！
