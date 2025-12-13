"""Tests for log fetcher module."""

import httpx
import pytest

from actions_ai_advisor.log_fetcher import LogFetcher


@pytest.mark.asyncio
async def test_fetch_failed_jobs(respx_mock):
    """Test fetching failed jobs."""
    # Mock the jobs API response
    jobs_response = {
        "jobs": [
            {
                "id": 123,
                "name": "build",
                "conclusion": "failure",
                "started_at": "2024-01-01T10:00:00Z",
                "completed_at": "2024-01-01T10:05:00Z",
                "steps": [
                    {"name": "Checkout", "conclusion": "success"},
                    {"name": "Run tests", "conclusion": "failure", "number": 2},
                ],
            },
            {
                "id": 124,
                "name": "lint",
                "conclusion": "success",
                "started_at": "2024-01-01T10:00:00Z",
                "completed_at": "2024-01-01T10:02:00Z",
                "steps": [],
            },
        ]
    }

    # Mock the logs API response
    logs_content = "Error: Test failed\nAssertion error on line 42"

    respx_mock.get(
        "https://api.github.com/repos/owner/repo/actions/runs/999/jobs"
    ).mock(return_value=httpx.Response(200, json=jobs_response))

    respx_mock.get(
        "https://api.github.com/repos/owner/repo/actions/jobs/123/logs"
    ).mock(return_value=httpx.Response(200, text=logs_content))

    fetcher = LogFetcher(github_token="test-token", repo="owner/repo", run_id="999")
    failed_jobs = await fetcher.fetch_failed_jobs()

    assert len(failed_jobs) == 1
    assert failed_jobs[0].job_name == "build"
    assert failed_jobs[0].step_name == "Run tests"
    assert failed_jobs[0].conclusion == "failure"
    assert failed_jobs[0].raw_logs == logs_content
    assert failed_jobs[0].duration_seconds == 300  # 5 minutes
    assert failed_jobs[0].exit_code == 1


@pytest.mark.asyncio
async def test_fetch_cancelled_jobs(respx_mock):
    """Test fetching cancelled jobs."""
    jobs_response = {
        "jobs": [
            {
                "id": 125,
                "name": "deploy",
                "conclusion": "cancelled",
                "started_at": "2024-01-01T10:00:00Z",
                "completed_at": "2024-01-01T10:01:00Z",
                "steps": [
                    {"name": "Deploy", "conclusion": "cancelled", "number": 1},
                ],
            }
        ]
    }

    logs_content = "Job cancelled by user"

    respx_mock.get(
        "https://api.github.com/repos/owner/repo/actions/runs/999/jobs"
    ).mock(return_value=httpx.Response(200, json=jobs_response))

    respx_mock.get(
        "https://api.github.com/repos/owner/repo/actions/jobs/125/logs"
    ).mock(return_value=httpx.Response(200, text=logs_content))

    fetcher = LogFetcher(github_token="test-token", repo="owner/repo", run_id="999")
    failed_jobs = await fetcher.fetch_failed_jobs()

    assert len(failed_jobs) == 1
    assert failed_jobs[0].conclusion == "cancelled"


@pytest.mark.asyncio
async def test_no_failed_jobs(respx_mock):
    """Test when there are no failed jobs."""
    jobs_response = {
        "jobs": [
            {
                "id": 126,
                "name": "build",
                "conclusion": "success",
                "started_at": "2024-01-01T10:00:00Z",
                "completed_at": "2024-01-01T10:05:00Z",
                "steps": [],
            }
        ]
    }

    respx_mock.get(
        "https://api.github.com/repos/owner/repo/actions/runs/999/jobs"
    ).mock(return_value=httpx.Response(200, json=jobs_response))

    fetcher = LogFetcher(github_token="test-token", repo="owner/repo", run_id="999")
    failed_jobs = await fetcher.fetch_failed_jobs()

    assert len(failed_jobs) == 0
