#include "stt_engine.h"
#include "whisper.h"
#include <iostream>
#include <cstring>

namespace vspeechflow {

STTEngine::~STTEngine() {
    if (ctx_) {
        whisper_free(ctx_);
        ctx_ = nullptr;
    }
}

bool STTEngine::initialize(const STTConfig& config) {
    config_ = config;

    // Whisper-Kontext initialisieren
    struct whisper_context_params ctx_params = whisper_context_default_params();
    ctx_params.use_gpu = config.use_gpu;

    ctx_ = whisper_init_from_file_with_params(config.model_path.c_str(), ctx_params);
    
    if (!ctx_) {
        std::cerr << "Error: Failed to load model from " << config.model_path << std::endl;
        return false;
    }

    std::cout << "Model loaded successfully: " << config.model_path << std::endl;
    std::cout << "  Language: " << config.language << std::endl;
    std::cout << "  Threads: " << config.num_threads << std::endl;

    return true;
}

std::string STTEngine::transcribe(const std::vector<float>& samples) {
    if (!ctx_) {
        std::cerr << "Error: Engine not initialized" << std::endl;
        return "";
    }

    if (samples.empty()) {
        std::cerr << "Error: No audio samples provided" << std::endl;
        return "";
    }

    // Whisper-Parameter konfigurieren
    struct whisper_full_params wparams = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
    
    wparams.n_threads = config_.num_threads;
    wparams.translate = config_.translate;
    wparams.print_progress = false;
    wparams.print_realtime = false;
    wparams.print_timestamps = false;

    // Sprache setzen
    if (config_.language != "auto") {
        wparams.language = config_.language.c_str();
    }

    // Transkription durchführen
    std::cout << "Processing " << samples.size() << " samples..." << std::endl;
    
    const int result = whisper_full(ctx_, wparams, samples.data(), samples.size());
    
    if (result != 0) {
        std::cerr << "Error: Transcription failed with code " << result << std::endl;
        return "";
    }

    // Ergebnis zusammenbauen
    const int n_segments = whisper_full_n_segments(ctx_);
    std::string full_text;

    for (int i = 0; i < n_segments; ++i) {
        const char* text = whisper_full_get_segment_text(ctx_, i);
        if (text) {
            full_text += text;
        }
    }

    return full_text;
}

std::vector<TranscriptSegment> STTEngine::transcribe_with_segments(
    const std::vector<float>& samples) {
    
    std::vector<TranscriptSegment> segments;

    if (!ctx_) {
        std::cerr << "Error: Engine not initialized" << std::endl;
        return segments;
    }

    if (samples.empty()) {
        std::cerr << "Error: No audio samples provided" << std::endl;
        return segments;
    }

    // Whisper-Parameter konfigurieren
    struct whisper_full_params wparams = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
    
    wparams.n_threads = config_.num_threads;
    wparams.translate = config_.translate;
    wparams.print_progress = false;
    wparams.print_realtime = false;
    wparams.print_timestamps = config_.print_timestamps;

    if (config_.language != "auto") {
        wparams.language = config_.language.c_str();
    }

    // Transkription durchführen
    std::cout << "Processing " << samples.size() << " samples..." << std::endl;
    
    const int result = whisper_full(ctx_, wparams, samples.data(), samples.size());
    
    if (result != 0) {
        std::cerr << "Error: Transcription failed with code " << result << std::endl;
        return segments;
    }

    // Segmente extrahieren
    const int n_segments = whisper_full_n_segments(ctx_);
    segments.reserve(n_segments);

    for (int i = 0; i < n_segments; ++i) {
        const char* text = whisper_full_get_segment_text(ctx_, i);
        const int64_t t0 = whisper_full_get_segment_t0(ctx_, i);
        const int64_t t1 = whisper_full_get_segment_t1(ctx_, i);

        if (text) {
            TranscriptSegment seg;
            seg.text = text;
            seg.start_ms = t0 * 10;  // whisper gibt in 10ms-Einheiten zurück
            seg.end_ms = t1 * 10;
            segments.push_back(seg);
        }
    }

    return segments;
}

} // namespace vspeechflow
