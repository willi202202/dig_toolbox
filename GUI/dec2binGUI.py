import os
import sys
import json
import math
import time
from dataclasses import dataclass
from decimal import Decimal, getcontext, InvalidOperation
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QAction, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QGroupBox, QFileDialog, QMessageBox, QStatusBar, QFrame, QMenu, QSplitter,
    QSizePolicy
)

# ------------------------------
# Config / persistence helpers
# ------------------------------

def get_config_dir() -> Path:
    home = Path.home()
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", str(home)))
        return base / "dec2bin_steps"
    return home / ".config" / "dec2bin_steps"

CONFIG_DIR = get_config_dir()
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = CONFIG_DIR / "ui_state.json"

# default decimal precision
DEFAULT_PREC = 50
getcontext().prec = DEFAULT_PREC

# ------------------------------
# Data structures
# ------------------------------
@dataclass
class IntStep:
    n: int
    q: int
    r: int
    bit: int

@dataclass
class FracStep:
    i: int
    before: Decimal
    doubled: Decimal
    bit: int
    new_frac: Decimal

@dataclass
class ComputeResult:
    ok: bool
    error: Optional[str]
    saturated: bool
    duration_ms: float
    # Steps
    int_steps: List[IntStep]
    int_bin: str
    frac_steps: List[FracStep]
    frac_bin: str
    joined_bin_with_point: str
    joined_bin_concat: str
    # two's complement (if applied)
    applied_twos: bool
    twos_bits: Optional[str]
    fixed_val: Optional[int]
    # Results
    total_bits: int
    scale: int
    hex_val: str
    recon_decimal: Decimal
    recon_error: Decimal
    min_val: Decimal
    max_val: Decimal

# ------------------------------
# Core logic
# ------------------------------

def clamp_decimal_to_range(x: Decimal, signed: bool, int_bits: int, frac_bits: int) -> tuple[Decimal, bool]:
    """
    Convention: int_bits = Bits VOR dem Komma **inklusive** Vorzeichenbit (Qm.n).
    Range (signed):   [-2^(m-1), 2^(m-1) - 2^-n]
    Range (unsigned): [0,         2^m      - 2^-n]
    """
    scale = Decimal(2) ** frac_bits
    if signed:
        min_val = - (Decimal(2) ** (int_bits - 1))
        max_val = (Decimal(2) ** (int_bits - 1)) - (Decimal(1) / scale)
    else:
        min_val = Decimal(0)
        max_val = (Decimal(2) ** int_bits) - (Decimal(1) / scale)

    saturated = False
    if x < min_val:
        x = min_val; saturated = True
    if x > max_val:
        x = max_val; saturated = True
    return x, saturated



def compute_dec_to_bin(number: Decimal, int_bits: int, frac_bits: int, use_twos_complement: bool,
                       decimal_prec: int = DEFAULT_PREC) -> ComputeResult:
    t0 = time.perf_counter()
    ctx = getcontext()
    old_prec = ctx.prec
    ctx.prec = max(decimal_prec, DEFAULT_PREC)
    try:
        neg = number < 0
        number = abs(number)

        # Clamp to range for display/range info (based on signedness option)
        signed = use_twos_complement
        clamped_abs, saturated = clamp_decimal_to_range(number if not neg else -number, signed, int_bits, frac_bits)
        if neg:
            clamped_abs = abs(clamped_abs)

        # integer part steps
        int_part = int(clamped_abs)
        n = int_part
        int_steps: List[IntStep] = []
        if n == 0:
            int_bin_list = ["0"]
        else:
            ints: List[int] = []
            while n > 0:
                q, r = divmod(n, 2)
                ints.append(r)
                int_steps.append(IntStep(n=n, q=q, r=r, bit=r))
                n = q
            ints.reverse()
            int_bin_list = [str(b) for b in ints]
        int_bin_raw = "".join(int_bin_list)
        # pad/truncate to fit int_bits
        if len(int_bin_raw) > int_bits:
            # overflow in int part -> saturate by taking lower bits (but we already clamped value)
            int_bin = int_bin_raw[-int_bits:]
        else:
            int_bin = int_bin_raw.rjust(int_bits, "0")

        # fractional part steps
        frac = clamped_abs - int(clamped_abs)
        frac_steps: List[FracStep] = []
        bits = []
        for i in range(1, frac_bits + 1):
            before = frac
            doubled = frac * 2
            bit = int(doubled)
            frac = doubled - Decimal(bit)
            bits.append(str(bit))
            frac_steps.append(FracStep(i=i, before=before, doubled=doubled, bit=bit, new_frac=frac))
        frac_bin = "".join(bits)

        # join
        with_point = f"{int_bin}.{frac_bin}" if frac_bits > 0 else int_bin
        concat = f"{int_bin}{frac_bin}"

        # apply two's complement if needed and number was negative
        applied_twos = False
        twos_bits = None
        fixed_val = None
        total_bits = int_bits + frac_bits
        scale = 1 << frac_bits

        if use_twos_complement and (neg or (clamped_abs != number)):
            applied_twos = True if neg else False
            fixed_val = int((clamped_abs * Decimal(scale)).to_integral_value(rounding=ctx.rounding))
            if neg:
                twos_val = (1 << total_bits) - fixed_val
            else:
                twos_val = fixed_val
            twos_bits = format(twos_val, f"0{total_bits}b")
            concat = twos_bits
            with_point = f"{twos_bits[:int_bits]}.{twos_bits[int_bits:]}" if frac_bits > 0 else twos_bits

        # hex from concat bits
        hex_val = hex(int(concat or "0", 2))

        # reconstruct decimal from concat bits as signed/unsigned per option
        if use_twos_complement and applied_twos and twos_bits is not None and neg:
            # interpret twos_bits back to negative value
            iv = int(twos_bits, 2)
            if iv & (1 << (total_bits - 1)):
                iv = iv - (1 << total_bits)
            recon = Decimal(iv) / Decimal(scale)
        else:
            iv = int(concat or "0", 2)
            recon = Decimal(iv) / Decimal(scale)

        # signed range info
        if use_twos_complement:
            min_val = - (Decimal(2) ** int_bits)
            max_val = (Decimal(2) ** int_bits) - (Decimal(1) / (Decimal(2) ** frac_bits))
        else:
            min_val = Decimal(0)
            max_val = (Decimal(2) ** int_bits) - (Decimal(1) / (Decimal(2) ** frac_bits))

        # true target value with sign
        target = -number if neg else number
        recon_error = recon - target

        t1 = time.perf_counter()
        return ComputeResult(
            ok=True,
            error=None,
            saturated=saturated,
            duration_ms=(t1 - t0) * 1000.0,
            int_steps=int_steps,
            int_bin=int_bin,
            frac_steps=frac_steps,
            frac_bin=frac_bin,
            joined_bin_with_point=with_point,
            joined_bin_concat=concat,
            applied_twos=applied_twos,
            twos_bits=twos_bits,
            fixed_val=fixed_val,
            total_bits=total_bits,
            scale=scale,
            hex_val=hex_val,
            recon_decimal=recon,
            recon_error=recon_error,
            min_val=min_val,
            max_val=max_val,
        )
    except (InvalidOperation, ValueError) as e:
        return ComputeResult(
            ok=False, error=str(e), saturated=False, duration_ms=0.0,
            int_steps=[], int_bin="", frac_steps=[], frac_bin="", joined_bin_with_point="",
            joined_bin_concat="", applied_twos=False, twos_bits=None, fixed_val=None,
            total_bits=int_bits + frac_bits, scale=1 << frac_bits, hex_val="0x0",
            recon_decimal=Decimal(0), recon_error=Decimal(0),
            min_val=Decimal(0), max_val=Decimal(0)
        )
    finally:
        ctx.prec = old_prec

# ------------------------------
# UI widgets
# ------------------------------
class StepsTable(QTableWidget):
    def __init__(self, columns: List[str]):
        super().__init__(0, len(columns))
        self.setHorizontalHeaderLabels(columns)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        f = QFont("Consolas,Monospace")
        f.setStyleHint(QFont.Monospace)
        self.setFont(f)

    def append_row(self, values: List[str]):
        r = self.rowCount()
        self.insertRow(r)
        for c, v in enumerate(values):
            item = QTableWidgetItem(v)
            self.setItem(r, c, item)
        self.resizeColumnsToContents()

    def clear_rows(self):
        self.setRowCount(0)

class Divider(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class Dec2BinWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Decimal → Binary (Fixpunkt) – Schritt für Schritt")
        self.resize(1100, 700)
        self.status = QStatusBar(self)
        self._build_ui()
        self._load_state()
        self._connect()

    # ---------- UI construction ----------
    def _build_ui(self):
        root = QVBoxLayout(self)

        # Top input row
        top = QHBoxLayout()
        root.addLayout(top)

        self.in_number = QLineEdit()
        self.in_number.setPlaceholderText("z. B. -13.625")
        self.in_intbits = QSpinBox(); self.in_intbits.setRange(1, 64); self.in_intbits.setValue(8)
        self.in_fracbits = QSpinBox(); self.in_fracbits.setRange(0, 64); self.in_fracbits.setValue(8)
        self.chk_signed = QCheckBox("Vorzeichen (2er-Komplement)")
        self.chk_signed.setChecked(True)
        self.btn_convert = QPushButton("Umrechnen")
        self.btn_convert.setDefault(True)
        self.btn_reset = QPushButton("Zurücksetzen")
        self.btn_examples = QPushButton("Beispiele ▾")

        # examples menu
        menu = QMenu(self)
        for label, num, ib, fb in [
            ("-13.625, 8, 8", "-13.625", 8, 8),
            ("0.1, 3, 12", "0.1", 3, 12),
            ("5.75, 4, 6", "5.75", 4, 6),
            ("-0.5, 1, 8", "-0.5", 1, 8),
        ]:
            act = QAction(label, self)
            act.triggered.connect(lambda _=False, n=num, i=ib, f=fb: self._fill_example(n, i, f))
            menu.addAction(act)
        self.btn_examples.setMenu(menu)

        def add_labeled(lbl: str, w: QWidget):
            box = QHBoxLayout()
            lab = QLabel(lbl)
            box.addWidget(lab)
            box.addWidget(w)
            container = QWidget(); container.setLayout(box)
            return container

        top.addWidget(add_labeled("Zahl", self.in_number))
        top.addWidget(add_labeled("int_bits", self.in_intbits))
        top.addWidget(add_labeled("frac_bits", self.in_fracbits))
        top.addWidget(self.chk_signed)
        top.addWidget(self.btn_convert)
        top.addWidget(self.btn_reset)
        top.addWidget(self.btn_examples)

        # hint line
        self.hint = QLabel("Darstellbarer Bereich wird nach Eingabe angezeigt.")
        self.hint.setStyleSheet("color: #555;")
        root.addWidget(self.hint)

        # splitter for tabs + side options later (kept simple now)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        # Tab: Schritte
        self.tab_steps = QWidget(); self.tabs.addTab(self.tab_steps, "Schritte")
        v = QVBoxLayout(self.tab_steps)

        # Group 1: Integer steps
        g1 = QGroupBox("Schritt 1 – Ganzzahlteil (Division durch 2)")
        v1 = QVBoxLayout(g1)
        self.tbl_int = StepsTable(["n", "q", "r", "Bit"])
        v1.addWidget(self.tbl_int)
        self.lbl_int_bin = QLabel("Ganzzahlteil: —")
        self.lbl_int_bin.setFont(QFont("Consolas,Monospace"))
        v1.addWidget(self.lbl_int_bin)
        v.addWidget(g1)

        v.addWidget(Divider())

        # Group 2: Fraction steps
        g2 = QGroupBox("Schritt 2 – Bruchteil (Multiplikation mit 2)")
        v2 = QVBoxLayout(g2)
        self.tbl_frac = StepsTable(["i", "frac", "frac*2", "Bit", "neuer frac"])
        v2.addWidget(self.tbl_frac)
        self.lbl_frac_bin = QLabel("Bruchteil: —")
        self.lbl_frac_bin.setFont(QFont("Consolas,Monospace"))
        v2.addWidget(self.lbl_frac_bin)
        v.addWidget(g2)

        v.addWidget(Divider())

        # Group 3: Join + optional two's complement
        g3 = QGroupBox("Schritt 3 – Zusammenfügen & 2er‑Komplement (falls aktiv)")
        v3 = QVBoxLayout(g3)
        self.lbl_join = QLabel("Binär (mit Punkt): —")
        self.lbl_join.setFont(QFont("Consolas,Monospace"))
        self.lbl_twos = QLabel("2er‑Komplement: —")
        self.lbl_twos.setFont(QFont("Consolas,Monospace"))

        self.btn_copy_steps = QPushButton("Schritte kopieren")
        self.btn_save_steps = QPushButton("Als Datei speichern…")
        rowbtn = QHBoxLayout()
        rowbtn.addWidget(self.btn_copy_steps)
        rowbtn.addWidget(self.btn_save_steps)
        rowbtn.addStretch(1)

        v3.addWidget(self.lbl_join)
        v3.addWidget(self.lbl_twos)
        v3.addLayout(rowbtn)
        v.addWidget(g3)

        # Tab: Ergebnisse
        self.tab_res = QWidget(); self.tabs.addTab(self.tab_res, "Ergebnisse")
        vr = QVBoxLayout(self.tab_res)

        self.lbl_bin_concat = QLabel("Binär (konkateniert): —")
        self.lbl_hex = QLabel("Hex: —")
        self.lbl_totalbits = QLabel("Gesamtbits: —; Skala: 2^—")
        self.lbl_recon = QLabel("Rekonstruiert: —; Δ: —")
        self.lbl_range = QLabel("Bereich: — … —")

        for w in [self.lbl_bin_concat, self.lbl_hex, self.lbl_totalbits, self.lbl_recon, self.lbl_range]:
            w.setFont(QFont("Consolas,Monospace"))
            vr.addWidget(w)

        self.btn_copy_bin = QPushButton("Binär kopieren")
        self.btn_copy_hex = QPushButton("Hex kopieren")
        self.btn_copy_all = QPushButton("Alles kopieren")
        r2 = QHBoxLayout(); r2.addWidget(self.btn_copy_bin); r2.addWidget(self.btn_copy_hex); r2.addWidget(self.btn_copy_all); r2.addStretch(1)
        vr.addLayout(r2)

        # bottom status
        root.addWidget(self.status)

    # ---------- connections ----------
    def _connect(self):
        self.btn_convert.clicked.connect(self.on_convert)
        self.in_number.returnPressed.connect(self.on_convert)
        self.btn_reset.clicked.connect(self.on_reset)

        self.btn_copy_steps.clicked.connect(self.copy_steps_to_clipboard)
        self.btn_save_steps.clicked.connect(self.save_steps_to_file)

        self.btn_copy_bin.clicked.connect(lambda: self.copy_text(self.lbl_bin_concat.text()))
        self.btn_copy_hex.clicked.connect(lambda: self.copy_text(self.lbl_hex.text()))
        self.btn_copy_all.clicked.connect(self.copy_all_results)

        # update hint on bit changes
        self.in_intbits.valueChanged.connect(self.update_range_hint)
        self.in_fracbits.valueChanged.connect(self.update_range_hint)
        self.chk_signed.toggled.connect(self.update_range_hint)
        self.update_range_hint()

    # ---------- helpers ----------
    def _fill_example(self, num: str, ib: int, fb: int):
        self.in_number.setText(num)
        self.in_intbits.setValue(ib)
        self.in_fracbits.setValue(fb)
        self.on_convert()

    def update_range_hint(self):
        ib = self.in_intbits.value()
        fb = self.in_fracbits.value()
        signed = self.chk_signed.isChecked()

        scale = Decimal(2) ** fbN
        if signed:
            # Qm.n mit m = int_bits (inkl. Sign)
            min_val = - (Decimal(2) ** (ib - 1))
            max_val = (Decimal(2) ** (ib - 1)) - (Decimal(1) / scale)
            rng = f"signed Q{ib}.{fb}"
        else:
            min_val = Decimal(0)
            max_val = (Decimal(2) ** ib) - (Decimal(1) / scale)
            rng = f"unsigned UQ{ib}.{fb}"

        self.hint.setText(
            f"Darstellbarer Bereich ({rng}): {min_val} … {max_val}  (Schrittweite 2^-{fb})"
        )


    def set_status(self, text: str):
        self.status.showMessage(text, 5000)

    def copy_text(self, text: str):
        # strip label prefixes like "Hex: "
        if ": " in text:
            text = text.split(": ", 1)[1]
        QGuiApplication.clipboard().setText(text)
        self.set_status("In Zwischenablage kopiert.")

    def copy_steps_to_clipboard(self):
        md = self._build_steps_markdown()
        QGuiApplication.clipboard().setText(md)
        self.set_status("Schritte (Markdown) kopiert.")

    def save_steps_to_file(self):
        md = self._build_steps_markdown()
        fn, _ = QFileDialog.getSaveFileName(self, "Schritte speichern", str(Path.home() / "dec2bin_steps.md"), "Markdown (*.md);;Text (*.txt)")
        if fn:
            try:
                Path(fn).write_text(md, encoding="utf-8")
                self.set_status(f"Gespeichert: {fn}")
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"Konnte Datei nicht speichern:\n{e}")

    def copy_all_results(self):
        parts = [
            self.lbl_join.text(),
            self.lbl_bin_concat.text(),
            self.lbl_hex.text(),
            self.lbl_totalbits.text(),
            self.lbl_recon.text(),
            self.lbl_range.text(),
        ]
        txt = "\n".join(parts)
        QGuiApplication.clipboard().setText(txt)
        self.set_status("Alle Ergebnisse kopiert.")

    def _build_steps_markdown(self) -> str:
        # gather from tables + labels
        lines = ["# Decimal → Binary – Schritte", ""]
        lines.append("## Schritt 1 – Ganzzahl (÷2)")
        lines.append("n | q | r | Bit")
        lines.append("-|-|-|-")
        for row in range(self.tbl_int.rowCount()):
            vals = [self.tbl_int.item(row, c).text() for c in range(self.tbl_int.columnCount())]
            lines.append(" | ".join(vals))
        lines.append("")
        lines.append(f"**{self.lbl_int_bin.text()}**")
        lines.append("")
        lines.append("## Schritt 2 – Bruchteil (×2)")
        lines.append("i | frac | frac*2 | Bit | neuer frac")
        lines.append("-|-|-|-|-")
        for row in range(self.tbl_frac.rowCount()):
            vals = [self.tbl_frac.item(row, c).text() for c in range(self.tbl_frac.columnCount())]
            lines.append(" | ".join(vals))
        lines.append("")
        lines.append(f"**{self.lbl_frac_bin.text()}**")
        lines.append("")
        lines.append("## Schritt 3 – Zusammen & 2er‑Komplement")
        lines.append(self.lbl_join.text())
        lines.append(self.lbl_twos.text())
        return "\n".join(lines)

    # ---------- actions ----------
    def on_reset(self):
        self.in_number.clear()
        self.in_intbits.setValue(8)
        self.in_fracbits.setValue(8)
        self.chk_signed.setChecked(True)
        self.tbl_int.clear_rows(); self.tbl_frac.clear_rows()
        for lbl in [self.lbl_int_bin, self.lbl_frac_bin, self.lbl_join, self.lbl_twos,
                    self.lbl_bin_concat, self.lbl_hex, self.lbl_totalbits, self.lbl_recon, self.lbl_range]:
            lbl.setText(lbl.text().split(":")[0] + ": —")
        self.update_range_hint()
        self.set_status("Zurückgesetzt.")

    def on_convert(self):
        text = self.in_number.text().strip()
        try:
            number = Decimal(text)
        except Exception:
            QMessageBox.warning(self, "Ungültige Zahl", "Bitte eine gültige Dezimalzahl eingeben (z. B. -13.625).")
            return
        ib = self.in_intbits.value(); fb = self.in_fracbits.value(); signed = self.chk_signed.isChecked()

        res = compute_dec_to_bin(number, ib, fb, signed, decimal_prec=DEFAULT_PREC)
        if not res.ok:
            QMessageBox.warning(self, "Fehler", f"Berechnung fehlgeschlagen:\n{res.error}")
            return

        # fill tables
        self.tbl_int.clear_rows()
        for st in res.int_steps:
            self.tbl_int.append_row([str(st.n), str(st.q), str(st.r), str(st.bit)])
        self.lbl_int_bin.setText(f"Ganzzahlteil ({ib} Bit): {res.int_bin}")

        self.tbl_frac.clear_rows()
        for st in res.frac_steps:
            self.tbl_frac.append_row([str(st.i), str(st.before), str(st.doubled), str(st.bit), str(st.new_frac)])
        self.lbl_frac_bin.setText(f"Bruchteil ({fb} Bit): {res.frac_bin}")

        self.lbl_join.setText(f"Binär (mit Punkt): {res.joined_bin_with_point}")
        self.lbl_twos.setText(f"2er‑Komplement: {res.twos_bits if res.applied_twos else '—'}")

        self.lbl_bin_concat.setText(f"Binär (konkateniert): {res.joined_bin_concat}")
        self.lbl_hex.setText(f"Hex: {res.hex_val}")
        self.lbl_totalbits.setText(f"Gesamtbits: {res.total_bits}; Skala: 2^{self.in_fracbits.value()}")
        self.lbl_recon.setText(f"Rekonstruiert: {res.recon_decimal}; Δ: {res.recon_error}")
        self.lbl_range.setText(f"Bereich: {res.min_val} … {res.max_val}")

        status_flags = []
        if res.saturated:
            status_flags.append("Sättigung")
        if res.applied_twos:
            status_flags.append("2er‑Komplement aktiv")
        status_str = ", ".join(status_flags) if status_flags else "OK"
        self.set_status(f"{status_str} – {res.duration_ms:.2f} ms")

        # persist
        self._save_state()

    # ---------- state ----------
    def _load_state(self):
        if not STATE_FILE.exists():
            return
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return
        self.in_number.setText(data.get("number", ""))
        self.in_intbits.setValue(int(data.get("int_bits", 8)))
        self.in_fracbits.setValue(int(data.get("frac_bits", 8)))
        self.chk_signed.setChecked(bool(data.get("signed", True)))

    def _save_state(self):
        data = {
            "number": self.in_number.text().strip(),
            "int_bits": self.in_intbits.value(),
            "frac_bits": self.in_fracbits.value(),
            "signed": self.chk_signed.isChecked(),
        }
        try:
            STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

# ------------------------------
# main
# ------------------------------

def main():
    app = QApplication(sys.argv)
    w = Dec2BinWindow()
    w.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
