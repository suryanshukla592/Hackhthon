#include <iostream>
#include <fstream>
#include <string>
#include <map>
#include <cstdint>
#include <cstring>
#include <dirent.h> 
#include <sstream>
#include <algorithm>

// This stores our signal data (I and Q parts)
struct IQSample {
    float i;
    float q;
};

// Helper function to turn the hex strings from the file into actual float numbers
float hexToFloat(const std::string& hexStr) {
    // Convert hex string to a 32-bit integer first
    uint32_t rawBits = std::stoul(hexStr, nullptr, 16);
    float result;
    // Copy the bits directly into a float variable
    std::memcpy(&result, &rawBits, sizeof(result));
    return result;
}

int main() {
    // Where the data is and what we want to call the finished file
    std::string inputDirectory = "./dsn_data"; 
    std::string outputFilename = "telemetry_baseband.bin";
    
    // We use a map so the files automatically sort themselves by the timestamp
    std::map<uint64_t, std::string> sortedFiles;

    std::cout << "Scanning directory for mission data...\n";

    // Standard code to open a folder and look inside
    DIR *dir;
    struct dirent *ent;
    if ((dir = opendir(inputDirectory.c_str())) != NULL) {
        while ((ent = readdir(dir)) != NULL) {
            std::string filename = ent->d_name;
            
            // Look for files that start with "dsn_capture_"
            if (filename.find("dsn_capture_") == 0) { 
                size_t extPos = filename.find(".txt");
                if (extPos != std::string::npos) {
                    // Pull out the number part of the filename to use as a sort key
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

    // Open the output file in binary mode so we don't mess up the float data
    std::ofstream outFile(outputFilename, std::ios::binary);
    if (!outFile.is_open()) {
        std::cerr << "Error: Could not create output file!\n";
        return 1;
    }

    int fileCount = 1;
    // Go through the files one by one in the right order
    for (const auto& pair : sortedFiles) {
        std::ifstream inFile(pair.second);
        
        // Print progress so we know the program hasn't crashed
        std::cout << "Processing: [" << fileCount << "/" << sortedFiles.size() << "] " 
                  << pair.second << "...\r" << std::flush;

        std::string line;
        while (std::getline(inFile, line)) {
            // Get rid of commas if the file has them
            std::replace(line.begin(), line.end(), ',', ' ');
            std::stringstream ss(line);
            std::string hexI, hexQ;
            
            // If we successfully find two strings in the line...
            if (ss >> hexI >> hexQ) {
                IQSample sample;
                // Convert them and save them to our struct
                sample.i = hexToFloat(hexI);
                sample.q = hexToFloat(hexQ);

                // Write the raw bytes of the struct to the binary file
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
