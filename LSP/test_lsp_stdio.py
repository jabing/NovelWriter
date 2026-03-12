#!/usr/bin/env python
"""
测试 NovelWriter LSP 服务器的 stdio 通信

这个脚本模拟一个简单的 LSP 客户端，验证服务器能够正常响应。
"""

import json
import subprocess
import sys


def send_request(process, request):
    """发送 LSP 请求到服务器"""
    # LSP 使用 Content-Length 头部
    content = json.dumps(request)
    message = f"Content-Length: {len(content)}\r\n\r\n{content}"
    
    print(f"\n>>> 发送请求:\n{json.dumps(request, indent=2)}")
    process.stdin.write(message)
    process.stdin.flush()


def read_response(process):
    """读取服务器响应"""
    # 读取 Content-Length 头部
    headers = {}
    while True:
        line = process.stdout.readline().strip()
        if not line:
            break
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()
    
    # 读取响应内容
    if "Content-Length" in headers:
        length = int(headers["Content-Length"])
        content = process.stdout.read(length)
        response = json.loads(content)
        print(f"\n<<< 收到响应:\n{json.dumps(response, indent=2)}")
        return response
    return None


def test_lsp_server():
    """测试 LSP 服务器"""
    print("=" * 60)
    print("测试 NovelWriter LSP 服务器")
    print("=" * 60)
    
    # 启动 LSP 服务器
    cmd = [sys.executable, "-m", "novelwriter_lsp"]
    print(f"\n启动服务器: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        # 1. 发送 initialize 请求
        print("\n" + "=" * 60)
        print("步骤 1: 发送 initialize 请求")
        print("=" * 60)
        
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": None,
                "rootUri": "file:///c:/dev_projects/NovelWriter/LSP",
                "capabilities": {
                    "textDocument": {
                        "definition": {"dynamicRegistration": True},
                        "documentSymbol": {"dynamicRegistration": True}
                    }
                }
            }
        }
        
        send_request(process, initialize_request)
        response = read_response(process)
        
        if response and "result" in response:
            print("\n✅ 服务器初始化成功！")
            print(f"服务器信息: {response['result'].get('serverInfo', {})}")
        else:
            print("\n❌ 服务器初始化失败")
            return False
        
        # 2. 发送 initialized 通知
        print("\n" + "=" * 60)
        print("步骤 2: 发送 initialized 通知")
        print("=" * 60)
        
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        
        send_request(process, initialized_notification)
        print("\n✅ 已发送 initialized 通知")
        
        # 3. 发送 textDocument/didOpen 通知
        print("\n" + "=" * 60)
        print("步骤 3: 发送 textDocument/didOpen 通知")
        print("=" * 60)
        
        test_document = """# Test Novel

@Character: John Doe {
    age: 42,
    status: "alive"
}

John walked into the scene.
"""
        
        didopen_notification = {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {
                "textDocument": {
                    "uri": "file:///c:/dev_projects/NovelWriter/LSP/test.md",
                    "languageId": "markdown",
                    "version": 1,
                    "text": test_document
                }
            }
        }
        
        send_request(process, didopen_notification)
        print("\n✅ 已发送文档打开通知")
        
        # 4. 发送 textDocument/definition 请求
        print("\n" + "=" * 60)
        print("步骤 4: 发送 textDocument/definition 请求")
        print("=" * 60)
        
        definition_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "textDocument/definition",
            "params": {
                "textDocument": {
                    "uri": "file:///c:/dev_projects/NovelWriter/LSP/test.md"
                },
                "position": {
                    "line": 2,  # @Character: John Doe 行
                    "character": 15  # "John" 的位置
                }
            }
        }
        
        send_request(process, definition_request)
        response = read_response(process)
        
        if response and "result" in response:
            print(f"\n✅ Go to Definition 返回: {response['result']}")
        else:
            print("\n⚠️  未找到定义")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成！服务器工作正常")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 关闭服务器
        process.terminate()
        process.wait()


if __name__ == "__main__":
    success = test_lsp_server()
    sys.exit(0 if success else 1)
