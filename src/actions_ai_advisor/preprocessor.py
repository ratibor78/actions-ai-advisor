"""Log preprocessing module to reduce tokens and extract relevant information."""

import re


def preprocess_logs(raw_logs: str) -> str:
    """Preprocess raw logs to reduce tokens and extract relevant errors.

    Args:
        raw_logs: Raw log content from GitHub Actions

    Returns:
        Cleaned and reduced log content
    """
    # Step 1: Remove ANSI escape codes
    text = _remove_ansi_codes(raw_logs)

    # Step 2: Remove timestamp prefixes
    text = _remove_timestamps(text)

    # Step 3: Split into lines for further processing
    lines = text.split("\n")

    # Step 4: Remove GitHub Actions metadata lines
    lines = _remove_github_metadata(lines)

    # Step 5: Collapse repeated lines
    lines = _collapse_repeated_lines(lines)

    # Step 6: Remove excessive empty lines
    lines = _remove_excessive_empty_lines(lines)

    # Step 7: Keep last N lines (focus on the failure)
    lines = lines[-150:]

    return "\n".join(lines)


def _remove_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text.

    Args:
        text: Text with ANSI codes

    Returns:
        Text without ANSI codes
    """
    ansi_escape = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
    return ansi_escape.sub("", text)


def _remove_timestamps(text: str) -> str:
    """Remove timestamp prefixes from lines.

    Args:
        text: Text with timestamps

    Returns:
        Text without timestamps
    """
    # Match ISO 8601 timestamps: 2024-01-01T10:00:00.123456Z
    timestamp_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s*", re.MULTILINE)
    return timestamp_pattern.sub("", text)


def _remove_github_metadata(lines: list[str]) -> list[str]:
    """Remove GitHub Actions metadata lines.

    Args:
        lines: List of log lines

    Returns:
        Filtered list without metadata
    """
    metadata_patterns = [
        r"^##\[group\]",
        r"^##\[endgroup\]",
        r"^##\[command\]",
        r"^##\[debug\]",
        r"::set-output",
        r"::debug",
        r"::notice",
        r"::warning",
    ]

    filtered_lines = []
    for line in lines:
        is_metadata = any(re.match(pattern, line) for pattern in metadata_patterns)
        if not is_metadata:
            filtered_lines.append(line)

    return filtered_lines


def _collapse_repeated_lines(lines: list[str]) -> list[str]:
    """Collapse consecutive repeated lines.

    If the same line appears 3+ times consecutively, replace with
    single instance + count.

    Args:
        lines: List of log lines

    Returns:
        List with repeated lines collapsed
    """
    if not lines:
        return lines

    collapsed = []
    prev_line = None
    repeat_count = 0

    for line in lines:
        if line == prev_line:
            repeat_count += 1
        else:
            # Output previous line if it had repeats
            if prev_line is not None:
                if repeat_count >= 3:
                    collapsed.append(f"{prev_line} (repeated {repeat_count} times)")
                else:
                    # Add each individual line if less than 3 repeats
                    for _ in range(repeat_count):
                        collapsed.append(prev_line)

            prev_line = line
            repeat_count = 1

    # Handle last line
    if prev_line is not None:
        if repeat_count >= 3:
            collapsed.append(f"{prev_line} (repeated {repeat_count} times)")
        else:
            for _ in range(repeat_count):
                collapsed.append(prev_line)

    return collapsed


def _remove_excessive_empty_lines(lines: list[str]) -> list[str]:
    """Remove more than 2 consecutive empty lines.

    Args:
        lines: List of log lines

    Returns:
        List with excessive empty lines removed
    """
    filtered = []
    empty_count = 0

    for line in lines:
        if line.strip() == "":
            empty_count += 1
            if empty_count <= 2:
                filtered.append(line)
        else:
            empty_count = 0
            filtered.append(line)

    return filtered
