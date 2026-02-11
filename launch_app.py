#!/usr/bin/env python3
"""
V-SpeechFlow Launcher
Prüft Dependencies, kompiliert das Projekt und startet die GUI ohne run_dev.py.
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path

# Farben für Terminal-Ausgabe
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Gibt einen formatierten Header aus."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}\n")


def print_success(text):
    """Gibt eine Erfolgsmeldung aus."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_warning(text):
    """Gibt eine Warnung aus."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text):
    """Gibt einen Fehler aus."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text):
    """Gibt eine Info aus."""
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")


def check_command(command, name):
    """Prüft ob ein Befehl verfügbar ist."""
    return shutil.which(command) is not None


def check_dependencies():
    """Prüft alle System-Dependencies."""
    print_header("Prüfe System-Dependencies")
    
    missing = []
    
    # CMake
    if check_command("cmake", "CMake"):
        print_success("CMake ist installiert")
    else:
        print_error("CMake ist nicht installiert")
        missing.append(("CMake", "brew install cmake"))
    
    # ffmpeg
    if check_command("ffmpeg", "ffmpeg"):
        print_success("ffmpeg ist installiert")
    else:
        print_error("ffmpeg ist nicht installiert")
        missing.append(("ffmpeg", "brew install ffmpeg"))
    
    # PortAudio (für Live-Recording)
    try:
        result = subprocess.run(
            ["brew", "list", "portaudio"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
        if result.returncode == 0:
            print_success("PortAudio ist installiert")
        else:
            print_warning("PortAudio ist nicht installiert (optional für Live-Recording)")
            missing.append(("PortAudio", "brew install portaudio"))
    except:
        print_warning("Brew nicht gefunden, kann PortAudio nicht prüfen")
    
    return missing


def setup_virtual_environment():
    """Erstellt und aktiviert ein virtuelles Environment."""
    print_header("Prüfe Python Virtual Environment")
    
    project_root = Path(__file__).parent
    venv_path = project_root / ".venv"
    
    # Prüfe ob venv existiert
    if venv_path.exists():
        print_success(f"Virtual Environment gefunden: {venv_path}")
        return venv_path
    
    print_info("Erstelle Virtual Environment...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True
        )
        print_success("Virtual Environment erstellt")
        return venv_path
    except subprocess.CalledProcessError as e:
        print_error(f"Fehler beim Erstellen des Virtual Environments: {e}")
        return None


def install_python_dependencies(venv_path):
    """Installiert Python-Dependencies im Virtual Environment."""
    print_header("Installiere Python-Dependencies")
    
    project_root = Path(__file__).parent
    requirements_file = project_root / "requirements.txt"
    
    if not requirements_file.exists():
        print_error(f"requirements.txt nicht gefunden: {requirements_file}")
        return False
    
    # Python im venv verwenden
    venv_python = venv_path / "bin" / "python"
    if not venv_python.exists():
        print_error(f"Python im venv nicht gefunden: {venv_python}")
        return False
    
    print_info("Installiere Python-Dependencies im Virtual Environment...")
    
    try:
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.DEVNULL
        )
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", str(requirements_file)],
            check=True
        )
        print_success("Python-Dependencies installiert")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Fehler beim Installieren der Python-Dependencies: {e}")
        return False


def check_and_compile():
    """Prüft ob das Binary existiert, kompiliert falls nötig."""
    print_header("Prüfe C++ Binary")
    
    project_root = Path(__file__).parent
    binary_path = project_root / "build" / "bin" / "stt_native"
    
    if binary_path.exists():
        print_success(f"Binary gefunden: {binary_path}")
        return True
    
    print_warning("Binary nicht gefunden, starte Kompilierung...")
    
    # Prüfe ob CMakeLists.txt existiert
    cmake_file = project_root / "CMakeLists.txt"
    if not cmake_file.exists():
        print_error("CMakeLists.txt nicht gefunden!")
        return False
    
    # Build-Verzeichnis erstellen
    build_dir = project_root / "build"
    build_dir.mkdir(exist_ok=True)
    
    try:
        # CMake konfigurieren
        print_info("Konfiguriere mit CMake...")
        subprocess.run(
            ["cmake", "..", "-DCMAKE_BUILD_TYPE=Release"],
            cwd=build_dir,
            check=True
        )
        
        # Kompilieren
        print_info("Kompiliere Projekt...")
        subprocess.run(
            ["cmake", "--build", ".", "--config", "Release", "-j"],
            cwd=build_dir,
            check=True
        )
        
        # Prüfen ob Binary jetzt existiert
        if binary_path.exists():
            print_success("Kompilierung erfolgreich!")
            return True
        else:
            print_error("Kompilierung abgeschlossen, aber Binary nicht gefunden")
            return False
            
    except subprocess.CalledProcessError as e:
        print_error(f"Fehler bei der Kompilierung: {e}")
        return False


def check_submodules():
    """Prüft ob Git-Submodule initialisiert sind."""
    print_header("Prüfe Git-Submodule")
    
    project_root = Path(__file__).parent
    whisper_dir = project_root / "third_party" / "whisper.cpp"
    
    if not whisper_dir.exists() or not any(whisper_dir.iterdir()):
        print_warning("whisper.cpp Submodul nicht initialisiert")
        print_info("Initialisiere Submodule...")
        
        try:
            subprocess.run(
                ["git", "submodule", "update", "--init", "--recursive"],
                cwd=project_root,
                check=True
            )
            print_success("Submodule initialisiert")
            return True
        except subprocess.CalledProcessError as e:
            print_error(f"Fehler beim Initialisieren der Submodule: {e}")
            return False
    else:
        print_success("whisper.cpp Submodul vorhanden")
        return True


def start_gui(venv_path):
    """Startet die GUI-Anwendung im Virtual Environment."""
    print_header("Starte V-SpeechFlow GUI")
    
    project_root = Path(__file__).parent
    
    # Python im venv verwenden
    venv_python = venv_path / "bin" / "python"
    
    # Starte die GUI im venv
    startup_script = project_root / "src" / "gui" / "app.py"
    
    try:
        # Starte als subprocess im venv
        subprocess.run(
            [str(venv_python), "-m", "src.gui.app"],
            cwd=project_root,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print_error(f"Fehler beim Starten der GUI: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n")
        print_info("GUI beendet")
        sys.exit(0)


def main():
    """Haupteinstiegspunkt."""
    print_header("V-SpeechFlow Launcher")
    print_info("Offline Speech-to-Text für macOS")
    
    # 1. System-Dependencies prüfen
    missing_deps = check_dependencies()
    
    if missing_deps:
        print_header("Fehlende Dependencies")
        print_warning("Folgende System-Dependencies fehlen:")
        for name, cmd in missing_deps:
            print(f"   • {name}: {Colors.OKCYAN}{cmd}{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}Installiere die fehlenden Dependencies und starte dann erneut.{Colors.ENDC}\n")
        sys.exit(1)
    
    # 2. Git-Submodule prüfen
    if not check_submodules():
        sys.exit(1)
    
    # 3. Virtual Environment einrichten
    venv_path = setup_virtual_environment()
    if not venv_path:
        sys.exit(1)
    
    # 4. Python-Dependencies installieren
    if not install_python_dependencies(venv_path):
        sys.exit(1)
    
    # 5. C++ Binary prüfen/kompilieren
    if not check_and_compile():
        sys.exit(1)
    
    # 6. GUI starten
    print_success("Alle Voraussetzungen erfüllt!\n")
    start_gui(venv_path)


if __name__ == "__main__":
    main()
