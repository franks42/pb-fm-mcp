"""
State Management Functions for Stateless MCP Server

These functions provide reference data that AI agents can cache to minimize
redundant fetching and enable local conversions and formatting.

Key functions:
- get_denomination_conversion_table(): Complete conversion info for all assets
- get_system_timezone_info(): Timezone context and current UTC time
- get_field_naming_conventions(): Standardized field naming reference
"""

from datetime import datetime, UTC
from typing import Dict, Any, List
from denomination_converter import DenominationConverter


class StateManagementsProvider:
    """
    Provides state management data for AI agents to cache and use locally.
    
    Optimizes stateless server performance by providing reference data once
    rather than including conversion/formatting data in every response.
    """
    
    def __init__(self, denomination_registry_path: str = "docs/denomination_registry.yaml"):
        """Initialize with denomination converter."""
        self.denomination_converter = DenominationConverter(denomination_registry_path)
        self.table_version = datetime.now(UTC).isoformat()
    
    def get_denomination_conversion_table(self) -> Dict[str, Any]:
        """
        Get complete denomination conversion table for AI agent caching.
        
        AI agents should cache this data and use it for local conversions
        rather than requesting display formats from the server.
        
        Returns:
            Complete conversion table with all supported assets
        """
        current_time = datetime.now(UTC).isoformat()
        
        # Get all supported assets
        supported_assets = self.denomination_converter.get_supported_assets()
        
        # Build comprehensive conversion table
        conversion_table = {
            "table_version": self.table_version,
            "last_updated": current_time,
            "description": "Complete denomination conversion reference for AI agent caching",
            "usage_instructions": {
                "cache_strategy": "Cache this table for the entire session",
                "update_frequency": "Re-fetch daily or when table_version changes",
                "conversion_pattern": "display_amount = base_amount / conversion_factor",
                "formatting_rule": "Use decimal_places for display precision"
            },
            "assets": []
        }
        
        # Add detailed info for each asset
        for asset in supported_assets:
            asset_info = {
                "asset_name": asset['asset_name'],
                "description": asset['description'],
                
                # Base denomination (for calculations)
                "base_denomination": {
                    "name": asset['base_denomination']['name'],
                    "description": asset['base_denomination']['description'],
                    "data_type": "integer",
                    "use_for": "calculations_and_api_responses"
                },
                
                # Display denomination (for user presentation)
                "display_denomination": {
                    "name": asset['display_denomination']['name'],
                    "description": asset['display_denomination']['description'],
                    "data_type": "decimal",
                    "use_for": "user_display_only"
                },
                
                # Conversion information
                "conversion": {
                    "factor": asset['conversion_factor'],
                    "formula": asset['conversion_formula'],
                    "reverse_formula": f"base_amount = display_amount * {asset['conversion_factor']}",
                    "decimal_places": self._extract_decimal_places(asset['display_denomination']['precision']),
                    "precision_note": "Always use base amounts for calculations to avoid precision loss"
                },
                
                # Field naming patterns
                "field_naming": {
                    "base_field_pattern": f"*_{self._get_suffix(asset['base_denomination']['name'])}",
                    "examples": [
                        f"available_total_amount_{self._get_suffix(asset['base_denomination']['name'])}",
                        f"delegated_staked_amount_{self._get_suffix(asset['base_denomination']['name'])}"
                    ]
                },
                
                # Example conversions
                "example_conversions": [
                    {
                        "base_amount": asset['conversion_factor'],  # 1 unit
                        "display_amount": "1.000000000" if asset['conversion_factor'] >= 1000000000 else "1.000000",
                        "formatted_display": f"1.0 {asset['display_denomination']['name']}"
                    },
                    {
                        "base_amount": asset['conversion_factor'] // 2,  # 0.5 units
                        "display_amount": "0.500000000" if asset['conversion_factor'] >= 1000000000 else "0.500000",
                        "formatted_display": f"0.5 {asset['display_denomination']['name']}"
                    }
                ]
            }
            
            conversion_table["assets"].append(asset_info)
        
        # Add quick lookup tables
        conversion_table["quick_lookup"] = {
            "base_denom_to_factor": {
                asset['base_denomination']['name']: asset['conversion_factor']
                for asset in supported_assets
            },
            "suffix_to_factor": {
                self._get_suffix(asset['base_denomination']['name']): asset['conversion_factor']
                for asset in supported_assets
            },
            "display_symbol_to_factor": {
                asset['display_denomination']['name']: asset['conversion_factor']
                for asset in supported_assets
            }
        }
        
        return conversion_table
    
    def get_system_timezone_info(self) -> Dict[str, Any]:
        """
        Get system timezone information for AI agent reference.
        
        All MCP server responses use UTC. AI agents should convert to
        user's local timezone for display purposes.
        
        Returns:
            Timezone context and current UTC time
        """
        current_utc = datetime.now(UTC)
        
        return {
            "server_timezone": "UTC",
            "current_utc_time": current_utc.isoformat(),
            "current_utc_timestamp": int(current_utc.timestamp()),
            "iso_format_standard": "ISO 8601 with explicit timezone (Z or +00:00)",
            
            "server_policy": {
                "all_timestamps_utc": True,
                "timezone_awareness": "All timestamps include explicit timezone",
                "no_local_time_assumptions": "Server never assumes caller's timezone",
                "date_calculations": "All server calculations use UTC"
            },
            
            "ai_agent_recommendations": {
                "caching": "Cache user's timezone preference for session",
                "conversion": "Convert all UTC times to user's local timezone for display",
                "formatting": "Use user's preferred date/time format",
                "calculations": "Always convert user input to UTC before sending to server",
                "validation": "Validate that all timestamps from server include timezone info"
            },
            
            "example_conversions": {
                "server_utc": "2024-07-17T10:30:00.123Z",
                "user_est": "2024-07-17T06:30:00.123-04:00 (July 17, 2024 at 6:30 AM EDT)",
                "user_pst": "2024-07-17T03:30:00.123-07:00 (July 17, 2024 at 3:30 AM PDT)",
                "user_cet": "2024-07-17T12:30:00.123+02:00 (July 17, 2024 at 12:30 PM CEST)"
            },
            
            "timestamp_patterns": {
                "standard_format": "YYYY-MM-DDTHH:MM:SS.sssZ",
                "alternative_format": "YYYY-MM-DDTHH:MM:SS.sss+00:00",
                "parsing_note": "Both formats represent UTC time",
                "millisecond_precision": "Server provides millisecond precision when available"
            }
        }
    
    def get_field_naming_conventions(self) -> Dict[str, Any]:
        """
        Get complete field naming conventions for AI agent reference.
        
        Helps AI agents understand and predict field names across all responses.
        
        Returns:
            Complete field naming reference
        """
        return {
            "version": self.table_version,
            "description": "Standardized field naming conventions across all MCP responses",
            
            "denomination_suffixes": {
                "description": "All amount fields include denomination suffix for clarity",
                "pattern": "field_name_{denomination_suffix}",
                "examples": {
                    "_nhash": "HASH amounts in nano-HASH base units",
                    "_uusd": "USD amounts in micro-USD base units", 
                    "_neth": "ETH amounts in nano-ETH base units",
                    "_uusdc": "USDC amounts in micro-USDC base units",
                    "_nsol": "SOL amounts in nano-SOL base units",
                    "_uxrp": "XRP amounts in micro-XRP base units",
                    "_uylds": "YLDS amounts in micro-YLDS base units"
                }
            },
            
            "field_categories": {
                "available_amounts": {
                    "pattern": "available_*_nhash",
                    "description": "HASH amounts available in wallet (not delegated)",
                    "examples": [
                        "available_total_amount_nhash",
                        "available_spendable_amount_nhash", 
                        "available_committed_amount_nhash",
                        "available_unvested_amount_nhash"
                    ]
                },
                
                "delegated_amounts": {
                    "pattern": "delegated_*_nhash", 
                    "description": "HASH amounts delegated to validators",
                    "examples": [
                        "delegated_staked_amount_nhash",
                        "delegated_rewards_amount_nhash",
                        "delegated_redelegated_amount_nhash",
                        "delegated_unbonding_amount_nhash",
                        "delegated_total_amount_nhash"
                    ]
                },
                
                "vesting_amounts": {
                    "pattern": "vesting_*_nhash",
                    "description": "HASH amounts related to vesting schedules",
                    "examples": [
                        "vesting_original_amount_nhash",
                        "vesting_total_vested_amount_nhash",
                        "vesting_total_unvested_amount_nhash",
                        "vesting_coverage_deficit_nhash"
                    ]
                },
                
                "supply_amounts": {
                    "pattern": "*_supply_nhash or *_nhash",
                    "description": "HASH token supply statistics",
                    "examples": [
                        "max_supply_nhash",
                        "current_supply_nhash",
                        "circulating_supply_nhash",
                        "burned_nhash",
                        "community_pool_nhash",
                        "bonded_nhash",
                        "locked_nhash"
                    ]
                }
            },
            
            "timestamp_fields": {
                "pattern": "*_date or *_time or *_timestamp",
                "format": "ISO 8601 UTC with explicit timezone",
                "examples": {
                    "vesting_start_date": "When vesting period begins",
                    "vesting_end_date": "When vesting period ends",
                    "last_updated_utc": "When data was last updated",
                    "block_timestamp": "When blockchain block was created"
                }
            },
            
            "identifier_fields": {
                "account_address": "Bech32-encoded Provenance account address",
                "validator_address": "Bech32-encoded validator operator address", 
                "transaction_hash": "Hexadecimal transaction identifier",
                "trading_pair_id": "Trading pair identifier (e.g., 'HASH-USD')",
                "asset_denom": "Full asset denomination (e.g., 'nhash', 'uusd.trading')"
            },
            
            "boolean_flags": {
                "is_vesting": "Boolean indicating active vesting restrictions",
                "is_active": "Boolean indicating active status",
                "earning_rewards": "Boolean indicating if delegation earns rewards"
            }
        }
    
    def _extract_decimal_places(self, precision_str: str) -> int:
        """Extract decimal places from precision string."""
        if 'decimal places' in precision_str:
            return int(precision_str.split()[0])
        return 6  # Default fallback
    
    def _get_suffix(self, denomination: str) -> str:
        """Get suffix for denomination."""
        suffix_mapping = {
            'nhash': 'nhash',
            'neth.figure.se': 'neth',
            'uusd.trading': 'uusd',
            'uusdc.figure.se': 'uusdc',
            'nsol.figure.se': 'nsol',
            'uxrp.figure.se': 'uxrp',
            'uylds.fcc': 'uylds'
        }
        return suffix_mapping.get(denomination, denomination.replace('.', '_'))


# Example AI Agent Integration Code (for documentation)
EXAMPLE_AI_AGENT_CODE = '''
# Example AI Agent Integration

class AIAgentStateMgmt:
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        self.conversion_table = None
        self.timezone_info = None
        
    async def initialize_session(self):
        """Initialize session by caching reference data."""
        # Cache conversion table
        self.conversion_table = await self.mcp_client.call(
            "get_denomination_conversion_table"
        )
        
        # Cache timezone info
        self.timezone_info = await self.mcp_client.call(
            "get_system_timezone_info"
        )
        
        print(f"Cached conversion table for {len(self.conversion_table['assets'])} assets")
        print(f"Server timezone: {self.timezone_info['server_timezone']}")
    
    def convert_amount_for_display(self, base_amount: int, field_name: str) -> str:
        """Convert base amount to user-friendly display."""
        # Extract denomination suffix from field name
        suffix = None
        for suf in ["_nhash", "_uusd", "_neth", "_uusdc", "_nsol", "_uxrp", "_uylds"]:
            if field_name.endswith(suf):
                suffix = suf[1:]  # Remove underscore
                break
        
        if not suffix:
            return str(base_amount)  # Fallback
        
        # Look up conversion factor
        factor = self.conversion_table["quick_lookup"]["suffix_to_factor"].get(suffix)
        if not factor:
            return str(base_amount)
        
        # Convert to display amount
        display_amount = base_amount / factor
        
        # Find asset info for formatting
        for asset in self.conversion_table["assets"]:
            if asset["base_denomination"]["name"].endswith(suffix):
                decimal_places = asset["conversion"]["decimal_places"]
                symbol = asset["display_denomination"]["name"]
                formatted = f"{display_amount:.{decimal_places}f}".rstrip('0').rstrip('.')
                return f"{formatted} {symbol}"
        
        return f"{display_amount}"
    
    def convert_timestamp_for_display(self, utc_timestamp: str, user_timezone: str = "America/New_York") -> str:
        """Convert UTC timestamp to user's local time."""
        # Parse UTC timestamp
        from datetime import datetime
        import pytz
        
        # Handle both Z and +00:00 formats
        if utc_timestamp.endswith('Z'):
            dt = datetime.fromisoformat(utc_timestamp[:-1] + '+00:00')
        else:
            dt = datetime.fromisoformat(utc_timestamp)
        
        # Convert to user timezone
        user_tz = pytz.timezone(user_timezone)
        local_dt = dt.astimezone(user_tz)
        
        # Format for user
        return local_dt.strftime("%B %d, %Y at %I:%M %p %Z")

# Usage example:
async def main():
    agent = AIAgentStateMgmt(mcp_client)
    await agent.initialize_session()
    
    # Later, when processing MCP responses:
    response = await mcp_client.call("get_hash_token_statistics")
    
    # Convert amounts for user display
    max_supply = response["max_supply_nhash"]  # e.g., 100000000000000000
    display_max = agent.convert_amount_for_display(max_supply, "max_supply_nhash")
    # Result: "100.0 HASH"
    
    # Convert timestamps for user display
    timestamp = response["last_updated_utc"]  # e.g., "2024-07-17T10:30:00.123Z"
    display_time = agent.convert_timestamp_for_display(timestamp, "America/New_York") 
    # Result: "July 17, 2024 at 06:30 AM EDT"
'''


# Testing and examples
if __name__ == "__main__":
    provider = StateManagementsProvider()
    
    print("=== Denomination Conversion Table ===")
    table = provider.get_denomination_conversion_table()
    print(f"Table version: {table['table_version']}")
    print(f"Supported assets: {len(table['assets'])}")
    
    for asset in table['assets'][:2]:  # Show first 2 assets
        print(f"\n{asset['asset_name']}:")
        print(f"  Base: {asset['base_denomination']['name']}")
        print(f"  Display: {asset['display_denomination']['name']}")
        print(f"  Factor: {asset['conversion']['factor']}")
        print(f"  Example: {asset['example_conversions'][0]['base_amount']} base = {asset['example_conversions'][0]['display_amount']} display")
    
    print("\n=== Timezone Info ===")
    tz_info = provider.get_system_timezone_info()
    print(f"Server timezone: {tz_info['server_timezone']}")
    print(f"Current UTC: {tz_info['current_utc_time']}")
    print(f"Example EST conversion: {tz_info['example_conversions']['user_est']}")