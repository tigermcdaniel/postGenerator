import textwrap
import requests
import os
import openai
import re
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
from colorthief import ColorThief
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("API_KEY"), 
)

output_directory = r"C:\Users\tiger\OneDrive\Documents\coding projects\postGenerator\output"
input_directory = r"C:\Users\tiger\OneDrive\Documents\coding projects\postGenerator\input"

def create_cover_image(text, base_image, image_size=(1080, 1080), bg_color=(0,0,0)):
    """Generate an Instagram-style post image with an optional base image."""
    print("Creating post image...")
    
    base_image_path = os.path.join(input_directory, base_image) 
    img = Image.open(base_image_path).convert("RGB")
    
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 70)
    except IOError:
        font = ImageFont.load_default()  # Fallback in case font file is missing
    
    # Define padding
    padding = 50 

    # Wrap text for better readability
    wrapped_text = textwrap.fill(text, width=20)  # Reduce width for more margin

    # Calculate text size
    text_size = draw.textbbox((0, 0), wrapped_text, font=font)

    # Calculate positions with padding
    text_x = max(padding, (img.width - text_size[2]) // 2)  # Ensure at least `padding` from edges
    text_y = max(padding, (img.height - text_size[3]) // 2)

    # Add a semi-transparent background behind the text
    bg_margin = 20  # Padding around text
    background_box = [
        text_x - bg_margin,   # Left
        text_y - bg_margin,   # Top
        text_x + text_size[2] + bg_margin,  # Right
        text_y + text_size[3] + bg_margin   # Bottom
    ]
    
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))  # Transparent overlay
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(background_box, fill=(*bg_color, 200))  # background with opacity

    # Merge overlay with original image
    img = Image.alpha_composite(img.convert("RGBA"), overlay)

    text_color = get_high_contrast_text_color(bg_color)

    # Draw text on top of the background
    draw = ImageDraw.Draw(img)
    draw.text((text_x, text_y), wrapped_text, font=font, fill=text_color)

    img = img.convert("RGB") 
    return img

def query_chatgpt(prompt):
    """
    Query ChatGPT with a given prompt.
    
    """

    structured_prompt = f"""
    {prompt}
    
    Please structure the response into 3-4 sections with clear headings.
    Use double line breaks (\n\n) to separate sections.
    Each section should have the response in this format:
    - A label [HEADER] before the header
    - A label [BODY] before the paragraph body (1-2 sentences).
    """

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": structured_prompt}],
        stream=True,
    )

    response_text = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            if(len(chunk.choices[0].delta.content) == 0): 
                continue
            response_text += chunk.choices[0].delta.content
    return response_text

def is_light_color(rgb):
    """Returns True if a color is light, False if dark."""
    r, g, b = rgb
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255  # Perceived brightness formula
    return luminance > 0.5  # Light colors have higher luminance

def get_high_contrast_text_color(bg_color):
    """Returns black or white text color based on the background."""
    return (0, 0, 0) if is_light_color(bg_color) else (255, 255, 255)

def create_content_image(header, body, image_size=(1080, 1080), bg_color="#F5F5F5"):
    """
    Creates an image with a header and body text.
    The header is displayed above the body with a larger font.
    Returns the generated image object.
    """

    img = Image.new("RGBA", image_size, bg_color)  # Light gray background

    draw = ImageDraw.Draw(img)

    # Load fonts (try custom, fallback to default)
    try:
        if(image_size[0] == 1080 and image_size[1] == 1080):
            header_font = ImageFont.truetype("arial.ttf", 70) 
            body_font = ImageFont.truetype("arial.ttf", 50)  
        else: 
            header_font = ImageFont.truetype("arial.ttf", 60)  
            body_font = ImageFont.truetype("arial.ttf", 40) 
    except IOError:
        header_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    # Wrap text with a narrower width for the header to create a buffer
    wrapped_header = textwrap.fill(header, width=25)  # Reduce width for more margin
    wrapped_body = textwrap.fill(body, width=30)  # Keep body text as is

    # Get text sizes
    header_size = draw.textbbox((0, 0), wrapped_header, font=header_font)
    body_size = draw.textbbox((0, 0), wrapped_body, font=body_font)

    # Calculate positions
    total_text_height = header_size[3] + 15 + body_size[3]  
    start_y = (img.height - total_text_height) // 2  

    header_x = (img.width - header_size[2]) // 2
    header_y = start_y

    body_x = (img.width - body_size[2]) // 2
    body_y = header_y + header_size[3] + 30  


    # Draw text
    text_color = get_high_contrast_text_color(bg_color)
    draw.text((header_x, header_y), wrapped_header, font=header_font, fill=text_color)
    draw.text((body_x, body_y), wrapped_body, font=body_font, fill=text_color)

    return img 

def get_image_palette(image_path, num_colors=6):
    """Extracts the dominant color palette from an image."""
    base_image_path = os.path.join(input_directory, image_path) 
    color_thief = ColorThief(base_image_path)
    palette = color_thief.get_palette(color_count=num_colors)
    return palette

def generate_post(post_name, cover_path, prompt):
    # make a directory to store outputs 
    output_path = os.path.join(output_directory, post_name)
    os.makedirs(output_path, exist_ok=True)

    # get the image size
    input_path = os.path.join(input_directory, cover_path) 
    cover = Image.open(input_path)
    width, height = cover.size

    # get the color palette
    palette = get_image_palette(cover_path)
    print(f"Color Palette: {palette}")

    # create the cover image
    cover_image = create_cover_image(prompt, cover_path, (width, height), palette[0])

    # save the cover image 
    cover_output_path = os.path.join(output_path, "cover.jpeg")
    cover_image.save(cover_output_path)
    print(f"Cover image saved as {cover_output_path}")

    # query chat gtp
    result = query_chatgpt(prompt)
    print(result)

    #create the following images
    headers = re.findall(r"\[HEADER\] (.+)", result)
    bodies = re.findall(r"\[BODY\] (.+)", result)

    # Ensure headers and bodies are paired
    sections = list(zip(headers, bodies))

    for i, (header, body) in enumerate(sections, start=1):

        content_output_path = os.path.join(output_path, f"post_{i}.jpeg")

        content_image = create_content_image(header, body, (width, height), palette[i])

        content_image.convert("RGB").save(content_output_path)
        print(f"Content image saved as {content_output_path}")


# example: nameForProject, coverPhotoName(in inputs folder), Prompt
# generate_post("cellularAging", 'Microbes.jpeg', "What is cellular aging, and can we slow it down?")
# generate_post("agingHands", 'agedhands.jpeg', "What are the top habits of people who live past 100?")
# generate_post("healthyEating", 'food.jpeg', "What do the longest-living people eat daily?")
# generate_post("coolGma", 'coolgma.jpeg', "Which supplements have the most evidence for longevity?")
# generate_post("stylegma", 'stylegma.jpeg', "Can gratitude and optimism help you live longer?")
# generate_post("teagma", 'teapart.jpeg', "Why is play and creativity important for aging well?")
# generate_post("tomato", 'tomato.jpeg', "How does a plant-based diet impact lifespan?")
# generate_post("corn", 'corn.jpeg', "What are the best anti-inflammatory foods for longevity?")
# generate_post("paint", 'paint.jpeg', "Why do purpose-driven people live longer?")
# generate_post("breath", 'breath.jpeg', "Can breathing techniques improve longevity?")
# generate_post("cells", 'cells.jpeg', "How can stem cells help reverse aging?")
generate_post("lightfood", 'lightfood.jpeg', "What’s the future of wellness?")