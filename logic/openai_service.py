# logic/openai_service.py

import threading
from openai import OpenAI
from config.settings import (
    OPENAI_API_KEY,
    MAX_TOKENS,
    ALLOWED_REGION,
    AZURE_REGION
)


class OpenAIService:

    MAX_INPUT_CHARS = 1000

    def __init__(self):
        self._client = OpenAI(api_key=OPENAI_API_KEY)

    # ── Text Question ─────────────────────────────────────────────────
    def ask_async(self, question: str,
                  on_success, on_error, on_chunk=None):
        threading.Thread(
            target = self._call_stream,
            args   = (question, on_success, on_error, on_chunk),
            daemon = True
        ).start()

    def _call_stream(self, question,
                     on_success, on_error, on_chunk):
        try:
            question      = self._trim(question)
            full_response = ""

            stream = self._client.chat.completions.create(
                model      = "gpt-4o-mini",
                max_tokens = MAX_TOKENS,
                stream     = True,
                messages   = [
                    {
                        "role"    : "system",
                        "content" : self._system_prompt()
                    },
                    {
                        "role"    : "user",
                        "content" : question
                    }
                ]
            )

            for chunk in stream:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    full_response += delta.content
                    if on_chunk:
                        on_chunk(full_response)

            on_success(full_response)

        except Exception as ex:
            error = str(ex)
            if "token" in error.lower():
                on_error("⚠️ Input too long. Please shorten.")
            else:
                on_error(error)

    # ── Vision: Images → OpenAI ───────────────────────────────────────
    def ask_vision_async(self, base64_images: list,
                         on_success, on_error, on_chunk=None):
        """Send screenshot images directly to OpenAI Vision API"""
        threading.Thread(
            target = self._call_vision_stream,
            args   = (base64_images,
                      on_success, on_error, on_chunk),
            daemon = True
        ).start()

    def _call_vision_stream(self, base64_images,
                            on_success, on_error, on_chunk):
        try:
            full_response = ""

            # ✅ Build content list with all images
            content = []

            # ✅ Add instruction text first
            content.append({
                "type" : "text",
                "text" : (
                    "Analyze these screenshots carefully.\n"
                    "1. If you see code — explain what it does "
                    "and how it works.\n"
                    "2. If you see a question — answer it "
                    "clearly and completely.\n"
                    "3. If you see an error — explain why it "
                    "happened and how to fix it.\n"
                    "4. If you see SQL — explain and optimize it.\n"
                    "5. Always give complete, working code "
                    "examples where relevant.\n"
                    "Format your response in clean HTML."
                )
            })

            # ✅ Add each screenshot as base64 image
            for b64 in base64_images:
                content.append({
                    "type"      : "image_url",
                    "image_url" : {
                        "url"    : f"data:image/png;base64,{b64}",
                        "detail" : "high"    # high detail OCR
                    }
                })

            stream = self._client.chat.completions.create(
                model      = "gpt-4o",      # ✅ Vision needs gpt-4o
                max_tokens = 2000,
                stream     = True,
                messages   = [
                    {
                        "role"    : "system",
                        "content" : self._system_prompt()
                    },
                    {
                        "role"    : "user",
                        "content" : content
                    }
                ]
            )

            for chunk in stream:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    full_response += delta.content
                    if on_chunk:
                        on_chunk(full_response)

            on_success(full_response)

        except Exception as ex:
            on_error(str(ex))

    # ── Helpers ───────────────────────────────────────────────────────
    def _trim(self, text: str) -> str:
        if len(text) > self.MAX_INPUT_CHARS:
            trimmed    = text[:self.MAX_INPUT_CHARS]
            last_space = trimmed.rfind(" ")
            if last_space > 0:
                trimmed = trimmed[:last_space]
            return trimmed
        return text

    def _system_prompt(self) -> str:
        return (
            "You are an expert AI assistant for a Senior Developer.\n\n"
            "Skills: SharePoint, SPFx, Power Apps, Power Automate, "
            "React, TypeScript, C#, Azure, SQL Server, Entity Framework, "
            "Microservices, SOLID, Design Patterns, MCP, JavaScript.\n\n"
            "RULES:\n"
            "1. Always return COMPLETE code — never truncate.\n"
            "2. Use simple clear English.\n"
            "3. Relate answers to the above skill set.\n"
            "4. Format in HTML only:\n"
            "   <h2> <h3> <p> <ul><li> <strong> "
            "   <code> <pre><code>\n"
            "5. Never include <html><head><body> tags.\n"
            "6. Return inner HTML content only.\n"
        )

    @property
    def screenshot_count(self) -> int:
        return 0