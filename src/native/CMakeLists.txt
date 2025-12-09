cmake_minimum_required(VERSION 3.20)

# STT Native Binary
add_executable(stt_native
    main.cpp
    wav_reader.cpp
    stt_engine.cpp
)

# whisper.cpp verlinken
target_link_libraries(stt_native PRIVATE whisper)

# Include-Pfade
target_include_directories(stt_native PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_SOURCE_DIR}/third_party/whisper.cpp
)

# Compiler-Warnungen
if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    target_compile_options(stt_native PRIVATE
        -Wall -Wextra -Wpedantic
        -Wno-unused-parameter
    )
endif()

# Optimierungen für Release
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    target_compile_options(stt_native PRIVATE -O3)
endif()
