import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter

fs = 2.0e6
symbol_rate = 10000
sps=200 #sps=fs/symbol_rate
filename = "telemetry_baseband.bin"
data = np.memmap(filename, dtype=np.complex64, mode='r')

# Process 5 seconds of data (gives the loop time to lock, plus plenty of data)
signal = data[0:int(5.0 * fs)] 

plt.figure(figsize=(10, 5))
plt.hist(signal, bins=100, color='purple', alpha=0.7, edgecolor='black')
plt.title("Symbol Decision Histogram (with distortion)", fontsize=14)
plt.xlabel("Symbol Amplitude")
plt.ylabel("Frequency (Count of Bits)")
plt.legend()
plt.grid(alpha=0.2)
plt.show()

t = np.arange(len(signal)) / fs
coarse_nco = np.exp(-1j * 2 * np.pi * 432999.0 * t)
coarse_baseband = signal * coarse_nco

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return lfilter(b, a, coarse_baseband)

clean_signal = butter_lowpass(15000, fs)

phase_est = 0.0
freq_est = 0.0 
loop_bw = 0.005 
alpha = np.sqrt(2) * loop_bw
beta = loop_bw**2
baseband_out = np.zeros(len(clean_signal), dtype=np.complex64)

for i in range(len(clean_signal)):
    nco = np.exp(-1j * phase_est)
    baseband_out[i] = clean_signal[i] * nco
    error = np.real(baseband_out[i]) * np.imag(baseband_out[i])
    phase_est += (freq_est * 2 * np.pi / fs) + (alpha * error)
    freq_est += (beta * error * fs / (2 * np.pi))
    phase_est %= (2 * np.pi)

sps_int = int(fs / symbol_rate)

rect_kernel = np.ones(sps_int) / sps_int

integrated_signal = np.convolve(np.real(baseband_out), rect_kernel, mode='same')

# PRECISION SAMPLING 
best_offset = 0
max_abs_mean = 0

for trial in range(sps_int):
    sample_test = integrated_signal[int(4.0 * fs) + trial :: sps_int]
    metric = np.mean(np.abs(sample_test))
    if metric > max_abs_mean:
        max_abs_mean = metric
        best_offset = trial

print(f"Optimal Sampling Offset: {best_offset}")
sampled_symbols = integrated_signal[int(4.0 * fs) + best_offset :: sps_int]

start_extract = int(4.0 * fs) 

sampled_symbols = sampled_symbols / np.mean(np.abs(sampled_symbols))

plt.figure(figsize=(10, 5))
plt.hist(sampled_symbols, bins=100, color='purple', alpha=0.7, edgecolor='black')
plt.axvline(0, color='red', linestyle='--', linewidth=2, label='Hard Decision Boundary (0.0)')
plt.title("Symbol Decision Histogram (Bimodal Distribution)", fontsize=14)
plt.xlabel("Symbol Amplitude (Soft Decision Value)")
plt.ylabel("Frequency (Count of Bits)")
plt.legend()
plt.grid(alpha=0.2)
plt.show()

bits_normal = (sampled_symbols > 0).astype(int)

# Correcting for Systematic Distortion (BPSK 180-degree Phase Ambiguity)
bits_inverted = 1 - bits_normal

bits_normal = (sampled_symbols > 0).astype(np.uint8)

bits_inverted = 1 - bits_normal

print(f"Extracted {len(bits_normal)} bits.")
print(f"First 50 bits (Normal):   {''.join(map(str, bits_normal[:]))}")
print(f"First 50 bits (Inverted): {''.join(map(str, bits_inverted[:]))}")

plt.figure(figsize=(6, 4))
plt.hist(bits_normal, bins=[-0.5, 0.5, 1.5], rwidth=0.8, color='skyblue', edgecolor='black')
plt.xticks([0, 1])
plt.xlabel("Bit Value")
plt.ylabel("Frequency")
plt.title("Histogram of Hard Bits")
plt.show()