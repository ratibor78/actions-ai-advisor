"""Module for fetching failed job logs from GitHub API."""

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class JobLog:
    """Represents a failed job with its logs."""

    job_name: str
    step_name: str
    conclusion: str
    raw_logs: str
    exit_code: int | None = None
    duration_seconds: int | None = None


class LogFetcher:
    """Fetches failed job logs from GitHub API."""

    def __init__(self, github_token: str, repo: str, run_id: str) -> None:
        """Initialize log fetcher.

        Args:
            github_token: GitHub token for API authentication
            repo: Repository in format 'owner/repo'
            run_id: GitHub Actions run ID
        """
        self.github_token = github_token
        self.repo = repo
        self.run_id = run_id
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "actions-ai-advisor",
        }

    async def fetch_failed_jobs(self) -> list[JobLog]:
        """Fetch all failed jobs and their logs for the run.

        Handles pagination to support workflows with >30 jobs (e.g., matrix builds).

        Returns:
            List of JobLog objects for failed jobs
        """
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # Fetch all jobs across all pages (GitHub paginates at 30 per page by default)
            all_jobs = await self._fetch_all_jobs(client)

            failed_jobs: list[JobLog] = []
            for job in all_jobs:
                conclusion = job.get("conclusion")
                if conclusion in ("failure", "cancelled"):
                    # Extract job metadata
                    job_id = job["id"]
                    job_name = job["name"]
                    started_at = job.get("started_at")
                    completed_at = job.get("completed_at")

                    # Calculate duration
                    duration_seconds = None
                    if started_at and completed_at:
                        from datetime import datetime

                        start = datetime.fromisoformat(
                            started_at.replace("Z", "+00:00")
                        )
                        end = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                        duration_seconds = int((end - start).total_seconds())

                    # Find failed step
                    failed_step_name = "Unknown Step"
                    exit_code = None
                    for step in job.get("steps", []):
                        if step.get("conclusion") in ("failure", "cancelled"):
                            failed_step_name = step.get("name", "Unknown Step")
                            # Exit code might not always be available
                            if "number" in step:
                                exit_code = 1  # Default to 1 for failed steps
                            break

                    # Fetch logs for this job
                    raw_logs = await self._fetch_job_logs(client, job_id)

                    failed_jobs.append(
                        JobLog(
                            job_name=job_name,
                            step_name=failed_step_name,
                            conclusion=conclusion,
                            raw_logs=raw_logs,
                            exit_code=exit_code,
                            duration_seconds=duration_seconds,
                        )
                    )

            return failed_jobs

    async def _fetch_all_jobs(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Fetch all jobs for the run, handling pagination.

        GitHub API paginates at 30 jobs per page by default. This method
        fetches all pages to ensure we don't miss failures in large matrix builds.

        Args:
            client: HTTP client to use

        Returns:
            List of all job objects from GitHub API
        """
        all_jobs = []
        page = 1
        per_page = 100  # Request max per page to minimize API calls

        while True:
            jobs_url = (
                f"{self.base_url}/repos/{self.repo}/actions/runs/{self.run_id}/jobs"
                f"?page={page}&per_page={per_page}"
            )
            response = await client.get(jobs_url, headers=self.headers)
            response.raise_for_status()
            jobs_data = response.json()

            jobs = jobs_data.get("jobs", [])
            if not jobs:
                # No more jobs, we've reached the end
                break

            all_jobs.extend(jobs)

            # Check if there are more pages
            total_count = jobs_data.get("total_count", 0)
            if len(all_jobs) >= total_count:
                # We've fetched all jobs
                break

            page += 1

        return all_jobs

    async def _fetch_job_logs(self, client: httpx.AsyncClient, job_id: int) -> str:
        """Fetch logs for a specific job.

        Args:
            client: HTTP client to use
            job_id: GitHub job ID

        Returns:
            Raw log content as string
        """
        logs_url = f"{self.base_url}/repos/{self.repo}/actions/jobs/{job_id}/logs"
        response = await client.get(logs_url, headers=self.headers)
        response.raise_for_status()
        return response.text
