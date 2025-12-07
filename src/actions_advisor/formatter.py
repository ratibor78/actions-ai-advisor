"""Output formatting module for Job Summary."""

import os
import re

from actions_advisor.file_parser import AffectedFile, format_github_link
from actions_advisor.llm_client import AnalysisResult
from actions_advisor.log_fetcher import JobLog


def format_analysis(
    job_log: JobLog,
    result: AnalysisResult,
    estimated_cost: float | None,
    affected_files: list[AffectedFile] | None = None,
    repo_owner: str = "",
    repo_name: str = "",
    commit_sha: str = "",
) -> str:
    """Format analysis as markdown with modern, visually rich formatting.

    Args:
        job_log: Failed job metadata
        result: LLM analysis result
        estimated_cost: Estimated cost in USD (None if not available)
        affected_files: List of files mentioned in errors (optional)
        repo_owner: GitHub repository owner for file links
        repo_name: GitHub repository name for file links
        commit_sha: Git commit SHA for file links

    Returns:
        Formatted markdown string with GitHub callouts, tables, and rich formatting
    """
    # Format duration
    duration_str = _format_duration(job_log.duration_seconds)

    # Format cost
    cost_str = "N/A"
    if estimated_cost is not None:
        cost_str = f"~${estimated_cost:.4f}"

    # Build failure header with key metrics (clean format)
    exit_code = job_log.exit_code or "N/A"
    failure_header = (
        f"**Failed:** `{job_log.job_name}` → `{job_log.step_name}`\n\n"
        f"**Exit Code:** `{exit_code}` | **Duration:** {duration_str}"
    )

    # Build token and cost info (compact single line)
    token_info = (
        f"**Model:** `{result.model_used}` | "
        f"**Tokens:** {result.input_tokens:,} in + {result.output_tokens:,} out | "
        f"**Cost:** {cost_str}"
    )

    # Build affected files section (if available)
    affected_files_section = ""
    if affected_files and repo_owner and repo_name and commit_sha:
        # Limit to top 10 files to keep summary concise
        files_to_show = affected_files[:10]
        file_links = [
            f"- {format_github_link(f, repo_owner, repo_name, commit_sha)}"
            for f in files_to_show
        ]

        if file_links:
            # Clean formatting without extra blank lines
            affected_files_section = (
                "\n### Affected Files\n\n"
                f"{chr(10).join(file_links)}\n\n"
            )

    # Apply red styling to Error Context section
    styled_analysis = _style_error_context(result.analysis)

    # Build markdown output
    markdown = f"""# Actions AI Advisor

{failure_header}
{affected_files_section}
---

{styled_analysis}

---

### Analysis Details

{token_info}

<sub>Powered by Actions AI Advisor | [Report Issues](https://github.com/ratibor78/actions-advisor/issues)</sub>
"""

    return markdown


def _style_error_context(analysis: str) -> str:
    """Apply red styling to Error Context section.

    Args:
        analysis: LLM-generated analysis markdown

    Returns:
        Analysis with red-styled error context
    """
    # Pattern to match "## Error Context" heading and its content
    # Captures content until next ## heading or end of string
    pattern = r"(## Error Context\s*\n)(.*?)(?=\n##|\Z)"

    def style_error(match: re.Match[str]) -> str:
        heading = match.group(1)  # Keep heading as-is (black)
        content = match.group(2)  # Error content to style red
        # Wrap content in red span (GitHub's error red color)
        return f'{heading}<span style="color: #d73a49;">\n\n{content}</span>'

    # Apply styling if Error Context section exists
    styled = re.sub(pattern, style_error, analysis, flags=re.DOTALL)
    return styled


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
