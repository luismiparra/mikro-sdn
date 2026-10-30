"""Readable console logs for the CI pipeline.

Only changes how the log records are shown, never what is logged or the record itself (the
tests read record.message through caplog and keep seeing the original text):

- An icon per line chosen by level and by the kind of action (clean, push, update, remove...).
- The "<scope> -> <message>" prefix used across the project is split into an aligned column, so
  the lines of every device stay readable when the push runs multi thread.
- "------------------------" headers are drawn as section banners.
- Under GitHub Actions warnings and errors are also emitted as annotations, so they show in the
  run summary page.
- A tally of the records per scope feeds the summary tables printed at the end of a run, that
  are also written to $GITHUB_STEP_SUMMARY when it exists.
"""

import logging
import os
import re
import threading
from collections import Counter, defaultdict

SCOPE_WIDTH = 14
BANNER_WIDTH = 78

LEVEL_ICONS = {
    logging.DEBUG: "🔍",
    logging.INFO: "🔹",
    logging.WARNING: "⚠️",
    logging.ERROR: "❌",
    logging.CRITICAL: "🔥",
}

#Kind of action -> (icon, regex over the message). The first match wins
KINDS = [
    ("connection", "🔌", re.compile(r"CONNECTION|host is unreachable|Error connecting", re.I)),
    ("error", "❌", re.compile(r"\berror\b", re.I)),
    ("dry_run", "🧪", re.compile(r"DRY RUN")),
    ("disabled", "⏸️", re.compile(r"disabled", re.I)),
    ("remove", "🗑️", re.compile(r"removing|^Delete ->", re.I)),
    ("update", "🔄", re.compile(r"Update needed|^Update ->")),
    ("create", "➕", re.compile(r"^Create ->|\bcreated\b", re.I)),
    ("not_found", "🔎", re.compile(r"not found", re.I)),
    ("clean", "🧹", re.compile(r"Start clean")),
    ("push", "🚀", re.compile(r"Start push|PUSH MODE")),
    ("ok", "✅", re.compile(r"^(OK|DONE)\b")),
    ("target", "🎯", re.compile(r"TARGET_DEVICE|SPECIFIC HOST|ONE HOST")),
    ("inventory", "📦", re.compile(r"inventory", re.I)),
    ("docs", "📝", re.compile(r"DOCS")),
    ("generate", "⚙️", re.compile(r"Generate|Prepare", re.I)),
]

#Icons of the section banners by keyword of the title
BANNER_ICONS = [
    (re.compile(r"START", re.I), "🚀"),
    (re.compile(r"DONE|END", re.I), "🏁"),
    (re.compile(r"INVENTORY"), "📦"),
    (re.compile(r"FILES"), "📁"),
    (re.compile(r"GENERATE"), "⚙️"),
    (re.compile(r"DISABLED|NOT CONFIG"), "⏸️"),
]

#"<scope> -> msg", "<scope> --> msg", "<scope> ->--msg", "<scope>->  msg"
_SCOPED = re.compile(r"^(?P<scope>[\w.\- ]+?)\s*-{1,2}>(?P<rest>.*)$", re.S)
#A scope is a section in capitals (GENERAL, ONEHOST MODE) or a device name (lab-mikro5), so
#"Update -> ..." or "Error getting device --> ..." are not split
_SCOPE_NAME = re.compile(r"^([A-Z][A-Z ]*|[\w.\-]*\d[\w.\-]*)$")
_HEADER = re.compile(r"^-{4,}\s*(?P<title>.*?)\s*-*$", re.S)


def classify(record):
    """Kind and icon of a record. Warnings and errors keep the icon of their level unless the
    error is a connection problem."""
    message = _split(record.getMessage())[1]
    for kind, icon, pattern in KINDS:
        if pattern.search(message):
            if record.levelno < logging.WARNING or (kind == "connection" and record.levelno >= logging.ERROR):
                return kind, icon
            break
    if record.levelno >= logging.ERROR:
        return "error", LEVEL_ICONS[logging.ERROR]
    if record.levelno >= logging.WARNING:
        return "warning", LEVEL_ICONS[logging.WARNING]
    return "info", LEVEL_ICONS.get(record.levelno, LEVEL_ICONS[logging.INFO])


def _split(message):
    """(scope, message) of a project log line. Scope is "" when the line has none."""
    message = message.strip()
    match = _SCOPED.match(message)
    if match and _SCOPE_NAME.match(match.group("scope").strip()):
        return match.group("scope").strip(), match.group("rest").strip()
    return "", message


def _banner(icon, title):
    text = f" {icon} {title} " if icon else f" {title} "
    side = max(3, (BANNER_WIDTH - len(text)) // 2)
    return f"\n{'━' * side}{text}{'━' * side}"


def _annotation_escape(text):
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


class PrettyFormatter(logging.Formatter):

    def __init__(self, github=None):
        super().__init__()
        self.github = os.environ.get("GITHUB_ACTIONS") == "true" if github is None else github

    def format(self, record):
        scope, message = _split(record.getMessage())

        header = _HEADER.match(message)
        if header and record.levelno < logging.WARNING:
            title = header.group("title")
            label = f"{scope} · {title}" if scope else title
            icon = next((icon for pattern, icon in BANNER_ICONS if pattern.search(title)), "")
            return _banner(icon, label)

        _, icon = classify(record)
        lines = message.lstrip("- ").splitlines() or [""]
        prefix = f"{icon} {scope:<{SCOPE_WIDTH}} │ "
        indent = " " * (SCOPE_WIDTH + 4) + "│ "
        text = prefix + lines[0] + "".join(f"\n{indent}{line}" for line in lines[1:])
        if record.exc_info:
            text += "\n" + self.formatException(record.exc_info)

        if self.github and record.levelno >= logging.WARNING:
            command = "error" if record.levelno >= logging.ERROR else "warning"
            title = f" title={scope}" if scope else ""
            return f"::{command}{title}::{_annotation_escape(text)}"
        return text


class TallyHandler(logging.Handler):
    """Counts the records of every scope by kind, for the summary tables."""

    def __init__(self):
        super().__init__(logging.DEBUG)
        self.counts = defaultdict(Counter)

    def emit(self, record):
        scope, _ = _split(record.getMessage())
        kind, _ = classify(record)
        self.counts[scope][kind] += 1


tally = TallyHandler()
_setup_lock = threading.Lock()


def setup(level=logging.INFO):
    """Drop-in for logging.basicConfig(level=...): does nothing when the root logger already
    has handlers, as basicConfig."""
    root = logging.getLogger()
    with _setup_lock:
        if root.handlers:
            return
        handler = logging.StreamHandler()
        handler.setFormatter(PrettyFormatter())
        root.addHandler(handler)
        root.addHandler(tally)
        root.setLevel(level)


def table(headers, rows):
    """Box drawn table, emoji aware enough for the icons used here."""
    def width(text):
        return sum(2 if ord(ch) > 0x2500 and ch not in "️─│" else 0 if ch == "️" else 1
                   for ch in str(text))

    def pad(text, size):
        return str(text) + " " * (size - width(text))

    sizes = [max(width(cell) for cell in column) for column in zip(headers, *rows)]
    line = lambda left, mid, right: left + mid.join("─" * (size + 2) for size in sizes) + right
    render = lambda cells: "│" + "│".join(f" {pad(cell, size)} " for cell, size in zip(cells, sizes)) + "│"
    out = [line("┌", "┬", "┐"), render(headers), line("├", "┼", "┤")]
    out += [render(row) for row in rows]
    out.append(line("└", "┴", "┘"))
    return "\n".join(out)


def markdown_table(headers, rows):
    out = ["| " + " | ".join(map(str, headers)) + " |", "|" + "|".join(" --- " for _ in headers) + "|"]
    out += ["| " + " | ".join(map(str, row)) + " |" for row in rows]
    return "\n".join(out)


def report(title, headers, rows):
    """Log a summary table and add it to the GitHub step summary when running in Actions."""
    if not rows:
        return
    logging.info(f"{title}\n{table(headers, rows)}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as file:
            file.write(f"### {title}\n\n{markdown_table(headers, rows)}\n\n")


def device_status(counts):
    if counts["connection"]:
        return "🔌 unreachable"
    if counts["error"]:
        return "❌ errors"
    if counts["disabled"]:
        return "⏸️ disabled"
    if counts["ok"]:
        return "✅ ok"
    return "➖"


def device_report(title, names):
    """Per device result of a clean + push run, from the tallied records."""
    headers = ["Device", "🗑️ Removed", "🔄 Updated", "⚠️ Warnings", "❌ Errors", "Status"]
    rows = []
    for name in names:
        counts = tally.counts.get(name, Counter())
        errors = counts["error"] + counts["connection"]
        rows.append([name, counts["remove"], counts["update"], counts["warning"], errors,
                     device_status(counts)])
    report(title, headers, rows)
