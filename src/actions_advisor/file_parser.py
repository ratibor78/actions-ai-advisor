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
# Pattern component for cross-platform paths (Windows: C:\path\file, Unix: /path/file)
PATH_PATTERN = r"(?:[A-Za-z]:[\\/])?[\w.\/\\\-]+"

FILE_PATTERNS = [
    # Python traceback: File "/path/to/file.py", line 123 (handles both / and \)
    re.compile(r'File "(?P<file>[^"]+\.(?:py|pyx))", line (?P<line>\d+)'),
    # PHP errors: in /path/to/file.php on line 4
    re.compile(rf" in (?P<file>{PATH_PATTERN}\.php) on line (?P<line>\d+)"),
    # .NET/C# errors: Program.cs(10,31): error CS0103 or C:\path\Program.cs(10,31)
    re.compile(rf"(?P<file>{PATH_PATTERN}\.cs)\((?P<line>\d+),\d+\):"),
    # Linters/type checkers with quoted files: mypy: "src/types.py" or "src\types.py"
    re.compile(r'(?:mypy|ruff|pylint|flake8|pyright|black):\s+"(?P<file>[^"]+)"'),
    # Dockerfile errors: Dockerfile:4
    re.compile(r"(?P<file>Dockerfile(?:\.[a-z]+)?):(?P<line>\d+)"),
    # Generic: file.py:123 or file.py:123:45 (Windows: C:\path\file.py:123)
    re.compile(rf"(?P<file>{PATH_PATTERN}\.(?:py|js|ts|tsx|jsx|go|rs|rb|java|cpp|c|h|cs|php|swift|kt|scala)):(?P<line>\d+)(?::\d+)?"),
    # Node.js stack: at /path/to/file.js:123:45 or at C:\path\file.js:123:45
    re.compile(rf"at (?P<file>{PATH_PATTERN}\.(?:js|ts|tsx|jsx)):(?P<line>\d+):\d+"),
    # Common extensionless files: Makefile, CMakeLists.txt
    re.compile(r"(?P<file>(?:Makefile|CMakeLists\.txt|Gemfile|Rakefile)):(?P<line>\d+)"),
    # Webpack: Module not found: Error: Can't resolve './src' or '.\src'
    re.compile(rf"Can't resolve ['\"](?P<file>{PATH_PATTERN})['\"]"),
    # Generic file mention: checking src/main.py or src\main.py
    re.compile(rf"(?:checking|in|file|from|import)\s+(?P<file>{PATH_PATTERN}\.(?:py|js|ts|go|rs|rb|java))"),
]


def parse_affected_files(log_content: str) -> list[AffectedFile]:
    """Extract file paths and line numbers from error logs.

    Args:
        log_content: Raw or preprocessed log content

    Returns:
        List of unique affected files with line numbers
    """
    affected_files: set[AffectedFile] = set()

    # Try to detect working directory from build tool output
    working_dir = _extract_working_directory(log_content)

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

            # If we have a working directory and path looks incomplete, prepend it
            if working_dir and normalized_path and _looks_like_incomplete_path(normalized_path):
                normalized_path = f"{working_dir}/{normalized_path}"

            if normalized_path and _is_valid_file_path(normalized_path):
                affected_files.add(
                    AffectedFile(
                        file_path=normalized_path,
                        line_start=line_num,
                    )
                )

    # Sort by file path for consistent output
    return sorted(affected_files, key=lambda f: (f.file_path, f.line_start or 0))


def _extract_working_directory(log_content: str) -> str | None:
    """Extract working directory from build tool output.

    Handles multiple build tools and log formats:
    - Rust: Compiling rust-app v0.1.0 (/path/to/rust-app)
    - Go: FAIL    example.com/go-app    0.002s

    Robust handling of:
    - ANSI color codes (common in CI logs)
    - GitHub Actions timestamps (YYYY-MM-DDTHH:MM:SS.NNNNNNNZ)
    - Various whitespace patterns
    - Root vs subdirectory projects

    Args:
        log_content: Raw log content from CI system

    Returns:
        Working directory name (e.g., "rust-app"), or None if:
        - No working directory detected
        - Root-level project (not in subdirectory)
    """
    # Step 1: Strip ANSI escape codes (color, bold, etc.)
    # GitHub Actions and most CI systems colorize output, which breaks pattern matching
    # Example: \x1b[1m\x1b[92mCompiling\x1b[0m → Compiling
    ansi_escape = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
    clean_content = ansi_escape.sub("", log_content)

    # Step 2: Rust/Cargo working directory detection
    # Matches: Compiling rust-app v0.1.0 (/home/runner/work/test-actions-advisor/test-actions-advisor/rust-app)
    # Handles:
    # - Optional GitHub Actions timestamp prefix: 2025-12-10T08:16:46.5215607Z
    # - Flexible whitespace between timestamp and "Compiling"
    # - Any Rust package name and version format
    # - Cross-platform paths (Unix and Windows)
    rust_pattern = re.compile(
        r"""
        (?:^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s+)?  # Optional timestamp + whitespace
        Compiling\s+                                          # "Compiling" + whitespace
        \S+\s+                                                # Package name + whitespace
        v[\d.]+(?:-[a-zA-Z0-9.]+)?\s+                        # Version (e.g., v0.1.0 or v0.1.0-beta) + whitespace
        \(                                                    # Opening parenthesis
        (?P<full_path>.*?/(?P<parent>[^/]+)/(?P<last>[^/\)]+))  # Capture path components
        \)                                                    # Closing parenthesis
        """,
        re.MULTILINE | re.VERBOSE
    )

    match = rust_pattern.search(clean_content)
    if match:
        parent = match.group("parent")
        last = match.group("last")

        # GitHub Actions pattern: /home/runner/work/{repo}/{repo}/{subdir}
        # Only use the last component as working directory if it differs from parent
        # - If parent == last: root project (e.g., /work/myrepo/myrepo) → return None
        # - If parent != last: subdirectory (e.g., /work/myrepo/myrepo/backend) → return "backend"
        if parent != last:
            return last

    # Step 3: Go test working directory detection
    # Matches: FAIL    example.com/go-app    0.002s
    go_pattern = re.compile(r"^FAIL\s+\S+/(\S+?)\s+[\d.]+s$", re.MULTILINE)
    match = go_pattern.search(clean_content)
    if match:
        return match.group(1)

    return None


def _looks_like_incomplete_path(path: str) -> bool:
    """Check if path looks like it might be missing a parent directory.

    Paths like src/lib.rs, tests/test.py, lib/utils.js might be relative
    to a project subdirectory (e.g., rust-app/src/lib.rs).

    Args:
        path: Normalized file path

    Returns:
        True if path might be incomplete
    """
    # If it's just a filename (no directory), it might need a working directory prefix
    if "/" not in path:
        return True

    # Common generic directory structures that might be in subdirectories
    generic_starts = ("src/", "tests/", "test/", "lib/", "pkg/", "internal/", "cmd/")
    return any(path.startswith(prefix) for prefix in generic_starts)


def _normalize_file_path(path: str) -> str | None:
    r"""Normalize file paths to relative project paths (cross-platform).

    Handles both Unix paths (/path/to/file) and Windows paths (C:\path\to\file).
    Converts all paths to Unix-style (forward slashes) for consistency.

    Args:
        path: Raw file path from error logs

    Returns:
        Normalized relative path with forward slashes, or None if path is invalid
    """
    # First, normalize backslashes to forward slashes for consistent processing
    normalized = path.replace("\\", "/")

    # Windows GitHub Actions: D:/a/{repo}/{repo}/... (after backslash conversion)
    # Example: D:/a/myrepo/myrepo/src/file.py -> src/file.py
    if re.match(r"^[A-Za-z]:/a/", normalized):
        parts = normalized.split("/")
        # Structure: ['D:', 'a', 'repo', 'repo', 'src', 'file.py']
        # Skip drive, 'a', repo name, repo name again (first 4 parts)
        if len(parts) > 4:
            return "/".join(parts[4:])

    # Linux GitHub Actions workspace: /home/runner/work/{repo}/{repo}/...
    # Extract relative path after the second occurrence of repo name
    if "/home/runner/work/" in normalized:
        parts = normalized.split("/")
        try:
            work_idx = parts.index("work")
            # Skip 'work', repo name, repo name again, then take the rest
            if len(parts) > work_idx + 3:
                return "/".join(parts[work_idx + 3 :])
        except (ValueError, IndexError):
            pass

    # Jenkins/other CI: /workspace/...
    if normalized.startswith("/workspace/"):
        return normalized.replace("/workspace/", "", 1)

    # CircleCI: /home/circleci/project/...
    if "/home/circleci/project/" in normalized:
        return normalized.split("/home/circleci/project/", 1)[1]

    # Strip Windows drive letter for absolute paths (C:/project/src -> project/src)
    # But keep paths that are already relative
    drive_match = re.match(r"^[A-Za-z]:/(.+)", normalized)
    if drive_match:
        # This is a Windows absolute path - try to extract repo-relative part
        # Common pattern: C:/Users/runner/project/src/file.py
        remaining_path = drive_match.group(1)
        # If it contains common workspace indicators, try to extract from there
        if "/project/" in remaining_path:
            return remaining_path.split("/project/", 1)[1]
        # Otherwise, just remove the drive letter and hope it's relative-ish
        return remaining_path

    # Clean relative path prefixes
    if normalized.startswith("./"):
        normalized = normalized[2:]  # Remove ./

    # Parent directory references are not resolvable in repo context
    if normalized.startswith("../"):
        return None

    # Unknown absolute paths (not CI workspace) are likely not resolvable
    if normalized.startswith("/"):
        return None

    # Already relative or simple path
    return normalized


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

    # Filter out common Java/JDK library files (from stack traces)
    if path.endswith(".java"):
        # Common JDK/library class names that should be filtered
        java_library_files = {
            "ArrayList.java", "HashMap.java", "Method.java", "Class.java",
            "String.java", "Integer.java", "Object.java", "Thread.java",
            "AssertEquals.java", "Assertions.java", "AssertionFailureBuilder.java",
            "Test.java", "Before.java", "After.java", "Suite.java",
        }
        filename = path.split("/")[-1]  # Get just the filename
        if filename in java_library_files:
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
        # Use path: qualifier (filename: is deprecated) and restrict to code search
        search_url = f"https://github.com/{repo_owner}/{repo_name}/search?q=path:{file.file_path}&type=code"
        display = f"{file.file_path}:{file.line_start}" if file.line_start else file.file_path
        return f"[`{display}`]({search_url}) _(open as search)_"
