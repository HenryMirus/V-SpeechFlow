#pragma once

#include <string>
#include <vector>
#include <memory>

// Forward-Declaration für whisper.cpp
struct whisper_context;

namespace vspeechflow {

/**
 * Segment einer Transkription mit Zeitstempel
 */
struct TranscriptSegment {
    int64_t start_ms;    // Start in Millisekunden
    int64_t end_ms;      // Ende in Millisekunden
    std::string text;    // Transkribierter Text
};

/**
 * Konfiguration für STT-Engine
 */
struct STTConfig {
    std::string model_path;         // Pfad zum ggml-Modell
    std::string language = "de";    // Sprache (z.B. "de", "en", "auto")
    int num_threads = 4;            // Anzahl Threads
    bool translate = false;         // Ins Englische übersetzen?
    bool print_timestamps = false;  // Segmente mit Timestamps ausgeben?
    bool use_gpu = false;           // GPU-Beschleunigung (falls verfügbar)
};

/**
 * STT-Engine: Wrapper um whisper.cpp
 */
class STTEngine {
public:
    STTEngine() = default;
    ~STTEngine();

    // Nicht kopierbar
    STTEngine(const STTEngine&) = delete;
    STTEngine& operator=(const STTEngine&) = delete;

    /**
     * Initialisiert die Engine mit einem Whisper-Modell
     * 
     * @param config Konfiguration
     * @return true bei Erfolg
     */
    bool initialize(const STTConfig& config);

    /**
     * Transkribiert Audio-Samples
     * 
     * @param samples Float-Array mit normalisierten Samples [-1.0, 1.0]
     * @return Vollständiger Transkript-Text
     */
    std::string transcribe(const std::vector<float>& samples);

    /**
     * Transkribiert mit Segment-Informationen
     * 
     * @param samples Float-Array mit normalisierten Samples
     * @return Vektor von Segmenten mit Timestamps
     */
    std::vector<TranscriptSegment> transcribe_with_segments(
        const std::vector<float>& samples);

    /**
     * Prüft, ob die Engine initialisiert ist
     */
    bool is_initialized() const { return ctx_ != nullptr; }

private:
    whisper_context* ctx_ = nullptr;
    STTConfig config_;
};

} // namespace vspeechflow
