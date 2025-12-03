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
    # .NET/C# errors: Program.cs(10,31): error CS0103
    re.compile(r"(?P<file>[\w./\-]+\.cs)\((?P<line>\d+),\d+\):"),
    # Linters/type checkers with quoted files: mypy: "src/types.py"
    re.compile(r'(?:mypy|ruff|pylint|flake8|pyright|black):\s+"(?P<file>[^"]+)"'),
    # Dockerfile errors: Dockerfile:4
    re.compile(r"(?P<file>Dockerfile(?:\.[a-z]+)?):(?P<line>\d+)"),
    # Generic: file.py:123 or file.py:123:45 (expanded to include more extensions)
    re.compile(r"(?P<file>[\w./\-]+\.(?:py|js|ts|tsx|jsx|go|rs|rb|java|cpp|c|h|cs|php|swift|kt|scala)):(?P<line>\d+)(?::\d+)?"),
    # Node.js stack: at /path/to/file.js:123:45
    re.compile(r"at (?P<file>[\w./\-]+\.(?:js|ts|tsx|jsx)):(?P<line>\d+):\d+"),
    # Common extensionless files: Makefile, CMakeLists.txt
    re.compile(r"(?P<file>(?:Makefile|CMakeLists\.txt|Gemfile|Rakefile)):(?P<line>\d+)"),
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

            # Normalize and validate file path
            normalized_path = _normalize_file_path(file_path)

            if normalized_path and _is_valid_file_path(normalized_path):
                affected_files.add(
                    AffectedFile(
                        file_path=normalized_path,
                        line_start=line_num,
                    )
                )

    # Sort by file path for consistent output
    return sorted(affected_files, key=lambda f: (f.file_path, f.line_start or 0))


def _normalize_file_path(path: str) -> str | None:
    """Normalize file paths to relative project paths.

    Args:
        path: Raw file path from error logs

    Returns:
        Normalized relative path, or None if path is invalid
    """
    # GitHub Actions workspace: /home/runner/work/{repo}/{repo}/...
    # Extract relative path after the second occurrence of repo name
    if "/home/runner/work/" in path:
        parts = path.split("/")
        try:
            work_idx = parts.index("work")
            # Skip 'work', repo name, repo name again, then take the rest
            if len(parts) > work_idx + 3:
                return "/".join(parts[work_idx + 3 :])
        except (ValueError, IndexError):
            pass

    # Jenkins/other CI: /workspace/...
    if path.startswith("/workspace/"):
        return path.replace("/workspace/", "", 1)

    # CircleCI: /home/circleci/project/...
    if "/home/circleci/project/" in path:
        return path.split("/home/circleci/project/", 1)[1]

    # Already relative or simple path
    return path


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

    # Common extensionless files in root
    extensionless_files = (
        "Dockerfile",
        "Makefile",
        "Gemfile",
        "Rakefile",
        "CMakeLists.txt",
    )
    for valid_file in extensionless_files:
        if path == valid_file or path.startswith(valid_file + "."):
            return True

    # Or be a simple filename in root with extension
    if "/" not in path and "." in path:
        return True

    # Or have a recognized source code extension (likely project file)
    if "." in path:
        ext = path.rsplit(".", 1)[1]
        source_extensions = {
            "py", "js", "ts", "tsx", "jsx", "go", "rs", "rb", "java",
            "cpp", "c", "h", "cs", "php", "swift", "kt", "scala",
            "pyx", "cc", "hpp", "cxx"
        }
        if ext in source_extensions:
            return True

    return False


def format_github_link(
    file: AffectedFile, repo_owner: str, repo_name: str, commit_sha: str
) -> str:
    """Generate GitHub URL for file with line number.

    Uses hybrid strategy (universal for all languages):
    - If path includes directory (e.g., src/main.py) → direct link
    - If only filename (e.g., main.py) → search link with note

    Args:
        file: Affected file with path and line info
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
        commit_sha: Git commit SHA

    Returns:
        Markdown formatted link to GitHub file or search
    """
    # Check if we have a directory path or just a filename
    has_directory = "/" in file.file_path

    if has_directory:
        # Strategy 1: Direct link to file (we have relative path)
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
    else:
        # Strategy 2: Search link (only filename, path not resolved)
        search_url = f"https://github.com/{repo_owner}/{repo_name}/search?q=filename:{file.file_path}"
        display = f"{file.file_path}:{file.line_start}" if file.line_start else file.file_path
        return f"[`{display}`]({search_url}) _(path not resolved, opened as search)_"
