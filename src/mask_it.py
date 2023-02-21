# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Mask It"""
import argparse
import logging
import os

from lib import aws, log, tools


def parse_args():
    """Parse arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-file", help="Original image file", required=True)
    parser.add_argument("-o", "--output-file", help="Masked image output file")
    parser.add_argument("-r", "--rules-file", help="Rules configuration file")
    parser.add_argument(
        "-k", "--keywords", help="Mask the keywords (case insensitive)", action="append"
    )
    parser.add_argument(
        "-e",
        "--exclude-words",
        help="Exclude the words (case insensitive)",
        action="append",
    )
    parser.add_argument(
        "-t",
        "--image-type",
        help="Image type (default is document)",
        default="document",
        choices=["document", "photo"],
    )
    parser.add_argument(
        "--pii",
        help="Mask Personally Identifiable Information (PII)",
        action="store_true",
    )
    parser.add_argument(
        "--pii-confidence-threshold",
        help="PII detection confidence threshold (in percentage). Default is 0.8",
        default=0.8,
    )
    parser.add_argument(
        "--use-grey-rectangle",
        help="Use grey rectangle masking (default is asterisk)",
        action="store_true",
    )
    parser.add_argument(
        "--verbose",
        help="Debugging mode",
        action="store_true",
    )
    return parser.parse_args()


def mask_it():
    """Detect texts in image and mask it if exists"""
    texts_need_to_be_masked = []
    args = parse_args()
    input_image_file = args.input_file
    image_type = args.image_type
    exclude_words = []
    if args.exclude_words:
        exclude_words = args.exclude_words
    use_grey_rectangle = args.use_grey_rectangle
    output_image_file = f"./masked_{os.path.basename(input_image_file)}"
    if args.output_file:
        output_image_file = args.output_file
    if args.verbose:
        log.logger.level = logging.DEBUG
    if (not args.keywords) and (not args.rules_file) and (not args.pii):
        log.error(
            "Please specify at least one of the parameters: --rules-file, --keywords, --pii"
        )
    if args.rules_file:
        rules_config = tools.load_rules(args.rules_file)
    if args.pii:
        pii_confidence_threshold = float(args.pii_confidence_threshold)
        if not 0 <= pii_confidence_threshold <= 1:
            log.error(
                "PII detection confidence threshold (in percentage) should be between 0 and 1"
            )
        comprehend = aws.Comprehend()
    with open(input_image_file, "rb") as image:
        input_image_bytes = {"Bytes": image.read()}
        if image_type == "document":
            log.debug("Image type is document, use Textract to detect texts.")
            textract = aws.Textract()
            detected_texts_info = textract.detect_text(
                input_image_bytes, input_image_file
            )
        if image_type == "photo":
            log.debug("Image type is photo, use Rekognition to detect texts.")
            rekognition = aws.Rekognition()
            detected_texts_info = rekognition.detect_text(
                input_image_bytes, input_image_file
            )
        if detected_texts_info:
            for text_info in detected_texts_info:
                detected_lines = []
                if image_type == "document":
                    if text_info["BlockType"] == "LINE":
                        detected_lines = text_info["Text"]
                        log.debug(f"Detected lines: {detected_lines}")
                if image_type == "photo":
                    if text_info["Type"] == "LINE":
                        detected_lines = text_info["DetectedText"]
                        log.debug(f"Detected lines: {detected_lines}")
                text_info["Keywords"] = []
                if detected_lines:
                    if args.rules_file:
                        tools.add_rules_based_keywords(
                            text_info, detected_lines, rules_config["rules"]
                        )
                    if args.keywords:
                        tools.add_user_specified_keywords(
                            text_info, detected_lines, args.keywords
                        )
                    if args.pii:
                        entities = comprehend.detect_pii(detected_lines)
                        tools.add_pii_keywords(
                            text_info,
                            detected_lines,
                            entities,
                            pii_confidence_threshold,
                        )
                if text_info["Keywords"]:
                    texts_need_to_be_masked.append(text_info)
    if not texts_need_to_be_masked:
        log.info(f"No texts need to be masked in {input_image_file}")
        return
    tools.mask_texts_in_image(
        input_image_file,
        texts_need_to_be_masked,
        exclude_words,
        output_image_file,
        use_grey_rectangle,
    )
    log.info("Done!")
    return


if __name__ == "__main__":
    mask_it()
