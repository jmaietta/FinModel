"""
Field discovery adapter to find the exact field names Polygon uses.
This will test multiple variations to find Sales & Marketing and G&A fields.
"""
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime


class PolygonAdapter:
    """Field discovery adapter to identify exact Polygon field names."""
    
    def __init__(self, api_key: str):
        """Initialize Polygon adapter with API key."""
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.logger = logging.getLogger(__name__)
        
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make HTTP request to Polygon API."""
        try:
            params['apikey'] = self.api_key
            url = f"{self.base_url}{endpoint}"
            
            self.logger.info(f"Making request to: {url}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return None
    
    def _safe_get_value(self, data_dict: Dict, key: str, default=0) -> float:
        """Safely extract value from nested dictionary structure."""
        try:
            if key in data_dict and isinstance(data_dict[key], dict):
                return float(data_dict[key].get('value', default))
            return float(default)
        except (ValueError, TypeError):
            return float(default)
    
    def discover_field_names(self, ticker: str) -> Dict:
        """
        Comprehensive field discovery to find exact Polygon field names.
        This will help us identify the correct field names for Sales & Marketing and G&A.
        """
        try:
            endpoint = f"/vX/reference/financials"
            params = {
                'ticker': ticker.upper(),
                'timeframe': 'quarterly',
                'limit': 1
            }
            
            self.logger.info(f"=== DISCOVERING FIELD NAMES FOR {ticker} ===")
            data = self._make_request(endpoint, params)
            
            if not data or 'results' not in data or len(data['results']) == 0:
                self.logger.warning(f"No data found for {ticker}")
                return {}
            
            result = data['results'][0]
            if 'financials' not in result or 'income_statement' not in result['financials']:
                self.logger.warning(f"No income statement found for {ticker}")
                return {}
            
            income_stmt = result['financials']['income_statement']
            period_date = result.get('end_date', 'Unknown')
            
            self.logger.info(f"Period: {period_date}")
            self.logger.info(f"Total fields available: {len(income_stmt)}")
            
            # Show ALL available fields with their values
            self.logger.info("\n=== ALL AVAILABLE FIELDS ===")
            field_analysis = {}
            
            for field_name in sorted(income_stmt.keys()):
                value = self._safe_get_value(income_stmt, field_name)
                field_analysis[field_name] = value
                
                # Format for display
                if value != 0:
                    if abs(value) >= 1000000000:
                        formatted_value = f"${value/1000000000:.2f}B"
                    elif abs(value) >= 1000000:
                        formatted_value = f"${value/1000000:.1f}M"
                    else:
                        formatted_value = f"${value:,.0f}"
                else:
                    formatted_value = "$0"
                
                self.logger.info(f"  '{field_name}': {formatted_value}")
            
            # Now let's specifically look for Sales & Marketing variations
            self.logger.info("\n=== SEARCHING FOR SALES & MARKETING FIELD ===")
            sm_candidates = []
            sm_keywords = ['sales', 'marketing', 'selling']
            
            for field_name in income_stmt.keys():
                field_lower = field_name.lower()
                if any(keyword in field_lower for keyword in sm_keywords):
                    value = self._safe_get_value(income_stmt, field_name)
                    sm_candidates.append((field_name, value))
                    self.logger.info(f"  CANDIDATE: '{field_name}' = ${value/1000000:.1f}M")
            
            # Look for G&A variations  
            self.logger.info("\n=== SEARCHING FOR GENERAL & ADMINISTRATIVE FIELD ===")
            ga_candidates = []
            ga_keywords = ['general', 'administrative', 'admin']
            
            for field_name in income_stmt.keys():
                field_lower = field_name.lower()
                if any(keyword in field_lower for keyword in ga_keywords):
                    value = self._safe_get_value(income_stmt, field_name)
                    ga_candidates.append((field_name, value))
                    self.logger.info(f"  CANDIDATE: '{field_name}' = ${value/1000000:.1f}M")
            
            # Look for combined SG&A fields
            self.logger.info("\n=== SEARCHING FOR COMBINED SG&A FIELDS ===")
            sga_candidates = []
            sga_keywords = ['selling_general', 'sg_a', 'sga', 'selling_and_administrative']
            
            for field_name in income_stmt.keys():
                field_lower = field_name.lower()
                if any(keyword in field_lower for keyword in sga_keywords):
                    value = self._safe_get_value(income_stmt, field_name)
                    sga_candidates.append((field_name, value))
                    self.logger.info(f"  CANDIDATE: '{field_name}' = ${value/1000000:.1f}M")
            
            # Look for expense-related fields that might contain our missing data
            self.logger.info("\n=== SEARCHING FOR OTHER EXPENSE FIELDS ===")
            expense_candidates = []
            expense_keywords = ['expense', 'cost', 'operating']
            exclude_keywords = ['tax', 'interest', 'depreciation', 'amortization']
            
            for field_name in income_stmt.keys():
                field_lower = field_name.lower()
                if (any(keyword in field_lower for keyword in expense_keywords) and 
                    not any(exclude in field_lower for exclude in exclude_keywords) and
                    field_name not in ['cost_of_revenue', 'operating_expenses', 'research_and_development']):
                    value = self._safe_get_value(income_stmt, field_name)
                    if value != 0:  # Only show non-zero values
                        expense_candidates.append((field_name, value))
                        self.logger.info(f"  CANDIDATE: '{field_name}' = ${value/1000000:.1f}M")
            
            # Analysis summary
            self.logger.info("\n=== ANALYSIS SUMMARY ===")
            if sm_candidates:
                self.logger.info(f"Found {len(sm_candidates)} Sales & Marketing candidates")
            else:
                self.logger.info("❌ No Sales & Marketing candidates found")
            
            if ga_candidates:
                self.logger.info(f"Found {len(ga_candidates)} General & Administrative candidates")
            else:
                self.logger.info("❌ No General & Administrative candidates found")
            
            if sga_candidates:
                self.logger.info(f"Found {len(sga_candidates)} combined SG&A candidates")
                # Check if any SG&A field equals S&M + G&A from Microsoft's actual figures
                expected_sga = 6212 + 1737  # Microsoft's Q1 2025 figures
                for field_name, value in sga_candidates:
                    if abs(value/1000000 - expected_sga) < 100:  # Within $100M
                        self.logger.info(f"  ✅ LIKELY MATCH: '{field_name}' ≈ ${expected_sga}M")
            else:
                self.logger.info("❌ No combined SG&A candidates found")
            
            return {
                'period': period_date,
                'all_fields': field_analysis,
                'sales_marketing_candidates': sm_candidates,
                'general_admin_candidates': ga_candidates,
                'combined_sga_candidates': sga_candidates,
                'other_expense_candidates': expense_candidates
            }
            
        except Exception as e:
            self.logger.error(f"Error discovering fields for {ticker}: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {}
    
    def test_field_mapping(self, ticker: str, field_candidates: Dict) -> Dict:
        """
        Test mapping with discovered field names to see if we can get the right values.
        """
        try:
            endpoint = f"/vX/reference/financials"
            params = {
                'ticker': ticker.upper(),
                'timeframe': 'quarterly',
                'limit': 1
            }
            
            data = self._make_request(endpoint, params)
            if not data or 'results' not in data or len(data['results']) == 0:
                return {}
            
            income_stmt = data['results'][0]['financials']['income_statement']
            
            self.logger.info("\n=== TESTING FIELD MAPPINGS ===")
            
            # Test the most promising candidates
            test_results = {}
            
            # Known working fields for comparison
            revenue = self._safe_get_value(income_stmt, 'revenues')
            rd = self._safe_get_value(income_stmt, 'research_and_development')
            
            self.logger.info(f"Reference values (MSFT Q1 2025):")
            self.logger.info(f"  Revenue: ${revenue/1000000:.0f}M (should be ~70,066)")
            self.logger.info(f"  R&D: ${rd/1000000:.0f}M (should be ~8,198)")
            
            # Test each candidate field
            for category, candidates in field_candidates.items():
                if candidates and category != 'all_fields':
                    self.logger.info(f"\nTesting {category}:")
                    for field_name, value in candidates:
                        test_results[field_name] = value
                        self.logger.info(f"  '{field_name}': ${value/1000000:.0f}M")
            
            return test_results
            
        except Exception as e:
            self.logger.error(f"Error testing field mapping: {str(e)}")
            return {}
    
    def get_income_statement(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> Dict:
        """Placeholder - run discovery first to determine correct mapping."""
        self.logger.info("Run discover_field_names() first to identify correct field mappings")
        return {}


class ProviderSelector:
    """Provider selector with field discovery capabilities."""
    
    def __init__(self, api_keys: dict):
        """Initialize with API keys dictionary."""
        self.api_key = api_keys.get('polygon', '')
        if not self.api_key:
            raise ValueError("Polygon API key is required")
            
        self.adapter = PolygonAdapter(self.api_key)
        self.logger = logging.getLogger(__name__)
    
    def discover_fields(self, ticker: str):
        """Discover available field names for a ticker."""
        self.logger.info(f"Discovering available fields for {ticker}")
        return self.adapter.discover_field_names(ticker)
    
    def test_mapping(self, ticker: str, candidates: Dict):
        """Test field mapping with discovered candidates."""
        return self.adapter.test_field_mapping(ticker, candidates)
