# Quick Start: VS Code LSP Client Setup for NovelWriter LSP

This guide explains how to quickly test the NovelWriter LSP server in VS Code using a generic LSP client extension, without writing a custom VS Code extension.

## Why Do I Need a Client?

The NovelWriter LSP server is a **server** program that provides language features (autocomplete, navigation, validation). VS Code is an **editor** that doesn't know how to talk to our custom LSP server by default.

**Analogy**: The LSP server is like a restaurant kitchen (does all the work), VS Code is like the dining room (where you interact), and the LSP client is like the waiter (translates orders between the two).

Without a client extension, VS Code doesn't know:
- How to start the server process
- How to send LSP requests
- What file types to handle (`.nwl`, `.md` files with NovelWriter syntax)
- How to display results (diagnostics, completions, etc.)

---

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.14+** installed
   ```bash
   python --version
   ```

2. **NovelWriter LSP server** installed and tested
   ```bash
   cd C:\dev_projects\NovelWriter\LSP
   pip install -r requirements.txt
   python -m novelwriter_lsp --version
   ```

3. **VS Code** installed (latest version)

---

## Step 1: Install a Generic LSP Client Extension

We'll use the **"vscode-languageserver-node"** client as it's well-maintained and supports custom LSP servers.

### Option A: Using the VS Code Extension Marketplace (Recommended)

1. Open VS Code
2. Press `Ctrl+Shift+X` (or `Cmd+Shift+X` on Mac) to open the Extensions panel
3. Search for: **"vscode-languageserver-node"**
4. Click **Install**

**Screenshot Description**: The Extensions panel showing the search box with "vscode-languageserver-node" entered, and the extension card with an "Install" button.

### Option B: Alternative LSP Client Extensions

If vscode-languageserver-node doesn't work for you, try these alternatives:

| Extension Name | Extension ID | Notes |
|----------------|--------------|-------|
| **LSP Client** | `gabrielbb.vscode-lsp` | Lightweight, supports stdio |
| **LSP Support** | `zxh404.vscode-proto3` | Good for protocol debugging |
| **vscode-languageserver** | `vscode.vscode-languageserver` | Official Microsoft extension |

**Screenshot Description**: A table showing alternative extensions with their IDs and brief notes about each one.

---

## Step 2: Configure the LSP Client

The client needs to know:
1. Which command to start the server
2. What file types to handle
3. How to communicate (stdio vs TCP)

### 2.1 Create or Update VS Code Settings

1. In VS Code, open your project folder: `File` → `Open Folder` → Select `C:\dev_projects\NovelWriter\LSP`
2. Open settings: `Ctrl+,` (or `Cmd+,` on Mac)
3. Search for **"lsp"** in the search box
4. Click **"Edit in settings.json"**

### 2.2 Add Client Configuration

Add the following configuration to your `.vscode/settings.json` file (create it if it doesn't exist):

```json
{
  "lsp.enable": true,
  "lsp.server-configurations": {
    "novelwriter": {
      "command": "python",
      "args": [
        "-m",
        "novelwriter_lsp"
      ],
      "transport": "stdio",
      "filetypes": [
        "markdown",
        "nwl",
        "novelwriter"
      ],
      "settings": {
        "novelwriter": {
          "enableDiagnostics": true,
          "enableCompletion": true,
          "enableHover": true
        }
      }
    }
  },
  "lsp.filetypes": {
    "markdown": "novelwriter"
  },
  "files.associations": {
    "*.nwl": "markdown",
    "*.novelwriter": "markdown"
  }
}
```

**Explanation of Configuration**:

| Setting | Purpose | Value |
|---------|---------|-------|
| `command` | Program to start the server | `python` |
| `args` | Arguments for the server program | `["-m", "novelwriter_lsp"]` runs our server as a module |
| `transport` | How client and server communicate | `stdio` (standard input/output) |
| `filetypes` | Which file types the server handles | `["markdown", "nwl", "novelwriter"]` |
| `files.associations` | Map custom extensions to VS Code languages | Maps `.nwl` files to Markdown |

**Screenshot Description**: A code editor window showing the VS Code settings.json file with the LSP configuration code highlighted, with a sidebar showing the file tree on the left.

---

## Step 3: Create a Test File

Create a new file in your project to test the LSP connection:

1. Right-click in the file explorer → `New File`
2. Name it: `test_novel.nwl`
3. Add the following content:

```markdown
# Novel: The Rusty Detective

@Character: John Doe {
    age: 42,
    status: "alive",
    occupation: "Private Investigator"
}

@Location: The Rusty Anchor Pub {
    city: "Boston",
    description: "A dimly lit waterfront bar"
}

## Chapter 1

John Doe walked into The Rusty Anchor Pub. The air smelled of stale beer and old wood.

@Event: John Meets Client {
    chapter: 1,
    location: "The Rusty Anchor Pub",
    participants: ["John Doe", "Jane Smith"],
    description: "Jane hires John to find her missing sister"
}
```

**Screenshot Description**: The VS Code editor window showing the test_novel.nwl file with the NovelWriter syntax highlighted, and the file tree in the sidebar showing the new file.

---

## Step 4: Test the Connection

### 4.1 Verify Server Started

1. Open the VS Code **Output** panel: `Ctrl+Shift+U` (or `Cmd+Shift+U` on Mac)
2. Select **"LSP Server"** from the dropdown menu
3. Look for startup messages like:
   ```
   Starting NovelWriter LSP Server v0.1.0
   Server started successfully
   ```

**Expected Output**:
```
2024-03-07 15:30:00 - novelwriter_lsp.server - INFO - Starting NovelWriter LSP Server v0.1.0
2024-03-07 15:30:00 - novelwriter_lsp.server - INFO - Server started successfully
```

**Screenshot Description**: The VS Code Output panel showing LSP server startup messages with timestamps and log levels.

### 4.2 Test LSP Features

#### Test 1: Go to Definition (F12)

1. Place your cursor on `John Doe` in the Event section (line 28)
2. Press `F12` or right-click → **"Go to Definition"**
3. **Expected**: Cursor jumps to the Character definition (line 4)

#### Test 2: Hover Information

1. Hover your mouse over `The Rusty Anchor Pub` (line 23)
2. **Expected**: A popup shows location details:
   ```
   Location: The Rusty Anchor Pub
   City: Boston
   Description: A dimly lit waterfront bar
   ```

#### Test 3: Find References (Shift+F12)

1. Place cursor on `John Doe` in the Character definition (line 4)
2. Press `Shift+F12` or right-click → **"Find All References"**
3. **Expected**: Shows 2 references:
   - Character definition (line 4)
   - Event participants (line 28)

#### Test 4: Document Symbols (Ctrl+Shift+O)

1. Press `Ctrl+Shift+O` (or `Cmd+Shift+O` on Mac)
2. **Expected**: Shows a symbol tree:
   ```
   📄 test_novel.nwl
   ├─ 📍 Location: The Rusty Anchor Pub
   ├─ 👤 Character: John Doe
   ├─ 🎬 Event: John Meets Client
   └─ 📖 Outline: Chapter 1
   ```

#### Test 5: Diagnostics

1. Intentionally create an error by adding a duplicate Character:
   ```markdown
   @Character: John Doe {
       age: 99,
       status: "duplicate"
   }
   ```
2. Open the **Problems** panel: `Ctrl+Shift+M`
3. **Expected**: Shows error:
   ```
   ERROR: Duplicate symbol definition 'John Doe' at line 34
   ```

**Screenshot Description**: A composite image showing all five LSP features being tested in VS Code: Go to Definition, Hover popup, Find References sidebar, Document Symbols outline, and Problems panel with diagnostics.

---

## Step 5: Troubleshooting

### Problem: Server doesn't start

**Symptoms**:
- No output in "LSP Server" panel
- No language features work

**Solutions**:

1. **Check Python is in PATH**:
   ```bash
   python --version
   ```
   If not found, add Python to your system PATH.

2. **Verify server can run manually**:
   ```bash
   cd C:\dev_projects\NovelWriter\LSP
   python -m novelwriter_lsp
   ```
   You should see startup messages.

3. **Check VS Code extension logs**:
   - Open **View** → **Output**
   - Select **"Extension Host"** from dropdown
   - Look for error messages from the LSP client extension

4. **Verify settings.json syntax**:
   - Check for missing commas in JSON
   - Validate JSON using an online tool like [jsonlint.com](https://jsonlint.com/)

### Problem: LSP features work for .md files but not .nwl files

**Symptoms**:
- Go to definition works in README.md
- Doesn't work in test_novel.nwl

**Solutions**:

1. **Check file associations** in settings.json:
   ```json
   "files.associations": {
     "*.nwl": "markdown",
     "*.novelwriter": "markdown"
   }
   ```

2. **Reload VS Code**:
   - Press `Ctrl+Shift+P` → **"Reload Window"**

3. **Check language mode**:
   - Click the language indicator in the bottom-right corner
   - Should show **"Markdown"** or **"NovelWriter"**

### Problem: Diagnostics don't appear

**Symptoms**:
- Server is running
- Intentional errors don't show in Problems panel

**Solutions**:

1. **Wait a moment** - LSP servers sometimes take a few seconds to process files

2. **Check if diagnostics are enabled**:
   ```json
   "lsp.server-configurations": {
     "novelwriter": {
       "settings": {
         "novelwriter": {
           "enableDiagnostics": true
         }
       }
     }
   }
   ```

3. **Save the file** - Diagnostics often update on save

### Problem: Go to Definition jumps to wrong location

**Symptoms**:
- F12 jumps to a different symbol than expected
- Or doesn't jump at all

**Solutions**:

1. **Verify symbol name matches exactly** (case-sensitive)
   - `@Character: John Doe` ≠ `@Character: john doe`

2. **Check for multiple definitions** with the same name

3. **Restart the LSP server**:
   - Press `Ctrl+Shift+P` → **"LSP: Restart Server"**

### Problem: Slow performance

**Symptoms**:
- Autocomplete takes several seconds to appear
- Editor lags when typing

**Solutions**:

1. **Disable unused features** in settings:
   ```json
   "novelwriter": {
     "enableCompletion": false,  // Disable if not needed
     "enableDiagnostics": true,
     "enableHover": true
   }
   ```

2. **Use a faster Python interpreter**:
   - Switch from standard CPython to PyPy for better performance

3. **Check server logs for bottlenecks**:
   - Look for slow operations in the LSP Server output panel

---

## Advanced Configuration

### Custom Command Line Arguments

If you want to pass additional arguments to the server:

```json
"lsp.server-configurations": {
  "novelwriter": {
    "command": "python",
    "args": [
      "-m",
      "novelwriter_lsp",
      "--debug"
    ],
    "transport": "stdio",
    "filetypes": ["markdown"]
  }
}
```

### Using TCP Transport (Advanced)

For debugging or remote servers, you can use TCP instead of stdio:

```json
"lsp.server-configurations": {
  "novelwriter": {
    "command": "python",
    "args": [
      "-m",
      "novelwriter_lsp",
      "--tcp",
      "--port", "9000"
    ],
    "transport": "tcp",
    "host": "localhost",
    "port": 9000,
    "filetypes": ["markdown"]
  }
}
```

**Note**: Our server currently only supports stdio. This is for future reference.

---

## Next Steps

Once the LSP client is working:

1. **Create your first novel**: Start a new `.nwl` file with your story
2. **Explore all features**: Try autocomplete, rename, codeLens
3. **Check the architecture**: Read [LSP_ARCHITECTURE_REDESIGN.md](LSP_ARCHITECTURE_REDESIGN.md) for details
4. **Develop your own extension**: If you need more control, build a custom VS Code extension

---

## Additional Resources

- [LSP Protocol Specification](https://microsoft.github.io/language-server-protocol/) - Official LSP documentation
- [pygls Documentation](https://github.com/openlawlibrary/pygls) - Python LSP framework we use
- [VS Code Extension API](https://code.visualstudio.com/api) - For building custom extensions
- [Main README.md](README.md) - Project overview and features
- [VS Code Setup Guide](VS_CODE_SETUP.md) - Detailed VS Code configuration

---

## FAQ

**Q: Can I use this with other editors (Sublime, Vim, etc.)?**

A: Yes! Any editor with LSP support can connect to our server. You'll need to configure the LSP client in your editor with the same command: `python -m novelwriter_lsp`.

**Q: Do I need to keep the server running?**

A: No, the LSP client automatically starts and manages the server. It will launch the server when needed and stop it when you close VS Code.

**Q: Can I run multiple LSP servers?**

A: Yes, VS Code supports multiple LSP clients. You can have our NovelWriter LSP alongside Python LSP, TypeScript LSP, etc.

**Q: Why use a generic client instead of building a custom extension?**

A: Generic clients are great for quick testing. For production use, a custom extension gives you more control over UI, commands, and integration with VS Code features.

---

## Success Checklist

Before moving on, verify:

- ✅ VS Code LSP client extension installed
- ✅ settings.json configured with server command
- ✅ Test file created (test_novel.nwl)
- ✅ Server shows startup messages in Output panel
- ✅ Go to Definition works (F12)
- ✅ Hover information shows correctly
- ✅ Find References displays all occurrences
- ✅ Document Symbols outline appears (Ctrl+Shift+O)
- ✅ Diagnostics show errors in Problems panel

If all boxes are checked, congratulations! You've successfully connected VS Code to the NovelWriter LSP server. 🎉

---

**Need help?** Check the [VS Code Setup Guide](VS_CODE_SETUP.md) for more detailed configuration options, or open an issue on the project repository.
