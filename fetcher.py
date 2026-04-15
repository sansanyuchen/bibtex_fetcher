import argparse
import sys
import re
import requests
import arxiv
from scholarly import scholarly

def fetch_from_arxiv(title):
    """
    Search arXiv for the title and attempt to retrieve its BibTeX.
    """
    print(f"Searching arXiv for: '{title}'...")
    try:
        # Create an arXiv client
        client = arxiv.Client()
        
        # Search for the exact title
        search = arxiv.Search(
            query=f'ti:"{title}"',
            max_results=5,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = list(client.results(search))
        
        if not results:
            print("  No results found on arXiv.")
            return None
            
        # Try to find a good match string-wise, or just take the first one
        best_match = None
        for res in results:
            # Simple case-insensitive match check
            if title.lower() in res.title.lower() or res.title.lower() in title.lower():
                best_match = res
                break
                
        if not best_match:
            # Fallback to first result if no exact substring match but API returned it
            best_match = results[0]
            
        print(f"  Found matching paper on arXiv: '{best_match.title}'")
        
        # Extract the arxiv ID
        # entry_id is something like 'http://arxiv.org/abs/1706.03762v5'
        # We need the '1706.03762' part for the bibtex endpoint
        
        match = re.search(r'arxiv\.org/abs/([^v]+)(?:v\d+)?', best_match.entry_id)
        if not match:
            print(f"  Could not extract arXiv ID from {best_match.entry_id}")
            return None
            
        arxiv_id = match.group(1)
        
        # Now fetch the bibtex
        # The arXiv bibtex endpoint is https://arxiv.org/bibtex/<id>
        # e.g., https://arxiv.org/bibtex/1706.03762
        bib_url = f"https://arxiv.org/bibtex/{arxiv_id}"
        
        response = requests.get(bib_url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"  Failed to fetch BibTeX from {bib_url}. Status code: {response.status_code}")
            return None

    except Exception as e:
        print(f"  Error searching arXiv: {e}")
        return None

def fetch_from_scholar(title):
    """
    Search Google Scholar for the title and return its BibTeX.
    Note: scholarly can be rate-limited or blocked by Google Scholar.
    """
    print(f"Searching Google Scholar for: '{title}'...")
    try:
        search_query = scholarly.search_pubs(title)
        
        # Get the first result
        try:
            first_result = next(search_query)
        except StopIteration:
            print("  No results found on Google Scholar.")
            return None
            
        print(f"  Found matching paper on Scholar: '{first_result.get('bib', {}).get('title', 'Unknown Title')}'")
        
        # Fetch the bibtex citation
        bibtex = scholarly.bibtex(first_result)
        return bibtex
        
    except Exception as e:
        print(f"  Error searching Google Scholar: {e}")
        print("  (Note: Google Scholar often blocks automated requests. You might be rate-limited).")
        return None

def main():
    parser = argparse.ArgumentParser(description="Fetch BibTeX citations for a paper title from arXiv and Google Scholar.")
    parser.add_argument("title", type=str, help="The title of the paper to look up.")
    args = parser.parse_args()

    title = args.title

    print("=" * 60)
    print(f"Looking up BibTeX for: '{title}'")
    print("=" * 60)

    # 1. Fetch from arXiv
    arxiv_bibtex = fetch_from_arxiv(title)
    if arxiv_bibtex:
        print("\n--- arXiv BibTeX ---")
        print(arxiv_bibtex.strip())
    else:
        print("\n--- arXiv BibTeX ---")
        print("Not available.")

    print("\n" + "=" * 60 + "\n")

    # 2. Fetch from Google Scholar
    scholar_bibtex = fetch_from_scholar(title)
    if scholar_bibtex:
        print("--- Google Scholar BibTeX ---")
        print(scholar_bibtex.strip())
    else:
        print("--- Google Scholar BibTeX ---")
        print("Not available.")
        
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
