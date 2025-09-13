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

# Import marketing intelligence module
try:
    from marketing_intelligence import analyze_company_marketing, analyze_industry_trends, create_marketing_infographic
    MARKETING_AVAILABLE = True
except ImportError:
    MARKETING_AVAILABLE = False
    print("Marketing intelligence modules not available")

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
            <strong>Research & Marketing Intelligence:</strong>
            <ul>
                <li>📚 PubMed medical/life science search</li>
                <li>🎓 Google Scholar academic search</li>
                <li>🔗 DOI resolution and CrossRef lookup</li>
                <li>📄 Citation parsing (BibTeX, APA, MLA)</li>
                <li>🏢 Company research & intelligence</li>
                <li>📈 Industry trend analysis</li>
                <li>📊 Marketing infographics & visualizations</li>
                <li>🌐 General web scraping and analysis</li>
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
        
        <h3>🏢 Company Intelligence</h3>
        <form method="post" action="/analyze_company">
            <label for="company">Company Name:</label><br>
            <input type="text" id="company" name="company" style="width: 100%; padding: 10px; margin: 5px 0;" placeholder="e.g., Apple, Google, Tesla"><br>
            
            <label for="focus_areas">Focus Areas (comma-separated):</label><br>
            <input type="text" id="focus_areas" name="focus_areas" value="innovation,market strategy,customer experience" style="width: 100%; padding: 10px; margin: 5px 0;"><br>
            
            <div style="margin: 10px 0;">
                <label><input type="checkbox" name="generate_infographic" checked> 📊 Generate Infographic</label>
            </div>
            
            <button type="submit">Analyze Company</button>
        </form>
        
        <h3>📈 Industry Trends</h3>
        <form method="post" action="/analyze_trends">
            <label for="industry">Industry:</label><br>
            <input type="text" id="industry" name="industry" style="width: 70%; padding: 10px; margin: 5px 0;" placeholder="e.g., healthcare, fintech, AI"><br>
            
            <label for="timeframe">Timeframe:</label><br>
            <select name="timeframe" style="width: 30%; padding: 10px; margin: 5px 0;">
                <option value="2023-2024" selected>2023-2024</option>
                <option value="2022-2023">2022-2023</option>
                <option value="2021-2022">2021-2022</option>
                <option value="last 5 years">Last 5 Years</option>
            </select><br>
            
            <div style="margin: 10px 0;">
                <label><input type="checkbox" name="create_visualization" checked> 📊 Create Trend Visualization</label>
            </div>
            
            <button type="submit">Analyze Industry Trends</button>
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

@app.route('/analyze_company', methods=['POST'])
def analyze_company_endpoint():
    """Company intelligence analysis endpoint"""
    if not MARKETING_AVAILABLE:
        return render_template_string(TEMPLATE, result="Marketing intelligence modules not available")
    
    company = request.form.get('company', '').strip()
    if not company:
        return render_template_string(TEMPLATE, result="Please enter a company name")
    
    # Parse focus areas
    focus_areas_str = request.form.get('focus_areas', 'innovation,market strategy,customer experience')
    focus_areas = [area.strip() for area in focus_areas_str.split(',')]
    
    generate_infographic = 'generate_infographic' in request.form
    
    try:
        # Perform company analysis
        results = analyze_company_marketing(company, focus_areas)
        
        # Generate infographic if requested
        if generate_infographic and 'error' not in results:
            infographic_data = create_marketing_infographic(results, "summary")
            results['infographic'] = infographic_data
        
        # Format results for display
        formatted_results = format_company_results(results, generate_infographic)
        return render_template_string(TEMPLATE, result=formatted_results)
        
    except Exception as e:
        return render_template_string(TEMPLATE, result=f"Company analysis error: {str(e)}")

@app.route('/analyze_trends', methods=['POST'])
def analyze_trends_endpoint():
    """Industry trends analysis endpoint"""
    if not MARKETING_AVAILABLE:
        return render_template_string(TEMPLATE, result="Marketing intelligence modules not available")
    
    industry = request.form.get('industry', '').strip()
    if not industry:
        return render_template_string(TEMPLATE, result="Please enter an industry")
    
    timeframe = request.form.get('timeframe', '2023-2024')
    create_visualization = 'create_visualization' in request.form
    
    try:
        # Perform trend analysis
        results = analyze_industry_trends(industry, timeframe)
        
        # Generate visualization if requested
        if create_visualization and 'error' not in results:
            viz_data = create_marketing_infographic(results, "trends")
            results['visualization'] = viz_data
        
        # Format results for display
        formatted_results = format_trends_results(results, create_visualization)
        return render_template_string(TEMPLATE, result=formatted_results)
        
    except Exception as e:
        return render_template_string(TEMPLATE, result=f"Trends analysis error: {str(e)}")

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
    
    if MARKETING_AVAILABLE:
        capabilities.extend([
            'Company intelligence analysis',
            'Industry trend analysis',
            'Marketing infographic generation',
            'Data visualization for marketing',
            'Consumer-friendly report generation'
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

def format_company_results(results: Dict, has_infographic: bool = False) -> str:
    """Format company intelligence results for display"""
    output = []
    
    if 'error' in results:
        return f"Company Analysis Error: {results['error']}"
    
    company = results.get('company', 'Unknown Company')
    output.append(f"🏢 Company Intelligence Report: {company}")
    output.append("=" * 60)
    output.append(f"📅 Analysis Date: {results.get('timestamp', '')}")
    output.append("")
    
    # Research papers summary
    if 'research_papers' in results:
        output.append("📚 Research Papers by Focus Area:")
        output.append("-" * 40)
        
        total_papers = 0
        for area, sources in results['research_papers'].items():
            area_papers = 0
            for source_name, papers in sources.items():
                if isinstance(papers, list):
                    area_papers += len([p for p in papers if 'error' not in p])
            
            total_papers += area_papers
            output.append(f"• {area.title()}: {area_papers} papers found")
            
            # Show top papers for this area
            if area_papers > 0:
                for source_name, papers in sources.items():
                    if isinstance(papers, list) and papers:
                        top_paper = papers[0]
                        if 'error' not in top_paper:
                            title = top_paper.get('title', 'Unknown title')[:80] + "..."
                            citations = top_paper.get('citation_count', 'N/A')
                            output.append(f"  Top: {title} (Citations: {citations})")
                output.append("")
        
        output.append(f"📊 Total Papers Found: {total_papers}")
        output.append("")
    
    # Infographic status
    if has_infographic:
        if 'infographic' in results:
            infographic = results['infographic']
            if 'error' not in infographic:
                output.append("📊 INFOGRAPHIC GENERATED!")
                output.append("-" * 30)
                
                if 'data_summary' in infographic:
                    summary = infographic['data_summary']
                    output.append(f"Papers Analyzed: {summary.get('papers_analyzed', 0)}")
                    output.append(f"Citations Tracked: {summary.get('citations_tracked', 0)}")
                
                output.append("")
                output.append("📈 Visual Charts Generated:")
                if 'charts' in infographic:
                    for chart_name in infographic['charts'].keys():
                        if chart_name != 'summary_stats':
                            output.append(f"  • {chart_name.replace('_', ' ').title()}")
                
                output.append("")
                output.append("💡 Tip: Charts are generated for easy marketing export!")
            else:
                output.append(f"⚠️  Infographic generation failed: {infographic['error']}")
    
    output.append("✨ Analysis Complete!")
    return "\n".join(output)

def format_trends_results(results: Dict, has_visualization: bool = False) -> str:
    """Format industry trends results for display"""
    output = []
    
    if 'error' in results:
        return f"Trends Analysis Error: {results['error']}"
    
    industry = results.get('industry', 'Unknown Industry')
    timeframe = results.get('timeframe', 'Unknown timeframe')
    
    output.append(f"📈 Industry Trends Analysis: {industry}")
    output.append("=" * 60)
    output.append(f"⏰ Timeframe: {timeframe}")
    output.append("")
    
    # Trend analysis summary
    if 'trend_analysis' in results:
        output.append("🔍 Trend Categories Analyzed:")
        output.append("-" * 40)
        
        total_insights = 0
        for trend_type, trend_data in results['trend_analysis'].items():
            if 'sources' in trend_data and 'scholar' in trend_data['sources']:
                papers = trend_data['sources']['scholar']
                paper_count = len([p for p in papers if 'error' not in p])
                
                output.append(f"• {trend_type.replace('_', ' ').title()}: {paper_count} papers")
                total_insights += paper_count
        
        output.append(f"📊 Total Research Papers: {total_insights}")
        output.append("")
    
    # Key insights
    if 'key_insights' in results and results['key_insights']:
        output.append("💡 Top Industry Insights:")
        output.append("-" * 30)
        
        for i, insight in enumerate(results['key_insights'][:3], 1):  # Top 3 insights
            title = insight.get('title', 'Unknown title')[:60] + "..."
            year = insight.get('year', 'Unknown')
            citations = insight.get('citations', 0)
            
            output.append(f"{i}. {title}")
            output.append(f"   Year: {year} | Citations: {citations}")
            output.append("")
    
    # Visualization status
    if has_visualization:
        if 'visualization' in results and 'error' not in results['visualization']:
            output.append("📊 TREND VISUALIZATIONS GENERATED!")
            output.append("-" * 35)
            output.append("📈 Charts ready for marketing presentations")
        else:
            output.append("⚠️ Visualization generation encountered issues")
        output.append("")
    
    output.append("✨ Trend Analysis Complete!")
    output.append("🎯 Ready for marketing consumption!")
    
    return "\n".join(output)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8503))
    print(f"Starting Molaison Research & Crawl Agent on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)