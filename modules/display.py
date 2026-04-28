# -*- coding: utf-8 -*-
import glob
import random
from PIL import Image
from config import DISPLAY_W, DISPLAY_H


def get_bg_images(folder):
    """Load all images from folder and preprocess to 320x480"""
    paths = sorted(
        glob.glob(f"{folder}/*.jpg")
        + glob.glob(f"{folder}/*.png")
        + glob.glob(f"{folder}/*.jpeg")
    )
    if not paths:
        raise FileNotFoundError(f"No images in {folder}")

    images = []
    for path in paths:
        img = Image.open(path).convert("RGB")
        if img.size != (DISPLAY_W, DISPLAY_H):
            canvas = Image.new("RGB", (DISPLAY_W, DISPLAY_H), (0, 0, 0))
            x = (DISPLAY_W - img.size[0]) // 2
            y = (DISPLAY_H - img.size[1]) // 2
            canvas.paste(img, (x, y))
            img = canvas
        images.append(img)
        print(f"Loaded: {path}")

    random.shuffle(images)
    return images
