"""
Batch-Processing Window für V-SpeechFlow

Separates Fenster für Batch-Verarbeitung mehrerer Audio-Dateien.
"""

import subprocess
import sys
import time
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QTextEdit,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from .batch_panel import BatchPanel
from .translations import tr
import logging


class BatchWorker(QThread):
    """Worker-Thread für Batch-Processing."""
    
    progress = pyqtSignal(int, int, str)  # current, total, filename
    file_finished = pyqtSignal(str, bool, str)  # filepath, success, message
    batch_finished = pyqtSignal(int, int, list)  # successful, failed, error_details
    output_received = pyqtSignal(str)
    
    def __init__(self, files: list, cli_args_base: list, batch_options: dict, output_dir: str = None):
        super().__init__()
        self.files = files
        self.cli_args_base = cli_args_base
        self.batch_options = batch_options
        self.output_dir = output_dir  # Ausgabe-Verzeichnis aus dem Output-Panel
        self.should_stop = False
        self.current_process = None
    
    def _resolve_cli_script(self) -> str:
        """Findet den Pfad zum CLI-Script (gleiche Methode wie CLIWorker)."""
        project_root = Path(__file__).parent.parent
        cli_script = project_root / "python" / "stt_cli.py"
        return str(cli_script)
    
    def run(self):
        """Führt Batch-Processing aus."""
        total = len(self.files)
        successful = 0
        failed = 0
        failed_files = []  # Liste von (dateiname, fehlergrund)
        
        cli_script = self._resolve_cli_script()
        if not Path(cli_script).exists():
            self.output_received.emit(f"❌ CLI script not found: {cli_script}\n")
            self.batch_finished.emit(0, total)
            return
        
        for i, file_path in enumerate(self.files, 1):
            if self.should_stop:
                break
            
            file_name = Path(file_path).name
            self.progress.emit(i, total, file_name)
            self.output_received.emit(f"\n{'='*60}\n")
            self.output_received.emit(tr("batch_processing_item").format(current=i, total=total, name=file_name) + "\n")
            
            # CLI-Argumente für diese Datei zusammenstellen
            cli_args = self.cli_args_base.copy()
            
            # Input-Datei setzen
            if "--input" in cli_args:
                input_index = cli_args.index("--input")
                cli_args[input_index + 1] = file_path
            else:
                cli_args.extend(["--input", file_path])
            
            # Output-Datei anpassen (pro Datei eigener Output)
            input_path = Path(file_path)
            
            # Basis-Verzeichnis: Output-Panel-Pfad oder Fallback auf Input-Verzeichnis
            if self.output_dir:
                base_dir = Path(self.output_dir)
                # Falls output_dir ein Dateipfad ist, verwende das übergeordnete Verzeichnis
                if base_dir.suffix:
                    base_dir = base_dir.parent
            else:
                base_dir = input_path.parent
            
            base_dir.mkdir(parents=True, exist_ok=True)
            
            if self.batch_options.get('create_subfolder'):
                output_dir = base_dir / "batch-transcripts"
                output_dir.mkdir(exist_ok=True)
                output_path = output_dir / f"{input_path.stem}_transcript.txt"
            else:
                output_path = base_dir / f"{input_path.stem}_transcript.txt"
            
            if "--output" in cli_args:
                output_index = cli_args.index("--output")
                cli_args[output_index + 1] = str(output_path)
            else:
                cli_args.extend(["--output", str(output_path)])
            
            # CLI ausführen — gleiche Methode wie CLIWorker (Popen mit Echtzeit-Output)
            try:
                import threading
                
                cmd = [sys.executable, cli_script] + cli_args
                self.output_received.emit(f"🔧 {' '.join(cmd)}\n")
                
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                self.current_process = proc
                
                # Output in Echtzeit lesen — proc als lokale Variable
                # damit Closures nicht auf self.current_process referenzieren
                stderr_lines = []
                
                def read_stdout(p=proc):
                    for line in iter(p.stdout.readline, ''):
                        if line:
                            self.output_received.emit(line.rstrip())
                    p.stdout.close()
                
                def read_stderr(p=proc, err_lines=stderr_lines):
                    for line in iter(p.stderr.readline, ''):
                        if line:
                            stripped = line.rstrip()
                            err_lines.append(stripped)
                            self.output_received.emit(stripped)
                    p.stderr.close()
                
                stdout_thread = threading.Thread(target=read_stdout, daemon=True)
                stderr_thread = threading.Thread(target=read_stderr, daemon=True)
                stdout_thread.start()
                stderr_thread.start()
                
                return_code = proc.wait()
                # Warte bis Reader-Threads fertig sind (alle Pipe-Daten gelesen)
                stdout_thread.join(timeout=30)
                stderr_thread.join(timeout=30)
                self.current_process = None
                
                if return_code == 0:
                    # Prüfe ob die Output-Datei tatsächlich erstellt wurde
                    if output_path.exists() and output_path.stat().st_size > 0:
                        successful += 1
                        self.file_finished.emit(file_path, True, tr("batch_item_success"))
                        self.output_received.emit(f"✅ {file_name} {tr('batch_item_done')}\n")
                    else:
                        failed += 1
                        error_reason = f"Output-Datei wurde nicht erstellt: {output_path}"
                        failed_files.append((file_name, error_reason))
                        self.file_finished.emit(file_path, False, f"❌ {error_reason}")
                        self.output_received.emit(f"❌ {file_name}: {error_reason}\n")
                        
                        if self.batch_options.get('stop_on_error'):
                            self.output_received.emit(f"\n⚠️ {tr('batch_error_abort')}\n")
                            break
                else:
                    failed += 1
                    error_msg = "\n".join(stderr_lines[-5:]) if stderr_lines else tr("batch_unknown_error")
                    failed_files.append((file_name, error_msg))
                    self.file_finished.emit(file_path, False, f"❌ {tr('batch_error_prefix')}: {error_msg}")
                    self.output_received.emit(f"❌ {file_name} {tr('batch_item_failed')}: {error_msg}\n")
                    
                    if self.batch_options.get('stop_on_error'):
                        self.output_received.emit(f"\n⚠️ {tr('batch_error_abort')}\n")
                        break
            
            except Exception as e:
                self.current_process = None
                failed += 1
                error_reason = str(e)
                failed_files.append((file_name, error_reason))
                self.file_finished.emit(file_path, False, f"❌ Exception: {error_reason}")
                self.output_received.emit(f"❌ {file_name} {tr('batch_item_failed')}: {error_reason}\n")
                
                if self.batch_options.get('stop_on_error'):
                    break
            
            # Kurze Pause zwischen Dateien, damit Ressourcen freigegeben werden
            if i < total and not self.should_stop:
                time.sleep(2)
        
        # Fehlerzusammenfassung ausgeben
        if failed_files:
            self.output_received.emit(f"\n{'='*60}\n")
            self.output_received.emit("⚠️ Fehlgeschlagene Dateien:\n")
            for idx, (fname, reason) in enumerate(failed_files, 1):
                self.output_received.emit(f"  {idx}. {fname}")
                # Nur erste Zeile des Fehlers anzeigen für Übersicht
                first_line = reason.strip().split('\n')[0]
                self.output_received.emit(f"     Grund: {first_line}\n")
        
        self.batch_finished.emit(successful, failed, failed_files)
    
    def stop(self):
        """Stoppt den Batch-Prozess."""
        self.should_stop = True
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.current_process.kill()
                self.current_process.wait()
            except Exception:
                pass


class BatchWindow(QDialog):
    """Dialog-Fenster für Batch-Processing."""
    
    def __init__(self, parent, settings_getter):
        super().__init__(parent)
        self.setWindowTitle(tr("batch_window_title"))
        self.setGeometry(150, 150, 900, 700)
        self.setModal(False)
        
        self.settings_getter = settings_getter  # Funktion um aktuelle Settings zu holen
        self.batch_worker = None
        self.is_processing = False
        
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die UI."""
        layout = QVBoxLayout(self)
        
        # Batch Panel
        self.batch_panel = BatchPanel()
        layout.addWidget(self.batch_panel)
        
        # Output-Bereich
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText(tr("batch_output_placeholder"))
        self.output_text.setStyleSheet(
            "font-family: 'Consolas', 'Monaco', monospace; "
            "font-size: 9pt; background-color: #f5f5f5;"
        )
        self.output_text.setMaximumHeight(200)
        layout.addWidget(self.output_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("▶️ " + tr("batch_btn_start"))
        self.btn_start.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_start.clicked.connect(self.start_batch)
        button_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("⏹️ " + tr("batch_btn_cancel"))
        self.btn_stop.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 10px;")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_batch)
        button_layout.addWidget(self.btn_stop)
        
        self.btn_close = QPushButton("✕ " + tr("batch_btn_close"))
        self.btn_close.clicked.connect(self.close)
        button_layout.addWidget(self.btn_close)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def start_batch(self):
        """Startet Batch-Processing."""
        # Validierung
        files = self.batch_panel.get_file_list()
        
        if not files:
            QMessageBox.warning(self, tr("batch_no_files_window_title"), tr("batch_no_files_window_msg"))
            return
        
        # CLI-Argumente von Parent holen
        try:
            cli_args = self.settings_getter()
            
            # Entferne --input falls vorhanden (wird pro Datei gesetzt)
            if "--input" in cli_args:
                input_index = cli_args.index("--input")
                cli_args.pop(input_index + 1)  # Remove path
                cli_args.pop(input_index)  # Remove --input
            
        except Exception as e:
            QMessageBox.critical(self, tr("batch_error_args_title"), f"{tr('batch_error_args_msg')}:\n{str(e)}")
            return
        
        # Batch-Optionen
        batch_options = self.batch_panel.get_options()
        
        # UI vorbereiten
        self.output_text.clear()
        self.output_text.append(f"=== {tr('batch_started_header')} ===\\n")
        self.output_text.append(f"{tr('batch_files_count')}: {len(files)}\\n")
        self.output_text.append(f"{tr('batch_options_label')}: {batch_options}\\n")
        
        self.is_processing = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_close.setEnabled(False)
        
        # Worker starten
        self.batch_worker = BatchWorker(files, cli_args, batch_options)
        self.batch_worker.progress.connect(self.on_progress)
        self.batch_worker.file_finished.connect(self.on_file_finished)
        self.batch_worker.batch_finished.connect(self.on_batch_finished)
        self.batch_worker.output_received.connect(self.on_output)
        self.batch_worker.start()
    
    def stop_batch(self):
        """Stoppt Batch-Processing."""
        if self.batch_worker:
            reply = QMessageBox.question(
                self,
                tr("batch_cancel_confirm_title"),
                tr("batch_cancel_confirm_msg"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.batch_worker.stop()
                self.output_text.append(f"\\n⏹️ {tr('batch_abort_requested')}\\n")
    
    def on_progress(self, current: int, total: int, filename: str):
        """Wird aufgerufen bei Fortschritt."""
        self.batch_panel.set_progress(current, total, filename)
    
    def on_file_finished(self, filepath: str, success: bool, message: str):
        """Wird aufgerufen wenn eine Datei fertig ist."""
        pass  # Optionally update file list widget
    
    def on_batch_finished(self, successful: int, failed: int):
        """Wird aufgerufen wenn Batch fertig ist."""
        self.is_processing = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_close.setEnabled(True)
        
        self.batch_panel.reset_progress()
        
        self.output_text.append(f"\\n{'='*60}\\n")
        self.output_text.append(f"=== {tr('batch_done_header')} ===\\n")
        self.output_text.append(f"✅ {tr('batch_done_success')}: {successful}\\n")
        self.output_text.append(f"❌ {tr('batch_done_failed')}: {failed}\\n")
        
        QMessageBox.information(
            self,
            tr("batch_complete_title"),
            tr("batch_complete_msg", success=successful, failed=failed)
        )
    
    def on_output(self, text: str):
        """Wird aufgerufen bei Output."""
        self.output_text.append(text)
        self.output_text.verticalScrollBar().setValue(
            self.output_text.verticalScrollBar().maximum()
        )
    
    def closeEvent(self, event):
        """Verhindert Schließen während Verarbeitung."""
        if self.is_processing:
            QMessageBox.warning(
                self,
                tr("batch_running_title"),
                tr("batch_running_msg")
            )
            event.ignore()
        else:
            event.accept()
