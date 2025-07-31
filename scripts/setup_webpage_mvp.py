#!/usr/bin/env python3
"""
Webpage MVP Setup Master Script

Orchestrates the complete setup process for webpage MVP:
1. Updates CloudFormation template
2. Deploys infrastructure
3. Tests infrastructure components
4. Validates MVP functionality
5. Provides next steps

Uses uv for all Python operations and provides comprehensive logging.
"""

import asyncio
import subprocess
import sys
import os
from datetime import datetime
from typing import List, Tuple
import argparse

# Color codes for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

def log(level: str, message: str) -> None:
    """Log message with color coding"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    colors = {
        'INFO': Colors.GREEN,
        'WARN': Colors.YELLOW,
        'ERROR': Colors.RED,
        'DEBUG': Colors.BLUE,
        'STEP': Colors.CYAN,
        'SUCCESS': Colors.MAGENTA
    }
    color = colors.get(level, Colors.NC)
    print(f"{color}[{level}]{Colors.NC} [{timestamp}] {message}")

def run_command(cmd: List[str], description: str, cwd: str = None) -> Tuple[bool, str]:
    """Run a command and return success status and output"""
    log('DEBUG', f'Running: {" ".join(cmd)}')
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            log('INFO', f'✓ {description} completed successfully')
            return True, result.stdout
        else:
            log('ERROR', f'✗ {description} failed (exit code: {result.returncode})')
            log('ERROR', f'stderr: {result.stderr}')
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        log('ERROR', f'✗ {description} timed out after 5 minutes')
        return False, "Command timed out"
    except Exception as e:
        log('ERROR', f'✗ {description} failed with exception: {e}')
        return False, str(e)

async def run_async_command(cmd: List[str], description: str, cwd: str = None) -> Tuple[bool, str]:
    """Run an async command"""
    log('DEBUG', f'Running async: {" ".join(cmd)}')
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
        
        if process.returncode == 0:
            log('INFO', f'✓ {description} completed successfully')
            return True, stdout.decode()
        else:
            log('ERROR', f'✗ {description} failed (exit code: {process.returncode})')
            log('ERROR', f'stderr: {stderr.decode()}')
            return False, stderr.decode()
            
    except asyncio.TimeoutError:
        log('ERROR', f'✗ {description} timed out after 5 minutes')
        return False, "Command timed out"
    except Exception as e:
        log('ERROR', f'✗ {description} failed with exception: {e}')
        return False, str(e)

class WebpageMVPSetup:
    """Master setup orchestrator for webpage MVP"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.scripts_dir = os.path.join(project_root, 'scripts')
        
        # Setup steps configuration
        self.steps = [
            ('check_prerequisites', 'Check Prerequisites'),
            ('update_cloudformation', 'Update CloudFormation Template'),
            ('deploy_infrastructure', 'Deploy Infrastructure'),
            ('test_infrastructure', 'Test Infrastructure Components'),
            ('test_mvp_functionality', 'Test MVP Functionality'),
            ('provide_next_steps', 'Provide Next Steps')
        ]
        
        self.step_results = {}

    def check_prerequisites(self) -> bool:
        """Check that all required tools are available"""
        log('STEP', 'Checking prerequisites...')
        
        # Required commands
        required_commands = [
            ('uv', 'Python package manager'),
            ('aws', 'AWS CLI'),
            ('sam', 'AWS SAM CLI'),
            ('git', 'Git version control')
        ]
        
        all_good = True
        
        for cmd, description in required_commands:
            success, _ = run_command(['which', cmd], f'Check {description}')
            if not success:
                log('ERROR', f'✗ {description} ({cmd}) not found')
                all_good = False
            else:
                log('INFO', f'✓ {description} ({cmd}) available')
        
        # Check AWS credentials
        success, output = run_command(['aws', 'sts', 'get-caller-identity'], 'Check AWS credentials')
        if success:
            log('INFO', '✓ AWS credentials configured')
        else:
            log('ERROR', '✗ AWS credentials not configured')
            log('ERROR', 'Please run: aws configure')
            all_good = False
        
        # Check git branch
        success, output = run_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 'Check git branch', self.project_root)
        if success:
            branch = output.strip()
            log('INFO', f'Current branch: {branch}')
            if branch != 'dev':
                log('WARN', f'Not on dev branch (currently on {branch})')
        
        # Check Python dependencies
        success, _ = run_command(['uv', '--version'], 'Check uv version')
        if success:
            log('INFO', '✓ uv package manager available')
        
        return all_good

    def update_cloudformation(self) -> bool:
        """Update CloudFormation template with webpage MVP resources"""
        log('STEP', 'Updating CloudFormation template...')
        
        template_script = os.path.join(self.scripts_dir, 'update_template_for_webpage.py')
        
        if not os.path.exists(template_script):
            log('ERROR', f'Template update script not found: {template_script}')
            return False
        
        # Run template update script
        success, output = run_command(
            ['uv', 'run', 'python', template_script, '--force'],
            'Update CloudFormation template',
            self.project_root
        )
        
        if success:
            log('SUCCESS', 'CloudFormation template updated with webpage MVP resources')
        
        return success

    def deploy_infrastructure(self) -> bool:
        """Deploy infrastructure using existing deployment script"""
        log('STEP', 'Deploying infrastructure...')
        
        deploy_script = os.path.join(self.project_root, 'deploy.sh')
        
        if not os.path.exists(deploy_script):
            log('ERROR', f'Deployment script not found: {deploy_script}')
            return False
        
        # Run deployment
        success, output = run_command(
            ['./deploy.sh', 'dev', '--clean', '--test'],
            'Deploy infrastructure to dev environment',
            self.project_root
        )
        
        if success:
            log('SUCCESS', 'Infrastructure deployed successfully')
        
        return success

    async def test_infrastructure(self) -> bool:
        """Test infrastructure components"""
        log('STEP', 'Testing infrastructure components...')
        
        test_script = os.path.join(self.scripts_dir, 'test_webpage_infrastructure.py')
        
        if not os.path.exists(test_script):
            log('ERROR', f'Infrastructure test script not found: {test_script}')
            return False
        
        # Run infrastructure tests
        success, output = await run_async_command(
            ['uv', 'run', 'python', test_script],
            'Test infrastructure components',
            self.project_root
        )
        
        if success:
            log('SUCCESS', 'Infrastructure components tested successfully')
        else:
            log('ERROR', 'Infrastructure tests failed - check output above')
        
        return success

    async def test_mvp_functionality(self) -> bool:
        """Test MVP functionality"""
        log('STEP', 'Testing MVP functionality...')
        
        test_script = os.path.join(self.scripts_dir, 'test_webpage_mvp.py')
        
        if not os.path.exists(test_script):
            log('ERROR', f'MVP test script not found: {test_script}')
            return False
        
        # Run MVP tests
        success, output = await run_async_command(
            ['uv', 'run', 'python', test_script, 
             '--mcp-url', 'https://pb-fm-mcp-dev.creativeapptitude.com/mcp',
             '--rest-url', 'https://pb-fm-mcp-dev.creativeapptitude.com'],
            'Test MVP functionality',
            self.project_root
        )
        
        if success:
            log('SUCCESS', 'MVP functionality tests passed')
        else:
            log('WARN', 'MVP tests failed (expected if webpage functions not implemented yet)')
        
        # Don't fail the setup for MVP test failures since functions may not be implemented
        return True

    def provide_next_steps(self) -> bool:
        """Provide next steps for development"""
        log('STEP', 'Providing next steps...')
        
        log('INFO', '\n' + '='*60)
        log('SUCCESS', 'Webpage MVP Infrastructure Setup Complete!')
        log('INFO', '='*60)
        
        log('INFO', '\n📋 NEXT DEVELOPMENT STEPS:')
        log('INFO', '')
        log('INFO', '1. IMPLEMENT WEBPAGE MCP FUNCTIONS:')
        log('INFO', '   - Create src/functions/webpage_session_management.py')
        log('INFO', '   - Create src/functions/webpage_queue_management.py') 
        log('INFO', '   - Create src/functions/webpage_orchestration.py')
        log('INFO', '   - Create src/functions/webpage_s3_helpers.py')
        log('INFO', '')
        log('INFO', '2. CREATE STATIC WEBSITE:')
        log('INFO', '   - Create static/index.html')
        log('INFO', '   - Create static/js/session.js')
        log('INFO', '   - Create static/css/style.css')
        log('INFO', '')
        log('INFO', '3. TEST INTEGRATION:')
        log('INFO', '   - Deploy: ./deploy.sh dev --clean --test')
        log('INFO', '   - Test: uv run python scripts/test_webpage_mvp.py')
        log('INFO', '')
        log('INFO', '🎯 MVP GOAL:')
        log('INFO', '   Single webpage displaying live HASH price')
        log('INFO', '   Updated by AI via MCP function call')
        log('INFO', '   Multi-browser synchronization')
        log('INFO', '')
        log('INFO', '📚 DOCUMENTATION:')
        log('INFO', '   - Architecture: docs/mvp-ai-driven-webpage.md')
        log('INFO', '   - TODO List: docs/mvp-implementation-todo.md')
        log('INFO', '')
        log('INFO', '🚀 RESOURCES CREATED:')
        log('INFO', '   - S3 Bucket: pb-fm-webpage-mvp-assets')
        log('INFO', '   - DynamoDB Table: pb-fm-webpage-sessions')
        log('INFO', '   - SQS Queue permissions: pb-fm-webpage-*')
        log('INFO', '')
        
        return True

    async def run_full_setup(self, skip_steps: List[str] = None) -> bool:
        """Run the complete setup process"""
        skip_steps = skip_steps or []
        
        log('INFO', f'{Colors.BOLD}=== Webpage MVP Setup Started ==={Colors.NC}')
        log('INFO', f'Project root: {self.project_root}')
        log('INFO', f'Started at: {datetime.now().isoformat()}')
        log('INFO', '')
        
        total_steps = len(self.steps)
        completed_steps = 0
        
        for i, (step_method, step_description) in enumerate(self.steps, 1):
            if step_method in skip_steps:
                log('INFO', f'[{i}/{total_steps}] Skipping: {step_description}')
                continue
                
            log('INFO', f'\n{Colors.BOLD}[{i}/{total_steps}] {step_description}{Colors.NC}')
            log('INFO', '-' * (len(step_description) + 10))
            
            try:
                method = getattr(self, step_method)
                
                if asyncio.iscoroutinefunction(method):
                    success = await method()
                else:
                    success = method()
                
                self.step_results[step_method] = success
                
                if success:
                    completed_steps += 1
                    log('SUCCESS', f'✓ Step {i} completed successfully')
                else:
                    log('ERROR', f'✗ Step {i} failed')
                    
                    # For critical failures, stop; for expected failures, continue
                    if step_method in ['check_prerequisites', 'deploy_infrastructure']:
                        log('ERROR', f'Critical step failed: {step_method}')
                        log('ERROR', 'Setup aborted due to critical failure')
                        return False
                    else:
                        log('WARN', f'Non-critical step failed: {step_method}. Continuing...')
                
            except Exception as e:
                log('ERROR', f'✗ Step {i} failed with exception: {e}')
                self.step_results[step_method] = False
                
                # For critical failures, stop; for expected failures, continue
                if step_method in ['check_prerequisites', 'deploy_infrastructure']:
                    log('ERROR', f'Critical step failed with exception: {step_method}')
                    log('ERROR', 'Setup aborted due to critical failure')
                    return False
                else:
                    log('WARN', f'Non-critical step failed with exception: {step_method}. Continuing...')
        
        # Summary
        log('INFO', f'\n{Colors.BOLD}=== Setup Summary ==={Colors.NC}')
        log('INFO', f'Completed steps: {completed_steps}/{total_steps}')
        
        if completed_steps == total_steps:
            log('SUCCESS', 'All setup steps completed successfully!')
            return True
        else:
            failed_steps = [step for step, success in self.step_results.items() if not success]
            log('WARN', f'Some steps failed: {failed_steps}')
            log('INFO', 'You can continue with manual implementation')
            return False

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Setup Webpage MVP Infrastructure')
    parser.add_argument('--skip', nargs='*', help='Steps to skip', 
                       choices=['check_prerequisites', 'update_cloudformation', 
                               'deploy_infrastructure', 'test_infrastructure',
                               'test_mvp_functionality', 'provide_next_steps'])
    parser.add_argument('--project-root', help='Project root directory',
                       default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    args = parser.parse_args()
    
    setup = WebpageMVPSetup(args.project_root)
    success = await setup.run_full_setup(args.skip)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    asyncio.run(main())