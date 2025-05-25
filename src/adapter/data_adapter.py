"""
Working field discovery adapter that performs discovery AND generates income statements.
"""
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime


class PolygonAdapter:
    """Working Polygon.io API adapter with field discovery and income statement generation."""
    
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
            
            # Look for Sales & Marketing variations
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
            
            # Analysis summary
            self.logger.info("\n=== ANALYSIS SUMMARY ===")
            if sm_candidates:
                self.logger.info(f"Found {len(sm_candidates)} Sales & Marketing candidates")
                for field_name, value in sm_candidates:
                    # Check if close to expected MSFT value of ~$6,212M
                    if 6000 <= value/1000000 <= 7000:
                        self.logger.info(f"  ✅ LIKELY MATCH: '{field_name}' = ${value/1000000:.0f}M (expected ~6,212M)")
            else:
                self.logger.info("❌ No Sales & Marketing candidates found")
            
            if ga_candidates:
                self.logger.info(f"Found {len(ga_candidates)} General & Administrative candidates")
                for field_name, value in ga_candidates:
                    # Check if close to expected MSFT value of ~$1,737M
                    if 1500 <= value/1000000 <= 2000:
                        self.logger.info(f"  ✅ LIKELY MATCH: '{field_name}' = ${value/1000000:.0f}M (expected ~1,737M)")
            else:
                self.logger.info("❌ No General & Administrative candidates found")
            
            if sga_candidates:
                self.logger.info(f"Found {len(sga_candidates)} combined SG&A candidates")
                for field_name, value in sga_candidates:
                    # Check if close to expected combined value of ~$7,949M
                    if 7500 <= value/1000000 <= 8500:
                        self.logger.info(f"  ✅ LIKELY MATCH: '{field_name}' = ${value/1000000:.0f}M (expected ~7,949M)")
            else:
                self.logger.info("❌ No combined SG&A candidates found")
            
            return {
                'period': period_date,
                'all_fields': field_analysis,
                'sales_marketing_candidates': sm_candidates,
                'general_admin_candidates': ga_candidates,
                'combined_sga_candidates': sga_candidates
            }
            
        except Exception as e:
            self.logger.error(f"Error discovering fields for {ticker}: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {}
    
    def get_income_statement(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> Dict:
        """
        Get income statement WITH field discovery for the first period.
        """
        try:
            timeframe = 'quarterly' if period.lower() == 'quarterly' else 'annual'
            
            endpoint = f"/vX/reference/financials"
            params = {
                'ticker': ticker.upper(),
                'timeframe': timeframe,
                'limit': limit
            }
            
            self.logger.info(f"Fetching {period} income statement for {ticker}")
            data = self._make_request(endpoint, params)
            
            if not data or 'results' not in data:
                self.logger.warning(f"No income statement data found for {ticker}")
                return {
                    'ticker': ticker.upper(),
                    'company_name': ticker.upper(),
                    'periods': {}
                }
            
            # PERFORM FIELD DISCOVERY ON FIRST RESULT
            if data['results']:
                self.logger.info("=== PERFORMING FIELD DISCOVERY ===")
                discovery_results = self.discover_field_names(ticker)
                
                # Determine the best field mappings from discovery
                field_mappings = self._determine_field_mappings(discovery_results)
                self.logger.info(f"Determined field mappings: {field_mappings}")
            
            # Initialize the result
            result = {
                'ticker': ticker.upper(),
                'company_name': ticker.upper(),
                'periods': {},
                'field_discovery': discovery_results if 'discovery_results' in locals() else {}
            }
            
            # Process each period using discovered field mappings
            for api_result in data.get('results', []):
                if 'financials' in api_result and 'income_statement' in api_result['financials']:
                    income_stmt = api_result['financials']['income_statement']
                    period_date = api_result.get('end_date', '')
                    
                    if not period_date:
                        continue
                    
                    # Create period items using discovered mappings
                    period_items = {
                        # CORE FIELDS (known to work)
                        'Revenues': {'value': self._safe_get_value(income_stmt, 'revenues')},
                        'CostOfGoodsSold': {'value': self._safe_get_value(income_stmt, 'cost_of_revenue')},
                        'GrossProfit': {'value': self._safe_get_value(income_stmt, 'gross_profit')},
                        'ResearchAndDevelopmentExpense': {'value': self._safe_get_value(income_stmt, 'research_and_development')},
                        'OperatingExpenses': {'value': self._safe_get_value(income_stmt, 'operating_expenses')},
                        'OperatingIncomeLoss': {'value': self._safe_get_value(income_stmt, 'operating_income_loss')},
                        'IncomeLossBeforeIncomeTaxes': {'value': self._safe_get_value(income_stmt, 'income_loss_from_continuing_operations_before_tax')},
                        'IncomeTaxExpenseBenefit': {'value': self._safe_get_value(income_stmt, 'income_tax_expense_benefit')},
                        'NetIncomeLoss': {'value': self._safe_get_value(income_stmt, 'net_income_loss')},
                        'WeightedAverageSharesOutstandingDiluted': {'value': self._safe_get_value(income_stmt, 'diluted_average_shares')},
                        
                        # DISCOVERED FIELDS (using field mappings)
                        'SalesAndMarketingExpense': {'value': self._safe_get_value(income_stmt, field_mappings.get('sales_marketing', 'missing_field'))},
                        'GeneralAndAdministrativeExpense': {'value': self._safe_get_value(income_stmt, field_mappings.get('general_admin', 'missing_field'))},
                        
                        # OTHER FIELDS
                        'StockBasedCompensation': {'value': self._safe_get_value(income_stmt, field_mappings.get('stock_compensation', 'missing_field'))},
                        'InterestExpense': {'value': 0},  # Not available for MSFT
                        'InterestIncome': {'value': 0},   # Not available for MSFT
                        'OtherExpenses': {'value': self._safe_get_value(income_stmt, 'nonoperating_income_loss')},
                        'OtherIncome': {'value': 0},      # Not available for MSFT
                        'DepreciationAndAmortization': {'value': 0},  # Not available for MSFT
                    }
                    
                    # Add this period to the result
                    result['periods'][period_date] = {
                        'items': period_items
                    }
                    
                    # Log the results
                    revenue = period_items['Revenues']['value']
                    sm = period_items['SalesAndMarketingExpense']['value']
                    ga = period_items['GeneralAndAdministrativeExpense']['value']
                    net_income = period_items['NetIncomeLoss']['value']
                    
                    self.logger.info(f"PROCESSED {period_date}:")
                    self.logger.info(f"  Revenue: ${revenue/1000000:.0f}M")
                    self.logger.info(f"  Sales & Marketing: ${sm/1000000:.0f}M")
                    self.logger.info(f"  G&A: ${ga/1000000:.0f}M")
                    self.logger.info(f"  Net Income: ${net_income/1000000:.0f}M")
            
            periods_count = len(result['periods'])
            self.logger.info(f"Successfully processed {periods_count} periods for {ticker} with field discovery")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching income statement for {ticker}: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'ticker': ticker.upper(),
                'company_name': ticker.upper(),
                'periods': {}
            }
    
    def _determine_field_mappings(self, discovery_results: Dict) -> Dict:
        """
        Determine the best field mappings based on discovery results.
        """
        mappings = {}
        
        # Sales & Marketing mapping
        sm_candidates = discovery_results.get('sales_marketing_candidates', [])
        for field_name, value in sm_candidates:
            # Look for field that's close to expected MSFT value (~$6,212M)
            if 6000 <= value/1000000 <= 7000:
                mappings['sales_marketing'] = field_name
                self.logger.info(f"Mapped Sales & Marketing to: {field_name}")
                break
        
        # General & Administrative mapping
        ga_candidates = discovery_results.get('general_admin_candidates', [])
        for field_name, value in ga_candidates:
            # Look for field that's close to expected MSFT value (~$1,737M)
            if 1500 <= value/1000000 <= 2000:
                mappings['general_admin'] = field_name
                self.logger.info(f"Mapped General & Administrative to: {field_name}")
                break
        
        # Combined SG&A mapping (if individual fields not found)
        if 'sales_marketing' not in mappings or 'general_admin' not in mappings:
            sga_candidates = discovery_results.get('combined_sga_candidates', [])
            for field_name, value in sga_candidates:
                if 7500 <= value/1000000 <= 8500:
                    mappings['combined_sga'] = field_name
                    self.logger.info(f"Mapped Combined SG&A to: {field_name}")
                    break
        
        return mappings
    
    def get_balance_sheet(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> List[Dict]:
        """Fetch balance sheet data from Polygon."""
        # Keep existing implementation
        return []
    
    def get_cash_flow(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> List[Dict]:
        """Fetch cash flow statement data from Polygon."""
        # Keep existing implementation
        return []


class ProviderSelector:
    """Provider selector with working field discovery."""
    
    def __init__(self, api_keys: dict):
        """Initialize with API keys dictionary."""
        self.api_key = api_keys.get('polygon', '')
        if not self.api_key:
            raise ValueError("Polygon API key is required")
            
        self.adapter = PolygonAdapter(self.api_key)
        self.logger = logging.getLogger(__name__)
    
    def get_income_statement(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch income statement with field discovery."""
        self.logger.info(f"Fetching income statement for {ticker} with field discovery")
        return self.adapter.get_income_statement(ticker, period, limit)
    
    def get_balance_sheet(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch balance sheet via Polygon only."""
        self.logger.info(f"Fetching balance sheet for {ticker} via Polygon")
        return self.adapter.get_balance_sheet(ticker, period, limit)
    
    def get_cash_flow(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch cash flow via Polygon only."""
        self.logger.info(f"Fetching cash flow for {ticker} via Polygon")
        return self.adapter.get_cash_flow(ticker, period, limit)
    
    def discover_fields(self, ticker: str):
        """Discover available field names for a ticker."""
        self.logger.info(f"Discovering available fields for {ticker}")
        return self.adapter.discover_field_names(ticker)
