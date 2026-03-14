"""Tests for manual_review_api module."""

import pytest
from fastapi.testclient import TestClient

from src.novel.manual_review_api import (
    ReviewIssue,
    ReviewStatus,
    ReviewStore,
    app,
    review_store,
)


@pytest.fixture
def client() -> TestClient:
    """Create a test client with a fresh store."""
    review_store.clear()
    return TestClient(app)


@pytest.fixture
def sample_issue() -> ReviewIssue:
    """Create a sample issue for testing."""
    return review_store.add_issue(
        chapter_number=5,
        description="Character location inconsistency",
        severity=4,
        context={"character": "Hero", "expected_location": "Castle"},
    )


class TestReviewStore:
    """Test ReviewStore operations."""

    def test_add_issue(self) -> None:
        """Test adding an issue to the store."""
        store = ReviewStore()
        issue = store.add_issue(
            chapter_number=1,
            description="Test issue",
            severity=3,
        )
        assert issue.issue_id is not None
        assert issue.chapter_number == 1
        assert issue.description == "Test issue"
        assert issue.severity == 3
        assert issue.status == ReviewStatus.PENDING

    def test_get_issue(self) -> None:
        """Test retrieving an issue by ID."""
        store = ReviewStore()
        added = store.add_issue(chapter_number=1, description="Test", severity=2)
        retrieved = store.get_issue(added.issue_id)
        assert retrieved is not None
        assert retrieved.issue_id == added.issue_id

    def test_get_issue_not_found(self) -> None:
        """Test retrieving a non-existent issue."""
        store = ReviewStore()
        result = store.get_issue("nonexistent")
        assert result is None

    def test_get_pending_issues(self) -> None:
        """Test getting all pending issues."""
        store = ReviewStore()
        store.add_issue(chapter_number=1, description="Issue 1", severity=3)
        store.add_issue(chapter_number=2, description="Issue 2", severity=4)
        pending = store.get_pending_issues()
        assert len(pending) == 2

    def test_update_issue(self) -> None:
        """Test updating an issue status."""
        store = ReviewStore()
        issue = store.add_issue(chapter_number=1, description="Test", severity=3)
        updated = store.update_issue(issue.issue_id, ReviewStatus.APPROVED, "Fixed")
        assert updated is not None
        assert updated.status == ReviewStatus.APPROVED
        assert updated.reason == "Fixed"
        assert updated.resolved_at is not None

    def test_get_stats(self) -> None:
        """Test getting statistics."""
        store = ReviewStore()
        store.add_issue(chapter_number=1, description="Issue 1", severity=3)
        issue2 = store.add_issue(chapter_number=2, description="Issue 2", severity=4)
        store.update_issue(issue2.issue_id, ReviewStatus.APPROVED)
        stats = store.get_stats()
        assert stats["pending_count"] == 1
        assert stats["approved_count"] == 1
        assert stats["rejected_count"] == 0
        assert stats["total_count"] == 2


class TestGetPendingIssues:
    """Test GET /issues/pending endpoint."""

    def test_empty_list(self, client: TestClient) -> None:
        """Test getting pending issues when none exist."""
        response = client.get("/issues/pending")
        assert response.status_code == 200
        assert response.json() == []

    def test_with_issues(self, client: TestClient, sample_issue: ReviewIssue) -> None:
        """Test getting pending issues when some exist."""
        response = client.get("/issues/pending")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["chapter_number"] == 5
        assert data[0]["description"] == "Character location inconsistency"
        assert data[0]["severity"] == 4


class TestGetIssue:
    """Test GET /issues/{issue_id} endpoint."""

    def test_get_existing_issue(self, client: TestClient, sample_issue: ReviewIssue) -> None:
        """Test getting an existing issue."""
        response = client.get(f"/issues/{sample_issue.issue_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["issue_id"] == sample_issue.issue_id
        assert data["chapter_number"] == 5
        assert data["context"]["character"] == "Hero"

    def test_get_nonexistent_issue(self, client: TestClient) -> None:
        """Test getting a non-existent issue."""
        response = client.get("/issues/nonexistent")
        assert response.status_code == 404


class TestSubmitDecision:
    """Test POST /issues/{issue_id}/decision endpoint."""

    def test_approve_issue(self, client: TestClient, sample_issue: ReviewIssue) -> None:
        """Test approving an issue."""
        response = client.post(
            f"/issues/{sample_issue.issue_id}/decision",
            json={"decision": "approve", "reason": "Fix looks good"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["reason"] == "Fix looks good"
        assert data["resolved_at"] is not None

    def test_reject_issue(self, client: TestClient, sample_issue: ReviewIssue) -> None:
        """Test rejecting an issue."""
        response = client.post(
            f"/issues/{sample_issue.issue_id}/decision",
            json={"decision": "reject", "reason": "Needs more work"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        assert data["reason"] == "Needs more work"

    def test_invalid_decision(self, client: TestClient, sample_issue: ReviewIssue) -> None:
        """Test submitting an invalid decision."""
        response = client.post(
            f"/issues/{sample_issue.issue_id}/decision",
            json={"decision": "invalid", "reason": "Test"},
        )
        assert response.status_code == 400

    def test_nonexistent_issue(self, client: TestClient) -> None:
        """Test submitting decision for non-existent issue."""
        response = client.post(
            "/issues/nonexistent/decision",
            json={"decision": "approve", "reason": "Test"},
        )
        assert response.status_code == 404


class TestGetStats:
    """Test GET /stats endpoint."""

    def test_empty_stats(self, client: TestClient) -> None:
        """Test stats when no issues exist."""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["pending_count"] == 0
        assert data["approved_count"] == 0
        assert data["rejected_count"] == 0

    def test_with_issues(self, client: TestClient) -> None:
        """Test stats with various issue states."""
        issue1 = review_store.add_issue(1, "Issue 1", 3)
        issue2 = review_store.add_issue(2, "Issue 2", 4)
        review_store.add_issue(3, "Issue 3", 2)
        review_store.update_issue(issue1.issue_id, ReviewStatus.APPROVED)
        review_store.update_issue(issue2.issue_id, ReviewStatus.REJECTED)

        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["pending_count"] == 1
        assert data["approved_count"] == 1
        assert data["rejected_count"] == 1
        assert data["total_count"] == 3


class TestAddIssueEndpoint:
    """Test POST /issues/add endpoint."""

    def test_add_issue(self, client: TestClient) -> None:
        """Test adding an issue via API."""
        response = client.post(
            "/issues/add",
            params={
                "chapter_number": 10,
                "description": "New test issue",
                "severity": 4,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chapter_number"] == 10
        assert data["description"] == "New test issue"
        assert data["severity"] == 4
        assert data["status"] == "pending"


class TestClearIssues:
    """Test DELETE /issues/clear endpoint."""

    def test_clear_issues(self, client: TestClient, sample_issue: ReviewIssue) -> None:
        """Test clearing all issues."""
        response = client.delete("/issues/clear")
        assert response.status_code == 200
        assert response.json()["message"] == "All issues cleared"
        stats = client.get("/stats").json()
        assert stats["total_count"] == 0
