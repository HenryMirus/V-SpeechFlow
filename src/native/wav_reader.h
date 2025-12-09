#pragma once

#include <string>
#include <vector>
#include <cstdint>

namespace vspeechflow {

/**
 * WAV-Header Struktur (simplified, für 16-bit PCM)
 */
struct WAVHeader {
    char riff[4];           // "RIFF"
    uint32_t file_size;
    char wave[4];           // "WAVE"
    char fmt[4];            // "fmt "
    uint32_t fmt_size;
    uint16_t audio_format;  // 1 = PCM
    uint16_t num_channels;
    uint32_t sample_rate;
    uint32_t byte_rate;
    uint16_t block_align;
    uint16_t bits_per_sample;
    char data[4];           // "data"
    uint32_t data_size;
} __attribute__((packed));

/**
 * WAVReader: Liest 16-bit PCM WAV-Dateien ein
 * 
 * Erwartet: 16kHz, mono, 16-bit PCM
 */
class WAVReader {
public:
    WAVReader() = default;
    ~WAVReader() = default;

    /**
     * Lädt eine WAV-Datei und konvertiert zu float32 für whisper.cpp
     * 
     * @param filepath Pfad zur WAV-Datei
     * @return true bei Erfolg, false bei Fehler
     */
    bool load(const std::string& filepath);

    /**
     * Gibt die Audio-Samples als float-Array zurück
     * Normalisiert auf [-1.0, 1.0]
     */
    const std::vector<float>& get_samples() const { return samples_; }

    /**
     * Sample-Rate der geladenen Datei
     */
    uint32_t get_sample_rate() const { return sample_rate_; }

    /**
     * Anzahl Kanäle
     */
    uint16_t get_num_channels() const { return num_channels_; }

    /**
     * Dauer in Sekunden
     */
    float get_duration() const;

private:
    std::vector<float> samples_;
    uint32_t sample_rate_ = 0;
    uint16_t num_channels_ = 0;
};

} // namespace vspeechflow
