#include <iostream>
#include <fstream>
#include <string>
#include <map>
#include <cstdint>
#include <cstring>
#include <dirent.h> 
#include <sstream>
#include <algorithm>

struct IQSample {
    float i;
    float q;
};

float hexToFloat(const std::string& hexStr) {
    // stoul handles "0x" automatically
    uint32_t rawBits = std::stoul(hexStr, nullptr, 16);
    float result;
    std::memcpy(&result, &rawBits, sizeof(result));
    return result;
}

int main() {
    std::string inputDirectory = "./dsn_data"; 
    std::string outputFilename = "telemetry_baseband.bin";
    std::map<uint64_t, std::string> sortedFiles;

    std::cout << "Scanning directory for mission data...\n";

    DIR *dir;
    struct dirent *ent;
    if ((dir = opendir(inputDirectory.c_str())) != NULL) {
        while ((ent = readdir(dir)) != NULL) {
            std::string filename = ent->d_name;
            if (filename.find("dsn_capture_") == 0) { 
                size_t extPos = filename.find(".txt");
                if (extPos != std::string::npos) {
                    std::string tsStr = filename.substr(12, extPos - 12);
                    sortedFiles[std::stoull(tsStr)] = inputDirectory + "/" + filename;
                }
            }
        }
        closedir(dir);
    } else {
        std::cerr << "Error: Folder 'dsn_data' not found!\n";
        return 1;
    }

    std::cout << "Detected " << sortedFiles.size() << " files for processing.\n";

    // Open file in binary mode (this will OVERWRITE the old small file)
    std::ofstream outFile(outputFilename, std::ios::binary);
    if (!outFile.is_open()) {
        std::cerr << "Error: Could not create output file!\n";
        return 1;
    }

    int fileCount = 1;
    for (const auto& pair : sortedFiles) {
        std::ifstream inFile(pair.second);
        
        // Progress bar so you know it's working
        std::cout << "Processing: [" << fileCount << "/" << sortedFiles.size() << "] " 
                  << pair.second << "...\r" << std::flush;

        std::string line;
        while (std::getline(inFile, line)) {
            // Scrub commas
            std::replace(line.begin(), line.end(), ',', ' ');
            std::stringstream ss(line);
            std::string hexI, hexQ;
            
            if (ss >> hexI >> hexQ) {
                IQSample sample;
                sample.i = hexToFloat(hexI);
                sample.q = hexToFloat(hexQ);

                outFile.write(reinterpret_cast<const char*>(&sample), sizeof(IQSample));
            }
        }
        fileCount++;
    }

    outFile.close();
    std::cout << "\n\nMISSION DATA RECONSTRUCTED!\n";
    std::cout << "Final file: " << outputFilename << "\n";
    std::cout << "You can now run Stage I (Python) to find the carrier.\n";

    return 0;
}