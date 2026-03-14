# NovelWriter LSP 测试文档

这是一个用于测试 NovelWriter LSP 服务器功能的示例文档。

## 角色定义

@Character: John Doe {
    age: 42,
    status: "alive",
    occupation: "Private Investigator"
}

@Character: Jane Smith {
    age: 35,
    status: "alive",
    occupation: "Client"
}

@Character: The Killer {
    age: 50,
    status: "unknown",
    occupation: "Antagonist"
}

## 地点定义

@Location: The Rusty Anchor Pub {
    city: "Boston",
    description: "A dimly lit waterfront bar with old wood and stale beer smell"
}

@Location: Jane's Apartment {
    city: "Boston",
    description: "A modern apartment overlooking the harbor"
}

@Location: The Crime Scene {
    city: "Boston",
    description: "An abandoned warehouse in the industrial district"
}

## 故事开始

John Doe walked into The Rusty Anchor Pub. The air smelled of stale beer and old wood.

@Event: John Meets Client {
    chapter: 1,
    location: "The Rusty Anchor Pub",
    participants: ["John Doe", "Jane Smith"],
    description: "Jane hires John to find her missing sister"
}

Jane Smith approached John Doe's table. "I need your help," she said.

## 调查开始

The next morning, John Doe visited The Crime Scene.

@Event: Investigates Warehouse {
    chapter: 2,
    location: "The Crime Scene",
    participants: ["John Doe"],
    description: "John discovers clues about the killer"
}

He found a mysterious note.

## 关键线索

@Item: Mysterious Note {
    description: "A cryptic note left by the killer",
    owner: "The Killer"
}

@Lore: The Brotherhood {
    description: "A secret society controlling the city",
    rules: [
        "Never reveal membership",
        "Always protect the code",
        "Death for betrayal"
    ]
}

## 情节转折

@PlotPoint: The Betrayal {
    chapter: 3,
    type: "twist",
    description: "John discovers Jane is actually part of the brotherhood"
}

@Relationship: John → Jane {
    type: "suspicious",
    description: "Trust issues begin to form"
}

## 测试说明

### LSP 功能测试

1. **跳转到定义 (Go to Definition)**
   - 将光标放在第二处 `John Doe` 上
   - 按 `F12` 或右键 → "Go to Definition"
   - 应该跳转到角色定义位置

2. **查找引用 (Find References)**
   - 将光标放在 `John Doe` 上
   - 按 `Shift+F12` 或右键 → "Find All References"
   - 应该显示所有引用位置

3. **文档符号 (Document Symbols)**
   - 按 `Ctrl+Shift+O`
   - 应该显示所有符号（Character、Location、Event 等）

4. **重命名符号 (Rename Symbol)**
   - 将光标放在 `John Doe` 上
   - 按 `F2` 输入新名称
   - 所有引用应该自动更新

5. **悬停信息 (Hover)**
   - 将光标悬停在 `John Doe` 上
   - 应该显示角色属性（age、status 等）

6. **代码补全 (Completion)**
   - 在新行输入 `@`
   - 应该显示符号类型建议

7. **诊断信息 (Diagnostics)**
   - 打开 "Problems" 面板（`Ctrl+Shift+M`）
   - 查看文档诊断

### 符号类型

本示例演示了以下符号类型：

- `@Character` - 角色
- `@Location` - 地点
- `@Event` - 事件
- `@Item` - 物品
- `@Lore` - 设定
- `@PlotPoint` - 情节点
- `@Relationship` - 关系
