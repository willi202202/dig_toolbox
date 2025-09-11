#!/usr/bin/env python3
import sys
import itertools

GRAY = {
    1: ["0", "1"],
    2: ["00", "01", "11", "10"]
}

def sop_form(vars, minterms):
    terms = []
    n = len(vars)
    for m in minterms:
        bits = f"{m:0{n}b}"
        literals = []
        for v, b in zip(vars, bits):
            literals.append(v if b == "1" else f"!{v}")
        terms.append("(" + " & ".join(literals) + ")")
    return " | ".join(terms)

def pos_form(vars, minterms):
    n = len(vars)
    all_indices = set(range(2**n))
    maxterms = sorted(all_indices - set(minterms))

    terms = []
    for m in maxterms:
        bits = f"{m:0{n}b}"
        literals = []
        for v, b in zip(vars, bits):
            literals.append(v if b == "0" else f"!{v}")
        terms.append("(" + " | ".join(literals) + ")")
    return " & ".join(terms)

def print_kmap(vars, minterms):
    n = len(vars)
    if n == 2:
        row_vars, col_vars = [vars[0]], [vars[1]]
    elif n == 3:
        row_vars, col_vars = [vars[0]], [vars[1], vars[2]]
    elif n == 4:
        row_vars, col_vars = [vars[0], vars[1]], [vars[2], vars[3]]
    else:
        print("Nur 2 bis 4 Variablen unterstützt.")
        return

    rows = GRAY[len(row_vars)]
    cols = GRAY[len(col_vars)]

    print("\nKarnaugh-Map für Variablen:", " ".join(vars))
    print("Zeilen:", " ".join(row_vars))
    print("Spalten:", " ".join(col_vars))
    print("Minterme:", minterms, "\n")

    kmap = {}
    for r, rv in enumerate(rows):
        for c, cv in enumerate(cols):
            bits = rv + cv
            idx = int(bits, 2)
            kmap[(r,c)] = 1 if idx in minterms else 0

    cell_width = 3
    header = " " * (len(row_vars) + 3)
    for cv in cols:
        header += cv.rjust(cell_width)
    print(header)

    for r, rv in enumerate(rows):
        line = rv.ljust(len(row_vars) + 2) + "|"
        for c in range(len(cols)):
            line += str(kmap[(r,c)]).rjust(cell_width)
        print(line)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Usage: kmap [-M] "<vars>" "<terms>"')
        sys.exit(1)

    use_max = False
    args = sys.argv[1:]

    if args[0] in ("-M", "--max"):
        use_max = True
        args = args[1:]

    vars = args[0].split()
    terms = list(map(int, args[1].split(',')))
    n = len(vars)

    if use_max:
        # Maxterme angegeben → in Minterme umwandeln
        all_indices = set(range(2**n))
        minterms = sorted(all_indices - set(terms))
    else:
        minterms = terms

    print_kmap(vars, minterms)

    sop = sop_form(vars, minterms)
    pos = pos_form(vars, minterms)

    print("\nEinfache Minterm-Darstellung (SOP, Sum of Products):")
    print(sop)

    print("\nEinfache Maxterm-Darstellung (POS, Product of Sums):")
    print(pos)

