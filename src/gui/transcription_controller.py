"""
Transcription-Controller für V-SpeechFlow

Extrahiert CLI-Argument-Building, Transkriptions-Orchestrierung
und Batch-Processing aus MainWindow.
"""

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer
from pathlib import Path
from .workers import CLIWorker
from .batch_window import BatchWorker
from .progress_tracker import ProgressTracker
from .translations import tr
from .constants import CLI_STOP_WAIT_MS, BATCH_STOP_WAIT_MS, PROGRESS_TIMER_MS


class TranscriptionController:
    """
    Orchestriert Einzel- und Batch-Transkriptionen.

    Args:
        main_window: Referenz auf das MainWindow
    """

    def __init__(self, main_window):
        self.mw = main_window

    def build_cli_arguments(self) -> list:
        """
        Baut die CLI-Argumente aus allen Panel-Einstellungen zusammen.

        Returns:
            Liste von CLI-Argumenten
        """
        args = []

        # Input-Datei
        input_file = self.mw.input_panel.get_selected_file()
        if input_file:
            args.extend(["--input", input_file])

        # Modell
        model_path = self.mw.model_panel.get_selected_model()
        if model_path:
            args.extend(["--model", model_path])

        # Settings
        settings = self.mw.settings_panel.get_settings()

        if 'threads' in settings:
            args.extend(["--threads", str(settings['threads'])])

        if 'language' in settings and settings['language'] != 'auto':
            args.extend(["-l", settings['language']])

        if settings.get('translate'):
            args.append("--translate")

        if settings.get('keep_temp'):
            args.append("--keep-temp")

        # Diarization
        diarization = self.mw.diarization_panel.get_settings()
        if diarization.get('enabled'):
            args.append("--diarize")

            if diarization.get('hf_token'):
                args.extend(["--hf-token", diarization['hf_token']])

            if diarization['mode'] == 'exact':
                args.extend(["--num-speakers", str(diarization['num_speakers'])])
            else:  # auto
                args.extend(["--min-speakers", str(diarization['min_speakers'])])
                args.extend(["--max-speakers", str(diarization['max_speakers'])])

        # Output
        output_settings = self.mw.output_panel.get_settings()

        output_path = self.mw.output_panel.get_output_path(input_file)
        args.extend(["--output", output_path])

        if output_settings.get('timestamps'):
            args.append("-s")

        # Binary Path (optional)
        binary_path = settings.get('binary_path')
        if binary_path and binary_path.strip():
            args.extend(["--binary", binary_path])

        return args

    def start_transcription(self):
        """Startet die Transkription mit vollständiger Validierung."""
        self.mw.log_info("=== Start Transkription angefordert ===")

        if self.mw.is_processing:
            self.mw.log_warning("Transkription bereits aktiv, Abbruch")
            QMessageBox.warning(
                self.mw, tr('main_already_active_title'), tr('main_already_active_msg')
            )
            return

        # Prüfen ob Batch-Modus aktiv ist
        if self.mw.input_panel.is_batch_mode():
            self.start_batch_processing()
            return

        # === Validierung aller Panels ===
        validation_errors = []

        input_file = self.mw.input_panel.get_selected_file()
        if not input_file:
            validation_errors.append(tr("validation_no_input"))

        model_path = self.mw.model_panel.get_selected_model()
        if not model_path:
            validation_errors.append(tr("validation_no_model"))

        diarization_settings = self.mw.diarization_panel.get_settings()
        if diarization_settings.get('enabled'):
            is_valid, error = self.mw.diarization_panel.validate_settings()
            if not is_valid:
                validation_errors.append(f"❌ Diarization: {error}")

        is_valid, error = self.mw.output_panel.validate_settings()
        if not is_valid:
            validation_errors.append(f"❌ Output: {error}")

        if validation_errors:
            self.mw.log_error(
                f"Validierungsfehler: {len(validation_errors)} Fehler gefunden"
            )
            for error in validation_errors:
                self.mw.log_error(f"  - {error}")
            error_message = (
                f"{tr('main_validation_fix_errors')}\n\n" +
                "\n".join(validation_errors)
            )
            QMessageBox.critical(
                self.mw, tr('main_validation_error_title'), error_message
            )
            return

        # === CLI-Argumente zusammenstellen ===
        try:
            cli_args = self.build_cli_arguments()
            self.mw.log_info(f"CLI-Argumente: {' '.join(cli_args)}")
        except Exception as e:
            self.mw.log_error(f"Fehler beim Erstellen der CLI-Argumente: {str(e)}")
            QMessageBox.critical(
                self.mw, tr('main_error'),
                f"{tr('main_cli_error')}\n{str(e)}"
            )
            return

        # === UI vorbereiten ===
        self.mw.output_preview.clear()
        self.mw.append_output(tr("transcription_started_msg") + "\n")
        self.mw.append_output(
            tr("transcription_command").format(cmd=' '.join(cli_args)) + "\n\n"
        )

        self.mw.is_processing = True
        self.mw.btn_start.setEnabled(False)
        self.mw.btn_stop.setEnabled(True)
        self.mw.progress_bar.setVisible(True)
        self.mw.progress_bar.setRange(0, 100)
        self.mw.progress_bar.setValue(0)
        self.mw.eta_label.setVisible(True)
        self.mw.eta_label.setText(tr("status_transcription_starting"))
        self.mw.statusBar().showMessage(tr("status_transcription_running"))

        # === CLI-Worker starten ===
        self.mw.log_info("CLI-Worker wird gestartet...")

        # Progress Tracker initialisieren
        self.mw.progress_tracker = ProgressTracker(
            has_diarization=diarization_settings.get('enabled', False)
        )
        self.mw.progress_tracker.start()

        # Versuche Audio-Länge zu ermitteln
        try:
            duration = self.mw.progress_tracker.get_audio_duration(input_file)
            if duration:
                self.mw.progress_tracker.set_audio_duration(duration)
        except Exception:
            pass  # Nicht kritisch

        self.mw.cli_worker = CLIWorker(cli_args)
        self.mw.cli_worker.output_received.connect(self.on_cli_output)
        self.mw.cli_worker.error_received.connect(self.on_cli_error)
        self.mw.cli_worker.process_finished.connect(self.on_cli_finished)
        self.mw.cli_worker.start()
        self.mw.log_info("CLI-Worker gestartet")

        # Progress Timer starten
        self.mw.progress_timer.start(PROGRESS_TIMER_MS)

        # === History speichern ===
        self.mw.history_manager.add_input_file(input_file)
        self.mw.history_manager.add_model(model_path)
        self.mw.session_manager.save_current_session()

    def stop_transcription(self):
        """Stoppt die Transkription."""
        if self.mw.is_batch_processing and self.mw.batch_worker:
            self.stop_batch_processing()
            return

        if not self.mw.is_processing or not self.mw.cli_worker:
            return

        self.mw.log_info("Stop Transkription angefordert")

        reply = QMessageBox.question(
            self.mw,
            tr('main_abort_transcription_title'),
            tr('main_abort_transcription_msg'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.mw.log_warning("Transkription wird abgebrochen...")
            self.mw.append_output("\n⏹️ Transkription wird abgebrochen...")
            self.mw.statusBar().showMessage("⏹️ Abbruch...")

            if self.mw.cli_worker:
                self.mw.cli_worker.stop()
                self.mw.cli_worker.wait(CLI_STOP_WAIT_MS)

                if self.mw.cli_worker.isRunning():
                    self.mw.cli_worker.terminate()
                    self.mw.cli_worker.wait()

            self.mw.append_output("❌ Transkription abgebrochen")
            self.mw.log_info("Transkription abgebrochen")
            self.mw.is_processing = False
            self.mw.progress_bar.setVisible(False)
            self.mw.eta_label.setVisible(False)
            self.mw.btn_start.setEnabled(True)
            self.mw.progress_timer.stop()
            self.mw.btn_stop.setEnabled(False)
            self.mw.statusBar().showMessage(tr("status_transcription_aborted"))
            self.mw.progress_tracker.reset()

    # ===== CLI-Worker Callbacks =====

    def on_cli_output(self, text: str):
        """Wird aufgerufen wenn CLI stdout Output empfängt."""
        self.mw.append_output(text)

        if self.mw.progress_tracker.parse_output_line(text):
            self._update_progress_ui()

    def on_cli_error(self, text: str):
        """Wird aufgerufen wenn CLI stderr Output empfängt."""
        text_lower = text.lower()

        if self.mw.progress_tracker.parse_output_line(text):
            self._update_progress_ui()

        # Debug-Präfixe von Whisper/ggml (keine echten Fehler)
        debug_prefixes = (
            'whisper_', 'ggml_', 'metal_', 'backend_', 'compute_',
            'encoder_', 'decoder_', 'kv_cache_', 'model_'
        )

        error_keywords = (
            'error:', 'failed:', 'exception:', 'traceback', 'cannot', 'unable to'
        )

        is_debug = any(text_lower.startswith(prefix) for prefix in debug_prefixes)
        is_error = any(keyword in text_lower for keyword in error_keywords)

        if is_error and not is_debug:
            self.mw.append_output(f"<span style='color: red;'>[ERROR] {text}</span>")
        elif is_debug:
            self.mw.append_output(f"<span style='color: #888;'>{text}</span>")
        else:
            self.mw.append_output(text)

    def on_cli_finished(self, return_code: int):
        """Wird aufgerufen wenn der CLI-Prozess beendet ist."""
        self.mw.log_info(f"CLI-Prozess beendet mit Exit-Code: {return_code}")
        self.mw.is_processing = False
        self.mw.progress_bar.setVisible(False)
        self.mw.eta_label.setVisible(False)
        self.mw.progress_timer.stop()

        self.mw.btn_start.setEnabled(True)
        self.mw.btn_stop.setEnabled(False)

        self.mw.progress_tracker.reset()
        self.mw.reset_diarization_warning()

        if return_code == 0:
            self.mw.append_output("\n" + "=" * 50)
            self.mw.append_output(tr("transcription_success_msg"))
            self.mw.append_output("=" * 50)

            input_file = self.mw.input_panel.get_selected_file()
            output_path = self.mw.output_panel.get_output_path(input_file)

            # Resolve actual file path if output_path is a directory
            resolved_path = Path(output_path)
            if resolved_path.is_dir():
                input_name = Path(input_file).stem if input_file else "recording"
                resolved_path = resolved_path / f"{input_name}_transcript.txt"
            output_file = str(resolved_path)

            self.mw.append_output(
                "\n" + tr("transcription_output_saved").format(path=output_file)
            )

            self.mw.history_manager.add_output_path(output_file)
            self.mw.menu_manager.update_recent_files_menu()
            self.mw.menu_manager.update_recent_models_menu()

            self.mw.statusBar().showMessage(tr("transcription_success_msg"))

            output_settings = self.mw.output_panel.get_settings()
            if output_settings.get('auto_open'):
                self.mw.open_output_file(output_file)

            QMessageBox.information(
                self.mw,
                tr('main_done'),
                f"{tr('main_transcription_success')}\n\n"
                f"{tr('main_file_saved_at')}\n{output_file}"
            )
        else:
            self.mw.append_output("\n" + "=" * 50)
            self.mw.append_output(
                f"❌ Transkription fehlgeschlagen (Exit Code: {return_code})"
            )
            self.mw.append_output("=" * 50)

            self.mw.statusBar().showMessage(
                f"❌ Transkription fehlgeschlagen (Code: {return_code})"
            )

            QMessageBox.critical(
                self.mw,
                tr('main_error'),
                f"{tr('main_transcription_failed', code=return_code)}\n\n"
                f"{tr('main_check_output')}"
            )

        # Worker cleanup
        if self.mw.cli_worker:
            self.mw.cli_worker.deleteLater()
            self.mw.cli_worker = None

    # ===== Progress =====

    def update_progress_display(self):
        """Aktualisiert die Progress-Anzeige regelmäßig."""
        if not self.mw.is_processing:
            return
        self._update_progress_ui()

    def _update_progress_ui(self):
        """Aktualisiert die Progress-UI basierend auf dem ProgressTracker."""
        progress_pct = self.mw.progress_tracker.get_progress_percentage()
        self.mw.progress_bar.setValue(int(progress_pct))

        status_text = self.mw.progress_tracker.get_status_text()
        phase_name = self.mw.progress_tracker.get_current_phase_name()
        elapsed = self.mw.progress_tracker.get_elapsed_time_str()

        self.mw.eta_label.setText(f"⚙️ {status_text} | 🕒 Verstrichen: {elapsed}")
        self.mw.statusBar().showMessage(
            f"⏳ {phase_name}: {progress_pct:.1f}%"
        )

    # ===== Batch-Processing =====

    def start_batch_processing(self):
        """Startet das Batch-Processing."""
        self.mw.log_info("=== Batch-Processing gestartet ===")

        files = self.mw.input_panel.get_batch_files()
        if not files:
            QMessageBox.warning(
                self.mw, tr('main_no_files_title'), tr('main_no_batch_files_msg')
            )
            return

        model_path = self.mw.model_panel.get_selected_model()
        if not model_path:
            QMessageBox.warning(
                self.mw, tr('main_no_model_title'), tr('main_no_model_msg')
            )
            return

        try:
            cli_args = self.build_cli_arguments()
            # --input entfernen (wird pro Datei im BatchWorker gesetzt)
            if "--input" in cli_args:
                input_index = cli_args.index("--input")
                cli_args.pop(input_index + 1)
                cli_args.pop(input_index)
            # --output entfernen (wird pro Datei im BatchWorker gesetzt)
            if "--output" in cli_args:
                output_index = cli_args.index("--output")
                cli_args.pop(output_index + 1)
                cli_args.pop(output_index)
        except Exception as e:
            QMessageBox.critical(
                self.mw, tr('main_error'), f"{tr('main_cli_error')}\n{str(e)}"
            )
            return

        batch_options = self.mw.input_panel.get_batch_options()

        # Output-Verzeichnis aus dem Output-Panel holen
        output_dir = self.mw.output_panel.get_output_path()

        self.mw.output_preview.clear()
        self.mw.append_output("=== Batch-Processing gestartet ===\n")
        self.mw.append_output(f"Dateien: {len(files)}\n")
        self.mw.append_output(f"Ausgabe-Verzeichnis: {output_dir}\n")
        self.mw.append_output(f"Optionen: {batch_options}\n\n")

        self.mw.is_processing = True
        self.mw.is_batch_processing = True
        self.mw.btn_start.setEnabled(False)
        self.mw.btn_stop.setEnabled(True)
        self.mw.progress_bar.setVisible(True)
        self.mw.progress_bar.setRange(0, len(files))
        self.mw.progress_bar.setValue(0)
        self.mw.eta_label.setVisible(True)
        self.mw.eta_label.setText(tr("status_batch_running"))
        self.mw.statusBar().showMessage(f"⏳ Batch-Processing: 0/{len(files)}")

        self.mw.batch_worker = BatchWorker(files, cli_args, batch_options, output_dir=output_dir)
        self.mw.batch_worker.progress.connect(self.on_batch_progress)
        self.mw.batch_worker.file_finished.connect(self.on_batch_file_finished)
        self.mw.batch_worker.batch_finished.connect(self.on_batch_finished)
        self.mw.batch_worker.output_received.connect(self.on_cli_output)
        self.mw.batch_worker.start()

        self.mw.log_info(f"Batch-Worker gestartet für {len(files)} Dateien")

    def stop_batch_processing(self):
        """Stoppt das Batch-Processing."""
        if not self.mw.batch_worker:
            return

        reply = QMessageBox.question(
            self.mw,
            tr('main_abort_batch_title'),
            tr('main_abort_batch_msg'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.mw.log_warning("Batch-Processing wird abgebrochen...")
            self.mw.append_output("\n⏹️ Batch-Processing wird abgebrochen...\n")

            if self.mw.batch_worker:
                self.mw.batch_worker.stop()
                self.mw.batch_worker.wait(BATCH_STOP_WAIT_MS)

                if self.mw.batch_worker.isRunning():
                    self.mw.batch_worker.terminate()
                    self.mw.batch_worker.wait()

            self.mw.append_output("❌ Batch-Processing abgebrochen\n")
            self.mw.log_info("Batch-Processing abgebrochen")
            self.cleanup_after_batch()

    def on_batch_progress(self, current: int, total: int, filename: str):
        """Wird bei Batch-Fortschritt aufgerufen."""
        self.mw.progress_bar.setValue(current)
        self.mw.statusBar().showMessage(
            f"⏳ Batch-Processing: {current}/{total} - {filename}"
        )
        self.mw.input_panel.batch_panel.set_progress(current, total, filename)

    def on_batch_file_finished(self, filepath: str, success: bool, message: str):
        """Wird aufgerufen wenn eine Datei fertig ist."""
        self.mw.log_info(f"Batch-Datei fertig: {filepath} - {message}")
        self.mw.reset_diarization_warning()

    def on_batch_finished(self, successful: int, failed: int, failed_files: list = None):
        """Wird aufgerufen wenn Batch fertig ist."""
        if failed_files is None:
            failed_files = []
        
        self.mw.log_info(
            f"Batch abgeschlossen: {successful} erfolgreich, {failed} fehlgeschlagen"
        )

        self.mw.append_output(f"\n{'=' * 60}\n")
        self.mw.append_output("=== Batch-Processing abgeschlossen ===\n")
        self.mw.append_output(f"✅ Erfolgreich: {successful}\n")
        self.mw.append_output(f"❌ Fehlgeschlagen: {failed}\n")

        # Detaillierte Fehlermeldung zusammenstellen
        msg = f"Batch-Processing abgeschlossen!\n\n" \
              f"✅ Erfolgreich: {successful}\n" \
              f"❌ Fehlgeschlagen: {failed}"
        
        if failed_files:
            msg += "\n\n--- Fehlgeschlagene Dateien ---"
            for fname, reason in failed_files:
                first_line = reason.strip().split('\n')[0]
                msg += f"\n• {fname}: {first_line}"
        
        if failed > 0:
            QMessageBox.warning(
                self.mw,
                tr("status_batch_done"),
                msg
            )
        else:
            QMessageBox.information(
                self.mw,
                tr("status_batch_done"),
                msg
            )

        self.cleanup_after_batch()

    def cleanup_after_batch(self):
        """Räumt nach Batch-Processing auf."""
        self.mw.is_processing = False
        self.mw.is_batch_processing = False
        self.mw.btn_start.setEnabled(True)
        self.mw.btn_stop.setEnabled(False)
        self.mw.progress_bar.setVisible(False)
        self.mw.eta_label.setVisible(False)
        self.mw.statusBar().showMessage(tr("status_batch_done"))
        self.mw.input_panel.batch_panel.reset_progress()
        self.mw.batch_worker = None
