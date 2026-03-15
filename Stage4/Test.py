
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter
import gc

# =============================================================================
# CONFIGURATION & DATA LOADING
# =============================================================================
fs = 2.0e6
filename = "telemetry_baseband.bin"
process_seconds = 60.0  
print("--- STARTING DSP PIPELINE ---")
print(f"1. Loading {process_seconds} seconds of telemetry data...")

try:
    data = np.memmap(filename, dtype=np.complex64, mode='r')
    signal = np.array(data[0:int(process_seconds * fs)]) 
    del data 
except FileNotFoundError:
    print(f"[-] ERROR: Could not find {filename}.")
    exit()

# =============================================================================
# STAGE I: COARSE SHIFT & PRE-FILTERING
# =============================================================================
print("2. Applying Coarse Frequency Shift (430,000 Hz)...")
t = np.arange(len(signal)) / fs
signal *= np.exp(-1j * 2 * np.pi * 430000.0 * t)
del t 

print("3. Pre-filtering deep space noise (15 kHz Lowpass)...")
def butter_lowpass_filter(data_array, cutoff, fs_rate, order=5):
    nyq = 0.5 * fs_rate
    b, a = butter(order, cutoff / nyq, btype='low', analog=False)
    return lfilter(b, a, data_array)

clean_signal = butter_lowpass_filter(signal, 15000, fs)
del signal 

# =============================================================================
# STAGE II: FINE CARRIER & CLOCK RECOVERY
# =============================================================================
print("4. Engaging Fine Costas Loop...")
phase_est, freq_est = 0.0, 0.0 
loop_bw = 0.005  
alpha, beta = np.sqrt(2) * loop_bw, loop_bw**2

baseband_out = np.zeros(len(clean_signal), dtype=np.complex64)

for i in range(len(clean_signal)):
    nco = np.exp(-1j * phase_est)
    baseband_out[i] = clean_signal[i] * nco
    error = np.real(baseband_out[i]) * np.imag(baseband_out[i])
    phase_est = (phase_est + (freq_est * 2 * np.pi / fs) + (alpha * error)) % (2 * np.pi)
    freq_est += (beta * error * fs / (2 * np.pi))

del clean_signal 

print("5. Extracting Exact Symbol Clock (FFT)...")
locked_segment = baseband_out[int(2.0 * fs):]
clock_energy = np.abs(locked_segment)**2 - np.mean(np.abs(locked_segment)**2)

fft_size = 2**19
f_clock = np.fft.fft(clock_energy, n=fft_size)
freqs = np.fft.fftfreq(fft_size, 1/fs)

mask = (freqs > 500) & (freqs < 15000)
symbol_rate = freqs[mask][np.argmax(np.abs(f_clock[mask]))]
true_sps = fs / symbol_rate
del locked_segment, clock_energy

# =============================================================================
# STAGE III: DEMODULATION & CLOSED-LOOP TIMING
# =============================================================================
print("6. Applying Boxcar Matched Filter...")
kernel = np.ones(int(true_sps)) / int(true_sps)
clean_real = np.convolve(np.real(baseband_out), kernel, mode='same')
clean_real = clean_real / np.std(clean_real)

print("7. Dynamic Symbol Synchronization (Early-Late Gate PLL)...")
start_idx = int(4.0 * fs) 
end_idx = len(clean_real)

chunk = clean_real[start_idx : start_idx + int(true_sps * 20)]
best_phase, max_energy = 0, 0
for p in range(int(true_sps)):
    idx = np.round(np.arange(p, len(chunk), true_sps)).astype(int)
    energy = np.mean(np.abs(chunk[idx[idx < len(chunk)]]))
    if energy > max_energy: 
        max_energy, best_phase = energy, p

current_idx_float = float(start_idx + best_phase)
sampled_symbols, final_indices = [], []

early_offset = int(true_sps * 0.15)  
late_offset  = int(true_sps * 0.15)  
timing_gain  = 0.2                   

while int(current_idx_float) + late_offset < end_idx:
    sample_idx = int(current_idx_float)
    final_indices.append(sample_idx)
    sampled_symbols.append(clean_real[sample_idx])
    
    early_amp = np.abs(clean_real[sample_idx - early_offset])
    late_amp  = np.abs(clean_real[sample_idx + late_offset])
    timing_error = late_amp - early_amp 
    current_idx_float += true_sps + (timing_gain * timing_error)

final_indices = np.array(final_indices)
sampled_symbols = np.array(sampled_symbols)

# =============================================================================
# STAGE IV: GOD MODE DECRYPTION (ALGEBRAIC KEY SEARCH)
# =============================================================================
print("\n" + "="*70)
print("       STAGE IV: GOD MODE DECRYPTION (ALGEBRAIC KEY SEARCH)")
print("="*70)

bits_normal = (sampled_symbols > 0).astype(np.uint8)
bits_diff_same_is_1 = (sampled_symbols[1:] * sampled_symbols[:-1] > 0).astype(np.uint8)
bits_diff_diff_is_1 = (sampled_symbols[1:] * sampled_symbols[:-1] < 0).astype(np.uint8)

logic_states = {
    "Normal BPSK": bits_normal,
    "DBPSK (Same Phase = 1)": bits_diff_same_is_1,
    "DBPSK (Diff Phase = 1)": bits_diff_diff_is_1
}

found = False

for state_name, state_bits in logic_states.items():
    if found: break
    
    for bit_shift in range(8):
        if found: break
        
        shifted = state_bits[bit_shift:]
        shifted = shifted[:len(shifted) - (len(shifted) % 8)]
        packed = np.packbits(shifted, bitorder='big')
        
        if len(packed) < 3: continue
        
        # Vectorized Algebraic Attack: Look for \nBM mathematically without knowing the key
        K1 = packed[:-2] ^ 0x0A
        K2 = packed[1:-1] ^ 0x42
        K3 = packed[2:] ^ 0x4D
        
        # If K1, K2, and K3 are identical at any index, we have found the exact XOR key and payload!
        valid_indices = np.where((K1 == K2) & (K2 == K3))[0]
        
        for idx in valid_indices:
            assumed_key = K1[idx]
            
            print(f"\n[!!!] GOD MODE TRIGGERED: Algebraic Signature Match!")
            print(f"    -> Demodulation: {state_name}, Bit Shift: {bit_shift}")
            print(f"    -> Discovered Secret XOR Key: 0x{assumed_key:02X}")
            print(f"    -> Payload Boundary found at Byte Index: {idx}")
            
            # Rip the entire array open with the newly discovered key
            decrypted_bytes = packed ^ assumed_key
            data = bytes(decrypted_bytes)
            
            # Extract the secret coordinates!
            try:
                pre_text = data[max(0, idx-100):idx]
                coords = ''.join(chr(b) for b in pre_text if 32 <= b <= 126)
                print(f"    -> Extracted Header/Coordinates: {coords}")
            except Exception:
                pass
            
            # Extract Image (skip the '\n', start perfectly at 'B')
            img_data = data[idx+1:] 
            
            filename = "VOYAGER_RECOVERED_GODMODE.bmp"
            with open(filename, "wb") as f:
                f.write(img_data)
                
            print(f"[SUCCESS] Clean Image safely saved to {filename}")
            found = True
            break

if not found:
    print("\n[-] Algebraic search failed.")

# =============================================================================
# STAGE V: MASTER DASHBOARD VISUALIZATION
# =============================================================================
print("\n9. Generating Master Diagnostic Dashboard...")
fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor('#111111')

ax1 = plt.subplot(2, 2, 1)
lock_slice = baseband_out[int(4.0 * fs):int(4.1 * fs)]
ax1.hexbin(lock_slice.real, lock_slice.imag, gridsize=60, cmap='magma')
ax1.axhline(0, color='white', linestyle='--', alpha=0.3)
ax1.axvline(0, color='white', linestyle='--', alpha=0.3)
ax1.set_title("Costas Loop Locked Constellation", color='white', fontsize=12)
ax1.axis('equal'); ax1.set_facecolor('black'); ax1.tick_params(colors='white')

ax2 = plt.subplot(2, 2, 2)
ax2.plot(freqs[mask], 10*np.log10(np.abs(f_clock[mask])), color='lime')
ax2.axvline(symbol_rate, color='r', linestyle='--', label=f'{symbol_rate:.1f} Hz')
ax2.set_title("Symbol Clock Spectrum (FFT)", color='white', fontsize=12)
ax2.set_facecolor('black'); ax2.tick_params(colors='white'); ax2.legend()

ax3 = plt.subplot(2, 2, 3)
num_plot_symbols = 40
if len(final_indices) > num_plot_symbols:
    plot_start = final_indices[0] - int(true_sps)
    plot_end = final_indices[num_plot_symbols] + int(true_sps)
    plot_slice = clean_real[plot_start:plot_end]

    ax3.plot(plot_slice, color='cyan', linewidth=2.0)
    ax3.axhline(0, color='white', linestyle='-', alpha=0.3)

    for i in range(num_plot_symbols):
        rel_idx = final_indices[i] - plot_start
        ax3.axvline(rel_idx, color='red', linestyle='--', alpha=0.4)
        ax3.plot(rel_idx, plot_slice[rel_idx], 'yo', markersize=6, markeredgecolor='black', zorder=5)
        
    ax3.set_title(f"Early-Late Gate PLL Alignment (True SPS={true_sps:.2f})", color='white', fontsize=12)
ax3.set_facecolor('black'); ax3.tick_params(colors='white')

ax4 = plt.subplot(2, 2, 4)
ax4.hist(sampled_symbols, bins=100, color='purple', alpha=0.8, edgecolor='black')
ax4.axvline(0, color='red', linestyle='--', linewidth=2)
ax4.set_title("Stage 3 Soft Decision Histogram", color='white', fontsize=12)
ax4.set_facecolor('black'); ax4.tick_params(colors='white')

plt.tight_layout()
plt.show()

del baseband_out, clean_real, sampled_symbols
gc.collect()
print("Pipeline Execution Complete. RAM cleared.")
