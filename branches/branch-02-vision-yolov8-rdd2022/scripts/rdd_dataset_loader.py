#!/usr/bin/env python3
"""
rdd_dataset_loader.py
-------------------------------------------------------------------------------
Part of Person 2's Module: Dataset Taxonomy & Adverse Weather Augmentation.
Implements:
  1. RDD2022 / N-RDD2024 Taxonomy definitions (D40 Pothole vs D70 Manhole vs D80 Patch).
  2. Synthetic Weather Augmentations:
     - Synthetic Rain Streaks generator.
     - Synthetic Fog / Haze generator.
     - Road Glare & Water Reflection simulator.
These augmentations train YOLOv8 to identify potholes based on geometric depth shadows
rather than relying on high-contrast dry daylight features.
-------------------------------------------------------------------------------
"""

import cv2
import numpy as np
import random

# RDD2022 / N-RDD2024 Standard Class Taxonomy
TAXONOMY = {
    0: 'D00_Longitudinal_Crack',
    1: 'D10_Transverse_Crack',
    2: 'D20_Alligator_Crack',
    3: 'D40_Pothole',            # <-- Core Target Class
    4: 'D70_Manhole_Cover',      # <-- False-positive filter
    5: 'D80_Repaired_Patch'      # <-- False-positive filter
}

def add_synthetic_rain(image, drop_length=20, drop_width=1, drop_color=(200, 200, 200), density=400):
    """Injects realistic synthetic rain streaks into a camera frame."""
    rain_layer = image.copy()
    h, w = image.shape[:2]
    
    for _ in range(density):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - drop_length - 1)
        slant = random.randint(-5, 5)
        cv2.line(rain_layer, (x, y), (x + slant, y + drop_length), drop_color, drop_width)
        
    # Alpha blend rain streaks
    return cv2.addWeighted(rain_layer, 0.25, image, 0.75, 0)

def add_synthetic_fog(image, fog_density=0.55):
    """Simulates dense atmospheric scattering / fog over the road surface."""
    h, w = image.shape[:2]
    # Create white haze layer
    fog_layer = np.full((h, w, 3), 220, dtype=np.uint8)
    return cv2.addWeighted(image, 1.0 - fog_density, fog_layer, fog_density, 0)

def add_water_glare(image, glare_radius=120):
    """Simulates low-angle sun glare reflected from waterlogged road surfaces."""
    h, w = image.shape[:2]
    glare_mask = np.zeros((h, w), dtype=np.uint8)
    center = (random.randint(int(w * 0.3), int(w * 0.7)), random.randint(int(h * 0.4), int(h * 0.8)))
    cv2.circle(glare_mask, center, glare_radius, 255, -1)
    glare_mask = cv2.GaussianBlur(glare_mask, (101, 101), 0)
    
    glare_bgr = cv2.cvtColor(glare_mask, cv2.COLOR_GRAY2BGR)
    return cv2.addWeighted(image, 1.0, glare_bgr, 0.4, 0)

def demo_augmentation(sample_image_path=None):
    if sample_image_path:
        img = cv2.imread(sample_image_path)
    else:
        # Create a synthetic road plane
        img = np.full((720, 1280, 3), 70, dtype=np.uint8)
        # Draw a simulated pothole void
        cv2.ellipse(img, (640, 500), (90, 40), 0, 0, 360, (30, 30, 35), -1)

    foggy = add_synthetic_fog(img, fog_density=0.45)
    rainy = add_synthetic_rain(foggy, density=600)
    monsoon_sim = add_water_glare(rainy)
    
    print("[OK] Weather augmentation pipeline operational.")
    return monsoon_sim

if __name__ == '__main__':
    demo_augmentation()
