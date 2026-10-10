"""
web_search.py - Web search tool for VERONICA.

Uses the DDGS search library instead of scraping DuckDuckGo HTML.
"""

from tools.base import BaseTool


class WebSearchTool(BaseTool):
    name = "web_search"

    description = (
        "Searches the web for information. Use this when the user explicitly "
        "asks VERONICA to search the internet or find current information."
    )

    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query."
            }
        },
        "required": ["query"]
    }

    def execute(self, **kwargs) -> str:
        query = kwargs.get("query", "").strip()

        if not query:
            return "Error: No search query was provided."

        try:
            from ddgs import DDGS

            results = []

            with DDGS() as ddgs:
                search_results = ddgs.text(
                    query,
                    max_results=5
                )

                for item in search_results:
                    title = item.get("title", "").strip()
                    url = item.get("href", "").strip()
                    body = item.get("body", "").strip()

                    if not title and not url:
                        continue

                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": body
                    })

            if not results:
                return f"No search results found for: {query}"

            output = [
                f"Web search results for: {query}",
                ""
            ]

            for index, result in enumerate(results, start=1):
                output.append(f"RESULT {index}")
                output.append(f"Title: {result['title']}")
                output.append(f"URL: {result['url']}")

                if result["snippet"]:
                    output.append(
                        f"Summary: {result['snippet']}"
                    )

                output.append("")

            return "\n".join(output)

        except ImportError:
            return (
                "Web search error: the 'ddgs' package is not installed. "
                "Run: pip install ddgs"
            )

        except Exception as e:
            return f"Web search failed: {e}"