"""Safe, non-executing error-line preview for Python syntax failures."""
import html

MAX_PREVIEW_CHARS = 20000


def highlighted_excerpt(code, line_number, context=3):
    """Return escaped HTML for a few source lines near a syntax error.

    Only the excerpt is rendered. Never run uploaded/pasted source.
    """
    if not isinstance(code, str):
        raise TypeError("code must be text")
    rows = code[:MAX_PREVIEW_CHARS].splitlines()
    if not isinstance(line_number, int) or line_number < 1 or line_number > len(rows):
        return ""
    start = max(1, line_number - context)
    end = min(len(rows), line_number + context)
    width = len(str(end))
    parts = ['<div class="doctor-code-excerpt" role="region" aria-label="문법 오류 위치">']
    if start > 1:
        parts.append('<div class="code-ellipsis">…</div>')
    for num in range(start, end + 1):
        safe = html.escape(rows[num - 1], quote=True)
        line_class = "code-error-line" if num == line_number else "code-normal-line"
        label = " 오류 발생" if num == line_number else ""
        parts.append(
            f'<div class="{line_class}" aria-label="{num}행{label}">'
            f'<span class="code-line-num">{num:>{width}}</span>'
            f'<span class="code-line-text">{safe or " "}</span></div>'
        )
    if end < len(rows):
        parts.append('<div class="code-ellipsis">…</div>')
    parts.append("</div>")
    return "\n".join(parts)
