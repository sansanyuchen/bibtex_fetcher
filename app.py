from flask import Flask, jsonify, render_template, request

from fetcher import search_bibtex as run_search

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_bibtex_api():
    data = request.json
    title = data.get('title')
    source = data.get('source', 'both') # 'arxiv', 'scholar', or 'both'
    
    if not title:
        return jsonify({"error": "Title is required"}), 400

    search_results = run_search(title, source=source)
    results = {}

    if 'arxiv' in search_results:
        arxiv = search_results['arxiv']
        results['arxiv'] = arxiv['bibtex'] if arxiv['bibtex'] else "Not found"
        results['arxiv_meta'] = {
            "matched_title": arxiv.get("matched_title"),
            "query_used": arxiv.get("query_used"),
            "score": arxiv.get("score"),
            "error": arxiv.get("error"),
        }

    if 'scholar' in search_results:
        scholar = search_results['scholar']
        results['scholar'] = scholar['bibtex'] if scholar['bibtex'] else "Not found"
        results['scholar_meta'] = {
            "matched_title": scholar.get("matched_title"),
            "query_used": scholar.get("query_used"),
            "score": scholar.get("score"),
            "error": scholar.get("error"),
        }

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
