import numpy as np
from scipy import signal

class FilterMA:
    def __init__(self, fs, N_exp, coeff_format="Q1.15", window="rectangular", shift_normalize=True):
        """
        Mittelwert- oder Fenster-FIR-Filter mit 2^N taps.
        
        fs: Abtastrate
        N_exp: Filterlänge = 2^N_exp
        coeff_format: Fixed-point Format z.B. "Q1.15"
        window: "rectangular", "hann", "hamming", "binomial"
        shift_normalize: wenn True, Summe der int-Koeffizienten = 2^N (Shifter statt Division)
        """
        self.fs = fs
        self.N_exp = N_exp
        self.fir_len = 1 << N_exp
        self.coeff_format = coeff_format
        self.window = window
        self.shift_normalize = shift_normalize

        # float coefficients (fenster wählen)
        self.b_float = self.make_weights(self.fir_len, window)

        # quantisieren
        self.b_q, self.b_int, self.sum_int, self.shift_bits = self.quantize_weights(self.b_float)

    def make_weights(self, L, kind="rectangular"):
        """Erzeuge Fensterkoeffizienten und normiere auf Summe = 1"""
        if kind == "rectangular":
            w = np.ones(L)
        elif kind == "hann":
            w = np.hanning(L)
        elif kind == "hamming":
            w = np.hamming(L)
        elif kind == "binomial":
            w = np.array([1.0])
            for _ in range(L-1):
                w = np.convolve(w, np.array([1.0, 1.0]))
            # auf Länge L trimmen falls nötig
            if len(w) > L:
                start = (len(w)-L)//2
                w = w[start:start+L]
        else:
            raise ValueError(f"Unbekanntes Fenster: {kind}")
        return w / np.sum(w)  # Normierung auf DC-Gain = 1

    def quantize_weights(self, w_float):
        m, n = map(int, self.coeff_format[1:].split("."))
        scale = 1 << n

        if self.shift_normalize:
            # direkte Shifter-Koeffizienten: Summe = 2^N_exp
            w_int = np.ones_like(w_float, dtype=int)  # alle = 1
            sum_int = np.sum(w_int)
            shift_bits = self.N_exp
            w_q = w_int.astype(float) / (1 << shift_bits)  # also 0.25 bei N_exp=2
        else:
            # klassisches Q-Format
            w_scaled = w_float * scale
            w_int = np.round(w_scaled).astype(int)
            sum_int = np.sum(w_int)
            shift_bits = int(np.log2(sum_int)) if sum_int > 0 else None
            w_q = w_int.astype(float) / scale

        return w_q, w_int, sum_int, shift_bits


    def print_coeffs(self):
        print(f"Filter: {self.window}, Länge = {self.fir_len}, Format = {self.coeff_format}")
        print("b_float (first 10) =", [f"{c:.6f}" for c in self.b_float[:10]])
        print("b_q (first 10)     =", [f"{c:.6f}" for c in self.b_q[:10]])
        print("b_int (first 10)   =", self.b_int[:10].tolist())
        print("Summe int          =", self.sum_int)
        print("Shift bits         =", self.shift_bits)


    def apply_filter(self, x, use_quantized=False):
        """FIR Filter anwenden"""
        b = self.b_q if use_quantized else self.b_float
        y = np.convolve(x, b, mode='full')[:len(x)]
        return y

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
    # window: "rectangular", "hann", "hamming", "binomial"
    filt = FilterMA(fs=200.0, N_exp=3, coeff_format="Q2.15", window="hamming", shift_normalize=False)
    filt.print_coeffs()
    filt.plot_response(fmin=0.1, minDB=-80, maxDB=5)
    #filt.plot_group_delay(fmin=0.01)
    #filt.plot_quantization_error(fmin=0.01, ymin_mag=-0.5, ymax_mag=0.5, ymin_phase=-1, ymax_phase=1)
    #filt.plot_impulse_and_step_response(n_samples=4000)

    # Interaktive Konsole öffnen (mit allen Variablen im aktuellen Namespace)
    #if ~(input("code interact? (j/n) ") != "j"):
    #    code.interact(local=locals())
