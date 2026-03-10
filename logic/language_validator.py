# logic/language_validator.py

from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from config.settings import ALLOWED_LANGUAGE

# Ensures consistent detection results every run
DetectorFactory.seed = 0


class LanguageValidator:
    """
    Validates that input text is English (en-US) only.
    Rejects any other language before sending to OpenAI.
    """

    @staticmethod
    def is_english(text: str) -> bool:
        """Returns True only if detected language is English"""
        try:
            if not text or len(text.strip()) < 3:
                return False

            detected = detect(text.strip())
            return detected == ALLOWED_LANGUAGE

        except LangDetectException:
            return False

    @staticmethod
    def validate(text: str) -> tuple:
        """
        Returns (is_valid, error_message)
        is_valid = True  → English detected, proceed
        is_valid = False → Non-English, show error
        """
        if not text or len(text.strip()) == 0:
            return False, "⚠️ Please enter a question."

        if len(text.strip()) < 3:
            return False, "⚠️ Question is too short."

        try:
            detected = detect(text.strip())

            if detected == ALLOWED_LANGUAGE:
                return True, ""
            else:
                return False, (
                    f"🌐 Only English (en-US) is accepted. "
                    f"Detected language: [{detected.upper()}]. "
                    f"Please retype in English."
                )

        except LangDetectException:
            return False, "⚠️ Could not detect language. Please type in English."