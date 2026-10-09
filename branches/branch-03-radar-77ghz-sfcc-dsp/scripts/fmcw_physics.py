#!/usr/bin/env python3
"""
fmcw_physics.py
-------------------------------------------------------------------------------
Person 3 Module: 77 GHz FMCW Radar Physics & Signal Model.

Core FMCW equations used throughout the pipeline:

  Beat Frequency (range):
      f_beat = (B / T_c) * (2 * d / c)
  => d = (f_beat * c * T_c) / (2 * B)

  Range Resolution:
      delta_R = c / (2 * B)

  Maximum Unambiguous Range:
      R_max = (c * T_c * fs) / (4 * B)

  Doppler Velocity:
      v = (f_doppler * c) / (2 * f_c)

  Radar Cross Section Contrast (water vs asphalt):
      RCS_water_asphalt_delta ≈ +20 dB
      (epsilon_r_water ≈ 80  vs  epsilon_r_asphalt ≈ 4)
      => Reflection coefficient ratio = sqrt(80/4) = sqrt(20) ≈ 4.5x
      => 20*log10(4.5) ≈ 13 dB (per-face), accumulated +20 dB for waterlogged void
-------------------------------------------------------------------------------
"""

import numpy as np

# === RADAR HARDWARE PARAMETERS (TI IWR1443BOOST) ===
RADAR_PARAMS = {
    'f_c':            77.0e9,      # Center frequency (77 GHz)
    'bandwidth':      4.0e9,       # Sweep bandwidth = 4 GHz -> delta_R = 3.75 cm
    'T_chirp':        40e-6,       # Chirp duration (40 microseconds)
    'fs':             10e6,        # ADC sampling rate (10 Msps)
    'N_samples':      256,         # Samples per chirp
    'N_chirps':       128,         # Chirps per frame
    'N_tx':           2,           # Transmit antennas
    'N_rx':           4,           # Receive antennas
    'c':              3e8,         # Speed of light (m/s)
    'lambda_':        3e8 / 77e9,  # Wavelength = 3.9 mm
}

# === DIELECTRIC CONSTANTS (key to pothole detection physics) ===
EPSILON_R = {
    'dry_asphalt':    4.0,
    'dry_concrete':   10.0,
    'air_void':       1.0,
    'turbid_water':   80.0,    # Water-filled pothole -> MASSIVE RCS spike
    'wet_asphalt':    15.0,
}

def beat_frequency_to_range(f_beat_hz: float) -> float:
    """Convert FMCW IF beat frequency to distance in meters."""
    p = RADAR_PARAMS
    return (f_beat_hz * p['c'] * p['T_chirp']) / (2.0 * p['bandwidth'])

def range_to_beat_frequency(d_m: float) -> float:
    """Convert distance (m) to expected FMCW IF beat frequency (Hz)."""
    p = RADAR_PARAMS
    return (2.0 * d_m * p['bandwidth']) / (p['c'] * p['T_chirp'])

def range_resolution() -> float:
    """Returns theoretical range resolution in meters for given bandwidth."""
    return RADAR_PARAMS['c'] / (2.0 * RADAR_PARAMS['bandwidth'])

def max_range() -> float:
    """Returns maximum unambiguous range in meters."""
    p = RADAR_PARAMS
    return (p['c'] * p['T_chirp'] * p['fs']) / (4.0 * p['bandwidth'])

def doppler_to_velocity(f_doppler_hz: float) -> float:
    """Convert Doppler frequency shift to radial velocity (m/s)."""
    p = RADAR_PARAMS
    return (f_doppler_hz * p['c']) / (2.0 * p['f_c'])

def compute_rcs_contrast(eps_r_target: float, eps_r_background: float) -> float:
    """
    Computes approximate Radar Cross Section (RCS) contrast in dB
    between a target and background medium based on reflection coefficient.
    """
    r_target = (np.sqrt(eps_r_target) - 1) / (np.sqrt(eps_r_target) + 1)
    r_bg     = (np.sqrt(eps_r_background) - 1) / (np.sqrt(eps_r_background) + 1)
    if r_bg == 0:
        return float('inf')
    rcs_db = 20 * np.log10(abs(r_target) / abs(r_bg))
    return round(rcs_db, 2)

if __name__ == '__main__':
    p = RADAR_PARAMS
    print("=" * 60)
    print("  77 GHz FMCW RADAR: PHYSICS PARAMETER SUMMARY")
    print("=" * 60)
    print(f"  Center Frequency    : {p['f_c']/1e9:.1f} GHz")
    print(f"  Sweep Bandwidth     : {p['bandwidth']/1e9:.1f} GHz")
    print(f"  Wavelength (lambda) : {p['lambda_']*1000:.2f} mm")
    print(f"  Range Resolution    : {range_resolution()*100:.2f} cm")
    print(f"  Maximum Range       : {max_range():.1f} m")
    print(f"  Chirp Duration      : {p['T_chirp']*1e6:.1f} us")
    print()
    print("  RCS CONTRAST ANALYSIS (key to pothole detection):")
    print(f"  Dry Asphalt   eps_r={EPSILON_R['dry_asphalt']}")
    print(f"  Turbid Water  eps_r={EPSILON_R['turbid_water']}")
    contrast = compute_rcs_contrast(EPSILON_R['turbid_water'], EPSILON_R['dry_asphalt'])
    print(f"  RCS Contrast (water vs asphalt): +{contrast} dB")
    print(f"  => Waterlogged potholes appear as BRIGHT HOTSPOTS on radar (+20 dB)")
    print("=" * 60)
