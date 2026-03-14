"""FastAPI web interface for manual review of issues that couldn't be auto-fixed.

This module provides a simple REST API for reviewing and resolving issues
that were escalated from the AutoFixer for manual review.

Endpoints:
    GET  /issues/pending         - List pending issues for manual review
    GET  /issues/{issue_id}      - Get issue details
    POST /issues/{issue_id}/decision - Approve/reject fix
    GET  /stats                  - Get review statistics
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ReviewStatus(str, Enum):
    """Status of a review issue."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ReviewIssue:
    """Represents an issue requiring manual review.

    Attributes:
        issue_id: Unique identifier for the issue
        chapter_number: Chapter where the issue was found
        description: Human-readable description of the issue
        severity: Severity level (1-5, with 5 being most severe)
        status: Current review status
        created_at: When the issue was created
        resolved_at: When the issue was resolved (if applicable)
        reason: Reason for approval/rejection
        context: Additional context about the issue
    """

    issue_id: str
    chapter_number: int
    description: str
    severity: int
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: datetime | None = None
    reason: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON response."""
        return {
            "issue_id": self.issue_id,
            "chapter_number": self.chapter_number,
            "description": self.description,
            "severity": self.severity,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "reason": self.reason,
            "context": self.context,
        }


class DecisionRequest(BaseModel):
    """Request body for submitting a review decision."""

    decision: str  # "approve" or "reject"
    reason: str = ""


class ReviewStore:
    """In-memory storage for review issues.

    This provides a simple storage mechanism without requiring database persistence.
    Issues can be added, retrieved, updated, and queried.
    """

    def __init__(self) -> None:
        """Initialize the review store."""
        self._issues: dict[str, ReviewIssue] = {}

    def add_issue(
        self,
        chapter_number: int,
        description: str,
        severity: int,
        context: dict[str, Any] | None = None,
    ) -> ReviewIssue:
        """Add a new issue to the store.

        Args:
            chapter_number: Chapter where issue was found
            description: Issue description
            severity: Severity level (1-5)
            context: Additional context

        Returns:
            The created ReviewIssue
        """
        issue_id = str(uuid4())[:8]
        issue = ReviewIssue(
            issue_id=issue_id,
            chapter_number=chapter_number,
            description=description,
            severity=severity,
            context=context or {},
        )
        self._issues[issue_id] = issue
        logger.info(f"Added issue {issue_id} for chapter {chapter_number}")
        return issue

    def get_issue(self, issue_id: str) -> ReviewIssue | None:
        """Get an issue by ID.

        Args:
            issue_id: The issue identifier

        Returns:
            ReviewIssue or None if not found
        """
        return self._issues.get(issue_id)

    def get_pending_issues(self) -> list[ReviewIssue]:
        """Get all pending issues.

        Returns:
            List of issues with PENDING status
        """
        return [i for i in self._issues.values() if i.status == ReviewStatus.PENDING]

    def update_issue(
        self,
        issue_id: str,
        status: ReviewStatus,
        reason: str = "",
    ) -> ReviewIssue | None:
        """Update an issue's status.

        Args:
            issue_id: The issue identifier
            status: New status
            reason: Reason for the decision

        Returns:
            Updated ReviewIssue or None if not found
        """
        issue = self._issues.get(issue_id)
        if issue:
            issue.status = status
            issue.reason = reason
            issue.resolved_at = datetime.now()
            logger.info(f"Updated issue {issue_id} to {status.value}")
        return issue

    def get_stats(self) -> dict[str, int]:
        """Get review statistics.

        Returns:
            Dictionary with counts by status
        """
        pending = sum(1 for i in self._issues.values() if i.status == ReviewStatus.PENDING)
        approved = sum(1 for i in self._issues.values() if i.status == ReviewStatus.APPROVED)
        rejected = sum(1 for i in self._issues.values() if i.status == ReviewStatus.REJECTED)

        return {
            "pending_count": pending,
            "approved_count": approved,
            "rejected_count": rejected,
            "total_count": len(self._issues),
        }

    def clear(self) -> None:
        """Clear all issues from the store."""
        self._issues.clear()
        logger.info("Cleared all issues from store")


# Global store instance
review_store = ReviewStore()

# FastAPI app
app = FastAPI(
    title="Manual Review API",
    description="API for reviewing issues that couldn't be auto-fixed",
    version="1.0.0",
)


@app.get("/issues/pending")
async def get_pending_issues() -> list[dict[str, Any]]:
    """List pending issues for manual review.

    Returns:
        List of pending issues with chapter, description, and severity.
    """
    issues = review_store.get_pending_issues()
    return [
        {
            "issue_id": i.issue_id,
            "chapter_number": i.chapter_number,
            "description": i.description,
            "severity": i.severity,
            "created_at": i.created_at.isoformat(),
        }
        for i in issues
    ]


@app.get("/issues/{issue_id}")
async def get_issue(issue_id: str) -> dict[str, Any]:
    """Get issue details.

    Args:
        issue_id: The issue identifier

    Returns:
        Full issue details with context

    Raises:
        HTTPException: 404 if issue not found
    """
    issue = review_store.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return issue.to_dict()


@app.post("/issues/{issue_id}/decision")
async def submit_decision(issue_id: str, request: DecisionRequest) -> dict[str, Any]:
    """Submit a review decision for an issue.

    Args:
        issue_id: The issue identifier
        request: Decision request with "approve" or "reject" and optional reason

    Returns:
        Updated issue status

    Raises:
        HTTPException: 400 if invalid decision, 404 if issue not found
    """
    if request.decision not in ("approve", "reject"):
        raise HTTPException(
            status_code=400,
            detail="Decision must be 'approve' or 'reject'",
        )

    status = ReviewStatus.APPROVED if request.decision == "approve" else ReviewStatus.REJECTED
    issue = review_store.update_issue(issue_id, status, request.reason)

    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")

    return {
        "issue_id": issue.issue_id,
        "status": issue.status.value,
        "reason": issue.reason,
        "resolved_at": issue.resolved_at.isoformat() if issue.resolved_at else None,
    }


@app.get("/stats")
async def get_stats() -> dict[str, int]:
    """Get review statistics.

    Returns:
        Dictionary with pending_count, approved_count, rejected_count
    """
    return review_store.get_stats()


@app.post("/issues/add")
async def add_issue(
    chapter_number: int,
    description: str,
    severity: int = 3,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Add a new issue to the review queue.

    This endpoint is for testing/development purposes.

    Args:
        chapter_number: Chapter where issue was found
        description: Issue description
        severity: Severity level (1-5)
        context: Additional context

    Returns:
        The created issue
    """
    issue = review_store.add_issue(chapter_number, description, severity, context)
    return issue.to_dict()


@app.delete("/issues/clear")
async def clear_issues() -> dict[str, str]:
    """Clear all issues from the store.

    This endpoint is for testing/development purposes.

    Returns:
        Confirmation message
    """
    review_store.clear()
    return {"message": "All issues cleared"}
