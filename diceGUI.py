import gi, random
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

class DiceDot(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.value = False
        self.set_size_request(60, 60)  # Quadratgröße

    def set_value(self, val):
        self.value = val
        self.queue_draw()  # neu zeichnen

    def do_draw(self, cr):
        alloc = self.get_allocation()
        radius = min(alloc.width, alloc.height) // 2 - 5
        cr.arc(alloc.width/2, alloc.height/2, radius, 0, 2*3.14159)
        if self.value:
            cr.set_source_rgb(0, 1, 0)  # grün
        else:
            cr.set_source_rgb(0.5, 0.5, 0.5)  # grau
        cr.fill()

class DiceWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Boolescher Würfel")
        self.set_border_width(10)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)

        # Gewürfelte Zahl
        self.result_label = Gtk.Label(label="Gewürfelte Zahl: -")
        main_box.pack_start(self.result_label, False, False, 0)

        # Syntax-Hinweis
        syntax_hint = (
            "Syntax: boolsche Ausdrücke mit x0, x1, x2\n"
            "Operatoren: and, or, not\n"
            "Beispiele: x0, x1 and not x2, x0 or x2"
        )
        self.syntax_label = Gtk.Label(label=syntax_hint)
        main_box.pack_start(self.syntax_label, False, False, 0)

        # Horizontaler Bereich für Eingaben und Würfel
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        main_box.pack_start(content_box, False, False, 0)

        # Eingabefelder
        self.entries_grid = Gtk.Grid(row_spacing=5, column_spacing=5)
        content_box.pack_start(self.entries_grid, False, False, 0)

        self.entries = {}
        self.expressions = {
            "a": "x2",
            "b": "x2 or x1 or (not x0)",
            "c": "x2 and x1 and (not x0)",
            "d": "x0",
            "e": "x2 and x1 and (not x0)",
            "f": "x2 or x1 or (not x0)",
            "g": "x2"
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

        # Würfel Grid mit quadratischem Rahmen
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        frame.set_size_request(220, 220)  # Quadrat
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
            dot = DiceDot()
            self.dice_grid.attach(dot, col, row, 1, 1)
            self.dice_spots[spot] = dot

        self.current_values = {}

    def roll_dice(self, widget):
        n = random.randint(1,6)
        self.result_label.set_text(f"Gewürfelte Zahl: {n}")
        x0 = bool(n & 1)
        x1 = bool(n & 2)
        x2 = bool(n & 4)
        self.current_values = {"x0": x0, "x1": x1, "x2": x2}
        self.update_dice_grid()

    def update_dice_grid(self):
        x0 = self.current_values.get("x0", False)
        x1 = self.current_values.get("x1", False)
        x2 = self.current_values.get("x2", False)
        for spot, entry in self.entries.items():
            expr = entry.get_text().strip()
            try:
                val = eval(expr, {}, {"x0": x0, "x1": x1, "x2": x2})
            except:
                val = False
            self.dice_spots[spot].set_value(val)

    def show_result(self, widget):
        x0 = self.current_values.get("x0", False)
        x1 = self.current_values.get("x1", False)
        x2 = self.current_values.get("x2", False)

        # Prüfen, welche Felder falsch sind
        wrong = []
        for spot, entry in self.entries.items():
            expr = entry.get_text().strip()
            try:
                user_val = eval(expr, {}, {"x0": x0, "x1": x1, "x2": x2})
            except:
                user_val = None
            correct_val = eval(self.expressions[spot], {}, {"x0": x0, "x1": x1, "x2": x2})
            if user_val != correct_val:
                wrong.append(spot)

        # Infofenster
        dialog = Gtk.Dialog(title="Resultat anzeigen?", parent=self, flags=0)
        dialog.set_default_size(300, 150)
        box = dialog.get_content_area()

        label_text = "Nicht alle Felder sind korrekt. Möchten Sie noch länger probieren?" if wrong else "Alles korrekt!"
        label = Gtk.Label(label=label_text)
        box.add(label)

        # Buttons nur bei Fehlern
        if wrong:
            btn_yes = Gtk.Button(label="JA")
            btn_yes.set_size_request(200, 80)  # sehr großer Button
            btn_yes.connect("clicked", lambda w: dialog.response(Gtk.ResponseType.YES))
            btn_no = Gtk.Button(label="NEIN")
            btn_no.set_size_request(80, 40)   # sehr kleiner Button
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
            # Korrigiere falsche Felder
            for spot in wrong:
                self.entries[spot].set_text(self.expressions[spot])

        self.update_dice_grid()

win = DiceWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
