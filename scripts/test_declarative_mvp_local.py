#!/usr/bin/env python3
"""
Local test for Declarative Dashboard MVP - No S3 Required

This creates local JSON files to simulate the declarative loading process.
"""

import json
import os
import time
from pathlib import Path

# Create test directory
test_dir = Path("web-assets/test-declarations/demo")
test_dir.mkdir(parents=True, exist_ok=True)

def create_test_declarations():
    """Create the three declaration files locally."""
    
    print("🚀 Creating Local Declarative Dashboard Test Files")
    print("=" * 60)
    
    # Phase 1: Layout Declaration
    print("\n📄 Creating layout.json...")
    layout = {
        "version": "1.0",
        "timestamp": "2024-01-15T12:00:00Z",
        "html": """
        <div id='test-dashboard'>
            <header>
                <h1>Local Test Dashboard</h1>
                <div id='status'>Layout Loaded!</div>
            </header>
            <main>
                <div id='chart1' class='chart-panel'>
                    <h2>Price Chart</h2>
                    <div class='placeholder'>Waiting for Plotly...</div>
                </div>
                <div id='chart2' class='chart-panel'>
                    <h2>Distribution</h2>
                    <div class='placeholder'>Waiting for Plotly...</div>
                </div>
            </main>
        </div>
        """,
        "css": """
        body { margin: 0; background: #0a0a0a; color: #fff; font-family: system-ui; }
        #test-dashboard { padding: 20px; }
        header { margin-bottom: 20px; }
        h1 { color: #00ff88; }
        #status { color: #0088ff; margin: 10px 0; }
        main { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .chart-panel { background: #1a1a1a; padding: 20px; border-radius: 8px; min-height: 300px; }
        .placeholder { color: #666; text-align: center; margin-top: 100px; }
        """
    }
    
    with open(test_dir / "layout.json", "w") as f:
        json.dump(layout, f, indent=2)
    print("✅ Created layout.json")
    
    # Phase 2: Plotly Declaration
    print("\n📊 Creating plotly.json...")
    plotly = {
        "version": "1.0",
        "timestamp": "2024-01-15T12:00:05Z",
        "charts": [
            {
                "id": "price-chart",
                "containerId": "chart1",
                "layout": {
                    "title": "Hash Price Over Time",
                    "xaxis": {"title": "Time"},
                    "yaxis": {"title": "Price (USD)"},
                    "paper_bgcolor": "#1a1a1a",
                    "plot_bgcolor": "#0f0f0f"
                }
            },
            {
                "id": "dist-chart",
                "containerId": "chart2",
                "layout": {
                    "title": "Portfolio Distribution",
                    "paper_bgcolor": "#1a1a1a",
                    "plot_bgcolor": "#0f0f0f"
                }
            }
        ]
    }
    
    with open(test_dir / "plotly.json", "w") as f:
        json.dump(plotly, f, indent=2)
    print("✅ Created plotly.json")
    
    # Phase 3: Data Declaration
    print("\n📈 Creating data.json...")
    data = {
        "version": "1.0",
        "timestamp": "2024-01-15T12:00:10Z",
        "datasets": [
            {
                "chartId": "price-chart",
                "traces": [{
                    "x": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
                    "y": [0.0082, 0.0085, 0.0087, 0.0084],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "line": {"color": "#00ff88"}
                }]
            },
            {
                "chartId": "dist-chart",
                "traces": [{
                    "labels": ["Staked", "Available", "Rewards"],
                    "values": [45, 35, 20],
                    "type": "pie",
                    "hole": 0.4
                }]
            }
        ]
    }
    
    with open(test_dir / "data.json", "w") as f:
        json.dump(data, f, indent=2)
    print("✅ Created data.json")
    
    print("\n" + "=" * 60)
    print("✨ Test files created!")
    print(f"\n📁 Files location: {test_dir.absolute()}")
    print("\n🌐 To test the progressive loading:")
    print("1. Open /dashboard/declarative?session=demo")
    print("2. Watch the dashboard load in 3 phases")
    print("3. Delete individual JSON files to see partial loading")
    print("\n💡 The browser polls these files every 2 seconds")
    
    # Also create a simple test HTML
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Declarative Dashboard Test</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
        <h1>Open Developer Console to see polling activity</h1>
        <p>Files being polled from: web-assets/test-declarations/demo/</p>
        <ul>
            <li>layout.json - HTML/CSS structure</li>
            <li>plotly.json - Chart configurations</li>
            <li>data.json - Chart data</li>
        </ul>
    </body>
    </html>
    """
    
    with open(test_dir / "test.html", "w") as f:
        f.write(test_html)
    
    return test_dir

if __name__ == "__main__":
    test_dir = create_test_declarations()
    print(f"\n🔧 You can modify files in: {test_dir}")
    print("🔄 Delete files to simulate progressive loading!")