import base64
import json
from io import BytesIO

import qrcode
from PIL import Image, ImageDraw, ImageFont


def generate_qr_code_base64(code: str, name: str) -> str:
    """
    Generate a modern, styled QR code image and return it as a base64-encoded PNG.

    Args:
        code: The attendee code (e.g., "EP25NJAH")
        name: The attendee name to display at the top

    Returns:
        Base64-encoded PNG image string
    """
    # Edge City Patagonia color palette
    PRIMARY_COLOR = '#4d65ff'  # Bright blue (from edgecity.live)
    SECONDARY_COLOR = '#286C71'  # Teal/dark cyan
    ACCENT_COLOR = '#cde1da'  # Light sage green
    BACKGROUND_COLOR = '#0F0F3E'  # Dark navy background
    TEXT_COLOR = '#FFFFFF'  # White text
    QR_BACKGROUND = '#FFFFFF'  # White QR code background
    CARD_BACKGROUND = '#1a1a4a'  # Slightly lighter navy for depth

    # Design constants
    PADDING = 60  # Generous padding
    CARD_PADDING = 30  # Padding inside the card
    CORNER_RADIUS = 24  # Rounded corners
    TEXT_MARGIN = 40  # Space between QR code and text
    LINE_SPACING = 10  # Space between wrapped text lines

    # Load fonts early (needed for text wrapping calculation)
    try:
        font_name = ImageFont.truetype(
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 36
        )
        font_large = ImageFont.truetype(
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 48
        )
        font_small = ImageFont.truetype(
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20
        )
    except:
        font_name = ImageFont.load_default()
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Create the JSON content for the QR code
    qr_content = json.dumps({'code': code})

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)

    # Create the QR code image
    qr_img = qr.make_image(fill_color='black', back_color='white')
    qr_img = qr_img.convert('RGB')
    qr_width, qr_height = qr_img.size

    # Calculate dimensions
    card_width = qr_width + (CARD_PADDING * 2)

    # Create a temporary image to measure text for wrapping
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)

    # Calculate max width for name (card width minus padding on both sides)
    max_name_width = card_width - (CARD_PADDING * 2)

    # Wrap the name text if needed
    name_lines = _wrap_text(name, font_name, max_name_width, temp_draw)

    # Calculate name section height based on number of lines
    name_bbox = temp_draw.textbbox((0, 0), 'Ay', font=font_name)  # Measure line height
    line_height = name_bbox[3] - name_bbox[1]
    NAME_SECTION_HEIGHT = (
        CARD_PADDING
        + (line_height * len(name_lines))
        + (LINE_SPACING * (len(name_lines) - 1))
        + 20
    )

    card_height = (
        NAME_SECTION_HEIGHT + qr_height + (CARD_PADDING * 2) + TEXT_MARGIN + 80
    )
    canvas_width = card_width + (PADDING * 2)
    canvas_height = card_height + (PADDING * 2)

    # Create canvas with dark background
    final_img = Image.new('RGB', (canvas_width, canvas_height), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(final_img)

    # Draw decorative circles in corners
    circle_radius = 120
    circle_alpha = 40

    # Top-left decorative circle (primary color)
    circle_overlay = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
    circle_draw = ImageDraw.Draw(circle_overlay)
    circle_draw.ellipse(
        [(-60, -60), (circle_radius, circle_radius)],
        fill=(*_hex_to_rgb(PRIMARY_COLOR), circle_alpha),
    )
    # Bottom-right decorative circle (secondary color)
    circle_draw.ellipse(
        [
            (canvas_width - circle_radius + 60, canvas_height - circle_radius + 60),
            (canvas_width + 60, canvas_height + 60),
        ],
        fill=(*_hex_to_rgb(SECONDARY_COLOR), circle_alpha),
    )
    # Top-right decorative circle (accent color)
    circle_draw.ellipse(
        [
            (canvas_width - circle_radius + 40, -40),
            (canvas_width + 80, circle_radius),
        ],
        fill=(*_hex_to_rgb(ACCENT_COLOR), circle_alpha),
    )

    final_img = Image.alpha_composite(
        final_img.convert('RGBA'), circle_overlay
    ).convert('RGB')
    draw = ImageDraw.Draw(final_img)

    # Draw the main card with gradient-like effect
    card_x = PADDING
    card_y = PADDING

    # Card shadow
    shadow_offset = 8
    draw.rounded_rectangle(
        [
            card_x + shadow_offset,
            card_y + shadow_offset,
            card_x + card_width + shadow_offset,
            card_y + card_height + shadow_offset,
        ],
        radius=CORNER_RADIUS,
        fill='#00000040',
    )

    # Main card background
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_width, card_y + card_height],
        radius=CORNER_RADIUS,
        fill=CARD_BACKGROUND,
    )

    # Draw the attendee name at the top (multi-line support)
    name_y = card_y + CARD_PADDING
    for line in name_lines:
        line_bbox = draw.textbbox((0, 0), line, font=font_name)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = card_x + (card_width - line_width) // 2

        # Draw line with colored shadow
        draw.text((line_x + 2, name_y + 2), line, fill=PRIMARY_COLOR, font=font_name)
        draw.text((line_x, name_y), line, fill=TEXT_COLOR, font=font_name)

        # Move to next line position
        name_y += line_height + LINE_SPACING

    # Draw QR code container with white background
    qr_x = card_x + CARD_PADDING
    qr_y = card_y + CARD_PADDING + NAME_SECTION_HEIGHT

    # QR code background with slight elevation
    draw.rounded_rectangle(
        [qr_x - 4, qr_y - 4, qr_x + qr_width + 4, qr_y + qr_height + 4],
        radius=16,
        fill=QR_BACKGROUND,
    )

    # Create mask for rounded QR code
    mask = Image.new('L', (qr_width, qr_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (qr_width, qr_height)], radius=12, fill=255)

    # Paste QR code
    qr_temp = Image.new('RGB', (qr_width, qr_height), QR_BACKGROUND)
    qr_temp.paste(qr_img, (0, 0))
    final_img.paste(qr_temp, (qr_x, qr_y), mask)

    # Calculate text position
    text_y = qr_y + qr_height + TEXT_MARGIN

    # Draw "ATTENDEE CODE" label
    label_text = 'ATTENDEE CODE'
    label_bbox = draw.textbbox((0, 0), label_text, font=font_small)
    label_width = label_bbox[2] - label_bbox[0]
    label_x = card_x + (card_width - label_width) // 2
    draw.text((label_x, text_y - 25), label_text, fill='#94A3B8', font=font_small)

    # Draw the code with gradient-like color
    code_bbox = draw.textbbox((0, 0), code, font=font_large)
    code_width = code_bbox[2] - code_bbox[0]
    code_x = card_x + (card_width - code_width) // 2

    # Draw text with colored shadow for depth
    draw.text((code_x + 2, text_y + 2), code, fill=PRIMARY_COLOR, font=font_large)
    draw.text((code_x, text_y), code, fill=TEXT_COLOR, font=font_large)

    # Add small decorative accent dots
    dot_y = card_y + card_height - 15
    dot_spacing = 12
    dot_radius = 4
    dot_start_x = card_x + (card_width - (dot_spacing * 4)) // 2

    colors = [
        SECONDARY_COLOR,
        PRIMARY_COLOR,
        ACCENT_COLOR,
        PRIMARY_COLOR,
        SECONDARY_COLOR,
    ]
    for i, color in enumerate(colors):
        dot_x = dot_start_x + (i * dot_spacing)
        draw.ellipse(
            [dot_x, dot_y, dot_x + dot_radius, dot_y + dot_radius],
            fill=color,
        )

    # Convert to base64
    buffered = BytesIO()
    final_img.save(buffered, format='PNG')
    img_bytes = buffered.getvalue()
    base64_str = base64.b64encode(img_bytes).decode('utf-8')

    return base64_str


def _hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _wrap_text(text, font, max_width, draw):
    """
    Wrap text to fit within a maximum width, breaking at word boundaries.

    Args:
        text: The text to wrap
        font: The font to use for measuring
        max_width: Maximum width in pixels
        draw: ImageDraw object for measuring text

    Returns:
        List of lines
    """
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        # Try adding the word to the current line
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line.append(word)
        else:
            # Current line is full, start a new one
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                # Single word is too long, add it anyway
                lines.append(word)

    # Add the last line
    if current_line:
        lines.append(' '.join(current_line))

    return lines if lines else [text]
