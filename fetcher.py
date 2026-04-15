import argparse
import difflib
import re
from typing import Dict, Iterable, List, Optional

import requests
from bs4 import BeautifulSoup
from scholarly import scholarly

ARXIV_SEARCH_URL = "https://arxiv.org/search/"
ARXIV_BIBTEX_URL = "https://arxiv.org/bibtex/{arxiv_id}"
REQUEST_TIMEOUT = 45
ARXIV_RESULT_LIMITS = (25, 100)
ARXIV_MATCH_THRESHOLD = 0.95
ARXIV_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "close",
}
TOKEN_ABBREVIATIONS = {
    "attn": "attention",
    "xformer": "transformer",
    "xformers": "transformers",
}
LOW_SIGNAL_TOKENS = {
    "paper",
    "papers",
    "study",
    "review",
    "survey",
    "model",
    "models",
    "method",
    "methods",
    "approach",
    "approaches",
    "transformer",
    "transformers",
    "llm",
    "llms",
}


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def tokenize_title(title: str) -> List[str]:
    normalized = normalize_title(title)
    return [token for token in normalized.split() if token]


def unique_titles(titles: Iterable[str]) -> List[str]:
    seen = set()
    ordered = []
    for title in titles:
        cleaned = " ".join(title.split())
        if not cleaned:
            continue
        marker = cleaned.lower()
        if marker in seen:
            continue
        seen.add(marker)
        ordered.append(cleaned)
    return ordered


def expand_abbreviations(title: str) -> str:
    return " ".join(TOKEN_ABBREVIATIONS.get(token.lower(), token) for token in title.split())


def generate_title_variants(title: str) -> List[str]:
    tokens = title.split()
    variants = [title]

    expanded = expand_abbreviations(title)
    if expanded != title:
        variants.append(expanded)

    if len(tokens) > 4:
        for index, token in enumerate(tokens):
            if token.lower().strip(",.:;!?()[]{}") in LOW_SIGNAL_TOKENS:
                reduced = " ".join(tokens[:index] + tokens[index + 1 :])
                variants.append(reduced)

    return unique_titles(variants)


def score_title_match(query_title: str, candidate_title: str) -> float:
    normalized_query = normalize_title(query_title)
    normalized_candidate = normalize_title(candidate_title)

    if normalized_query == normalized_candidate:
        return 1.0

    query_tokens = set(tokenize_title(query_title))
    candidate_tokens = set(tokenize_title(candidate_title))

    if not query_tokens or not candidate_tokens:
        return 0.0

    overlap = len(query_tokens & candidate_tokens)
    precision = overlap / len(query_tokens)
    recall = overlap / len(candidate_tokens)
    ratio = difflib.SequenceMatcher(
        None, normalized_query, normalized_candidate
    ).ratio()

    return max(ratio, (precision * 0.7) + (recall * 0.3))


def empty_result(source: str, error: Optional[str] = None) -> Dict[str, Optional[str]]:
    return {
        "source": source,
        "bibtex": None,
        "matched_title": None,
        "query_used": None,
        "score": None,
        "error": error,
    }


def fetch_arxiv_search_page(query_title: str, size: int) -> str:
    response = requests.get(
        ARXIV_SEARCH_URL,
        params={
            "query": query_title,
            "searchtype": "title",
            "size": size,
        },
        headers=ARXIV_REQUEST_HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.text


def fetch_from_arxiv_details(
    title: str, candidate_titles: Optional[Iterable[str]] = None
) -> Dict[str, Optional[str]]:
    """
    Search arXiv for the title and attempt to retrieve its BibTeX.
    """
    print(f"Searching arXiv for: '{title}'...")
    title_variants = unique_titles(candidate_titles or generate_title_variants(title))

    best_candidate = None
    best_variant = None

    try:
        for size in ARXIV_RESULT_LIMITS:
            for variant in title_variants:
                html = fetch_arxiv_search_page(variant, size=size)
                soup = BeautifulSoup(html, "html.parser")
                results = soup.select("li.arxiv-result")

                for result in results:
                    title_el = result.select_one("p.title")
                    link_el = result.select_one("p.list-title a")
                    if not title_el or not link_el:
                        continue

                    candidate_title = title_el.get_text(" ", strip=True)
                    candidate_link = link_el.get("href", "")
                    candidate_score = max(
                        score_title_match(title, candidate_title),
                        score_title_match(variant, candidate_title),
                    )

                    if not best_candidate or candidate_score > best_candidate["score"]:
                        best_candidate = {
                            "title": candidate_title,
                            "link": candidate_link,
                            "score": candidate_score,
                        }
                        best_variant = variant

                    if candidate_score >= 0.98:
                        break

                if best_candidate and best_candidate["score"] >= 0.98:
                    break

            if best_candidate and best_candidate["score"] >= ARXIV_MATCH_THRESHOLD:
                break

        if not best_candidate:
            print("  No results found on arXiv.")
            return empty_result("arxiv", error="No results found on arXiv.")

        if best_candidate["score"] < ARXIV_MATCH_THRESHOLD:
            print(
                "  Best arXiv result was too far from the requested title: "
                f"'{best_candidate['title']}'"
            )
            return empty_result(
                "arxiv",
                error="arXiv returned only weak title matches for this query.",
            )

        print(
            "  Found matching paper on arXiv: "
            f"'{best_candidate['title']}' (score={best_candidate['score']:.2f})"
        )

        match = re.search(r"arxiv\.org/abs/([^?#]+)", best_candidate["link"])
        if not match:
            print(f"  Could not extract arXiv ID from {best_candidate['link']}")
            return empty_result("arxiv", error="Could not extract arXiv identifier.")

        arxiv_id = re.sub(r"v\d+$", "", match.group(1))
        bibtex_response = requests.get(
            ARXIV_BIBTEX_URL.format(arxiv_id=arxiv_id),
            headers=ARXIV_REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        bibtex_response.raise_for_status()

        return {
            "source": "arxiv",
            "bibtex": bibtex_response.text,
            "matched_title": best_candidate["title"],
            "query_used": best_variant,
            "score": round(best_candidate["score"], 3),
            "error": None,
        }

    except requests.RequestException as e:
        print(f"  Error searching arXiv: {e}")
        return empty_result("arxiv", error=str(e))
    except Exception as e:
        print(f"  Error parsing arXiv response: {e}")
        return empty_result("arxiv", error=str(e))


def fetch_from_scholar_details(title: str) -> Dict[str, Optional[str]]:
    """
    Search Google Scholar for the title and return its BibTeX.
    Note: scholarly can be rate-limited or blocked by Google Scholar.
    """
    print(f"Searching Google Scholar for: '{title}'...")
    try:
        search_query = scholarly.search_pubs(title)

        try:
            first_result = next(search_query)
        except StopIteration:
            print("  No results found on Google Scholar.")
            return empty_result("scholar", error="No results found on Google Scholar.")

        matched_title = first_result.get("bib", {}).get("title", "Unknown Title")
        score = round(score_title_match(title, matched_title), 3)

        print(
            "  Found matching paper on Scholar: "
            f"'{matched_title}' (score={score:.2f})"
        )

        bibtex = scholarly.bibtex(first_result)
        return {
            "source": "scholar",
            "bibtex": bibtex,
            "matched_title": matched_title,
            "query_used": title,
            "score": score,
            "error": None,
        }

    except Exception as e:
        print(f"  Error searching Google Scholar: {e}")
        print(
            "  (Note: Google Scholar often blocks automated requests. "
            "You might be rate-limited)."
        )
        return empty_result("scholar", error=str(e))


def fetch_from_arxiv(title: str, candidate_titles: Optional[Iterable[str]] = None):
    return fetch_from_arxiv_details(title, candidate_titles=candidate_titles)["bibtex"]


def fetch_from_scholar(title: str):
    return fetch_from_scholar_details(title)["bibtex"]


def search_bibtex(title: str, source: str = "both") -> Dict[str, Dict[str, Optional[str]]]:
    results = {}
    scholar_details = None

    if source in {"both", "scholar"}:
        scholar_details = fetch_from_scholar_details(title)
        results["scholar"] = scholar_details

    if source in {"both", "arxiv"}:
        title_variants = generate_title_variants(title)
        if scholar_details and scholar_details.get("matched_title"):
            title_variants = unique_titles(
                [scholar_details["matched_title"], *title_variants]
            )
        arxiv_details = fetch_from_arxiv_details(title, candidate_titles=title_variants)
        results["arxiv"] = arxiv_details

    return results


def print_source_result(label: str, details: Dict[str, Optional[str]]) -> None:
    print(f"--- {label} BibTeX ---")
    if details.get("bibtex"):
        if details.get("matched_title"):
            print(f"Matched title: {details['matched_title']}")
        if details.get("query_used") and details["query_used"] != details.get("matched_title"):
            print(f"Query used: {details['query_used']}")
        if details.get("score") is not None:
            print(f"Match score: {details['score']}")
        print(details["bibtex"].strip())
    else:
        print("Not available.")
        if details.get("error"):
            print(f"Reason: {details['error']}")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch BibTeX citations for a paper title from arXiv and Google Scholar."
    )
    parser.add_argument("title", type=str, help="The title of the paper to look up.")
    parser.add_argument(
        "--source",
        choices=["arxiv", "scholar", "both"],
        default="both",
        help="Choose which source to query.",
    )
    args = parser.parse_args()

    title = args.title

    print("=" * 60)
    print(f"Looking up BibTeX for: '{title}'")
    print("=" * 60)

    results = search_bibtex(title, source=args.source)

    if "scholar" in results:
        print_source_result("Google Scholar", results["scholar"])
        if "arxiv" in results:
            print("\n" + "=" * 60 + "\n")

    if "arxiv" in results:
        print_source_result("arXiv", results["arxiv"])

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
