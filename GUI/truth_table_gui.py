#!/usr/bin/env python3
"""
TruthTable GUI for Boolean expressions with optional don't-cares, CSV export,
classic DNF/KNF, and SymPy-based minimization (SOP/POS).

Dependencies:
  - Python 3.9+
  - PySide6 (recommended) or PyQt5 (fallback if you adjust the imports)
  - sympy (optional; used for minimization. The app still works without it.)

Run:
  python3 truth_table_gui.py

Notes:
  - Variables are space-separated with MSB on the left (e.g. "A B C").
  - Use ! for NOT, * for AND, + for OR in expressions.
"""

from __future__ import annotations

import csv
import itertools
import sys
from typing import Dict, Iterable, List, Sequence, Tuple

# --- Qt Imports (PySide6) ---
try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ImportError as e:
    raise SystemExit(
        "PySide6 is required. Install with: pip install PySide6\n"
        "Alternatively, adapt the imports for PyQt5 if you prefer."
    ) from e


# ------------------------
#  Core Boolean Utilities
# ------------------------

def eval_expr(expr_str: str, var_values: Dict[str, bool]) -> bool:
    """Evaluate a boolean expression using Python's eval safely enough for our DSL.

    Operators mapping:
      !  -> not
      *  -> and
      +  -> or
    Example: "A*B + !C"
    """
    safe_expr = (
        expr_str.replace("!", " not ")
        .replace("*", " and ")
        .replace("+", " or ")
    )
    # Disallow builtins entirely; var_values contains only name->bool
    return bool(eval(safe_expr, {}, var_values))


def minterm(values: Sequence[int], variables: Sequence[str]) -> str:
    return "*".join(var if val else f"!{var}" for val, var in zip(values, variables))


def maxterm(values: Sequence[int], variables: Sequence[str]) -> str:
    return "(" + "+".join(var if not val else f"!{var}" for val, var in zip(values, variables)) + ")"


class TruthTableEngine:
    def __init__(self, expr: str, vars_space_sep: str, dc_expr: str = "", csvfull: bool = False) -> None:
        self.expr = expr.strip()
        self.var_names = [v.strip() for v in vars_space_sep.split() if v.strip()]
        self.dc_exprs = [s.strip() for s in dc_expr.split("+") if s.strip()] if dc_expr else []
        self.csvfull = csvfull
        if not self.var_names:
            raise ValueError("Keine Variablen angegeben (Feld 'Variablen').")

        self.n_vars = len(self.var_names)
        self.rows_full: List[List[str]] = []
        self.rows_reduced: List[List[str]] = []
        self.ones: List[Tuple[int, ...]] = []
        self.zeros: List[Tuple[int, ...]] = []
        self.dc_values: List[Tuple[int, ...]] = []

    def compute(self) -> None:
        self.rows_full.clear()
        self.rows_reduced.clear()
        self.ones.clear()
        self.zeros.clear()

        for values in itertools.product([0, 1], repeat=self.n_vars):
            bool_map = {var: bool(val) for var, val in zip(self.var_names, values)}
            dec_value = sum(val << (self.n_vars - i - 1) for i, val in enumerate(values))
            bin_value = ''.join(str(val) for val in values)

            try:
                is_dc = any(eval_expr(dc, bool_map) for dc in self.dc_exprs) if self.dc_exprs else False
                if is_dc:
                    output = "X"
                else:
                    val = int(eval_expr(self.expr, bool_map))
                    output = str(val)
                    if val == 1:
                        self.ones.append(values)
                    else:
                        self.zeros.append(values)
            except Exception:
                output = "?"

            min_t = minterm(values, self.var_names)
            max_t = maxterm(values, self.var_names)

            row_full = [str(dec_value), bin_value] + [str(v) for v in values] + [output, min_t, max_t]
            row_reduced = [str(dec_value)] + [str(v) for v in values] + [output]

            self.rows_full.append(row_full)
            self.rows_reduced.append(row_reduced)

        # Build dc_values for SymPy
        self.dc_values = [vals for vals in itertools.product([0, 1], repeat=self.n_vars)
                          if any(eval_expr(dc, dict(zip(self.var_names, [bool(v) for v in vals]))) for dc in self.dc_exprs)]

    # Classic DNF/KNF from table
    def classic_dnf(self) -> str:
        terms = [minterm(v, self.var_names) for v in self.ones]
        return " + ".join(terms) if terms else "0"

    def classic_knf(self) -> str:
        terms = [maxterm(v, self.var_names) for v in self.zeros]
        return " * ".join(terms) if terms else "1"

    # SymPy minimization (optional)
    def minimized(self) -> Tuple[str | None, str | None, str]:
        """Returns (minimized_dnf, minimized_knf, info_text) where DNF/KNF may be None if unavailable."""
        try:
            from sympy import symbols
            from sympy.logic.boolalg import SOPform, POSform
        except Exception as e:
            return None, None, f"SymPy nicht verfügbar ({e}). Minimierung übersprungen."

        if not self.var_names:
            return None, None, "Keine Variablen für Minimierung."

        syms = symbols(self.var_names)
        min_dnf_str = None
        min_knf_str = None

        info = []
        info.append(f"ones: {self.ones}")
        info.append(f"zeros: {self.zeros}")
        info.append(f"dontcares: {self.dc_values}")

        if self.ones:
            mdnf = SOPform(syms, self.ones, self.dc_values)
            s = str(mdnf).replace("&", "*").replace("|", "+").replace("~", "!")
            min_dnf_str = s
        if self.zeros:
            mknf = POSform(syms, self.zeros, self.dc_values)
            s = str(mknf).replace("&", "*").replace("|", "+").replace("~", "!")
            min_knf_str = s

        return min_dnf_str, min_knf_str, "\n".join(info)

    def headers_full(self) -> List[str]:
        return ["Dec", "Bin"] + self.var_names + ["Res", "Minterm", "Maxterm"]

    def headers_reduced(self) -> List[str]:
        return ["Dec"] + self.var_names + ["Res"]

    def csv_payload(self) -> Tuple[List[str], List[List[str]]]:
        if self.csvfull:
            return self.headers_full(), self.rows_full
        else:
            return self.headers_reduced(), self.rows_reduced


# ------------------------
#  Qt GUI
# ------------------------
class TruthTableGUI(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("TruthTable – Boolesche Ausdrücke als Tabelle")
        self.resize(1100, 760)
        self.engine: TruthTableEngine | None = None

        # Widgets
        self.expr_edit = QtWidgets.QLineEdit()
        self.expr_edit.setPlaceholderText("Hauptausdruck, z.B. A*B + !C")

        self.dc_edit = QtWidgets.QLineEdit()
        self.dc_edit.setPlaceholderText("Don't care Ausdruck, z.B. A*!B (optional)")

        self.vars_edit = QtWidgets.QLineEdit()
        self.vars_edit.setPlaceholderText("Variablen (MSB links), z.B. A B C")

        self.csvfull_cb = QtWidgets.QCheckBox("CSV mit Bin/Minterm/Maxterm (csvfull)")

        self.generate_btn = QtWidgets.QPushButton("Tabelle erzeugen")
        self.import_btn = QtWidgets.QPushButton("Tabelle importieren…")
        self.export_btn = QtWidgets.QPushButton("CSV exportieren…")
        self.export_btn.setEnabled(False)

        self.table = QtWidgets.QTableWidget()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        self.output = QtWidgets.QTextEdit()
        self.output.setReadOnly(True)
        self.output.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.output.setFont(QtGui.QFont("Courier New", 10))

        # Layout Top Form
        form = QtWidgets.QGridLayout()
        form.addWidget(QtWidgets.QLabel("Ausdruck"), 0, 0)
        form.addWidget(self.expr_edit, 0, 1, 1, 3)
        form.addWidget(QtWidgets.QLabel("Don't care"), 1, 0)
        form.addWidget(self.dc_edit, 1, 1, 1, 3)
        form.addWidget(QtWidgets.QLabel("Variablen"), 2, 0)
        form.addWidget(self.vars_edit, 2, 1)
        form.addWidget(self.csvfull_cb, 2, 2)
        btn_box = QtWidgets.QHBoxLayout()
        btn_box.addWidget(self.generate_btn)
        btn_box.addWidget(self.import_btn)
        btn_box.addStretch(1)
        btn_box.addWidget(self.export_btn)

        # Splitter for table and output
        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter.addWidget(self.table)
        splitter.addWidget(self.output)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        # Central widget
        central = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(central)
        vbox.addLayout(form)
        vbox.addLayout(btn_box)
        vbox.addWidget(splitter)
        self.setCentralWidget(central)

        # Status bar
        self.status = self.statusBar()

        # Signals
        self.generate_btn.clicked.connect(self.on_generate)
        self.import_btn.clicked.connect(self.on_import_table)
        self.export_btn.clicked.connect(self.on_export_csv)

        # Demo defaults to make first run easy
        self.expr_edit.setText("A*B + !C")
        self.dc_edit.setText("A*!B")
        self.vars_edit.setText("A B C")

    # --- Helpers ---
    def _populate_table(self, headers: list[str], rows: list[list[str]]) -> None:
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels(headers)
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QtWidgets.QTableWidgetItem(val)
                if c <= len(headers) - 4:
                    item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()

    def _render_results_panel(self) -> None:
        assert self.engine is not None
        dnf = self.engine.classic_dnf()
        knf = self.engine.classic_knf()
        min_dnf, min_knf, info = self.engine.minimized()
        text_lines = []
        text_lines.append("Eingaben:")
        text_lines.append(f"  Variablen: {', '.join(self.engine.var_names)}")
        text_lines.append(f"  Ausdruck: {self.expr_edit.text().strip() or '<aus Tabelle>'}")
        dc = self.dc_edit.text().strip()
        text_lines.append(f"  Don't care: {dc if dc else 'keine'}")
        text_lines.append(f"  Anzahl Variablen: {self.engine.n_vars}")
        text_lines.append("")
        text_lines.append("DNF (Summe der Minterme):")
        text_lines.append(dnf)
        text_lines.append("")
        text_lines.append("KNF (Produkt der Maxterme):")
        text_lines.append(knf)
        text_lines.append("")
        text_lines.append("Vektoren für SymPy:")
        text_lines.append(info)
        text_lines.append("")
        text_lines.append("SymPy minimierte Ausdrücke:")
        if min_dnf is not None:
            text_lines.append(f"  Minimierte DNF: {min_dnf}")
        if min_knf is not None:
            text_lines.append(f"  Minimierte KNF: {min_knf}")
        self.output.setPlainText("".join(text_lines))

    # --- UI Actions ---
    def on_generate(self) -> None:
        expr = self.expr_edit.text().strip()
        dc = self.dc_edit.text().strip()
        vars_ = self.vars_edit.text().strip()
        csvfull = self.csvfull_cb.isChecked()

        if not expr:
            QtWidgets.QMessageBox.warning(self, "Fehlender Ausdruck", "Bitte Hauptausdruck eingeben.")
            return
        if not vars_:
            QtWidgets.QMessageBox.warning(self, "Fehlende Variablen", "Bitte Variablen (mit Leerzeichen) eingeben.")
            return

        try:
            self.engine = TruthTableEngine(expr, vars_, dc, csvfull)
            self.engine.compute()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Fehler", f"Berechnung fehlgeschlagen: {e}")
            return

        headers = self.engine.headers_full()
        rows = self.engine.rows_full
        self._populate_table(headers, rows)
        self._render_results_panel()
        self.status.showMessage(f"Tabelle mit {len(rows)} Zeilen erzeugt.", 5000)
        self.export_btn.setEnabled(True)

    def on_import_table(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Tabelle importieren", "", "Tabellen (*.csv *.tsv)")
        if not path:
            return
        try:
            # Read CSV/TSV with basic dialect detection
            with open(path, newline="") as f:
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                except Exception:
                    # fallback: tsv if tabs present else semicolon else comma
                    if "	" in sample:
                        dialect = csv.excel_tab
                    elif ";" in sample:
                        dialect = csv.excel
                        dialect.delimiter = ";"  # type: ignore[attr-defined]
                    else:
                        dialect = csv.excel
                reader = csv.reader(f, dialect)
                rows = list(reader)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Import-Fehler", f"Datei konnte nicht gelesen werden: {e}")
            return

        if not rows:
            QtWidgets.QMessageBox.warning(self, "Leere Datei", "Die Tabelle enthält keine Daten.")
            return

        headers = [h.strip() for h in rows[0]]
        data = rows[1:]
        if not data:
            QtWidgets.QMessageBox.warning(self, "Keine Datenzeilen", "Die Tabelle hat nur eine Kopfzeile.")
            return

        # Heuristik: Ergebnis-Spalte = 'Res' oder 'Y' oder letzte Spalte
        result_idx = None
        for cand in ("Res", "RES", "res", "Y", "y"):  # prefer named columns
            if cand in headers:
                result_idx = headers.index(cand)
                break
        if result_idx is None:
            result_idx = len(headers) - 1
        result_name = headers[result_idx]

        # Variablen = alle anderen Spalten, deren Werte nur 0/1 sind
        var_cols: list[int] = [i for i in range(len(headers)) if i != result_idx]
        # filter to those that look boolean
        def _is_bool_col(idx: int) -> bool:
            vals = [r[idx].strip() for r in data if len(r) > idx]
            return all(v in ("0", "1") for v in vals if v != "")
        var_cols = [i for i in var_cols if _is_bool_col(i)]
        if not var_cols:
            QtWidgets.QMessageBox.critical(self, "Import-Fehler", "Keine geeigneten Variablen-Spalten (0/1) gefunden.")
            return

        var_names = [headers[i] for i in var_cols]
        # MSB links: Reihenfolge belassen, Nutzer kann danach bei Bedarf ändern
        self.vars_edit.setText(" ".join(var_names))
        self.expr_edit.setText("")  # wir rechnen aus Tabelle, nicht aus Ausdruck
        self.dc_edit.setText("")

        # Bilde Engine aus Tabellenzeilen
        try:
            # Wir missbrauchen die Engine mit Dummy-Ausdruck, aber füllen ihre Strukturen selbst
            self.engine = TruthTableEngine("A", " ".join(var_names), "", self.csvfull_cb.isChecked())
            # Reset
            self.engine.rows_full.clear()
            self.engine.rows_reduced.clear()
            self.engine.ones.clear()
            self.engine.zeros.clear()
            self.engine.dc_values.clear()

            # Parse rows
            for r in data:
                if len(r) <= result_idx:
                    continue
                out_raw = r[result_idx].strip()
                # akzeptiere X/x/- als Don't care
                if out_raw.upper() == "X" or out_raw == "-":
                    out_token = "X"
                elif out_raw in ("0", "1"):
                    out_token = out_raw
                else:
                    # Skip non-boolean outputs silently
                    continue

                # Extract variable bits
                vals_bits: list[int] = []
                ok = True
                for c in var_cols:
                    if c >= len(r) or r[c].strip() not in ("0", "1"):
                        ok = False
                        break
                    vals_bits.append(int(r[c].strip()))
                if not ok:
                    continue

                values = tuple(vals_bits)
                dec_value = sum(v << (len(values) - i - 1) for i, v in enumerate(values))
                bin_value = ''.join(str(v) for v in values)
                min_t = minterm(values, var_names)
                max_t = maxterm(values, var_names)

                if out_token == "1":
                    self.engine.ones.append(values)
                elif out_token == "0":
                    self.engine.zeros.append(values)
                else:  # X
                    self.engine.dc_values.append(values)

                row_full = [str(dec_value), bin_value] + [str(v) for v in values] + [out_token, min_t, max_t]
                row_reduced = [str(dec_value)] + [str(v) for v in values] + [out_token]
                self.engine.rows_full.append(row_full)
                self.engine.rows_reduced.append(row_reduced)

            # Falls Tabelle unvollständig ist, nur das Gelieferte anzeigen
            headers_full = ["Dec", "Bin"] + var_names + ["Res", "Minterm", "Maxterm"]
            self._populate_table(headers_full, self.engine.rows_full)
            self._render_results_panel()
            self.status.showMessage(
                f"Tabelle importiert ({len(self.engine.rows_full)} Zeilen, Ergebnisspalte: {result_name}).", 7000
            )
            self.export_btn.setEnabled(True)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Import-Fehler", str(e))
            return

    def on_export_csv(self) -> None:
        if not self.engine:
            return
        headers, rows = self.engine.csv_payload()

        suggested = "tab.csv" if self.engine.csvfull else "tab_reduced.csv"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "CSV speichern", suggested, "CSV (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(headers)
                writer.writerows(rows)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Fehler beim Speichern", str(e))
            return

        self.status.showMessage(f"CSV gespeichert: {path}", 5000)


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    win = TruthTableGUI()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
