"""
Denomination Conversion System

This module handles conversions between base denominations (for calculations)
and display denominations (for user interfaces), maintaining precision and
providing validation for all denomination operations.

Key principles:
- BASE DENOM: Integer, exact precision, used for calculations
- DISPLAY DENOM: Decimal, user-friendly, used for presentation
- NO PRECISION LOSS: Conversions preserve exact values
"""

import yaml
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional, Tuple, Union
from pathlib import Path


class DenominationConverter:
    """
    Handles all denomination conversions and validations for PB-FM-Hastra assets.
    
    Provides conversion between base units (for calculations) and display units
    (for user interfaces) while maintaining precision and validation.
    """
    
    def __init__(self, registry_path: str = "src/mcpserver/docs/denomination_registry.yaml"):
        """Initialize with denomination registry."""
        self.registry_path = Path(registry_path)
        self.registry = self._load_registry()
        self.assets = self.registry.get('assets', {})
        self.denomination_lookup = self.registry.get('denomination_lookup', {})
        self.suffix_lookup = self.registry.get('suffix_lookup', {})
        
    def _load_registry(self) -> Dict[str, Any]:
        """Load denomination registry from YAML file."""
        try:
            with open(self.registry_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Denomination registry not found: {self.registry_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid denomination registry YAML: {e}")
    
    def get_asset_info(self, denomination: str) -> Optional[Dict[str, Any]]:
        """Get asset information for a given denomination."""
        if denomination in self.denomination_lookup:
            lookup_info = self.denomination_lookup[denomination]
            asset_name = lookup_info['asset']
            if asset_name in self.assets:
                return {
                    'asset_name': asset_name,
                    'asset_config': self.assets[asset_name],
                    'lookup_info': lookup_info
                }
        return None
    
    def get_asset_from_suffix(self, field_suffix: str) -> Optional[Dict[str, Any]]:
        """Get asset information from field name suffix (e.g., '_nhash')."""
        if field_suffix in self.suffix_lookup:
            denomination = self.suffix_lookup[field_suffix]
            return self.get_asset_info(denomination)
        return None
    
    def is_base_denomination(self, denomination: str) -> bool:
        """Check if denomination is a base (calculation) denomination."""
        asset_info = self.get_asset_info(denomination)
        return asset_info is not None and asset_info['lookup_info']['type'] == 'base'
    
    def get_conversion_factor(self, denomination: str) -> Optional[int]:
        """Get conversion factor for denomination (base_amount / factor = display_amount)."""
        asset_info = self.get_asset_info(denomination)
        if asset_info:
            return asset_info['lookup_info']['conversion_factor']
        return None
    
    def base_to_display(self, base_amount: int, denomination: str) -> Tuple[Optional[Decimal], Optional[str]]:
        """
        Convert base amount to display format.
        
        Args:
            base_amount: Amount in base units (integer)
            denomination: Base denomination (e.g., 'nhash', 'uusd.trading')
            
        Returns:
            Tuple of (display_amount, display_symbol) or (None, None) if invalid
        """
        if not isinstance(base_amount, int):
            return None, None
            
        asset_info = self.get_asset_info(denomination)
        if not asset_info:
            return None, None
        
        conversion_factor = asset_info['lookup_info']['conversion_factor']
        asset_config = asset_info['asset_config']
        
        # Convert to decimal with appropriate precision
        display_amount = Decimal(base_amount) / Decimal(conversion_factor)
        
        # Get display symbol
        display_denom = asset_config['denominations']['display_denom']
        display_symbol = display_denom['name']
        
        # Round to appropriate decimal places
        precision = self._get_decimal_places(asset_config)
        display_amount = display_amount.quantize(
            Decimal('0.1') ** precision, 
            rounding=ROUND_HALF_UP
        )
        
        return display_amount, display_symbol
    
    def display_to_base(self, display_amount: Union[str, float, Decimal], asset_symbol: str) -> Optional[int]:
        """
        Convert display amount to base format.
        
        Args:
            display_amount: Amount in display units (decimal)
            asset_symbol: Display asset symbol (e.g., 'HASH', 'ETH')
            
        Returns:
            Base amount (integer) or None if invalid
        """
        # Find asset by display symbol
        asset_config = None
        for asset_name, config in self.assets.items():
            if config['denominations']['display_denom']['name'] == asset_symbol:
                asset_config = config
                break
        
        if not asset_config:
            return None
        
        try:
            # Convert to Decimal for precision
            decimal_amount = Decimal(str(display_amount))
            
            # Get conversion factor
            conversion_factor = asset_config['conversion']['base_to_display_factor']
            
            # Convert to base units
            base_amount = decimal_amount * Decimal(conversion_factor)
            
            # Must result in exact integer
            if base_amount % 1 != 0:
                return None  # Would lose precision
            
            return int(base_amount)
            
        except (ValueError, TypeError, ArithmeticError):
            return None
    
    def _get_decimal_places(self, asset_config: Dict[str, Any]) -> int:
        """Get number of decimal places for display formatting."""
        precision_str = asset_config['denominations']['display_denom']['precision']
        if 'decimal places' in precision_str:
            return int(precision_str.split()[0])
        return 6  # Default fallback
    
    def create_amount_object(
        self, 
        base_amount: int, 
        denomination: str, 
        include_display: bool = True
    ) -> Dict[str, Any]:
        """
        Create standardized amount object with base and optional display formats.
        
        Args:
            base_amount: Amount in base units
            denomination: Base denomination
            include_display: Whether to include display format
            
        Returns:
            Standardized amount object
        """
        if not isinstance(base_amount, int):
            raise ValueError("Base amount must be integer")
        
        result = {
            'base_units': base_amount,
            'base_denom': denomination
        }
        
        if include_display:
            display_amount, display_symbol = self.base_to_display(base_amount, denomination)
            if display_amount is not None:
                result.update({
                    'display_amount': str(display_amount),
                    'display_symbol': display_symbol
                })
        
        return result
    
    def create_multi_asset_response(
        self, 
        amounts: Dict[str, int], 
        include_display: bool = True
    ) -> Dict[str, Any]:
        """
        Create standardized multi-asset response.
        
        Args:
            amounts: Dict mapping denominations to base amounts
            include_display: Whether to include display formats
            
        Returns:
            Standardized multi-asset response
        """
        asset_balances = []
        
        for denomination, base_amount in amounts.items():
            asset_info = self.get_asset_info(denomination)
            if not asset_info:
                continue
                
            balance_obj = self.create_amount_object(base_amount, denomination, include_display)
            
            # Add asset identification
            asset_config = asset_info['asset_config']
            balance_obj['asset_name'] = asset_config['denominations']['display_denom']['name']
            balance_obj['asset_description'] = asset_config['description']
            
            asset_balances.append(balance_obj)
        
        return {'asset_balances': asset_balances}
    
    def validate_denomination(self, denomination: str) -> Dict[str, Any]:
        """
        Validate denomination and return validation result.
        
        Returns:
            Validation result with status and details
        """
        result = {
            'is_valid': False,
            'exists': False,
            'is_base_denom': False,
            'asset_info': None,
            'errors': []
        }
        
        if not denomination:
            result['errors'].append("Denomination cannot be empty")
            return result
        
        asset_info = self.get_asset_info(denomination)
        if not asset_info:
            result['errors'].append(f"Unknown denomination: {denomination}")
            return result
        
        result.update({
            'is_valid': True,
            'exists': True,
            'is_base_denom': asset_info['lookup_info']['type'] == 'base',
            'asset_info': asset_info
        })
        
        return result
    
    def convert_field_to_standardized(
        self, 
        field_name: str, 
        field_value: Any, 
        target_format: str = 'base'
    ) -> Dict[str, Any]:
        """
        Convert field with embedded denomination to standardized format.
        
        Args:
            field_name: Field name (e.g., 'available_total_amount_nhash')
            field_value: Field value
            target_format: 'base', 'display', or 'both'
            
        Returns:
            Standardized field representation
        """
        # Extract denomination suffix
        suffix = None
        for suf in self.suffix_lookup.keys():
            if field_name.endswith(suf):
                suffix = suf
                break
        
        if not suffix:
            return {
                'error': f"No denomination suffix found in field: {field_name}",
                'original_field': field_name,
                'original_value': field_value
            }
        
        denomination = self.suffix_lookup[suffix]
        base_name = field_name[:-len(suffix)]
        
        result = {
            'field_base_name': base_name,
            'denomination': denomination,
            'original_field': field_name,
            'original_value': field_value
        }
        
        if target_format in ['base', 'both']:
            result['base_format'] = {
                f"{base_name}_base_units": int(field_value) if isinstance(field_value, (int, str)) else field_value,
                f"{base_name}_base_denom": denomination
            }
        
        if target_format in ['display', 'both']:
            if isinstance(field_value, (int, str)):
                try:
                    base_amount = int(field_value)
                    display_amount, display_symbol = self.base_to_display(base_amount, denomination)
                    if display_amount is not None:
                        result['display_format'] = {
                            f"{base_name}_display_amount": str(display_amount),
                            f"{base_name}_display_symbol": display_symbol
                        }
                except (ValueError, TypeError):
                    result['display_error'] = f"Could not convert {field_value} to display format"
        
        return result
    
    def get_supported_assets(self) -> List[Dict[str, Any]]:
        """Get list of all supported assets with their denomination info."""
        supported = []
        
        for asset_name, config in self.assets.items():
            base_denom = config['denominations']['base_denom']
            display_denom = config['denominations']['display_denom']
            conversion = config['conversion']
            
            supported.append({
                'asset_name': asset_name,
                'description': config['description'],
                'base_denomination': {
                    'name': base_denom['name'],
                    'description': base_denom['description'],
                    'data_type': base_denom['data_type']
                },
                'display_denomination': {
                    'name': display_denom['name'],
                    'description': display_denom['description'],
                    'data_type': display_denom['data_type'],
                    'precision': display_denom['precision']
                },
                'conversion_factor': conversion['base_to_display_factor'],
                'conversion_formula': conversion['formula']
            })
        
        return supported


# Usage examples and testing
if __name__ == "__main__":
    converter = DenominationConverter()
    
    print("=== Denomination Converter Examples ===\n")
    
    # Example 1: Base to display conversion
    print("1. Base to Display Conversion:")
    base_amount = 1500000000  # 1.5 HASH in nhash
    display_amount, symbol = converter.base_to_display(base_amount, "nhash")
    print(f"   {base_amount} nhash = {display_amount} {symbol}")
    
    # Example 2: Display to base conversion
    print("\n2. Display to Base Conversion:")
    base_result = converter.display_to_base("1.5", "HASH")
    print(f"   1.5 HASH = {base_result} nhash")
    
    # Example 3: Create amount object
    print("\n3. Standardized Amount Object:")
    amount_obj = converter.create_amount_object(1500000000, "nhash", include_display=True)
    print(f"   Amount object: {amount_obj}")
    
    # Example 4: Multi-asset response
    print("\n4. Multi-Asset Response:")
    amounts = {
        "nhash": 1000000000,
        "uusd.trading": 500000,
        "neth.figure.se": 2000000000
    }
    multi_response = converter.create_multi_asset_response(amounts)
    print(f"   Multi-asset response:")
    for balance in multi_response['asset_balances']:
        print(f"     {balance}")
    
    # Example 5: Field conversion
    print("\n5. Field Conversion:")
    field_result = converter.convert_field_to_standardized(
        "available_total_amount_nhash", 
        1000000000, 
        "both"
    )
    print(f"   Field conversion result:")
    for key, value in field_result.items():
        print(f"     {key}: {value}")
    
    # Example 6: Supported assets
    print("\n6. Supported Assets:")
    assets = converter.get_supported_assets()
    for asset in assets:
        print(f"   {asset['asset_name']}: {asset['base_denomination']['name']} -> {asset['display_denomination']['name']}")
        print(f"     Factor: {asset['conversion_factor']} ({asset['conversion_formula']})")