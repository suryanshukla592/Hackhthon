import numpy as np
import matplotlib.pyplot as plt

# 1. Mission Parameters
fs = 2.0e6
filename = "telemetry_baseband.bin"
target_freq = 433000
search_width = 20000  # How far to look above/below 433kHz

# 2. Loading 20 seconds of data
data = np.memmap(filename, dtype=np.complex64, mode='r')
start_sec = 30.0
end_sec = 50.0
signal_chunk = data[int(start_sec * fs):int(end_sec * fs)]

print("Tracking carrier peak over time...")

# 3. Calculate Spectrogram Data
nfft_size = 8192 # Balance between speed and frequency resolution
Pxx, freqs, bins, im = plt.specgram(signal_chunk, NFFT=nfft_size, Fs=fs, noverlap=nfft_size//2)
plt.close() # We don't want to show this plot yet

# 4. Extract the Peak Trace
# Filter frequencies to only look near 430kHz
freq_mask = (freqs > target_freq - search_width) & (freqs < target_freq + search_width)
filtered_freqs = freqs[freq_mask]
filtered_Pxx = Pxx[freq_mask, :]

# Find the frequency index with the max power for each time bin
peak_indices = np.argmax(filtered_Pxx, axis=0)
peak_freqs = filtered_freqs[peak_indices]

# 5. Plot the Drift Characterization
plt.figure(figsize=(12, 6))
plt.plot(bins, peak_freqs / 1000, color='cyan', linewidth=1.5, label='Carrier Center Frequency')

plt.title("Stage I: Voyager-X Drift Characterization", fontsize=16)
plt.xlabel("Time (Seconds from slice start)", fontsize=12)
plt.ylabel("Frequency (kHz)", fontsize=12)
plt.grid(True, alpha=0.2)
plt.legend()

# Calculate statistics for the Mission Report
max_drift = (np.max(peak_freqs) - np.min(peak_freqs)) / 1000
print(f"--- DRIFT STATISTICS ---")
print(f"Average Frequency: {np.mean(peak_freqs)/1000:.2f} kHz")
print(f"Total Peak-to-Peak Wobble: {max_drift:.2f} kHz")
print(f"------------------------")

plt.show()
