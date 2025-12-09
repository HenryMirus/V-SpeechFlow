#include "wav_reader.h"
#include <fstream>
#include <iostream>
#include <cstring>

namespace vspeechflow {

bool WAVReader::load(const std::string& filepath) {
    std::ifstream file(filepath, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "Error: Cannot open WAV file: " << filepath << std::endl;
        return false;
    }

    // Header einlesen
    WAVHeader header;
    file.read(reinterpret_cast<char*>(&header), sizeof(WAVHeader));

    // Validierung
    if (std::strncmp(header.riff, "RIFF", 4) != 0 ||
        std::strncmp(header.wave, "WAVE", 4) != 0) {
        std::cerr << "Error: Not a valid WAV file (missing RIFF/WAVE)" << std::endl;
        return false;
    }

    if (header.audio_format != 1) {
        std::cerr << "Error: Only PCM format supported (audio_format=" 
                  << header.audio_format << ")" << std::endl;
        return false;
    }

    if (header.bits_per_sample != 16) {
        std::cerr << "Error: Only 16-bit samples supported (bits_per_sample=" 
                  << header.bits_per_sample << ")" << std::endl;
        return false;
    }

    sample_rate_ = header.sample_rate;
    num_channels_ = header.num_channels;

    // Warnung bei nicht-idealer Konfiguration
    if (sample_rate_ != 16000) {
        std::cerr << "Warning: Sample rate is " << sample_rate_ 
                  << "Hz, recommended is 16000Hz" << std::endl;
    }

    if (num_channels_ != 1) {
        std::cerr << "Warning: Audio has " << num_channels_ 
                  << " channel(s), mono recommended" << std::endl;
    }

    // Audio-Daten einlesen
    const size_t num_samples = header.data_size / (header.bits_per_sample / 8);
    std::vector<int16_t> raw_samples(num_samples);
    
    file.read(reinterpret_cast<char*>(raw_samples.data()), header.data_size);
    
    if (!file) {
        std::cerr << "Error: Failed to read audio data" << std::endl;
        return false;
    }

    // Konvertierung: int16 -> float32 [-1.0, 1.0]
    samples_.resize(num_samples);
    for (size_t i = 0; i < num_samples; ++i) {
        samples_[i] = static_cast<float>(raw_samples[i]) / 32768.0f;
    }

    // Bei Stereo: Nur linken Kanal nehmen (vereinfacht)
    if (num_channels_ == 2) {
        std::vector<float> mono_samples;
        mono_samples.reserve(num_samples / 2);
        for (size_t i = 0; i < num_samples; i += 2) {
            mono_samples.push_back(samples_[i]);
        }
        samples_ = std::move(mono_samples);
        num_channels_ = 1;
    }

    file.close();
    
    std::cout << "Loaded WAV: " << filepath << std::endl;
    std::cout << "  Sample rate: " << sample_rate_ << " Hz" << std::endl;
    std::cout << "  Channels: " << num_channels_ << std::endl;
    std::cout << "  Duration: " << get_duration() << " seconds" << std::endl;
    std::cout << "  Samples: " << samples_.size() << std::endl;

    return true;
}

float WAVReader::get_duration() const {
    if (sample_rate_ == 0) return 0.0f;
    return static_cast<float>(samples_.size()) / static_cast<float>(sample_rate_);
}

} // namespace vspeechflow
