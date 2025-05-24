"""
Validation module for ensuring data quality.

This module provides functionality for validating financial data
to ensure it meets quality standards.
"""
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime


class DataValidator:
    """Validates financial data."""
    
    def __init__(self):
        """Initialize data validator."""
        self.logger = logging.getLogger(__name__)
    
    def validate_income_statement(self, income_statement: Dict) -> Dict:
        """Validate income statement data.
        
        Args:
            income_statement: Income statement data to validate.
            
        Returns:
            Validation result with issues and warnings.
        """
        result = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        # Check basic structure
        if not income_statement:
            result['valid'] = False
            result['issues'].append('Income statement data is empty')
            return result
        
        # Check required fields
        required_fields = ['ticker', 'periods']
        for field in required_fields:
            if field not in income_statement:
                result['valid'] = False
                result['issues'].append(f'Missing required field: {field}')
        
        # If missing required fields, return early
        if not result['valid']:
            return result
        
        # Check periods
        periods = income_statement.get('periods', {})
        if not periods:
            result['valid'] = False
            result['issues'].append('No periods found in income statement')
            return result
        
        # Validate each period
        for period_key, period_data in periods.items():
            period_issues = self._validate_period(period_key, period_data)
            if period_issues:
                result['valid'] = False
                result['issues'].extend(period_issues)
        
        # Check for consistency across periods
        consistency_warnings = self._check_period_consistency(periods)
        if consistency_warnings:
            result['warnings'].extend(consistency_warnings)
        
        return result
    
    def _validate_period(self, period_key: str, period_data: Dict) -> List[str]:
        """Validate a single period of income statement data.
        
        Args:
            period_key: Period key.
            period_data: Period data to validate.
            
        Returns:
            List of validation issues.
        """
        issues = []
        
        # Check required fields
        required_fields = ['period_end_date', 'items']
        for field in required_fields:
            if field not in period_data:
                issues.append(f'Period {period_key}: Missing required field: {field}')
        
        # If missing required fields, return early
        if issues:
            return issues
        
        # Check items
        items = period_data.get('items', {})
        if not items:
            issues.append(f'Period {period_key}: No items found')
            return issues
        
        # Check key metrics
        key_metrics = ['Revenues', 'NetIncomeLoss']
        for metric in key_metrics:
            if metric not in items:
                issues.append(f'Period {period_key}: Missing key metric: {metric}')
        
        # Validate item values
        for item_key, item_data in items.items():
            if not isinstance(item_data, dict):
                issues.append(f'Period {period_key}: Item {item_key} is not a dictionary')
                continue
            
            if 'value' not in item_data:
                issues.append(f'Period {period_key}: Item {item_key} is missing value')
        
        return issues
    
    def _check_period_consistency(self, periods: Dict) -> List[str]:
        """Check consistency across periods.
        
        Args:
            periods: Dictionary of periods to check.
            
        Returns:
            List of consistency warnings.
        """
        warnings = []
        
        # Check for consistent metrics across periods
        all_metrics = set()
        period_metrics = {}
        
        for period_key, period_data in periods.items():
            items = period_data.get('items', {})
            period_metrics[period_key] = set(items.keys())
            all_metrics.update(items.keys())
        
        # Check if any periods are missing metrics that others have
        for period_key, metrics in period_metrics.items():
            missing_metrics = all_metrics - metrics
            if missing_metrics:
                warnings.append(f'Period {period_key} is missing metrics that other periods have: {", ".join(missing_metrics)}')
        
        return warnings


class SchemaValidator:
    """Validates data against a schema."""
    
    def __init__(self):
        """Initialize schema validator."""
        self.logger = logging.getLogger(__name__)
    
    def validate(self, data: Dict, schema: Dict) -> Dict:
        """Validate data against a schema.
        
        Args:
            data: Data to validate.
            schema: Schema to validate against.
            
        Returns:
            Validation result with issues.
        """
        result = {
            'valid': True,
            'issues': []
        }
        
        # This is a placeholder for a more complex schema validation
        # In a real-world scenario, we would use a library like jsonschema
        
        # Check required fields
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in data:
                result['valid'] = False
                result['issues'].append(f'Missing required field: {field}')
        
        # Check field types
        properties = schema.get('properties', {})
        for field, field_schema in properties.items():
            if field in data:
                field_type = field_schema.get('type')
                if field_type and not self._check_type(data[field], field_type):
                    result['valid'] = False
                    result['issues'].append(f'Field {field} has wrong type. Expected {field_type}.')
        
        return result
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if a value has the expected type.
        
        Args:
            value: Value to check.
            expected_type: Expected type.
            
        Returns:
            True if the value has the expected type, False otherwise.
        """
        if expected_type == 'string':
            return isinstance(value, str)
        elif expected_type == 'number':
            return isinstance(value, (int, float))
        elif expected_type == 'integer':
            return isinstance(value, int)
        elif expected_type == 'boolean':
            return isinstance(value, bool)
        elif expected_type == 'array':
            return isinstance(value, list)
        elif expected_type == 'object':
            return isinstance(value, dict)
        else:
            return True  # Unknown type, assume valid
