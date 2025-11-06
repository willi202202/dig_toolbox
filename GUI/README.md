# 🎲 Boolean Dice GUI (PySide6)

Ein plattformübergreifendes GUI-Tool zum Üben von boolescher Logik – entwickelt mit **PySide6 (Qt for Python)**.  
Läuft unter **Windows** und **Linux**.

---

## 🧩 Installation

Erstelle und aktiviere eine virtuelle Umgebung:

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS
```

Installiere die benötigten Pakete:

```bash
pip install -r requirements.txt
```

Um die Umgebung wieder zu verlassen:

```bash
deactivate
```

---

## ▶️ Anwendung starten

```bash
.venv\Scripts\activate   # Windows
python diceGUI.py
```

Oder unter Linux:

```bash
source .venv/bin/activate
python diceGUI.py
```

---

## 🏗️ EXE erstellen (Windows)

Zum Erzeugen einer eigenständigen ausführbaren Datei:

```bash
pyinstaller -F -w diceGUI.py
```

Die EXE befindet sich anschließend im Ordner:

```
dist/diceGUI.exe
```

---

## 📦 Abhängigkeiten speichern

Falls du neue Pakete installierst, kannst du die Liste aktualisieren:

```bash
pip freeze > requirements.txt
```

---

## 📁 Projektstruktur

```
boolean_dice_qt/
├─ diceGUI.py
├─ requirements.txt
├─ README.md
└─ .gitignore
```

---

## ⚙️ Speicherort der Einstellungen

Die Anwendung legt Benutzereinstellungen und Statistikdaten automatisch ab:

- **Windows:** %APPDATA%\boolean_dice\saved_entries.json  
- **Linux/macOS:** ~/.config/boolean_dice/saved_entries.json

---

## 🧠 Hinweis

Dieses Projekt verwendet:
- **PySide6** für das GUI (Qt for Python)
- **PyInstaller** zum Erstellen einer EXE (optional)

---

## 📦 `requirements.txt` (empfohlener Inhalt)

```text
pyside6>=6.7
pyside6-tools>=6.7
pyinstaller>=6.0
```

