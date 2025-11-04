import numpy as np
import matplotlib.pyplot as plt

class FilterMA:
    """Moving Average Filter (FIR) mit 2^N Länge und Fixed-Point Unterstützung"""

    def __init__(self, fs, N_exp=4, coeff_format="Q1.15"):
        """
        fs: Samplingfrequenz
        N_exp: Filterlänge = 2^N_exp
        coeff_format: Fixed-point Format z.B. "Q1.15"
        """
        self.fs = fs
        self.N_exp = N_exp
        self.fir_len = 2**N_exp
        self.coeff_format = coeff_format
        self.m, self.n = None, None
        self.b_float = np.ones(self.fir_len) / self.fir_len
        self.a_float = np.array([1.0])
        self.b_q = None
        self.b_overflow = []
        self.b_underflow = []
        self.quantize_coeffs()

    def quantize_coeffs(self):
        """Quantisiere FIR-Koeffizienten"""
        if not self.coeff_format.startswith("Q"):
            raise ValueError("Format muss 'Qm.n' sein, z.B. 'Q1.15'")
        self.m, self.n = map(int, self.coeff_format[1:].split("."))
        word_bits = self.m + self.n
        scale = 1 << self.n
        min_val = -(1 << (word_bits - 1))
        max_val = (1 << (word_bits - 1)) - 1

        ints = []
        overflow_flags = []
        underflow_flags = []

        for c in self.b_float:
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
                underflow = True
            ints.append(val)
            overflow_flags.append(overflow)
            underflow_flags.append(underflow)

        self.b_q = np.array(ints)
        self.b_overflow = overflow_flags
        self.b_underflow = underflow_flags
        return any(self.b_overflow) or any(self.b_underflow)

    def apply_filter(self, x, use_quantized=False):
        """FIR Filter anwenden"""
        b = self.b_q if use_quantized else self.b_float
        y = np.convolve(x, b, mode='full')[:len(x)]
        return y

    def print_coeffs(self):
        """Koeffizienten anzeigen (Float + Fixed + Hex)"""
        word_bits = self.m + self.n
        hex_digits = (word_bits + 3) // 4

        def to_hex(val):
            return format(val & ((1 << word_bits) - 1), f"#0{hex_digits+2}X")

        print(f"fs = {self.fs} Hz")
        print(f"FIR length = {self.fir_len}")
        print(f"coeff_format = {self.coeff_format} (Q{self.m}.{self.n})")
        print("b_float =", [f"{c:.6f}" for c in self.b_float])
        print("b_int =", [f"{c}" for c in self.b_q])
        print("b_hex =", [to_hex(c) for c in self.b_q])
        print("overflow:", self.b_overflow)
        print("underflow:", self.b_underflow)
        sum = any(self.b_overflow) or any(self.b_underflow)
        print("error summary:", sum)
        return sum

    def plot_response(self, fmin=0.1, minDB=-60, maxDB=5):
        """Plot frequency response (Amplitude + Phase) of MA filter"""
        import matplotlib.pyplot as plt
        from scipy import signal
        import numpy as np

        # Frequenzachse
        worN = 200000
        w, h_float = signal.freqz(self.b_float, worN=worN, fs=self.fs)
        _, h_q     = signal.freqz(self.b_q, worN=worN, fs=self.fs)

        plt.figure(figsize=(10, 6))

        # Amplitude
        plt.subplot(2, 1, 1)
        plt.semilogx(w, 20 * np.log10(np.abs(h_float)), label="Float")
        plt.semilogx(w, 20 * np.log10(np.abs(h_q)), "--", label=f"Fixed-point {self.coeff_format}")
        plt.xlim([fmin, self.fs / 2])
        plt.ylim([minDB, maxDB])
        plt.ylabel("Amplitude [dB]")
        plt.title(f"Frequency Response of MA Filter (length = {self.fir_len})")
        plt.grid(which="both", linestyle="--", alpha=0.7)
        plt.legend()

        # Phase
        plt.subplot(2, 1, 2)
        plt.semilogx(w, np.angle(h_float, deg=True), label="Float")
        plt.semilogx(w, np.angle(h_q, deg=True), "--", label=f"Fixed-point {self.coeff_format}")
        plt.xlim([fmin, self.fs / 2])
        plt.ylabel("Phase [degrees]")
        plt.xlabel("Frequency [Hz]")
        plt.grid(which="both", linestyle="--", alpha=0.7)
        plt.legend()

        plt.tight_layout()
        plt.show()


# Beispiel
if __name__ == "__main__":
    filt = FilterMA(fs=200.0, N_exp=8, coeff_format="Q4.40")
    sum = filt.print_coeffs()
    if sum:
        print("Warnung: Es gab Über- oder Unterläufe bei der Quantisierung!")
        if input("Trotzdem fortfahren? (j/n) ") != "j":
            exit(1)

    filt.plot_response(fmin=0.1, minDB=-60, maxDB=5)
    #filt.plot_group_delay(fmin=0.01)
    #filt.plot_quantization_error(fmin=0.01, ymin_mag=-0.5, ymax_mag=0.5, ymin_phase=-1, ymax_phase=1)
    #filt.plot_impulse_and_step_response(n_samples=4000)

    # Interaktive Konsole öffnen (mit allen Variablen im aktuellen Namespace)
    if ~(input("code interact? (j/n) ") != "j"):
        code.interact(local=locals())
