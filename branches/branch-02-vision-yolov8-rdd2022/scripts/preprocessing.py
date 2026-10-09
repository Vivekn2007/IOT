#!/usr/bin/env python3
"""
preprocessing.py
-------------------------------------------------------------------------------
Part of Person 2's Module: Optical Image Preprocessing for Adverse Weather.
Implements:
  1. Contrast Limited Adaptive Histogram Equalization (CLAHE):
     Normalizes localized contrast over Indian asphalt surfaces, mitigating harsh
     tree shadows and monsoonal low-light degradation without blowing out noise.
  2. Bilateral Filtering:
     Edge-preserving spatial smoothing that removes high-frequency asphalt grit
     texture while preserving the sharp topological boundary of pothole edges.
-------------------------------------------------------------------------------
"""

import cv2
import numpy as np

class AdverseWeatherPreprocessor:
    def __init__(self, clip_limit=2.5, grid_size=(8, 8), bilateral_d=9, sigma_color=75, sigma_space=75):
        # CLAHE initialized on Lightness channel of LAB color space
        self.clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
        self.bilateral_d = bilateral_d
        self.sigma_color = sigma_color
        self.sigma_space = sigma_space

    def apply_clahe(self, bgr_image):
        """Enhances localized road contrast in LAB space without color distortion."""
        lab = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_clahe = self.clahe.apply(l)
        lab_clahe = cv2.merge((l_clahe, a, b))
        return cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)

    def apply_bilateral(self, bgr_image):
        """Smooths asphalt texture noise while keeping pothole perimeter edges sharp."""
        return cv2.bilateralFilter(bgr_image, d=self.bilateral_d, 
                                   sigmaColor=self.sigma_color, sigmaSpace=self.sigma_space)

    def process(self, bgr_image):
        """Full sequential preprocessing pipeline: CLAHE -> Bilateral Filter."""
        clahe_out = self.apply_clahe(bgr_image)
        filtered_out = self.apply_bilateral(clahe_out)
        return filtered_out

def demo():
    # Quick self-test with a dummy synthetic road frame
    dummy = np.random.randint(50, 150, (720, 1280, 3), dtype=np.uint8)
    preprocessor = AdverseWeatherPreprocessor()
    out = preprocessor.process(dummy)
    print(f"[OK] Preprocessor verified! Input: {dummy.shape} -> Output: {out.shape}")

if __name__ == '__main__':
    demo()
