import numpy as np

# 1. Mission Parameters
fs = 2.0e6
filename = "telemetry_baseband.bin"
target_freq = 433000
search_width = 30000 

# 2. Loading 60 seconds of data (memmap is very fast)
data = np.memmap(filename, dtype=np.complex64, mode='r')
start_idx = int(30 * fs)
end_idx = int(90 * fs)
signal_chunk = data[start_idx:end_idx]

print("Scanning for carrier peak (Math-only mode)...")

# 3. Calculate Power Density manually
nfft_size = 32768
# We'll look at the first chunk to find the peak frequency
fft_data = np.fft.fft(signal_chunk[:nfft_size])
freqs = np.fft.fftfreq(nfft_size, 1/fs)

# 4. Filter to our target zone
mask = (freqs > target_freq - search_width) & (freqs < target_freq + search_width)
zone_freqs = freqs[mask]
zone_pwr = np.abs(fft_data[mask])**2

# 5. Extract results
peak_freq = zone_freqs[np.argmax(zone_pwr)]

print("\n" + "="*40)
print(f"STAGE I MISSION DATA")
print("="*40)
print(f"DETECTED PEAK:  {peak_freq:,.2f} Hz")
print(f"TARGET OFFSET:  {peak_freq - target_freq:,.2f} Hz")
print("="*40)
print("\nCopy the DETECTED PEAK value. You will need it for Stage II.")
