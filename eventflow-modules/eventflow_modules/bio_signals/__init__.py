"""Bio-signals module exports for medical applications. Supports ECG, EEG, and EMG processing."""
from __future__ import annotations
from .ecg import ecg_processing
from .eeg import eeg_processing
from .emg import emg_processing
__all__ = ["ecg_processing", "eeg_processing", "emg_processing"]