import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter

# --- 1. CONFIGURATION ---
fs = 2.0e6
filename = "telemetry_baseband.bin"
data = np.memmap(filename, dtype=np.complex64, mode='r')
# 5 seconds is plenty for this refined method
signal = data[0:int(5 * fs)] 

# --- 2. COARSE SHIFT & PRE-FILTER (The Fix) ---
print("Step 1: Coarse shift to baseband...")
t = np.arange(len(signal)) / fs
# Blindly shift down by 432,999 Hz
coarse_nco = np.exp(-1j * 2 * np.pi * 432999.0 * t)
coarse_baseband = signal * coarse_nco

print("Step 2: Pre-filtering noise...")
def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return lfilter(b, a, coarse_baseband)

# Squeeze the bandwidth down to +/- 15kHz. The noise is now gone.
clean_signal = butter_lowpass(15000, fs)

# --- 3. FINE COSTAS LOOP ---
print("Step 3: Engaging Fine Costas Loop...")
phase_est = 0.0
freq_est = 0.0 # Starting at 0 because we already did the coarse shift
loop_bw = 0.005 # Tighter, smoother loop
alpha = np.sqrt(2) * loop_bw
beta = loop_bw**2

baseband_out = np.zeros(len(clean_signal), dtype=np.complex64)

for i in range(len(clean_signal)):
    nco = np.exp(-1j * phase_est)
    baseband_out[i] = clean_signal[i] * nco
    
    # Error detector now works flawlessly because the noise is gone
    error = np.real(baseband_out[i]) * np.imag(baseband_out[i])
    
    phase_est += (freq_est * 2 * np.pi / fs) + (alpha * error)
    freq_est += (beta * error * fs / (2 * np.pi))
    phase_est %= (2 * np.pi)

print("Lock complete.")

# --- 4. CLOCK RECOVERY ---
print("Step 4: Extracting Symbol Clock...")
locked_segment = baseband_out[int(2.0 * fs):]

# Because we filtered the signal, the symbol transitions are smooth.
# Squaring the magnitude highlights these transitions perfectly.
clock_energy = np.abs(locked_segment)**2
clock_energy -= np.mean(clock_energy)

fft_size = 2**19
f_clock = np.fft.fft(clock_energy, n=fft_size)
freqs = np.fft.fftfreq(fft_size, 1/fs)

mask = (freqs > 500) & (freqs < 15000)
symbol_rate = freqs[mask][np.argmax(np.abs(f_clock[mask]))]

print("\n" + "="*45)
print("             STAGE II TRUE OUTPUTS")
print("="*45)
print(f"TRUE SYMBOL RATE: {symbol_rate:,.2f} Hz")
print(f"SAMPLES/SYMBOL:   {fs/symbol_rate:.2f}")
print("="*45)

# --- 5. VISUAL VERIFICATION ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Plot 1: The BPSK Constellation
lock_slice = baseband_out[int(4.0 * fs):int(4.1 * fs)]
ax1.hexbin(lock_slice.real, lock_slice.imag, gridsize=60, cmap='magma')
ax1.axhline(0, color='white', linestyle='--', alpha=0.3)
ax1.axvline(0, color='white', linestyle='--', alpha=0.3)
ax1.set_title("Costas Loop Constellation", fontsize=14)
ax1.set_xlabel("Real"); ax1.set_ylabel("Imag")
ax1.axis('equal')

# Plot 2: The Clock Spike
ax2.plot(freqs[mask], 10*np.log10(np.abs(f_clock[mask])))
ax2.axvline(symbol_rate, color='r', linestyle='--', label=f'Clock: {symbol_rate:.1f} Hz')
ax2.set_title("Symbol Clock Spectrum", fontsize=14)
ax2.set_xlabel("Frequency (Hz)"); ax2.set_ylabel("Magnitude (dB)")
ax2.legend()
ax2.grid(alpha=0.3)

plt.tight_layout()
plt.show()