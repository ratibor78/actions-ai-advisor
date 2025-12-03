"""Tests for file parser module."""

from actions_advisor.file_parser import (
    AffectedFile,
    format_github_link,
    parse_affected_files,
)


def test_parse_python_traceback():
    """Test parsing Python traceback with file and line number."""
    log = """
Traceback (most recent call last):
  File "src/main.py", line 42, in main
    result = process_data()
  File "src/processor.py", line 15, in process_data
    raise ValueError("Invalid data")
ValueError: Invalid data
"""
    files = parse_affected_files(log)

    assert len(files) == 2
    assert files[0].file_path == "src/main.py"
    assert files[0].line_start == 42
    assert files[1].file_path == "src/processor.py"
    assert files[1].line_start == 15


def test_parse_generic_file_line():
    """Test parsing generic file:line format."""
    log = """
src/types.py:1: error: Module shadows stdlib
tests/test_example.py:3: AssertionError
"""
    files = parse_affected_files(log)

    assert len(files) == 2
    assert files[0].file_path == "src/types.py"
    assert files[0].line_start == 1
    assert files[1].file_path == "tests/test_example.py"
    assert files[1].line_start == 3


def test_parse_nodejs_stack_trace():
    """Test parsing Node.js stack trace."""
    log = """
Error: Cannot find module './src/index.js'
    at Function.Module._resolveFilename (node:internal/modules/cjs/loader.js:933:15)
    at src/app.js:45:10
    at lib/server.ts:123:5
"""
    files = parse_affected_files(log)

    # Should find src/app.js and lib/server.ts
    file_paths = [f.file_path for f in files]
    assert "src/app.js" in file_paths
    assert "lib/server.ts" in file_paths


def test_parse_docker_copy_error():
    """Test parsing Docker COPY error shows Dockerfile, not missing file."""
    log = """
------
 > [2/3] COPY app.py /app/:
------
Dockerfile:4
--------------------
   4 | >>> COPY app.py /app/
--------------------
ERROR: failed to build: "/app.py": not found
"""
    files = parse_affected_files(log)

    # Should find Dockerfile:4 (the source), not app.py (the missing file)
    assert len(files) >= 1
    assert any(f.file_path == "Dockerfile" and f.line_start == 4 for f in files)


def test_skip_system_paths():
    """Test that system/library paths are filtered out."""
    log = """
  File "/usr/lib/python3.12/site-packages/pkg/module.py", line 10
  File "/opt/hostedtoolcache/Python/3.12/lib/python3.12/asyncio.py", line 50
  File "src/main.py", line 42
"""
    files = parse_affected_files(log)

    # Should only find src/main.py, not system paths
    assert len(files) == 1
    assert files[0].file_path == "src/main.py"


def test_deduplication():
    """Test that duplicate file mentions are deduplicated."""
    log = """
src/types.py:1: error
src/types.py:1: note: Module shadows stdlib
src/main.py:10: error
src/types.py:1: error
"""
    files = parse_affected_files(log)

    # Should have 2 unique files (src/types.py:1 and src/main.py:10)
    assert len(files) == 2


def test_format_github_link_with_line():
    """Test GitHub link formatting with line number."""
    file = AffectedFile(file_path="src/main.py", line_start=42)

    link = format_github_link(file, "user", "repo", "abc123")

    assert link == "[`src/main.py:42`](https://github.com/user/repo/blob/abc123/src/main.py#L42)"


def test_format_github_link_with_range():
    """Test GitHub link formatting with line range."""
    file = AffectedFile(file_path="src/main.py", line_start=10, line_end=15)

    link = format_github_link(file, "user", "repo", "abc123")

    assert (
        link
        == "[`src/main.py:10-15`](https://github.com/user/repo/blob/abc123/src/main.py#L10-L15)"
    )


def test_format_github_link_without_line():
    """Test GitHub link formatting without line number."""
    file = AffectedFile(file_path="src/main.py")

    link = format_github_link(file, "user", "repo", "abc123")

    assert link == "[`src/main.py`](https://github.com/user/repo/blob/abc123/src/main.py)"


def test_parse_empty_log():
    """Test parsing empty log returns empty list."""
    files = parse_affected_files("")

    assert files == []


def test_parse_webpack_error():
    """Test parsing webpack module resolution error with file reference."""
    log = """
ERROR in main
Module not found: Error: Can't resolve './src/utils.js' in '/home/runner/work/repo'
"""
    files = parse_affected_files(log)

    # Should find src/utils.js (after removing ./ prefix)
    assert len(files) >= 1
    assert any(f.file_path == "src/utils.js" for f in files)


def test_parse_dockerfile_variants():
    """Test parsing Dockerfile variants (Dockerfile.dev, Dockerfile.prod)."""
    log = """
Dockerfile.dev:12: warning: Using latest tag
Dockerfile.prod:5: ERROR: invalid syntax
Dockerfile:10: RUN command failed
"""
    files = parse_affected_files(log)

    assert len(files) == 3
    dockerfile_files = [f for f in files if "Dockerfile" in f.file_path]
    assert len(dockerfile_files) == 3
    # Check line numbers are captured
    assert any(f.line_start == 12 for f in dockerfile_files)
    assert any(f.line_start == 5 for f in dockerfile_files)
    assert any(f.line_start == 10 for f in dockerfile_files)


def test_parse_mypy_quoted_file():
    """Test parsing mypy errors with quoted filenames."""
    log = """
mypy: "src/types.py" shadows library module "types"
note: A user-defined top-level module with name "types" is not supported
"""
    files = parse_affected_files(log)

    assert len(files) >= 1
    assert any(f.file_path == "src/types.py" for f in files)


def test_parse_ruff_quoted_file():
    """Test parsing ruff errors with quoted filenames."""
    log = """
ruff: "src/main.py" contains errors
Found 3 errors in "tests/test_app.py"
"""
    files = parse_affected_files(log)

    assert len(files) >= 1
    # Should find at least src/main.py
    file_paths = [f.file_path for f in files]
    assert "src/main.py" in file_paths


def test_parse_dotnet_error():
    """Test parsing .NET/C# error format."""
    log = """
Error: /home/runner/work/project/project/dotnet-app/Program.cs(10,31): \
error CS0103: The name 'UndefinedSymbol' does not exist in the current context

Build FAILED.

Error: /home/runner/work/project/project/dotnet-app/Program.cs(10,31): error CS0103
    0 Warning(s)
    1 Error(s)
"""
    files = parse_affected_files(log)

    assert len(files) >= 1
    # Should find Program.cs with line 10
    assert any(f.file_path == "dotnet-app/Program.cs" and f.line_start == 10 for f in files)


def test_parse_go_test_with_working_directory():
    """Test parsing Go test errors creates search link for filename-only paths."""
    log = """
Run go test ./...
--- FAIL: TestAdd (0.00s)
    math_test.go:7: expected 2, got 3
FAIL
FAIL    example.com/go-app    0.002s
FAIL
Error: Process completed with exit code 1.
"""
    files = parse_affected_files(log)

    assert len(files) >= 1
    # Should find math_test.go (filename only) with line 7
    # Will create search link since no directory in path
    assert any(f.file_path == "math_test.go" and f.line_start == 7 for f in files)


def test_format_github_link_search_for_filename_only():
    """Test that filename-only paths create search links."""
    file = AffectedFile(file_path="math_test.go", line_start=7)

    link = format_github_link(file, "user", "repo", "abc123")

    # Should be a search link with path: qualifier (not filename:)
    assert "search?q=path:math_test.go" in link
    assert "&type=code" in link
    assert "open as search" in link
    assert "`math_test.go:7`" in link


def test_normalize_removes_dot_slash():
    """Test that ./ prefix is removed from paths."""
    from actions_advisor.file_parser import _normalize_file_path

    assert _normalize_file_path("./src/main.py") == "src/main.py"
    assert _normalize_file_path("./test.py") == "test.py"


def test_normalize_rejects_parent_directory():
    """Test that ../ paths are rejected."""
    from actions_advisor.file_parser import _normalize_file_path

    assert _normalize_file_path("../src/main.py") is None
    assert _normalize_file_path("../../test.py") is None


def test_normalize_rejects_unknown_absolute_paths():
    """Test that unknown absolute paths are rejected."""
    from actions_advisor.file_parser import _normalize_file_path

    # Unknown CI paths should be rejected
    assert _normalize_file_path("/builds/project-123/src/main.go") is None
    assert _normalize_file_path("/tmp/test.py") is None
    assert _normalize_file_path("/var/app/main.js") is None

    # But known CI paths should work
    assert _normalize_file_path("/workspace/src/main.py") == "src/main.py"
    assert _normalize_file_path("/home/circleci/project/test.py") == "test.py"
