"""Output formatting module for Job Summary."""

import os

from actions_advisor.llm_client import AnalysisResult
from actions_advisor.log_fetcher import JobLog


def format_analysis(
    job_log: JobLog, result: AnalysisResult, estimated_cost: float | None
) -> str:
    """Format analysis as markdown.

    Args:
        job_log: Failed job metadata
        result: LLM analysis result
        estimated_cost: Estimated cost in USD (None if not available)

    Returns:
        Formatted markdown string
    """
    # Format duration
    duration_str = _format_duration(job_log.duration_seconds)

    # Format cost
    cost_str = ""
    if estimated_cost is not None:
        cost_str = f" | 💰 ~${estimated_cost:.4f}"

    # Build markdown
    markdown = f"""## 🔍 Actions Advisor

### ❌ Failed: `{job_log.job_name}` → `{job_log.step_name}`

**Exit Code:** {job_log.exit_code or "N/A"} | **Duration:** {duration_str}

---

{result.analysis}

---

<sub>📊 {result.input_tokens} input + {result.output_tokens} output tokens\
{cost_str} ({result.model_used})</sub>
"""

    return markdown


def _format_duration(seconds: int | None) -> str:
    """Format duration as human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration (e.g., "2m 34s")
    """
    if seconds is None:
        return "N/A"

    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    remaining_seconds = seconds % 60

    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"

    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m {remaining_seconds}s"


def write_job_summary(content: str) -> None:
    """Write content to GitHub Job Summary.

    Args:
        content: Markdown content to write
    """
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        # If not running in GitHub Actions, print to stdout
        print("=== Job Summary (would be written to $GITHUB_STEP_SUMMARY) ===")
        print(content)
        return

    with open(summary_file, "a") as f:
        f.write(content)
        f.write("\n\n")
