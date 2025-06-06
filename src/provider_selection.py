# src/provider_selection.py

"""
Provider selection module for Polygon financial data.

This module implements a simplified provider selection system that uses
only Polygon as the financial data provider.
"""

import logging
from typing import Dict, Any, Optional

from .adapter.data_adapter import PolygonAdapter


class ProviderSelector:
    """Simplified provider selection system for Polygon only."""
    
    def __init__(self, api_keys: Dict[str, str]):
        """Initialize the provider selector.
        
        Args:
            api_keys: Dictionary of API keys (should contain 'polygon' key).
        """
        self.api_keys = api_keys
        self.logger = logging.getLogger(__name__)
        
        if 'polygon' not in api_keys or not api_keys['polygon']:
            raise ValueError("Polygon API key is required")
        
        # Initialize Polygon adapter
        self.polygon_adapter = PolygonAdapter(api_keys['polygon'])
        self.logger.info("Initialized Polygon provider selector")
    
    def select_provider(self, ticker: str, required_fields: Optional[list] = None) -> str:
        """Select the optimal provider (always returns 'polygon')."""
        self.logger.info(f"Selected polygon as provider for {ticker}")
        return 'polygon'
    
    def get_income_statement(
        self, 
        ticker: str, 
        period: str = 'quarterly',
        limit: int = 12
    ) -> Dict[str, Any]:
        """
        Get income statement data from Polygon.
        
        Args:
            ticker: Stock ticker symbol
            period: 'quarterly' or 'annual'
            limit: Number of periods to retrieve
            
        Returns:
            Dictionary containing income statement data in expected format
            
        Raises:
            RuntimeError: if Polygon API fails
        """
        try:
            self.logger.info(f"Fetching {period} income statement for {ticker} via Polygon")
            
            # Get data from Polygon adapter (now returns the correct institutional format)
            adapter_result = self.polygon_adapter.get_income_statement(ticker, period, limit)
            
            # Log what we received for debugging
            self.logger.info(f"Adapter returned type: {type(adapter_result)}")
            
            if not adapter_result:
                raise RuntimeError(f"No income statement data returned for {ticker}")
            
            # The new adapter already returns the correct format, so we can return it directly
            # But we'll add some metadata for compatibility
            if isinstance(adapter_result, dict) and 'periods' in adapter_result:
                self.logger.info(f"Received correctly formatted data with {len(adapter_result['periods'])} periods")
                
                # Add metadata for compatibility with any downstream processing
                result = {
                    'ticker': adapter_result.get('ticker', ticker),
                    'company_name': adapter_result.get('company_name', ticker),
                    'periods': adapter_result['periods'],  # This is already in the correct format
                    'metadata': {
                        'provider': 'polygon',
                        'period_type': period,
                        'limit': limit,
                        'total_results': len(adapter_result['periods'])
                    }
                }
                
                return result
            else:
                # Handle case where adapter returns unexpected format
                self.logger.error(f"Unexpected data format from adapter: {type(adapter_result)}")
                raise RuntimeError(f"Invalid data format returned for {ticker}")
            
        except Exception as e:
            error_msg = f"Polygon API failed for {ticker}: {e}"
            self.logger.error(error_msg)
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            raise RuntimeError(error_msg)
    
    def get_balance_sheet(
        self, 
        ticker: str, 
        period: str = 'quarterly',
        limit: int = 12
    ) -> Dict[str, Any]:
        """
        Get balance sheet data from Polygon.
        
        Args:
            ticker: Stock ticker symbol
            period: 'quarterly' or 'annual'
            limit: Number of periods to retrieve
            
        Returns:
            Dictionary containing balance sheet data
            
        Raises:
            RuntimeError: if Polygon API fails
        """
        try:
            self.logger.info(f"Fetching {period} balance sheet for {ticker} via Polygon")
            
            # Balance sheet still returns list format, so we transform it
            periods_list = self.polygon_adapter.get_balance_sheet(ticker, period, limit)
            
            if not periods_list:
                raise RuntimeError(f"No balance sheet data returned for {ticker}")
            
            # Transform list to dictionary format
            periods_dict = {}
            for period_data in periods_list:
                period_key = period_data.get('period_end_date', f'period_{len(periods_dict)}')
                periods_dict[period_key] = period_data
            
            return {
                'ticker': ticker,
                'company_name': ticker,
                'periods': periods_dict,  # Dictionary format
                'metadata': {
                    'provider': 'polygon',
                    'period_type': period,
                    'limit': limit,
                    'total_results': len(periods_dict)
                }
            }
            
        except Exception as e:
            error_msg = f"Polygon API failed for balance sheet {ticker}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def get_cash_flow(
        self, 
        ticker: str, 
        period: str = 'quarterly',
        limit: int = 12
    ) -> Dict[str, Any]:
        """
        Get cash flow data from Polygon.
        
        Args:
            ticker: Stock ticker symbol
            period: 'quarterly' or 'annual'
            limit: Number of periods to retrieve
            
        Returns:
            Dictionary containing cash flow data
            
        Raises:
            RuntimeError: if Polygon API fails
        """
        try:
            self.logger.info(f"Fetching {period} cash flow for {ticker} via Polygon")
            
            # Cash flow still returns list format, so we transform it
            periods_list = self.polygon_adapter.get_cash_flow(ticker, period, limit)
            
            if not periods_list:
                raise RuntimeError(f"No cash flow data returned for {ticker}")
            
            # Transform list to dictionary format
            periods_dict = {}
            for period_data in periods_list:
                period_key = period_data.get('period_end_date', f'period_{len(periods_dict)}')
                periods_dict[period_key] = period_data
            
            return {
                'ticker': ticker,
                'company_name': ticker,
                'periods': periods_dict,  # Dictionary format
                'metadata': {
                    'provider': 'polygon',
                    'period_type': period,
                    'limit': limit,
                    'total_results': len(periods_dict)
                }
            }
            
        except Exception as e:
            error_msg = f"Polygon API failed for cash flow {ticker}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def update_provider_priorities(self, priorities: dict):
        """No-op for simplified version."""
        self.logger.info("Provider priorities update ignored (Polygon only)")
        pass
    
    def update_provider_completeness(self, completeness: dict):
        """No-op for simplified version."""
        self.logger.info("Provider completeness update ignored (Polygon only)")
        pass
    
    def load_analysis_results(self, analysis_file: str):
        """No-op for simplified version."""
        self.logger.info(f"Analysis file loading ignored (Polygon only): {analysis_file}")
        pass
