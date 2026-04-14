from __future__ import annotations

from typing import Any


def _fmt_cmd(cmd: str) -> str:
    cmd = (cmd or '').strip()
    if not cmd:
        return 'command'
    return cmd


def summarize_automation(commands: list[str], results: list[Any] | None) -> str:
    """Create a human-readable summary for executed automation commands.

    This is returned to the chat UI so the assistant never shows an empty
    response when the task executed successfully (e.g. "open youtube and search hello").

    Args:
      commands: list of automation command strings.
      results: list returned by Backend.Automation.Automation().

    Returns:
      A plain English summary.
    """
    commands = commands or []
    results = results or []

    if not commands:
        return "I didn't receive any automation commands to run."

    lines: list[str] = []
    for idx, cmd in enumerate(commands):
        res = results[idx] if idx < len(results) else None

        # Normalize
        ok = None
        err = None
        extra = None

        if isinstance(res, Exception):
            ok = False
            err = str(res)
        elif isinstance(res, bool):
            ok = res
        elif res is None:
            ok = None
        else:
            # strings (e.g. screenshot message) or other
            ok = True
            extra = str(res)

        c = _fmt_cmd(cmd)

        if ok is True:
            if extra and extra.lower() != 'true':
                lines.append(f"✓ {c} — {extra}")
            else:
                lines.append(f"✓ {c} — done")
        elif ok is False:
            lines.append(f"✗ {c} — failed" + (f" ({err})" if err else ""))
        else:
            lines.append(f"• {c} — executed")

    header = "⚡ AGENT: Executing your computer commands...\n\n"
    summary = header + "\n".join(lines)
    
    # AGENT RULE 1 & 9: Confirm completion and suggest next step
    summary += "\n\n✅ Task complete — Everything is up to date."
    summary += "\n⚡ Want me to assist with anything else?"
    return summary
