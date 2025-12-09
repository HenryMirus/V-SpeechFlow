#include "wav_reader.h"
#include "stt_engine.h"
#include <iostream>
#include <fstream>
#include <string>
#include <cstring>
#include <cstdlib>

// Argumente-Struktur
struct Arguments {
    std::string model_path;
    std::string audio_file;
    std::string language = "de";
    std::string output_file;
    int num_threads = 4;
    bool show_segments = false;
    bool translate = false;
    bool help = false;
};

void print_usage(const char* prog_name) {
    std::cout << "Usage: " << prog_name << " [OPTIONS]\n\n"
              << "Options:\n"
              << "  -m, --model PATH       Path to ggml model file (required)\n"
              << "  -f, --file PATH        Path to WAV audio file (required)\n"
              << "  -l, --language CODE    Language code (default: de)\n"
              << "  -t, --threads N        Number of threads (default: 4)\n"
              << "  -o, --output PATH      Write transcript to file\n"
              << "  -s, --segments         Show segments with timestamps\n"
              << "  --translate            Translate to English\n"
              << "  -h, --help             Show this help\n\n"
              << "Example:\n"
              << "  " << prog_name << " -m models/ggml-small.bin -f audio.wav\n"
              << "  " << prog_name << " -m models/ggml-small.bin -f audio.wav -s -o output.txt\n";
}

Arguments parse_arguments(int argc, char* argv[]) {
    Arguments args;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];

        if (arg == "-h" || arg == "--help") {
            args.help = true;
        } else if (arg == "-m" || arg == "--model") {
            if (i + 1 < argc) {
                args.model_path = argv[++i];
            }
        } else if (arg == "-f" || arg == "--file") {
            if (i + 1 < argc) {
                args.audio_file = argv[++i];
            }
        } else if (arg == "-l" || arg == "--language") {
            if (i + 1 < argc) {
                args.language = argv[++i];
            }
        } else if (arg == "-t" || arg == "--threads") {
            if (i + 1 < argc) {
                args.num_threads = std::atoi(argv[++i]);
            }
        } else if (arg == "-o" || arg == "--output") {
            if (i + 1 < argc) {
                args.output_file = argv[++i];
            }
        } else if (arg == "-s" || arg == "--segments") {
            args.show_segments = true;
        } else if (arg == "--translate") {
            args.translate = true;
        }
    }

    return args;
}

std::string format_timestamp(int64_t ms) {
    int hours = ms / 3600000;
    int minutes = (ms % 3600000) / 60000;
    int seconds = (ms % 60000) / 1000;
    int millis = ms % 1000;

    char buffer[32];
    snprintf(buffer, sizeof(buffer), "%02d:%02d:%02d.%03d", 
             hours, minutes, seconds, millis);
    return std::string(buffer);
}

int main(int argc, char* argv[]) {
    std::cout << "V-SpeechFlow STT Native v1.0.0\n" << std::endl;

    Arguments args = parse_arguments(argc, argv);

    if (args.help) {
        print_usage(argv[0]);
        return 0;
    }

    // Validierung
    if (args.model_path.empty()) {
        std::cerr << "Error: Model path required (-m/--model)\n" << std::endl;
        print_usage(argv[0]);
        return 1;
    }

    if (args.audio_file.empty()) {
        std::cerr << "Error: Audio file required (-f/--file)\n" << std::endl;
        print_usage(argv[0]);
        return 1;
    }

    // WAV-Datei laden
    vspeechflow::WAVReader reader;
    if (!reader.load(args.audio_file)) {
        return 2;
    }

    // STT-Engine initialisieren
    vspeechflow::STTConfig config;
    config.model_path = args.model_path;
    config.language = args.language;
    config.num_threads = args.num_threads;
    config.translate = args.translate;
    config.print_timestamps = args.show_segments;

    vspeechflow::STTEngine engine;
    if (!engine.initialize(config)) {
        return 3;
    }

    std::cout << "\nStarting transcription...\n" << std::endl;

    // Transkription
    if (args.show_segments) {
        // Mit Segmenten
        auto segments = engine.transcribe_with_segments(reader.get_samples());
        
        std::cout << "\n=== Transcript (with timestamps) ===\n" << std::endl;
        
        for (const auto& seg : segments) {
            std::cout << "[" << format_timestamp(seg.start_ms) 
                      << " --> " << format_timestamp(seg.end_ms) 
                      << "] " << seg.text << std::endl;
        }

        // Ausgabe in Datei
        if (!args.output_file.empty()) {
            std::ofstream out(args.output_file);
            if (out.is_open()) {
                for (const auto& seg : segments) {
                    out << "[" << format_timestamp(seg.start_ms) 
                        << " --> " << format_timestamp(seg.end_ms) 
                        << "] " << seg.text << "\n";
                }
                out.close();
                std::cout << "\nTranscript saved to: " << args.output_file << std::endl;
            }
        }

    } else {
        // Nur Text
        std::string transcript = engine.transcribe(reader.get_samples());
        
        std::cout << "\n=== Transcript ===\n" << std::endl;
        std::cout << transcript << std::endl;

        // Ausgabe in Datei
        if (!args.output_file.empty()) {
            std::ofstream out(args.output_file);
            if (out.is_open()) {
                out << transcript << "\n";
                out.close();
                std::cout << "\nTranscript saved to: " << args.output_file << std::endl;
            }
        }
    }

    std::cout << "\nDone." << std::endl;
    return 0;
}
