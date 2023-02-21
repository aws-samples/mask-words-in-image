# mask-words-in-image

## Introduction

A tool that can mask words in an image file. User specifies which words should be masked, it can be any combinations of the following three types.

- Regular expressions
- Keywords
- PII (Personally Identifiable Information)

Under the hood, it use the Text Detection capability in [Amazon Rekognition](https://docs.aws.amazon.com/rekognition/latest/dg/what-is.html) or [AWS Textract](https://docs.aws.amazon.com/textract/latest/dg/what-is.html) to detect the texts in the image, then use [Amazon Comprehend](https://docs.aws.amazon.com/comprehend/latest/dg/what-is.html) to detect PII entities in texts.

## Requirements

- Python 3.8+
- AWS account

## Usage

1. Install the modules `pip install -r src/requirements.txt`.

2. Set up your AWS credential.

3. Follow the below usage to mask your first image. Here are some examples:

   - Mask AWS account ID in the design diagram: `python src/mask_it.py -i assets/design_diagram.png -r rules.yaml`
   - Mask the keyword "stack-set-id" in the code sample: `python src/mask_it.py -i assets/code_sample.png -k stack-set-id`

```
usage: mask_it.py [-h] -i INPUT_FILE [-o OUTPUT_FILE] [-r RULES_FILE] [-k KEYWORDS] [-e EXCLUDE_WORDS] [-t {document,photo}] [--pii] [--pii-confidence-threshold PII_CONFIDENCE_THRESHOLD] [--use-grey-rectangle] [--verbose]

options:
  -h, --help            show this help message and exit
  -i INPUT_FILE, --input-file INPUT_FILE
                        Original image file
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        Masked image output file
  -r RULES_FILE, --rules-file RULES_FILE
                        Rules configuration file
  -k KEYWORDS, --keywords KEYWORDS
                        Mask the keywords (case insensitive)
  -e EXCLUDE_WORDS, --exclude-words EXCLUDE_WORDS
                        Exclude the words (case insensitive)
  -t {document,photo}, --image-type {document,photo}
                        Image type (default is document)
  --pii                 Mask Personally Identifiable Information (PII)
  --pii-confidence-threshold PII_CONFIDENCE_THRESHOLD
                        PII detection confidence threshold (in percentage). Default is 0.8
  --use-grey-rectangle  Use grey rectangle masking (default is asterisk)
  --verbose             Debugging mode
```

## Tips

- Use `-t photo` if the image is a photo of the real world (by default it is `-t document`).
- Use `-k <keyword1> -k <keyword2>...` to specify mutliple keywords.
- Use `-e <keyword1> -e <keyword2>...` to exclude multiple keywords (e.g exclude the words from the rules or pii).
- Use `--pii` to mask PII in an image, e.g vehicle registration plate in a car image.
- Use `--pii-confidence-threshold` to adjust the PII detection confidence threshold (in percentage).
- Use `--use-grey-rectangle` if you prefer grey rectangle rather than asterisks.
- Use `--verbose` to see detailed information.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
