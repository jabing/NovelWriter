"""WebSocket workflow progress broadcast tests.

Tests the WebSocket endpoint for real-time workflow progress updates.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.novel_agent.api.websocket import (
    ConnectionManager,
    broadcast_progress,
    broadcast_workflow_complete,
    broadcast_workflow_error,
    broadcast_workflow_start,
    broadcast_workflow_step_complete,
    extract_project_id_from_query,
    subscribe_to_project_from_query,
)


class TestConnectionManager:
    """Tests for ConnectionManager class."""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        """Create a fresh ConnectionManager instance."""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self, manager: ConnectionManager) -> None:
        """Test basic connect and disconnect functionality."""
        websocket = MagicMock(spec=["send_text", "accept", "receive_text"])
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.receive_text = AsyncMock(side_effect=asyncio.CancelledError())

        await manager.connect(websocket)
        assert manager.get_connection_count() == 1

        manager.disconnect(websocket)
        assert manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_connect_project_subscription(self, manager: ConnectionManager) -> None:
        """Test project-specific subscription adds to global connections too."""
        websocket = MagicMock(spec=["send_text", "accept", "receive_text"])
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.receive_text = AsyncMock(side_effect=asyncio.CancelledError())

        await manager.connect_project(websocket, "project_123")
        assert manager.get_connection_count() == 1
        assert manager.get_project_connection_count("project_123") == 1
        # Project subscription should also be a global connection
        assert websocket in manager._active_connections

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self, manager: ConnectionManager) -> None:
        """Test broadcasting to all connected clients."""
        websocket1 = MagicMock(spec=["send_text", "accept", "receive_text"])
        websocket1.accept = AsyncMock()
        websocket1.send_text = AsyncMock()
        websocket1.receive_text = AsyncMock(side_effect=asyncio.CancelledError())

        websocket2 = MagicMock(spec=["send_text", "accept", "receive_text"])
        websocket2.accept = AsyncMock()
        websocket2.send_text = AsyncMock()
        websocket2.receive_text = AsyncMock(side_effect=asyncio.CancelledError())

        await manager.connect(websocket1)
        await manager.connect(websocket2)

        message = {"type": "test", "data": {"value": 42}}
        await manager.broadcast(message)

        websocket1.send_text.assert_called_once()
        websocket2.send_text.assert_called_once()

        call_args1 = json.loads(websocket1.send_text.call_args[0][0])
        assert call_args1 == message

    @pytest.mark.asyncio
    async def test_broadcast_to_project(self, manager: ConnectionManager) -> None:
        """Test broadcasting to a specific project."""
        websocket1 = MagicMock(spec=["send_text", "accept", "receive_text"])
        websocket1.accept = AsyncMock()
        websocket1.send_text = AsyncMock()
        websocket1.receive_text = AsyncMock(side_effect=asyncio.CancelledError())

        websocket2 = MagicMock(spec=["send_text", "accept", "receive_text"])
        websocket2.accept = AsyncMock()
        websocket2.send_text = AsyncMock()
        websocket2.receive_text = AsyncMock(side_effect=asyncio.CancelledError())

        await manager.connect_project(websocket1, "project_123")
        await manager.connect(websocket2)

        message = {"type": "workflow_progress", "data": {"progress": 50}}
        await manager.broadcast_project("project_123", message)

        websocket1.send_text.assert_called_once()
        websocket2.send_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_global_and_project(self, manager: ConnectionManager) -> None:
        """Test broadcasting to both global and project subscribers."""
        websocket1 = MagicMock(spec=["send_text", "accept", "receive_text"])
        websocket1.accept = AsyncMock()
        websocket1.send_text = AsyncMock()
        websocket1.receive_text = AsyncMock(side_effect=asyncio.CancelledError())

        websocket2 = MagicMock(spec=["send_text", "accept", "receive_text"])
        websocket2.accept = AsyncMock()
        websocket2.send_text = AsyncMock()
        websocket2.receive_text = AsyncMock(side_effect=asyncio.CancelledError())

        websocket3 = MagicMock(spec=["send_text", "accept", "receive_text"])
        websocket3.accept = AsyncMock()
        websocket3.send_text = AsyncMock()
        websocket3.receive_text = AsyncMock(side_effect=asyncio.CancelledError())

        await manager.connect(websocket1)
        await manager.connect_project(websocket2, "project_123")
        await manager.connect_project(websocket3, "project_456")

        message = {"type": "test"}
        await manager.broadcast_global_and_project("project_123", message)

        # websocket1: global only -> 1 message
        # websocket2: global + project_123 -> 2 messages (global + project_123)
        # websocket3: global only (not project_123) -> 1 message
        assert websocket1.send_text.call_count == 1
        assert websocket2.send_text.call_count == 2
        assert websocket3.send_text.call_count == 1

    @pytest.mark.asyncio
    async def test_disconnect_project(self) -> None:
        """Test disconnecting from a specific project."""
        manager = ConnectionManager()
        websocket = MagicMock(spec=["send_text", "accept", "receive_text"])
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.receive_text = AsyncMock(side_effect=asyncio.CancelledError())

        await manager.connect_project(websocket, "project_123")
        await manager.connect_project(websocket, "project_456")

        assert manager.get_connection_count() == 1
        assert manager.get_project_connection_count("project_123") == 1
        assert manager.get_project_connection_count("project_456") == 1

        manager.disconnect_project(websocket, "project_123")

        assert manager.get_connection_count() == 1
        assert manager.get_project_connection_count("project_123") == 0
        assert manager.get_project_connection_count("project_456") == 1


class TestWorkflowProgressBroadcasting:
    """Tests for workflow progress broadcasting functions."""

    @pytest.mark.asyncio
    async def test_broadcast_progress_message(self) -> None:
        """Test broadcast_progress creates correct message format."""
        from src.novel_agent.api.websocket import manager as ws_manager

        original_broadcast = ws_manager.broadcast_global_and_project
        ws_manager.broadcast_global_and_project = AsyncMock()

        try:
            await broadcast_progress(
                task_id="test_task_123",
                progress=50,
                current_step="Generating chapter 5",
                project_id="project_456"
            )

            ws_manager.broadcast_global_and_project.assert_awaited_once()
            call_args = ws_manager.broadcast_global_and_project.call_args

            assert call_args[0][0] == "project_456"
            message = call_args[0][1]

            assert message["type"] == "workflow_progress"
            assert message["data"]["task_id"] == "test_task_123"
            assert message["data"]["progress"] == 50
            assert message["data"]["current_step"] == "Generating chapter 5"
        finally:
            ws_manager.broadcast_global_and_project = original_broadcast

    @pytest.mark.asyncio
    async def test_broadcast_progress_with_additional_data(self) -> None:
        """Test broadcast_progress includes additional data."""
        from src.novel_agent.api.websocket import manager as ws_manager

        original_broadcast = ws_manager.broadcast_global_and_project
        ws_manager.broadcast_global_and_project = AsyncMock()

        try:
            additional = {"some_key": "some_value", "count": 100}
            await broadcast_progress(
                task_id="test_task",
                progress=25,
                current_step="Starting",
                additional_data=additional
            )

            ws_manager.broadcast_global_and_project.assert_awaited_once()
            call_args = ws_manager.broadcast_global_and_project.call_args
            message = call_args[0][1]

            assert message["data"]["some_key"] == "some_value"
            assert message["data"]["count"] == 100
        finally:
            ws_manager.broadcast_global_and_project = original_broadcast

    @pytest.mark.asyncio
    async def test_broadcast_workflow_start(self) -> None:
        """Test broadcast_workflow_start creates correct message."""
        from src.novel_agent.api.websocket import manager as ws_manager

        original_broadcast = ws_manager.broadcast_global_and_project
        ws_manager.broadcast_global_and_project = AsyncMock()

        try:
            await broadcast_workflow_start(
                task_id="task_123",
                project_id="project_456",
                workflow_type="chapter_generation",
                total_steps=10
            )

            ws_manager.broadcast_global_and_project.assert_awaited_once()
            call_args = ws_manager.broadcast_global_and_project.call_args
            message = call_args[0][1]

            assert message["type"] == "workflow_progress"
            assert message["data"]["progress"] == 0
            assert message["data"]["current_step"] == "Starting chapter_generation"
            assert message["data"]["workflow_type"] == "chapter_generation"
            assert message["data"]["total_steps"] == 10
        finally:
            ws_manager.broadcast_global_and_project = original_broadcast

    @pytest.mark.asyncio
    async def test_broadcast_workflow_complete(self) -> None:
        """Test broadcast_workflow_complete creates correct message."""
        from src.novel_agent.api.websocket import manager as ws_manager

        original_broadcast = ws_manager.broadcast_global_and_project
        ws_manager.broadcast_global_and_project = AsyncMock()

        try:
            results = {"chapters_generated": 5, "words_written": 15000}
            await broadcast_workflow_complete(
                task_id="task_123",
                project_id="project_456",
                results=results
            )

            ws_manager.broadcast_global_and_project.assert_awaited_once()
            call_args = ws_manager.broadcast_global_and_project.call_args
            message = call_args[0][1]

            assert message["data"]["progress"] == 100
            assert message["data"]["current_step"] == "Workflow completed"
            assert message["data"]["completed"] is True
            assert message["data"]["results"] == results
        finally:
            ws_manager.broadcast_global_and_project = original_broadcast

    @pytest.mark.asyncio
    async def test_broadcast_workflow_error_with_step(self) -> None:
        """Test broadcast_workflow_error uses provided step when available."""
        from src.novel_agent.api.websocket import manager as ws_manager

        original_broadcast = ws_manager.broadcast_global_and_project
        ws_manager.broadcast_global_and_project = AsyncMock()

        try:
            await broadcast_workflow_error(
                task_id="task_123",
                project_id="project_456",
                error_message="LLM timeout",
                step="Generating outline"
            )

            ws_manager.broadcast_global_and_project.assert_awaited_once()
            call_args = ws_manager.broadcast_global_and_project.call_args
            message = call_args[0][1]

            assert message["data"]["progress"] == 0
            assert message["data"]["current_step"] == "Generating outline"
            assert message["data"]["error"] is True
            assert message["data"]["error_message"] == "LLM timeout"
        finally:
            ws_manager.broadcast_global_and_project = original_broadcast

    @pytest.mark.asyncio
    async def test_broadcast_workflow_error_without_step(self) -> None:
        """Test broadcast_workflow_error uses default step when no step provided."""
        from src.novel_agent.api.websocket import manager as ws_manager

        original_broadcast = ws_manager.broadcast_global_and_project
        ws_manager.broadcast_global_and_project = AsyncMock()

        try:
            await broadcast_workflow_error(
                task_id="task_123",
                project_id="project_456",
                error_message="Unknown error",
                step=None
            )

            ws_manager.broadcast_global_and_project.assert_awaited_once()
            call_args = ws_manager.broadcast_global_and_project.call_args
            message = call_args[0][1]

            assert message["data"]["current_step"] == "Error occurred"
        finally:
            ws_manager.broadcast_global_and_project = original_broadcast

    @pytest.mark.asyncio
    async def test_broadcast_workflow_step_complete(self) -> None:
        """Test broadcast_workflow_step_complete creates correct message."""
        from src.novel_agent.api.websocket import manager as ws_manager

        original_broadcast = ws_manager.broadcast_global_and_project
        ws_manager.broadcast_global_and_project = AsyncMock()

        try:
            await broadcast_workflow_step_complete(
                task_id="task_123",
                project_id="project_456",
                step_name="Character Selection",
                progress=30
            )

            ws_manager.broadcast_global_and_project.assert_awaited_once()
            call_args = ws_manager.broadcast_global_and_project.call_args
            message = call_args[0][1]

            assert message["data"]["progress"] == 30
            assert message["data"]["current_step"] == "Completed: Character Selection"
        finally:
            ws_manager.broadcast_global_and_project = original_broadcast


class TestQueryHelpers:
    """Tests for query parameter extraction functions."""

    def test_extract_project_id_from_query(self) -> None:
        """Test extracting project_id from query string."""
        assert extract_project_id_from_query("project_id=abc123") == "abc123"
        assert extract_project_id_from_query("project_id=test&other=value") == "test"
        assert extract_project_id_from_query("other=value&project_id=xyz") == "xyz"

    def test_extract_project_id_empty_query(self) -> None:
        """Test with empty query string."""
        assert extract_project_id_from_query("") is None
        assert extract_project_id_from_query(None) is None

    def test_extract_project_id_no_project_param(self) -> None:
        """Test with query string that has no project_id."""
        assert extract_project_id_from_query("other=value") is None
        assert extract_project_id_from_query("page=1&limit=10") is None
