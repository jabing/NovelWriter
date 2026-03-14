"""Quick test to verify LSP server startup and response."""

import json
import subprocess
import sys
import time

def test_server_startup():
    """Test that server starts and responds to initialize request."""
    print("Starting LSP server...")

    proc = subprocess.Popen(
        [sys.executable, "-m", "novelwriter_lsp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        time.sleep(0.1)

        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": None,
                "rootUri": None,
                "capabilities": {}
            }
        }

        print(f"Sending: {json.dumps(init_request)}")
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        response_line = proc.stdout.readline()
        print(f"Received: {response_line}")

        if response_line:
            response = json.loads(response_line)
            if response.get("id") == 1 and "result" in response:
                print("✅ Server initialization successful")
                print(f"Capabilities: {list(response['result'].get('capabilities', {}).keys())}")
                return True
            else:
                print("❌ Invalid response")
                return False
        else:
            print("❌ No response from server")
            return False

    finally:
        try:
            proc.stdin.write('{"jsonrpc":"2.0","id":2,"method":"shutdown","params":{}}' + "\n")
            proc.stdin.flush()
            time.sleep(0.1)
            proc.stdin.write('{"jsonrpc":"2.0","method":"exit","params":{}}' + "\n")
            proc.stdin.flush()
        except:
            pass

        proc.terminate()
        try:
            proc.wait(timeout=2)
        except:
            proc.kill()
            proc.wait()

if __name__ == "__main__":
    success = test_server_startup()
    sys.exit(0 if success else 1)
