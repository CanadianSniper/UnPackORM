import os
import sys
import argparse
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from typing import Tuple, Optional, Dict

SUPPORTED_EXTS = (".png", ".jpg", ".jpeg", ".tga", ".tif", ".tiff")

# -----------------------------
# Core image logic
# -----------------------------

def load_image_rgb_or_rgba(path: str) -> Image.Image:
    """Load an image, preserving alpha if present; convert color to RGB(A)."""
    img = Image.open(path)
    # Convert paletted to RGBA if needed
    if img.mode in ("P", "LA"):
        img = img.convert("RGBA")
    # Normalize to RGB / RGBA only
    if img.mode == "RGBA":
        return img
    elif img.mode != "RGB":
        return img.convert("RGB")
    return img

PRESETS: Dict[str, Tuple[str, str, str]] = {
    # Map name -> (AO_from, Roughness_from, Metallic_from)
    # Each value in tuple must be one of: "R", "G", "B"
    "ORM (R=AO, G=Roughness, B=Metallic)": ("R", "G", "B"),
    "MRA (R=Metallic, G=Roughness, B=AO)": ("B", "G", "R"),
    "RMA (R=Roughness, G=Metallic, B=AO)": ("B", "R", "G"),
}


def channel_by_letter(img: Image.Image, letter: str) -> Image.Image:
    r, g, b = img.split()[:3]
    return {"R": r, "G": g, "B": b}[letter]


def maybe_invert(ch: Image.Image, do_invert: bool) -> Image.Image:
    if not do_invert:
        return ch
    # Invert grayscale channel
    return Image.eval(ch, lambda px: 255 - px)


def save_grayscale(ch: Image.Image, out_path: str) -> None:
    # Ensure single-channel L mode
    if ch.mode != "L":
        ch = ch.convert("L")
    ch.save(out_path)


def unpack_orm(
    input_path: str,
    output_dir: str,
    preset_name: str = "ORM (R=AO, G=Roughness, B=Metallic)",
    invert_roughness: bool = False,
    invert_metallic: bool = False,
    export_alpha_as_height: bool = False,
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Unpack an ORM-like packed texture to grayscale AO / Roughness / Metallic (and optional Height from Alpha).

    Returns tuple of saved file paths: (ao, roughness, metallic, height)
    Missing outputs return as None.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    img = load_image_rgb_or_rgba(input_path)

    base = os.path.splitext(os.path.basename(input_path))[0]
    ao_path = os.path.join(output_dir, f"{base}_AO.png")
    rough_path = os.path.join(output_dir, f"{base}_Roughness.png")
    metal_path = os.path.join(output_dir, f"{base}_Metallic.png")
    height_path = os.path.join(output_dir, f"{base}_Height.png")

    # Pick channels by preset
    if preset_name not in PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}")
    ao_from, rough_from, metal_from = PRESETS[preset_name]

    ao_ch = channel_by_letter(img, ao_from)
    rough_ch = maybe_invert(channel_by_letter(img, rough_from), invert_roughness)
    metal_ch = maybe_invert(channel_by_letter(img, metal_from), invert_metallic)

    save_grayscale(ao_ch, ao_path)
    save_grayscale(rough_ch, rough_path)
    save_grayscale(metal_ch, metal_path)

    saved_height = None
    if export_alpha_as_height and img.mode == "RGBA":
        _, _, _, a = img.split()
        save_grayscale(a, height_path)
        saved_height = height_path

    return ao_path, rough_path, metal_path, saved_height


# -----------------------------
# GUI
# -----------------------------

class UnpackORMApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("UnpackORM Pro — AO/Roughness/Metallic Extractor")
        root.geometry("610x520")
        root.resizable(False, False)

        self.texture_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.preset = tk.StringVar(value=list(PRESETS.keys())[0])
        self.invert_rough = tk.BooleanVar(value=False)
        self.invert_metal = tk.BooleanVar(value=False)
        self.export_alpha_height = tk.BooleanVar(value=False)
        self.batch_mode = tk.BooleanVar(value=False)

        self.build_ui()
        self.preview_images = {}  # cache to keep references

    def build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # Input selection
        frm_in = ttk.LabelFrame(self.root, text="Input")
        frm_in.pack(fill="x", **pad)

        ttk.Label(frm_in, text="Packed Texture (file or folder in Batch mode)").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm_in, textvariable=self.texture_path, width=70).grid(row=1, column=0, sticky="we")
        ttk.Button(frm_in, text="Browse",
                   command=self.select_texture).grid(row=1, column=1, padx=6)

        ttk.Checkbutton(frm_in, text="Batch process a folder", variable=self.batch_mode).grid(row=2, column=0, sticky="w", pady=(6,0))

        # Output selection
        frm_out = ttk.LabelFrame(self.root, text="Output")
        frm_out.pack(fill="x", **pad)

        ttk.Label(frm_out, text="Output Folder").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm_out, textvariable=self.output_path, width=70).grid(row=1, column=0, sticky="we")
        ttk.Button(frm_out, text="Browse",
                   command=self.select_output_folder).grid(row=1, column=1, padx=6)

        # Options
        frm_opts = ttk.LabelFrame(self.root, text="Options")
        frm_opts.pack(fill="x", **pad)

        ttk.Label(frm_opts, text="Channel Preset").grid(row=0, column=0, sticky="w")
        ttk.Combobox(frm_opts, textvariable=self.preset, values=list(PRESETS.keys()), state="readonly", width=40).grid(row=0, column=1, sticky="w")

        ttk.Checkbutton(frm_opts, text="Invert Roughness (Gloss → Rough)", variable=self.invert_rough).grid(row=1, column=0, sticky="w", pady=(6,0))
        ttk.Checkbutton(frm_opts, text="Invert Metallic", variable=self.invert_metal).grid(row=1, column=1, sticky="w", pady=(6,0))
        ttk.Checkbutton(frm_opts, text="Export Alpha as Height (if present)", variable=self.export_alpha_height).grid(row=2, column=0, sticky="w", pady=(6,0))

        # Actions
        frm_actions = ttk.Frame(self.root)
        frm_actions.pack(fill="x", **pad)

        ttk.Button(frm_actions, text="Unpack",
                   command=self.process_texture).pack(side="left")
        ttk.Button(frm_actions, text="Open Output Folder",
                   command=self.open_output_folder).pack(side="left", padx=6)

        # Preview
        self.frm_prev = ttk.LabelFrame(self.root, text="Preview (first processed image this session)")
        self.frm_prev.pack(fill="both", expand=True, **pad)
        self.canvas_prev = tk.Canvas(self.frm_prev, width=560, height=240, bg="#2b2b2b", highlightthickness=0)
        self.canvas_prev.pack(padx=8, pady=8)
        self.canvas_prev.create_text(280, 120, text="Processed AO / Roughness / Metallic previews will show here.", fill="#dddddd")

    # ------------- helpers -------------
    def select_texture(self):
        if self.batch_mode.get():
            folder = filedialog.askdirectory()
            if folder:
                self.texture_path.set(folder)
        else:
            f = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.tga;*.tif;*.tiff")])
            if f:
                self.texture_path.set(f)

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_path.set(folder)

    def open_output_folder(self):
        path = self.output_path.get()
        if not path or not os.path.isdir(path):
            messagebox.showwarning("Open Folder", "Please choose a valid output folder first.")
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f"open '{path}'")
            else:
                os.system(f"xdg-open '{path}'")
        except Exception as e:
            messagebox.showerror("Open Folder", f"Failed to open folder:\n{e}")

    def iter_images_in_folder(self, folder: str):
        for root_dir, _, files in os.walk(folder):
            for name in files:
                if os.path.splitext(name)[1].lower() in SUPPORTED_EXTS:
                    yield os.path.join(root_dir, name)

    def process_single(self, in_path: str, out_dir: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        return unpack_orm(
            input_path=in_path,
            output_dir=out_dir,
            preset_name=self.preset.get(),
            invert_roughness=self.invert_rough.get(),
            invert_metallic=self.invert_metal.get(),
            export_alpha_as_height=self.export_alpha_height.get(),
        )

    def process_texture(self):
        input_sel = self.texture_path.get()
        output_dir = self.output_path.get()
        if not input_sel or not output_dir:
            messagebox.showwarning("Missing Information", "Please select both an input path and an output folder.")
            return

        try:
            saved_any = False
            first_preview_set = False
            if self.batch_mode.get():
                if not os.path.isdir(input_sel):
                    messagebox.showerror("Batch Mode", "In batch mode, the input must be a folder.")
                    return
                count = 0
                for img_path in self.iter_images_in_folder(input_sel):
                    ao, rr, mm, hh = self.process_single(img_path, output_dir)
                    saved_any = True
                    count += 1
                    if not first_preview_set:
                        self.update_preview(ao, rr, mm)
                        first_preview_set = True
                if count == 0:
                    messagebox.showinfo("No Images", "No supported images found in that folder.")
                    return
                messagebox.showinfo("Success", f"Processed {count} image(s). Files saved to:\n{output_dir}")
            else:
                if not os.path.isfile(input_sel):
                    messagebox.showerror("Input", "Input path is not a file.")
                    return
                ao, rr, mm, hh = self.process_single(input_sel, output_dir)
                saved_any = True
                self.update_preview(ao, rr, mm)
                parts = [p for p in (ao, rr, mm, hh) if p]
                messagebox.showinfo("Success", "Saved:\n- " + "\n- ".join(parts))

            if saved_any and output_dir:
                # Optional: auto-open folder
                pass
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{e}")

    def update_preview(self, ao_path: Optional[str], rough_path: Optional[str], metal_path: Optional[str]):
        # Clear canvas
        self.canvas_prev.delete("all")
        if not (ao_path and rough_path and metal_path):
            self.canvas_prev.create_text(280, 120, text="Preview unavailable.", fill="#dddddd")
            return

        def load_thumb(p):
            img = Image.open(p).convert("L")
            img = img.resize((170, 170), Image.LANCZOS)
            return ImageTk.PhotoImage(img)

        self.preview_images["ao"] = load_thumb(ao_path)
        self.preview_images["r"] = load_thumb(rough_path)
        self.preview_images["m"] = load_thumb(metal_path)

        # Draw side by side
        x0, y0 = 90, 40
        self.canvas_prev.create_image(x0, y0, anchor="nw", image=self.preview_images["ao"])
        self.canvas_prev.create_text(x0 + 85, y0 + 180, text="AO", fill="#ffffff")

        x1 = x0 + 190
        self.canvas_prev.create_image(x1, y0, anchor="nw", image=self.preview_images["r"])
        self.canvas_prev.create_text(x1 + 85, y0 + 180, text="Roughness", fill="#ffffff")

        x2 = x1 + 190
        self.canvas_prev.create_image(x2, y0, anchor="nw", image=self.preview_images["m"])
        self.canvas_prev.create_text(x2 + 85, y0 + 180, text="Metallic", fill="#ffffff")


# -----------------------------
# CLI entry point (optional)
# -----------------------------

def run_cli():
    parser = argparse.ArgumentParser(description="Unpack an ORM/MRA/RMA packed texture to grayscale AO/R/M maps.")
    parser.add_argument("input", help="Input image path or folder (for batch if --batch)")
    parser.add_argument("--out", required=True, help="Output folder")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), default=list(PRESETS.keys())[0])
    parser.add_argument("--invert-rough", action="store_true", help="Invert the roughness channel (Gloss → Rough)")
    parser.add_argument("--invert-metal", action="store_true", help="Invert the metallic channel")
    parser.add_argument("--alpha-as-height", action="store_true", help="Export alpha channel as Height if present")
    parser.add_argument("--batch", action="store_true", help="Treat input as a folder and process images recursively")

    args = parser.parse_args()

    if args.batch and not os.path.isdir(args.input):
        print("In batch mode, input must be a folder.")
        sys.exit(2)

    os.makedirs(args.out, exist_ok=True)

    if args.batch:
        count = 0
        for root_dir, _, files in os.walk(args.input):
            for name in files:
                if os.path.splitext(name)[1].lower() in SUPPORTED_EXTS:
                    in_path = os.path.join(root_dir, name)
                    unpack_orm(
                        input_path=in_path,
                        output_dir=args.out,
                        preset_name=args.preset,
                        invert_roughness=args.invert_rough,
                        invert_metallic=args.invert_metal,
                        export_alpha_as_height=args.alpha_as_height,
                    )
                    count += 1
        print(f"Processed {count} images → {args.out}")
    else:
        if not os.path.isfile(args.input):
            print("Input path is not a file.")
            sys.exit(2)
        paths = unpack_orm(
            input_path=args.input,
            output_dir=args.out,
            preset_name=args.preset,
            invert_roughness=args.invert_rough,
            invert_metallic=args.invert_metal,
            export_alpha_as_height=args.alpha_as_height,
        )
        print("Saved:\n- " + "\n- ".join([p for p in paths if p]))


if __name__ == "__main__":
    # If run with arguments, act as CLI; otherwise, show GUI
    if len(sys.argv) > 1 and any(a.startswith("-") for a in sys.argv[1:]):
        run_cli()
    else:
        root = tk.Tk()
        # Use themed widgets
        try:
            root.call("tk", "scaling", 1.2)
        except Exception:
            pass
        app = UnpackORMApp(root)
        root.mainloop()
