import sys
import unicodedata
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


APP_NAME = "JASS Punjabi Script Explorer"
VERSION = "v1.0"

SAMPLE_GURMUKHI = "ਪੰਜਾਬੀ ਭਾਸ਼ਾ ਪੰਜਾਬ ਦੀ ਇੱਕ ਮਹੱਤਵਪੂਰਨ ਭਾਸ਼ਾ ਹੈ।"
SAMPLE_SHAHMUKHI = "پنجابی زبان پنجاب دی اک اہم زبان اے۔"


class PunjabiScriptExplorer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"{APP_NAME} {VERSION}")
        self.resize(1200, 800)

        self.gurmukhi_text = QTextEdit()
        self.shahmukhi_text = QTextEdit()

        self.gurmukhi_text.setPlainText(SAMPLE_GURMUKHI)
        self.shahmukhi_text.setPlainText(SAMPLE_SHAHMUKHI)

        self._build_ui()
        self._apply_style()
        self.update_statistics()
        self.inspect_current_text()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(18, 16, 18, 12)
        root.setSpacing(12)

        title = QLabel(f"{APP_NAME}")
        title.setObjectName("title")

        subtitle = QLabel(
            "Explore Punjabi Gurmukhi and Shahmukhi text • "
            "Unicode • statistics • search • export"
        )
        subtitle.setObjectName("subtitle")

        root.addWidget(title)
        root.addWidget(subtitle)

        # Search bar
        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search in both text panels…")
        self.search_edit.returnPressed.connect(self.search_text)

        search_button = QPushButton("🔎 Search")
        search_button.clicked.connect(self.search_text)

        clear_search = QPushButton("Clear")
        clear_search.clicked.connect(self.clear_search)

        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(search_button)
        search_row.addWidget(clear_search)
        root.addLayout(search_row)

        # Script panels
        splitter = QSplitter(Qt.Horizontal)

        gurmukhi_box = QGroupBox("Gurmukhi")
        g_layout = QVBoxLayout(gurmukhi_box)
        g_layout.addWidget(self.gurmukhi_text)

        g_buttons = QHBoxLayout()
        copy_g = QPushButton("Copy")
        copy_g.clicked.connect(
            lambda: QGuiApplication.clipboard().setText(
                self.gurmukhi_text.toPlainText()
            )
        )
        clear_g = QPushButton("Clear")
        clear_g.clicked.connect(self.gurmukhi_text.clear)
        g_buttons.addWidget(copy_g)
        g_buttons.addWidget(clear_g)
        g_layout.addLayout(g_buttons)

        shahmukhi_box = QGroupBox("Shahmukhi")
        s_layout = QVBoxLayout(shahmukhi_box)
        s_layout.addWidget(self.shahmukhi_text)

        s_buttons = QHBoxLayout()
        copy_s = QPushButton("Copy")
        copy_s.clicked.connect(
            lambda: QGuiApplication.clipboard().setText(
                self.shahmukhi_text.toPlainText()
            )
        )
        clear_s = QPushButton("Clear")
        clear_s.clicked.connect(self.shahmukhi_text.clear)
        s_buttons.addWidget(copy_s)
        s_buttons.addWidget(clear_s)
        s_layout.addLayout(s_buttons)

        splitter.addWidget(gurmukhi_box)
        splitter.addWidget(shahmukhi_box)
        splitter.setSizes([580, 580])

        root.addWidget(splitter, 2)

        # Statistics
        stats_box = QGroupBox("Text Statistics")
        stats_layout = QGridLayout(stats_box)

        self.g_chars = QLabel("0")
        self.g_words = QLabel("0")
        self.g_lines = QLabel("0")

        self.s_chars = QLabel("0")
        self.s_words = QLabel("0")
        self.s_lines = QLabel("0")

        labels = [
            ("Gurmukhi characters", self.g_chars),
            ("Gurmukhi words", self.g_words),
            ("Gurmukhi lines", self.g_lines),
            ("Shahmukhi characters", self.s_chars),
            ("Shahmukhi words", self.s_words),
            ("Shahmukhi lines", self.s_lines),
        ]

        for i, (name, value) in enumerate(labels):
            stats_layout.addWidget(QLabel(name), i // 3, (i % 3) * 2)
            stats_layout.addWidget(value, i // 3, (i % 3) * 2 + 1)

        root.addWidget(stats_box)

        # Unicode inspector
        unicode_box = QGroupBox("Unicode Inspector")
        unicode_layout = QVBoxLayout(unicode_box)

        self.unicode_label = QLabel(
            "Select text in either panel to inspect its first character."
        )

        self.unicode_table = QTableWidget(0, 4)
        self.unicode_table.setHorizontalHeaderLabels(
            ["Character", "Code Point", "Unicode Name", "Category"]
        )
        self.unicode_table.horizontalHeader().setStretchLastSection(True)
        self.unicode_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.unicode_table.setSelectionMode(QTableWidget.NoSelection)

        unicode_layout.addWidget(self.unicode_label)
        unicode_layout.addWidget(self.unicode_table)

        root.addWidget(unicode_box, 1)

        # Bottom actions
        action_row = QHBoxLayout()

        inspect = QPushButton("🔤 Inspect Unicode")
        inspect.clicked.connect(self.inspect_current_text)

        export_g = QPushButton("Export Gurmukhi")
        export_g.clicked.connect(lambda: self.export_text("gurmukhi"))

        export_s = QPushButton("Export Shahmukhi")
        export_s.clicked.connect(lambda: self.export_text("shahmukhi"))

        sample = QPushButton("Load Sample")
        sample.clicked.connect(self.load_sample)

        action_row.addWidget(inspect)
        action_row.addStretch()
        action_row.addWidget(sample)
        action_row.addWidget(export_g)
        action_row.addWidget(export_s)

        root.addLayout(action_row)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

        self.gurmukhi_text.textChanged.connect(self.update_statistics)
        self.shahmukhi_text.textChanged.connect(self.update_statistics)

        self.gurmukhi_text.cursorPositionChanged.connect(self.inspect_current_text)
        self.shahmukhi_text.cursorPositionChanged.connect(self.inspect_current_text)

    def _apply_style(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f5f7fb;
            }

            QLabel#title {
                font-size: 27px;
                font-weight: 700;
                padding-top: 2px;
            }

            QLabel#subtitle {
                color: #687385;
                font-size: 13px;
                padding-bottom: 4px;
            }

            QGroupBox {
                background: white;
                border: 1px solid #dfe4ec;
                border-radius: 10px;
                margin-top: 10px;
                padding: 12px;
                font-weight: 600;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
            }

            QTextEdit {
                background: #fbfcfe;
                border: 1px solid #d9dee7;
                border-radius: 7px;
                padding: 10px;
                font-size: 18px;
            }

            QLineEdit {
                background: white;
                border: 1px solid #d9dee7;
                border-radius: 7px;
                padding: 9px;
                font-size: 14px;
            }

            QPushButton {
                background: #ffffff;
                border: 1px solid #d3d9e3;
                border-radius: 7px;
                padding: 8px 13px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #eef3fb;
            }

            QTableWidget {
                background: #fbfcfe;
                border: 1px solid #d9dee7;
                border-radius: 6px;
                gridline-color: #e5e9ef;
            }

            QHeaderView::section {
                background: #f0f3f8;
                padding: 6px;
                border: none;
                font-weight: 600;
            }
            """
        )

        # Prefer fonts that normally have broad Indic/Arabic coverage.
        self.gurmukhi_text.setFont(QFont("Nirmala UI", 18))
        self.shahmukhi_text.setFont(QFont("Nirmala UI", 18))

    @staticmethod
    def text_stats(text):
        stripped = text.strip()
        chars = len(text)
        words = len(stripped.split()) if stripped else 0
        lines = len(text.splitlines()) if text else 0
        return chars, words, lines

    def update_statistics(self):
        g = self.text_stats(self.gurmukhi_text.toPlainText())
        s = self.text_stats(self.shahmukhi_text.toPlainText())

        self.g_chars.setText(f"{g[0]:,}")
        self.g_words.setText(f"{g[1]:,}")
        self.g_lines.setText(f"{g[2]:,}")

        self.s_chars.setText(f"{s[0]:,}")
        self.s_words.setText(f"{s[1]:,}")
        self.s_lines.setText(f"{s[2]:,}")

        self.status.showMessage(
            f"Gurmukhi: {g[1]:,} words • Shahmukhi: {s[1]:,} words"
        )

    def inspect_current_text(self):
        # Prefer the panel whose cursor is currently active.
        widget = self.gurmukhi_text
        if self.shahmukhi_text.hasFocus():
            widget = self.shahmukhi_text

        text = widget.toPlainText()
        pos = widget.textCursor().position()

        if not text:
            self.unicode_label.setText("No text to inspect.")
            self.unicode_table.setRowCount(0)
            return

        if pos >= len(text):
            pos = len(text) - 1

        start = max(0, pos - 10)
        end = min(len(text), pos + 11)
        sample = text[start:end]

        rows = []
        seen = set()

        for char in sample:
            if char.isspace() or char in seen:
                continue
            seen.add(char)
            code = f"U+{ord(char):04X}"
            try:
                name = unicodedata.name(char)
            except ValueError:
                name = "UNNAMED"
            category = unicodedata.category(char)
            rows.append((char, code, name, category))

        self.unicode_label.setText(
            f"Inspecting {len(rows)} unique non-space characters around the cursor."
        )

        self.unicode_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                self.unicode_table.setItem(r, c, QTableWidgetItem(value))

        self.unicode_table.resizeColumnsToContents()

    def search_text(self):
        query = self.search_edit.text().strip()
        if not query:
            self.status.showMessage("Enter text to search.")
            return

        found = []

        if query.casefold() in self.gurmukhi_text.toPlainText().casefold():
            found.append("Gurmukhi")

        if query.casefold() in self.shahmukhi_text.toPlainText().casefold():
            found.append("Shahmukhi")

        if found:
            self.status.showMessage(
                f"Found “{query}” in: {', '.join(found)}"
            )
        else:
            self.status.showMessage(f"“{query}” not found.")

    def clear_search(self):
        self.search_edit.clear()
        self.status.showMessage("Search cleared.")

    def load_sample(self):
        self.gurmukhi_text.setPlainText(SAMPLE_GURMUKHI)
        self.shahmukhi_text.setPlainText(SAMPLE_SHAHMUKHI)
        self.status.showMessage("Sample Punjabi text loaded.")

    def export_text(self, side):
        if side == "gurmukhi":
            text = self.gurmukhi_text.toPlainText()
            title = "Export Gurmukhi Text"
            default_name = "punjabi_gurmukhi.txt"
        else:
            text = self.shahmukhi_text.toPlainText()
            title = "Export Shahmukhi Text"
            default_name = "punjabi_shahmukhi.txt"

        path, _ = QFileDialog.getSaveFileName(
            self,
            title,
            str(Path.home() / default_name),
            "Text Files (*.txt);;All Files (*)",
        )

        if not path:
            return

        try:
            Path(path).write_text(text, encoding="utf-8")
            self.status.showMessage(f"Exported: {path}")
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Could not write the file:\n{exc}",
            )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)

    window = PunjabiScriptExplorer()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
