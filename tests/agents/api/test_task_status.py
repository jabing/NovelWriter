"""Tests for tasks router."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.novel_agent.api.routers.tasks import get_task_store, _task_store
from src.novel_agent.api.schemas.workflow import WorkflowStatus


# Clear task store before each test
@pytest.fixture(autouse=True)
def clear_task_store():
    _task_store._tasks.clear()


class TestListTasks:
    """Tests for GET /api/tasks endpoint."""

    def test_list_tasks_empty(self, client_without_auth: TestClient):
        """Test listing tasks when none exist."""
        response = client_without_auth.get("/api/tasks/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["tasks"] == []

    def test_list_tasks_with_data(self, client_without_auth: TestClient):
        """Test listing tasks when tasks exist."""
        # Create a task
        task_id = get_task_store().create_task(
            task_id="test-task-1",
            status=WorkflowStatus.RUNNING,
            progress=50,
            current_step="Processing"
        )
        
        response = client_without_auth.get("/api/tasks/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["task_id"] == task_id
        assert data["tasks"][0]["status"] == WorkflowStatus.RUNNING.value
        assert data["tasks"][0]["progress"] == 50
        assert data["tasks"][0]["current_step"] == "Processing"
        assert data["running_count"] == 1

    def test_list_tasks_status_counts(self, client_without_auth: TestClient):
        """Test that status counts are accurate."""
        get_task_store().create_task(task_id="task1", status=WorkflowStatus.QUEUED)
        get_task_store().create_task(task_id="task2", status=WorkflowStatus.RUNNING)
        get_task_store().create_task(task_id="task3", status=WorkflowStatus.COMPLETED)
        get_task_store().create_task(task_id="task4", status=WorkflowStatus.FAILED)
        
        response = client_without_auth.get("/api/tasks/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 4
        assert data["queued_count"] == 1
        assert data["running_count"] == 1
        assert data["completed_count"] == 1
        assert data["failed_count"] == 1


class TestGetTaskStatus:
    """Tests for GET /api/tasks/{task_id}/status endpoint."""

    def test_task_status_success(self, client_without_auth: TestClient):
        """Test getting a task status successfully."""
        task_id = get_task_store().create_task(
            task_id="test-task",
            status=WorkflowStatus.RUNNING,
            progress=75,
            current_step="Generating chapter 5"
        )
        
        response = client_without_auth.get(f"/api/tasks/{task_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == WorkflowStatus.RUNNING.value
        assert data["progress"] == 75
        assert data["current_step"] == "Generating chapter 5"
        assert data["errors"] == []

    def test_task_not_found(self, client_without_auth: TestClient):
        """Test getting a non-existent task returns 404."""
        response = client_without_auth.get("/api/tasks/nonexistent-id/status")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_task_with_errors(self, client_without_auth: TestClient):
        """Test getting a task with errors."""
        task_id = get_task_store().create_task(
            task_id="error-task",
            status=WorkflowStatus.FAILED,
            progress=30,
            errors=["Connection timeout", "Retry limit exceeded"]
        )
        
        response = client_without_auth.get(f"/api/tasks/{task_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == WorkflowStatus.FAILED.value
        assert len(data["errors"]) == 2
        assert "Connection timeout" in data["errors"]


class TestUpdateTask:
    """Tests for PATCH /api/tasks/{task_id} endpoint."""

    def test_update_task_status(self, client_without_auth: TestClient):
        """Test updating task status."""
        task_id = get_task_store().create_task(
            task_id="update-task",
            status=WorkflowStatus.RUNNING,
            progress=25
        )
        
        response = client_without_auth.patch(
            f"/api/tasks/{task_id}",
            json={"status": WorkflowStatus.COMPLETED.value, "progress": 100}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == WorkflowStatus.COMPLETED.value
        assert data["progress"] == 100

    def test_update_task_not_found(self, client_without_auth: TestClient):
        """Test updating a non-existent task returns 404."""
        response = client_without_auth.patch(
            "/api/tasks/nonexistent-id",
            json={"status": WorkflowStatus.RUNNING.value}
        )
        
        assert response.status_code == 404
