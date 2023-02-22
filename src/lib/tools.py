"""Tools"""
import os
import re

import numpy as np
import yaml
from PIL import Image, ImageDraw
from yaml.loader import SafeLoader

from lib import log


def load_rules(rules_file: str) -> dict:
    """Read rules"""
    if not os.path.exists(rules_file):
        log.error(f"{rules_file} does not exist")
    with open(rules_file, encoding="utf8") as rules:
        return yaml.load(rules, Loader=SafeLoader)


def mask_texts_in_image(
    input_image_file: str,
    texts_info: list,
    exclude_words: list,
    output_image_file: str,
    use_grey_rectangle: bool,
):
    """Mask texts in image"""
    with Image.open(input_image_file) as image:
        image_np = np.array(image)
        image_height, image_width = image_np.shape[:2]
        for text_info in texts_info:
            keywords = text_info["Keywords"]
            if "Text" in text_info:
                text = text_info["Text"]
            if "DetectedText" in text_info:
                text = text_info["DetectedText"]
            width_ratio = text_info["Geometry"]["BoundingBox"]["Width"]
            height_ratio = text_info["Geometry"]["BoundingBox"]["Height"]
            left_ratio = text_info["Geometry"]["BoundingBox"]["Left"]
            top_ratio = text_info["Geometry"]["BoundingBox"]["Top"]
            for keyword in keywords:
                if keyword.lower() in [word.lower() for word in exclude_words]:
                    log.debug(f"{keyword} is in the excluding list, don't mask it.")
                    continue
                log.debug(f"Masking {keyword} in {text} in image")
                for index in find_keyword_indexes(keyword, text):
                    left, upper, right, lower = map(
                        int,
                        (
                            (left_ratio + (index + 1) / len(text) * width_ratio)
                            * image_width,
                            top_ratio * image_height,
                            (
                                left_ratio
                                + ((index + 1) / len(text) + len(keyword) / len(text))
                                * width_ratio
                            )
                            * image_width,
                            (height_ratio + top_ratio) * image_height,
                        ),
                    )
                    bouding_box = (left, upper, right, lower)
                    area_needs_mask = image.crop(bouding_box)
                    masked_area_width, masked_area_height = area_needs_mask.size
                    asterisk_img = Image.new(
                        "RGB", (masked_area_width, masked_area_height), "white"
                    )
                    if use_grey_rectangle:
                        asterisk_img = Image.new(
                            "RGB", (masked_area_width, masked_area_height), "grey"
                        )
                    draw = ImageDraw.Draw(asterisk_img)
                    draw.text(
                        (0, 0),
                        "*" * (int(masked_area_width) * int(masked_area_height)),
                        fill="grey",
                    )
                    area_needs_mask.paste(asterisk_img, (0, 0))
                    image.paste(area_needs_mask, bouding_box)
        log.info(f"Saving masked image to {output_image_file}")
        image.save(output_image_file)


def find_keyword_indexes(keyword: str, text: str) -> list:
    """Find all keywords indexes in text"""
    indexes = []
    start = 0
    while start < len(text):
        index = text.lower().find(keyword.lower(), start)
        if index == -1:
            break
        indexes.append(index)
        start = index + len(keyword)
    return indexes


def add_rules_based_keywords(text_info: dict, detected_texts: str, rules: dict) -> dict:
    """Add rules based keywords"""
    for rule in rules:
        all_matched = re.findall(rule, detected_texts)
        if all_matched:
            for matched in all_matched:
                text_info["Keywords"].append(matched)
    return text_info


def add_user_specified_keywords(
    text_info: dict, detected_texts: str, keywords: list
) -> dict:
    """Add user specified keywords"""
    for keyword in keywords:
        if keyword.lower() in detected_texts.lower():
            text_info["Keywords"].append(keyword)
    return text_info


def add_pii_keywords(
    text_info: dict, detected_texts: str, pii_entities: list, confidence: int
) -> dict:
    """Add PII entities keywords"""
    if pii_entities:
        for entity in pii_entities:
            if entity["Score"] > confidence:
                text_info["Keywords"].append(
                    detected_texts[
                        int(entity["BeginOffset"]) : int(entity["EndOffset"])
                    ]
                )
    return text_info
