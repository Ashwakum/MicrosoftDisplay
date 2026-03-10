# logic/html_builder.py


class HtmlBuilder:

    # ── Shared CSS ────────────────────────────────────────────────────
    _CSS = """
    <style>
      * {
        box-sizing : border-box;
        margin     : 0;
        padding    : 0;
      }

      body {
        font-family : Segoe UI, Arial, sans-serif;
        background  : #1e1e2e;
        color       : #e0e0e0;
        padding     : 20px;
        line-height : 1.7;
        font-size   : 14px;
      }

      .card {
        background    : #2e2e3e;
        border-radius : 10px;
        padding       : 20px 24px;
        border-left   : 4px solid #7c6af7;
      }

      h2 {
        color         : #a78bfa;
        font-size     : 18px;
        font-weight   : 700;
        margin-bottom : 12px;
        padding-bottom: 8px;
        border-bottom : 1px solid #444466;
      }

      h3 {
        color         : #c4b5fd;
        font-size     : 15px;
        font-weight   : 600;
        margin        : 16px 0 8px 0;
      }

      p {
        color         : #d0d0e8;
        margin-bottom : 10px;
        font-size     : 14px;
      }

      ul, ol {
        padding-left  : 22px;
        margin-bottom : 12px;
      }

      li {
        color         : #d0d0e8;
        margin-bottom : 6px;
        font-size     : 14px;
      }

      strong {
        color         : #f0c060;
        font-weight   : 700;
      }

      code {
        background    : #3a3a5c;
        color         : #f472b6;
        padding       : 2px 7px;
        border-radius : 4px;
        font-family   : Consolas, Courier New, monospace;
        font-size     : 13px;
      }

      pre {
        background    : #12121e;
        border-radius : 8px;
        padding       : 16px;
        margin        : 12px 0;
        overflow-x    : auto;
        border-left   : 4px solid #7c6af7;
      }

      pre code {
        background    : transparent;
        color         : #a8ff78;
        font-family   : Consolas, Courier New, monospace;
        font-size     : 13px;
        line-height   : 1.8;
        padding       : 0;
        border-radius : 0;
      }

      .info {
        color         : #94a3b8;
        font-size     : 13px;
        font-style    : italic;
      }

      .error-box {
        background    : #3b0f0f;
        border-left   : 4px solid #ef4444;
        border-radius : 8px;
        padding       : 16px;
        color         : #fca5a5;
      }

      .loading {
        color         : #94a3b8;
        font-style    : italic;
        animation     : pulse 1.5s infinite;
      }

      @keyframes pulse {
        0%   { opacity: 1.0; }
        50%  { opacity: 0.4; }
        100% { opacity: 1.0; }
      }
    </style>
    """

    # ── Page Wrapper ──────────────────────────────────────────────────
    @staticmethod
    def _wrap(body_html: str) -> str:
        return (
            "<!DOCTYPE html>"
            "<html><head>"
            "<meta charset='utf-8'>"
            + HtmlBuilder._CSS +
            "</head><body>"
            "<div class='card'>"
            + body_html +
            "</div></body></html>"
        )

    # ── Public Methods ────────────────────────────────────────────────
    @staticmethod
    def build_page(content: str) -> str:
        """
        Wrap AI response in full HTML page.
        content = raw HTML from OpenAI (h2/h3/p/pre/code etc.)
        """
        return HtmlBuilder._wrap(content)

    @staticmethod
    def build_empty() -> str:
        return HtmlBuilder._wrap(
            "<h2>👋 Welcome to AI Assistant</h2>"
            "<p>Type a question and press <strong>Enter</strong>.</p>"
            "<p>Or use <strong>🔊 System [1]</strong> "
            "to capture Teams / Zoom / Meet audio.</p>"
            "<p>Or use <strong>🎤 Mic [4]</strong> "
            "to speak directly.</p>"
            "<p>Or press <strong>7</strong> to capture a screenshot "
            "then <strong>8</strong> to send to AI.</p>"
            "<p class='info'>Keyboard: "
            "1=System  2=Pause  3=Resume  "
            "4=Mic  5=Reset  7=Screenshot  8=Send</p>"
        )

    @staticmethod
    def build_loading() -> str:
        return HtmlBuilder._wrap(
            "<h2>⏳ Thinking...</h2>"
            "<p class='loading'>AI is generating your answer. "
            "Please wait...</p>"
        )

    @staticmethod
    def build_error(message: str) -> str:
        return HtmlBuilder._wrap(
            "<div class='error-box'>"
            "<h2>⚠️ Error</h2>"
            f"<p>{message}</p>"
            "</div>"
        )

    @staticmethod
    def build_language_error(message: str) -> str:
        return HtmlBuilder._wrap(
            "<div class='error-box'>"
            "<h2>🌐 English Only</h2>"
            f"<p>{message}</p>"
            "<p>This assistant only accepts "
            "<strong>English (en-US)</strong> input.</p>"
            "<ul>"
            "<li>✅ <code>What is a for loop?</code></li>"
            "<li>✅ <code>How do I use async/await in C#?</code>"
            "</li>"
            "<li>❌ Non-English text is rejected</li>"
            "</ul>"
            "</div>"
        )