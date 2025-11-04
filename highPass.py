import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# Parameters
fs = 200.0      # Sampling rate [Hz]
Ts = 1/fs
fc = 0.5        # Cutoff frequency [Hz]
fmin = 0.01     # lowest frequency to display [Hz]
gain_db = 6.0   # Gain in dB
gain = 10**(gain_db/20)   # linear Gain

# Coefficient (float)
alpha_float = 1 / (1 + 2 * np.pi * fc * Ts)

# Fixed-point coefficient Q1.15
alpha_q15_int = int(round(alpha_float * (2**15)))
alpha_q15 = alpha_q15_int / (2**15)

gain_q15_int = int(round(gain * (2**15)))
gain_q15 = gain_q15_int / (2**15)

# Filter coefficients (float) with gain
b_float = [gain * alpha_float, -gain * alpha_float]
a_float = [1.0, -alpha_float]

# Filter coefficients (Q1.15) with gain
b_q15 = [gain * alpha_q15, -gain * alpha_q15]
a_q15 = [1.0, -alpha_q15]

# Frequency response
w, h_float = signal.freqz(b_float, a_float, worN=200000, fs=fs)
_, h_q15 = signal.freqz(b_q15, a_q15, worN=200000, fs=fs)

# Text label with parameters
param_text = (f"fs = {fs} Hz\n"
              f"fc = {fc} Hz\n"
              f"alpha_float = {alpha_float:.6f}\n"
              f"alpha_q15_int = 0x{alpha_q15_int:04X}\n"
              f"gain = {gain:.3f} ({gain_db:.1f} dB)\n"
              f"gain_q15_int = 0x{gain_q15_int:04X} ({gain_q15:.3f})")

# Plot amplitude response
plt.figure(figsize=(10, 6))
plt.subplot(2, 1, 1)
plt.semilogx(w, 20*np.log10(np.abs(h_float)), label="Float")
plt.semilogx(w, 20*np.log10(np.abs(h_q15)), "--", label="Fixed-point")
plt.axvline(fc, color="red", linestyle=":", label=f"fc = {fc} Hz")
plt.xlim([fmin, fs/2])   # use fmin variable here
plt.ylim([-40, 12])   
plt.ylabel("Amplitude [dB]")
plt.title("Frequency Response of First-Order High-Pass Filter")
plt.grid(which="both", linestyle="--", alpha=0.7)
plt.legend()
plt.text(0.2*fs/2, -15, param_text, fontsize=9, bbox=dict(facecolor='white', alpha=0.7))

# Plot phase response
plt.subplot(2, 1, 2)
plt.semilogx(w, np.angle(h_float, deg=True), label="Float")
plt.semilogx(w, np.angle(h_q15, deg=True), "--", label="Fixed-point")
plt.axvline(fc, color="red", linestyle=":")
plt.xlim([fmin, fs/2])   # use fmin variable here
plt.ylabel("Phase [degrees]")
plt.xlabel("Frequency [Hz]")
plt.grid(which="both", linestyle="--", alpha=0.7)
plt.legend()

plt.tight_layout()
plt.show()
