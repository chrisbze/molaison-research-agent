#!/usr/bin/env python3
"""
Academic Research Module for Molaison Research Agent
Handles PubMed, Google Scholar, DOI resolution, and citation parsing
"""

import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import time

# Academic APIs and tools
try:
    from scholarly import scholarly
    from Bio import Entrez
    from crossref.restful import Works
    import bibtexparser
    from dateutil.parser import parse as date_parse
except ImportError as e:
    print(f"Warning: Some academic libraries not available: {e}")
    scholarly = None

class AcademicResearcher:
    def __init__(self):
        self.works = Works() if 'Works' in globals() else None
        # Set email for Entrez (required by NCBI)
        Entrez.email = "molaison-research@example.com"  # Change this to your email
        
    def search_pubmed(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search PubMed for medical/life science articles"""
        try:
            # Search PubMed
            handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
            search_results = Entrez.read(handle)
            handle.close()
            
            if not search_results["IdList"]:
                return []
            
            # Get article details
            ids = ",".join(search_results["IdList"])
            handle = Entrez.efetch(db="pubmed", id=ids, rettype="xml", retmode="text")
            articles = Entrez.read(handle)
            handle.close()
            
            results = []
            for article in articles['PubmedArticle']:
                try:
                    medline = article['MedlineCitation']
                    article_data = medline['Article']
                    
                    # Extract basic information
                    title = article_data.get('ArticleTitle', 'No title')
                    abstract = article_data.get('Abstract', {}).get('AbstractText', ['No abstract available'])
                    
                    if isinstance(abstract, list):
                        abstract = ' '.join(str(part) for part in abstract)
                    
                    # Extract authors
                    authors = []
                    author_list = article_data.get('AuthorList', [])
                    for author in author_list:
                        if 'LastName' in author and 'ForeName' in author:
                            authors.append(f"{author['ForeName']} {author['LastName']}")
                    
                    # Extract journal and publication info
                    journal = article_data.get('Journal', {}).get('Title', 'Unknown journal')
                    pub_date = medline.get('DateCompleted', {})
                    year = pub_date.get('Year', 'Unknown year')
                    
                    # Get PMID
                    pmid = medline.get('PMID', '')
                    
                    results.append({
                        'source': 'PubMed',
                        'pmid': str(pmid),
                        'title': str(title),
                        'authors': authors,
                        'journal': str(journal),
                        'year': str(year),
                        'abstract': str(abstract),
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else '',
                        'citation_count': 'N/A'
                    })
                    
                except Exception as e:
                    print(f"Error processing PubMed article: {e}")
                    continue
                    
            return results
            
        except Exception as e:
            print(f"PubMed search error: {e}")
            return []
    
    def search_google_scholar(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search Google Scholar for academic articles"""
        if not scholarly:
            return [{"error": "Google Scholar library not available"}]
            
        try:
            search_query = scholarly.search_pubs(query)
            results = []
            
            for i, publication in enumerate(search_query):
                if i >= max_results:
                    break
                    
                try:
                    # Get detailed information
                    pub_filled = scholarly.fill(publication)
                    
                    # Extract information
                    title = pub_filled.get('title', 'No title')
                    authors = pub_filled.get('author', [])
                    author_names = [author.get('name', '') for author in authors if isinstance(author, dict)]
                    
                    venue = pub_filled.get('venue', 'Unknown venue')
                    year = pub_filled.get('year', 'Unknown year')
                    citations = pub_filled.get('num_citations', 0)
                    abstract = pub_filled.get('abstract', 'No abstract available')
                    
                    # Get URL
                    url = pub_filled.get('url', '')
                    if not url and pub_filled.get('url_scholarbib'):
                        url = pub_filled.get('url_scholarbib')
                    
                    results.append({
                        'source': 'Google Scholar',
                        'title': str(title),
                        'authors': author_names,
                        'venue': str(venue),
                        'year': str(year),
                        'abstract': str(abstract),
                        'citation_count': citations,
                        'url': str(url),
                        'scholar_id': pub_filled.get('scholar_id', '')
                    })
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error processing Scholar result: {e}")
                    continue
                    
            return results
            
        except Exception as e:
            print(f"Google Scholar search error: {e}")
            return []
    
    def resolve_doi(self, doi: str) -> Dict:
        """Resolve DOI using CrossRef API"""
        if not self.works:
            return {"error": "CrossRef library not available"}
            
        try:
            # Clean DOI
            clean_doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
            
            # Get work from CrossRef
            work = self.works.doi(clean_doi)
            
            if not work:
                return {"error": "DOI not found"}
            
            # Extract information
            title = work.get('title', ['Unknown title'])[0] if work.get('title') else 'Unknown title'
            authors = []
            
            for author in work.get('author', []):
                given = author.get('given', '')
                family = author.get('family', '')
                if given and family:
                    authors.append(f"{given} {family}")
            
            # Get journal/publisher info
            container_title = work.get('container-title', ['Unknown journal'])
            journal = container_title[0] if container_title else 'Unknown journal'
            
            # Get publication date
            pub_date = work.get('published-print', work.get('published-online', {}))
            year = 'Unknown year'
            if pub_date.get('date-parts'):
                year = str(pub_date['date-parts'][0][0])
            
            # Get other metadata
            volume = work.get('volume', '')
            issue = work.get('issue', '')
            pages = work.get('page', '')
            
            return {
                'source': 'CrossRef DOI',
                'doi': clean_doi,
                'title': str(title),
                'authors': authors,
                'journal': str(journal),
                'year': str(year),
                'volume': str(volume),
                'issue': str(issue),
                'pages': str(pages),
                'url': f"https://doi.org/{clean_doi}",
                'citation_count': work.get('is-referenced-by-count', 0)
            }
            
        except Exception as e:
            print(f"DOI resolution error: {e}")
            return {"error": f"Failed to resolve DOI: {str(e)}"}
    
    def parse_citation(self, citation_text: str, format_type: str = "auto") -> Dict:
        """Parse citation text in various formats (BibTeX, APA, MLA, etc.)"""
        try:
            result = {
                'original': citation_text,
                'format': format_type,
                'parsed': {}
            }
            
            # Try BibTeX parsing first
            if '@' in citation_text and '{' in citation_text:
                try:
                    bib_db = bibtexparser.loads(citation_text)
                    if bib_db.entries:
                        entry = bib_db.entries[0]
                        result['format'] = 'BibTeX'
                        result['parsed'] = {
                            'title': entry.get('title', ''),
                            'authors': entry.get('author', '').split(' and '),
                            'journal': entry.get('journal', entry.get('booktitle', '')),
                            'year': entry.get('year', ''),
                            'volume': entry.get('volume', ''),
                            'pages': entry.get('pages', ''),
                            'doi': entry.get('doi', ''),
                            'url': entry.get('url', '')
                        }
                        return result
                except:
                    pass
            
            # Basic regex parsing for common citation formats
            patterns = {
                'title': r'"([^"]+)"|'([^']+)'|([A-Z][^.]*\.)',
                'year': r'\((\d{4})\)|(\d{4})',
                'doi': r'doi:?\s*(10\.\d+/[^\s]+)',
                'url': r'(https?://[^\s]+)'
            }
            
            parsed = {}
            for field, pattern in patterns.items():
                match = re.search(pattern, citation_text, re.IGNORECASE)
                if match:
                    parsed[field] = match.group(1) or match.group(0)
            
            # Try to extract authors (basic heuristic)
            # Look for patterns like "Smith, J., Jones, M."
            author_pattern = r'([A-Z][a-z]+,\s[A-Z]\.(?:\s[A-Z]\.)?)'
            authors = re.findall(author_pattern, citation_text)
            if authors:
                parsed['authors'] = authors
            
            result['parsed'] = parsed
            result['format'] = 'Parsed'
            
            return result
            
        except Exception as e:
            return {
                'original': citation_text,
                'format': 'Error',
                'error': str(e),
                'parsed': {}
            }
    
    def comprehensive_search(self, query: str, sources: List[str] = None, max_results: int = 10) -> Dict:
        """Search across multiple academic sources"""
        if sources is None:
            sources = ['pubmed', 'scholar', 'doi']
        
        results = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'sources': {}
        }
        
        if 'pubmed' in sources:
            print(f"Searching PubMed for: {query}")
            results['sources']['pubmed'] = self.search_pubmed(query, max_results)
        
        if 'scholar' in sources:
            print(f"Searching Google Scholar for: {query}")
            results['sources']['scholar'] = self.search_google_scholar(query, max_results)
        
        # If query looks like a DOI, resolve it
        if 'doi' in sources and ('10.' in query or 'doi' in query.lower()):
            print(f"Resolving DOI: {query}")
            doi_result = self.resolve_doi(query)
            if 'error' not in doi_result:
                results['sources']['doi'] = [doi_result]
        
        return results

# Convenience functions for Flask integration
def search_academic(query: str, sources: List[str] = None, max_results: int = 10) -> Dict:
    """Main search function for academic content"""
    researcher = AcademicResearcher()
    return researcher.comprehensive_search(query, sources, max_results)

def parse_citation_text(citation: str, format_type: str = "auto") -> Dict:
    """Parse a citation string"""
    researcher = AcademicResearcher()
    return researcher.parse_citation(citation, format_type)