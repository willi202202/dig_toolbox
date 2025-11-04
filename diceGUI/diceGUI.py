import os
import sys
import re
import json
import random
from pathlib import Path

from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QLineEdit, QFrame, QMessageBox, QFormLayout, QSpacerItem,
    QSizePolicy
)


# ------------------------------
# Cross‑platform config directory
# ------------------------------

def get_config_dir() -> Path:
    home = Path.home()
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("APPDATA", str(home)))
        return base / "boolean_dice"
    # Linux/macOS
    return home / ".config" / "boolean_dice"

CONFIG_DIR = get_config_dir()
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
SAVE_FILE = CONFIG_DIR / "saved_entries.json"


# ------------------------------
# Custom widgets
# ------------------------------
class DiceDot(QWidget):
    """Round indicator with center label. Colors:
    - green if value True
    - red if error True
    - gray otherwise
    """

    def __init__(self, label_text: str, parent=None):
        super().__init__(parent)
        self.value = False
        self.error = False
        self.label_text = label_text
        self.setMinimumSize(60, 60)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def sizeHint(self) -> QSize:
        return QSize(60, 60)

    def set_value(self, val: bool, error: bool = False):
        self.value = bool(val)
        self.error = bool(error)
        self.update()

    def paintEvent(self, event):
        rect = self.rect()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        radius = min(rect.width(), rect.height()) // 2 - 5
        center = rect.center()
        circle_rect = QRect(center.x() - radius, center.y() - radius, radius * 2, radius * 2)

        # Fill color
        if self.error:
            fill = QColor(220, 0, 0)
        elif self.value:
            fill = QColor(0, 170, 0)
        else:
            fill = QColor(130, 130, 130)

        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(QBrush(fill))
        painter.drawEllipse(circle_rect)

        # Label text
        painter.setPen(Qt.black)
        font = QFont()
        font.setPointSize(14)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, self.label_text)


class Histogram(QWidget):
    def __init__(self, histogram_data: dict[int, int], parent=None):
        super().__init__(parent)
        self.histogram_data = histogram_data
        self.setMinimumSize(220, 160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()

        # Background
        painter.fillRect(rect, QColor(245, 245, 245))

        # Axis margins
        left = 10
        right = 10
        top = 10
        bottom = 20

        w = rect.width() - left - right
        h = rect.height() - top - bottom
        if w <= 0 or h <= 0:
            return

        max_count = max(self.histogram_data.values()) if self.histogram_data else 1
        max_count = max(1, max_count)

        bar_w = w / 6.0
        for i in range(6):
            x = left + i * bar_w
            count = self.histogram_data.get(i + 1, 0)
            bar_h = (count / max_count) * h
            bar_rect = QRect(int(x + 5), int(top + (h - bar_h)), int(bar_w - 10), int(bar_h))

            painter.setBrush(QBrush(QColor(60, 140, 230)))
            painter.setPen(Qt.NoPen)
            painter.drawRect(bar_rect)

            # Label under bar
            painter.setPen(Qt.black)
            painter.drawText(int(x), rect.height() - bottom + 2, int(bar_w), bottom, Qt.AlignHCenter | Qt.AlignTop, str(i + 1))


# ------------------------------
# Main window
# ------------------------------
class DiceWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Boolescher Würfel (Qt)")
        self.current_values: dict[str, bool] = {}

        # Default expressions for each dice spot
        self.expressions: dict[str, str] = {
            "a": "s2",
            "b": "s2 or s1 or (not s0)",
            "c": "s2 and s1",
            "d": "s0",
            "e": "s2 and s1",
            "f": "s2 or s1 or (not s0)",
            "g": "s2",
        }

        self.histogram: dict[int, int] = {i: 0 for i in range(1, 7)}

        self._build_ui()
        self.load_entries()

    # ---------- UI ----------
    def _build_ui(self):
        root = QVBoxLayout(self)

        # Result label
        self.result_label = QLabel("Gewürfelte Zahl (dezimal): -\nGewürfelte Zahl (binär) : --- (S2 = -, S1 = -, S0 = -)")
        self.result_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(self.result_label)

        # Syntax hint
        syntax_hint = (
            "Syntax: boolsche Ausdrücke mit s2 (MSB), s1, s0 (LSB)\n"
            "Operatoren: and, or, not, +, *, !, |, &, ¬\n"
            "Klammern: ()\n"
            "Beispiele: s0, s1 and not s2, (s0 or s2) and s1, !S0 & S1"
        )
        self.syntax_label = QLabel(syntax_hint)
        self.syntax_label.setWordWrap(True)
        root.addWidget(self.syntax_label)

        # Content row: entries | dice grid | histogram
        content_row = QHBoxLayout()
        root.addLayout(content_row)

        # --- Entries ---
        self.entries: dict[str, QLineEdit] = {}
        form = QFormLayout()
        for i, spot in enumerate(["a", "b", "c", "d", "e", "f", "g"]):
            le = QLineEdit()
            le.setPlaceholderText("Ausdruck, z.B. s2 and not s1")
            self.entries[spot] = le
            form.addRow(QLabel(spot), le)

        # buttons under form
        btn_roll = QPushButton("Würfeln")
        btn_roll.clicked.connect(self.roll_dice)
        btn_show = QPushButton("Zeige Resultat")
        btn_show.clicked.connect(self.show_result)

        left_col = QVBoxLayout()
        left_col.addLayout(form)
        left_col.addWidget(btn_roll)
        left_col.addWidget(btn_show)
        left_col.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        left_wrap = QWidget()
        left_wrap.setLayout(left_col)
        content_row.addWidget(left_wrap, 0)

        # --- Dice grid ---
        grid_frame = QFrame()
        grid_frame.setFrameShape(QFrame.StyledPanel)
        grid_frame.setFrameShadow(QFrame.Sunken)
        grid_frame.setMinimumSize(220, 220)

        grid = QGridLayout(grid_frame)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        positions = {
            "a": (0, 0),
            "b": (2, 0),
            "c": (0, 1),
            "d": (1, 1),
            "e": (2, 1),
            "f": (0, 2),
            "g": (2, 2),
        }

        self.dice_spots: dict[str, DiceDot] = {}
        for spot, (col, row) in positions.items():
            dot = DiceDot(spot)
            self.dice_spots[spot] = dot
            grid.addWidget(dot, row, col)

        content_row.addWidget(grid_frame, 0, Qt.AlignTop)

        # --- Histogram ---
        self.histogram_widget = Histogram(self.histogram)
        content_row.addWidget(self.histogram_widget, 1)

        # Status label at bottom
        self.status_label = QLabel("")
        root.addWidget(self.status_label)

    # ---------- Logic ----------
    @staticmethod
    def normalize_expr(expr: str) -> str:
        # Normalize Sx -> sx and replace operators with Python boolean ops
        expr = re.sub(r"\bS([0-2])\b", r"s\1", expr, flags=re.IGNORECASE)
        expr = expr.replace("!", " not ")
        expr = expr.replace("¬", " not ")
        expr = expr.replace("*", " and ")
        expr = expr.replace("&", " and ")
        expr = expr.replace("+", " or ")
        expr = expr.replace("|", " or ")
        expr = re.sub(r"\s+", " ", expr)
        return expr.strip()

    def roll_dice(self):
        n = random.randint(1, 6)
        bin_str = f"{n:03b}"
        self.result_label.setText(
            f"Gewürfelte Zahl (dezimal): {n}\n"
            f"Gewürfelte Zahl (binär) : {bin_str} (S2 = {bin_str[0]}, S1 = {bin_str[1]}, S0 = {bin_str[2]})"
        )
        s2 = bool(n & 4)
        s1 = bool(n & 2)
        s0 = bool(n & 1)
        self.current_values = {"s0": s0, "s1": s1, "s2": s2}

        # update histogram
        self.histogram[n] += 1
        self.histogram_widget.update()

        self.update_dice_grid()

    def update_dice_grid(self):
        s0 = self.current_values.get("s0", False)
        s1 = self.current_values.get("s1", False)
        s2 = self.current_values.get("s2", False)
        syntax_errors: list[str] = []

        safe_globals = {"__builtins__": {}}
        safe_locals = {"s0": s0, "s1": s1, "s2": s2}

        for spot, line_edit in self.entries.items():
            raw = line_edit.text().strip()
            expr = self.normalize_expr(raw)
            try:
                val = bool(eval(expr or "False", safe_globals, safe_locals))
                error = False
            except Exception:
                val = False
                error = True
                syntax_errors.append(spot)
            self.dice_spots[spot].set_value(val, error)

        self.status_label.setText(
            f"Syntaxfehler in Feld: {', '.join(syntax_errors)}" if syntax_errors else ""
        )

    def show_result(self):
        s0 = self.current_values.get("s0", False)
        s1 = self.current_values.get("s1", False)
        s2 = self.current_values.get("s2", False)

        safe_globals = {"__builtins__": {}}
        safe_locals = {"s0": s0, "s1": s1, "s2": s2}

        wrong: list[str] = []
        for spot, line_edit in self.entries.items():
            raw = line_edit.text().strip()
            expr = self.normalize_expr(raw)
            try:
                user_val = eval(expr or "False", safe_globals, safe_locals)
            except Exception:
                user_val = None

            correct_val = eval(self.expressions[spot], safe_globals, safe_locals)
            if user_val != correct_val:
                wrong.append(spot)

        if wrong:
            res = QMessageBox.question(
                self,
                "Resultat anzeigen?",
                "Nicht alle Felder sind korrekt. Möchten Sie noch länger probieren?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if res == QMessageBox.No:
                # fill wrong entries with solution
                for spot in wrong:
                    self.entries[spot].setText(self.expressions[spot])
                self.update_dice_grid()
        else:
            QMessageBox.information(self, "Resultat", "Alles korrekt!")

    # ---------- Persistence ----------
    def load_entries(self):
        if SAVE_FILE.exists():
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for spot, val in data.get("entries", {}).items():
                    if spot in self.entries:
                        self.entries[spot].setText(val)
                hist = data.get("histogram", {})
                for i in range(1, 7):
                    # histogram might store keys as str
                    self.histogram[i] = int(hist.get(str(i), hist.get(i, 0)))
                self.histogram_widget.update()
            except Exception:
                pass

    def save_entries(self):
        data = {
            "entries": {spot: le.text() for spot, le in self.entries.items()},
            "histogram": self.histogram,
        }
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # Save on window close
    def closeEvent(self, event):
        self.save_entries()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    win = DiceWindow()
    win.resize(900, 480)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
