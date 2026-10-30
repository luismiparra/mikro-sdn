"""CI log formatter: icons, scope column, banners, GitHub annotations and summary tables."""

import logging
from collections import Counter

import pytest

import mikro_log


def record(message, level=logging.INFO, exc_info=None):
    return logging.LogRecord("root", level, __file__, 1, message, None, exc_info)


def fmt(message, level=logging.INFO, github=False, exc_info=None):
    return mikro_log.PrettyFormatter(github=github).format(record(message, level, exc_info))


@pytest.fixture
def tally(monkeypatch):
    handler = mikro_log.TallyHandler()
    monkeypatch.setattr(mikro_log, "tally", handler)
    return handler


# ---------------------------------------------------------------- formatter

@pytest.mark.parametrize("message, level, icon, scope, text", [
    ("lab-mikro5 -> Start clean", logging.INFO, "🧹", "lab-mikro5", "Start clean"),
    ("lab-mikro5 -> OK push", logging.INFO, "✅", "lab-mikro5", "OK push"),
    ("lab-mikro5 -> Start push", logging.INFO, "🚀", "lab-mikro5", "Start push"),
    ("lab-mikro5 -> A_Update needed at /ip/route -> x", logging.INFO, "🔄", "lab-mikro5", "A_Update needed"),
    ("lab-mikro5 -> general rule Found rule not at the config, removing -> {}", logging.INFO, "🗑️", "lab-mikro5", "removing"),
    ("lab-mikro5 -> Push Disabled", logging.INFO, "⏸️", "lab-mikro5", "Push Disabled"),
    ("\n\nlab-mikro0 --> Generate config for: ---> ['fw']", logging.DEBUG, "⚙️", "lab-mikro0", "Generate config for"),
    ("GENERAL -> load inventory", logging.INFO, "📦", "GENERAL", "load inventory"),
    ("GENERAL -> Start Creating DOCS", logging.INFO, "📝", "GENERAL", "Start Creating DOCS"),
    ("GENERAL -> TARGET_DEVICE found in env: lab-mikro5", logging.INFO, "🎯", "GENERAL", "TARGET_DEVICE"),
    ("GENERAL -> something else", logging.INFO, "🔹", "GENERAL", "something else"),
    ("Config generation DONE \n\n", logging.DEBUG, "🔍", "", "Config generation DONE"),
    ("Tag found: x", logging.DEBUG, "🔍", "", "Tag found"),
    ("Update -> Module: dcim Item: dev1", logging.INFO, "🔄", "", "Update -> Module"),
    ("Delete -> Module: dcim Item: dev1", logging.INFO, "🗑️", "", "Delete -> Module"),
    ("Create -> Module: dcim Item: dev1", logging.INFO, "➕", "", "Create -> Module"),
    ("DRY RUN dcim.devices: create 1", logging.INFO, "🧪", "", "DRY RUN"),
    ("Region with slug 'x' not found.", logging.INFO, "🔎", "", "not found"),
    ("Error creating private RIR: x", logging.INFO, "❌", "", "Error creating"),
    ("lab-mikro0 --> Warning No specific FW config ", logging.WARNING, "⚠️", "lab-mikro0", "Warning No specific"),
    ("dev1 -> Connection has either been refused, or the host is unreachable.", logging.WARNING, "⚠️", "dev1", "refused"),
    ("lab-mikro6 ->--CONNECTION ERROR!->>> at IP 1.2.3.4", logging.ERROR, "🔌", "lab-mikro6", "CONNECTION ERROR!"),
    ("lab-mikro6 -> Error getRunningBy: x", logging.ERROR, "❌", "lab-mikro6", "Error getRunningBy"),
    ("Something broke", logging.CRITICAL, "❌", "", "Something broke"),
])
def test_line_has_icon_scope_column_and_message(message, level, icon, scope, text):
    line = fmt(message, level)
    assert line.startswith(f"{icon} {scope:<{mikro_log.SCOPE_WIDTH}} │ ")
    assert text in line
    assert "\n" not in line


def test_scope_is_only_a_section_or_a_device_name():
    assert mikro_log._split("Error getting device --> dev1 IP --> x") == ("", "Error getting device --> dev1 IP --> x")
    assert mikro_log._split("MAIN CONTROL->  x") == ("MAIN CONTROL", "x")
    assert mikro_log._split("Update -> x") == ("", "Update -> x")


@pytest.mark.parametrize("message, icon, title", [
    ("GENERAL -> ------------------------AUTOMATION LOAD INVENTORY", "📦", "GENERAL · AUTOMATION LOAD INVENTORY"),
    ("GENERAL -> ------------------------GENERATE CONFIG", "⚙️", "GENERAL · GENERATE CONFIG"),
    ("GENERAL -> ------------------------CREATE FILES", "📁", "GENERAL · CREATE FILES"),
    ("NETBOX -> ------------------------DONE in 1.0s", "🏁", "NETBOX · DONE in 1.0s"),
    ("\n ---- MIKRO-SDN START---- \n\n", "🚀", "MIKRO-SDN START"),
    ("GENERAL -> ------------------------SOMETHING", "", "GENERAL · SOMETHING"),
])
def test_section_headers_are_banners(message, icon, title):
    banner = fmt(message)
    text = f" {icon} {title} " if icon else f" {title} "
    assert banner.startswith("\n━━━") and banner.endswith("━━━")
    assert text in banner


def test_header_logged_as_warning_keeps_its_level_icon():
    line = fmt("MAIN CONTROL->  ------------------------MIKRO AUTO DISABLED", logging.WARNING)
    assert line.startswith("⚠️ MAIN CONTROL")
    assert line.endswith("│ MIKRO AUTO DISABLED")


def test_multiline_messages_are_indented_under_the_message_column():
    first, blank, last = fmt("lab-mikro5 -> ADD FW rule Error\n\n  boom", logging.ERROR).split("\n")
    column = first.index("│")
    assert blank.index("│") == last.index("│") == column + 1
    assert last.endswith("│   boom")


def test_exceptions_are_appended():
    try:
        raise ValueError("bad")
    except ValueError:
        import sys
        line = fmt("lab-mikro5 -> failed", logging.ERROR, exc_info=sys.exc_info())
    assert "ValueError: bad" in line


def test_github_annotations_for_warnings_and_errors():
    error = fmt("lab-mikro5 -> Error 100%\nnext", logging.ERROR, github=True)
    assert error.startswith("::error title=lab-mikro5::❌ lab-mikro5")
    assert "100%25%0A" in error and "\n" not in error
    assert fmt("odd warning", logging.WARNING, github=True).startswith("::warning::⚠️")
    assert fmt("lab-mikro5 -> Start push", github=True).startswith("🚀")


def test_github_mode_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert mikro_log.PrettyFormatter().github is True
    monkeypatch.setenv("GITHUB_ACTIONS", "")
    assert mikro_log.PrettyFormatter().github is False


# ---------------------------------------------------------------- setup

def test_setup_does_nothing_when_logging_is_configured(monkeypatch):
    root = logging.getLogger()
    monkeypatch.setattr(root, "handlers", [logging.NullHandler()])
    mikro_log.setup(logging.DEBUG)
    assert len(root.handlers) == 1


def test_setup_installs_formatter_and_tally(monkeypatch):
    root = logging.getLogger()
    monkeypatch.setattr(root, "handlers", [])
    monkeypatch.setattr(root, "level", root.level)
    mikro_log.setup(logging.DEBUG)
    assert isinstance(root.handlers[0].formatter, mikro_log.PrettyFormatter)
    assert root.handlers[1] is mikro_log.tally
    assert root.level == logging.DEBUG


# ---------------------------------------------------------------- tables

def test_table_aligns_text_and_icons():
    lines = mikro_log.table(["Device", "Status"], [["gw1", "✅ ok"], ["lab-mikro10", "⏸️ disabled"]]).split("\n")
    assert lines[0].startswith("┌") and lines[-1].startswith("└")
    widths = {table_width(line) for line in lines}
    assert len(widths) == 1


def table_width(line):
    # Display width with the same rule the table uses: emojis are two columns, VS16 none
    return sum(0 if ch == "️" else 2 if ord(ch) > 0x2500 and ch not in "─│┌┬┐├┼┤└┴┘" else 1 for ch in line)


def test_markdown_table():
    assert mikro_log.markdown_table(["a", "b"], [[1, 2]]) == "| a | b |\n| --- | --- |\n| 1 | 2 |"


def test_report_logs_and_writes_the_step_summary(monkeypatch, tmp_path, caplog):
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    with caplog.at_level(logging.INFO):
        mikro_log.report("GENERAL -> Result", ["Device"], [["gw1"]])
        mikro_log.report("GENERAL -> Empty", ["Device"], [])
    assert "GENERAL -> Result\n┌" in caplog.text and "Empty" not in caplog.text
    assert summary.read_text() == "### GENERAL -> Result\n\n| Device |\n| --- |\n| gw1 |\n\n"


def test_report_without_step_summary(monkeypatch, caplog):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    with caplog.at_level(logging.INFO):
        mikro_log.report("GENERAL -> Result", ["Device"], [["gw1"]])
    assert "│ gw1    │" in caplog.text


@pytest.mark.parametrize("counts, status", [
    ({"connection": 1, "ok": 1}, "🔌 unreachable"),
    ({"error": 1, "ok": 1}, "❌ errors"),
    ({"disabled": 1}, "⏸️ disabled"),
    ({"ok": 2}, "✅ ok"),
    ({}, "➖"),
])
def test_device_status(counts, status):
    assert mikro_log.device_status(Counter(counts)) == status


def test_device_report_counts_the_records_of_every_device(tally, monkeypatch):
    for message, level in [
        ("gw1 -> Start clean", logging.INFO),
        ("gw1 -> x Found rule not at the config, removing -> {}", logging.INFO),
        ("gw1 -> A_Update needed at /ip/route", logging.INFO),
        ("gw1 -> B_Update needed at /ip/route", logging.INFO),
        ("gw1 -> Error connecting to 10.0.0.1 ---> refused", logging.WARNING),
        ("gw1 -> OK push", logging.INFO),
        ("gw2 ->--CONNECTION ERROR!->>> at IP 1.2.3.4", logging.ERROR),
    ]:
        tally.handle(record(message, level))
    reported = []
    monkeypatch.setattr(mikro_log, "report", lambda title, headers, rows: reported.append(rows))

    mikro_log.device_report("GENERAL -> Push result", ["gw1", "gw2", "gw3"])

    assert reported == [[["gw1", 1, 2, 1, 0, "✅ ok"],
                         ["gw2", 0, 0, 0, 1, "🔌 unreachable"],
                         ["gw3", 0, 0, 0, 0, "➖"]]]
