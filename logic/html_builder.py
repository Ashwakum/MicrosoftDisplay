# logic/html_builder.py

from config.settings import ACCENT_COLOR


class HtmlBuilder:

    @staticmethod
    def build_page(content_html: str) -> str:
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family : 'Segoe UI', Arial, sans-serif;
    background  : #C6C6C6;
    min-height  : 100vh;
    padding     : 24px;
    color       : #000000;
    line-height : 1.7;
  }}

  .card {{
    background    : #C6C6C6;
    border-radius : 12px;
    padding       : 24px;
    border-left   : 4px solid {ACCENT_COLOR};
    box-shadow    : 0 2px 12px rgba(0,0,0,0.12);
    animation     : fadeIn 0.4s ease;
  }}

  h2 {{
    color         : #000000;
    font-size     : 20px;
    font-weight   : 700;
    margin-bottom : 14px;
    border-bottom : 2px solid #000000;
    padding-bottom: 8px;
  }}

  h3 {{
    color         : #000000;
    font-size     : 16px;
    font-weight   : 600;
    margin        : 14px 0 8px 0;
  }}

  p {{
    margin-bottom : 12px;
    color         : #000000;
    font-size     : 14px;
  }}

  ul {{
    padding-left  : 20px;
    margin-bottom : 12px;
  }}

  li {{
    margin-bottom : 8px;
    color         : #000000;
    font-size     : 14px;
  }}

  code {{
    background    : #b0b0b0;
    color         : #000000;
    padding       : 2px 8px;
    border-radius : 4px;
    font-family   : 'Consolas', monospace;
    font-size     : 13px;
    font-weight   : 600;
  }}

  pre {{
    background    : #a0a0a0;
    border-radius : 8px;
    padding       : 16px;
    overflow-x    : auto;
    margin        : 12px 0;
    border-left   : 3px solid #000000;
  }}

  pre code {{
    background    : transparent;
    color         : #000000;
    font-size     : 13px;
    padding       : 0;
  }}

  strong {{
    color         : #000000;
    font-weight   : 700;
  }}

  @keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}
</style>
</head>
<body>
  <div class='card'>{content_html}</div>
</body>
</html>"""

    @staticmethod
    def build_empty() -> str:
        return HtmlBuilder.build_page("""
            <h2>👋 Welcome to AI Assistant</h2>
            <p>Type your question and click <strong>Ask AI</strong>.</p>
            <p>Or use <strong>🔊 System Audio</strong> to capture Teams/Zoom/Meet.</p>
            <p>Or use <strong>🎤 Mic</strong> to speak directly.</p>
        """)

    @staticmethod
    def build_loading() -> str:
        return HtmlBuilder.build_page("""
            <h2>⏳ Thinking...</h2>
            <p>Please wait while AI generates your answer.</p>
        """)

    @staticmethod
    def build_error(message: str) -> str:
        return HtmlBuilder.build_page(f"""
            <h2 style='color:#cc0000'>⚠️ Error</h2>
            <p style='color:#cc0000'>{message}</p>
        """)

    # ✅ THIS WAS MISSING — now added
    @staticmethod
    def build_language_error(message: str) -> str:
        return HtmlBuilder.build_page(f"""
            <h2 style='color:#cc6600'>🌐 English Only</h2>
            <p>{message}</p>
            <br>
            <p>This assistant only accepts <strong>English (en-US)</strong>.</p>
            <ul>
                <li>✅ Accepted: <code>What is C#?</code></li>
                <li>❌ Rejected: Non-English text</li>
            </ul>
        """)