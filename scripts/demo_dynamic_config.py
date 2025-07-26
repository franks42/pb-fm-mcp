#!/usr/bin/env python3
"""
Dynamic Plotly Configuration Demo

Shows how Claude can update chart appearance in real-time without redeployment.
This demonstrates the revolutionary feedback loop for UI development.

Usage:
    python scripts/demo_dynamic_config.py --dashboard-id test-dynamic --mcp-url <URL>
"""

import asyncio
import argparse
import json
import time
from datetime import datetime

# This simulates Claude using MCP functions
async def simulate_claude_updates(dashboard_id: str, mcp_url: str):
    """Simulate Claude updating chart configurations in real-time."""
    
    print("🎨 Dynamic Plotly Configuration Demo")
    print("=" * 60)
    print(f"Dashboard ID: {dashboard_id}")
    print(f"MCP URL: {mcp_url}")
    print("\nThis demo shows how Claude can update chart styles without redeployment.")
    print("Open the dashboard in your browser and click '✨ Live Config' to see updates!")
    print("=" * 60)
    
    # Sequence of style updates Claude might make
    style_updates = [
        {
            "name": "Modern Blue Theme",
            "updates": {
                "gauge.bar.color": "#00ccff",
                "gauge.bgcolor": "rgba(0, 204, 255, 0.1)",
                "gauge.borderwidth": 0,
                "title.font.color": "#00ccff"
            }
        },
        {
            "name": "High Contrast Mode",
            "updates": {
                "gauge.bar.color": "#00ff00",
                "gauge.bgcolor": "#000000",
                "gauge.bordercolor": "#ffffff",
                "gauge.borderwidth": 3
            }
        },
        {
            "name": "Elegant Gradient",
            "updates": {
                "gauge.bar.color": "#ff6b6b",
                "gauge.steps[0].color": "rgba(255, 107, 107, 0.2)",
                "gauge.steps[1].color": "rgba(255, 193, 7, 0.2)",
                "gauge.steps[2].color": "rgba(40, 167, 69, 0.2)"
            }
        },
        {
            "name": "Neon Cyberpunk",
            "updates": {
                "gauge.bar.color": "#39ff14",
                "gauge.borderwidth": 2,
                "gauge.bordercolor": "#ff1493",
                "gauge.bgcolor": "rgba(57, 255, 20, 0.1)",
                "title.font.color": "#39ff14"
            }
        },
        {
            "name": "Minimal Clean",
            "updates": {
                "gauge.bar.color": "#ffffff",
                "gauge.borderwidth": 1,
                "gauge.bordercolor": "rgba(255, 255, 255, 0.3)",
                "gauge.bgcolor": "transparent",
                "gauge.axis.visible": False
            }
        }
    ]
    
    print("\n🚀 Starting style updates in 5 seconds...")
    print("   (Make sure the dashboard is open with Live Config enabled)")
    await asyncio.sleep(5)
    
    for i, style in enumerate(style_updates, 1):
        print(f"\n🎨 Update {i}/{len(style_updates)}: {style['name']}")
        
        # Simulate MCP call to update chart config
        mcp_payload = {
            "jsonrpc": "2.0",
            "method": "update_chart_config",
            "params": {
                "dashboard_id": dashboard_id,
                "chart_element": "gauge",
                "updates": style['updates'],
                "context": f"demo_style_{style['name'].lower().replace(' ', '_')}"
            },
            "id": str(i)
        }
        
        print(f"   📡 Sending update: {json.dumps(style['updates'], indent=2)}")
        
        # In real usage, this would be an actual MCP call
        # For demo, we just simulate the delay
        await asyncio.sleep(3)
        
        print(f"   ✅ {style['name']} applied - check your dashboard!")
        
        # Wait between updates for visibility
        if i < len(style_updates):
            print(f"   ⏳ Next update in 5 seconds...")
            await asyncio.sleep(5)
    
    print("\n🎉 Demo complete! The feedback loop eliminates:")
    print("   ❌ Code changes in Python files")
    print("   ❌ SAM build process (2-3 minutes)")
    print("   ❌ SAM deploy process (2-3 minutes)")
    print("   ❌ Waiting for Lambda cold starts")
    print("\n✅ Instead, you get instant visual feedback!")


async def test_real_time_collaboration():
    """Show how user and AI can collaborate on design."""
    
    print("\n🤝 Real-Time Collaboration Example:")
    print("-" * 40)
    print("User: 'The gauge is hard to see in dark mode'")
    print("Claude: 'Let me try a few high-contrast options...'")
    print("\n[Claude updates colors in real-time]")
    print("\nUser: 'The second one looks good but make the bar brighter'")
    print("Claude: 'Adjusting the bar color now...'")
    print("\n[Claude fine-tunes the specific color]")
    print("\nUser: 'Perfect! Save that configuration'")
    print("Claude: 'Configuration saved. No deployment needed!'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Dynamic Plotly Configuration Demo')
    parser.add_argument(
        '--dashboard-id',
        default='test-dynamic-config',
        help='Dashboard ID for testing'
    )
    parser.add_argument(
        '--mcp-url',
        default='http://localhost:8000/mcp',
        help='MCP server URL'
    )
    
    args = parser.parse_args()
    
    # Run the demo
    asyncio.run(simulate_claude_updates(args.dashboard_id, args.mcp_url))
    asyncio.run(test_real_time_collaboration())
    
    print("\n💡 This dynamic configuration system enables:")
    print("   • Instant visual feedback during development")
    print("   • AI-driven design optimization")
    print("   • User-AI collaborative UI refinement")
    print("   • No code changes or redeployment needed")
    print("   • Version tracking of all configuration changes")
    print("\n🚀 Revolutionary for rapid UI iteration!")