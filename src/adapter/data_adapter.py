"""
Enhanced data adapter with intelligent field mapping that can handle field name variations.
"""
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import re


class PolygonAdapter:
    """Enhanced Polygon.io API adapter with intelligent field mapping."""
    
    def __init__(self, api_key: str):
        """Initialize Polygon adapter with API key."""
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.logger = logging.getLogger(__name__)
        
        # Smart field mapping - each template field maps to multiple possible Polygon field names
        self.field_mappings = {
            'Revenues': [
                'revenues', 'total_revenues', 'revenue', 'total_revenue', 'net_revenues'
            ],
            'CostOfGoodsSold': [
                'cost_of_revenue', 'cost_of_goods_sold', 'cost_of_sales', 'costs_of_revenue'
            ],
            'GrossProfit': [
                'gross_profit', 'gross_income'
            ],
            'SalesAndMarketingExpense': [
                'sales_and_marketing_expenses', 'sales_marketing_expenses', 'marketing_expenses',
                'sales_and_marketing', 'selling_and_marketing_expenses', 'selling_marketing_expenses'
            ],
            'ResearchAndDevelopmentExpense': [
                'research_and_development', 'research_development', 'rd_expenses', 'r_and_d'
            ],
            'GeneralAndAdministrativeExpense': [
                'general_and_administrative_expenses', 'general_administrative_expenses',
                'general_and_admin_expenses', 'ga_expenses', 'administrative_expenses'
            ],
            'StockBasedCompensation': [
                'stock_based_compensation', 'share_based_compensation', 'equity_compensation',
                'benefits_costs_expenses', 'employee_stock_compensation'
            ],
            'OperatingExpenses': [
                'operating_expenses', 'total_operating_expenses', 'operating_costs'
            ],
            'OperatingIncomeLoss': [
                'operating_income_loss', 'operating_income', 'income_from_operations'
            ],
            'InterestExpense': [
                'interest_expense', 'interest_expenses', 'financial_expenses'
            ],
            'InterestIncome': [
                'interest_income', 'interest_and_investment_income', 'investment_income'
            ],
            'OtherExpenses': [
                'other_expenses', 'nonoperating_income_loss', 'other_operating_expenses',
                'miscellaneous_expenses'
            ],
            'OtherIncome': [
                'other_income', 'other_comprehensive_income_loss', 'miscellaneous_income',
                'nonoperating_income'
            ],
            'DepreciationAndAmortization': [
                'depreciation_and_amortization', 'depreciation_amortization', 'da_expenses'
            ],
            'IncomeLossBeforeIncomeTaxes': [
                'income_loss_from_continuing_operations_before_tax', 'pretax_income',
                'income_before_taxes', 'earnings_before_taxes'
            ],
            'IncomeTaxExpenseBenefit': [
                'income_tax_expense_benefit', 'income_tax_expense', 'tax_expense',
                'provision_for_income_taxes'
            ],
            'NetIncomeLoss': [
                'net_income_loss', 'net_income', 'net_earnings', 'bottom_line'
            ],
            'WeightedAverageSharesOutstandingDiluted': [
                'weighted_average_shares_outstanding_diluted', 'diluted_shares_outstanding',
                'diluted_average_shares', 'shares_outstanding_diluted', 'diluted_shares'
            ]
        }
        
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
    
    def _intelligent_field_mapping(self, available_fields: List[str], template_field: str) -> Optional[str]:
        """
        Intelligently map template field to available Polygon field using multiple strategies.
        
        Args:
            available_fields: List of field names available from Polygon API
            template_field: The institutional template field name we're trying to map
            
        Returns:
            Best matching Polygon field name, or None if no match found
        """
        if template_field not in self.field_mappings:
            return None
        
        possible_matches = self.field_mappings[template_field]
        
        # Strategy 1: Exact match
        for possible_field in possible_matches:
            if possible_field in available_fields:
                self.logger.debug(f"Exact match: {template_field} -> {possible_field}")
                return possible_field
        
        # Strategy 2: Case-insensitive match
        available_fields_lower = [f.lower() for f in available_fields]
        for possible_field in possible_matches:
            if possible_field.lower() in available_fields_lower:
                # Find the original case version
                for original_field in available_fields:
                    if original_field.lower() == possible_field.lower():
                        self.logger.debug(f"Case-insensitive match: {template_field} -> {original_field}")
                        return original_field
        
        # Strategy 3: Partial match (contains key terms)
        key_terms = self._extract_key_terms(template_field)
        for available_field in available_fields:
            available_field_lower = available_field.lower()
            matches = 0
            for term in key_terms:
                if term in available_field_lower:
                    matches += 1
            
            # If we match most key terms, consider it a good match
            if matches >= len(key_terms) * 0.6:  # 60% of terms must match
                self.logger.debug(f"Partial match: {template_field} -> {available_field} (matched {matches}/{len(key_terms)} terms)")
                return available_field
        
        # Strategy 4: Fuzzy matching for shares
        if 'shares' in template_field.lower() and 'diluted' in template_field.lower():
            for available_field in available_fields:
                if 'shares' in available_field.lower() and 'diluted' in available_field.lower():
                    self.logger.debug(f"Fuzzy shares match: {template_field} -> {available_field}")
                    return available_field
        
        self.logger.warning(f"No mapping found for {template_field} in available fields: {available_fields}")
        return None
    
    def _extract_key_terms(self, field_name: str) -> List[str]:
        """Extract key terms from a field name for matching."""
        # Remove common words and split on boundaries
        field_lower = field_name.lower()
        # Split on capital letters, underscores, spaces, and remove common words
        terms = re.findall(r'[a-z]+', field_lower)
        
        # Remove very common words that don't help with matching
        stop_words = {'and', 'of', 'the', 'expense', 'income', 'loss', 'benefit', 'outstanding'}
        key_terms = [term for term in terms if term not in stop_words and len(term) > 2]
        
        return key_terms
    
    def _create_comprehensive_field_map(self, available_fields: List[str]) -> Dict[str, str]:
        """Create a comprehensive mapping from template fields to Polygon fields."""
        field_map = {}
        
        for template_field in self.field_mappings.keys():
            polygon_field = self._intelligent_field_mapping(available_fields, template_field)
            if polygon_field:
                field_map[template_field] = polygon_field
            else:
                self.logger.warning(f"Could not map template field: {template_field}")
        
        return field_map
    
    def get_income_statement(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> Dict:
        """
        Fetch income statement data with intelligent field mapping.
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
            
            # Initialize the result
            result = {
                'ticker': ticker.upper(),
                'company_name': ticker.upper(),
                'periods': {}
            }
            
            # Get available fields from first result for intelligent mapping
            if data['results'] and 'financials' in data['results'][0] and 'income_statement' in data['results'][0]['financials']:
                first_income_stmt = data['results'][0]['financials']['income_statement']
                available_fields = list(first_income_stmt.keys())
                
                self.logger.info(f"Available Polygon fields for {ticker}: {available_fields}")
                
                # Create intelligent field mapping
                field_map = self._create_comprehensive_field_map(available_fields)
                self.logger.info(f"Created field mapping: {field_map}")
            else:
                self.logger.error("No income statement data in first result")
                return result
            
            # Process each period using the intelligent mapping
            for api_result in data.get('results', []):
                if 'financials' in api_result and 'income_statement' in api_result['financials']:
                    income_stmt = api_result['financials']['income_statement']
                    period_date = api_result.get('end_date', '')
                    
                    if not period_date:
                        continue
                    
                    # Create period items using intelligent mapping
                    period_items = {}
                    
                    for template_field, polygon_field in field_map.items():
                        value = self._safe_get_value(income_stmt, polygon_field)
                        period_items[template_field] = {'value': value}
                        
                        # Log significant values for debugging
                        if value != 0:
                            self.logger.debug(f"  {template_field} ({polygon_field}): ${value:,.0f}")
                    
                    # Add this period to the result
                    result['periods'][period_date] = {
                        'items': period_items
                    }
                    
                    # Log summary for this period
                    revenue = period_items.get('Revenues', {}).get('value', 0)
                    net_income = period_items.get('NetIncomeLoss', {}).get('value', 0)
                    shares = period_items.get('WeightedAverageSharesOutstandingDiluted', {}).get('value', 0)
                    
                    self.logger.info(f"Processed {period_date}: Revenue=${revenue:,.0f}, Net Income=${net_income:,.0f}, Diluted Shares={shares:,.0f}")
            
            periods_count = len(result['periods'])
            self.logger.info(f"Successfully processed {periods_count} periods for {ticker} with intelligent mapping")
            
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
    
    def suggest_field_mappings(self, ticker: str) -> Dict[str, List[str]]:
        """
        Analyze available fields and suggest mappings for missing template fields.
        This could be used for ML training data or manual review.
        """
        try:
            data = self._make_request(f"/vX/reference/financials", {
                'ticker': ticker.upper(),
                'timeframe': 'quarterly',
                'limit': 1
            })
            
            if not data or not data.get('results'):
                return {}
            
            result = data['results'][0]
            if 'financials' not in result or 'income_statement' not in result['financials']:
                return {}
            
            available_fields = list(result['financials']['income_statement'].keys())
            suggestions = {}
            
            # For each template field, suggest possible matches
            for template_field in self.field_mappings.keys():
                current_mapping = self._intelligent_field_mapping(available_fields, template_field)
                
                # Find other potential matches
                key_terms = self._extract_key_terms(template_field)
                potential_matches = []
                
                for available_field in available_fields:
                    score = 0
                    for term in key_terms:
                        if term in available_field.lower():
                            score += 1
                    
                    if score > 0:
                        potential_matches.append({
                            'field': available_field,
                            'score': score,
                            'current_mapping': available_field == current_mapping
                        })
                
                # Sort by score
                potential_matches.sort(key=lambda x: x['score'], reverse=True)
                suggestions[template_field] = potential_matches
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error suggesting mappings for {ticker}: {str(e)}")
            return {}
    
    def debug_available_fields(self, ticker: str, period: str = 'quarterly', limit: int = 1) -> Dict:
        """Enhanced debug method with intelligent mapping analysis."""
        try:
            debug_info = super().debug_available_fields(ticker, period, limit)
            
            # Add intelligent mapping analysis
            if 'income_statement_fields' in debug_info:
                available_fields = debug_info['income_statement_fields']
                field_map = self._create_comprehensive_field_map(available_fields)
                suggestions = self.suggest_field_mappings(ticker)
                
                debug_info['intelligent_mapping'] = field_map
                debug_info['mapping_suggestions'] = suggestions
            
            return debug_info
            
        except Exception as e:
            self.logger.error(f"Error in enhanced debug for {ticker}: {str(e)}")
            return {}
    
    def get_balance_sheet(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> List[Dict]:
        """Fetch balance sheet data from Polygon."""
        # Keep existing implementation
        try:
            timeframe = 'quarterly' if period.lower() == 'quarterly' else 'annual'
            
            endpoint = f"/vX/reference/financials"
            params = {
                'ticker': ticker.upper(),
                'timeframe': timeframe,
                'limit': limit
            }
            
            self.logger.info(f"Fetching {period} balance sheet for {ticker}")
            data = self._make_request(endpoint, params)
            
            if not data or 'results' not in data:
                self.logger.warning(f"No balance sheet data found for {ticker}")
                return []
            
            formatted_data = []
            for result in data.get('results', []):
                if 'financials' in result and 'balance_sheet' in result['financials']:
                    balance_sheet = result['financials']['balance_sheet']
                    
                    formatted_item = {
                        'ticker': ticker.upper(),
                        'period_end_date': result.get('end_date', ''),
                        'filing_date': result.get('filing_date', ''),
                        'timeframe': result.get('timeframe', ''),
                        'total_assets': self._safe_get_value(balance_sheet, 'assets'),
                        'current_assets': self._safe_get_value(balance_sheet, 'current_assets'),
                        'total_liabilities': self._safe_get_value(balance_sheet, 'liabilities'),
                        'current_liabilities': self._safe_get_value(balance_sheet, 'current_liabilities'),
                        'total_equity': self._safe_get_value(balance_sheet, 'equity'),
                        'retained_earnings': self._safe_get_value(balance_sheet, 'equity_attributable_to_parent'),
                    }
                    formatted_data.append(formatted_item)
            
            self.logger.info(f"Successfully fetched {len(formatted_data)} balance sheet records for {ticker}")
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Error fetching balance sheet for {ticker}: {str(e)}")
            return []
    
    def get_cash_flow(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> List[Dict]:
        """Fetch cash flow statement data from Polygon."""
        # Keep existing implementation
        try:
            timeframe = 'quarterly' if period.lower() == 'quarterly' else 'annual'
            
            endpoint = f"/vX/reference/financials"
            params = {
                'ticker': ticker.upper(),
                'timeframe': timeframe,
                'limit': limit
            }
            
            self.logger.info(f"Fetching {period} cash flow for {ticker}")
            data = self._make_request(endpoint, params)
            
            if not data or 'results' not in data:
                self.logger.warning(f"No cash flow data found for {ticker}")
                return []
            
            formatted_data = []
            for result in data.get('results', []):
                if 'financials' in result and 'cash_flow_statement' in result['financials']:
                    cash_flow = result['financials']['cash_flow_statement']
                    
                    formatted_item = {
                        'ticker': ticker.upper(),
                        'period_end_date': result.get('end_date', ''),
                        'filing_date': result.get('filing_date', ''),
                        'timeframe': result.get('timeframe', ''),
                        'operating_cash_flow': self._safe_get_value(cash_flow, 'net_cash_flow_from_operating_activities'),
                        'investing_cash_flow': self._safe_get_value(cash_flow, 'net_cash_flow_from_investing_activities'),
                        'financing_cash_flow': self._safe_get_value(cash_flow, 'net_cash_flow_from_financing_activities'),
                        'free_cash_flow': self._safe_get_value(cash_flow, 'net_cash_flow'),
                    }
                    formatted_data.append(formatted_item)
            
            self.logger.info(f"Successfully fetched {len(formatted_data)} cash flow records for {ticker}")
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Error fetching cash flow for {ticker}: {str(e)}")
            return []


class ProviderSelector:
    """Provider selector that returns data in institutional template format."""
    
    def __init__(self, api_keys: dict):
        """Initialize with API keys dictionary."""
        self.api_key = api_keys.get('polygon', '')
        if not self.api_key:
            raise ValueError("Polygon API key is required")
            
        self.adapter = PolygonAdapter(self.api_key)
        self.logger = logging.getLogger(__name__)
    
    def get_income_statement(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch income statement with intelligent field mapping."""
        self.logger.info(f"Fetching quarterly income statement for {ticker} via Polygon")
        return self.adapter.get_income_statement(ticker, period, limit)
    
    def get_balance_sheet(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch balance sheet via Polygon only."""
        self.logger.info(f"Fetching balance sheet for {ticker} via Polygon")
        return self.adapter.get_balance_sheet(ticker, period, limit)
    
    def get_cash_flow(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch cash flow via Polygon only."""
        self.logger.info(f"Fetching cash flow for {ticker} via Polygon")
        return self.adapter.get_cash_flow(ticker, period, limit)
    
    def debug_fields(self, ticker: str, period: str = 'quarterly'):
        """Debug available fields with intelligent mapping suggestions."""
        self.logger.info(f"Debugging available fields for {ticker}")
        return self.adapter.debug_available_fields(ticker, period)
    
    def suggest_mappings(self, ticker: str):
        """Get mapping suggestions for ML training or manual review."""
        return self.adapter.suggest_field_mappings(ticker)
