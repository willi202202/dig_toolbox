import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter, firwin, resample
import csv

class Channel:
    def __init__(self):
        self.time = None   # Zeitvektor
        self.data = None   # Messwerte
        self.fs = None     # Sampling rate, falls berechenbar
        self.format = "float32"  # aktuelles Datenformat
    
    def generate_test_signal(self, frequency=5.0, amplitude=1.0, offset=0.0,
                             noise_std=0.0, duration=5.0, fs=2000):
        """
        Erzeugt ein künstliches Sinussignal und speichert es in self.time und self.data.

        Parameters
        ----------
        frequency : float
            Frequenz des Sinussignals [Hz]
        amplitude : float
            Amplitude des Sinussignals
        offset : float
            DC-Offset des Signals
        noise_std : float
            Standardabweichung des additiven Gaußschen Rauschens
        duration : float
            Signaldauer in Sekunden
        fs : float
            Samplingrate in Hz
        """
        self.format = "float32"
        self.fs = fs
        self.time = np.linspace(0, duration, int(duration*fs), endpoint=False)
        self.data = amplitude * np.sin(2 * np.pi * frequency * self.time) + offset
        if noise_std > 0.0:
            self.data += np.random.randn(len(self.data)) * noise_std


    def load_data(self, time, data):
        """Messwerte aus Arrays einlesen."""
        self.time = np.array(time, dtype=float)
        self.data = np.array(data, dtype=float)
        if len(self.time) > 1:
            dt = np.mean(np.diff(self.time))
            self.fs = 1.0 / dt

    def load_csv(self, filename, skip_header=False):
        time, values = [], []
        with open(filename, "r", newline="") as f:
            reader = csv.reader(f)
            if skip_header:
                next(reader, None)
            for row in reader:
                if row:
                    time.append(float(row[0]))
                    values.append(float(row[1]))
        self.load_data(time, values)

    def save_csv(self, filename, header=False):
        if self.data is None or self.time is None:
            raise ValueError("Keine Daten vorhanden.")
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            if header:
                writer.writerow(["time", "value"])
            for t, v in zip(self.time, self.data.astype(float)):
                writer.writerow([t, v])

    # --- Resampling ---
    def resample(self, new_fs):
        if self.data is None or self.fs is None:
            raise ValueError("Keine Daten vorhanden oder fs unbekannt.")
        n_samples = int(len(self.data) * new_fs / self.fs)
        self.data = resample(self.data, n_samples)
        self.time = np.linspace(self.time[0], self.time[-1], n_samples, endpoint=False)
        self.fs = new_fs
        print(f"Resampling auf {new_fs} Hz, neue Länge {n_samples}")

    # --- Datenformat setzen ---
    def set_format(self, fmt, gain=1.0, offset=0.0):
        """
        Konvertiert self.data in float16, float32 oder signed Fixpoint Qm.n.
        Gain und Offset werden vor der Konvertierung angewendet.

        Fixpoint-Format: 'q<m>.<n>', z.B. q12.4
        """
        if self.data is None:
            raise ValueError("Keine Daten vorhanden.")

        # Gain + Offset anwenden
        data_adj = self.data * gain + offset

        # float Formate
        if fmt == "float16":
            self.data = data_adj.astype(np.float16)
        elif fmt == "float32":
            self.data = data_adj.astype(np.float32)

        # signed Fixpoint
        elif fmt.lower().startswith("q"):
            try:
                m, n = map(int, fmt[1:].split('.'))
            except Exception:
                raise ValueError("Fixpoint-Format muss 'q<m>.<n>' sein, z.B. q12.4")

            # Skaliere Daten auf integer
            scale = 2**n
            max_val = 2**(m+n) - 1  # maximaler positiver Wert
            min_val = -2**(m+n)     # minimaler negativer Wert
            data_int = np.round(data_adj * scale).astype(np.int32)
            # Clippen auf Wertebereich
            data_int = np.clip(data_int, min_val, max_val)
            self.data = data_int.astype(np.int16)  # immer 16bit intern

        else:
            raise ValueError("Unbekanntes Format")

        self.format = fmt
        print(f"Datenformat gesetzt auf {fmt} (Gain={gain}, Offset={offset})")


    # --- Filter IIR ---
    def filter_IIR(self, filter_type="lowpass", cutoff=1.0, order=4):
        if self.data is None or self.fs is None:
            raise ValueError("Keine Daten oder fs unbekannt.")
        nyq = 0.5 * self.fs
        if isinstance(cutoff, (list, tuple, np.ndarray)):
            normal_cutoff = [c / nyq for c in cutoff]
        else:
            normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype=filter_type, analog=False)
        return lfilter(b, a, self.data)

    # --- Filter FIR ---
    def filter_FIR(self, filter_type="lowpass", length=101):
        if self.data is None or self.fs is None:
            raise ValueError("Keine Daten oder fs unbekannt.")
        
        # Faustformel: cutoff abhängig von Länge
        cutoff = 0.44 * self.fs / length
        nyq = 0.5 * self.fs
        normal_cutoff = cutoff / nyq
        
        if filter_type == "lowpass":
            b = firwin(length, normal_cutoff)
        elif filter_type == "highpass":
            b = firwin(length, normal_cutoff, pass_zero=False)
        else:
            raise ValueError("FIR nur für lowpass/highpass.")
        
        filtered = lfilter(b, [1.0], self.data)
        delay = (length - 1) // 2
        return filtered, cutoff, delay

    # --- Plot ---
    def plot_data(self, filtered=None):
        if self.data is None:
            raise ValueError("Keine Daten vorhanden.")
        plt.figure(figsize=(10, 5))
        plt.plot(self.time, self.data, label=f"Daten ({self.format})")
        if filtered is not None:
            plt.plot(self.time, filtered, label="Gefiltert")
        plt.legend()
        plt.xlabel("Zeit [s]")
        plt.ylabel("Wert")
        plt.title("Messwerte")
        plt.grid(True)
        plt.show()

# Beispiel
if __name__ == "__main__":
    ch0 = Channel()
    # künstliche Testdaten
    ch0.generate_test_signal(frequency=5, amplitude=0.5, offset=0.0, noise_std=0.5, duration=5, fs=500)
    ch0.plot_data()

    ch0.resample(new_fs=200)
    ch0.plot_data()
    ch0.set_format("q4.12", gain=1.0, offset=0.0)
    ch0.plot_data()
    #ch0.set_format("q12.4", gain=1.0, offset=0.0)
    #ch0.plot_data()
    
    ch0.save_csv("messwerte.csv")
    #ch0.load_csv("messwerte.csv")

    # IIR Lowpass
    y_iir = ch0.filter_IIR("lowpass", cutoff=10, order=2)

    # FIR Highpass
    y_fir, fc, gd = ch0.filter_FIR("lowpass", length=16)
    print(f"FIR Cutoff: {fc:.2f} Hz, Group Delay: {gd} Samples")

    ch0.plot_data(filtered=y_iir)
    ch0.plot_data(filtered=y_fir)

