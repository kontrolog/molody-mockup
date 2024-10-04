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
    return [f for f in os.listdir(
        BACKGROUND_FOLDER) if f.endswith(('.jpg', '.png'))]


def get_vectors():
    return [f for f in os.listdir(VECTOR_FOLDER) if f.endswith('.png')]


@app.route('/')
def index():
    fonts = get_fonts()
    backgrounds = get_backgrounds()
    vectors = get_vectors()
    return render_template(
        'index.html', fonts=fonts, backgrounds=backgrounds, vectors=vectors)


@app.route('/generate_mockup', methods=['POST'])
def generate_mockup():
    data = request.json
    print("Data received:", data)  # Print the received data for debugging
    background = data['background']

    # Load background image
    bg_image = Image.open(os.path.join(BACKGROUND_FOLDER, background))

    # Create a drawing object
    draw = ImageDraw.Draw(bg_image)

    y = 10  # Initial vertical position for the first font

    for font_data in data['fonts']:
        font_name = font_data['font']
        font_size = int(font_data['fontSize'])
        horizontal_offset = int(font_data.get('horizontalOffset', 0))
        vertical_offset = int(font_data.get('verticalOffset', 0))
        text_align = font_data.get('textAlign', 'left')
        vertical_align = font_data.get('verticalAlign', 'top')
        text_lines = font_data['text'].split(
            '\n')  # Get text for this font and split into lines

        # Set line spacing
        line_spacing = 10

        # Load font
        font = ImageFont.truetype(os.path.join(
            FONT_FOLDER, font_name), font_size)

        # Calculate total text block height for this font
        total_font_height = 0
        line_heights = []
        for line in text_lines:
            bbox = font.getbbox(line)
            line_height = bbox[3] - bbox[1]
            line_heights.append(line_height)
            total_font_height += line_height + line_spacing

        total_font_height -= line_spacing  # Remove extra spacing

        # Adjust y for vertical alignment of the text block
        if vertical_align == 'top':
            y += vertical_offset
        elif vertical_align == 'middle':
            y = (bg_image.height - total_font_height) / 2 + vertical_offset
        elif vertical_align == 'bottom':
            y = bg_image.height - total_font_height - 10 + vertical_offset

        # Draw each line of text for this font
        for i, line in enumerate(text_lines):
            line_width = font.getbbox(line)[2]
            if text_align == 'left':
                x = 10 + horizontal_offset
            elif text_align == 'center':
                x = (bg_image.width -
                     line_width) / 2 + horizontal_offset
            else:  # right
                x = bg_image.width - line_width - 10 + horizontal_offset
            draw.text((x, y), line, font=font, fill=(0, 0, 0))
            y += line_heights[i] + line_spacing

        # Move y down for the next font (only if not bottom aligned)
        if vertical_align != 'bottom':
            y += vertical_offset

    # Add vectors (same as before)
    for vector_data in data['vectors']:
        vector = vector_data.get('vector')
        if vector:
            vector_scale = float(vector_data.get('vectorScale', 1))
            vector_x = int(vector_data.get('vectorX', 0))
            vector_y = int(vector_data.get('vectorY', 0))
            vector_path = os.path.join(VECTOR_FOLDER, vector)
            vector_image = Image.open(vector_path)

            new_size = (int(vector_image.width * vector_scale),
                        int(vector_image.height * vector_scale))
            vector_image = vector_image.resize(new_size, Image.LANCZOS)

            bg_image.paste(vector_image, (vector_x, vector_y), vector_image)

    # Save and encode the image
    buffered = io.BytesIO()
    bg_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return jsonify({'image': img_str})


@app.route('/merge_mockups', methods=['POST'])
def merge_mockups():
    data = request.json
    images_base64 = data['images']

    # Decode the base64 images into PIL Image objects
    images = [Image.open(io.BytesIO(base64.b64decode(
        img))) for img in images_base64]

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
    app.run(host='0.0.0.0', port=8080, debug=True)