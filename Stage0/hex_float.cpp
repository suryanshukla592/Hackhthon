#include <iostream>
#include <fstream>
#include <string>
#include <map>
#include <cstdint>
#include <cstring>
#include <dirent.h> 
#include <sstream>
#include <algorithm>

// Standard IQ Sample structure
struct IQSample {
    float i;
    float q;
};

// Robust hex-to-float conversion for IEEE 754
float hexToFloat(const std::string& hexStr) {
    try {
        // stoul handles "0x" prefix or raw hex automatically
        uint32_t rawBits = std::stoul(hexStr, nullptr, 16);
        float result;
        
        // This is the standard way to map bits to float without type-punning UB
        std::memcpy(&result, &rawBits, sizeof(result));
        return result;
    } catch (...) {
        return 0.0f; // Return 0 if the hex string is malformed
    }
}

int main() {
    std::string inputDirectory = "./dsn_data"; 
    std::string outputFilename = "telemetry_baseband.bin";
    std::map<uint64_t, std::string> sortedFiles;

    // ... (Your directory scanning code remains the same) ...

    std::ofstream outFile(outputFilename, std::ios::binary);
    if (!outFile.is_open()) {
        std::cerr << "Error: Could not create output file!\n";
        return 1;
    }

    for (const auto& [timestamp, filePath] : sortedFiles) {
        std::ifstream inFile(filePath);
        std::string line;

        while (std::getline(inFile, line)) {
            // Remove commas or semicolons commonly found in CSV-style telemetry
            std::replace(line.begin(), line.end(), ',', ' ');
            std::replace(line.begin(), line.end(), ';', ' ');

            std::stringstream ss(line);
            std::string hexI, hexQ;
            
            if (ss >> hexI >> hexQ) {
                IQSample sample;
                sample.i = hexToFloat(hexI);
                sample.q = hexToFloat(hexQ);

                // Writing as raw binary (4 bytes for I, 4 bytes for Q)
                outFile.write(reinterpret_cast<const char*>(&sample), sizeof(IQSample));
            }
        }
    }

    outFile.close();
    std::cout << "\nConversion Complete. Binary floats written to " << outputFilename << "\n";
    return 0;
}
