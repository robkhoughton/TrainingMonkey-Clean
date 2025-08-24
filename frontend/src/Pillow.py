from PIL import Image, ImageDraw, ImageFont

# Define your colors and names
colors = [
    ("Primary", "#3498db"),
    ("Secondary", "#2ecc71"),
    ("Warning", "#e67e22"),
    ("Danger", "#e74c3c"),
    ("Dark", "#2c3e50"),
    ("Accent", "#9b59b6"),
    ("Trimp", "#e84393"),
    ("Background", "#f9fafb"),
]

# Image settings
swatch_width = 320
swatch_height = 50
padding = 10
font_size = 18

# Create the image
img_height = (swatch_height + padding) * len(colors) + padding
img_width = swatch_width + 200
img = Image.new("RGB", (img_width, img_height), "white")
draw = ImageDraw.Draw(img)

# Try to load a font, fallback to default if not found
try:
    font = ImageFont.truetype("arial.ttf", font_size)
except:
    font = ImageFont.load_default()

for i, (name, hexcode) in enumerate(colors):
    y = padding + i * (swatch_height + padding)
    # Draw color rectangle
    draw.rectangle(
        [padding, y, padding + swatch_width, y + swatch_height],
        fill=hexcode,
        outline="gray",
        width=2
    )
    # Write name and hex code
    text = f"{name} ({hexcode})"
    draw.text(
        (padding + swatch_width + 20, y + swatch_height // 4),
        text,
        fill="black",
        font=font
    )

# Save the image
img.save("color_palette.png")
print("Saved as color_palette.png")
