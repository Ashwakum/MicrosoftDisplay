# logic/openai_service.py

import io
import base64
import threading
from openai import OpenAI
from config.settings import (
    OPENAI_API_KEY,
    MAX_TOKENS
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

            if full_response:
                on_success(full_response)
            else:
                on_error("⚠️ Empty response. Try again.")

        except Exception as ex:
            on_error(str(ex))

    # ── Vision: Screenshots ───────────────────────────────────────────
    def ask_vision_async(self, base64_images: list,
                         on_success, on_error, on_chunk=None):
        print(f"✅ ask_vision_async — {len(base64_images)} image(s)")
        threading.Thread(
            target = self._call_vision_stream,
            args   = (base64_images,
                      on_success, on_error, on_chunk),
            daemon = True
        ).start()

    def _call_vision_stream(self, base64_images,
                            on_success, on_error, on_chunk):
        try:
            print(f"🔍 Vision stream — {len(base64_images)} image(s)")
            full_response = ""
            content       = []

            content.append({
                "type" : "text",
                "text" : (
                    "You are an expert Senior Developer assistant.\n\n"
                    "STEP 1 — READ THE IMAGE:\n"
                    "Read EVERY line of code, text, error, "
                    "class names, method names exactly as shown.\n\n"
                    "STEP 2 — GENERATE COMPLETE SOLUTION:\n"
                    "Write the FULL file from top to bottom.\n"
                    "Include ALL imports, namespace, class, "
                    "all methods with complete body.\n"
                    "NEVER use '...' or 'rest remains same'.\n\n"
                    "STEP 3 — EXPLAIN:\n"
                    "Explain what the code does and what you added.\n\n"
                    "OUTPUT FORMAT — STRICT HTML ONLY:\n"
                    "Use ONLY these tags: "
                    "<h2> <h3> <p> <ul> <ol> <li> "
                    "<strong> <code> <pre><code>\n"
                    "Put ALL code inside <pre><code>...</code></pre>\n"
                    "Do NOT use markdown (no ```backticks```)\n"
                    "Do NOT include <html><head><body> tags\n"
                    "Return inner HTML content ONLY"
                )
            })

            for i, b64 in enumerate(base64_images):
                print(f"🔍 Adding image {i + 1}")
                content.append({
                    "type"      : "image_url",
                    "image_url" : {
                        "url"    : f"data:image/jpeg;base64,{b64}",
                        "detail" : "high"
                    }
                })

            print("🔍 Calling gpt-4o...")
            stream = self._client.chat.completions.create(
                model      = "gpt-4o",
                max_tokens = 4096,
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

            print("🔍 Reading stream...")
            for chunk in stream:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    full_response += delta.content
                    if on_chunk:
                        on_chunk(full_response)

            print(f"✅ Vision done — {len(full_response)} chars")

            if full_response:
                on_success(full_response)
            else:
                on_error("⚠️ No response. Try again.")

        except Exception as ex:
            print(f"❌ Vision error: {type(ex).__name__}: {str(ex)}")
            on_error(str(ex))

    # ── System Prompt ─────────────────────────────────────────────────
    def _system_prompt(self) -> str:
        return (
            "You are an expert AI assistant for a Senior Developer.\n\n"

            "SKILLS: SharePoint, SPFx, Power Apps, Power Automate, "
            "React, TypeScript, C#, .NET, ASP.NET Core, Azure, "
            "SQL Server, Entity Framework, Microservices, "
            "SOLID, Design Patterns, JavaScript, System Design.\n\n"

            "=== STRICT OUTPUT RULES — NEVER BREAK ===\n\n"

            "1. OUTPUT FORMAT: Return ONLY inner HTML — "
            "no <html>, no <head>, no <body> tags.\n\n"

            "2. USE ONLY THESE HTML TAGS:\n"
            "   <h2>  — main heading\n"
            "   <h3>  — sub heading\n"
            "   <p>   — paragraph text\n"
            "   <ul><li>  — bullet list\n"
            "   <ol><li>  — numbered list\n"
            "   <strong>  — bold important words\n"
            "   <code>x</code>  — inline code\n"
            "   <pre><code>ALL CODE HERE</code></pre>  "
            "— every code block\n\n"

            "3. NO MARKDOWN EVER:\n"
            "   NEVER use ```python or ```csharp or ``` backticks\n"
            "   NEVER use **bold** or *italic* markdown\n"
            "   NEVER use # heading markdown\n"
            "   ALWAYS use HTML tags instead\n\n"

            "4. COMPLETE CODE ALWAYS:\n"
            "   NEVER truncate with '...'\n"
            "   NEVER write 'rest of code remains same'\n"
            "   ALWAYS write every single line\n\n"

            "5. EXAMPLE of correct response:\n"
            "<h2>Python For Loop</h2>\n"
            "<p>A <strong>for loop</strong> repeats code.</p>\n"
            "<pre><code>for i in range(5):\n"
            "    print(i)\n"
            "</code></pre>\n"
            "<p>This prints <code>0</code> to <code>4</code>.</p>\n"
        )

    # ── Helpers ───────────────────────────────────────────────────────
    def _trim(self, text: str) -> str:
        if len(text) > self.MAX_INPUT_CHARS:
            trimmed    = text[:self.MAX_INPUT_CHARS]
            last_space = trimmed.rfind(" ")
            if last_space > 0:
                trimmed = trimmed[:last_space]
            return trimmed
        return text