"""
Taxonomy mapping module for standardizing financial concepts.

This module provides functionality for mapping company-specific
taxonomy extensions to standard financial concepts.
"""
import logging
from typing import Dict, List, Optional, Union, Any


class TaxonomyMapper:
    """Maps company-specific taxonomy extensions to standard concepts."""
    
    def __init__(self):
        """Initialize taxonomy mapper."""
        self.logger = logging.getLogger(__name__)
        
        # Standard mapping of common income statement concepts
        self.income_stmt_mapping = {
            # Revenue concepts
            'Revenue': 'Revenues',
            'SalesRevenueNet': 'Revenues',
            'RevenueFromContractWithCustomerExcludingAssessedTax': 'Revenues',
            'RevenueFromContractWithCustomer': 'Revenues',
            
            # Cost of revenue concepts
            'CostOfGoodsAndServicesSold': 'CostOfRevenue',
            'CostOfRevenue': 'CostOfRevenue',
            'CostOfServices': 'CostOfRevenue',
            'CostOfGoodsSold': 'CostOfRevenue',
            
            # Gross profit concepts
            'GrossProfit': 'GrossProfit',
            
            # Operating expense concepts
            'OperatingExpenses': 'OperatingExpenses',
            'SellingGeneralAndAdministrativeExpense': 'OperatingExpenses',
            'ResearchAndDevelopmentExpense': 'OperatingExpenses',
            
            # Operating income concepts
            'OperatingIncomeLoss': 'OperatingIncomeLoss',
            'IncomeLossFromOperations': 'OperatingIncomeLoss',
            
            # Net income concepts
            'NetIncomeLoss': 'NetIncomeLoss',
            'ProfitLoss': 'NetIncomeLoss',
            
            # EPS concepts
            'EarningsPerShareBasic': 'EarningsPerShareBasic',
            'EarningsPerShareDiluted': 'EarningsPerShareDiluted'
        }
        
        # Technology sector specific mappings
        self.tech_sector_mapping = {
            # Cloud revenue concepts
            'CloudServicesRevenue': 'CloudRevenue',
            'HostedSoftwareAndSolutionsRevenue': 'CloudRevenue',
            'SoftwareAsAServiceRevenue': 'CloudRevenue',
            
            # Subscription revenue concepts
            'SubscriptionRevenue': 'SubscriptionRevenue',
            'RecurringRevenue': 'SubscriptionRevenue',
            
            # Hardware revenue concepts
            'HardwareRevenue': 'HardwareRevenue',
            'ProductRevenue': 'HardwareRevenue',
            
            # R&D expense concepts
            'ResearchAndDevelopmentExpense': 'ResearchAndDevelopmentExpense'
        }
    
    def map_income_statement(self, income_statement: Dict) -> Dict:
        """Map income statement concepts to standard taxonomy.
        
        Args:
            income_statement: Income statement data to map.
            
        Returns:
            Mapped income statement data.
        """
        result = {
            'ticker': income_statement.get('ticker', ''),
            'company_name': income_statement.get('company_name', ''),
            'periods': {}
        }
        
        # Process each period
        for period_key, period_data in income_statement.get('periods', {}).items():
            # Copy period metadata
            result['periods'][period_key] = {
                'period_end_date': period_data.get('period_end_date', ''),
                'period_type': period_data.get('period_type', ''),
                'currency': period_data.get('currency', 'USD'),
                'items': {}
            }
            
            # Map items
            items = period_data.get('items', {})
            mapped_items = {}
            
            for item_key, item_data in items.items():
                # Check if this item maps to a standard concept
                standard_key = self._get_standard_concept(item_key)
                
                if standard_key:
                    # If this standard concept already exists, sum the values
                    if standard_key in mapped_items:
                        mapped_items[standard_key]['value'] += item_data.get('value', 0)
                    else:
                        mapped_items[standard_key] = {
                            'value': item_data.get('value', 0),
                            'unit': item_data.get('unit', 'USD')
                        }
                else:
                    # Keep the original item if no mapping exists
                    mapped_items[item_key] = {
                        'value': item_data.get('value', 0),
                        'unit': item_data.get('unit', 'USD')
                    }
            
            # Add mapped items to result
            result['periods'][period_key]['items'] = mapped_items
        
        return result
    
    def _get_standard_concept(self, concept: str) -> Optional[str]:
        """Get standard concept for a given concept.
        
        Args:
            concept: Original concept name.
            
        Returns:
            Standard concept name, or None if no mapping exists.
        """
        # Check income statement mapping
        if concept in self.income_stmt_mapping:
            return self.income_stmt_mapping[concept]
        
        # Check technology sector mapping
        if concept in self.tech_sector_mapping:
            return self.tech_sector_mapping[concept]
        
        # No mapping found
        return None
