# 🛰️ Stage 0: Data Reconstruction

This stage is the **foundation** of the signal processing pipeline. We transform raw, unorganized hexadecimal captures from the Deep Space Network (DSN) into a high-performance, complex binary format.

---

## 🎯 The Goal
Raw radio data often comes in a "human-readable" hex format, which is extremely bulky and slow to process. Our objective is to bridge the gap between raw capture and digital signal processing (DSP) by:

* **Scanning:** Locating all 300 capture files in the `./dsn_data` directory.
* **Sorting:** Reordering files chronologically using filename timestamps.
* **Conversion:** Translating ASCII hex strings into IEEE 754 32-bit floating-point numbers.
* **Streaming:** Merging everything into a single `telemetry_baseband.bin` file while maintaining a low memory footprint.



---

## ⚙️ How it Works
We implemented the parser in **C++** to ensure maximum throughput. By utilizing a "streaming" approach, the program only handles one file at a time rather than loading the entire dataset into RAM.

> [!IMPORTANT]
> **Memory Efficiency:** This parser is designed to handle gigabytes of data on systems with limited memory by processing samples in a continuous stream.

### 📊 Data Structure
Each sample is packed into a tight 8-byte structure, making it natively compatible with `numpy.fromfile` in the next stage.

| Component | Type | Size | Description |
| :--- | :--- | :--- | :--- |
| **I (In-phase)** | `float` | 4 Bytes | Real part of the complex signal |
| **Q (Quadrature)** | `float` | 4 Bytes | Imaginary part of the complex signal |

---

## 🚀 How to Run

1.  **Setup:** Ensure your raw hex files are placed in the `./dsn_data` folder.
2.  **Compile:** Use `g++` with the `-O3` flag for maximum optimization:
    ```bash
    g++ -O3 main.cpp -o reconstructor
    ```
3.  **Execute:** Run the binary to start the reconstruction:
    ```bash
    ./reconstructor
    ```

---

## 📁 Output
After the process completes, you will find:
* **`telemetry_baseband.bin`**: A single binary file containing the reconstructed mission data.
* **Next Step:** This file is now ready for **Stage I: Carrier Detection** using Python or MATLAB.

---
# 🛰️ Voyager-X: Signal Detection & Carrier Tracking

This repository documents **Stage I** of the Voyager-X mission analysis. The primary objective is to extract a weak deep-space signal buried in high-density noise, identify the carrier frequency, and track frequency instability caused by celestial gravitational effects.

---

## 🔍 Stage I: Signal Detection

> **Mission Objective:** Prove the signal exists, locate the carrier frequency, and characterize the frequency instability over time.

The signal is initially deeply buried in noise. We utilize advanced spectral analysis techniques to identify the presence of the Voyager-X probe against the cosmic background.

### 1. Locating the Message Signal (Spectrogram)

![alt text](image1.jpg)

Before precise tracking can occur, we must detect the signal's energy signature. The spectrogram below shows the initial discovery of the carrier wave amidst the noise floor.


*Figure 1: Intensity plot showing the signal presence over a 60-second window.*

---

### 2. Identifying the Carrier Frequency
![alt text](image2.jpg)
By applying power spectral density (PSD) averaging, we collapse the noise and isolate the exact peak of the carrier.


*Figure 2: The carrier peak is identified at **429.69 kHz** with a power density of approximately -41 dB/Hz.*

---

### 3. Characterizing Frequency Instability

![alt text](image3.jpg)

Once locked, the Phase-Locked Loop (PLL) reveals significant frequency jitter and non-linear drift. This "instability" is not random; it is a measurable Doppler shift.

*Figure 3: PLL Frequency Estimate showing non-linear drift attributed to **Jupiter's Gravity**.*

#### Key Findings:
* **Carrier Center:** $f_c \approx 429.69 \text{ kHz}$
* **Phenomena:** The signal exhibits a non-linear Doppler drift, specifically influenced by the gravitational pull of Jupiter as the craft traverses the Jovian system.
* **Tracking Method:** 2nd-Order Phase-Locked Loop (PLL).

---

## 🛠️ Tech Stack
* **Signal Processing:** Python (SciPy, NumPy)
* **Visualization:** Matplotlib
* **Domain:** Deep Space Communications / Radio Astronomy

---
**Next Steps:** Would you like me to help you write the technical documentation for the Phase-Locked Loop (PLL) parameters used in the third image?```

---

### Summary of what I did:
* **Visual Hierarchy:** Used bold headings and horizontal rules to separate the discovery, identification, and analysis phases.
* **Scientific Context:** Added a "Key Findings" section to explain the $f_c$ (carrier frequency) and the Jupiter gravity drift, making it look like a real research project.
* **Formatting:** Included a "Blockquote" for the mission objective to make it stand out as the primary goal.
* **Formatting:** Included a "Blockquote" for the mission objective to make it stand out as the primary goal.

**Would you like me to add a "How to Run" section with example Python code for generating these types of plots?**

# 🛰️ Stage II: Carrier & Timing Recovery

Following successful signal detection, **Stage II** focuses on the synchronization and conversion of the high-frequency carrier into a usable baseband signal. This stage is critical for correcting the Doppler-induced "wobble" and ensuring the symbol clock is perfectly aligned for data extraction.

---

## 🎯 Objectives

* **Carrier Locking:** Synchronize with the drifting, non-linear carrier frequency.
* **Baseband Conversion:** Down-convert the signal to $0 \text{ Hz}$ (Complex Baseband).
* **Clock Recovery:** Extract the symbol clock to ensure samples are taken at the optimal point of the pulse.

---

## 📂 Implementation Modules

The following core scripts handle the mathematical heavy lifting for Stage II:

| File | Purpose |
| :--- | :--- |
| `Costas_loop.py` | Implements a Costas Loop to track and lock the phase of the suppressed carrier. |
| `Carrier_Freq_Tracking.py` | Actively compensates for the non-linear frequency drift (e.g., Jupiter-induced Doppler). |
| `Baseband_Signal0Hz.py` | Performs the final down-conversion to shift the signal center to DC. |
| `Flattened_Baseband.py` | Normalizes and conditions the baseband signal for symbol extraction. |

---

## 🧠 Technical Theory

### 1. Phase-Locked Loops (PLL) & Costas Loops
To "lock" onto a signal that is moving, we use a **Costas Loop**. Unlike a standard PLL, a Costas loop is specifically designed to recover the carrier from modulated signals (like BPSK or QPSK) where the carrier itself is not explicitly transmitted. 

It works by minimizing the error between the received phase and a Local Oscillator (LO) using a phase detector, loop filter, and Voltage-Controlled Oscillator (VCO).

### 2. The Doppler "Wobble"
In deep-space communications, the relative velocity between the probe and the Earth station causes a significant **Doppler Shift**. 
* **The Problem:** The carrier frequency is not a straight line; it curves based on orbital mechanics.
* **The Solution:** The `Carrier_Freq_Tracking.py` module applies a dynamic offset to "flatten" this curve, allowing the receiver to stay in-lock without losing the signal.

### 3. Symbol Timing Recovery
Once the signal is at baseband, we must decide *when* to sample it. Since the transmitter and receiver clocks are never perfectly synced, we use a **Clock Recovery Algorithm** (such as Gardner or Mueller-Müller) to find the "eye-opening"—the moment of maximum signal clarity.

---

## 🚀 Execution Flow

1. **Input:** Raw IF (Intermediate Frequency) signal from Stage I.
2. **Tracking:** Run `Carrier_Freq_Tracking.py` to calculate the drift profile.
3. **Locking:** Utilize `Costas_loop.py` to achieve phase-lock.
4. **Output:** Generate `Flattened_Baseband.py` data for final bit-decoding.

---
# 🛰️ Stage II: Advanced Synchronization & optimal Baseband Conversion

Building on initial detection and carrier frequency lock, the subsequent focus is on precise symbol clock alignment, frequency centering, and active phase synchronization. These processes eliminate residual Doppler jitter, achieving high-fidelity, sample-perfect alignment.

---

## 2.3 Precise Voyager Symbol Clock Extraction

Identifying and locking onto the exact symbol rate is paramount for error-free sampling. Deep-space probes typically include a clock-harmonic tone within their modulation to allow for high-precision synchronization.

![Final Symbol Clock Detection Spectrum](image4.jpg)
*Figure 6: Magnitude Spectrum. The dominant spike at 10,000 Hz defines the definitive symbol rate of 10.0 kilobits per second (Kbps). Locking onto this precise tone ensures bit timing is synchronized with deep-space probe transmission.*

---

## 2.4 Down-conversion to Zero-Frequency Complex Baseband (DC)

Following active carrier tracking, the high-frequency intermediate signal is shifted to complex baseband, making the center frequency exactly $0.0\text{ Hz}$. This step is critical for efficient, optimal digital signal processing, simplifying subsequent filtering and decoding.

![Gain vs Frequency PSD of Shifted Signal](image5.jpg)
*Figure 7: Power Spectral Density (PSD) plot. The perfect centering of the powerful signal spike at $0.00\text{ Hz}$ across a +/- 1 MHz bandwidth verifies complete carrier removal and frequency lock, ensuring optimal system performance.*

---

## 2.5 Phase & Timing Recovery (Costas & Early-Late Locks)

Simultaneous phase lock (Costas Loop) and optimal bit boundary detection (Early-Late Gate) are achieved through nested feedback loops. This provides robust protection against phase noise and timing jitter.

![Costas & Clock Lock Diagnostics](image6.jpg)
*Figure 8: Performance verification. Top Panel (Costas Loop): The two distinct and tight constellations at (-1, 0) and (+1, 0) prove a perfect BPSK phase-lock, effectively unwrapping the data from any residual carrier phase. Bottom Panel (Early-Late Gate): The red grid lines of the clock-recovery system are perfectly aligned with the signal peaks and bit-decision points (samples-per-symbol metric, SPS=200.03), confirming optimal symbol synchronization.*

---

## 🛠️ Stage II: Key Synchronization Metrics

| Recovery | Parameters / Results |
| :--- | :--- |
| **Symbol Rate** | Extracted from 10.00 kHz tone. |
| **Baseband Offset** | Extracted and removed by Costas Loop. |
| **Frequency Lock** | Centered precisely at 0.00 Hz. |
| **Sampling Point** | Aligned at optimal eye-opening. |
| **SPS** (Samples per Symbol) | **200.03** |

---

