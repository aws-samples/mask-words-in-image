"""Demo of using mask it with Slack"""
import logging
import os
import shutil

import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from lib import aws, log, tools

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_USER_TOKEN = os.environ["SLACK_USER_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
REKOGNITION_CLIENT = aws.Rekognition()
COMPREHEND_CLINENT = aws.Comprehend()

# Customizable parameters
DEBUG_MODE = True
RULES_FILE = "rules.yaml"
EXCLUDE_WORDS = []
PII_CONFIDENCE_THRESHOLD = 0.2

if DEBUG_MODE:
    log.logger.level = logging.DEBUG

app = App(token=SLACK_BOT_TOKEN)


def file_downloader(filename, url):
    """Download file from url"""
    log.info(f"Downloading {filename}")
    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    response = requests.get(url, stream=True, headers=headers, timeout=10)
    with open(filename, "wb") as downloaded_file:
        shutil.copyfileobj(response.raw, downloaded_file)


def mask_it(
    filename,
    rules_file,
    exclude_words,
    rekognition_client,
    comprehend_client,
    pii_confidence_threshold,
):
    """Detect and mask PII in image"""
    texts_need_to_be_masked = []
    use_grey_rectangle = True
    input_image_file = filename
    output_image_file = filename
    rules_config = tools.load_rules(rules_file)
    with open(input_image_file, "rb") as image:
        input_image_bytes = {"Bytes": image.read()}
        detected_texts_info = rekognition_client.detect_text(
            input_image_bytes, input_image_file
        )
        if detected_texts_info:
            all_detected_lines = [
                text_info["DetectedText"]
                for text_info in detected_texts_info
                if text_info["Type"] == "LINE"
            ]
            log.info(" ".join(all_detected_lines))
            for text_info in detected_texts_info:
                detected_lines = []
                if text_info["Type"] == "LINE":
                    detected_lines = text_info["DetectedText"]
                    log.debug(f"Detected lines: {detected_lines}")
                text_info["Keywords"] = []
                if detected_lines:
                    tools.add_rules_based_keywords(
                        text_info, detected_lines, rules_config["rules"]
                    )
                    entities = comprehend_client.detect_pii(detected_lines)
                    tools.add_pii_keywords(
                        text_info,
                        detected_lines,
                        entities,
                        pii_confidence_threshold,
                    )
                if text_info["Keywords"]:
                    texts_need_to_be_masked.append(text_info)
    if not texts_need_to_be_masked:
        log.info(f"No sensitive data was found in {input_image_file}")
        return False
    tools.mask_texts_in_image(
        input_image_file,
        texts_need_to_be_masked,
        exclude_words,
        output_image_file,
        use_grey_rectangle,
    )
    log.info(f"Sensitive data has been masked in {input_image_file}")
    return True


@app.event("message")
def message_events_handler(body, logger):
    """Message events handler"""
    logger.debug(body)


@app.event("file_shared")
def file_shared_events_handler(body, say, logger):
    """File shared event handler"""
    logger.debug(body)
    file_id = body["event"]["file_id"]
    file_info = app.client.files_info(file=file_id)["file"]
    file_name = file_info["name"]
    file_type = file_info["filetype"]
    file_user = file_info["user"]
    file_url = file_info["url_private_download"]
    channel = file_info["channels"][0]
    logger.info(f"File {file_name} has been shared.")
    try:
        if file_type in ("png", "jpeg", "jpg"):
            file_downloader(file_name, file_url)
            if mask_it(
                file_name,
                RULES_FILE,
                EXCLUDE_WORDS,
                REKOGNITION_CLIENT,
                COMPREHEND_CLINENT,
                PII_CONFIDENCE_THRESHOLD,
            ):
                say(
                    text=f"Hi <@{file_user}>! "
                    f"{file_name} has been removed as it has `sensitive` data, "
                    f"here is the masked version."
                )
                app.client.files_delete(token=SLACK_USER_TOKEN, file=file_id)
                logger.info("Uploading masked image.")
                response = app.client.files_upload_v2(
                    channel=channel, file=file_name, filename=file_name
                )
                logger.debug(response)
            else:
                log.info(f"No need to mask {file_name}")
    except Exception as error:
        log.error(f"Oops, something went wrong. {error}")
    finally:
        if os.path.exists(file_name):
            log.info(f"Remove file {file_name} from local disk")
            os.remove(file_name)


if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
