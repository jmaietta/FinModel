# src/provider_selection.py

"""
Provider selection module for intelligent data source management.

This module implements a provider selection system that automatically chooses
the optimal financial data provider based on data quality analysis.
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any
from enum import Enum

from .adapter.data_adapter import (
    DataAdapter,
    PolygonAdapter,
    SimFinAdapter,
    AlphaVantageAdapter,
    FinnhubAdapter,
    LocalFileAdapter,
    AdapterFactory
)


class ProviderPriority(Enum):
    """Priority levels for data providers."""
    HIGH = 3
    MEDIUM = 2
    LOW = 1


class ProviderSelector:
    """Intelligent provider selection system."""
    
    def __init__(self, api_keys: Dict[str, str], data_dir: str = './data'):
        """Initialize the provider selector.
        
        Args:
            api_keys: Dictionary of API keys for each provider.
            data_dir: Directory for local data storage.
        """
        self.api_keys = api_keys
        self.data_dir = data_dir
        self.logger = logging.getLogger(__name__)
        
        # Default provider priorities
        self.provider_priorities = {
            'simfin': ProviderPriority.HIGH,
            'alphavantage': ProviderPriority.HIGH,
            'polygon': ProviderPriority.MEDIUM,
            'finnhub': ProviderPriority.MEDIUM,
            'local': ProviderPriority.LOW
        }
        
        # Default completeness (for future enhancements)
        self.provider_completeness = {
            'simfin': 85,
            'alphavantage': 75,
            'polygon': 70,
            'finnhub': 65,
            'local': 100
        }
        
        # Initialize adapters
        self.adapters: Dict[str, DataAdapter] = {}
        self._initialize_adapters()
    
    def _initialize_adapters(self):
        """Initialize data adapters for all providers."""
        for provider, api_key in self.api_keys.items():
            if api_key and provider in self.provider_priorities:
                try:
                    if provider == 'local':
                        self.adapters[provider] = LocalFileAdapter(self.data_dir)
                    else:
                        self.adapters[provider] = AdapterFactory.create_adapter(
                            provider, {'api_key': api_key}
                        )
                    self.logger.info(f"Initialized {provider} adapter")
                except Exception as e:
                    self.logger.error(f"Failed to initialize {provider} adapter: {e}")
    
    def select_provider(self, ticker: str, required_fields: Optional[List[str]] = None) -> str:
        """Select the optimal provider based on priority and completeness."""
        # Check local first
        if 'local' in self.adapters:
            local_data = self.adapters['local'].get_income_statement(ticker)
            if local_data and local_data.get('periods'):
                self.logger.info(f"Using local data for {ticker}")
                return 'local'
        
        # Sort by priority
        sorted_providers = sorted(
            self.provider_priorities.items(),
            key=lambda kv: kv[1].value,
            reverse=True
        )
        available = [p for p, _ in sorted_providers if p in self.adapters]
        
        if not available:
            raise ValueError("No data providers available. Please check API keys.")
        
        # If fields required, sort by completeness
        if required_fields:
            available.sort(
                key=lambda p: self.provider_completeness.get(p, 0),
                reverse=True
            )
        
        choice = available[0]
        self.logger.info(f"Selected {choice} as optimal provider for {ticker}")
        return choice
    
    def get_income_statement(
        self, 
        ticker: str, 
        period: str = 'quarterly',
        limit: int = 12
    ) -> Dict[str, Any]:
        """
        Get income statement data, trying each provider in priority order.
        
        Raises:
            RuntimeError: if all providers fail.
        """
        errors: List[str] = []
        
        # Build prioritized provider list
        sorted_providers = [
            provider for provider, _ in
            sorted(self.provider_priorities.items(),
                   key=lambda kv: kv[1].value,
                   reverse=True)
            if provider in self.adapters
        ]
        
        for provider in sorted_providers:
            adapter = self.adapters[provider]
            try:
                self.logger.info(f"Attempting {period} income statement for {ticker} via {provider}")
                data = adapter.get_income_statement(ticker, period, limit)
                
                if data and data.get('periods'):
                    # Cache locally if applicable
                    if provider != 'local' and 'local' in self.adapters:
                        try:
                            self.adapters['local'].save_income_statement(ticker, data)
                            self.logger.info(f"Cached {ticker} income statement locally")
                        except Exception as cache_err:
                            self.logger.warning(f"Failed to cache locally: {cache_err}")
                    return data
                else:
                    raise RuntimeError(f"No periods returned from {provider}")
            
            except Exception as e:
                err_msg = f"{provider} failed: {e}"
                errors.append(err_msg)
                self.logger.warning(err_msg)
        
        # All providers failed
        full_msg = "All providers failed for income statement:\n" + "\n".join(errors)
        self.logger.error(full_msg)
        raise RuntimeError(full_msg)
    
    def update_provider_priorities(self, priorities: Dict[str, ProviderPriority]):
        """Update provider priorities dynamically."""
        for p, pr in priorities.items():
            if p in self.provider_priorities:
                self.provider_priorities[p] = pr
                self.logger.info(f"Updated {p} priority to {pr.name}")
    
    def update_provider_completeness(self, completeness: Dict[str, int]):
        """Update provider completeness scores dynamically."""
        for p, score in completeness.items():
            if p in self.provider_completeness:
                self.provider_completeness[p] = score
                self.logger.info(f"Updated {p} completeness to {score}")
    
    def load_analysis_results(self, analysis_file: str):
        """Load provider analysis results from a JSON file."""
        if not os.path.exists(analysis_file):
            self.logger.warning(f"Analysis file {analysis_file} not found")
            return
        try:
            with open(analysis_file, 'r') as f:
                analysis = json.load(f)
            # Parse and apply updates...
            self.logger.info(f"Loaded provider analysis from {analysis_file}")
        except Exception as e:
            self.logger.error(f"Error loading analysis: {e}")
