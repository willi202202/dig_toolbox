import code
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.signal import lfilter

class FilterIIR:
    def __init__(self, fs, fc, order=1, btype="low", coeff_format="Q1.15"):
        self.fs = fs
        self.fc = fc
        self.order = order
        self.btype = btype
        self.coeff_format = coeff_format
        self.m, self.n = None, None
        self.a_overflow = []
        self.a_underflow = []
        self.b_overflow = []
        self.b_underflow = []
        self.design()

    def quantize(self, coeffs):
        """ Quantize coefficients to fixed-point format """
        if not self.coeff_format.startswith("Q"):
            raise ValueError("Format muss 'Qm.n' sein, z.B. 'Q1.15'")
        self.m, self.n = map(int, self.coeff_format[1:].split("."))
        word_bits = self.m + self.n
        scale = 1 << self.n
        min_val = -(1 << (word_bits - 1))
        max_val = (1 << (word_bits - 1)) - 1
        lsb = 1.0 / scale

        ints = []
        q_overflow = []
        q_underflow = []

        for c in coeffs:
            val = int(round(c * scale))
            overflow = False
            underflow = False

            if val > max_val:
                overflow = True
                val = max_val
            elif val < min_val:
                overflow = True
                val = min_val
            elif abs(val) < 1 and c != 0.0:
                underflow = True  # kleiner als 1 LSB

            ints.append(val)
            q_overflow.append(overflow)
            q_underflow.append(underflow)

        return ints, q_overflow, q_underflow

    def design(self):
        """ Design and quantize filter coefficients """
        b, a = signal.butter(
            self.order,
            self.fc / (self.fs / 2),
            btype=self.btype,
            analog=False
        )

        # Normalisieren auf a0 = 1
        #b = b / a[0]
        #a = a / a[0]

        self.b_float = b
        self.a_float = a

        # Quantisieren: alle b, aber nur a1..aN
        self.b_q, self.b_overflow, self.b_underflow = self.quantize(self.b_float)
        self.a_q, self.a_overflow, self.a_underflow = self.quantize(self.a_float)
        return any(self.b_overflow) or any(self.a_overflow) or any(self.b_underflow) or any(self.a_underflow)

    def print_coeffs(self):
        """ Print filter coefficients with hex output """
        m, n = self.m, self.n
        word_bits = m + n
        hex_digits = (word_bits + 3) // 4  # volle Hexstellen

        def to_hex(val):
            return format(val & ((1 << word_bits) - 1), f"#0{hex_digits+2}X")

        print(f"fs = {self.fs} Hz")
        print(f"fc = {self.fc} Hz")
        print(f"order = {self.order}")
        print(f"btype = {self.btype}")
        print(f"coeff_format = {self.coeff_format} (Q{m}.{n})")

        print("b_float =", [f"{c:.6f}" for c in self.b_float])
        print("a_float =", [f"{c:.6f}" for c in self.a_float])

        print("b_int =", [f"{c}" for c in self.b_q])
        print("a_int =", [f"{c}" for c in self.a_q])

        print("b_hex =", [to_hex(c) for c in self.b_q])
        print("a_hex =", [to_hex(c) for c in self.a_q])

        print("overflow b:", self.b_overflow)
        print("underflow b:", self.b_underflow)
        print("overflow a:", self.a_overflow)
        print("underflow b:", self.a_underflow)

        sum = any(self.b_overflow) or any(self.a_overflow) or any(self.b_underflow) or any(self.a_underflow)
        print("error summary:", sum)
        return sum

    def plot_response(self, fmin=0.1, minDB=-60, maxDB=5):
        """ Plot frequency response (Amplitude + Phase) """
        w, h_float = signal.freqz(self.b_float, self.a_float, worN=200000, fs=self.fs)
        _, h_q = signal.freqz(self.b_q, self.a_q, worN=200000, fs=self.fs)

        plt.figure(figsize=(10, 6))
        
        # Amplitude
        plt.subplot(2, 1, 1)
        plt.semilogx(w, 20 * np.log10(np.abs(h_float)), label="Float")
        plt.semilogx(w, 20 * np.log10(np.abs(h_q)), "--", label=f"Fixed-point {self.coeff_format}")
        plt.axvline(self.fc, color="red", linestyle=":", label=f"fc = {self.fc} Hz")
        plt.xlim([fmin, self.fs / 2])
        plt.ylim([minDB, maxDB])
        plt.ylabel("Amplitude [dB]")
        plt.title(f"Frequency Response of {self.order}-Order {self.btype.title()}-Pass Filter")
        plt.grid(which="both", linestyle="--", alpha=0.7)
        plt.legend()

        # Phase
        plt.subplot(2, 1, 2)
        plt.semilogx(w, np.angle(h_float, deg=True), label="Float")
        plt.semilogx(w, np.angle(h_q, deg=True), "--", label=f"Fixed-point {self.coeff_format}")
        plt.axvline(self.fc, color="red", linestyle=":")
        plt.xlim([fmin, self.fs / 2])
        plt.ylabel("Phase [degrees]")
        plt.xlabel("Frequency [Hz]")
        plt.grid(which="both", linestyle="--", alpha=0.7)
        plt.legend()

        plt.tight_layout()
        plt.show()

    
    def plot_group_delay(self, fmin=0.1):
        """ Plot group delay in samples and seconds """
        # Gruppenlaufzeit in Samples
        w, gd_float = signal.group_delay((self.b_float, self.a_float))
        _, gd_q = signal.group_delay((self.b_q, self.a_q))

        # rad/sample -> Hz
        f = w * self.fs / (2*np.pi)
        
        # Gruppenlaufzeit in Sekunden
        Ts = 1 / self.fs
        gd_float_s = gd_float * Ts
        gd_q_s = gd_q * Ts

        plt.figure(figsize=(8, 5))
        ax1 = plt.gca()
        
        # Plot in Samples
        ax1.semilogx(f, gd_float, label="Float [samples]")
        ax1.semilogx(f, gd_q, "--", label=f"Fixed-point {self.coeff_format} [samples]")
        ax1.set_xlabel("Frequency [Hz]")
        ax1.set_ylabel("Group delay [samples]")
        ax1.set_xlim([fmin, self.fs / 2])
        ax1.grid(which="both", linestyle="--", alpha=0.7)

        # Sekunden-Achse
        ax2 = ax1.twinx()
        ax2.semilogx(f, gd_float_s, color='blue', alpha=0)  # nur Achse sichtbar
        ax2.set_ylabel("Group delay [s]")

        # vertikale Linie bei fc
        ax1.axvline(self.fc, color="red", linestyle=":", label=f"fc = {self.fc} Hz")
        
        # Legende
        ax1.legend()
        plt.title(f"Group Delay of {self.order}-Order {self.btype.title()}-Pass Filter")
        plt.tight_layout()
        plt.show()

    def plot_quantization_error(self, fmin=0.1, ymin_mag=None, ymax_mag=None, ymin_phase=None, ymax_phase=None):
        """ Plot Quantisierungsfehler im Frequenzgang """
        # Frequenzantworten
        w, h_float = signal.freqz(self.b_float, self.a_float, worN=200000, fs=self.fs)
        _, h_q     = signal.freqz(self.b_q, self.a_q, worN=200000, fs=self.fs)

        # Fehler berechnen
        error_mag_db = 20 * np.log10(np.abs(h_float) / np.abs(h_q))
        error_phase = np.rad2deg(np.angle(h_float) - np.angle(h_q))
        error_mag_abs = np.abs(np.abs(h_float) - np.abs(h_q))  # Absolutwert linear

        plt.figure(figsize=(10, 6))
        
        # --- Amplitudenfehler ---
        ax1 = plt.subplot(2, 1, 1)
        ax1.semilogx(w, error_mag_db, label="Error [dB]")
        ax1.axvline(self.fc, color="red", linestyle=":", label=f"fc = {self.fc} Hz")
        ax1.set_xlim([fmin, self.fs/2])
        if ymin_mag is not None and ymax_mag is not None:
            ax1.set_ylim([ymin_mag, ymax_mag])
        ax1.set_ylabel("Amplitude Error [dB]")
        ax1.set_title("Quantisierungsfehler im Frequenzgang")
        ax1.grid(which="both", linestyle="--", alpha=0.7)
        ax1.legend(loc="upper left")

        # Zweite Achse für Absolutwert
        ax2 = ax1.twinx()
        ax2.semilogx(w, error_mag_abs, color='orange', alpha=0.7, label="Error [abs]")
        ax2.set_ylabel("Amplitude Error [linear]")
        ax2.legend(loc="upper right")

        # --- Phasenfehler ---
        ax3 = plt.subplot(2, 1, 2)
        ax3.semilogx(w, error_phase)
        ax3.axvline(self.fc, color="red", linestyle=":")
        ax3.set_xlim([fmin, self.fs/2])
        if ymin_phase is not None and ymax_phase is not None:
            ax3.set_ylim([ymin_phase, ymax_phase])
        ax3.set_ylabel("Phase Error [degrees]")
        ax3.set_xlabel("Frequency [Hz]")
        ax3.grid(which="both", linestyle="--", alpha=0.7)

        plt.tight_layout()
        plt.show()

    def plot_impulse_and_step_response(self, n_samples=200):
        """ Plot impulse and step response of the filter. """
        import numpy as np
        import matplotlib.pyplot as plt

        # Impuls: δ[n]
        impulse = np.zeros(n_samples)
        impulse[0] = 1.0

        # Schritt: u[n]
        step = np.ones(n_samples)

        # Float-Filter
        y_impulse_float = self.apply_filter(impulse, use_quantized=False)
        y_step_float    = self.apply_filter(step, use_quantized=False)

        # Quantisierter Filter
        y_impulse_q = self.apply_filter(impulse, use_quantized=True)
        y_step_q    = self.apply_filter(step, use_quantized=True)

        # Plot
        fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

        # Impulsantwort
        axes[0].stem(y_impulse_float, linefmt="C0-", markerfmt="C0o", basefmt="k-", label="Float")
        axes[0].stem(y_impulse_q, linefmt="C1--", markerfmt="C1x", basefmt="k-", label=f"Fixed-point {self.coeff_format}")
        axes[0].set_ylabel("Amplitude")
        axes[0].set_title("Impulse Response")
        axes[0].grid(True, linestyle="--", alpha=0.7)
        axes[0].legend()

        # Sprungantwort
        axes[1].plot(y_step_float, "C0-", label="Float")
        axes[1].plot(y_step_q, "C1--", label=f"Fixed-point {self.coeff_format}")
        axes[1].set_xlabel("Samples")
        axes[1].set_ylabel("Amplitude")
        axes[1].set_title("Step Response")
        axes[1].grid(True, linestyle="--", alpha=0.7)
        axes[1].legend()

        plt.tight_layout()
        plt.show()



    def apply_filter(self, x, use_quantized=False):
        """ Apply the filter to input signal """
        if use_quantized:
            if self.b_q is None or self.a_q is None:
                raise RuntimeError("Quantized coefficients not available.")
            b = np.array(self.b_q, dtype=float)
            a = np.array(self.a_q, dtype=float)
        else:
            b = np.array(self.b_float, dtype=float)
            a = np.array(self.a_float, dtype=float)

        # Filter signal
        y = signal.lfilter(b, a, x)
        return y

# Beispiel
if __name__ == "__main__":
    filt = FilterIIR(fs=200.0, fc=0.1, order=4, btype="low", coeff_format="Q4.40")
    sum = filt.print_coeffs()
    if sum:
        print("Warnung: Es gab Über- oder Unterläufe bei der Quantisierung!")
        if input("Trotzdem fortfahren? (j/n) ") != "j":
            exit(1)

    filt.plot_response(fmin=0.01, minDB=-120, maxDB=5)
    filt.plot_group_delay(fmin=0.01)
    filt.plot_quantization_error(fmin=0.01, ymin_mag=-0.5, ymax_mag=0.5, ymin_phase=-1, ymax_phase=1)
    filt.plot_impulse_and_step_response(n_samples=4000)

    # Interaktive Konsole öffnen (mit allen Variablen im aktuellen Namespace)
    if ~(input("code interact? (j/n) ") != "j"):
        code.interact(local=locals())
