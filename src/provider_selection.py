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
            
            # Use existing Polygon adapter
            periods_list = self.polygon_adapter.get_income_statement(ticker, period, limit)
            
            if not periods_list:
                raise RuntimeError(f"No income statement data returned for {ticker}")
            
            # Transform list to dictionary format that Excel generator expects
            # Convert list of period data to dictionary with period dates as keys
            periods_dict = {}
            for period_data in periods_list:
                period_key = period_data.get('period_end_date', f'period_{len(periods_dict)}')
                periods_dict[period_key] = period_data
            
            # Return in expected format
            return {
                'ticker': ticker,
                'provider': 'polygon',
                'periods': periods_dict,  # Now a dictionary instead of list
                'metadata': {
                    'period_type': period,
                    'limit': limit,
                    'total_results': len(periods_dict)
                }
            }
            
        except Exception as e:
            error_msg = f"Polygon API failed for {ticker}: {e}"
            self.logger.error(error_msg)
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
                'provider': 'polygon',
                'periods': periods_dict,  # Dictionary format
                'metadata': {
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
                'provider': 'polygon',
                'periods': periods_dict,  # Dictionary format
                'metadata': {
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
