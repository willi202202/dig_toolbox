import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# Parameters

fmin = 0.01     # lowest frequency to display [Hz]

# Coefficients for moving average (FIR)
b_float = np.ones(N) / N
a_float = [1.0]  # FIR -> no feedback

# Fixed-point coefficients approximation (Q1.15)
b_q15_int = np.round(b_float * (2**15)).astype(int)
b_q15 = b_q15_int / (2**15)
a_q15 = [1.0]

# Frequency response
w, h_float = signal.freqz(b_float, a_float, worN=200000, fs=fs)
_, h_q15 = signal.freqz(b_q15, a_q15, worN=200000, fs=fs)

# Cutoff frequency (-3 dB approx for moving average)
fc = 0.443 * fs / N

# Group delay [s]
group_delay = (N - 1) / 2 * (1/fs)

# Text label with parameters
param_text = (f"fs = {fs} Hz\n"
              f"N = {N}\n"
              f"fc ≈ {fc:.3f} Hz\n"
              f"Group delay = {group_delay*1000:.2f} ms")

# Plot amplitude response
plt.figure(figsize=(10, 6))
plt.subplot(2, 1, 1)
plt.semilogx(w, 20*np.log10(np.abs(h_float)), label="Float")
plt.semilogx(w, 20*np.log10(np.abs(h_q15)), "--", label="Fixed-point Q1.15")
plt.axvline(fc, color="red", linestyle=":", label=f"fc ≈ {fc:.3f} Hz")
plt.xlim([fmin, fs/2])
plt.ylim([-60, 5])
plt.ylabel("Amplitude [dB]")
plt.title("Frequency Response of Moving Average Filter")
plt.grid(which="both", linestyle="--", alpha=0.7)
plt.legend()
plt.text(0.02, -25, param_text, fontsize=9, bbox=dict(facecolor='white', alpha=0.7))

# Plot phase response
plt.subplot(2, 1, 2)
plt.semilogx(w, np.angle(h_float, deg=True), label="Float")
plt.semilogx(w, np.angle(h_q15, deg=True), "--", label="Fixed-point Q1.15")
plt.axvline(fc, color="red", linestyle=":")
plt.xlim([fmin, fs/2])
plt.ylabel("Phase [degrees]")
plt.xlabel("Frequency [Hz]")
plt.grid(which="both", linestyle="--", alpha=0.7)
plt.legend()

plt.tight_layout()
plt.show()
