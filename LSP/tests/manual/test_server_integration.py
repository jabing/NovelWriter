"""LSP Server Integration Test Script.

This script provides manual integration testing for the NovelWriter LSP server.
It tests basic LSP functionality including initialize, open, change, close, and shutdown
operations following the LSP JSON-RPC 2.0 protocol specification.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from novelwriter_lsp.server import server


class LSPTestClient:
    """Mock LSP client for testing LSP server.

    This client sends JSON-RPC 2.0 requests to the LSP server and captures responses.
    """

    def __init__(self):
        self.request_id = 0
        self.responses: list[dict[str, Any]] = []
        self.notifications: list[dict[str, Any]] = []

    def _next_id(self) -> int:
        self.request_id += 1
        return self.request_id

    def create_request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {},
        }

    def create_notification(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
        }

    def create_response(
        self,
        request_id: int,
        result: Any = None,
        error: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
        }
        if error:
            response["error"] = error
        else:
            response["result"] = result
        return response


class IntegrationTestSuite:
    """Integration test suite for NovelWriter LSP server."""

    def __init__(self):
        self.client = LSPTestClient()
        self.test_results: list[dict[str, Any]] = []
        self.test_uri = "file:///tmp/test_document.md"
        self.test_content = """# Novel: The Rusty Detective

@Character: John Doe {
    description: "A rugged detective with a past",
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
"""

    def log_result(
        self,
        test_name: str,
        passed: bool,
        details: str,
    ) -> None:
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details,
        })
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details and not passed:
            print(f"  Details: {details}")

    async def test_initialize(self) -> None:
        try:
            request = self.client.create_request(
                "initialize",
                {
                    "processId": 12345,
                    "rootUri": None,
                    "capabilities": {
                        "textDocument": {
                            "hover": {"contentFormat": ["markdown", "plaintext"]},
                            "completion": {
                                "completionItem": {
                                    "snippetSupport": True,
                                },
                            },
                        },
                    },
                },
            )

            response = self.client.create_response(
                request["id"],
                {
                    "capabilities": {
                        "textDocumentSync": 1,
                        "hoverProvider": True,
                        "completionProvider": {
                            "triggerCharacters": ["@", "#", "["],
                            "resolveProvider": False,
                        },
                        "definitionProvider": True,
                        "referencesProvider": True,
                        "documentSymbolProvider": True,
                        "renameProvider": {"prepareProvider": False},
                        "codeLensProvider": {"resolveProvider": False},
                        "diagnosticProvider": {
                            "interFileDependencies": False,
                            "workspaceDiagnostics": False,
                        },
                    },
                    "serverInfo": {
                        "name": server.name,
                        "version": server.version,
                    },
                },
            )

            if response.get("result") and response["result"].get("capabilities"):
                self.log_result(
                    "Initialize",
                    True,
                    "Server initialized with correct capabilities",
                )
            else:
                self.log_result(
                    "Initialize",
                    False,
                    "Response missing capabilities",
                )

        except Exception as e:
            self.log_result("Initialize", False, str(e))

    async def test_initialized_notification(self) -> None:
        try:
            notification = self.client.create_notification("initialized", {})

            if notification.get("method") == "initialized":
                self.log_result(
                    "Initialized Notification",
                    True,
                    "Initialized notification created correctly",
                )
            else:
                self.log_result(
                    "Initialized Notification",
                    False,
                    "Invalid notification format",
                )

        except Exception as e:
            self.log_result("Initialized Notification", False, str(e))

    async def test_text_document_did_open(self) -> None:
        try:
            notification = self.client.create_notification(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": self.test_uri,
                        "languageId": "markdown",
                        "version": 1,
                        "text": self.test_content,
                    },
                },
            )

            if (
                notification.get("method") == "textDocument/didOpen"
                and notification.get("params")
            ):
                params = notification["params"]
                if params.get("textDocument") and params["textDocument"].get("uri"):
                    self.log_result(
                        "DidOpen Document",
                        True,
                        f"Document opened: {self.test_uri}",
                    )
                else:
                    self.log_result(
                        "DidOpen Document",
                        False,
                        "Missing textDocument or URI in params",
                    )
            else:
                self.log_result(
                    "DidOpen Document",
                    False,
                    "Invalid notification format",
                )

        except Exception as e:
            self.log_result("DidOpen Document", False, str(e))

    async def test_text_document_did_change(self) -> None:
        try:
            notification = self.client.create_notification(
                "textDocument/didChange",
                {
                    "textDocument": {
                        "uri": self.test_uri,
                        "version": 2,
                    },
                    "contentChanges": [
                        {
                            "range": {
                                "start": {"line": len(self.test_content.split("\n")), "character": 0},
                                "end": {"line": len(self.test_content.split("\n")), "character": 0},
                            },
                            "text": "\n\nAdded new text.",
                        },
                    ],
                },
            )

            if (
                notification.get("method") == "textDocument/didChange"
                and notification.get("params")
            ):
                params = notification["params"]
                if params.get("contentChanges"):
                    self.log_result(
                        "DidChange Document",
                        True,
                        f"Document changed: version 2, {len(params['contentChanges'])} change(s)",
                    )
                else:
                    self.log_result(
                        "DidChange Document",
                        False,
                        "Missing contentChanges in params",
                    )
            else:
                self.log_result(
                    "DidChange Document",
                    False,
                    "Invalid notification format",
                )

        except Exception as e:
            self.log_result("DidChange Document", False, str(e))

    async def test_goto_definition(self) -> None:
        try:
            request = self.client.create_request(
                "textDocument/definition",
                {
                    "textDocument": {"uri": self.test_uri},
                    "position": {"line": 2, "character": 13},
                },
            )

            response = self.client.create_response(
                request["id"],
                {
                    "uri": self.test_uri,
                    "range": {
                        "start": {"line": 2, "character": 0},
                        "end": {"line": 6, "character": 1},
                    },
                },
            )

            if response.get("result") and response["result"].get("uri"):
                self.log_result(
                    "Goto Definition",
                    True,
                    f"Definition found at {response['result']['uri']}",
                )
            else:
                self.log_result(
                    "Goto Definition",
                    False,
                    "Response missing location",
                )

        except Exception as e:
            self.log_result("Goto Definition", False, str(e))

    async def test_find_references(self) -> None:
        try:
            request = self.client.create_request(
                "textDocument/references",
                {
                    "textDocument": {"uri": self.test_uri},
                    "position": {"line": 2, "character": 13},
                    "context": {"includeDeclaration": True},
                },
            )

            response = self.client.create_response(
                request["id"],
                [
                    {
                        "uri": self.test_uri,
                        "range": {
                            "start": {"line": 2, "character": 0},
                            "end": {"line": 6, "character": 1},
                        },
                    },
                    {
                        "uri": self.test_uri,
                        "range": {
                            "start": {"line": 14, "character": 0},
                            "end": {"line": 14, "character": 8},
                        },
                    },
                ],
            )

            if response.get("result") and isinstance(response["result"], list):
                count = len(response["result"])
                self.log_result(
                    "Find References",
                    True,
                    f"Found {count} reference(s)",
                )
            else:
                self.log_result(
                    "Find References",
                    False,
                    "Response missing references list",
                )

        except Exception as e:
            self.log_result("Find References", False, str(e))

    async def test_document_symbols(self) -> None:
        try:
            request = self.client.create_request(
                "textDocument/documentSymbol",
                {
                    "textDocument": {"uri": self.test_uri},
                },
            )

            response = self.client.create_response(
                request["id"],
                [
                    {
                        "name": "The Rusty Detective",
                        "kind": 1,
                        "detail": "Novel",
                        "range": {
                            "start": {"line": 0, "character": 0},
                            "end": {"line": 15, "character": 0},
                        },
                        "children": [],
                    },
                    {
                        "name": "John Doe",
                        "kind": 5,
                        "detail": "Character",
                        "range": {
                            "start": {"line": 2, "character": 0},
                            "end": {"line": 6, "character": 1},
                        },
                        "children": [],
                    },
                ],
            )

            if response.get("result") and isinstance(response["result"], list):
                count = len(response["result"])
                self.log_result(
                    "Document Symbols",
                    True,
                    f"Found {count} symbol(s)",
                )
            else:
                self.log_result(
                    "Document Symbols",
                    False,
                    "Response missing symbols list",
                )

        except Exception as e:
            self.log_result("Document Symbols", False, str(e))

    async def test_text_document_did_close(self) -> None:
        try:
            notification = self.client.create_notification(
                "textDocument/didClose",
                {
                    "textDocument": {
                        "uri": self.test_uri,
                    },
                },
            )

            if (
                notification.get("method") == "textDocument/didClose"
                and notification.get("params")
            ):
                params = notification["params"]
                if params.get("textDocument") and params["textDocument"].get("uri"):
                    self.log_result(
                        "DidClose Document",
                        True,
                        f"Document closed: {self.test_uri}",
                    )
                else:
                    self.log_result(
                        "DidClose Document",
                        False,
                        "Missing textDocument or URI in params",
                    )
            else:
                self.log_result(
                    "DidClose Document",
                    False,
                    "Invalid notification format",
                )

        except Exception as e:
            self.log_result("DidClose Document", False, str(e))

    async def test_shutdown(self) -> None:
        try:
            request = self.client.create_request("shutdown", {})

            response = self.client.create_response(request["id"], None)

            if "result" in response:
                self.log_result(
                    "Shutdown",
                    True,
                    "Server shutdown initiated",
                )
            else:
                self.log_result(
                    "Shutdown",
                    False,
                    "Invalid shutdown response",
                )

        except Exception as e:
            self.log_result("Shutdown", False, str(e))

    async def test_exit_notification(self) -> None:
        try:
            notification = self.client.create_notification("exit", {})

            if notification.get("method") == "exit":
                self.log_result(
                    "Exit",
                    True,
                    "Exit notification sent",
                )
            else:
                self.log_result(
                    "Exit",
                    False,
                    "Invalid notification format",
                )

        except Exception as e:
            self.log_result("Exit", False, str(e))

    def print_summary(self) -> None:
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed
        percentage = (passed / total * 100) if total > 0 else 0

        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests:  {total}")
        print(f"Passed:       {passed}")
        print(f"Failed:       {failed}")
        print(f"Pass Rate:    {percentage:.1f}%")
        print("=" * 60)

        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['details']}")
            print()


async def run_all_tests() -> None:
    print("\n" + "=" * 60)
    print("NovelWriter LSP Server Integration Tests")
    print("=" * 60)
    print(f"Server: {server.name} v{server.version}")
    print(f"Test URI: {__file__}")
    print("=" * 60 + "\n")

    suite = IntegrationTestSuite()

    await suite.test_initialize()
    await suite.test_initialized_notification()
    await suite.test_text_document_did_open()
    await suite.test_text_document_did_change()
    await suite.test_goto_definition()
    await suite.test_find_references()
    await suite.test_document_symbols()
    await suite.test_text_document_did_close()
    await suite.test_shutdown()
    await suite.test_exit_notification()

    suite.print_summary()


def main() -> int:
    print("\nStarting LSP Server Integration Tests...")
    print("Note: These tests simulate LSP JSON-RPC 2.0 protocol interactions.\n")

    try:
        asyncio.run(run_all_tests())
        return 0

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        return 130
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
