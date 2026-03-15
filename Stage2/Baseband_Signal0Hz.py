import numpy as np
import matplotlib.pyplot as plt

# 1. Parameters 
sample_rate = 2e6  # 2.0 MSps from the mission brief
file_path = r'C:\Users\shlok\OneDrive\Desktop\Hackethon_dj\stage_1\telemetry_baseband.bin'
num_samples = 5_000_000 

# Load the data (just like before)
data = np.fromfile(file_path, dtype=np.complex64, count=num_samples)

# 2. Define the Frequency Shift 
shift_freq_hz = -430000.0  

# 3. Generate the Complex Sinusoid (The "Mixer") 
print(f"Shifting signal by {shift_freq_hz} Hz...")

t = np.arange(len(data)) / sample_rate

complex_mixer = np.exp(1j * 2 * np.pi * shift_freq_hz * t)

# 4. Apply the Shift 

corrected_data = data * complex_mixer

#5. Verify the Result
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

print("Calculating Power Spectral Density (Gain vs Frequency)...")

plt.figure(figsize=(12, 6))


plt.psd(corrected_data, NFFT=8192, Fs=sample_rate, color='blue')

plt.title('Gain vs Frequency (Power Spectral Density) of Shifted Signal')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Power Spectral Density (dB/Hz)')

plt.xlim(-50000, 50000) 

plt.grid(True)
plt.tight_layout()
plt.show()
