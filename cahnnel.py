import code
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter, firwin, resample
import csv
import FilterIIR as FilterIIR

class Channel:
    def __init__(self, name="DatenReihe"):
        self.name = name
        self.time = None
        self.data = None
        self.fs = None
        self.format = "float32"
        self.info = True

    # --- Daten laden ---
    def load_data(self, time, data):
        self.format = "float32"
        self.time = np.array(time, dtype=float)
        self.data = np.array(data, dtype=float)
        if len(self.time) > 1:
            self.fs = 1.0 / np.mean(np.diff(self.time))
        if self.info:
            print(f"load_data: Samples={len(self.data)}, Dauer={self.time[-1]-self.time[0]:.3f}s, fs={self.fs:.2f} Hz, Format={self.format}")

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
        if self.info:
            print(f"load_csv: '{filename}', samples={len(values)}, fs={self.fs:.2f} Hz, format={self.format}")

    def save_csv(self, filename, header=False):
        if self.data is None or self.time is None:
            raise ValueError("Keine Daten vorhanden.")
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            if header:
                writer.writerow(["time", "value"])
            for t, v in zip(self.time, self.data.astype(float)):
                writer.writerow([t, v])
        if self.info:
            print(f"save_csv: '{filename}', samples={len(self.data)}, fs={self.fs:.2f} Hz, format={self.format}")

    # --- Resampling ---
    def resample(self, new_fs):
        if self.data is None or self.fs is None:
            raise ValueError("Keine Daten oder fs unbekannt.")
        n_samples = len(self.data)
        n_samples_new = int(n_samples * new_fs / self.fs)
        self.data = resample(self.data, n_samples_new)
        self.time = np.linspace(self.time[0], self.time[-1], n_samples_new, endpoint=False)
        
        if self.info:
            print(f"resample: from {self.fs} to {new_fs} Hz, "
                  f"samples from {n_samples} to {n_samples_new}")
        self.fs = new_fs

    def q_range(self, fmt):
        if fmt.lower().startswith("q"):
            try:
                m, n = map(int, fmt[1:].split('.'))
            except Exception:
                raise ValueError("Fixpoint-Format muss 'q<m>.<n>' sein, z.B. q12.4")
            lsb = 2**(-n)
            min_val = -2**(m-1)
            max_val = 2**(m-1) - lsb
            if self.info:
                print(f"q_range: {fmt} min: {min_val} max: {max_val} LSB: {lsb} ")
            return m, n, min_val, max_val, lsb
        else:
            raise ValueError("Fixpoint-Format muss 'q<m>.<n>' sein, z.B. q12.4")
    
    def gain_offset(self, gain=1.0, offset=0.0):
        if self.data is None:
            raise ValueError("Keine Daten vorhanden.")
        self.data = self.data * gain + offset
        if self.info:
            print(f"gain_offset: gain {gain}, offset {offset} applied to data")

    def get_float32(self, dataIn=None, formatIn=None, save=False):
        """
        Konvertiert data ins float32-Array,
        unter Berücksichtigung des aktuellen Formats.
        """
        if dataIn is None:
            if self.data is None:
                raise ValueError("Keine Daten vorhanden.")
            else:
                dataIn = self.data
        if formatIn is None:
            if self.format is None:
                raise ValueError("Kein Format vorhanden.")
            else:
                formatIn = self.format
        

        if formatIn == "float32":
            dataOut =  dataIn.astype(np.float32)
        elif formatIn == "float16":
            dataOut =  dataIn.astype(np.float32)
        elif formatIn.startswith("q"):
            try:
                parts = formatIn[1:].split(".")
                int_bits = int(parts[0])
                frac_bits = int(parts[1])
            except Exception:
                raise ValueError(f"Ungültiges Q-Format: {format}")

            scale = 2**frac_bits
            dataOut = dataIn.astype(np.float32) / scale
        else:
            raise ValueError(f"Unbekanntes Format {format}")
        if self.info:
            print(f"get_float32: format dataIn: {type(dataIn[0])}, format dataOut: {formatIn}")
        if save:
            self.data = dataOut
            self.format = "float32"
    
    def get_float16(self, dataIn=None, formatIn=None, save=False):
        """
        Konvertiert self.data ins float16-Array,
        unter Berücksichtigung des aktuellen Formats.
        """
        if dataIn is None:
            if self.data is None:
                raise ValueError("Keine Daten vorhanden.")
            else:
                dataIn = self.data
        if formatIn is None:
            if self.format is None:
                raise ValueError("Kein Format vorhanden.")
            else:
                formatIn = self.format
        
        if formatIn == "float32":
            dataOut = dataIn.astype(np.float16)
        elif formatIn == "float16":
            dataOut = dataIn.astype(np.floa16)
        elif formatIn.startswith("q"):
            try:
                parts = formatIn[1:].split(".")
                int_bits = int(parts[0])
                frac_bits = int(parts[1])
            except Exception:
                raise ValueError(f"Ungültiges Q-Format: {formatIn}")

            scale = 2**frac_bits
            dataOut = dataIn.astype(np.float16) / scale
        else:
            raise ValueError(f"Unbekanntes Format {formatIn}")
        if self.info:
            print(f"get_float16: format dataIn: {type(dataIn[0])}, format dataOut: {formatIn}")
        if save:
            self.data = dataOut
            self.format = "float16"
    
    # --- Konvertiert Format ---
    def convert_format(self, dataIn=None, formatIn=None, formatOut="float32", save=False):
        """
        Konvertiert data in float32, float16 oder signed Fixpoint Qm.n.
        """
        if dataIn is None:
            if self.data is None:
                raise ValueError("Keine Daten vorhanden.")
            else:
                dataIn = self.data
        if formatIn is None:
            if self.format is None:
                raise ValueError("Kein Format vorhanden.")
            else:
                formatIn = self.format
        
        clipped_count = 0
        underflow_count = 0
        # float Formate
        if formatOut == "float16":
            dataOut = self.get_float16(dataIn, formatIn, False) 
        elif formatOut == "float32":
            dataOut = self.get_float32(dataIn, formatIn, False)
        # Fixpoint Qm.n
        elif formatOut.lower().startswith("q"):
            if formatIn.lower().startswith("q"):
                data_adj = self.get_float32(dataIn, formatIn, False)  # zuerst in float32
            else:
                data_adj = dataIn.astype(np.float32)
            
            m, n, min_val, max_val, lsb = self.q_range(formatOut)

            # Clipping-Zählung
            below = np.sum(data_adj < min_val)
            above = np.sum(data_adj > max_val)
            clipped_count = below + above
                
            data_adj = np.clip(data_adj, min_val, max_val)
            scale = 2**n
            dataOut = np.round(data_adj * scale).astype(np.int32)

            # Unterlauf-Zählung (Werte < 0.5 LSB auf 0 gerundet)
            underflow_count = np.sum((dataOut == 0) & (np.abs(data_adj) < 0.5 * lsb) & (data_adj != 0))
            
        else:
            raise ValueError("Unbekanntes Format")
        
        if self.info:
            msg = f"convert_format: format dataIn: {type(dataIn[0])}, format dataOut: {formatIn}"
            if clipped_count > 0:
                msg += f" | ⚠️ {clipped_count} cliped values"
            if underflow_count > 0:
                msg += f" | ℹ️ {underflow_count} values < 1 LSB → set to 0"
            print(msg)

        if save:
            self.data = dataOut
            self.format = formatOut
        return dataOut, formatOut
    
    # --- Testsignal erzeugen ---
    def generate_test_signal(self, frequency=5.0, amplitude=1.0, offset=0.0,
                             noise_std=0.0, duration=5.0, fs=2000,
                             formatOut="float32"):
        self.fs = fs
        self.time = np.linspace(0, duration, int(duration*fs), endpoint=False)
        self.data = amplitude * np.sin(2 * np.pi * frequency * self.time) + offset
        if noise_std > 0.0:
            self.data += np.random.randn(len(self.data)) * noise_std

        if self.info:
            print(f"generate_test_signal: "
                f"f={frequency} Hz, "
                f"A={amplitude}, "
                f"offset={offset}, "
                f"noiseStd={noise_std}, "
                f"duration={duration}s, "
                f"fs={fs} Hz, "
                f"format={formatOut}, "
                f"samples={len(self.data)}")
        
        self.convert_format(dataIn=None, formatIn=None, formatOut=formatOut, save=False)


    def plot_data(self, curves=None, label=None, reformat=False):
        if self.data is None:
            raise ValueError("Keine Daten vorhanden.")

        plt.figure(figsize=(10, 5))

        # Daten konvertieren, falls nötig
        if reformat and self.format != "float32":
            data_for_plot = self.get_float32()
        else:
            data_for_plot = self.data.astype(float)

        # Hauptdaten plotten
        plt.plot(self.time, data_for_plot, label=f"Daten ({self.format}, fs={self.fs} Hz)")

        # Zusätzliche Kurven plotten
        if curves is not None:
            curves = np.asarray(curves)  # sicherstellen, dass es ein Array ist

            if curves.ndim == 1:
                if curves.shape[0] != len(self.time):
                    raise ValueError(f"Kurve hat Länge {curves.shape[0]}, aber Zeit hat Länge {len(self.time)}.")
                lbl = label if isinstance(label, str) else "No Name"
                plt.plot(self.time, curves, label=lbl)

            elif curves.ndim == 2:
                if curves.shape[0] == len(self.time):
                    # jede Spalte ist eine Kurve
                    n_curves = curves.shape[1]
                    for i in range(n_curves):
                        if isinstance(label, (list, tuple, np.ndarray)) and len(label) == n_curves:
                            lbl = label[i]
                        else:
                            lbl = f"No Name {i}"
                        plt.plot(self.time, curves[:, i], label=lbl)

                elif curves.shape[1] == len(self.time):
                    # jede Zeile ist eine Kurve
                    n_curves = curves.shape[0]
                    for i in range(n_curves):
                        if isinstance(label, (list, tuple, np.ndarray)) and len(label) == n_curves:
                            lbl = label[i]
                        else:
                            lbl = f"No Name {i}"
                        plt.plot(self.time, curves[i, :], label=lbl)

                else:
                    raise ValueError(
                        f"Keine Dimension von curves passt zur Zeitachse (time={len(self.time)}, curves={curves.shape})."
                    )
            else:
                raise ValueError("curves muss 1D oder 2D sein.")

        plt.legend()
        plt.xlabel("Zeit [s]")
        plt.ylabel("Wert")
        plt.title(self.name)
        plt.grid(True)
        plt.show()




# Beispiel
if __name__ == "__main__":
    ch0 = Channel(name = "Messwerte")
    # künstliche Testdaten
    ch0.generate_test_signal(frequency=5, amplitude=0.5, offset=0.0, noise_std=0.5, duration=5, fs=500)
    #ch0.load_csv("meas_generated.csv")
    ch0.save_csv("meas_generated.csv")
    #ch0.plot_data()

    ch0.resample(new_fs=200)
    #ch0.plot_data()
    #ch0.gain_offset(gain=1.0, offset=0.0)
    ch0.convert_format(dataIn=None, formatIn=None, formatOut="q2.15", save=True)
    #ch0.plot_data()

    filt0 = FilterIIR.FilterIIR(fs=200.0, fc=5, order=2, btype="low", coeff_format="Q2.20")
    filt0.print_coeffs()
    #filt0.plot_response(fmin=0.01)
    filtered0 = filt0.apply_filter(ch0.data, use_quantized=True)
    #ch0.plot_data(curves=filtered0, label="Filtered Step 0", reformat=False)

    filt1 = FilterIIR.FilterIIR(fs=200.0, fc=5, order=2, btype="high", coeff_format="Q2.20")
    filt1.print_coeffs()
    #filt1.plot_response(fmin=0.01)
    filtered1 = filt1.apply_filter(filtered0, use_quantized=True)
    
    filtered2 = filt0.apply_filter(filtered1, use_quantized=True)
    filtered2 = filt1.apply_filter(filtered2, use_quantized=True)
    
    ch0.plot_data(curves=[filtered0, filtered1, filtered2], label=["Filtered Step 1","Filtered Step 2", "Filtered Step 2"], reformat=False)
    

    # ch0.save_csv("meas_filtered.csv")

    # Interaktive Konsole öffnen (mit allen Variablen im aktuellen Namespace)
    code.interact(local=locals())


