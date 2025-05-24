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
        
        # Default provider priorities based on qualitative analysis
        # These can be updated based on empirical data when available
        self.provider_priorities = {
            'simfin': ProviderPriority.HIGH,      # Best for detailed expense breakdown
            'alphavantage': ProviderPriority.HIGH, # Good historical data and standard mapping
            'polygon': ProviderPriority.MEDIUM,    # Good structure but missing some tech items
            'finnhub': ProviderPriority.MEDIUM,    # Fast updates but less historical depth
            'local': ProviderPriority.LOW          # Fallback option
        }
        
        # Provider completeness scores (percentage of required fields available)
        # Based on qualitative analysis, to be updated with empirical data
        self.provider_completeness = {
            'simfin': 85,       # Most detailed breakdown of expenses
            'alphavantage': 75, # Good coverage but missing some breakdowns
            'polygon': 70,      # Missing some tech-specific items
            'finnhub': 65,      # Limited breakdown of expenses
            'local': 100        # Assumes local data is complete if available
        }
        
        # Initialize adapters
        self.adapters = {}
        self._initialize_adapters()
    
    def _initialize_adapters(self):
        """Initialize data adapters for all providers."""
        # Only initialize adapters with valid API keys
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
                    self.logger.error(f"Failed to initialize {provider} adapter: {str(e)}")
    
    def select_provider(self, ticker: str, required_fields: Optional[List[str]] = None) -> str:
        """Select the optimal provider for the given ticker and requirements.
        
        Args:
            ticker: Ticker symbol of the company.
            required_fields: List of specific fields required (optional).
            
        Returns:
            Name of the selected provider.
        """
        # Check if we have local data first
        if 'local' in self.adapters:
            local_adapter = self.adapters['local']
            local_data = local_adapter.get_income_statement(ticker)
            
            # If local data exists and is complete, use it
            if local_data and 'periods' in local_data and local_data['periods']:
                self.logger.info(f"Using local data for {ticker}")
                return 'local'
        
        # Sort providers by priority (highest first)
        sorted_providers = sorted(
            self.provider_priorities.items(),
            key=lambda x: x[1].value,
            reverse=True
        )
        
        # Filter to only include providers with initialized adapters
        available_providers = [
            provider for provider, _ in sorted_providers
            if provider in self.adapters
        ]
        
        if not available_providers:
            raise ValueError("No data providers available. Please check API keys.")
        
        # If specific fields are required, prioritize providers with better completeness
        if required_fields:
            # Sort by completeness for the specific fields needed
            # This is a placeholder for future empirical data
            # For now, we use the general completeness scores
            available_providers.sort(
                key=lambda p: self.provider_completeness.get(p, 0),
                reverse=True
            )
        
        # Return the highest priority available provider
        selected_provider = available_providers[0]
        self.logger.info(f"Selected {selected_provider} as optimal provider for {ticker}")
        return selected_provider
    
    def get_income_statement(self, 
                           ticker: str, 
                           period: str = 'quarterly',
                           limit: int = 12) -> Dict:
        """Get income statement using the optimal provider.
        
        Args:
            ticker: Ticker symbol of the company.
            period: 'quarterly' or 'annual'.
            limit: Maximum number of periods to return.
            
        Returns:
            Income statement data.
        """
        # Select the optimal provider
        provider = self.select_provider(ticker)
        
        # Get the adapter
        adapter = self.adapters.get(provider)
        if not adapter:
            raise ValueError(f"Selected provider {provider} has no initialized adapter")
        
        # Get income statement data
        self.logger.info(f"Retrieving {period} income statement for {ticker} using {provider}")
        income_statement = adapter.get_income_statement(ticker, period, limit)
        
        # If data is successfully retrieved and not from local storage,
        # save a copy to local storage for future use
        if (income_statement and 'periods' in income_statement and 
            income_statement['periods'] and provider != 'local' and
            'local' in self.adapters):
            
            local_adapter = self.adapters['local']
            local_adapter.save_income_statement(ticker, income_statement)
            self.logger.info(f"Saved {ticker} income statement to local storage")
        
        return income_statement
    
    def update_provider_priorities(self, priorities: Dict[str, ProviderPriority]):
        """Update provider priorities based on new data or analysis.
        
        Args:
            priorities: Dictionary mapping provider names to priority levels.
        """
        for provider, priority in priorities.items():
            if provider in self.provider_priorities:
                self.provider_priorities[provider] = priority
                self.logger.info(f"Updated {provider} priority to {priority.name}")
    
    def update_provider_completeness(self, completeness: Dict[str, int]):
        """Update provider completeness scores based on empirical data.
        
        Args:
            completeness: Dictionary mapping provider names to completeness scores (0-100).
        """
        for provider, score in completeness.items():
            if provider in self.provider_completeness:
                self.provider_completeness[provider] = score
                self.logger.info(f"Updated {provider} completeness score to {score}")
    
    def load_analysis_results(self, analysis_file: str):
        """Load provider analysis results from a file.
        
        Args:
            analysis_file: Path to the analysis results file.
        """
        if not os.path.exists(analysis_file):
            self.logger.warning(f"Analysis file {analysis_file} not found")
            return
        
        try:
            with open(analysis_file, 'r') as f:
                analysis = json.load(f)
            
            if 'provider_scores' in analysis:
                # Update completeness scores
                completeness_updates = {}
                for provider, scores in analysis['provider_scores'].items():
                    if 'completeness_score' in scores:
                        completeness_updates[provider] = scores['completeness_score']
                
                if completeness_updates:
                    self.update_provider_completeness(completeness_updates)
                
                # Update priorities based on overall scores
                priority_updates = {}
                for provider, scores in analysis['provider_scores'].items():
                    if 'overall_score' in scores:
                        # Assign priority based on overall score
                        if scores['overall_score'] >= 80:
                            priority_updates[provider] = ProviderPriority.HIGH
                        elif scores['overall_score'] >= 60:
                            priority_updates[provider] = ProviderPriority.MEDIUM
                        else:
                            priority_updates[provider] = ProviderPriority.LOW
                
                if priority_updates:
                    self.update_provider_priorities(priority_updates)
            
            self.logger.info(f"Loaded provider analysis results from {analysis_file}")
            
        except Exception as e:
            self.logger.error(f"Error loading analysis results: {str(e)}")
