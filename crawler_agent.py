#!/usr/bin/env python3
"""
Enhanced Molaison Research Agent with Academic Search Capabilities
"""

from flask import Flask, render_template_string, request, jsonify
import sys
from pathlib import Path
import subprocess
import threading
import time
import os

sys.path.append(str(Path(__file__).parent))

# Import academic research module
try:
    from academic_research import search_academic, parse_citation_text
    ACADEMIC_AVAILABLE = True
except ImportError:
    ACADEMIC_AVAILABLE = False
    print("Academic research modules not available")

app = Flask(__name__)

def format_academic_results(results):
    """Format academic search results for display"""
    output = []
    output.append(f"🔍 Academic Search Results for: '{results['query']}'")
    output.append(f"📅 Search performed: {results['timestamp']}")
    output.append("")
    
    total_results = 0
    for source, source_results in results['sources'].items():
        if isinstance(source_results, list) and source_results:
            total_results += len(source_results)
            output.append(f"📚 {source.upper()} Results ({len(source_results)}):")
            output.append("-" * 50)
            
            for i, paper in enumerate(source_results[:5], 1):  # Show first 5
                if 'error' in paper:
                    output.append(f"{i}. Error: {paper['error']}")
                    continue
                    
                title = paper.get('title', 'No title')
                authors = paper.get('authors', [])
                year = paper.get('year', 'Unknown year')
                journal = paper.get('journal', paper.get('venue', 'Unknown journal'))
                citations = paper.get('citation_count', 'N/A')
                url = paper.get('url', '')
                
                # Format authors (limit to first 3)
                author_str = ', '.join(authors[:3])
                if len(authors) > 3:
                    author_str += f" et al. ({len(authors)} total)"
                
                output.append(f"{i}. {title}")
                output.append(f"   Authors: {author_str}")
                output.append(f"   Journal: {journal} ({year})")
                output.append(f"   Citations: {citations}")
                if url:
                    output.append(f"   URL: {url}")
                
                # Show abstract preview
                abstract = paper.get('abstract', '')
                if abstract and abstract != 'No abstract available':
                    preview = abstract[:200] + "..." if len(abstract) > 200 else abstract
                    output.append(f"   Abstract: {preview}")
                
                output.append("")
            
            if len(source_results) > 5:
                output.append(f"   ... and {len(source_results) - 5} more results")
                output.append("")
    
    if total_results == 0:
        output.append("No results found. Try different keywords or sources.")
    else:
        output.append(f"📊 Total Results Found: {total_results}")
    
    return "\n".join(output)

def format_citation_result(parsed):
    """Format citation parsing results for display"""
    output = []
    output.append("📄 Citation Parsing Results")
    output.append("=" * 50)
    
    output.append(f"Original Citation:")
    output.append(f"'{parsed['original']}'")
    output.append("")
    
    output.append(f"Detected Format: {parsed['format']}")
    
    if 'error' in parsed:
        output.append(f"Error: {parsed['error']}")
        return "\n".join(output)
    
    if parsed['parsed']:
        output.append("")
        output.append("Extracted Information:")
        output.append("-" * 30)
        
        for field, value in parsed['parsed'].items():
            if value and value != 'Unknown' and value != '':
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value)
                output.append(f"{field.title()}: {value}")
    else:
        output.append("No structured information could be extracted.")
    
    return "\n".join(output)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Molaison Research & Crawl Agent</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        textarea { width: 100%; height: 150px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { background-color: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background-color: #2980b9; }
        .results { margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Molaison Research & Crawl Agent</h1>
        
        <div class="status success">
            <strong>Status:</strong> Research Agent is running on port 8503
        </div>
        
        <div class="status info">
            <strong>Research Capabilities:</strong>
            <ul>
                <li>📚 PubMed medical/life science search</li>
                <li>🎓 Google Scholar academic search</li>
                <li>🔗 DOI resolution and CrossRef lookup</li>
                <li>📄 Citation parsing (BibTeX, APA, MLA)</li>
                <li>🌐 General web scraping and analysis</li>
                <li>📊 Multi-source academic research</li>
            </ul>
        </div>
        
        <h3>🎓 Academic Search</h3>
        <form method="post" action="/search_academic">
            <label for="query">Research Query:</label><br>
            <input type="text" id="query" name="query" style="width: 100%; padding: 10px; margin: 5px 0;" placeholder="e.g., machine learning, COVID-19, climate change"><br>
            
            <div style="margin: 10px 0;">
                <label><input type="checkbox" name="sources" value="pubmed" checked> 📚 PubMed</label>&nbsp;&nbsp;
                <label><input type="checkbox" name="sources" value="scholar" checked> 🎓 Google Scholar</label>&nbsp;&nbsp;
                <label><input type="checkbox" name="sources" value="doi"> 🔗 DOI Resolution</label>
            </div>
            
            <label for="max_results">Max Results:</label>
            <input type="number" id="max_results" name="max_results" value="10" min="1" max="50" style="width: 100px; padding: 5px; margin: 5px;">
            <button type="submit">Search Academic Sources</button>
        </form>
        
        <h3>📄 Citation Parser</h3>
        <form method="post" action="/parse_citation">
            <label for="citation">Citation Text:</label><br>
            <textarea id="citation" name="citation" style="width: 100%; height: 80px; padding: 10px; margin: 5px 0;" placeholder="Paste citation here (BibTeX, APA, MLA, etc.)"></textarea><br>
            <button type="submit">Parse Citation</button>
        </form>
        
        <h3>🌐 URL Analysis</h3>
        <form method="post" action="/test">
            <label for="url">Enter URL to analyze:</label><br>
            <input type="url" id="url" name="url" style="width: 100%; padding: 10px; margin: 5px 0;" placeholder="https://example.com"><br>
            <button type="submit">Analyze URL</button>
        </form>
        
        <div class="results" id="results">
            {% if result %}
                <h4>Analysis Result:</h4>
                <pre>{{ result }}</pre>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(TEMPLATE)

@app.route('/search_academic', methods=['POST'])
def search_academic_endpoint():
    """Academic search endpoint"""
    if not ACADEMIC_AVAILABLE:
        return render_template_string(TEMPLATE, result="Academic search modules not available")
    
    query = request.form.get('query', '').strip()
    if not query:
        return render_template_string(TEMPLATE, result="Please enter a search query")
    
    # Get selected sources
    sources = request.form.getlist('sources')
    if not sources:
        sources = ['pubmed', 'scholar']
    
    max_results = int(request.form.get('max_results', 10))
    
    try:
        # Perform academic search
        results = search_academic(query, sources, max_results)
        
        # Format results for display
        formatted_results = format_academic_results(results)
        return render_template_string(TEMPLATE, result=formatted_results)
        
    except Exception as e:
        return render_template_string(TEMPLATE, result=f"Academic search error: {str(e)}")

@app.route('/parse_citation', methods=['POST'])
def parse_citation_endpoint():
    """Citation parsing endpoint"""
    if not ACADEMIC_AVAILABLE:
        return render_template_string(TEMPLATE, result="Citation parsing modules not available")
    
    citation_text = request.form.get('citation', '').strip()
    if not citation_text:
        return render_template_string(TEMPLATE, result="Please enter citation text")
    
    try:
        # Parse citation
        parsed = parse_citation_text(citation_text)
        
        # Format results
        formatted_result = format_citation_result(parsed)
        return render_template_string(TEMPLATE, result=formatted_result)
        
    except Exception as e:
        return render_template_string(TEMPLATE, result=f"Citation parsing error: {str(e)}")

@app.route('/test', methods=['POST'])
def test_crawler():
    url = request.form.get('url', '')
    if not url:
        return render_template_string(TEMPLATE, result="Please provide a valid URL")
    
    try:
        # Simple URL validation and basic info
        result = f"""URL Analysis for: {url}

This is a test of the Research & Crawl Agent.
The agent is running and ready to process requests.

Next steps:
- Implement actual crawling logic
- Add data extraction capabilities  
- Configure output formats
- Set up scheduling

Status: Agent is operational and ready for configuration."""
        
        return render_template_string(TEMPLATE, result=result)
    except Exception as e:
        return render_template_string(TEMPLATE, result=f"Error: {str(e)}")

@app.route('/status')
def status():
    capabilities = [
        'Web scraping and URL analysis',
        'General data extraction'
    ]
    
    if ACADEMIC_AVAILABLE:
        capabilities.extend([
            'PubMed medical/life science search',
            'Google Scholar academic search', 
            'DOI resolution and CrossRef lookup',
            'Citation parsing (BibTeX, APA, MLA)',
            'Multi-source academic research'
        ])
    
    return jsonify({
        'status': 'running',
        'agent': 'Enhanced Academic Research Agent',
        'port': int(os.environ.get('PORT', 8503)),
        'academic_features_available': ACADEMIC_AVAILABLE,
        'capabilities': capabilities,
        'endpoints': [
            '/search_academic - Academic research across multiple sources',
            '/parse_citation - Parse citation text',
            '/test - General URL analysis',
            '/status - Agent status'
        ]
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8503))
    print(f"Starting Molaison Research & Crawl Agent on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)