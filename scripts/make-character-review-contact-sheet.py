import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


source = Path(os.environ["AEVRYND_CONTACT_INPUT_DIR"])
output = Path(os.environ["AEVRYND_CONTACT_OUTPUT"])
columns = int(os.environ.get("AEVRYND_CONTACT_COLUMNS", "4"))
cell_width = int(os.environ.get("AEVRYND_CONTACT_CELL_WIDTH", "440"))
cell_height = int(os.environ.get("AEVRYND_CONTACT_CELL_HEIGHT", "352"))
label_height = 28
requested = os.environ.get("AEVRYND_CONTACT_FILES")
paths = [source / name for name in requested.split(";")] if requested else sorted(path for path in source.glob("*.png") if path.is_file())
missing = [str(path) for path in paths if not path.is_file()]
if missing:
    raise RuntimeError("Missing requested review images: " + ", ".join(missing))
if not paths:
    raise RuntimeError(f"No PNG review images found in {source}")

rows = math.ceil(len(paths) / columns)
sheet = Image.new("RGB", (columns * cell_width, rows * (cell_height + label_height)), (5, 5, 5))
draw = ImageDraw.Draw(sheet)
font = ImageFont.load_default()
for index, path in enumerate(paths):
    with Image.open(path) as image:
        image = image.convert("RGB")
        image.thumbnail((cell_width, cell_height), Image.Resampling.LANCZOS)
        column, row = index % columns, index // columns
        x = column * cell_width + (cell_width - image.width) // 2
        y = row * (cell_height + label_height) + label_height + (cell_height - image.height) // 2
        sheet.paste(image, (x, y))
        draw.text((column * cell_width + 8, row * (cell_height + label_height) + 7), path.stem, fill=(245, 245, 245), font=font)

output.parent.mkdir(parents=True, exist_ok=True)
sheet.save(output, quality=91, optimize=True)
print(output)
