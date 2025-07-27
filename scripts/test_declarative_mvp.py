#!/usr/bin/env python3
"""
Test script for the Declarative Dashboard MVP

This demonstrates the three-phase progressive loading:
1. HTML/CSS layout
2. Plotly configuration (empty charts)
3. Data population

Usage:
    uv run python scripts/test_declarative_mvp.py [--session SESSION_ID]
"""

import asyncio
import sys
import time
from datetime import datetime
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.functions.declarative_dashboard import (
    create_example_dashboard,
    declare_dashboard_layout,
    declare_plotly_charts,
    declare_chart_data
)


async def demo_progressive_loading(session_id: str = None):
    """Demonstrate progressive dashboard loading with delays between phases."""
    
    if session_id is None:
        session_id = f"demo_{int(time.time())}"
    
    print(f"\n🚀 Declarative Dashboard MVP Demo")
    print(f"Session ID: {session_id}")
    print("=" * 60)
    
    # Phase 1: Layout
    print("\n📄 Phase 1: Declaring HTML/CSS Layout...")
    layout_html = """
    <div id='mvp-container'>
        <header>
            <h1>Progressive Dashboard Loading Demo</h1>
            <div id='phase-status'>Phase 1: Layout Loaded</div>
        </header>
        <main id='chart-grid'>
            <div class='chart-panel'>
                <h2>Price Chart</h2>
                <div id='price-chart' class='chart-container'>
                    <div class='placeholder'>Waiting for Plotly configuration...</div>
                </div>
            </div>
            <div class='chart-panel'>
                <h2>Distribution</h2>
                <div id='dist-chart' class='chart-container'>
                    <div class='placeholder'>Waiting for Plotly configuration...</div>
                </div>
            </div>
        </main>
    </div>
    """
    
    layout_css = """
    body { margin: 0; background: #0a0a0a; color: #fff; font-family: system-ui; }
    #mvp-container { padding: 20px; max-width: 1200px; margin: 0 auto; }
    header { margin-bottom: 30px; }
    h1 { color: #00ff88; margin: 0 0 10px 0; }
    #phase-status { color: #0088ff; font-size: 14px; }
    #chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .chart-panel { background: #1a1a1a; border: 1px solid #333; padding: 20px; border-radius: 8px; }
    .chart-panel h2 { color: #00ff88; margin: 0 0 15px 0; font-size: 18px; }
    .chart-container { height: 300px; background: #0f0f0f; border-radius: 4px; position: relative; }
    .placeholder { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                   color: #666; font-size: 14px; }
    """
    
    layout_result = await declare_dashboard_layout(
        session_id=session_id,
        layout_html=layout_html,
        layout_css=layout_css
    )
    
    print(f"✅ Layout declared: {layout_result['s3_key']}")
    print(f"   Dashboard URL: {layout_result['dashboard_url']}")
    
    # Wait before Phase 2
    print("\n⏳ Waiting 5 seconds before Phase 2...")
    await asyncio.sleep(5)
    
    # Phase 2: Plotly Configuration
    print("\n📊 Phase 2: Declaring Plotly Charts (empty)...")
    charts = [
        {
            "id": "price-trends",
            "containerId": "price-chart",
            "layout": {
                "title": {"text": "Hash Price Trend", "font": {"color": "#00ff88"}},
                "xaxis": {"title": "Time", "gridcolor": "#333"},
                "yaxis": {"title": "Price (USD)", "gridcolor": "#333"},
                "paper_bgcolor": "#0f0f0f",
                "plot_bgcolor": "#0a0a0a",
                "font": {"color": "#fff"}
            },
            "config": {"displayModeBar": false, "responsive": true}
        },
        {
            "id": "distribution",
            "containerId": "dist-chart",
            "layout": {
                "title": {"text": "Portfolio Distribution", "font": {"color": "#00ff88"}},
                "paper_bgcolor": "#0f0f0f",
                "plot_bgcolor": "#0a0a0a",
                "font": {"color": "#fff"}
            },
            "config": {"displayModeBar": false, "responsive": true}
        }
    ]
    
    plotly_result = await declare_plotly_charts(
        session_id=session_id,
        charts=charts
    )
    
    print(f"✅ Plotly charts declared: {plotly_result['s3_key']}")
    print(f"   Charts configured: {plotly_result['charts_configured']}")
    
    # Wait before Phase 3
    print("\n⏳ Waiting 5 seconds before Phase 3...")
    await asyncio.sleep(5)
    
    # Phase 3: Data
    print("\n📈 Phase 3: Declaring Chart Data...")
    datasets = [
        {
            "chartId": "price-trends",
            "traces": [{
                "x": [f"2024-01-{i:02d}" for i in range(1, 11)],
                "y": [0.0080 + (i * 0.0001) + (0.0002 if i % 2 else -0.0001) for i in range(10)],
                "type": "scatter",
                "mode": "lines+markers",
                "name": "HASH/USD",
                "line": {"color": "#00ff88", "width": 3},
                "marker": {"size": 8, "color": "#00ff88"}
            }]
        },
        {
            "chartId": "distribution",
            "traces": [{
                "labels": ["Staked", "Available", "Rewards", "Locked"],
                "values": [45, 25, 20, 10],
                "type": "pie",
                "hole": 0.4,
                "marker": {"colors": ["#00ff88", "#0088ff", "#ff8800", "#ff0088"]}
            }]
        }
    ]
    
    data_result = await declare_chart_data(
        session_id=session_id,
        datasets=datasets
    )
    
    print(f"✅ Data declared: {data_result['s3_key']}")
    print(f"   Datasets configured: {data_result['datasets_configured']}")
    
    print("\n" + "=" * 60)
    print("✨ MVP Demo Complete!")
    print(f"\n🌐 View your progressive dashboard at:")
    print(f"   /dashboard/declarative?session={session_id}")
    print("\nThe dashboard will progressively load:")
    print("  1. HTML/CSS structure")
    print("  2. Empty Plotly charts with axes")
    print("  3. Live data populating the charts")
    print("\nRefresh the page to see it load again!")
    
    return session_id


async def quick_demo():
    """Create a complete dashboard instantly for testing."""
    print("\n🚀 Quick Demo: Creating complete dashboard...")
    
    result = await create_example_dashboard(
        session_id=f"quick_demo_{int(time.time())}",
        wallet_address="pb1yl3rpckr7k428d00fj43lxhgzfpasn9pylxpgm"
    )
    
    if result['success']:
        print(f"\n✅ Complete dashboard created!")
        print(f"   URL: {result['dashboard_url']}")
    else:
        print(f"\n❌ Failed: {result['error']}")
    
    return result


async def main():
    parser = argparse.ArgumentParser(description='Test Declarative Dashboard MVP')
    parser.add_argument('--session', help='Session ID for dashboard')
    parser.add_argument('--quick', action='store_true', help='Run quick demo (all phases at once)')
    args = parser.parse_args()
    
    try:
        if args.quick:
            await quick_demo()
        else:
            await demo_progressive_loading(args.session)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))