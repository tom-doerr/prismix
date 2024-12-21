def apply_code_edit(file_content: str, start_line: int, end_line: int, replacement_text: str) -> str:
    """Applies a code edit to the given file content."""
    lines = file_content.splitlines(True)
    modified_lines = lines[: start_line - 1] if start_line > 1 else []
    modified_lines.append(replacement_text)
    modified_lines.extend(lines[end_line:])
    return "".join(modified_lines)
