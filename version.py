"""
Version management for pb-fm-mcp

Automatically increments patch version for deployments and provides
consistent versioning across MCP and REST APIs.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Version file path
VERSION_FILE = Path(__file__).parent / "version.json"

# Default version if file doesn't exist
DEFAULT_VERSION = {
    "major": 0,
    "minor": 1,
    "patch": 0,
    "build_number": 0,
    "build_datetime": None,
    "last_deployment": None,
    "deployment_environment": None
}

def load_version() -> Dict[str, Any]:
    """Load version from file or create default"""
    try:
        if VERSION_FILE.exists():
            with open(VERSION_FILE, 'r') as f:
                return json.load(f)
        else:
            # Create default version file
            save_version(DEFAULT_VERSION)
            return DEFAULT_VERSION.copy()
    except Exception:
        return DEFAULT_VERSION.copy()

def save_version(version_data: Dict[str, Any]) -> None:
    """Save version to file"""
    try:
        with open(VERSION_FILE, 'w') as f:
            json.dump(version_data, f, indent=2)
    except Exception:
        pass  # Silently fail if we can't write

def get_version_string() -> str:
    """Get current version as semver string (e.g., '0.1.5')"""
    version = load_version()
    return f"{version['major']}.{version['minor']}.{version['patch']}"

def get_full_version_info() -> Dict[str, Any]:
    """Get complete version information"""
    version = load_version()
    return {
        "version": get_version_string(),
        "build_number": version.get('build_number', 0),
        "build_datetime": version.get('build_datetime'),
        "last_deployment": version.get('last_deployment'),
        "deployment_environment": version.get('deployment_environment'),
        "git_info": get_git_info()
    }

def increment_version(component: str = "patch", environment: str = None) -> str:
    """
    Increment version component and save
    
    Args:
        component: "major", "minor", or "patch" (default)
        environment: deployment environment ("prod", "dev", etc.)
    
    Returns:
        New version string
    """
    version = load_version()
    
    if component == "major":
        version["major"] += 1
        version["minor"] = 0
        version["patch"] = 0
    elif component == "minor":
        version["minor"] += 1
        version["patch"] = 0
    elif component == "patch":
        version["patch"] += 1
    
    # Always increment build number and set build datetime
    current_time = datetime.now()
    version["build_number"] = version.get("build_number", 0) + 1
    version["build_datetime"] = current_time.isoformat()
    version["last_deployment"] = current_time.isoformat()
    version["deployment_environment"] = environment
    
    save_version(version)
    return get_version_string()

def get_git_info() -> Dict[str, str]:
    """Get git information if available"""
    git_info = {}
    try:
        # Try to get git info
        import subprocess
        
        # Get current branch
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"], 
                capture_output=True, 
                text=True, 
                cwd=Path(__file__).parent
            )
            if result.returncode == 0:
                git_info["branch"] = result.stdout.strip()
        except:
            pass
            
        # Get commit hash
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"], 
                capture_output=True, 
                text=True,
                cwd=Path(__file__).parent
            )
            if result.returncode == 0:
                git_info["commit"] = result.stdout.strip()
        except:
            pass
            
    except ImportError:
        pass
    
    return git_info

def deployment_hook(environment: str = None) -> str:
    """
    Hook to call before deployment to increment version
    
    Args:
        environment: "prod", "dev", etc.
    
    Returns:
        New version string
    """
    # Auto-detect environment from stack name or other indicators
    if not environment:
        # Check AWS SAM/CloudFormation environment variables
        stack_name = os.environ.get('AWS_SAM_STACK_NAME', '')
        if 'prod' in stack_name.lower() or 'production' in stack_name.lower():
            environment = 'prod'
        elif 'dev' in stack_name.lower() or 'development' in stack_name.lower():
            environment = 'dev'
        else:
            environment = 'local'
    
    return increment_version("patch", environment)

if __name__ == "__main__":
    # Command line interface
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "increment":
            component = sys.argv[2] if len(sys.argv) > 2 else "patch"
            environment = sys.argv[3] if len(sys.argv) > 3 else None
            new_version = increment_version(component, environment)
            print(f"Version incremented to: {new_version}")
        elif command == "get":
            print(get_version_string())
        elif command == "info":
            info = get_full_version_info()
            print(json.dumps(info, indent=2))
        elif command == "deploy":
            environment = sys.argv[2] if len(sys.argv) > 2 else None
            new_version = deployment_hook(environment)
            print(f"Pre-deployment version: {new_version}")
    else:
        print(f"Current version: {get_version_string()}")
        info = get_full_version_info()
        if info.get('build_datetime'):
            print(f"Build: {info['build_datetime']} (#{info.get('build_number', 0)})")
        if info.get('last_deployment'):
            print(f"Last deployment: {info['last_deployment']} ({info.get('deployment_environment', 'unknown')})")
        if info.get('git_info'):
            git = info['git_info']
            if git.get('branch') or git.get('commit'):
                print(f"Git: {git.get('branch', 'unknown')}@{git.get('commit', 'unknown')}")