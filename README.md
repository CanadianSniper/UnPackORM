# UnpackORM Pro — AO / Roughness / Metallic Extractor

**UnpackORM Pro** is a Python tool that unpacks ORM-style packed textures into separate grayscale Ambient Occlusion (AO), Roughness, and Metallic maps — with optional Height map export from the alpha channel.

It supports both **GUI** and **CLI** usage, batch folder processing, multiple channel presets, and quick previews.

---

## Features

- 🎛 **Channel Presets** — Extract from common packed formats:
  - ORM (R=AO, G=Roughness, B=Metallic)
  - MRA (R=Metallic, G=Roughness, B=AO)
  - RMA (R=Roughness, G=Metallic, B=AO)
- 🔄 **Optional Inversion** — Flip Roughness or Metallic values (Gloss → Rough, etc.)
- 🖼 **Alpha to Height** — Export the alpha channel as a height/displacement map
- 📂 **Batch Processing** — Process a folder of textures at once
- 🖥 **Preview Panel** — GUI shows thumbnails of AO/Roughness/Metallic outputs
- 🛠 **Cross-Platform** — Works on Windows, macOS, and Linux

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/UnpackORM.git
   cd UnpackORM
   ```

2. **Install required dependencies:**
   ```bash
   pip install pillow
   ```

3. (Optional) If you want to process `.tga`, `.tif`, `.tiff` images, make sure your Pillow build supports them.

---

## Usage

### 1. GUI Mode
Simply run:
```bash
python UnpackORM.py
```
The GUI will open, allowing you to:
- Select an input file or folder
- Choose an output folder
- Set channel presets and options
- Click **Unpack** to process

**GUI Options:**
- **Batch Mode** — Enable to process every supported image in a folder
- **Invert Roughness/Metallic** — Flip channel values
- **Export Alpha as Height** — Save the alpha channel as a grayscale height map

---

### 2. CLI Mode
Run with arguments to skip the GUI:
```bash
python UnpackORM.py <input_path> --out <output_folder> [options]
```

**Arguments:**
| Option                | Description |
|-----------------------|-------------|
| `<input_path>`        | Path to image file or folder (if `--batch` is used) |
| `--out`               | Output folder path (required) |
| `--preset`            | Channel preset: `"ORM (R=AO, G=Roughness, B=Metallic)"`, `"MRA (R=Metallic, G=Roughness, B=AO)"`, `"RMA (R=Roughness, G=Metallic, B=AO)"` |
| `--invert-rough`      | Invert the roughness channel |
| `--invert-metal`      | Invert the metallic channel |
| `--alpha-as-height`   | Export alpha channel as height map |
| `--batch`             | Treat input as folder and process recursively |

**Examples:**
```bash
# Unpack a single image
python UnpackORM.py textures/wood_orm.png --out outputs

# Batch process an entire folder, inverting roughness
python UnpackORM.py textures/ --out outputs --batch --invert-rough
```

---

## Supported Formats

- `.png`
- `.jpg` / `.jpeg`
- `.tga`
- `.tif` / `.tiff`

---

## Output

Given `MyTexture.png` as input, outputs will be:

- `MyTexture_AO.png`
- `MyTexture_Roughness.png`
- `MyTexture_Metallic.png`
- (optional) `MyTexture_Height.png` (if alpha channel exported)

---

## License

MIT License — See [LICENSE](LICENSE) for details.

---

## Credits

Developed by **[Your Name]**  
Powered by [Python](https://www.python.org/) & [Pillow](https://python-pillow.org/)
