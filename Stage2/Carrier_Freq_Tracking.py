import numpy as np
import matplotlib.pyplot as plt

def pll_carrier_recovery(iq_samples, fs, initial_freq_guess):
    """
    Second-order PLL to track the drifting carrier and mix it down to 0 Hz.
    """
    num_samples = len(iq_samples)
    out_samples = np.zeros(num_samples, dtype=np.complex64)
    
    # Loop Parameters 
    damping_factor = 0.707
    bandwidth = 0.0005 
    
    denom = (1.0 + 2.0 * damping_factor * bandwidth + bandwidth**2)
    alpha = (4.0 * damping_factor * bandwidth) / denom
    beta = (4.0 * bandwidth**2) / denom
    
    phase_est = 0.0
    freq_est = initial_freq_guess * 2 * np.pi / fs
    freq_history = np.zeros(num_samples)

    for i in range(num_samples):
        # 1. Generate Local Oscillator
        local_osc = np.exp(-1j * phase_est)
        
        # 2. Mix to Baseband
        out_samples[i] = iq_samples[i] * local_osc
        
        # 3. Phase Error Detector
        error = np.angle(out_samples[i]**4) / 4.0
        
        # 4. Update Loop Filter
        phase_est += freq_est + alpha * error
        freq_est += beta * error
        phase_est = (phase_est + np.pi) % (2 * np.pi) - np.pi
        
        # Save frequency history (converted back to Hz)
        freq_history[i] = freq_est * fs / (2 * np.pi)

    return out_samples, freq_history

if __name__ == "__main__":
    # --- Configuration ---
    fs = 2.0e6  
    initial_peak_hz = 433300.0  
    filename = 'C:/Users/LENOVO/OneDrive/Desktop/Hackathon/processed_iq_data/telemetry_baseband.bin'
    
    try:
        # Load a 5-second chunk of data to clearly see the drift
        raw_data = np.memmap(filename, dtype='float32', mode='r')
        duration_sec = 5.0
        num_samples = int(duration_sec * fs)
        
        print(f"Loading {duration_sec} seconds of data...")
        I = raw_data[:num_samples*2:2]
        Q = raw_data[1:num_samples*2:2]
        iq_chunk = I + 1j * Q

        # Run Carrier Recovery
        print("Running Phase Locked Loop (PLL)...")
        baseband_iq, freq_track = pll_carrier_recovery(iq_chunk, fs, initial_peak_hz)

        # --- Plot 1: Doppler Drift Tracking ONLY ---
        time_axis = np.linspace(0, duration_sec, len(freq_track))
        
        plt.figure(figsize=(8, 5))
        plt.plot(time_axis, freq_track / 1e3, color='crimson', linewidth=1.5)
        plt.title("Output 1: Carrier Frequency Tracking")
        plt.xlabel("Time (s)")
        plt.ylabel("Frequency (kHz)")
        plt.grid(True, alpha=0.5)

        plt.tight_layout()
        plt.show()

    except FileNotFoundError:
        print("Error: Could not find telemetry_baseband.bin. Please check the path.")
