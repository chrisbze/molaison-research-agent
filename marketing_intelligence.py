#!/usr/bin/env python3
"""
Marketing Intelligence Module for Molaison Research Agent
Analyzes top companies, research papers, and generates consumer-friendly infographics
"""

import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import time
import io
import base64

# Visualization libraries
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    from wordcloud import WordCloud
    import pandas as pd
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    VISUALIZATION_AVAILABLE = True
except ImportError as e:
    print(f"Visualization libraries not available: {e}")
    VISUALIZATION_AVAILABLE = False

# Import academic research functions
try:
    from academic_research import AcademicResearcher
except ImportError:
    AcademicResearcher = None

class MarketingIntelligenceAnalyzer:
    def __init__(self):
        self.researcher = AcademicResearcher() if AcademicResearcher else None
        
        # Company intelligence sources
        self.company_sources = {
            'fortune_500': 'https://fortune.com/fortune500/',
            'crunchbase_api': 'https://api.crunchbase.com/v3.1/',  # Requires API key
            'yahoo_finance': 'https://finance.yahoo.com/quote/',
            'sec_filings': 'https://www.sec.gov/Archives/edgar/'
        }
        
        # Marketing-focused search queries
        self.marketing_queries = {
            'trends': ['market trends', 'consumer behavior', 'digital transformation'],
            'innovation': ['disruptive technology', 'innovation strategy', 'emerging markets'],
            'customer_experience': ['customer satisfaction', 'user experience', 'brand loyalty'],
            'sustainability': ['sustainable business', 'ESG initiatives', 'green marketing'],
            'ai_ml': ['artificial intelligence marketing', 'machine learning business', 'AI adoption']
        }
    
    def search_company_intelligence(self, company_name: str, focus_areas: List[str] = None) -> Dict:
        """Search for company intelligence and research papers"""
        if not self.researcher:
            return {"error": "Academic researcher not available"}
        
        if focus_areas is None:
            focus_areas = ['innovation', 'market strategy', 'customer experience']
        
        results = {
            'company': company_name,
            'timestamp': datetime.now().isoformat(),
            'intelligence': {},
            'research_papers': {},
            'market_insights': {}
        }
        
        try:
            # Search for company research papers
            for area in focus_areas:
                query = f'"{company_name}" {area}'
                print(f"Searching for: {query}")
                
                # Search academic sources
                academic_results = self.researcher.comprehensive_search(
                    query, sources=['pubmed', 'scholar'], max_results=10
                )
                
                results['research_papers'][area] = academic_results['sources']
                
                # Add market intelligence searches
                market_query = f'{company_name} {area} market analysis'
                results['market_insights'][area] = {
                    'search_performed': True,
                    'query': market_query,
                    'timestamp': datetime.now().isoformat()
                }
                
                time.sleep(1)  # Rate limiting
            
            return results
            
        except Exception as e:
            return {"error": f"Company intelligence search failed: {str(e)}"}
    
    def analyze_market_trends(self, industry: str, timeframe: str = "2023-2024") -> Dict:
        """Analyze market trends for a specific industry"""
        if not self.researcher:
            return {"error": "Academic researcher not available"}
        
        trend_queries = [
            f"{industry} market trends {timeframe}",
            f"{industry} consumer behavior {timeframe}",
            f"{industry} innovation {timeframe}",
            f"{industry} digital transformation {timeframe}"
        ]
        
        results = {
            'industry': industry,
            'timeframe': timeframe,
            'trend_analysis': {},
            'key_insights': [],
            'top_papers': []
        }
        
        try:
            for query in trend_queries:
                search_results = self.researcher.comprehensive_search(
                    query, sources=['scholar'], max_results=15
                )
                
                trend_type = query.split()[1] + '_' + query.split()[2]  # e.g., "market_trends"
                results['trend_analysis'][trend_type] = search_results
                
                # Extract key insights from top papers
                if 'scholar' in search_results['sources']:
                    top_papers = search_results['sources']['scholar'][:3]
                    for paper in top_papers:
                        if 'abstract' in paper:
                            results['key_insights'].append({
                                'title': paper.get('title', ''),
                                'insight': paper.get('abstract', '')[:300] + "...",
                                'citations': paper.get('citation_count', 0),
                                'year': paper.get('year', 'Unknown')
                            })
                
                time.sleep(2)  # Rate limiting for Google Scholar
            
            return results
            
        except Exception as e:
            return {"error": f"Market trend analysis failed: {str(e)}"}
    
    def generate_infographic_data(self, research_data: Dict, viz_type: str = "summary") -> Dict:
        """Process research data into infographic-ready format"""
        if not VISUALIZATION_AVAILABLE:
            return {"error": "Visualization libraries not available"}
        
        try:
            if viz_type == "summary":
                return self._create_summary_infographic(research_data)
            elif viz_type == "trends":
                return self._create_trends_infographic(research_data)
            elif viz_type == "comparison":
                return self._create_comparison_infographic(research_data)
            else:
                return {"error": f"Unsupported visualization type: {viz_type}"}
                
        except Exception as e:
            return {"error": f"Infographic generation failed: {str(e)}"}
    
    def _create_summary_infographic(self, data: Dict) -> Dict:
        """Create a summary infographic from research data"""
        # Extract key metrics
        total_papers = 0
        total_citations = 0
        key_topics = []
        yearly_distribution = {}
        
        # Process research sources
        if 'research_papers' in data:
            for area, sources in data['research_papers'].items():
                for source_name, papers in sources.items():
                    if isinstance(papers, list):
                        for paper in papers:
                            if 'error' not in paper:
                                total_papers += 1
                                total_citations += int(paper.get('citation_count', 0) or 0)
                                
                                # Track years
                                year = paper.get('year', 'Unknown')
                                if year != 'Unknown' and year.isdigit():
                                    yearly_distribution[year] = yearly_distribution.get(year, 0) + 1
                                
                                # Extract key topics from titles
                                title = paper.get('title', '')
                                if title:
                                    key_topics.extend(self._extract_keywords(title))
        
        # Create visualizations
        charts = {}
        
        # 1. Citation distribution chart
        if yearly_distribution:
            charts['yearly_publications'] = self._create_bar_chart(
                yearly_distribution, 
                "Publications by Year", 
                "Year", 
                "Number of Publications"
            )
        
        # 2. Word cloud of key topics
        if key_topics:
            charts['topic_wordcloud'] = self._create_wordcloud(key_topics)
        
        # 3. Summary statistics
        charts['summary_stats'] = {
            'total_papers': total_papers,
            'total_citations': total_citations,
            'avg_citations': round(total_citations / max(total_papers, 1), 2),
            'research_areas': len(data.get('research_papers', {})),
            'time_period': f"{min(yearly_distribution.keys()) if yearly_distribution else 'N/A'}-{max(yearly_distribution.keys()) if yearly_distribution else 'N/A'}"
        }
        
        return {
            'type': 'summary_infographic',
            'charts': charts,
            'data_summary': {
                'papers_analyzed': total_papers,
                'citations_tracked': total_citations,
                'key_topics': list(set(key_topics[:20]))  # Top 20 unique topics
            }
        }
    
    def _create_trends_infographic(self, data: Dict) -> Dict:
        """Create trends-focused infographic"""
        charts = {}
        
        if 'trend_analysis' in data:
            trend_data = data['trend_analysis']
            
            # Create trend comparison chart
            trend_metrics = {}
            for trend_type, results in trend_data.items():
                if 'sources' in results and 'scholar' in results['sources']:
                    papers = results['sources']['scholar']
                    trend_metrics[trend_type] = len(papers)
            
            if trend_metrics:
                charts['trend_comparison'] = self._create_horizontal_bar_chart(
                    trend_metrics,
                    "Research Activity by Trend Category",
                    "Number of Papers"
                )
        
        # Citation impact analysis
        if 'key_insights' in data:
            insights = data['key_insights']
            citation_data = [insight.get('citations', 0) for insight in insights if isinstance(insight.get('citations', 0), int)]
            
            if citation_data:
                charts['citation_impact'] = self._create_histogram(
                    citation_data,
                    "Citation Impact Distribution",
                    "Citations",
                    "Frequency"
                )
        
        return {
            'type': 'trends_infographic',
            'charts': charts
        }
    
    def _create_comparison_infographic(self, data: Dict) -> Dict:
        """Create comparison infographic for multiple entities"""
        # Implementation for comparison charts
        return {
            'type': 'comparison_infographic',
            'charts': {}
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for word cloud"""
        # Simple keyword extraction
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        
        # Filter out common words
        stopwords = {'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'their', 'said', 'each', 'which', 'what', 'there', 'were', 'more', 'some', 'time', 'very', 'when', 'could', 'would', 'like', 'than', 'only', 'other', 'into', 'over', 'also', 'your', 'work', 'life', 'such'}
        
        return [word for word in words if word not in stopwords]
    
    def _create_bar_chart(self, data: Dict, title: str, xlabel: str, ylabel: str) -> str:
        """Create a bar chart and return as base64 string"""
        if not VISUALIZATION_AVAILABLE:
            return ""
        
        try:
            plt.figure(figsize=(10, 6))
            years = list(data.keys())
            values = list(data.values())
            
            plt.bar(years, values, color='#3498db')
            plt.title(title, fontsize=16, fontweight='bold')
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            print(f"Chart creation error: {e}")
            return ""
    
    def _create_horizontal_bar_chart(self, data: Dict, title: str, xlabel: str) -> str:
        """Create horizontal bar chart"""
        if not VISUALIZATION_AVAILABLE:
            return ""
        
        try:
            plt.figure(figsize=(10, 8))
            categories = list(data.keys())
            values = list(data.values())
            
            # Clean category names
            clean_categories = [cat.replace('_', ' ').title() for cat in categories]
            
            plt.barh(clean_categories, values, color='#e74c3c')
            plt.title(title, fontsize=16, fontweight='bold')
            plt.xlabel(xlabel)
            plt.tight_layout()
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            print(f"Horizontal chart creation error: {e}")
            return ""
    
    def _create_histogram(self, data: List, title: str, xlabel: str, ylabel: str) -> str:
        """Create histogram"""
        if not VISUALIZATION_AVAILABLE or not data:
            return ""
        
        try:
            plt.figure(figsize=(10, 6))
            plt.hist(data, bins=20, color='#9b59b6', alpha=0.7, edgecolor='black')
            plt.title(title, fontsize=16, fontweight='bold')
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.tight_layout()
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            print(f"Histogram creation error: {e}")
            return ""
    
    def _create_wordcloud(self, words: List[str]) -> str:
        """Create word cloud visualization"""
        if not VISUALIZATION_AVAILABLE or not words:
            return ""
        
        try:
            # Join words for word cloud
            text = ' '.join(words)
            
            wordcloud = WordCloud(
                width=800, 
                height=400, 
                background_color='white',
                colormap='viridis',
                max_words=50
            ).generate(text)
            
            plt.figure(figsize=(12, 6))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('Key Research Topics', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            print(f"Word cloud creation error: {e}")
            return ""
    
    def export_marketing_report(self, analysis_data: Dict, format_type: str = "html") -> str:
        """Export complete marketing intelligence report"""
        try:
            if format_type == "html":
                return self._create_html_report(analysis_data)
            elif format_type == "json":
                return json.dumps(analysis_data, indent=2)
            else:
                return f"Unsupported export format: {format_type}"
                
        except Exception as e:
            return f"Report export failed: {str(e)}"
    
    def _create_html_report(self, data: Dict) -> str:
        """Create HTML marketing report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Marketing Intelligence Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #667eea; }}
                .chart {{ text-align: center; margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
                .insight {{ background: #e8f4f8; padding: 15px; margin: 10px 0; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Marketing Intelligence Report</h1>
                <p>Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
        """
        
        # Add summary statistics
        if 'charts' in data and 'summary_stats' in data['charts']:
            stats = data['charts']['summary_stats']
            html += f"""
            <div class="section">
                <h2>📊 Research Summary</h2>
                <div class="metric"><strong>{stats['total_papers']}</strong><br>Papers Analyzed</div>
                <div class="metric"><strong>{stats['total_citations']}</strong><br>Total Citations</div>
                <div class="metric"><strong>{stats['avg_citations']}</strong><br>Avg Citations</div>
                <div class="metric"><strong>{stats['research_areas']}</strong><br>Research Areas</div>
            </div>
            """
        
        # Add charts
        if 'charts' in data:
            charts = data['charts']
            for chart_name, chart_data in charts.items():
                if isinstance(chart_data, str) and chart_data.startswith('data:image'):
                    html += f"""
                    <div class="section">
                        <h3>{chart_name.replace('_', ' ').title()}</h3>
                        <div class="chart">
                            <img src="{chart_data}" style="max-width: 100%; height: auto;">
                        </div>
                    </div>
                    """
        
        html += "</body></html>"
        return html

# Convenience functions for Flask integration
def analyze_company_marketing(company_name: str, focus_areas: List[str] = None) -> Dict:
    """Analyze company marketing intelligence"""
    analyzer = MarketingIntelligenceAnalyzer()
    return analyzer.search_company_intelligence(company_name, focus_areas)

def analyze_industry_trends(industry: str, timeframe: str = "2023-2024") -> Dict:
    """Analyze industry trends for marketing insights"""
    analyzer = MarketingIntelligenceAnalyzer()
    return analyzer.analyze_market_trends(industry, timeframe)

def create_marketing_infographic(research_data: Dict, viz_type: str = "summary") -> Dict:
    """Generate marketing infographic from research data"""
    analyzer = MarketingIntelligenceAnalyzer()
    return analyzer.generate_infographic_data(research_data, viz_type)