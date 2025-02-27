import os
from PIL import Image, ImageDraw, ImageFont


base_image = "agedhands.jpeg"
absolute_path = os.path.abspath(base_image)
print(f"Absolute path: {absolute_path}")
print("test")

print(os.path.exists("C:\\Users\\tiger\\OneDrive\\Documents\\coding projects\\auto-posting\\agedhands.jpeg"))

script_dir = os.path.dirname(os.path.abspath(__file__))  # Get script's directory
base_image = os.path.join(script_dir, "agedhands.jpeg")  # Use correct relative path

print("Using base image:", base_image)  # Debugging