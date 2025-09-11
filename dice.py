#!/usr/bin/env python3
import random
import sys

# --- Würfelaugen als ASCII-Art ---
dice_faces = {
    1: (
        "┌─────┐",
        "│     │",
        "│  ●  │",
        "│     │",
        "└─────┘"
    ),
    2: (
        "┌─────┐",
        "│ ●   │",
        "│     │",
        "│   ● │",
        "└─────┘"
    ),
    3: (
        "┌─────┐",
        "│ ●   │",
        "│  ●  │",
        "│   ● │",
        "└─────┘"
    ),
    4: (
        "┌─────┐",
        "│ ● ● │",
        "│     │",
        "│ ● ● │",
        "└─────┘"
    ),
    5: (
        "┌─────┐",
        "│ ● ● │",
        "│  ●  │",
        "│ ● ● │",
        "└─────┘"
    ),
    6: (
        "┌─────┐",
        "│ ● ● │",
        "│ ● ● │",
        "│ ● ● │",
        "└─────┘"
    )
}

# --- Würfeln ---
def roll_dice(n=1):
    rolls = [random.randint(1, 6) for _ in range(n)]
    return rolls

# --- Würfel nebeneinander ausgeben ---
def print_dice(rolls):
    # alle Würfel auf einmal nebeneinander
    lines = [""] * 5
    for roll in rolls:
        face = dice_faces[roll]
        for i, line in enumerate(face):
            lines[i] += line + "  "  # zwei Leerzeichen dazwischen
    for line in lines:
        print(line)

# --- CLI ---
if __name__ == "__main__":
    # Anzahl der Würfel aus dem Argument, Standard 1
    try:
        n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        if n < 1:
            raise ValueError
    except ValueError:
        print("Bitte eine positive Zahl angeben, z. B.: dice 3")
        sys.exit(1)

    rolls = roll_dice(n)
    print(f"Gewürfelt: {', '.join(map(str, rolls))}\n")
    print_dice(rolls)

