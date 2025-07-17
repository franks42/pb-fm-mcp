"""
Configuration-Driven API Transformation Engine

This module implements a declarative transformation system that uses YAML configuration
to define the complete data flow from PB-API responses to standardized MCP responses.

The data flow follows the pattern:
target_path ← source_path ← PB-API-json-return ← PB-API-URL + PB-API-parameter(s)

Flow breakdown:
1. PB-API-URL + PB-API-parameter(s) → Make HTTP request to Provenance Blockchain API
2. PB-API-json-return → Receive raw JSON response from PB API  
3. source_path ← Extract specific field/value from the raw JSON response
4. target_path ← Transform and map extracted value to standardized field name
"""

import yaml
import re
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

import utils


class ConfigDrivenTransformer:
    """
    Transforms API responses based on declarative YAML configuration.
    
    Supports:
    - Direct field mappings with various transforms
    - Array processing with item-level mappings
    - Calculated fields with formulas
    - Dynamic field naming based on data values
    - Complex nested data extraction
    """
    
    def __init__(self, config_path: str = "src/mcpserver/docs/pb_api_endpoint_mappings.yaml"):
        """Initialize transformer with configuration file."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.transforms = self.config.get('transforms', {})
        
    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def get_endpoint_config(self, endpoint_name: str) -> Dict[str, Any]:
        """Get configuration for specific endpoint."""
        endpoints = self.config.get('endpoints', {})
        if endpoint_name not in endpoints:
            raise ValueError(f"Endpoint '{endpoint_name}' not found in configuration")
        return endpoints[endpoint_name]
    
    def transform_response(
        self, 
        endpoint_name: str, 
        raw_response: Dict[str, Any], 
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Transform raw API response using endpoint configuration.
        
        IMPORTANT: Automatically expands all base64-encoded values in the response
        before transformation to ensure hidden data is captured and available
        for source path extraction.
        
        Args:
            endpoint_name: Name of endpoint in configuration
            raw_response: Raw response from PB/FM API
            parameters: Parameters used in the API call
            
        Returns:
            Standardized response following Field Registry conventions
        """
        if parameters is None:
            parameters = {}
            
        # Handle error responses
        if raw_response.get("MCP-ERROR") or raw_response.get("error_message"):
            return {"error_message": raw_response.get("MCP-ERROR") or raw_response.get("error_message")}
        
        # CRITICAL: Expand all base64-encoded values before transformation
        # This ensures that any relevant information hidden in base64 blobs is available
        # for source path extraction and transformation
        from base64expand import base64expand
        expanded_response = base64expand(raw_response)
        
        config = self.get_endpoint_config(endpoint_name)
        result = {}
        
        # Apply direct field mappings (using expanded response)
        field_mappings = config.get('field_mappings', [])
        for mapping in field_mappings:
            self._apply_field_mapping(expanded_response, result, mapping)
        
        # Apply array mappings (using expanded response)
        array_mappings = config.get('array_mappings')
        if array_mappings:
            self._apply_array_mappings(expanded_response, result, array_mappings)
        
        # Apply calculated fields (using expanded response)
        calculated_fields = config.get('calculated_fields', [])
        for calc_field in calculated_fields:
            self._apply_calculated_field(result, calc_field, parameters, expanded_response)
        
        # Filter out excluded fields
        excluded_fields = config.get('excluded_fields', [])
        for field in excluded_fields:
            result.pop(field, None)
        
        return result
    
    def _apply_field_mapping(self, source: Dict[str, Any], target: Dict[str, Any], mapping: Dict[str, Any]):
        """Apply a single field mapping."""
        source_path = mapping['source_path']
        target_path = mapping['target_path']
        transform = mapping.get('transform', 'direct')
        
        # Extract value using path
        value = self._extract_value_by_path(source, source_path, mapping.get('array_filter'))
        
        if value is not None:
            # Apply transformation
            transformed_value = self._apply_transform(value, transform)
            
            # Handle dynamic field names
            if 'dynamic_field_name' in mapping:
                target_path = self._resolve_dynamic_field_name(mapping['dynamic_field_name'], source, target_path)
            
            # Set target value
            self._set_value_by_path(target, target_path, transformed_value)
    
    def _apply_array_mappings(self, source: Dict[str, Any], target: Dict[str, Any], array_config: Dict[str, Any]):
        """Apply array-level mappings."""
        source_array_path = array_config['source_array']
        target_array_path = array_config['target_array']
        item_mappings = array_config['item_mappings']
        
        source_array = self._extract_value_by_path(source, source_array_path)
        if not isinstance(source_array, list):
            return
        
        target_array = []
        for source_item in source_array:
            target_item = {}
            for item_mapping in item_mappings:
                self._apply_field_mapping(source_item, target_item, item_mapping)
            target_array.append(target_item)
        
        self._set_value_by_path(target, target_array_path, target_array)
    
    def _apply_calculated_field(
        self, 
        target: Dict[str, Any], 
        calc_config: Dict[str, Any], 
        parameters: Dict[str, Any], 
        raw_response: Dict[str, Any]
    ):
        """Apply calculated field using formula."""
        target_path = calc_config['target_path']
        formula = calc_config['formula']
        
        if formula.startswith("PARAMETER:"):
            param_name = formula.split(":", 1)[1]
            value = parameters.get(param_name)
        elif formula == "CURRENT_ISO_TIME":
            value = datetime.now(UTC).isoformat()
        elif formula.startswith("VESTING_CALCULATION:"):
            value = self._calculate_vesting(calc_config, target, parameters)
        else:
            # Arithmetic formula using other target fields
            value = self._evaluate_formula(formula, target)
        
        if value is not None:
            self._set_value_by_path(target, target_path, value)
    
    def _extract_value_by_path(self, data: Dict[str, Any], path: str, array_filter: Dict[str, Any] = None) -> Any:
        """
        Extract value from nested dictionary using dot notation path.
        
        Supports:
        - Simple paths: "field.subfield"
        - Array indexing: "array[0].field"
        - Array filtering: "array[?field=='value'].target"
        """
        if not path or data is None:
            return None
        
        # Handle array filtering syntax
        if '[?' in path and array_filter:
            return self._extract_with_filter(data, path, array_filter)
        
        # Split path and traverse
        parts = self._parse_path(path)
        current = data
        
        for part in parts:
            if isinstance(part, dict) and 'index' in part:
                # Array index access
                if isinstance(current, list) and part['index'] < len(current):
                    current = current[part['index']]
                else:
                    return None
            elif isinstance(part, str):
                # Dictionary key access
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
            else:
                return None
        
        return current
    
    def _extract_with_filter(self, data: Dict[str, Any], path: str, filter_config: Dict[str, Any]) -> Any:
        """Extract value using array filtering."""
        # Parse filter expression: "results[?denom=='nhash'].amount"
        match = re.match(r"([^[]+)\[\?([^=]+)==['\"]([^'\"]+)['\"]\]\.(.+)", path)
        if not match:
            return None
        
        array_path, filter_field, filter_value, target_field = match.groups()
        
        # Get the array
        array_data = self._extract_value_by_path(data, array_path)
        if not isinstance(array_data, list):
            return None
        
        # Find matching item
        for item in array_data:
            if isinstance(item, dict) and item.get(filter_field) == filter_value:
                return self._extract_value_by_path(item, target_field)
        
        return None
    
    def _parse_path(self, path: str) -> List[Union[str, Dict[str, Any]]]:
        """Parse path string into components."""
        parts = []
        current = ""
        i = 0
        
        while i < len(path):
            char = path[i]
            if char == '.':
                if current:
                    parts.append(current)
                    current = ""
            elif char == '[':
                if current:
                    parts.append(current)
                    current = ""
                # Parse array index
                j = i + 1
                while j < len(path) and path[j] != ']':
                    j += 1
                if j < len(path):
                    index_str = path[i+1:j]
                    if index_str.isdigit():
                        parts.append({'index': int(index_str)})
                    i = j
            else:
                current += char
            i += 1
        
        if current:
            parts.append(current)
        
        return parts
    
    def _set_value_by_path(self, data: Dict[str, Any], path: str, value: Any):
        """Set value in nested dictionary using dot notation path."""
        parts = path.split('.')
        current = data
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def _apply_transform(self, value: Any, transform: str) -> Any:
        """Apply transformation to value."""
        if transform == 'direct':
            return value
        elif transform == 'string_to_int':
            return int(value) if isinstance(value, str) and value.isdigit() else value
        elif transform == 'ensure_int':
            return int(value) if isinstance(value, (str, int, float)) else value
        elif transform == 'iso_timestamp':
            # Ensure ISO 8601 format
            return value  # Assume already in correct format
        else:
            return value
    
    def _resolve_dynamic_field_name(self, dynamic_config: Dict[str, Any], source: Dict[str, Any], default: str) -> str:
        """Resolve dynamic field name based on data values."""
        template = dynamic_config.get('template', default)
        suffix_mapping = dynamic_config.get('suffix_mapping', {})
        
        # Extract denom value to determine suffix
        denom = source.get('denom', '')
        suffix = suffix_mapping.get(denom, 'unknown')
        
        return template.format(suffix=suffix)
    
    def _evaluate_formula(self, formula: str, data: Dict[str, Any]) -> Any:
        """Evaluate arithmetic formula using data values."""
        # Simple arithmetic evaluation
        # Replace field names with their values
        expression = formula
        for key, value in data.items():
            if isinstance(value, (int, float)):
                expression = expression.replace(key, str(value))
        
        try:
            # Safe evaluation of arithmetic expressions
            return eval(expression, {"__builtins__": {}})
        except:
            return None
    
    def _calculate_vesting(self, calc_config: Dict[str, Any], data: Dict[str, Any], parameters: Dict[str, Any]) -> int:
        """Calculate vesting amounts using linear interpolation."""
        try:
            original_amount = data.get('vesting_original_amount_nhash', 0)
            start_time = data.get('vesting_start_date', '')
            end_time = data.get('vesting_end_date', '')
            current_time = data.get('date_time_result', datetime.now(UTC).isoformat())
            
            if not all([original_amount, start_time, end_time, current_time]):
                return 0
            
            # Convert to timestamps
            start_ts = datetime.fromisoformat(start_time.replace('Z', '+00:00')).timestamp()
            end_ts = datetime.fromisoformat(end_time.replace('Z', '+00:00')).timestamp()
            current_ts = datetime.fromisoformat(current_time.replace('Z', '+00:00')).timestamp()
            
            if current_ts <= start_ts:
                return 0
            elif current_ts >= end_ts:
                return original_amount
            else:
                # Linear interpolation
                progress = (current_ts - start_ts) / (end_ts - start_ts)
                return int(original_amount * progress)
                
        except Exception:
            return 0


# Usage example and testing
if __name__ == "__main__":
    transformer = ConfigDrivenTransformer()
    
    # Test hash statistics transformation
    raw_hash_stats = {
        "maxSupply": {"amount": "100000000000000000", "denom": "nhash"},
        "burned": {"amount": "1000000000000000", "denom": "nhash"},
        "currentSupply": {"amount": "99000000000000000", "denom": "nhash"},
        "circulation": {"amount": "50000000000000000", "denom": "nhash"},
        "communityPool": {"amount": "10000000000000000", "denom": "nhash"},
        "bonded": {"amount": "25000000000000000", "denom": "nhash"},
        "lastUpdated": "2024-07-17T10:30:00Z"
    }
    
    result = transformer.transform_response("hash_statistics", raw_hash_stats)
    print("Hash Statistics Result:")
    print(result)
    print()
    
    # Test account balance transformation
    raw_balances = {
        "results": [
            {"denom": "nhash", "amount": "1000000000"},
            {"denom": "uusd.trading", "amount": "500000"}
        ]
    }
    
    result = transformer.transform_response("asset_balances", raw_balances, {"account_address": "tp1abc123"})
    print("Asset Balances Result:")
    print(result)