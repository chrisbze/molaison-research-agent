#!/usr/bin/env python3
"""
Simple web interface for Molaison Crawler Agent
"""

from flask import Flask, render_template_string, request, jsonify
import sys
from pathlib import Path
import subprocess
import threading
import time

sys.path.append(str(Path(__file__).parent))

app = Flask(__name__)

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
            <strong>Available Commands:</strong>
            <ul>
                <li>Web scraping and data extraction</li>
                <li>Automated research tasks</li>
                <li>URL content analysis</li>
                <li>Data export capabilities</li>
            </ul>
        </div>
        
        <h3>Quick Test</h3>
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
    return jsonify({
        'status': 'running',
        'agent': 'Research & Crawl Agent',
        'port': 8503,
        'capabilities': [
            'Web scraping',
            'Data extraction', 
            'Research automation',
            'Content analysis'
        ]
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8503))
    print(f"Starting Molaison Research & Crawl Agent on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)