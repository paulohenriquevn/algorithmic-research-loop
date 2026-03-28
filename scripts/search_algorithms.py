#!/usr/bin/env python3
"""
Algorithm search utility for the Algorithmic Research Loop plugin.

Searches GitHub for algorithm implementations and ArXiv for algorithm papers.
No API key required. Uses only Python stdlib.

Usage:
    python3 search_algorithms.py github --query "quickselect" --language python
    python3 search_algorithms.py github --query "sorting algorithm" --max-results 10
    python3 search_algorithms.py arxiv --query "selection algorithm average case"
    python3 search_algorithms.py arxiv --query "graph coloring" --category cs.DS --max-results 5
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
ARXIV_API_URL = "http://export.arxiv.org/api/query"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2.0
REQUEST_TIMEOUT_SECONDS = 30
USER_AGENT = "AlgorithmicResearchLoop/1.0"


# ---------------------------------------------------------------------------
# GitHub search
# ---------------------------------------------------------------------------

def search_github(query: str, language: str | None = None,
                  max_results: int = 20, sort: str = "stars") -> list[dict]:
    """Search GitHub repositories for algorithm implementations.

    Uses the public GitHub search API (no auth required, rate-limited to
    ~10 requests/minute for unauthenticated clients).
    """
    search_query = query
    if language:
        search_query = f"{query} language:{language}"

    params = urllib.parse.urlencode({
        "q": search_query,
        "sort": sort,
        "order": "desc",
        "per_page": min(max_results, 100),
    })

    url = f"{GITHUB_SEARCH_URL}?{params}"

    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/vnd.github.v3+json",
            })
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                data = json.loads(response.read().decode("utf-8"))
            return _parse_github_response(data)

        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))
                continue
            raise
        except urllib.error.URLError as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            raise

    return []


def _parse_github_response(data: dict) -> list[dict]:
    """Parse GitHub search API response into structured results."""
    results = []
    for item in data.get("items", []):
        results.append({
            "name": item.get("full_name", ""),
            "description": item.get("description") or "",
            "source_url": item.get("html_url", ""),
            "language": item.get("language") or "unknown",
            "stars": item.get("stargazers_count", 0),
            "forks": item.get("forks_count", 0),
            "updated": (item.get("updated_at") or "")[:10],
            "license": (item.get("license") or {}).get("spdx_id"),
            "topics": item.get("topics", []),
            "source": "github",
        })
    return results


# ---------------------------------------------------------------------------
# ArXiv search
# ---------------------------------------------------------------------------

def search_arxiv(query: str, max_results: int = 20, sort_by: str = "relevance",
                 category: str | None = None) -> list[dict]:
    """Search ArXiv for algorithm papers.

    Uses the ArXiv public API (Atom XML). Rate limit: ~3 requests/second.
    """
    search_query = f"all:{query}"
    if category:
        search_query = f"cat:{category} AND {search_query}"

    params = urllib.parse.urlencode({
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": "descending",
    })

    url = f"{ARXIV_API_URL}?{params}"

    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT,
            })
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                xml_data = response.read().decode("utf-8")
            return _parse_arxiv_response(xml_data)

        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))
                continue
            raise
        except urllib.error.URLError as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            raise

    return []


def _parse_arxiv_response(xml_data: str) -> list[dict]:
    """Parse ArXiv Atom XML response into structured paper objects."""
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    root = ET.fromstring(xml_data)
    papers = []

    for entry in root.findall("atom:entry", ns):
        title_el = entry.find("atom:title", ns)
        summary_el = entry.find("atom:summary", ns)
        published_el = entry.find("atom:published", ns)

        if title_el is None or summary_el is None:
            continue

        title = " ".join(title_el.text.strip().split())
        abstract = " ".join(summary_el.text.strip().split())

        # ArXiv ID from entry id URL
        id_el = entry.find("atom:id", ns)
        arxiv_url = id_el.text.strip() if id_el is not None else ""
        arxiv_id = arxiv_url.split("/abs/")[-1] if "/abs/" in arxiv_url else ""
        arxiv_id_base = arxiv_id.rsplit("v", 1)[0] if "v" in arxiv_id else arxiv_id

        # Authors
        authors = []
        for author_el in entry.findall("atom:author", ns):
            name_el = author_el.find("atom:name", ns)
            if name_el is not None:
                authors.append(name_el.text.strip())

        # Categories
        categories = []
        for cat_el in entry.findall("atom:category", ns):
            term = cat_el.get("term", "")
            if term:
                categories.append(term)

        # PDF link
        pdf_url = ""
        for link_el in entry.findall("atom:link", ns):
            if link_el.get("title") == "pdf":
                pdf_url = link_el.get("href", "")
                break

        published = published_el.text.strip()[:10] if published_el is not None else ""

        papers.append({
            "id": arxiv_id_base,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "published": published,
            "year": int(published[:4]) if published else None,
            "categories": categories,
            "pdf_url": pdf_url,
            "web_url": arxiv_url,
            "source": "arxiv",
        })

    return papers


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search for algorithm implementations (GitHub) and papers (ArXiv)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # GitHub sub-command
    gh_parser = subparsers.add_parser("github", help="Search GitHub repositories")
    gh_parser.add_argument("--query", required=True, help="Search query")
    gh_parser.add_argument("--language", default=None,
                           help="Filter by programming language (e.g., python, rust, go)")
    gh_parser.add_argument("--max-results", type=int, default=20,
                           help="Maximum results to return (default: 20, max: 100)")
    gh_parser.add_argument("--sort", default="stars",
                           choices=["stars", "forks", "updated"],
                           help="Sort order (default: stars)")

    # ArXiv sub-command
    ax_parser = subparsers.add_parser("arxiv", help="Search ArXiv papers")
    ax_parser.add_argument("--query", required=True, help="Search query")
    ax_parser.add_argument("--max-results", type=int, default=20,
                           help="Maximum results to return (default: 20)")
    ax_parser.add_argument("--category", default=None,
                           help="ArXiv category filter (e.g., cs.DS, cs.CC)")
    ax_parser.add_argument("--sort-by", default="relevance",
                           choices=["relevance", "lastUpdatedDate", "submittedDate"],
                           help="Sort order (default: relevance)")

    args = parser.parse_args()

    try:
        if args.command == "github":
            results = search_github(
                query=args.query,
                language=args.language,
                max_results=args.max_results,
                sort=args.sort,
            )
        elif args.command == "arxiv":
            results = search_arxiv(
                query=args.query,
                max_results=args.max_results,
                sort_by=args.sort_by,
                category=args.category,
            )
        else:
            parser.print_help()
            sys.exit(1)
            return

        json.dump(results, sys.stdout, indent=2, ensure_ascii=False)
        print()

    except urllib.error.HTTPError as e:
        json.dump({"error": f"HTTP error: {e.code} {e.reason}", "results": []},
                  sys.stdout, indent=2)
        print()
        sys.exit(1)

    except urllib.error.URLError as e:
        json.dump({"error": f"Network error: {e.reason}", "results": []},
                  sys.stdout, indent=2)
        print()
        sys.exit(1)

    except ET.ParseError as e:
        json.dump({"error": f"Failed to parse ArXiv response: {e}", "results": []},
                  sys.stdout, indent=2)
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
