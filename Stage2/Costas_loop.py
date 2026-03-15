import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter

# 1. CONFIGURATION & DATA LOADING 
fs = 2.0e6
filename = "telemetry_baseband.bin"
print("Loading data...")
data = np.memmap(filename, dtype=np.complex64, mode='r')
# Process 4.5 seconds to ensure the loop is fully locked and stable
signal = data[0:int(4.5 * fs)] 

# 2. COARSE SHIFT & PRE-FILTER 
print("Applying coarse frequency shift and pre-filter...")
t = np.arange(len(signal)) / fs
coarse_nco = np.exp(-1j * 2 * np.pi * 432999.0 * t)
coarse_baseband = signal * coarse_nco

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return lfilter(b, a, coarse_baseband)

clean_signal = butter_lowpass(15000, fs)

# 3. COSTAS LOOP (FINE PHASE LOCK)
print("Engaging Costas Loop for absolute phase alignment...")
phase_est = 0.0
freq_est = 0.0 
loop_bw = 0.005 
alpha = np.sqrt(2) * loop_bw
beta = loop_bw**2

baseband_out = np.zeros(len(clean_signal), dtype=np.complex64)

for i in range(len(clean_signal)):
    nco = np.exp(-1j * phase_est)
    baseband_out[i] = clean_signal[i] * nco
    
    # Costas error detector
    error = np.real(baseband_out[i]) * np.imag(baseband_out[i])
    
    phase_est += (freq_est * 2 * np.pi / fs) + (alpha * error)
    freq_est += (beta * error * fs / (2 * np.pi))
    phase_est %= (2 * np.pi)

# 4. THE MATCHED FILTER 
print("Applying Matched Filter (200-sample integration)...")
symbol_rate = 10000.0 
sps = int(fs / symbol_rate)

kernel = np.ones(sps) / sps
clean_real = np.convolve(np.real(baseband_out), kernel, mode='same')

# 5. VISUALIZATION SLICE 
start_sample = int(4.0 * fs)
num_symbols = 40
end_sample = start_sample + (num_symbols * sps)

# Extract just the slice we want to look at
plot_slice = clean_real[start_sample:end_sample]

# 6. PLOTTING THE "EYE" ALIGNMENT
print("Generating Timing Verification Plot...")
plt.figure(figsize=(15, 6))

# Plot the filtered signal 
plt.plot(plot_slice, color='cyan', linewidth=2.5, label='Filtered BPSK Baseband')
plt.axhline(0, color='white', linestyle='-', alpha=0.5)

# Plot the Sampling Points 
for i in range(num_symbols):
    sample_point = (i * sps) + (sps // 2)
    plt.axvline(sample_point, color='red', linestyle='--', alpha=0.6)

    plt.plot(sample_point, plot_slice[sample_point], 'yo', markersize=6)

plt.title("Verification: Symbol Sampling Alignment (SPS = 200)", fontsize=16)
plt.xlabel("Samples (Relative to slice start)", fontsize=12)
plt.ylabel("Amplitude (Binary 1 -> Positive, Binary 0 -> Negative)", fontsize=12)

plt.gca().set_facecolor('#111111')
plt.grid(color='white', alpha=0.1)
plt.legend(loc='upper right')
plt.tight_layout()
plt.show()
