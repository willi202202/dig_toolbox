#!/usr/bin/env python3
import argparse
import itertools
import csv
from sympy import symbols
from sympy.logic.boolalg import SOPform, POSform
# python3 tab.py 'A*B + !C' --dc 'A*!B' --v 'A B C' --csvfull

def parse_args():
    parser = argparse.ArgumentParser(description="Erzeuge eine binäre Wahrheitstabelle aus einem Booleschen Ausdruck.")
    parser.add_argument("tab", type=str, help="Hauptausdruck")
    parser.add_argument("--dc", type=str, default="", help="Don't care Ausdruck")
    parser.add_argument("--v", type=str, required=True, help="Variablen, MSB links, durch Leerzeichen getrennt")
    parser.add_argument("--csvfull", action="store_true", help="CSV-Ausgabe mit Bin, Minterm und Maxterm erweitern")
    return parser.parse_args()

def eval_expr(expr_str, var_values):
    safe_expr = expr_str.replace('!', 'not ').replace('*', ' and ').replace('+', ' or ')
    return eval(safe_expr, {}, var_values)

def minterm(values, variables):
    return "*".join(var if val else f"!{var}" for val, var in zip(values, variables))

def maxterm(values, variables):
    return "(" + "+".join(var if not val else f"!{var}" for val, var in zip(values, variables)) + ")"

def main():
    args = parse_args()
    var_names = args.v.split()
    n_vars = len(var_names)
    dc_exprs = args.dc.split('+') if args.dc else []

    # SymPy Variablen
    syms = symbols(var_names)

    # Eingaben zusammenfassen
    print("Eingaben:")
    print(f"  Variablen: {', '.join(var_names)}")
    print(f"  Ausdruck: {args.tab}")
    print(f"  Don't care: {args.dc if args.dc else 'keine'}")
    print(f"  Anzahl Variablen: {n_vars}")
    print("\nWahrheitstabelle:\n")

    # Berechne alle Zeilen und speichere F-Values
    rows = []
    ones = []
    zeros = []
    for values in itertools.product([0,1], repeat=n_vars):
        var_values = {var: bool(val) for var, val in zip(var_names, values)}
        dec_value = sum(val << (n_vars-i-1) for i, val in enumerate(values))
        bin_value = ''.join(str(val) for val in values)

        try:
            if any(eval_expr(expr_str, var_values) for expr_str in dc_exprs):
                output = "X"
            else:
                val = int(eval_expr(args.tab, var_values))
                output = str(val)
                if val == 1:
                    ones.append(values)
                elif val == 0:
                    zeros.append(values)
        except:
            output = "?"

        min_t = minterm(values, var_names)
        max_t = maxterm(values, var_names)

        # Zeilenaufbau für volle Tabelle
        row_full = [str(dec_value), bin_value] + [str(v) for v in values] + [output, min_t, max_t]
        # Zeilenaufbau für reduzierte Tabelle
        row_reduced = [str(dec_value)] + [str(v) for v in values] + [output]

        rows.append((row_full, row_reduced))

    # Header vorbereiten
    headers_full = ["Dec", "Bin"] + var_names + ["Res", "Minterm", "Maxterm"]
    headers_reduced = ["Dec"] + var_names + ["Res"]

    # Auswahl nach csvfull
    headers = headers_full if args.csvfull else headers_reduced
    rows_out = [r[0] if args.csvfull else r[1] for r in rows]

    # Tabelle drucken (immer volle Tabelle für die Konsole!)
    print_headers = headers_full
    print_rows = [r[0] for r in rows]
    col_widths = [max(len(row[i]) for row in print_rows + [print_headers]) for i in range(len(print_headers))]
    header_line = " | ".join(h.ljust(col_widths[i]) for i,h in enumerate(print_headers))
    print(header_line)
    print("-" * len(header_line))
    for row in print_rows:
        print(" | ".join(row[i].ljust(col_widths[i]) for i in range(len(print_headers))))

    # CSV schreiben
    with open("tab.csv", "w", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows_out)

    # DNF / KNF aus Tabelle (klassisch)
    dnf_terms = [minterm(v, var_names) for v in ones]
    knf_terms = [maxterm(v, var_names) for v in zeros]
    print("\nDNF (Summe der Minterme):")
    print(" + ".join(dnf_terms) if dnf_terms else "0")
    print("\nKNF (Produkt der Maxterme):")
    print(" * ".join(knf_terms) if knf_terms else "1")   

    # SymPy Minimierung
    dc_values = [values for values in itertools.product([0,1], repeat=n_vars)
                 if any(eval_expr(expr_str, dict(zip(var_names, [bool(v) for v in values]))) for expr_str in dc_exprs)]

    print("\nVektoren für SymPy:")
    print(f"  ones: {ones}")
    print(f"  zeros: {zeros}")
    print(f"  dontcares: {dc_values}")

    print("\nSymPy minimierte Ausdrücke:")
    if ones:
        min_dnf = SOPform(syms, ones, dc_values)
        min_dnf_str = str(min_dnf)
        min_dnf_str = min_dnf_str.replace("&", "*").replace("|", "+").replace("~", "!")
        print(f"Minimierte DNF: {min_dnf_str}")
    if zeros:
        min_knf = POSform(syms, zeros, dc_values)
        min_knf_str = str(min_knf)
        min_knf_str = min_knf_str.replace("&", "*").replace("|", "+").replace("~", "!")
        print(f"Minimierte KNF: {min_knf_str}")

if __name__ == "__main__":
    main()
