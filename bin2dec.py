#!/usr/bin/env python3
import sys
from decimal import Decimal, getcontext

getcontext().prec = 50

def bin2dec_steps_auto(bin_str, twos_complement=True):
    print(f"Binärzahl: {bin_str}")
    if '.' in bin_str:
        int_part_str, frac_part_str = bin_str.split('.')
    else:
        int_part_str = bin_str
        frac_part_str = ''

    int_bits = len(int_part_str)
    frac_bits = len(frac_part_str)

    print(f"Int-Teil ({int_bits} Bit): {int_part_str}")
    print(f"Frac-Teil ({frac_bits} Bit): {frac_part_str}\n")

    is_negative = twos_complement and int_part_str[0] == '1'

    # Negative Zahl: 2er-Komplement rückgängig
    if is_negative:
        print("Negative Zahl erkannt (2er-Komplement). Schritt: invertieren + 1")
        full_bin = int_part_str + frac_part_str
        inverted = ''.join('0' if b=='1' else '1' for b in full_bin)
        value = int(inverted, 2) + 1
        value = -value
        print(f"Invertiert: {inverted}")
        print(f"+1 → {abs(value)} (Skalierte Zahl)\n")
    else:
        value = int(int_part_str, 2)
        print(f"Positive Zahl. Ganzzahlwert: {value}\n")

    # Ganzzahlteil
    print("Schritt 1: Berechnung Ganzzahlteil")
    dec_int = 0
    for i, b in enumerate(reversed(int_part_str)):
        weight = 2**i
        dec_int += int(b) * weight
        print(f"Bit {int_bits-i-1} = {b} → {b}*{weight} = {int(b)*weight}")
    if is_negative:
        dec_int = -((2**int_bits) - dec_int)
    print(f"Ganzzahlteil Dezimal: {dec_int}\n")

    # Bruchteil
    print("Schritt 2: Berechnung Bruchteil")
    dec_frac = Decimal('0')
    for i, b in enumerate(frac_part_str, start=1):
        weight = Decimal('1') / (2**i)
        dec_frac += int(b) * weight
        print(f"Bit -{i} = {b} → {b}*{weight} = {int(b)*weight}")
    print(f"Bruchteil Dezimal: {dec_frac}\n")

    dec_total = Decimal(dec_int) + dec_frac
    print(f"Endergebnis Dezimal: {dec_total}")
    return dec_total

# --- CLI ---
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: bin2dec <Binärzahl>")
        sys.exit(1)

    bin_str = sys.argv[1]
    bin2dec_steps_auto(bin_str)

