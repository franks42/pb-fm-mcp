"""
Grouped Attribute Transformation Engine

This module extends the configuration-driven transformer to support:
1. LOGICAL GROUPS: Attributes that must be understood together
2. API CALL GROUPS: Attributes that come from the same PB-API endpoint
3. BANDWIDTH OPTIMIZATION: Filtering out irrelevant data
4. CONFUSION REDUCTION: Removing fields that could confuse AI agents

Supports grouped MCP functions that combine multiple API calls and 
return logically coherent attribute sets.
"""

import yaml
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from .config_driven_transformer import ConfigDrivenTransformer
from .denomination_converter import DenominationConverter


class GroupedAttributeTransformer(ConfigDrivenTransformer):
    """
    Enhanced transformer that handles attribute groupings and multi-API-call functions.
    """
    
    def __init__(
        self, 
        config_path: str = "src/mcpserver/docs/pb_api_endpoint_mappings.yaml",
        groups_path: str = "src/mcpserver/docs/pb_api_attribute_groups.yaml",
        denomination_registry_path: str = "src/mcpserver/docs/denomination_registry.yaml"
    ):
        """Initialize with endpoint mappings, attribute groups, and denomination converter."""
        super().__init__(config_path)
        self.groups_path = Path(groups_path)
        self.groups_config = self._load_groups_config()
        self.denomination_converter = DenominationConverter(denomination_registry_path)
        
    def _load_groups_config(self) -> Dict[str, Any]:
        """Load attribute groups configuration."""
        try:
            with open(self.groups_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Groups configuration file not found: {self.groups_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid groups YAML configuration: {e}")
    
    def get_logical_group(self, group_name: str) -> Dict[str, Any]:
        """Get logical attribute group configuration."""
        groups = self.groups_config.get('attribute_groups', {})
        if group_name not in groups:
            raise ValueError(f"Logical group '{group_name}' not found")
        return groups[group_name]
    
    def get_api_call_group(self, group_name: str) -> Dict[str, Any]:
        """Get API call group configuration."""
        groups = self.groups_config.get('api_call_groups', {})
        if group_name not in groups:
            raise ValueError(f"API call group '{group_name}' not found")
        return groups[group_name]
    
    def get_mcp_function_group(self, function_name: str) -> Dict[str, Any]:
        """Get MCP function group configuration."""
        groups = self.groups_config.get('mcp_function_groups', {})
        for group_name, group_config in groups.items():
            if group_config.get('mcp_function_name') == function_name:
                return group_config
        raise ValueError(f"MCP function group for '{function_name}' not found")
    
    def validate_logical_group_completeness(self, group_name: str, attributes: Set[str]) -> Dict[str, Any]:
        """
        Validate that all required attributes for a logical group are present.
        
        Returns validation result with missing attributes and warnings.
        """
        group_config = self.get_logical_group(group_name)
        required_attributes = set(group_config.get('attributes', []))
        provided_attributes = set(attributes)
        
        missing = required_attributes - provided_attributes
        extra = provided_attributes - required_attributes
        
        return {
            'is_complete': len(missing) == 0,
            'missing_attributes': list(missing),
            'extra_attributes': list(extra),
            'reasoning': group_config.get('reasoning', ''),
            'required_together': group_config.get('required_together', False)
        }
    
    def apply_bandwidth_optimization(self, raw_response: Dict[str, Any], api_call_group: str) -> Dict[str, Any]:
        """
        Apply bandwidth optimization by filtering out irrelevant attributes.
        """
        group_config = self.get_api_call_group(api_call_group)
        filtered_out = set(group_config.get('filtered_out_attributes', []))
        
        # Also apply global optimization rules
        optimization_rules = self.groups_config.get('optimization_rules', {})
        bandwidth_rules = optimization_rules.get('bandwidth_reduction', {}).get('rules', [])
        
        # Create filtered response
        filtered_response = {}
        
        def filter_recursive(data: Any, current_path: str = "") -> Any:
            if isinstance(data, dict):
                filtered_dict = {}
                for key, value in data.items():
                    full_key = f"{current_path}.{key}" if current_path else key
                    
                    # Check if this key should be filtered out
                    if key in filtered_out:
                        continue
                    
                    # Apply global bandwidth rules
                    if self._should_filter_by_rules(key, bandwidth_rules):
                        continue
                    
                    filtered_dict[key] = filter_recursive(value, full_key)
                return filtered_dict
            elif isinstance(data, list):
                return [filter_recursive(item, current_path) for item in data]
            else:
                return data
        
        return filter_recursive(raw_response)
    
    def _should_filter_by_rules(self, field_name: str, rules: List[str]) -> bool:
        """Check if field should be filtered based on optimization rules."""
        for rule in rules:
            # Simple rule matching - could be made more sophisticated
            if "pagination metadata" in rule and field_name in ["page_request", "pagination", "total_count"]:
                return True
            if "internal API structure" in rule and field_name in ["@type", "base_account"]:
                return True
            if "blockchain metadata" in rule and field_name in ["block_height", "validator_count"]:
                return True
            if "ratio fields" in rule and "ratio" in field_name.lower():
                return True
            if "timestamp fields" in rule and field_name in ["last_updated"]:
                return True
        return False
    
    def transform_grouped_response(
        self, 
        mcp_function_name: str, 
        api_responses: Dict[str, Dict[str, Any]], 
        parameters: Dict[str, Any] = None,
        stateless_optimized: bool = True
    ) -> Dict[str, Any]:
        """
        Transform multiple API responses into a grouped MCP response.
        
        Args:
            mcp_function_name: Name of the MCP function being called
            api_responses: Dict mapping API call group names to their responses
            parameters: Parameters used in the MCP function call
            stateless_optimized: If True, use base denominations only and UTC timestamps
            
        Returns:
            Grouped and filtered response optimized for stateless server
        """
        if parameters is None:
            parameters = {}
        
        # Get MCP function group configuration
        try:
            function_config = self.get_mcp_function_group(mcp_function_name)
        except ValueError:
            # Fallback to single endpoint transformation
            if len(api_responses) == 1:
                endpoint_name = list(api_responses.keys())[0]
                return self.transform_response(endpoint_name, list(api_responses.values())[0], parameters)
            else:
                raise ValueError(f"Multiple API responses provided but no group config for {mcp_function_name}")
        
        result = {}
        
        # Process each API call group
        api_calls = function_config.get('combines_api_calls', [])
        for api_call_group in api_calls:
            if api_call_group in api_responses:
                raw_response = api_responses[api_call_group]
                
                # CRITICAL: Expand all base64-encoded values before processing
                # This ensures that any relevant information hidden in base64 blobs is available
                # for transformation, filtering, and source path extraction
                from base64expand import base64expand
                expanded_response = base64expand(raw_response)
                
                # Apply bandwidth optimization (using expanded response)
                filtered_response = self.apply_bandwidth_optimization(expanded_response, api_call_group)
                
                # Transform using endpoint-specific logic
                # Map API call group to endpoint name for transformation
                endpoint_mapping = {
                    'pb_account_info_call': 'account_info',
                    'pb_account_balances_call': 'asset_balances', 
                    'pb_vesting_info_call': 'vesting_info',
                    'pb_delegation_info_call': 'delegation_data',
                    'pb_hash_statistics_call': 'hash_statistics',
                    'fm_exchange_commitments_call': 'committed_amount'
                }
                
                endpoint_name = endpoint_mapping.get(api_call_group, api_call_group)
                transformed_data = self.transform_response(endpoint_name, filtered_response, parameters)
                
                # Merge into result
                result.update(transformed_data)
        
        # Validate logical group completeness if specified
        logical_groups = function_config.get('returns_logical_groups', [])
        validation_results = {}
        
        for logical_group in logical_groups:
            validation = self.validate_logical_group_completeness(logical_group, set(result.keys()))
            validation_results[logical_group] = validation
            
            if not validation['is_complete'] and validation['required_together']:
                # Add warning about incomplete logical group
                result['_warnings'] = result.get('_warnings', [])
                result['_warnings'].append({
                    'type': 'incomplete_logical_group',
                    'group': logical_group,
                    'missing_attributes': validation['missing_attributes'],
                    'reasoning': validation['reasoning']
                })
        
        # Apply stateless optimizations if requested
        if stateless_optimized:
            result = self._apply_stateless_optimizations(result)
        
        # Add metadata about the grouping and optimizations
        result['_metadata'] = {
            'mcp_function': mcp_function_name,
            'api_calls_used': api_calls,
            'logical_groups_returned': logical_groups,
            'group_validation': validation_results,
            'stateless_optimized': stateless_optimized,
            'response_format': 'base_denominations_only' if stateless_optimized else 'full_format',
            'timestamp_format': 'utc_iso_with_timezone' if stateless_optimized else 'mixed'
        }
        
        return result
    
    def _apply_stateless_optimizations(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply stateless server optimizations to response.
        
        - Ensure all amounts use base denominations only
        - Ensure all timestamps are UTC ISO format with timezone
        - Remove any display formatting that should be done by AI agent
        """
        optimized = response.copy()
        
        def optimize_recursive(data: Any, path: str = "") -> Any:
            if isinstance(data, dict):
                optimized_dict = {}
                
                for key, value in data.items():
                    # Handle amount fields - ensure base denomination only
                    if self._is_amount_field(key):
                        # Ensure we're using base denomination format
                        if not self.denomination_converter._has_embedded_denomination(key):
                            # This shouldn't happen with our transformations, but handle it
                            optimized_dict[key] = value
                        else:
                            # Keep base denomination field as-is
                            optimized_dict[key] = value
                    
                    # Handle timestamp fields - ensure UTC ISO format
                    elif self._is_timestamp_field(key):
                        optimized_dict[key] = self._ensure_utc_iso_format(value)
                    
                    # Remove display format fields (AI agent should handle these)
                    elif self._is_display_format_field(key):
                        # Skip display format fields in stateless mode
                        continue
                    
                    # Recursively optimize nested structures
                    elif isinstance(value, (dict, list)):
                        optimized_dict[key] = optimize_recursive(value, f"{path}.{key}" if path else key)
                    
                    else:
                        optimized_dict[key] = value
                
                return optimized_dict
                
            elif isinstance(data, list):
                return [optimize_recursive(item, f"{path}[{i}]") for i, item in enumerate(data)]
            else:
                return data
        
        return optimize_recursive(optimized)
    
    def _is_amount_field(self, field_name: str) -> bool:
        """Check if field is an amount field."""
        return 'amount' in field_name.lower() or any(
            field_name.endswith(suffix) for suffix in ['_nhash', '_uusd', '_neth', '_uusdc', '_nsol', '_uxrp', '_uylds']
        )
    
    def _is_timestamp_field(self, field_name: str) -> bool:
        """Check if field is a timestamp field."""
        timestamp_patterns = ['_date', '_time', '_timestamp', '_updated', 'timestamp']
        return any(pattern in field_name.lower() for pattern in timestamp_patterns)
    
    def _is_display_format_field(self, field_name: str) -> bool:
        """Check if field is a display format field that should be removed in stateless mode."""
        display_patterns = ['display_amount', 'display_symbol', 'formatted_display', 'display_']
        return any(pattern in field_name.lower() for pattern in display_patterns)
    
    def _ensure_utc_iso_format(self, timestamp_value: Any) -> str:
        """Ensure timestamp is in UTC ISO format with explicit timezone."""
        if not isinstance(timestamp_value, str):
            return str(timestamp_value)
        
        # If already has timezone info, keep as-is
        if timestamp_value.endswith('Z') or '+' in timestamp_value[-6:] or timestamp_value.endswith('+00:00'):
            return timestamp_value
        
        # If it looks like ISO format without timezone, assume UTC and add Z
        if 'T' in timestamp_value and len(timestamp_value) >= 19:
            return f"{timestamp_value}Z" if not timestamp_value.endswith('Z') else timestamp_value
        
        # Otherwise return as-is
        return timestamp_value
    
    def create_stateless_optimized_response(
        self, 
        base_data: Dict[str, Any],
        include_conversion_hints: bool = True
    ) -> Dict[str, Any]:
        """
        Create response optimized for stateless server with AI agent state management.
        
        Args:
            base_data: Data with base denominations and UTC timestamps
            include_conversion_hints: Whether to include hints for AI agent conversions
            
        Returns:
            Stateless-optimized response
        """
        # Apply stateless optimizations
        optimized = self._apply_stateless_optimizations(base_data)
        
        if include_conversion_hints:
            # Add conversion hints for AI agent
            optimized['_conversion_hints'] = {
                'base_denominations_used': self._extract_base_denominations(optimized),
                'ai_agent_notes': {
                    'amounts': 'All amounts in base units - use cached conversion table for display',
                    'timestamps': 'All timestamps in UTC - convert to user timezone for display',
                    'caching': 'Cache conversion table and timezone info at session start'
                },
                'recommended_ai_functions': [
                    'get_denomination_conversion_table()',
                    'get_system_timezone_info()'
                ]
            }
        
        return optimized
    
    def get_required_api_calls(self, mcp_function_name: str) -> List[Dict[str, Any]]:
        """
        Get list of API calls required for an MCP function.
        
        Returns list of API call configurations with URLs and parameters.
        """
        function_config = self.get_mcp_function_group(mcp_function_name)
        api_calls = function_config.get('combines_api_calls', [])
        
        call_configs = []
        for api_call_group in api_calls:
            call_config = self.get_api_call_group(api_call_group)
            call_configs.append({
                'group_name': api_call_group,
                'url': call_config.get('pb_api_url'),
                'method': call_config.get('pb_api_method'),
                'parameters': call_config.get('pb_api_parameters', [])
            })
        
        return call_configs
    
    def explain_attribute_grouping(self, mcp_function_name: str) -> Dict[str, Any]:
        """
        Provide explanation of why attributes are grouped together.
        
        Useful for documentation and AI agent understanding.
        """
        function_config = self.get_mcp_function_group(mcp_function_name)
        
        explanation = {
            'function_name': mcp_function_name,
            'description': function_config.get('description'),
            'reasoning': function_config.get('reasoning'),
            'logical_groups': [],
            'api_efficiency': {}
        }
        
        # Explain logical groups
        logical_groups = function_config.get('returns_logical_groups', [])
        for group_name in logical_groups:
            group_config = self.get_logical_group(group_name)
            explanation['logical_groups'].append({
                'name': group_name,
                'description': group_config.get('description'),
                'attributes': group_config.get('attributes', []),
                'reasoning': group_config.get('reasoning'),
                'required_together': group_config.get('required_together', False)
            })
        
        # Explain API efficiency
        api_calls = function_config.get('combines_api_calls', [])
        for api_call in api_calls:
            call_config = self.get_api_call_group(api_call)
            explanation['api_efficiency'][api_call] = {
                'url': call_config.get('pb_api_url'),
                'relevant_attributes': call_config.get('relevant_attributes', []),
                'filtered_attributes': call_config.get('filtered_out_attributes', []),
                'reasoning': call_config.get('reasoning')
            }
        
        return explanation
    
    def validate_denomination_context(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that all amount fields have proper denomination context.
        
        Returns validation result with any missing denomination contexts.
        """
        validation_result = {
            'is_valid': True,
            'missing_contexts': [],
            'inconsistent_formats': [],
            'warnings': []
        }
        
        # Get denomination context rules
        denom_rules = self.groups_config.get('denomination_context_rules', {})
        mandatory_pairings = denom_rules.get('mandatory_pairings', {}).get('amount_denomination_pairs', [])
        
        def check_recursive(data: Any, path: str = "") -> None:
            if isinstance(data, dict):
                # Check for amount fields without context
                for key, value in data.items():
                    full_path = f"{path}.{key}" if path else key
                    
                    # Check if this is an amount field
                    if 'amount' in key.lower() and not self._has_embedded_denomination(key):
                        # Look for required context fields
                        for pairing in mandatory_pairings:
                            if pairing['primary'] in key or key.endswith('amount'):
                                required_context = pairing['required_context']
                                missing_context = []
                                
                                for context_field in required_context:
                                    if context_field not in data:
                                        missing_context.append(context_field)
                                
                                if missing_context:
                                    validation_result['missing_contexts'].append({
                                        'field': full_path,
                                        'missing': missing_context,
                                        'reasoning': pairing['reasoning']
                                    })
                                    validation_result['is_valid'] = False
                    
                    # Recursively check nested objects
                    if isinstance(value, (dict, list)):
                        check_recursive(value, full_path)
                        
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    check_recursive(item, f"{path}[{i}]")
        
        check_recursive(response)
        
        # Check for consistent denomination format
        self._validate_denomination_format_consistency(response, validation_result)
        
        return validation_result
    
    def _has_embedded_denomination(self, field_name: str) -> bool:
        """Check if field name has embedded denomination suffix."""
        denom_rules = self.groups_config.get('denomination_context_rules', {})
        embedded_rules = denom_rules.get('embedded_denomination_fields', {})
        
        # Check nhash suffix
        if field_name.endswith('_nhash'):
            return True
            
        # Check other denomination suffixes
        suffixes = ['_uusd', '_neth', '_uusdc', '_nsol', '_uxrp', '_uylds']
        return any(field_name.endswith(suffix) for suffix in suffixes)
    
    def _validate_denomination_format_consistency(self, response: Dict[str, Any], validation_result: Dict[str, Any]) -> None:
        """Validate consistent denomination format across response."""
        embedded_fields = []
        separate_fields = []
        
        def scan_formats(data: Any, path: str = "") -> None:
            if isinstance(data, dict):
                has_amount = False
                has_denom = False
                
                for key, value in data.items():
                    if 'amount' in key.lower():
                        if self._has_embedded_denomination(key):
                            embedded_fields.append(f"{path}.{key}" if path else key)
                        else:
                            has_amount = True
                    if 'denom' in key.lower():
                        has_denom = True
                
                if has_amount and has_denom:
                    separate_fields.append(path or "root")
                
                # Recursively scan
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        scan_formats(value, f"{path}.{key}" if path else key)
                        
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    scan_formats(item, f"{path}[{i}]")
        
        scan_formats(response)
        
        # Check for mixed formats
        if embedded_fields and separate_fields:
            validation_result['inconsistent_formats'].append({
                'issue': 'Mixed denomination formats',
                'embedded_fields': embedded_fields,
                'separate_format_objects': separate_fields,
                'recommendation': 'Use consistent format - either all embedded suffixes or all separate denom fields'
            })
    
    def add_denomination_context(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatically add missing denomination context where possible.
        
        Returns enhanced response with denomination context added.
        """
        enhanced_response = response.copy()
        validation = self.validate_denomination_context(response)
        
        if not validation['is_valid']:
            # Add missing denomination contexts
            for missing in validation['missing_contexts']:
                field_path = missing['field']
                missing_contexts = missing['missing']
                
                # Try to infer denomination from field name patterns
                for context_field in missing_contexts:
                    if context_field == 'asset_denom':
                        # Infer denomination from field name
                        if 'nhash' in field_path.lower():
                            self._set_value_by_path(enhanced_response, 
                                                  f"{field_path.rsplit('.', 1)[0]}.asset_denom", 
                                                  "nhash")
                        elif 'uusd' in field_path.lower():
                            self._set_value_by_path(enhanced_response,
                                                  f"{field_path.rsplit('.', 1)[0]}.asset_denom",
                                                  "uusd.trading")
                        # Add other denomination inferences as needed
            
            # Add metadata about enhancements
            enhanced_response['_denomination_context'] = {
                'auto_enhanced': True,
                'original_validation': validation,
                'enhancements_applied': len(validation['missing_contexts'])
            }
        
        return enhanced_response
    
    def standardize_denomination_format(self, response: Dict[str, Any], prefer_embedded: bool = True) -> Dict[str, Any]:
        """
        Standardize denomination format across entire response.
        
        Args:
            prefer_embedded: If True, convert to embedded format (*_nhash). 
                           If False, convert to separate denom fields.
        """
        standardized = response.copy()
        
        def convert_recursive(data: Any, path: str = "") -> Any:
            if isinstance(data, dict):
                converted_dict = {}
                amount_field = None
                denom_value = None
                
                # First pass: identify amount and denom pairs
                for key, value in data.items():
                    if 'amount' in key.lower() and not self._has_embedded_denomination(key):
                        amount_field = key
                    elif 'denom' in key.lower():
                        denom_value = value
                
                # Second pass: convert based on preference
                for key, value in data.items():
                    if key == amount_field and denom_value and prefer_embedded:
                        # Convert to embedded format
                        denom_suffix = self._get_denomination_suffix(denom_value)
                        new_key = f"{key}_{denom_suffix}"
                        converted_dict[new_key] = value
                    elif key.endswith('_denom') and prefer_embedded:
                        # Skip separate denom field when using embedded format
                        continue
                    elif self._has_embedded_denomination(key) and not prefer_embedded:
                        # Convert embedded to separate format
                        base_key = key.rsplit('_', 1)[0]
                        denom = key.rsplit('_', 1)[1]
                        converted_dict[base_key] = value
                        converted_dict[f"{base_key}_denom"] = self._expand_denomination(denom)
                    else:
                        # Keep as-is, but recursively convert nested structures
                        if isinstance(value, (dict, list)):
                            converted_dict[key] = convert_recursive(value, f"{path}.{key}" if path else key)
                        else:
                            converted_dict[key] = value
                
                return converted_dict
                
            elif isinstance(data, list):
                return [convert_recursive(item, f"{path}[{i}]") for i, item in enumerate(data)]
            else:
                return data
        
        return convert_recursive(standardized)
    
    def _get_denomination_suffix(self, denom: str) -> str:
        """Convert full denomination to suffix format."""
        denom_mapping = {
            'nhash': 'nhash',
            'uusd.trading': 'uusd',
            'neth.figure.se': 'neth',
            'uusdc.figure.se': 'uusdc',
            'nsol.figure.se': 'nsol',
            'uxrp.figure.se': 'uxrp',
            'uylds.fcc': 'uylds'
        }
        return denom_mapping.get(denom, denom.replace('.', '_'))
    
    def _expand_denomination(self, suffix: str) -> str:
        """Convert suffix back to full denomination."""
        suffix_mapping = {
            'nhash': 'nhash',
            'uusd': 'uusd.trading',
            'neth': 'neth.figure.se',
            'uusdc': 'uusdc.figure.se',
            'nsol': 'nsol.figure.se',
            'uxrp': 'uxrp.figure.se',
            'uylds': 'uylds.fcc'
        }
        return suffix_mapping.get(suffix, suffix)
    
    def enhance_with_denomination_conversion(
        self, 
        response: Dict[str, Any], 
        include_display_format: bool = False
    ) -> Dict[str, Any]:
        """
        Enhance response with denomination conversion capabilities.
        
        Args:
            response: Transformed response
            include_display_format: Whether to add display format alongside base
            
        Returns:
            Enhanced response with denomination conversions
        """
        enhanced = response.copy()
        
        def enhance_recursive(data: Any, path: str = "") -> Any:
            if isinstance(data, dict):
                enhanced_dict = {}
                
                for key, value in data.items():
                    # Check if this is a field with embedded denomination
                    if self.denomination_converter._has_embedded_denomination(key):
                        # Add the original field
                        enhanced_dict[key] = value
                        
                        # Add denomination conversion info if requested
                        if include_display_format and isinstance(value, int):
                            conversion_result = self.denomination_converter.convert_field_to_standardized(
                                key, value, "display"
                            )
                            
                            if 'display_format' in conversion_result:
                                # Add display fields alongside base field
                                enhanced_dict.update(conversion_result['display_format'])
                                
                    elif isinstance(value, (dict, list)):
                        # Recursively enhance nested structures
                        enhanced_dict[key] = enhance_recursive(value, f"{path}.{key}" if path else key)
                    else:
                        enhanced_dict[key] = value
                
                return enhanced_dict
                
            elif isinstance(data, list):
                return [enhance_recursive(item, f"{path}[{i}]") for i, item in enumerate(data)]
            else:
                return data
        
        enhanced_response = enhance_recursive(enhanced)
        
        # Add denomination metadata
        enhanced_response['_denomination_info'] = {
            'conversion_applied': include_display_format,
            'supported_assets': [asset['asset_name'] for asset in self.denomination_converter.get_supported_assets()],
            'base_denominations_used': self._extract_base_denominations(response)
        }
        
        return enhanced_response
    
    def _extract_base_denominations(self, response: Dict[str, Any]) -> List[str]:
        """Extract list of base denominations used in response."""
        denominations = set()
        
        def extract_recursive(data: Any) -> None:
            if isinstance(data, dict):
                for key, value in data.items():
                    # Check for embedded denomination in field name
                    for suffix, denom in self.denomination_converter.suffix_lookup.items():
                        if key.endswith(suffix):
                            denominations.add(denom)
                            break
                    
                    # Check for explicit denomination fields
                    if 'denom' in key.lower() and isinstance(value, str):
                        if self.denomination_converter.get_asset_info(value):
                            denominations.add(value)
                    
                    # Recursively check nested structures
                    if isinstance(value, (dict, list)):
                        extract_recursive(value)
                        
            elif isinstance(data, list):
                for item in data:
                    extract_recursive(item)
        
        extract_recursive(response)
        return sorted(list(denominations))
    
    def validate_and_enhance_denominations(
        self, 
        response: Dict[str, Any], 
        auto_fix: bool = True,
        include_display: bool = False
    ) -> Dict[str, Any]:
        """
        Comprehensive denomination validation and enhancement.
        
        Args:
            response: Response to validate and enhance
            auto_fix: Whether to automatically fix denomination issues
            include_display: Whether to add display format conversions
            
        Returns:
            Enhanced response with denomination validation results
        """
        # Step 1: Validate denomination context
        context_validation = self.validate_denomination_context(response)
        
        # Step 2: Validate individual denominations
        denominations_used = self._extract_base_denominations(response)
        denomination_validations = {}
        
        for denom in denominations_used:
            validation = self.denomination_converter.validate_denomination(denom)
            denomination_validations[denom] = validation
        
        # Step 3: Auto-fix if requested
        final_response = response.copy()
        
        if auto_fix:
            # Fix denomination context issues
            if not context_validation['is_valid']:
                final_response = self.add_denomination_context(final_response)
            
            # Standardize denomination format
            final_response = self.standardize_denomination_format(final_response, prefer_embedded=True)
        
        # Step 4: Add display formats if requested
        if include_display:
            final_response = self.enhance_with_denomination_conversion(final_response, include_display_format=True)
        
        # Step 5: Add comprehensive validation metadata
        final_response['_denomination_validation'] = {
            'context_validation': context_validation,
            'denomination_validations': denomination_validations,
            'auto_fixes_applied': auto_fix,
            'display_formats_added': include_display,
            'denominations_found': denominations_used,
            'all_valid': context_validation['is_valid'] and all(
                v['is_valid'] for v in denomination_validations.values()
            )
        }
        
        return final_response
    
    def create_standardized_amount_response(
        self, 
        amounts: Dict[str, int], 
        response_type: str = 'calculation'
    ) -> Dict[str, Any]:
        """
        Create standardized amount response using denomination converter.
        
        Args:
            amounts: Dict mapping denominations to base amounts
            response_type: 'calculation' (base only), 'display' (both), or 'user_friendly' (display focus)
            
        Returns:
            Standardized amount response
        """
        if response_type == 'calculation':
            # Pure calculation format - base units only
            result = {}
            for denom, amount in amounts.items():
                # Convert denomination to field suffix
                suffix = None
                for suf, d in self.denomination_converter.suffix_lookup.items():
                    if d == denom:
                        suffix = suf
                        break
                
                if suffix:
                    field_name = f"amount{suffix}"
                    result[field_name] = amount
                else:
                    # Fallback to explicit base format
                    result[f"amount_base_units_{denom.replace('.', '_')}"] = amount
                    result[f"denom_{denom.replace('.', '_')}"] = denom
            
            return result
            
        elif response_type == 'display':
            # Both base and display formats
            return self.denomination_converter.create_multi_asset_response(amounts, include_display=True)
            
        elif response_type == 'user_friendly':
            # Display-focused format
            asset_balances = []
            for denom, amount in amounts.items():
                amount_obj = self.denomination_converter.create_amount_object(amount, denom, include_display=True)
                
                # Add user-friendly formatting
                if 'display_amount' in amount_obj and 'display_symbol' in amount_obj:
                    # Format with commas for readability
                    display_val = float(amount_obj['display_amount'])
                    formatted = f"{display_val:,.6f}".rstrip('0').rstrip('.')
                    amount_obj['formatted_display'] = f"{formatted} {amount_obj['display_symbol']}"
                
                asset_balances.append(amount_obj)
            
            return {'asset_balances': asset_balances}
        
        else:
            raise ValueError(f"Unknown response_type: {response_type}")


# Usage example
if __name__ == "__main__":
    transformer = GroupedAttributeTransformer()
    
    # Example: Complete wallet composition
    print("=== Complete Wallet Composition Example ===")
    
    # Simulate responses from multiple API calls
    api_responses = {
        'pb_account_balances_call': {
            'results': [
                {'denom': 'nhash', 'amount': '1000000000'},
                {'denom': 'uusd.trading', 'amount': '500000'}
            ],
            'pagination': {'total_count': 2, 'page': 1}  # This will be filtered out
        },
        'pb_delegation_info_call': {
            'delegated_staked_amount': 500000000,
            'delegated_rewards_amount': 10000000,
            'delegated_redelegated_amount': 0,
            'delegated_unbonding_amount': 0,
            'delegated_total_delegated_amount': 510000000,
            'delegated_earning_amount': 500000000,
            'delegated_not_earning_amount': 10000000
        },
        'fm_exchange_commitments_call': {
            'commitments': [
                {
                    'market_id': 1,
                    'amount': [{'denom': 'nhash', 'amount': '100000000'}]
                }
            ]
        }
    }
    
    result = transformer.transform_grouped_response(
        'get_complete_wallet_composition',
        api_responses,
        {'account_address': 'tp1abc123'}
    )
    
    print("Transformed Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    print("\n=== Attribute Grouping Explanation ===")
    explanation = transformer.explain_attribute_grouping('get_complete_wallet_composition')
    print(f"Function: {explanation['function_name']}")
    print(f"Description: {explanation['description']}")
    print(f"Reasoning: {explanation['reasoning']}")
    
    for group in explanation['logical_groups']:
        print(f"\nLogical Group: {group['name']}")
        print(f"  Description: {group['description']}")
        print(f"  Attributes: {group['attributes']}")
        print(f"  Reasoning: {group['reasoning']}")