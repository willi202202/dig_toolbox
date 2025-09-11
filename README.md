# dig_toolbox

Digitaltechnik Toolbox:
--------------------------
dice     → Würfel (ASCII)                   Usage: dice [NrOfDice]
dec2bin  → Dezimal → Binär                  Usage: dec2bin <Zahl> <NrOfIntBits> <NrOfFracBits>
bin2dec  → Binär → Dezimal                  Usage: bin2dec <Bin[.Bin]>
kmap     → Karnaugh-Map                     Usage: kmap [-M] <vars> <Maxterm RowNr>
bit      → Bit Manipulation                 Usage: bit --clear 11110000 4
bool     → Minimierung / Wahrheitstabelle   Usage: tab '!A*!B*!C + !A*B*!C + A*B*!C + A*B*C' --dc 'A*!B*!C + A*!B*C' --v 'A B C' --csvfull
csv2term → Minterme & Maxterme aus Tabelle  Usage: csv2term <path_to_csv>
