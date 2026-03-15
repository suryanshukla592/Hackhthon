import numpy as np
import matplotlib.pyplot as plt

# 1. Mission Parameters
fs = 2.0e6
filename = "telemetry_baseband.bin"
target_freq = 433000  # The peak you found earlier
zoom_width = 30000    # Widened the zoom to be safe

# 2. Loading Data
data = np.memmap(filename, dtype=np.complex64, mode='r')

# Let's try seconds 30 to 50 (sometimes the start is messy)
start_sec = 30.0
end_sec = 50.0
start_idx = int(start_sec * fs)
end_idx = int(end_sec * fs)

signal_chunk = data[start_idx:end_idx]

print(f"Analyzing 20s slice. Calculating optimal contrast...")

# 3. Generating the Spectrogram
plt.figure(figsize=(14, 8))
nfft_size = 16384

# We generate the raw data first to find the best vmin/vmax
Pxx, freqs, bins, im = plt.specgram(
    signal_chunk, 
    NFFT=nfft_size, 
    Fs=fs, 
    noverlap=nfft_size // 2, 
    cmap='magma'
)

# --- AUTO-BRIGHTNESS LOGIC ---
# We calculate the 10th percentile (noise) and 99.9th percentile (peak)
# This forces the signal to stand out regardless of your PC's power levels.
data_db = 10 * np.log10(Pxx)
auto_vmin = np.percentile(data_db, 10)
auto_vmax = np.percentile(data_db, 99.9)
im.set_clim(vmin=auto_vmin, vmax=auto_vmax)
# -----------------------------

plt.title(f"Voyager-X Carrier Search (Time: {start_sec}s - {end_sec}s)", fontsize=16)
plt.xlabel("Time (Seconds)", fontsize=12)
plt.ylabel("Frequency (Hz)", fontsize=12)

# Set the window around our 433kHz target
plt.ylim(target_freq - zoom_width, target_freq + zoom_width)

plt.colorbar(im).set_label('Power (dB)')
plt.grid(True, color='white', alpha=0.1)

print(f"Plotting with Auto-Contrast: vmin={auto_vmin:.1f}, vmax={auto_vmax:.1f}")
plt.show()