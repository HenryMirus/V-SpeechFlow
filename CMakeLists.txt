cmake_minimum_required(VERSION 3.20)
project(V-SpeechFlow VERSION 1.0.0 LANGUAGES CXX C)

# C++17 Standard erforderlich
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# macOS/Apple Silicon spezifische Flags
if(APPLE)
    set(CMAKE_OSX_ARCHITECTURES "arm64" CACHE STRING "Build for Apple Silicon")
    set(CMAKE_OSX_DEPLOYMENT_TARGET "11.0" CACHE STRING "Minimum macOS version")
endif()

# Build-Typ: Release per Default für Optimierung
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Ausgabe in bin/ Verzeichnis
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# whisper.cpp als Submodul einbinden
set(WHISPER_BUILD_TESTS OFF CACHE BOOL "Build whisper tests" FORCE)
set(WHISPER_BUILD_EXAMPLES OFF CACHE BOOL "Build whisper examples" FORCE)

# Prüfen ob whisper.cpp vorhanden ist
if(EXISTS "${CMAKE_SOURCE_DIR}/third_party/whisper.cpp/CMakeLists.txt")
    add_subdirectory(third_party/whisper.cpp)
else()
    message(FATAL_ERROR "whisper.cpp not found! Run: git submodule update --init --recursive")
endif()

# Unser STT-Native Binary
add_subdirectory(src/native)
