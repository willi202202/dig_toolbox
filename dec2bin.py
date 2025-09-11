#!/usr/bin/env python3
import sys
from decimal import Decimal, getcontext

# Hohe Genauigkeit für Brüche
getcontext().prec = 50

def dec_to_bin_steps(number, int_bits, frac_bits):
    print(f"Dezimalzahl: {number}")
    
    neg = number < 0
    number = abs(Decimal(str(number)))
    int_part = int(number)
    frac_part = number - int_part

    # --- Schritt 1: Ganzzahlteil ---
    print("\nSchritt 1: Ganzzahl in Binär umwandeln (durch 2 teilen)")
    n = int_part
    int_bin_list = []
    if n == 0:
        int_bin_list.append('0')
        print("0 / 2 = 0 Rest 0 -> Binär: 0")
    else:
        step = 1
        while n > 0:
            q, r = divmod(n, 2)
            int_bin_list.append(str(r))
            print(f"Schritt {step}: {n} / 2 = {q} Rest {r}")
            n = q
            step += 1
    int_bin = ''.join(reversed(int_bin_list)).rjust(int_bits, '0')
    print(f"Ganzzahlteil ({int_bits} Bit): {int_bin}")

    # --- Schritt 2: Bruchteil ---
    print("\nSchritt 2: Bruchteil in Binär umwandeln (mit 2 multiplizieren)")
    frac_bin_list = []
    frac = frac_part
    for i in range(1, frac_bits+1):
        frac *= 2
        bit = int(frac)
        frac_bin_list.append(str(bit))
        frac -= Decimal(bit)
        print(f"Bit {i}: {bit} (neuer Bruchteil: {frac})")
    frac_bin = ''.join(frac_bin_list)
    print(f"Bruchteil ({frac_bits} Bit): {frac_bin}")

    # --- Schritt 3: Zusammenfügen ---
    bin_str = f"{int_bin}.{frac_bin}" if frac_bin else int_bin

    # --- Schritt 4: 2er-Komplement für negative Zahl ---
    if neg:
        total_bits = int_bits + frac_bits
        scale = 2**frac_bits
        fixed_val = int(number * scale)
        twos_val = (1 << total_bits) - fixed_val
        bin_str_twos = format(twos_val, f'0{total_bits}b')
        print("\nSchritt 3: 2er-Komplement für negative Zahl")
        print(f"Skalierte Zahl: {fixed_val}")
        print(f"2er-Komplement ({total_bits} Bit): {bin_str_twos}")
        bin_str = bin_str_twos

    print(f"\nEndergebnis Binär: {bin_str}")
    return bin_str

# --- CLI ---
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: dec2bin_step_decimal.py <Zahl> <Bits vor Komma> <Bits nach Komma>")
        sys.exit(1)

    try:
        number = float(sys.argv[1])
        int_bits = int(sys.argv[2])
        frac_bits = int(sys.argv[3])
        dec_to_bin_steps(number, int_bits, frac_bits)
    except ValueError:
        print("Ungültige Eingabe!")
        sys.exit(1)

