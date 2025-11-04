import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, firwin, freqz


# -------------------
# Basisklasse
# -------------------
class BaseFilter:
    def __init__(self, fs, fc=None, fmin=0.01, typ="IIR", btype="low"):
        self.fs = fs
        self.fc = fc
        self.fmin = fmin
        self.typ = typ.lower()
        self.btype = btype.lower()
        self.b = None
        self.a = None

    def design(self):
        """In Unterklassen implementieren"""
        raise NotImplementedError

    def plot_response(self, title="Filter Frequency Response"):
        if self.b is None:
            raise ValueError("Filterkoeffizienten nicht gesetzt. Bitte design() aufrufen.")

        # Frequenzgang berechnen
        w, h = freqz(self.b, self.a, worN=655360 , fs=self.fs)

        # Maske für fmin
        mask = w >= self.fmin
        w_plot = w[mask]
        h_plot = h[mask]

        # Textlabel
        param_text = (f"fs = {self.fs} Hz\n"
                    f"fc = {self.fc:.3f} Hz\n"
                    f"type = {self.typ}")
        if hasattr(self, "group_delay"):
            param_text += f"\nGroup Delay = {self.group_delay:.3f} s"

        # Plot Amplitude
        plt.figure(figsize=(10, 6))
        plt.subplot(2, 1, 1)
        plt.semilogx(w_plot, 20*np.log10(np.abs(h_plot)), label="Amplitude")
        plt.axvline(self.fc, color="red", linestyle=":", label=f"fc = {self.fc:.3f} Hz")
        plt.xlim([self.fmin, self.fs/2])
        plt.ylim([-80, 5])
        plt.ylabel("Amplitude [dB]")
        plt.title(title)
        plt.grid(which="both", linestyle="--", alpha=0.7)
        plt.legend()
        plt.text(self.fmin*1.1, -20, param_text, fontsize=9,
                bbox=dict(facecolor='white', alpha=0.7))

        # Plot Phase
        plt.subplot(2, 1, 2)
        plt.semilogx(w_plot, np.angle(h_plot, deg=True), label="Phase")
        plt.axvline(self.fc, color="red", linestyle=":")
        plt.xlim([self.fmin, self.fs/2])
        plt.ylabel("Phase [degrees]")
        plt.xlabel("Frequency [Hz]")
        plt.grid(which="both", linestyle="--", alpha=0.7)
        plt.legend()

        plt.tight_layout()
        plt.show()

# -------------------
# IIR Filter (Butterworth)
# -------------------
class IIRFilter(BaseFilter):
    def __init__(self, fs, fc, order=4, btype="low", fmin=0.01):
        super().__init__(fs, fc, fmin, typ="IIR", btype=btype)
        self.order = order
        self.design()

    def design(self):
        nyq = 0.5 * self.fs
        norm_cutoff = self.fc / nyq
        self.b, self.a = butter(self.order, norm_cutoff, btype=self.btype, analog=False)
    
    def print_info(self):
        if self.b is None or self.a is None:
            raise ValueError("Filterkoeffizienten nicht gesetzt. Bitte design() aufrufen.")

        # Sampling period
        Ts = 1.0 / self.fs if self.fs else None

        # Koeffizienten in Float
        b_str = ", ".join([f"{v:.6f}" for v in self.b])

        # Koeffizienten in Q1.15
        q15 = [f"0x{int(np.round(v*(2**15))) & 0xFFFF:04X}" for v in self.b]
        q15_str = ", ".join(q15)

        # Group Delay
        gd = getattr(self, "group_delay", None)

        print(f"typ = {self.typ}")
        if Ts:
            print(f"Sampling period: \tTs = {Ts*1000:.3f} ms")
        print(f"Sampling rate: \tfs = {self.fs:.3f} Hz")
        print(f"cutoff frequency: \tfc = {self.fc:.3f} Hz")
        if hasattr(self, "order"):
            print(f"order : {self.order}")
        print(f"Resulting coefficients: \t{b_str}")
        print(f"Coefficient in Q1.15 format: \t{q15_str}")
        if gd is not None:
            print(f"group_delay: \t{gd:.6f} s")

# -------------------
# FIR Filter (Windowed-Sinc)
# -------------------
class FIRFilter(BaseFilter):
    def __init__(self, fs=200.0, length=16, btype="low", fmin=0.01):
        super().__init__(fs=fs, fmin=fmin, typ="FIR", btype=btype)
        self.length = length
        if not (self.length & (self.length-1) == 0):
            raise ValueError("FIR length must be a power of 2")
        self.a = [1.0]  # FIR-Filter Denominator immer 1
        self.design()

    def design(self):
        """Design FIR Filter (Lowpass)."""
        # fc als fs/4 * 2/length (Faustregel)
        self.fc = self.fs / 4 * (2 / self.length)
        self.b = firwin(self.length, self.fc/(0.5*self.fs))
        # Group Delay
        self.group_delay = (self.length - 1)/2 * 1/self.fs

    def print_info(self):
        print(f"typ = {self.typ}")
        print(f"Sampling period: \tTs = {self.Ts*1000:.3f} ms")
        print(f"Sampling rate: \tfs = {self.fs:.3f} Hz")
        print(f"cutoff frequency: \tfc = {self.fc:.3f} Hz")
        print(f"length: \t{self.length}")
        # Koeffizienten Float
        b_str = ", ".join([f"{v:.6f}" for v in self.b])
        print(f"Resulting coefficients: \t{b_str}")
        # Q1.15 Format
        q15 = [f"0x{int(np.round(v*(2**15))) & 0xFFFF:04X}" for v in self.b]
        q15_str = ", ".join(q15)
        print(f"Coefficient in Q1.15 format: \t{q15_str}")
        print(f"group_delay: \t{self.group_delay:.6f} s")


# -------------------
# Beispiel
# -------------------
if __name__ == "__main__":

    iir = IIRFilter(fs=200.0, fc=0.5, order=1, fmin=0.01, btype="low")
    iir.plot_response(title="IIR lowpass") # Butterworth
    iir.print_info()

    #fir = FIRFilter(fs=fs, length=512, fmin=0.01, typ="lowpass")
    #fir.plot_response(title="FIR") # Windowed-Sinc
    #fir.print_info()
    
