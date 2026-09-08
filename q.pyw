import subprocess
import webbrowser
import tkinter as tk
import ctypes
import ctypes.wintypes
import os
import zlib
import struct

def copy_image_simple_windows(image_path):
    if not os.path.exists(image_path):
        print(f"Error: File does not exist: {image_path}")
        return False
    abs_path = os.path.abspath(image_path)
    if ' ' in abs_path:
        print(" Note: Path contains spaces, but it will still work")

    ps_command = f"""
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    try {{
        $img = [System.Drawing.Image]::FromFile('{abs_path}')
        [System.Windows.Forms.Clipboard]::SetImage($img)
        $img.Dispose()
        Write-Host "SUCCESS"
    }}
    catch {{
        Write-Error $_.Exception.Message
        exit 1
    }}
    """
    try:
        result = subprocess.run(
            ['powershell', '-STA', '-Command', ps_command],
            check=True,
            capture_output=True,
            text=True
        )
        
        if "SUCCESS" in result.stdout:
            print(" Image copied to clipboard")
            return True
        else:
            print(" Unknown error")
            return False

    except subprocess.CalledProcessError as e:
        print(" Error executing PowerShell:")
        print(e.stderr if e.stderr else "Unknown error")
        return False



# ==================== Windows API Screenshot Function ====================
def take_full_screenshot():
    """Take screenshot of entire screen using Windows API"""
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    
    # Get screen dimensions
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    
    # Get device contexts
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbitmap = gdi32.CreateCompatibleBitmap(hdc_screen, screen_width, screen_height)
    gdi32.SelectObject(hdc_mem, hbitmap)
    
    # Copy screen to bitmap
    gdi32.BitBlt(hdc_mem, 0, 0, screen_width, screen_height, hdc_screen, 0, 0, 0x00CC0020)
    
    # Define BITMAPINFOHEADER
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", ctypes.wintypes.DWORD),
            ("biWidth", ctypes.wintypes.LONG),
            ("biHeight", ctypes.wintypes.LONG),
            ("biPlanes", ctypes.wintypes.WORD),
            ("biBitCount", ctypes.wintypes.WORD),
            ("biCompression", ctypes.wintypes.DWORD),
            ("biSizeImage", ctypes.wintypes.DWORD),
            ("biXPelsPerMeter", ctypes.wintypes.LONG),
            ("biYPelsPerMeter", ctypes.wintypes.LONG),
            ("biClrUsed", ctypes.wintypes.DWORD),
            ("biClrImportant", ctypes.wintypes.DWORD)
        ]
    
    class BITMAPINFO(ctypes.Structure):
        _fields_ = [
            ("bmiHeader", BITMAPINFOHEADER),
            ("bmiColors", ctypes.wintypes.DWORD * 3)
        ]
    
    # Get bitmap info
    bi = BITMAPINFO()
    bi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bi.bmiHeader.biWidth = screen_width
    bi.bmiHeader.biHeight = screen_height
    bi.bmiHeader.biPlanes = 1
    bi.bmiHeader.biBitCount = 24
    bi.bmiHeader.biCompression = 0
    
    # First call to get image size
    gdi32.GetDIBits(hdc_mem, hbitmap, 0, screen_height, None, ctypes.byref(bi), 0)
    
    # Calculate buffer size if not set
    if bi.bmiHeader.biSizeImage == 0:
        # Calculate row size with 4-byte alignment
        row_size = ((screen_width * 24 + 31) // 32) * 4
        bi.bmiHeader.biSizeImage = row_size * screen_height
    
    # Allocate buffer for pixel data
    pixels = ctypes.create_string_buffer(bi.bmiHeader.biSizeImage)
    
    # Second call to get actual pixel data
    result = gdi32.GetDIBits(hdc_mem, hbitmap, 0, screen_height, pixels, ctypes.byref(bi), 0)
    
    if result == 0:
        print("Error getting bitmap data")
        return None, 0, 0, 0
    
    # Cleanup
    gdi32.DeleteObject(hbitmap)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)
    
    return pixels.raw, screen_width, screen_height, bi.bmiHeader.biSizeImage

def save_as_png(pixels, width, height, x1, y1, x2, y2, filepath):
    """Save selected area as compressed PNG file using zlib"""
    # Sort coordinates
    x1, x2 = min(x1, x2), max(x1, x2)
    y1, y2 = min(y1, y2), max(y1, y2)
    
    crop_width = x2 - x1
    crop_height = y2 - y1
    
    if crop_width <= 0 or crop_height <= 0:
        return False
    
    # Calculate stride (row size with 4-byte alignment)
    original_stride = ((width * 24 + 31) // 32) * 4
    pixel_data = bytearray()

    for y in range(y1, y2):
        bmp_y = height - 1 - y
        row_start = bmp_y * original_stride + x1 * 3
        row_data = pixels[row_start:row_start + crop_width * 3]
        
        # Convert BGR to RGB
        for i in range(0, len(row_data), 3):
            pixel_data.extend([row_data[i+2], row_data[i+1], row_data[i]])
    
    # Create PNG file
    with open(filepath, 'wb') as f:
        # PNG signature
        f.write(b'\x89PNG\r\n\x1a\n')
        
        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB', crop_width, crop_height, 8, 2, 0, 0, 0)
        ihdr_chunk = b'IHDR' + ihdr_data
        crc = zlib.crc32(ihdr_chunk) & 0xffffffff
        f.write(struct.pack('>I', len(ihdr_data)))
        f.write(ihdr_chunk)
        f.write(struct.pack('>I', crc))
        
        # IDAT chunk - compressed image data
        # Add filter byte (0 = none) for each scanline
        filtered_data = bytearray()
        for y in range(crop_height):
            filtered_data.append(0)  # filter type 0
            row_start = y * crop_width * 3
            filtered_data.extend(pixel_data[row_start:row_start + crop_width * 3])
        
        # Compress with zlib (maximum compression)
        compress = zlib.compressobj(zlib.Z_BEST_COMPRESSION, zlib.DEFLATED, 15, 8, zlib.Z_DEFAULT_STRATEGY)
        compressed_data = compress.compress(filtered_data)
        compressed_data += compress.flush()
        
        idat_data = compressed_data
        idat_chunk = b'IDAT' + idat_data
        crc = zlib.crc32(idat_chunk) & 0xffffffff
        f.write(struct.pack('>I', len(idat_data)))
        f.write(idat_chunk)
        f.write(struct.pack('>I', crc))
        
        # IEND chunk
        iend_chunk = b'IEND'
        crc = zlib.crc32(iend_chunk) & 0xffffffff
        f.write(struct.pack('>I', 0))
        f.write(iend_chunk)
        f.write(struct.pack('>I', crc))
    
    return True

# ==================== Main Application ====================
class SelectionApp:
    def __init__(self):
        # Create fullscreen window
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(cursor='cross', bg='black')
        self.root.attributes('-alpha', 0.3)
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        # Canvas for drawing selection rectangle
        self.canvas = tk.Canvas(self.root, cursor='cross', bg='grey', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Take screenshot first
        print("Taking screenshot...")
        self.pixels, self.screen_width, self.screen_height, _ = take_full_screenshot()
        
        if self.pixels is None:
            print("Failed to capture screenshot!")
            self.root.destroy()
            return
        
        print(f"Screenshot captured: {self.screen_width}x{self.screen_height}")
        print("Select area with mouse...")
        
        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        # Bind escape key to exit
        self.root.bind("<Escape>", lambda e: self.exit())
        
        self.root.mainloop()
    
    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
    
    def on_drag(self, event):
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline='red', width=2, fill='blue', stipple='gray50'
        )
    
    def on_release(self, event):
        if self.start_x is not None and self.start_y is not None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, "tmp.png")
            
            # Save selected area as PNG
            success = save_as_png(
                self.pixels, self.screen_width, self.screen_height,
                self.start_x, self.start_y, event.x, event.y,
                file_path
            )
            
            if success:
                copy_image_simple_windows(file_path)
                webbrowser.open('https://lens.google.com/')
            else:
                print("Invalid selection! Area too small or negative dimensions.")
            
            # Close and exit
            self.root.destroy()
            exit(0)
    
    def exit(self):
        self.root.destroy()
        exit(0)

# Run the application
if __name__ == "__main__":
    app = SelectionApp()