#!/usr/bin/env python3
"""
rdd_dataset_loader.py
-------------------------------------------------------------------------------
Unified Indian Road Damage Dataset Loader & Taxonomy Inspector.
Integrates and supports all three dataset formats:
  1. YOLO format:  E:\\IOT project\\data\\india_txt\\
  2. COCO format:  E:\\IOT project\\data\\india_coco\\
  3. Pascal VOC:   E:\\IOT project\\data\\india_voc\\

Taxonomy:
  Class 0: D00 - Longitudinal Crack (wheel path)
  Class 1: D10 - Transverse Crack (construction joint)
  Class 2: D20 - Alligator Crack (fatigue spiderweb)
  Class 3: D40 - POTHOLE (Core Target Class)
  Class 4: D50 - Crosswalk line blur
  Class 5: D60 - Lane line blur
  Class 6: D70 - Manhole cover (False Positive filter)
  Class 7: D80 - Repaired road patch (False Positive filter)
-------------------------------------------------------------------------------
"""

import os
import glob
import json
import xml.etree.ElementTree as ET
import cv2
import numpy as np

DATASET_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))
if not os.path.exists(DATASET_ROOT):
    DATASET_ROOT = r"E:\IOT project\data"

CLASS_NAMES = ['D00', 'D10', 'D20', 'D40', 'D50', 'D60', 'D70', 'D80']
CLASS_DESCRIPTIONS = {
    'D00': 'Longitudinal Crack (Linear)',
    'D10': 'Transverse Crack (Road Joint)',
    'D20': 'Alligator Crack (Fatigue Mesh)',
    'D40': 'POTHOLE (Structural Depression)',
    'D50': 'Crosswalk Marking Blur',
    'D60': 'White/Yellow Line Blur',
    'D70': 'Manhole / Utility Cover',
    'D80': 'Repaired Asphalt Patch'
}

CLASS_COLORS = {
    'D40': (0, 0, 255),       # Bright Red for genuine Potholes
    'D00': (255, 180, 0),     # Orange for longitudinal cracks
    'D10': (255, 220, 0),     # Yellow for transverse cracks
    'D20': (200, 100, 255),   # Purple for alligator cracks
    'D50': (120, 120, 120),   # Gray for markings
    'D60': (160, 160, 160),   # Gray for lane blur
    'D70': (0, 200, 200),     # Cyan for manholes
    'D80': (0, 220, 100)      # Green for repaired patches
}

class IndiaRDDLoader:
    def __init__(self, base_path=DATASET_ROOT):
        self.base_path = base_path
        self.txt_dir = os.path.join(base_path, "india_txt")
        self.coco_dir = os.path.join(base_path, "india_coco")
        self.voc_dir = os.path.join(base_path, "india_voc")

    def get_summary(self):
        """Returns inventory across all 3 formats."""
        summary = {}
        for name, folder in [('india_txt', self.txt_dir), ('india_coco', self.coco_dir), ('india_voc', self.voc_dir)]:
            if os.path.exists(folder):
                imgs = glob.glob(os.path.join(folder, "**", "*.jpg"), recursive=True)
                txts = glob.glob(os.path.join(folder, "**", "*.txt"), recursive=True)
                xmls = glob.glob(os.path.join(folder, "**", "*.xml"), recursive=True)
                jsons = glob.glob(os.path.join(folder, "**", "*.json"), recursive=True)
                summary[name] = {
                    'status': 'Available',
                    'images_count': len(imgs),
                    'annotations_count': len(txts) + len(xmls) + len(jsons),
                    'path': folder
                }
            else:
                summary[name] = {'status': 'Not Found', 'path': folder}
        return summary

    def load_yolo_samples(self, split='train', max_samples=10, pothole_only=False):
        """Loads samples from india_txt in YOLO format."""
        images_dir = os.path.join(self.txt_dir, split, "images")
        labels_dir = os.path.join(self.txt_dir, split, "labels")
        
        samples = []
        image_files = glob.glob(os.path.join(images_dir, "*.jpg"))
        
        for img_path in image_files:
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            label_path = os.path.join(labels_dir, f"{base_name}.txt")
            
            boxes = []
            if os.path.exists(label_path):
                with open(label_path, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if not parts: continue
                        cid = int(parts[0])
                        cname = CLASS_NAMES[cid] if cid < len(CLASS_NAMES) else f"Class_{cid}"
                        cx, cy, nw, nh = map(float, parts[1:])
                        boxes.append({
                            'class_id': cid,
                            'class_name': cname,
                            'is_pothole': (cname == 'D40'),
                            'norm_box': [cx, cy, nw, nh]
                        })

            if pothole_only and not any(b['is_pothole'] for b in boxes):
                continue

            samples.append({
                'image_path': img_path,
                'format': 'YOLO',
                'boxes': boxes,
                'pothole_count': sum(1 for b in boxes if b['is_pothole']),
                'non_pothole_count': sum(1 for b in boxes if not b['is_pothole'])
            })
            if len(samples) >= max_samples:
                break

        return samples

    def load_voc_samples(self, split='train', max_samples=10):
        """Loads samples from india_voc XML annotations."""
        split_dir = os.path.join(self.voc_dir, split)
        xml_files = glob.glob(os.path.join(split_dir, "*.xml"))
        samples = []

        for xml_p in xml_files[:max_samples]:
            try:
                tree = ET.parse(xml_p)
                root = tree.getroot()
                fn = root.find('filename').text
                img_p = os.path.join(split_dir, fn)
                boxes = []
                for obj in root.findall('object'):
                    cname = obj.find('name').text
                    bnd = obj.find('bndbox')
                    xmin = float(bnd.find('xmin').text)
                    ymin = float(bnd.find('ymin').text)
                    xmax = float(bnd.find('xmax').text)
                    ymax = float(bnd.find('ymax').text)
                    boxes.append({
                        'class_name': cname,
                        'is_pothole': (cname == 'D40'),
                        'xyxy': [xmin, ymin, xmax, ymax]
                    })
                samples.append({'image_path': img_p, 'format': 'VOC', 'boxes': boxes})
            except Exception:
                pass
        return samples

    def render_sample(self, sample, out_path=None):
        """Renders an image highlighting POTHOLES (Red) vs NON-POTHOLES (Orange/Purple/Cyan)."""
        img = cv2.imread(sample['image_path'])
        if img is None: return None
        h, w = img.shape[:2]

        for b in sample['boxes']:
            cname = b['class_name']
            col = CLASS_COLORS.get(cname, (200, 200, 200))
            is_pot = b['is_pothole']
            
            if 'norm_box' in b:
                cx, cy, nw, nh = b['norm_box']
                x1 = int((cx - nw / 2.0) * w)
                y1 = int((cy - nh / 2.0) * h)
                x2 = int((cx + nw / 2.0) * w)
                y2 = int((cy + nh / 2.0) * h)
            else:
                x1, y1, x2, y2 = map(int, b['xyxy'])

            thickness = 3 if is_pot else 1
            cv2.rectangle(img, (x1, y1), (x2, y2), col, thickness)
            
            lbl = f"POTHOLE [D40]" if is_pot else f"{cname} ({CLASS_DESCRIPTIONS.get(cname, 'Defect')})"
            (lw, lh), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(img, (x1, max(0, y1 - 20)), (x1 + lw + 6, y1), col, -1)
            cv2.putText(img, lbl, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

        # Header legend
        cv2.rectangle(img, (0, 0), (w, 32), (15, 20, 28), -1)
        legend_txt = "RED = D40 POTHOLE (Tracked) | ORANGE/PURPLE = CRACKS/MARKINGS (Filtered Out)"
        cv2.putText(img, legend_txt, (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (70, 214, 207), 1, cv2.LINE_AA)

        if out_path:
            cv2.imwrite(out_path, img)
        return img

def main():
    print("=" * 72)
    print("       INDIAN ROAD DAMAGE DATASET (RDD) INTEGRATION & LOADER          ")
    print("=" * 72)
    loader = IndiaRDDLoader()
    summary = loader.get_summary()
    
    print("\n[DATASET INTEGRATION SUMMARY]")
    for k, v in summary.items():
        print(f"  * {k.upper():<12}: {v['status']} | Images: {v.get('images_count', 0)} | Annotations: {v.get('annotations_count', 0)}")
        print(f"    Location: {v['path']}")

    print("\n[TAXONOMY CLASSIFICATION]")
    for cid, cname in enumerate(CLASS_NAMES):
        role = ">>> TARGET: POTHOLE <<<" if cname == 'D40' else "FALSE POSITIVE (Reject)"
        print(f"  Class {cid}: {cname:<6} - {CLASS_DESCRIPTIONS[cname]:<32} [{role}]")

    # Generate sample visualization
    samples = loader.load_yolo_samples(split='train', max_samples=3, pothole_only=True)
    if samples:
        out_dir = os.path.join(loader.base_path, "sample_previews")
        os.makedirs(out_dir, exist_ok=True)
        for i, s in enumerate(samples):
            out_f = os.path.join(out_dir, f"rdd_sample_{i+1}_annotated.jpg")
            loader.render_sample(s, out_f)
            print(f"\n[OK] Rendered annotated sample {i+1}: {out_f}")
            print(f"     Potholes (D40): {s['pothole_count']} | Non-potholes (Cracks/Lines): {s['non_pothole_count']}")

if __name__ == '__main__':
    main()
