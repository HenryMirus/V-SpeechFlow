"""
py2app Setup-Script für V-SpeechFlow
Erstellt eine macOS .app Bundle
"""

from setuptools import setup
from pathlib import Path

APP = ['launch_app.py']
DATA_FILES = [
    ('build/bin', ['build/bin/stt_native']),
    ('third_party/whisper.cpp', []),  # Submodule
]

OPTIONS = {
    'argv_emulation': False,
    'packages': [
        'PyQt6',
        'torch',
        'torchaudio',
        'torchcodec',
        'pyannote.audio',
        'numpy',
        'rich',
        'requests',
        'watchdog',
    ],
    'includes': [
        'src.gui',
        'src.python',
    ],
    'excludes': [
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
    ],
    'iconfile': None,  # Optional: Icon hinzufügen
    'plist': {
        'CFBundleName': 'V-SpeechFlow',
        'CFBundleDisplayName': 'V-SpeechFlow',
        'CFBundleIdentifier': 'com.vspeechflow.app',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'NSMicrophoneUsageDescription': 'V-SpeechFlow benötigt Zugriff auf das Mikrofon für Live-Transkription.',
        'NSAppleEventsUsageDescription': 'V-SpeechFlow benötigt Zugriff für Automatisierung.',
        'LSMinimumSystemVersion': '11.0',
        'NSHighResolutionCapable': True,
    },
    'semi_standalone': False,
    'site_packages': True,
}

setup(
    name='V-SpeechFlow',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    version='0.1.0',
    description='Offline Speech-to-Text für macOS',
    author='V-SpeechFlow Team',
)
