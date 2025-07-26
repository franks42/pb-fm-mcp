#!/usr/bin/env python3
"""
Browser Automation Demo Script

This script demonstrates the revolutionary AI-controlled browser automation capabilities
through MCP functions. It shows how Claude can interact with dashboards like a human user.

Usage:
    python scripts/demo_browser_automation.py --dashboard-url <URL>
"""

import asyncio
import argparse
import json
from datetime import datetime
from typing import Dict, Any

# This would connect to the deployed MCP server
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import our browser automation functions for local testing
from functions.browser_automation import (
    browser_navigate,
    browser_screenshot, 
    browser_click,
    browser_type,
    browser_get_text,
    browser_execute_javascript,
    browser_wait_for_element,
    browser_get_page_info,
    browser_close_session
)


class BrowserAutomationDemo:
    """Demonstrates AI-controlled browser automation capabilities."""
    
    def __init__(self):
        self.session_id = None
        self.results = []
    
    async def log_step(self, step: str, result: Dict[Any, Any]):
        """Log demonstration step with results."""
        timestamp = datetime.now().isoformat()
        print(f"\n🤖 [{timestamp}] {step}")
        
        if result.get('success'):
            print(f"✅ Success: {result.get('message', 'Operation completed')}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        # Store detailed results
        self.results.append({
            'timestamp': timestamp,
            'step': step,
            'result': result
        })
        
        # Extract session ID if available
        if result.get('session_id'):
            self.session_id = result['session_id']
    
    async def demo_dashboard_navigation(self, dashboard_url: str):
        """Demonstrate basic dashboard navigation."""
        print("\n" + "="*80)
        print("🚀 DEMO: AI-Controlled Dashboard Navigation")
        print("="*80)
        
        # Step 1: Navigate to dashboard
        result = await browser_navigate(dashboard_url)
        await self.log_step("Navigate to dashboard", result)
        
        if not result.get('success'):
            return False
        
        # Step 2: Take initial screenshot
        result = await browser_screenshot(self.session_id, context="Initial dashboard view")
        await self.log_step("Capture initial screenshot", result)
        
        # Step 3: Get page information
        result = await browser_get_page_info(self.session_id)
        await self.log_step("Analyze page information", result)
        
        return True
    
    async def demo_dashboard_interaction(self):
        """Demonstrate interactive dashboard controls."""
        print("\n" + "="*80)
        print("🎮 DEMO: AI-Controlled Dashboard Interaction")
        print("="*80)
        
        # Step 1: Look for control buttons
        result = await browser_execute_javascript(
            """
            // Find all control buttons on the page
            const buttons = Array.from(document.querySelectorAll('button.control-button'));
            return buttons.map(btn => ({
                text: btn.textContent.trim(),
                id: btn.id,
                onclick: btn.onclick ? btn.onclick.toString() : null,
                visible: btn.offsetParent !== null
            }));
            """,
            self.session_id
        )
        await self.log_step("Discover control buttons", result)
        
        if result.get('success') and result.get('result'):
            buttons = result['result']
            print(f"   📊 Found {len(buttons)} control buttons:")
            for btn in buttons:
                print(f"      • {btn['text']} (visible: {btn['visible']})")
        
        # Step 2: Click on Portfolio Health button if available
        result = await browser_click(
            "button:contains('Portfolio Health'), button:contains('🏥')",
            self.session_id,
            wait_timeout=5
        )
        await self.log_step("Click Portfolio Health button", result)
        
        # Step 3: Wait for visualization to load
        result = await browser_wait_for_element(
            "#plotly-div, .visualization-container",
            self.session_id,
            state="visible",
            timeout_seconds=15
        )
        await self.log_step("Wait for visualization to load", result)
        
        # Step 4: Take screenshot of loaded visualization
        result = await browser_screenshot(
            self.session_id, 
            context="Portfolio visualization loaded"
        )
        await self.log_step("Capture visualization screenshot", result)
        
        return True
    
    async def demo_dashboard_analysis(self):
        """Demonstrate AI analysis of dashboard data."""
        print("\n" + "="*80)
        print("🔍 DEMO: AI-Powered Dashboard Analysis")
        print("="*80)
        
        # Step 1: Extract status message
        result = await browser_get_text(
            "#status, .status-message",
            self.session_id
        )
        await self.log_step("Read dashboard status", result)
        
        # Step 2: Extract AI insights if available
        result = await browser_get_text(
            "#ai-insights, .ai-insights",
            self.session_id
        )
        await self.log_step("Read AI insights", result)
        
        # Step 3: Analyze chart data using JavaScript
        result = await browser_execute_javascript(
            """
            // Analyze Plotly chart data if available
            if (window.Plotly && window.Plotly.d3) {
                const plotlyDiv = document.getElementById('plotly-div');
                if (plotlyDiv && plotlyDiv.data) {
                    return {
                        charts_found: plotlyDiv.data.length,
                        chart_types: plotlyDiv.data.map(trace => trace.type),
                        has_data: plotlyDiv.data.some(trace => trace.x && trace.x.length > 0)
                    };
                }
            }
            return { message: 'No Plotly charts found' };
            """,
            self.session_id
        )
        await self.log_step("Analyze chart data", result)
        
        # Step 4: Check for error messages
        result = await browser_execute_javascript(
            """
            // Look for error messages or warnings
            const errors = Array.from(document.querySelectorAll('.error, .warning, [class*="error"], [class*="warning"]'));
            return errors.map(el => ({
                text: el.textContent.trim(),
                class: el.className,
                visible: el.offsetParent !== null
            }));
            """,
            self.session_id
        )
        await self.log_step("Check for error messages", result)
        
        return True
    
    async def demo_dashboard_testing(self):
        """Demonstrate automated dashboard testing."""
        print("\n" + "="*80)
        print("🧪 DEMO: AI-Driven Dashboard Testing")
        print("="*80)
        
        # Step 1: Test screenshot button
        result = await browser_click(
            "button:contains('Screenshot'), button:contains('📸')",
            self.session_id
        )
        await self.log_step("Test screenshot button", result)
        
        # Step 2: Test theme toggle
        result = await browser_click(
            "button:contains('Theme'), button:contains('🌙')",
            self.session_id
        )
        await self.log_step("Test theme toggle button", result)
        
        # Step 3: Verify theme change
        result = await browser_execute_javascript(
            """
            // Check if theme changed
            const body = document.body;
            const computedStyle = window.getComputedStyle(body);
            return {
                background_color: computedStyle.backgroundColor,
                color: computedStyle.color,
                background_image: computedStyle.backgroundImage
            };
            """,
            self.session_id
        )
        await self.log_step("Verify theme change", result)
        
        # Step 4: Test responsive design
        result = await browser_execute_javascript(
            """
            // Test different viewport sizes
            const originalWidth = window.innerWidth;
            const originalHeight = window.innerHeight;
            
            // Simulate mobile viewport
            window.resizeTo(375, 667);
            
            setTimeout(() => {
                const mobileLayout = {
                    width: window.innerWidth,
                    height: window.innerHeight,
                    control_panel_visible: document.querySelector('.control-panel').offsetParent !== null
                };
                
                // Restore original size
                window.resizeTo(originalWidth, originalHeight);
                
                return {
                    original: { width: originalWidth, height: originalHeight },
                    mobile: mobileLayout
                };
            }, 100);
            """,
            self.session_id
        )
        await self.log_step("Test responsive design", result)
        
        return True
    
    async def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "="*80)
        print("📋 AUTOMATION REPORT")
        print("="*80)
        
        success_count = sum(1 for r in self.results if r['result'].get('success'))
        total_count = len(self.results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        print(f"📊 Overall Success Rate: {success_rate:.1f}% ({success_count}/{total_count})")
        print(f"⏱️  Total Steps Executed: {total_count}")
        print(f"✅ Successful Operations: {success_count}")
        print(f"❌ Failed Operations: {total_count - success_count}")
        
        # Group results by category
        categories = {
            'Navigation': ['Navigate', 'Analyze page'],
            'Interaction': ['Click', 'Type', 'Wait'],
            'Analysis': ['Read', 'Extract', 'Analyze'],
            'Testing': ['Test', 'Verify', 'Check']
        }
        
        print("\n📈 Results by Category:")
        for category, keywords in categories.items():
            category_results = [
                r for r in self.results 
                if any(keyword in r['step'] for keyword in keywords)
            ]
            if category_results:
                category_success = sum(1 for r in category_results if r['result'].get('success'))
                category_total = len(category_results)
                category_rate = (category_success / category_total * 100)
                print(f"   {category}: {category_rate:.1f}% ({category_success}/{category_total})")
        
        # Save detailed report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_steps': total_count,
                'successful_steps': success_count,
                'success_rate': success_rate
            },
            'detailed_results': self.results
        }
        
        report_file = f"browser_automation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
    
    async def cleanup(self):
        """Clean up browser session."""
        if self.session_id:
            result = await browser_close_session(self.session_id)
            await self.log_step("Close browser session", result)


async def main():
    """Main demonstration script."""
    parser = argparse.ArgumentParser(description='Browser Automation Demo')
    parser.add_argument(
        '--dashboard-url', 
        default='https://7fucgrbd16.execute-api.us-west-1.amazonaws.com/v1/dashboard/demo-automation',
        help='Dashboard URL to test'
    )
    parser.add_argument(
        '--skip-interaction',
        action='store_true',
        help='Skip interactive demo steps'
    )
    
    args = parser.parse_args()
    
    demo = BrowserAutomationDemo()
    
    try:
        print("🤖 Starting AI-Controlled Browser Automation Demo")
        print(f"🎯 Target URL: {args.dashboard_url}")
        
        # Run demonstration phases
        success = await demo.demo_dashboard_navigation(args.dashboard_url)
        
        if success and not args.skip_interaction:
            await demo.demo_dashboard_interaction()
            await demo.demo_dashboard_analysis()
            await demo.demo_dashboard_testing()
        
        # Generate comprehensive report
        await demo.generate_report()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Demo failed with error: {e}")
    finally:
        # Always cleanup
        await demo.cleanup()
        print("\n🏁 Demo completed")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())


# Example revolutionary use cases this enables:

"""
🎯 REVOLUTIONARY USE CASES:

1. **Conversational Dashboard Debugging**
   Claude: "I notice your chart isn't loading. Let me click the refresh button and check for errors."
   → Automatically clicks refresh, analyzes console logs, reports back

2. **Automated User Journey Testing**  
   Claude: "Let me test the complete user workflow from login to report generation."
   → Navigates through entire process, validates each step, reports issues

3. **Real-time UX Optimization**
   Claude: "Your users struggle with this layout. Let me test different arrangements."
   → Modifies CSS via JavaScript, tests usability, measures improvements

4. **Cross-device Compatibility Testing**
   Claude: "Let me check how this looks on mobile devices."
   → Simulates different screen sizes, tests responsive behavior

5. **Performance Analysis**
   Claude: "I'll measure how long each interaction takes and identify bottlenecks."
   → Times user actions, analyzes performance metrics, suggests optimizations

6. **Accessibility Validation**
   Claude: "Let me check if this dashboard meets accessibility standards."
   → Tests keyboard navigation, screen reader compatibility, color contrast

7. **Data Validation Testing**
   Claude: "I'll verify all the numbers match between different dashboard views."
   → Extracts data from multiple sources, cross-validates for consistency

This creates the first truly conversational approach to web application testing and optimization!
"""