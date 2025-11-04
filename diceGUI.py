import gi, random, re, os, json
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

# --- Plattformunabhängiger Speicherort für JSON ---
config_dir = os.path.join(os.path.expanduser("~"), ".config", "boolean_dice")
if os.name == "nt":  # Windows
    config_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "boolean_dice")
os.makedirs(config_dir, exist_ok=True)
SAVE_FILE = os.path.join(config_dir, "saved_entries.json")


# --- Würfel-Punkte ---
class DiceDot(Gtk.DrawingArea):
    def __init__(self, label_text):
        super().__init__()
        self.value = False
        self.error = False
        self.label_text = label_text
        self.set_size_request(60, 60)

    def set_value(self, val, error=False):
        self.value = val
        self.error = error
        self.queue_draw()

    def do_draw(self, cr):
        alloc = self.get_allocation()
        radius = min(alloc.width, alloc.height) // 2 - 5

        # Kreis zeichnen
        cr.arc(alloc.width/2, alloc.height/2, radius, 0, 2*3.14159)
        if self.error:
            cr.set_source_rgb(1, 0, 0)
        elif self.value:
            cr.set_source_rgb(0, 1, 0)
        else:
            cr.set_source_rgb(0.5, 0.5, 0.5)
        cr.fill_preserve()
        cr.set_source_rgb(0, 0, 0)
        cr.stroke()

        # Text mittig
        cr.set_source_rgb(0, 0, 0)
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(18)
        xb, yb, w, h, xa, ya = cr.text_extents(self.label_text)
        x = alloc.width/2 - w/2 - xb
        y = alloc.height/2 - h/2 - yb
        cr.move_to(x, y)
        cr.show_text(self.label_text)


# --- Histogramm der Würfelzahlen ---
class Histogram(Gtk.DrawingArea):
    def __init__(self, histogram_data):
        super().__init__()
        self.histogram_data = histogram_data
        self.set_size_request(200, 150)

    def do_draw(self, cr):
        alloc = self.get_allocation()
        width = alloc.width
        height = alloc.height
        max_count = max(self.histogram_data.values()) or 1
        bar_width = width / 6

        for i in range(6):
            x = i * bar_width
            bar_height = (self.histogram_data[i+1] / max_count) * (height - 20)
            cr.rectangle(x+5, height - bar_height - 5, bar_width-10, bar_height)
            cr.set_source_rgb(0, 0.5, 1)  # blau
            cr.fill()
            # Zahl unter Bar
            cr.set_source_rgb(0, 0, 0)
            cr.select_font_face("Sans", 0, 0)
            cr.set_font_size(12)
            text = str(i+1)
            xb, yb, w, h, xa, ya = cr.text_extents(text)
            cr.move_to(x + bar_width/2 - w/2, height - 2)
            cr.show_text(text)


# --- Hauptfenster ---
class DiceWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Boolescher Würfel")
        self.set_border_width(10)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)

        # Gewürfelte Zahl
        self.result_label = Gtk.Label()
        self.result_label.set_text(
            "Gewürfelte Zahl (dezimal): -\nGewürfelte Zahl (binär) : --- (S2 = -, S1 = -, S0 = -)"
        )
        main_box.pack_start(self.result_label, False, False, 0)

        # Syntax-Hinweis
        syntax_hint = (
            "Syntax: boolsche Ausdrücke mit s2 (MSB), s1, s0 (LSB)\n"
            "Operatoren: and, or, not, +, *, !, |, &, ¬\n"
            "Klammern: ()\n"
            "Beispiele: s0, s1 and not s2, (s0 or s2) and s1, !S0 & S1"
        )
        self.syntax_label = Gtk.Label(label=syntax_hint)
        main_box.pack_start(self.syntax_label, False, False, 0)

        # Horizontaler Bereich für Eingaben, Würfel und Histogramm
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        main_box.pack_start(content_box, False, False, 0)

        # Eingabefelder
        self.entries_grid = Gtk.Grid(row_spacing=5, column_spacing=5)
        content_box.pack_start(self.entries_grid, False, False, 0)

        self.entries = {}
        self.expressions = {
            "a": "s2",
            "b": "s2 or s1 or (not s0)",
            "c": "s2 and s1",
            "d": "s0",
            "e": "s2 and s1",
            "f": "s2 or s1 or (not s0)",
            "g": "s2"
        }

        for i, spot in enumerate(["a","b","c","d","e","f","g"]):
            label = Gtk.Label(label=spot)
            entry = Gtk.Entry()
            self.entries[spot] = entry
            self.entries_grid.attach(label, 0, i, 1, 1)
            self.entries_grid.attach(entry, 1, i, 1, 1)

        self.roll_button = Gtk.Button(label="Würfeln")
        self.roll_button.connect("clicked", self.roll_dice)
        self.entries_grid.attach(self.roll_button, 0, len(self.entries), 2, 1)

        self.show_button = Gtk.Button(label="Zeige Resultat")
        self.show_button.connect("clicked", self.show_result)
        self.entries_grid.attach(self.show_button, 0, len(self.entries)+1, 2, 1)

        # Würfel Grid
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        frame.set_size_request(220, 220)
        content_box.pack_start(frame, False, False, 0)
        self.dice_grid = Gtk.Grid(row_spacing=5, column_spacing=5)
        frame.add(self.dice_grid)

        positions = {
            "a": (0,0), "b": (2,0),
            "c": (0,1), "d": (1,1), "e": (2,1),
            "f": (0,2), "g": (2,2)
        }
        self.dice_spots = {}
        for spot, (col,row) in positions.items():
            dot = DiceDot(spot)
            self.dice_grid.attach(dot, col, row, 1, 1)
            self.dice_spots[spot] = dot

        # Histogramm
        self.histogram = {i:0 for i in range(1,7)}
        self.histogram_widget = Histogram(self.histogram)
        content_box.pack_start(self.histogram_widget, False, False, 0)

        # Statusleiste
        self.status_label = Gtk.Label(label="")
        main_box.pack_end(self.status_label, False, False, 0)

        self.current_values = {}

        # Gespeicherte Eingaben und Histogramm laden
        self.load_entries()

    # --- Ausdruck normalisieren ---
    def normalize_expr(self, expr):
        expr = re.sub(r'\bS([0-2])\b', r's\1', expr, flags=re.IGNORECASE)
        expr = expr.replace('!', ' not ')
        expr = expr.replace('¬', ' not ')
        expr = expr.replace('*', ' and ')
        expr = expr.replace('&', ' and ')
        expr = expr.replace('+', ' or ')
        expr = expr.replace('|', ' or ')
        expr = re.sub(r'\s+', ' ', expr)
        return expr.strip()

    # --- Würfeln ---
    def roll_dice(self, widget):
        n = random.randint(1,6)
        bin_str = f"{n:03b}"
        self.result_label.set_text(
            f"Gewürfelte Zahl (dezimal): {n}\n"
            f"Gewürfelte Zahl (binär) : {bin_str} (S2 = {bin_str[0]}, S1 = {bin_str[1]}, S0 = {bin_str[2]})"
        )
        s2 = bool(n & 4)
        s1 = bool(n & 2)
        s0 = bool(n & 1)
        self.current_values = {"s0": s0, "s1": s1, "s2": s2}

        # Histogramm aktualisieren
        self.histogram[n] += 1
        self.histogram_widget.queue_draw()

        self.update_dice_grid()

    # --- Würfelpunkte aktualisieren ---
    def update_dice_grid(self):
        s0 = self.current_values.get("s0", False)
        s1 = self.current_values.get("s1", False)
        s2 = self.current_values.get("s2", False)
        syntax_errors = []

        for spot, entry in self.entries.items():
            expr = self.normalize_expr(entry.get_text().strip())
            try:
                val = eval(expr, {}, {"s0": s0, "s1": s1, "s2": s2})
                error = False
            except:
                val = False
                error = True
                syntax_errors.append(spot)
            self.dice_spots[spot].set_value(val, error)

        self.status_label.set_text(
            f"Syntaxfehler in Feld: {', '.join(syntax_errors)}" if syntax_errors else ""
        )

    # --- Resultat prüfen ---
    def show_result(self, widget):
        s0 = self.current_values.get("s0", False)
        s1 = self.current_values.get("s1", False)
        s2 = self.current_values.get("s2", False)
        wrong = []

        for spot, entry in self.entries.items():
            expr = self.normalize_expr(entry.get_text().strip())
            try:
                user_val = eval(expr, {}, {"s0": s0, "s1": s1, "s2": s2})
            except:
                user_val = None
            correct_val = eval(self.expressions[spot], {}, {"s0": s0, "s1": s1, "s2": s2})
            if user_val != correct_val:
                wrong.append(spot)

        dialog = Gtk.Dialog(title="Resultat anzeigen?", parent=self, flags=0)
        dialog.set_default_size(300, 150)
        box = dialog.get_content_area()
        label_text = "Nicht alle Felder sind korrekt. Möchten Sie noch länger probieren?" if wrong else "Alles korrekt!"
        box.add(Gtk.Label(label=label_text))

        if wrong:
            btn_yes = Gtk.Button(label="JA")
            btn_yes.connect("clicked", lambda w: dialog.response(Gtk.ResponseType.YES))
            btn_no = Gtk.Button(label="NEIN")
            btn_no.connect("clicked", lambda w: dialog.response(Gtk.ResponseType.NO))
            btn_box = Gtk.Box(spacing=10)
            btn_box.pack_start(btn_yes, True, True, 0)
            btn_box.pack_start(btn_no, False, False, 0)
            box.add(btn_box)
        else:
            ok_btn = Gtk.Button(label="OK")
            ok_btn.connect("clicked", lambda w: dialog.response(Gtk.ResponseType.OK))
            box.add(ok_btn)

        dialog.show_all()
        response = dialog.run()
        dialog.destroy()

        if wrong and response == Gtk.ResponseType.NO:
            for spot in wrong:
                self.entries[spot].set_text(self.expressions[spot])

        self.update_dice_grid()

    # --- JSON Laden/Speichern ---
    def load_entries(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r") as f:
                    data = json.load(f)
                    for spot, val in data.get("entries", {}).items():
                        if spot in self.entries:
                            self.entries[spot].set_text(val)
                    for i in range(1,7):
                        self.histogram[i] = data.get("histogram", {}).get(str(i), 0)
            except:
                pass

    def save_entries(self):
        data = {
            "entries": {spot: entry.get_text() for spot, entry in self.entries.items()},
            "histogram": self.histogram
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)


# --- Programmstart ---
win = DiceWindow()
win.connect("destroy", lambda w: (w.save_entries(), Gtk.main_quit()))
win.show_all()
Gtk.main()
