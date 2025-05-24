"""
API client module for retrieving SEC EDGAR data.

This module provides interfaces for interacting with the SEC EDGAR API
and other third-party APIs for retrieving SEC filing data.
"""
import os
import time
import logging
import json
import requests
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from ..config import ApiConfig


class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(self, requests_per_second: int = 10):
        """Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum number of requests per second.
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
    
    def wait(self) -> None:
        """Wait if necessary to comply with rate limits."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()


class ApiClient:
    """Base API client for SEC EDGAR data."""
    
    def __init__(self, config: ApiConfig):
        """Initialize API client.
        
        Args:
            config: API configuration.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.rate_limiter = RateLimiter(config.rate_limit)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SecEdgarParser/1.0',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        })
        
        # Add API key if provided
        if config.api_key:
            self.session.headers.update({'X-API-Key': config.api_key})
    
    def _make_request(self, 
                     endpoint: str, 
                     method: str = 'GET', 
                     params: Optional[Dict] = None, 
                     data: Optional[Dict] = None,
                     headers: Optional[Dict] = None) -> requests.Response:
        """Make an API request with rate limiting and retries.
        
        Args:
            endpoint: API endpoint to request.
            method: HTTP method (GET, POST, etc.).
            params: Query parameters.
            data: Request body data.
            headers: Additional headers.
            
        Returns:
            Response object.
            
        Raises:
            requests.RequestException: If the request fails after retries.
        """
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        combined_headers = self.session.headers.copy()
        if headers:
            combined_headers.update(headers)
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Wait for rate limiter
                self.rate_limiter.wait()
                
                # Make the request
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=combined_headers,
                    timeout=self.config.timeout
                )
                
                # Check for success
                response.raise_for_status()
                return response
                
            except requests.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt+1}/{self.config.max_retries+1}): {str(e)}")
                
                # If this was the last attempt, raise the exception
                if attempt == self.config.max_retries:
                    raise
                
                # Otherwise, wait before retrying
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def get(self, 
            endpoint: str, 
            params: Optional[Dict] = None, 
            headers: Optional[Dict] = None) -> Dict:
        """Make a GET request to the API.
        
        Args:
            endpoint: API endpoint to request.
            params: Query parameters.
            headers: Additional headers.
            
        Returns:
            Parsed JSON response.
        """
        response = self._make_request(endpoint, 'GET', params, headers=headers)
        return response.json()


class SecEdgarClient(ApiClient):
    """Client for the official SEC EDGAR API."""
    
    def get_company_submissions(self, cik: str) -> Dict:
        """Get company submissions.
        
        Args:
            cik: Central Index Key (CIK) of the company.
            
        Returns:
            Company submissions data.
        """
        # Ensure CIK is properly formatted (10 digits with leading zeros)
        cik = cik.strip().lstrip('0')
        cik_padded = cik.zfill(10)
        
        endpoint = f"submissions/CIK{cik_padded}.json"
        return self.get(endpoint)
    
    def get_company_facts(self, cik: str) -> Dict:
        """Get all company facts.
        
        Args:
            cik: Central Index Key (CIK) of the company.
            
        Returns:
            Company facts data.
        """
        # Ensure CIK is properly formatted (10 digits with leading zeros)
        cik = cik.strip().lstrip('0')
        cik_padded = cik.zfill(10)
        
        endpoint = f"api/xbrl/companyfacts/CIK{cik_padded}.json"
        return self.get(endpoint)
    
    def get_company_concept(self, cik: str, taxonomy: str, tag: str) -> Dict:
        """Get a specific company concept.
        
        Args:
            cik: Central Index Key (CIK) of the company.
            taxonomy: Taxonomy name (e.g., 'us-gaap').
            tag: Concept tag (e.g., 'Revenues').
            
        Returns:
            Company concept data.
        """
        # Ensure CIK is properly formatted (10 digits with leading zeros)
        cik = cik.strip().lstrip('0')
        cik_padded = cik.zfill(10)
        
        endpoint = f"api/xbrl/companyconcept/CIK{cik_padded}/{taxonomy}/{tag}.json"
        return self.get(endpoint)
    
    def get_filing_metadata(self, accession_number: str) -> Dict:
        """Get metadata for a specific filing.
        
        Args:
            accession_number: Accession number of the filing.
            
        Returns:
            Filing metadata.
        """
        # Format accession number (remove dashes)
        accession = accession_number.replace('-', '')
        
        endpoint = f"api/xbrl/filings/{accession}.json"
        return self.get(endpoint)


class CompanyInfo:
    """Utility class for retrieving and caching company information."""
    
    def __init__(self, api_client: ApiClient, cache_dir: str):
        """Initialize company info utility.
        
        Args:
            api_client: API client for retrieving data.
            cache_dir: Directory for caching company data.
        """
        self.api_client = api_client
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        self.company_cache = {}
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load local ticker-to-CIK mapping
        self.ticker_to_cik_map = self._load_ticker_to_cik_mapping()
    
    def _load_ticker_to_cik_mapping(self) -> Dict:
        """Load ticker-to-CIK mapping from local file.
        
        Returns:
            Dictionary mapping tickers to CIKs.
        """
        # Path to the local mapping file - use absolute path
        mapping_file = '/home/ubuntu/sec_parser/data/tech_company_cik_mapping.json'
        
        self.logger.info(f"Attempting to load ticker-to-CIK mapping from: {mapping_file}")
        
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r') as f:
                    mapping = json.load(f)
                self.logger.info(f"Successfully loaded ticker-to-CIK mapping for {len(mapping)} companies")
                
                # Debug: Print the first few entries
                sample_entries = list(mapping.items())[:5]
                self.logger.debug(f"Sample mapping entries: {sample_entries}")
                
                return mapping
            except Exception as e:
                self.logger.error(f"Error loading ticker-to-CIK mapping: {str(e)}")
                return {}
        else:
            self.logger.error(f"Ticker-to-CIK mapping file not found at: {mapping_file}")
            return {}
    
    def get_cik_from_ticker(self, ticker: str) -> str:
        """Get CIK from ticker symbol.
        
        Args:
            ticker: Ticker symbol.
            
        Returns:
            CIK number.
            
        Raises:
            ValueError: If the ticker cannot be resolved to a CIK.
        """
        # Normalize ticker to uppercase for consistent lookup
        ticker = ticker.upper()
        
        self.logger.debug(f"Looking up CIK for ticker: {ticker}")
        
        # Check cache first
        if ticker in self.company_cache:
            self.logger.debug(f"Found ticker {ticker} in cache")
            return self.company_cache[ticker]['cik']
        
        # Check local mapping
        if ticker in self.ticker_to_cik_map:
            self.logger.debug(f"Found ticker {ticker} in local mapping")
            cik = str(self.ticker_to_cik_map[ticker]['cik_str'])
            self.company_cache[ticker] = {'cik': cik}
            return cik
        
        # If not in local mapping, try hardcoded values for common tech companies
        hardcoded_mapping = {
            'AAPL': '320193',
            'MSFT': '789019',
            'GOOGL': '1652044',
            'AMZN': '1018724',
            'META': '1326801',
            'NVDA': '1045810',
            'TSLA': '1318605',
            'INTC': '50863',
            'AMD': '2488',
            'CSCO': '858877'
        }
        
        if ticker in hardcoded_mapping:
            self.logger.debug(f"Found ticker {ticker} in hardcoded mapping")
            cik = hardcoded_mapping[ticker]
            self.company_cache[ticker] = {'cik': cik}
            return cik
        
        # If not found anywhere, raise error
        self.logger.error(f"Could not resolve ticker {ticker} to a CIK")
        raise ValueError(f"Could not resolve ticker {ticker} to a CIK. Ticker not found in any mapping.")
    
    def is_tech_company(self, cik: str) -> bool:
        """Check if a company is in the Technology sector based on local mapping.
        
        Args:
            cik: Central Index Key (CIK) of the company.
            
        Returns:
            True if the company is in the Technology sector, False otherwise.
        """
        # For simplicity, consider all companies in our mapping to be tech companies
        # This is a reasonable assumption since we're focusing on tech sector companies
        
        # Check if any ticker in our mapping maps to this CIK
        for ticker, company_info in self.ticker_to_cik_map.items():
            if str(company_info['cik_str']) == cik:
                self.logger.debug(f"CIK {cik} found in tech company mapping")
                return True
        
        # Also check hardcoded values
        hardcoded_ciks = [
            '320193',  # AAPL
            '789019',  # MSFT
            '1652044', # GOOGL
            '1018724', # AMZN
            '1326801', # META
            '1045810', # NVDA
            '1318605', # TSLA
            '50863',   # INTC
            '2488',    # AMD
            '858877'   # CSCO
        ]
        
        if cik in hardcoded_ciks:
            self.logger.debug(f"CIK {cik} found in hardcoded tech company list")
            return True
        
        # If not found in our tech mapping, assume it's not a tech company
        return False
