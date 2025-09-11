#!/usr/bin/env python3
import sys

def validate_bin(b):
    if not all(c in '01' for c in b):
        print("Ungültige Binärzahl:", b)
        sys.exit(1)
    return b

def print_bitfield(b):
    n = len(b)
    # feste Breite pro Spalte (3)
    indices = " ".join(f"{i:>2}" for i in range(n-1, -1, -1))
    bits    = " ".join(f"{bit:>2}" for bit in b)
    print(f"Index:{indices}")
    print(f"Bits :{bits}\n")

def print_result(b):
    n = len(b)
    unsigned = int(b, 2)

    # Sign-Magnitude
    sign = -1 if b[0] == '1' else 1
    sign_magnitude = sign * int(b[1:], 2)

    # Zweierkomplement
    if b[0] == '1':
        twos = unsigned - (1 << n)
    else:
        twos = unsigned

    # Bit-Statistik
    ones = sum(1 for bit in b if bit == '1')
    zeros = n - ones
    lead = len(b) - len(b.lstrip('0'))
    parity = "gerade" if ones % 2 == 0 else "ungerade"

    # Bitfield anzeigen
    print_bitfield(b)

    # Tabelle mit Interpretationen
    print(f"{'Darstellung':<18} | {'Dezimal':<7} | Hexadezimal")
    print(f"{'-'*18}-+-{'-'*7}-+{'-'*12}")
    print(f"{'Unsigned':<18} | {unsigned:<7} | {hex(unsigned)}")
    print(f"{'Sign-Magnitude':<18} | {sign_magnitude:<7} | "
          f"{hex(sign_magnitude) if sign_magnitude >= 0 else '-' + hex(-sign_magnitude)}")
    print(f"{'Zweierkomplement':<18} | {twos:<7} | "
          f"{hex(twos) if twos >= 0 else '-' + hex(-twos)}")

    # Bit-Statistik
    print("\nBit-Statistik:")
    print(f"  Anzahl Bits:     {n}")
    print(f"  Gesetzte Bits:   {ones}")
    print(f"  Nullen:          {zeros}")
    print(f"  Führende Nullen: {lead}")
    print(f"  Parität:         {parity}")

# --- Operationen ---
def bin_not(b): return ''.join('1' if x=='0' else '0' for x in b)

def twos_complement(b):
    n = len(b)
    inverted = bin_not(b)
    value = int(inverted, 2) + 1
    return f"{value:0{n}b}"

def rol(b, n): n%=len(b); return b[n:]+b[:n]
def ror(b, n): n%=len(b); return b[-n:]+b[:-n]
def sll(b, n): return (b + '0'*n)[:len(b)]
def srl(b, n): return ('0'*n + b)[-len(b):]

def set_bit(b, n):
    b_list=list(b); b_list[-(n+1)]='1'; return ''.join(b_list)
def clear_bit(b, n):
    b_list=list(b); b_list[-(n+1)]='0'; return ''.join(b_list)
def toggle_bit(b, n):
    b_list=list(b); b_list[-(n+1)]='0' if b_list[-(n+1)]=='1' else '1'; return ''.join(b_list)

def reverse_bits(b): return b[::-1]
def swap_nibbles(b):
    if len(b)%8!=0: b=b.zfill(8)
    return b[4:8]+b[0:4]

# --- Main ---
if __name__ == "__main__":
    if len(sys.argv) == 2 and not sys.argv[1].startswith("--"):
        b = validate_bin(sys.argv[1])
        print_result(b)
        sys.exit(0)

    if len(sys.argv) < 3:
        print("Usage examples:")
        print("  bit <bin>                -> Analyse")
        print("  bit --not <bin>")
        print("  bit --twos <bin>")
        print("  bit --rol <bin> <n>")
        print("  bit --ror <bin> <n>")
        print("  bit --sll <bin> <n>")
        print("  bit --srl <bin> <n>")
        print("  bit --set <bin> <n>")
        print("  bit --clear <bin> <n>")
        print("  bit --toggle <bin> <n>")
        print("  bit --reverse <bin>")
        print("  bit --swap <bin>")
        print("  bit --count <bin>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "--not":
        print_result(bin_not(validate_bin(sys.argv[2])))
    elif cmd == "--twos":
        print_result(twos_complement(validate_bin(sys.argv[2])))
    elif cmd == "--rol":
        print_result(rol(validate_bin(sys.argv[2]), int(sys.argv[3])))
    elif cmd == "--ror":
        print_result(ror(validate_bin(sys.argv[2]), int(sys.argv[3])))
    elif cmd == "--sll":
        print_result(sll(validate_bin(sys.argv[2]), int(sys.argv[3])))
    elif cmd == "--srl":
        print_result(srl(validate_bin(sys.argv[2]), int(sys.argv[3])))
    elif cmd == "--set":
        print_result(set_bit(validate_bin(sys.argv[2]), int(sys.argv[3])))
    elif cmd == "--clear":
        print_result(clear_bit(validate_bin(sys.argv[2]), int(sys.argv[3])))
    elif cmd == "--toggle":
        print_result(toggle_bit(validate_bin(sys.argv[2]), int(sys.argv[3])))
    elif cmd == "--reverse":
        print_result(reverse_bits(validate_bin(sys.argv[2])))
    elif cmd == "--swap":
        print_result(swap_nibbles(validate_bin(sys.argv[2])))
    elif cmd == "--count":
        print_result(validate_bin(sys.argv[2]))
    else:
        print("Unbekannter Befehl:", cmd)

