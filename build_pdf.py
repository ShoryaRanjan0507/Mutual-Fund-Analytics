import os
from PIL import Image

def build_pdf():
    # Define files
    image_paths = ["page1.png", "page2.png", "page3.png", "page4.png"]
    output_pdf = "Dashboard.pdf"
    
    print("Loading images and converting to RGB...")
    images = []
    for path in image_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required image not found: {path}")
        img = Image.open(path)
        # Convert to RGB since PDF doesn't support alpha transparency (RGBA) in the same way
        images.append(img.convert("RGB"))
        
    print(f"Saving combined images to {output_pdf}...")
    images[0].save(output_pdf, save_all=True, append_images=images[1:])
    print(f"Successfully created {output_pdf} containing {len(images)} pages.")

if __name__ == "__main__":
    build_pdf()
