#!/usr/bin/env python3
# python3 d:/Projekte_GITHub/dig_toolbox/csv2term.py d:/Projekte_GITHub/dig_toolbox/tab.csv          

import csv
import sys
import argparse

def minterm(values, variables):
    return "*".join(var if val == "1" else f"!{var}" for var, val in zip(variables, values))

def maxterm(values, variables):
    return "(" + "+".join(var if val == "0" else f"!{var}" for var, val in zip(variables, values)) + ")"

def main():
    parser = argparse.ArgumentParser(description="Extrahiere Minterme, Maxterme und Don't-care Terme aus einer CSV-Wahrheitstabelle.")
    parser.add_argument("csvfile", type=str, help="Pfad zur CSV-Datei (z.B. tab.csv)")
    args = parser.parse_args()

    # CSV einlesen
    try:
        with open(args.csvfile, newline="") as f:
            reader = csv.reader(f, delimiter=";")
            headers = next(reader)
            rows = list(reader)
    except FileNotFoundError:
        print(f"Fehler: Datei '{args.csvfile}' nicht gefunden.")
        sys.exit(1)

    # Header analysieren
    if "Res" not in headers:
        print("Fehler: CSV enthält keine 'Res'-Spalte.")
        sys.exit(1)

    var_names = [h for h in headers if h not in ("Dec", "Res", "Bin", "Minterm", "Maxterm")]
    res_idx = headers.index("Res")
    var_indices = [headers.index(v) for v in var_names]

    ones, zeros, dcs = [], [], []

    for row in rows:
        res = row[res_idx].upper()
        values = [row[i] for i in var_indices]

        if res == "1":
            ones.append(minterm(values, var_names))
        elif res == "0":
            zeros.append(maxterm(values, var_names))
        elif res in ("X", "D"):
            dcs.append(minterm(values, var_names))
        else:
            print(f"Warnung: Ungültiger Wert in 'Res'-Spalte: '{row[res_idx]}' in Zeile {row}")
            row[res_idx] = "?"  # markiert ungültigen Wert

    print("Minterme (Res=1):")
    print(" + ".join(ones) if ones else "keine")

    print("\nMaxterme (Res=0):")
    print(" * ".join(zeros) if zeros else "keine")

    print("\nDon't care Terme (Res=X oder D):")
    print(" + ".join(dcs) if dcs else "keine")

if __name__ == "__main__":
    main()
