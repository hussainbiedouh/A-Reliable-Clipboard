"""
Create Windows ICO icon from PNG
"""
from PIL import Image, ImageDraw
import struct
import os

def create_ico_from_png():
    """Convert PNG to ICO format for Windows."""
    asset_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(asset_dir, 'clipboard.png')
    ico_path = os.path.join(asset_dir, 'clipboard.ico')
    
    # Load the PNG
    img = Image.open(png_path).convert('RGBA')
    
    # Resize to standard icon sizes
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []
    
    for size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        images.append(resized)
    
    # Create ICO file manually
    with open(ico_path, 'wb') as f:
        # ICO header
        f.write(struct.pack('<HHH', 0, 1, len(images)))  # Reserved, Type, Count
        
        # Calculate offsets
        header_size = 6 + (16 * len(images))
        offset = header_size
        
        image_data = []
        for i, img in enumerate(images):
            # Convert to BGRA for ICO
            img_bytes = img.tobytes()
            
            # Create BMP data (without file header)
            bmp_data = b''
            
            # BITMAPINFOHEADER
            bmp_header = struct.pack('<IIIHHIIIIII',
                40,  # Header size
                img.width,
                img.height * 2,  # Height * 2 for XOR + AND mask
                1,  # Planes
                32,  # Bits per pixel
                0,  # Compression (BI_RGB)
                0,  # Image size (can be 0 for uncompressed)
                0, 0, 0, 0  # XPelsPerMeter, YPelsPerMeter, Colors used, Important colors
            )
            
            # Pixel data (bottom-up, BGRA)
            pixels = []
            for y in range(img.height - 1, -1, -1):
                for x in range(img.width):
                    pixel = img.getpixel((x, y))
                    if len(pixel) == 4:
                        pixels.extend([pixel[2], pixel[1], pixel[0], pixel[3]])  # BGRA
                    else:
                        pixels.extend([pixel[0], pixel[1], pixel[2], 255])
            
            bmp_data = bmp_header + bytes(pixels)
            
            # AND mask (all zeros for 32-bit icons)
            and_mask_size = ((img.width + 31) // 32) * 4 * img.height
            and_mask = b'\x00' * and_mask_size
            
            # Directory entry
            w = 0 if img.width >= 256 else img.width
            h = 0 if img.height >= 256 else img.height
            
            entry = struct.pack('<BBBBHHII',
                w, h,  # Width, Height
                0,  # Color palette
                0,  # Reserved
                1,  # Color planes
                32,  # Bits per pixel
                len(bmp_data) + len(and_mask),  # Size
                offset  # Offset
            )
            
            f.write(entry)
            f.write(bmp_data)
            f.write(and_mask)
            offset += len(bmp_data) + len(and_mask)
    
    print(f"Created ICO: {ico_path}")
    return ico_path

if __name__ == "__main__":
    create_ico_from_png()
