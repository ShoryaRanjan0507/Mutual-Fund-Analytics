"""
Mutual Fund Analytics - Dashboard PDF Builder

This module consolidates the PNG screenshot page renderings of the PowerBI dashboard
into a unified document: Dashboard.pdf.
"""

import os
from PIL import Image

def build_pdf():
    """
    Combines the dashboard page screenshots into a single multi-page PDF document.
    """
    image_paths = ["page1.png", "page2.png", "page3.png", "page4.png"]
    output_pdf = "Dashboard.pdf"
    
    print("=" * 80)
    print("STARTING DASHBOARD PDF BUILD")
    print("=" * 80)
    
    images = []
    for path in image_paths:
        if not os.path.exists(path):
            print(f"[WARNING] Required image not found: {path}. Skipping PDF consolidation.")
            return False
        img = Image.open(path)
        images.append(img.convert("RGB"))
        
    print(f"Consolidating {len(images)} pages into {output_pdf}...")
    images[0].save(output_pdf, save_all=True, append_images=images[1:])
    print(f"[SUCCESS] Successfully created {output_pdf} containing {len(images)} pages.")
    print("=" * 80)
    return True

if __name__ == "__main__":
    build_pdf()
