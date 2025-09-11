#!/usr/bin/env python3
import itertools
import re
import sys

# --- Hilfsfunktionen für NAND / NOR ---
def nand(*args):
    return not all(bool(a) for a in args)

def nor(*args):
    return not any(bool(a) for a in args)

# --- Vorverarbeitung: Typos + Infix -> Funktionsaufrufe ---
def preprocess(expr):
    expr = re.sub(r'\bnamnd\b', 'nand', expr, flags=re.IGNORECASE)
    pattern = re.compile(
        r'(?P<left>\([^()]*\)|\b[A-Za-z_]\w*\b)\s*'
        r'(?P<op>nand|nor)\s*'
        r'(?P<right>\([^()]*\)|\b[A-Za-z_]\w*\b)',
        flags=re.IGNORECASE
    )
    prev = None
    while prev != expr:
        prev = expr
        expr = pattern.sub(
            lambda m: f"{m.group('op').lower()}({m.group('left')},{m.group('right')})",
            expr
        )
    return expr

# --- Variablen finden ---
def extract_variables(expr):
    tokens = re.findall(r"[A-Za-z_]\w*", expr)
    keywords = {"and", "or", "not", "true", "false", "nand", "nor"}
    variables = sorted(set(t for t in tokens if t.lower() not in keywords))
    return variables

# --- Hilfsfunktionen für Terme ---
def minterm_from_row(variables, row):
    return "".join(v if val else f"¬{v}" for v, val in zip(variables, row))

def maxterm_from_row(variables, row):
    parts = []
    for v, val in zip(variables, row):
        if val == 0:
            parts.append(v)
        else:
            parts.append(f"¬{v}")
    return "(" + " + ".join(parts) + ")"

# --- Analyse ---
def analyze_terms(expr, var_order=None):
    expr_proc = preprocess(expr)
    variables = extract_variables(expr_proc)
    
    # Reihenfolge anpassen, falls übergeben
    if var_order:
        for v in var_order:
            if v not in variables:
                raise ValueError(f"Variable '{v}' nicht im Ausdruck gefunden.")
        variables = var_order

    if not (1 <= len(variables) <= 5):
        raise ValueError("Bitte zwischen 1 und 5 Variablen verwenden.")

    combos = list(itertools.product([0, 1], repeat=len(variables)))
    minterms, maxterms = [], []
    min_idx, max_idx = [], []

    safe_globals = {"__builtins__": None, "nand": nand, "nor": nor, "True": True, "False": False}

    for combo in combos:
        env = dict(zip(variables, [bool(x) for x in combo]))
        try:
            result = eval(expr_proc, safe_globals, env)
            result01 = int(bool(result))
        except Exception as e:
            result01 = f"Err: {e}"

        if result01 == 1:
            minterms.append(minterm_from_row(variables, combo))
            min_idx.append(int("".join(map(str, combo)), 2))
        elif result01 == 0:
            maxterms.append(maxterm_from_row(variables, combo))
            max_idx.append(int("".join(map(str, combo)), 2))

    return variables, minterms, maxterms, min_idx, max_idx

# --- CLI ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Bitte einen booleschen Ausdruck angeben, z. B.:")
        print('   term "(a and b) or not c"')
        print('Optional: Reihenfolge der Variablen angeben (MSB → LSB)')
        print('   term "(a and b) or not c" a b c')
        sys.exit(1)

    expr = sys.argv[1]
    var_order = sys.argv[2:] if len(sys.argv) > 2 else None

    variables, minterms, maxterms, min_idx, max_idx = analyze_terms(expr, var_order)

    print(f"\nVariablen: {', '.join(variables)}")

    print("\nMinterme (DNF / Sum of Products):")
    if minterms:
        print(" + ".join(minterms))
        print(f"Indizes: m{', m'.join(map(str, min_idx))}")
    else:
        print("   Keine (Funktion ist identisch 0)")

    print("\nMaxterme (KNF / Product of Sums):")
    if maxterms:
        print(" * ".join(maxterms))
        print(f"Indizes: M{', M'.join(map(str, max_idx))}")
    else:
        print("   Keine (Funktion ist identisch 1)")

