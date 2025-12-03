"""Parse file paths and line numbers from error logs."""

import re
from dataclasses import dataclass


@dataclass
class AffectedFile:
    """Represents a file mentioned in error logs."""

    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    description: str | None = None

    def __hash__(self) -> int:
        """Make hashable for deduplication."""
        return hash((self.file_path, self.line_start, self.line_end))

    def __eq__(self, other: object) -> bool:
        """Compare for deduplication."""
        if not isinstance(other, AffectedFile):
            return False
        return (
            self.file_path == other.file_path
            and self.line_start == other.line_start
            and self.line_end == other.line_end
        )


# Common error patterns across languages (covers ~90% of cases)
FILE_PATTERNS = [
    # Python traceback: File "/path/to/file.py", line 123
    re.compile(r'File "(?P<file>[^"]+\.(?:py|pyx))", line (?P<line>\d+)'),
    # Generic: file.py:123 or file.py:123:45
    re.compile(r"(?P<file>[\w./\-]+\.(?:py|js|ts|tsx|jsx|go|rs|rb|java|cpp|c|h)):(?P<line>\d+)(?::\d+)?"),
    # Node.js stack: at /path/to/file.js:123:45
    re.compile(r"at (?P<file>[\w./\-]+\.(?:js|ts|tsx|jsx)):(?P<line>\d+):\d+"),
    # Docker COPY: COPY file.txt /app/
    re.compile(r"COPY (?P<file>[\w./\-]+\.\w+)"),
    # Webpack: Module not found: Error: Can't resolve './src'
    re.compile(r"Can't resolve ['\"](?P<file>[\w./\-]+)['\"]"),
    # Generic file mention: checking src/main.py
    re.compile(r"(?:checking|in|file|from|import)\s+(?P<file>[\w./\-]+\.(?:py|js|ts|go|rs|rb|java))"),
]


def parse_affected_files(log_content: str) -> list[AffectedFile]:
    """Extract file paths and line numbers from error logs.

    Args:
        log_content: Raw or preprocessed log content

    Returns:
        List of unique affected files with line numbers
    """
    affected_files: set[AffectedFile] = set()

    for pattern in FILE_PATTERNS:
        for match in pattern.finditer(log_content):
            file_path = match.group("file")
            line_num = None

            # Try to extract line number if present
            try:
                line_str = match.group("line")
                line_num = int(line_str) if line_str else None
            except (IndexError, ValueError):
                pass

            # Skip common false positives
            if _is_valid_file_path(file_path):
                affected_files.add(
                    AffectedFile(
                        file_path=file_path,
                        line_start=line_num,
                    )
                )

    # Sort by file path for consistent output
    return sorted(affected_files, key=lambda f: (f.file_path, f.line_start or 0))


def _is_valid_file_path(path: str) -> bool:
    """Filter out false positives.

    Args:
        path: Potential file path

    Returns:
        True if path looks like a real project file
    """
    # Skip system/library paths
    if any(
        skip in path
        for skip in [
            "/usr/",
            "/opt/",
            "/lib/",
            "/node_modules/",
            "site-packages/",
            ".venv/",
            "venv/",
        ]
    ):
        return False

    # Must have a reasonable length
    if len(path) < 3 or len(path) > 200:
        return False

    # Should start with typical project paths or be relative
    valid_starts = ("src/", "tests/", "test/", "lib/", "app/", "./", "../", "pkg/")
    if path.startswith(valid_starts):
        return True

    # Or be a simple filename in root
    if "/" not in path and "." in path:
        return True

    return False


def format_github_link(
    file: AffectedFile, repo_owner: str, repo_name: str, commit_sha: str
) -> str:
    """Generate GitHub URL for file with line number.

    Args:
        file: Affected file with path and line info
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
        commit_sha: Git commit SHA

    Returns:
        Markdown formatted link to GitHub file
    """
    base_url = f"https://github.com/{repo_owner}/{repo_name}/blob/{commit_sha}/{file.file_path}"

    # Add line anchor if available
    if file.line_start:
        if file.line_end and file.line_end != file.line_start:
            # Range: #L10-L15
            line_anchor = f"#L{file.line_start}-L{file.line_end}"
            display = f"{file.file_path}:{file.line_start}-{file.line_end}"
        else:
            # Single line: #L10
            line_anchor = f"#L{file.line_start}"
            display = f"{file.file_path}:{file.line_start}"
        return f"[`{display}`]({base_url}{line_anchor})"
    else:
        return f"[`{file.file_path}`]({base_url})"
