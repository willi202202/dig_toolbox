#!/usr/bin/env python3
import itertools
import re
import sys

# --- Hilfsfunktionen für nand / nor ---
def nand(*args):
    return not all(bool(a) for a in args)

def nor(*args):
    return not any(bool(a) for a in args)

# --- Vorverarbeitung: typos + einfache Infix -> Funktionsaufrufe ---
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
        expr = pattern.sub(lambda m: f"{m.group('op').lower()}({m.group('left')},{m.group('right')})", expr)
    return expr

# --- Variablen finden ---
def extract_variables(expr):
    tokens = re.findall(r"[A-Za-z_]\w*", expr)
    keywords = {"and", "or", "not", "true", "false", "nand", "nor"}
    variables = sorted(set(t for t in tokens if t.lower() not in keywords))
    return variables

# --- Wahrheitstabelle ---
def truth_table(expr, var_order=None):
    expr_proc = preprocess(expr)
    variables = extract_variables(expr_proc)
    
    # Falls manuelle Reihenfolge übergeben wurde → übernehmen
    if var_order:
        # prüfen, ob alle Variablen drin sind
        for v in var_order:
            if v not in variables:
                raise ValueError(f"Variable '{v}' nicht im Ausdruck gefunden.")
        # Variablen auf die gewünschte Reihenfolge setzen
        variables = var_order
    
    if not (1 <= len(variables) <= 5):
        raise ValueError("Bitte zwischen 1 und 5 Variablen verwenden.")
    
    combos = list(itertools.product([0, 1], repeat=len(variables)))
    header = "Dec " + " ".join(f"{v:>3}" for v in variables) + "   Res"
    print(header)
    print("-" * len(header))

    safe_globals = {"__builtins__": None, "nand": nand, "nor": nor, "True": True, "False": False}

    for idx, combo in enumerate(combos):
        env = dict(zip(variables, [bool(x) for x in combo]))
        try:
            result = eval(expr_proc, safe_globals, env)
            result01 = int(bool(result))
        except Exception:
            result01 = "Err"
        row = f"{idx:>3} " + " ".join(f"{x:>3}" for x in combo) + f"   {result01}"
        print(row)

# --- CLI ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Bitte Ausdruck als Argument angeben, z. B.:')
        print('  tt "(a and b) or not c" [Reihenfolge der Variablen]')
        sys.exit(1)

    expr = sys.argv[1]
    var_order = sys.argv[2:] if len(sys.argv) > 2 else None
    truth_table(expr, var_order)

