#!/usr/bin/env python3
import argparse
import itertools
from sympy import symbols
from sympy.logic.boolalg import SOPform, POSform

def parse_args():
    parser = argparse.ArgumentParser(description="Erzeuge eine binäre Wahrheitstabelle aus einem Booleschen Ausdruck.")
    parser.add_argument("tab", type=str, help="Hauptausdruck")
    parser.add_argument("--dc", type=str, default="", help="Don't care Ausdruck")
    parser.add_argument("--v", type=str, required=True, help="Variablen, MSB links, durch Leerzeichen getrennt")
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
        rows.append((str(dec_value), bin_value, output, min_t, max_t))

    # Tabelle drucken
    col_widths = [max(len(row[i]) for row in rows + [("Dec","Bin","F","Minterm","Maxterm")]) for i in range(5)]
    headers = ["Dec","Bin","F","Minterm","Maxterm"]
    header_line = " | ".join(h.ljust(col_widths[i]) for i,h in enumerate(headers))
    print(header_line)
    print("-" * len(header_line))
    for row in rows:
        print(" | ".join(row[i].ljust(col_widths[i]) for i in range(5)))

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
        print(f"Minimierte DNF: {min_dnf}")
    if zeros:
        min_knf = POSform(syms, zeros, dc_values)
        print(f"Minimierte KNF: {min_knf}")

if __name__ == "__main__":
    main()

