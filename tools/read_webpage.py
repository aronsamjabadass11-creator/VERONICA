"""
read_webpage.py - Reads webpages and PDFs for VERONICA.
"""

import io
import re

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from tools.base import BaseTool


class ReadWebpageTool(BaseTool):
    name = "read_webpage"

    description = (
        "Reads useful content from a webpage or PDF. "
        "Can extract text from official datasheets and documents."
    )

    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The full URL of the webpage or PDF."
            }
        },
        "required": ["url"]
    }

    def execute(self, **kwargs) -> str:
        url = kwargs.get("url", "").strip()

        if not url:
            return "Error: No URL was provided."

        if not url.startswith(("http://", "https://")):
            return "Error: URL must start with http:// or https://"

        try:
            response = requests.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 Chrome/154.0 Safari/537.36"
                    )
                },
                timeout=20,
                allow_redirects=True,
            )

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type", ""
            ).lower()

            # =====================================================
            # PDF HANDLING
            # =====================================================

            if (
                "application/pdf" in content_type
                or url.lower().split("?")[0].endswith(".pdf")
            ):
                return self._read_pdf(response.content, url)

            # =====================================================
            # WEBPAGE HANDLING
            # =====================================================

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            for element in soup([
                "script",
                "style",
                "noscript",
                "nav",
                "footer",
                "header",
                "aside",
                "form",
                "svg"
            ]):
                element.decompose()

            main = (
                soup.find("main")
                or soup.find("article")
                or soup.find("body")
            )

            if main is None:
                return "No readable webpage content was found."

            raw_text = main.get_text(
                "\n",
                strip=True
            )

            text = self._clean_text(raw_text)

            if not text:
                return "No readable text was found."

            # Keep the LLM request reasonably small.
            MAX_CHARS = 12000

            if len(text) > MAX_CHARS:
                text = text[:MAX_CHARS]

                last_space = text.rfind(" ")

                if last_space > 8000:
                    text = text[:last_space]

                text += (
                    "\n\n[VERONICA: webpage content truncated]"
                )

            return (
                f"SOURCE URL:\n{response.url}\n\n"
                f"WEBPAGE CONTENT:\n{text}"
            )

        except requests.RequestException as e:
            return f"Unable to read webpage: {e}"

        except Exception as e:
            return f"Webpage reading failed: {e}"

    # =============================================================
    # PDF READER
    # =============================================================

    def _read_pdf(self, pdf_bytes, url):

        try:
            reader = PdfReader(
                io.BytesIO(pdf_bytes)
            )

            page_text = []

            # Read enough pages to keep the AI request manageable.
            max_pages = min(
                len(reader.pages),
                12
            )

            for page_number in range(max_pages):

                page = reader.pages[page_number]

                try:
                    text = page.extract_text() or ""
                except Exception:
                    text = ""

                text = self._clean_text(text)

                if text:
                    page_text.append(
                        f"[PAGE {page_number + 1}]\n{text}"
                    )

            if not page_text:
                return (
                    "PDF was opened successfully, but no selectable "
                    "text could be extracted."
                )

            text = "\n\n".join(page_text)

            # Final protection against huge LLM requests.
            MAX_CHARS = 14000

            if len(text) > MAX_CHARS:

                text = text[:MAX_CHARS]

                last_space = text.rfind(" ")

                if last_space > 9000:
                    text = text[:last_space]

                text += (
                    "\n\n[VERONICA: PDF content truncated]"
                )

            return (
                f"SOURCE PDF:\n{url}\n\n"
                f"PDF CONTENT:\n{text}"
            )

        except Exception as e:
            return f"PDF reading failed: {e}"

    # =============================================================
    # TEXT CLEANER
    # =============================================================

    def _clean_text(self, text):

        lines = []

        for line in text.splitlines():

            line = re.sub(
                r"\s+",
                " ",
                line
            ).strip()

            if line:
                lines.append(line)

        # Remove immediately repeated lines.
        cleaned = []

        previous = None

        for line in lines:

            if line != previous:
                cleaned.append(line)

            previous = line

        return "\n".join(cleaned)