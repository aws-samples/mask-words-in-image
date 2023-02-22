"""AWS"""
import boto3
from botocore.exceptions import ClientError

from lib import log


class Rekognition:
    """
    Encapsulates an Amazon Rekognition image. This class is a thin wrapper
    around parts of the Boto3 Amazon Rekognition API.
    """

    def __init__(
        self,
    ):
        """
        Initializes
        """
        self.rekognition_client = boto3.client("rekognition")

    def detect_text(self, image: bytes, image_name: str) -> list:
        """
        Detects text in the image.
        :param image: Data that defines the image, either the image bytes or
                      an Amazon S3 bucket and object key.
        :param image_name: The name of the image.
        :return The list of text elements found in the image.
        """
        try:
            response = self.rekognition_client.detect_text(Image=image)
            texts = response["TextDetections"]
            log.debug(f"Detected {len(texts)} texts in {image_name}")
        except ClientError as error:
            log.error(error)
        else:
            return texts


class Comprehend:
    """Encapsulates Comprehend detection functions."""

    def __init__(self):
        """
        Initialization
        """
        self.comprehend_client = boto3.client("comprehend")

    def detect_pii(self, text: str, language_code="en") -> list:
        """
        Detects personally identifiable information (PII) in a document. PII can be
        things like names, account numbers, or addresses.
        :param text: The document to inspect.
        :param language_code: The language of the document.
        :return: The list of PII entities along with their confidence scores.
        """
        try:
            response = self.comprehend_client.detect_pii_entities(
                Text=text, LanguageCode=language_code
            )
            entities = response["Entities"]
            log.debug(f"Detected {len(entities)} PII entities in {text}.")
            if entities:
                log.debug(entities)
        except ClientError as error:
            log.error(error)
        else:
            return entities


class Textract:
    """Encapsulates Textract functions."""

    def __init__(self):
        """
        Initialization
        """
        self.textract_client = boto3.client("textract")

    def detect_text(self, document: bytes, document_name: str) -> list:
        """
        Detects text elements in a local image file or from in-memory byte data.
        The image must be in PNG or JPG format.
        :param document: In-memory byte data of a document image.
        :return: The list of blocks that detected in the image.
        """
        try:
            response = self.textract_client.detect_document_text(Document=document)
            blocks = response["Blocks"]
            log.debug(f"Detected {len(blocks)} blocks in {document_name}.")
        except ClientError as error:
            log.error(error)
        return blocks
