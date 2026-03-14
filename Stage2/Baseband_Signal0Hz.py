import numpy as np
import matplotlib.pyplot as plt

# --- 1. Parameters ---
sample_rate = 2e6  # 2.0 MSps from the mission brief
file_path = r'C:\Users\shlok\OneDrive\Desktop\Hackethon_dj\stage_1\telemetry_baseband.bin'
num_samples = 5_000_000 

# Load the data (just like before)
data = np.fromfile(file_path, dtype=np.complex64, count=num_samples)

# --- 2. Define the Frequency Shift ---
# Look at your spectrogram! Where was the wavy line? 
# If the line is at +150,000 Hz, you need to shift by -150,000 Hz to get it to 0.
# (Replace this value with what you observed)
shift_freq_hz = -433000.0  

# --- 3. Generate the Complex Sinusoid (The "Mixer") ---
print(f"Shifting signal by {shift_freq_hz} Hz...")

# Create an array representing time 't' for each sample
# t = [0, 1/Fs, 2/Fs, 3/Fs, ...]
t = np.arange(len(data)) / sample_rate

# Calculate the complex exponential: e^(-j * 2 * pi * f * t)
# Note: 1j is how Python represents the imaginary unit 'j' (or 'i')
complex_mixer = np.exp(1j * 2 * np.pi * shift_freq_hz * t)

# --- 4. Apply the Shift ---
# Multiply the raw data by the mixer to shift the frequencies
corrected_data = data * complex_mixer

# --- 5. Verify the Result ---
print("Plotting corrected spectrogram...")
plt.figure(figsize=(14, 7))
plt.specgram(
    corrected_data, 
    NFFT=4096, 
    Fs=sample_rate, 
    noverlap=2048, 
    cmap='viridis', 
    scale='dB'
)
  
plt.title(f'Spectrogram After {shift_freq_hz} Hz Shift')
plt.xlabel('Time (Seconds)')
plt.ylabel('Frequency (Hz)')
plt.ylim(-sample_rate/2, sample_rate/2) 
plt.colorbar(label='Intensity (dB)')
plt.tight_layout()
plt.show()

# Optional: Save the coarsely corrected data to a new file for the next step
# corrected_data.tofile('coarse_corrected.bin')

# Assuming 'corrected_data' and 'sample_rate' are already defined 
# from the previous coarse correction script.

print("Calculating Power Spectral Density (Gain vs Frequency)...")

plt.figure(figsize=(12, 6))

# plt.psd automatically computes the FFT, applies a windowing function, 
# averages the results, and plots it in decibels (dB).
# NFFT controls the resolution. Higher NFFT = sharper spikes.
plt.psd(corrected_data, NFFT=8192, Fs=sample_rate, color='blue')

plt.title('Gain vs Frequency (Power Spectral Density) of Shifted Signal')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Power Spectral Density (dB/Hz)')

# Optional: If you want to zoom in on the center to see the peak closely, 
# uncomment the line below and adjust the zoom window (e.g., +/- 50 kHz)
# plt.xlim(-50000, 50000) 

plt.grid(True)
plt.tight_layout()
plt.show()
