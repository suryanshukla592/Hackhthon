import numpy as np
import matplotlib.pyplot as plt

sample_rate = 2.0e6
filename = "telemetry_baseband.bin"

print("Loading data for Peak Analysis...")
data = np.memmap(filename, dtype=np.complex64, mode='r')

# Grab a 5-second chunk from the middle of the file
start_idx = int(sample_rate * 60) # Start at 60 seconds
chunk_size = int(sample_rate * 5)
signal_chunk = data[start_idx : start_idx + chunk_size]

print("Calculating Power Spectral Density (PSD)...")
# We use a massive FFT to pull the signal out of the noisee 
fft_size = 131072
freqs = np.fft.fftfreq(fft_size, 1/sample_rate)
psd = np.abs(np.fft.fft(signal_chunk[:fft_size]))**2
psd_db = 10 * np.log10(psd)

# Shift for plotting
freqs = np.fft.fftshift(freqs)
psd_db = np.fft.fftshift(psd_db)

# Find the peak
peak_idx = np.argmax(psd_db)
peak_freq = freqs[peak_idx]
peak_val = psd_db[peak_idx]
avg_noise = np.mean(psd_db)

print("-" * 40)
print(f"PEAK FREQUENCY DETECTED: {peak_freq:,.2f} Hz")
print(f"PEAK POWER LEVEL: {peak_val:.2f} dB")
print(f"AVERAGE NOISE LEVEL: {avg_noise:.2f} dB")
print("-" * 40)

plt.figure(figsize=(12, 6))
plt.plot(freqs, psd_db, color='blue', lw=0.5)
plt.axvline(peak_freq, color='red', linestyle='--', label=f'Carrier Peak: {peak_freq:.0f} Hz')
plt.title("Stage I: Frequency Domain Signal Search")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Power (dB)")
plt.grid(alpha=0.3)
plt.legend()
plt.show()
