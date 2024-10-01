from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import base64
import io
import os

app = Flask(__name__)

# Folder paths
FONT_FOLDER = "fonts"
BACKGROUND_FOLDER = "backgrounds"
VECTOR_FOLDER = "vectors"

# Create folders if they don't exist
for folder in [FONT_FOLDER, BACKGROUND_FOLDER, VECTOR_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Helper functions to get assets
def get_fonts():
    return [f for f in os.listdir(FONT_FOLDER) if f.endswith(('.otf', '.ttf'))]

def get_backgrounds():
    return [f for f in os.listdir(BACKGROUND_FOLDER) if f.endswith(('.jpg', '.png'))]

def get_vectors():
    return [f for f in os.listdir(VECTOR_FOLDER) if f.endswith('.png')]

@app.route('/')
def index():
    fonts = get_fonts()
    backgrounds = get_backgrounds()
    vectors = get_vectors()
    return render_template('index.html', fonts=fonts, backgrounds=backgrounds, vectors=vectors)

@app.route('/generate_mockup', methods=['POST'])
def generate_mockup():
    data = request.json
    text_lines = data['text'].split('\n')
    font_name = data['font']
    font_size = int(data['fontSize'])
    background = data['background']
    text_align = data['textAlign']
    vertical_align = data['verticalAlign']
    vector = data.get('vector')
    vector_scale = float(data.get('vectorScale', 1))
    vector_x = int(data.get('vectorX', 0))
    vector_y = int(data.get('vectorY', 0))
    horizontal_offset = int(data.get('horizontalOffset', 0))
    vertical_offset = int(data.get('verticalOffset', 0))

    # Set line spacing (you can adjust this value as needed)
    line_spacing = 10  # Space between lines

    # Load background image
    bg_image = Image.open(os.path.join(BACKGROUND_FOLDER, background))

    # Create a drawing object
    draw = ImageDraw.Draw(bg_image)

    # Load font
    font = ImageFont.truetype(os.path.join(FONT_FOLDER, font_name), font_size)

    # Calculate text dimensions
    line_sizes = [font.getbbox(line) for line in text_lines]
    max_width = max(bbox[2] - bbox[0] for bbox in line_sizes)
    total_height = sum(bbox[3] - bbox[1] for bbox in line_sizes) + (len(text_lines) - 1) * line_spacing

    # Calculate initial text position
    if text_align == 'left':
        x = 10 + horizontal_offset
    elif text_align == 'center':
        x = (bg_image.width - max_width) / 2 + horizontal_offset
    else:  # right
        x = bg_image.width - max_width - 10 + horizontal_offset

    if vertical_align == 'top':
        y = 10 + vertical_offset
    elif vertical_align == 'middle':
        y = (bg_image.height - total_height) / 2 + vertical_offset
    else:  # bottom
        y = bg_image.height - total_height - 10 + vertical_offset

    # Draw text on image
    for i, line in enumerate(text_lines):
        bbox = line_sizes[i]
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]

        if text_align == 'center':
            line_x = x + (max_width - line_width) / 2
        elif text_align == 'right':
            line_x = x + max_width - line_width
        else:  # left
            line_x = x

        draw.text((line_x, y), line, font=font, fill=(0, 0, 0))  # Black text
        y += line_height + line_spacing  # Add line spacing after each line

    # Add vector if specified
    if vector:
        vector_path = os.path.join(VECTOR_FOLDER, vector)
        vector_image = Image.open(vector_path)

        # Resize vector image
        new_size = (int(vector_image.width * vector_scale), int(vector_image.height * vector_scale))
        vector_image = vector_image.resize(new_size, Image.LANCZOS)

        # Paste vector image onto background
        bg_image.paste(vector_image, (vector_x, vector_y), vector_image)

    # Save the image to a bytes buffer
    buffered = io.BytesIO()
    bg_image.save(buffered, format="PNG")

    # Encode the image to base64
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return jsonify({'image': img_str})

@app.route('/merge_mockups', methods=['POST'])
def merge_mockups():
    data = request.json
    images_base64 = data['images']

    # Decode the base64 images into PIL Image objects
    images = [Image.open(io.BytesIO(base64.b64decode(img))) for img in images_base64]

    # Assume all images have the same size, get the size of the first image
    width, height = images[0].size

    # Create a blank image to hold the merged result
    merged_image = Image.new('RGBA', (width, height * len(images)))

    # Paste the images one below the other
    for i, img in enumerate(images):
        merged_image.paste(img, (0, i * height))

    # Save the merged image to a bytes buffer
    buffered = io.BytesIO()
    merged_image.save(buffered, format="PNG")

    # Encode the merged image to base64
    merged_img_str = base64.b64encode(buffered.getvalue()).decode()

    return jsonify({'merged_image': merged_img_str})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)