from flask import Flask, request, jsonify, render_template
from fetcher import fetch_from_arxiv, fetch_from_scholar

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_bibtex():
    data = request.json
    title = data.get('title')
    source = data.get('source', 'both') # 'arxiv', 'scholar', or 'both'
    
    if not title:
        return jsonify({"error": "Title is required"}), 400

    results = {}

    if source in ['both', 'arxiv']:
        arxiv_bibtex = fetch_from_arxiv(title)
        results['arxiv'] = arxiv_bibtex if arxiv_bibtex else "Not found"

    if source in ['both', 'scholar']:
        scholar_bibtex = fetch_from_scholar(title)
        results['scholar'] = scholar_bibtex if scholar_bibtex else "Not found"

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
