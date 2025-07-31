#!/usr/bin/env python3
"""
Comprehensive Function Architecture Validation Script

This script validates the complete function registration architecture:
1. @api_function decorators → __init__.py imports
2. @api_function decorators → CSV entries  
3. CSV entries → decorated functions in source
4. __init__.py imports → actual files exist
5. Decorator syntax validation
6. Duplicate function name detection
7. Investigation of commented decorators

Ensures CSV files remain the single source of truth for protocol management.
"""

import ast
import csv
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass


@dataclass
class FunctionInfo:
    """Information about a function found in source code"""
    name: str
    file_path: Path
    has_decorator: bool
    decorator_commented: bool
    decorator_protocols: List[str]
    line_number: int


@dataclass
class ValidationResult:
    """Results of validation checks"""
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]
    
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


class FunctionValidator:
    """Comprehensive function architecture validator"""
    
    def __init__(self, src_dir: str = "src", csv_files: List[str] = None):
        self.src_dir = Path(src_dir)
        self.functions_dir = self.src_dir / "functions"
        self.csv_files = csv_files or ["function_protocols.csv", "function_protocols_prod.csv"]
        self.result = ValidationResult([], [], [])
        
    def validate_all(self) -> ValidationResult:
        """Run all validation checks"""
        print("🔍 Starting Comprehensive Function Architecture Validation...")
        print("=" * 70)
        
        # Collect all data
        source_functions = self._scan_source_functions()
        csv_functions = self._load_csv_functions()
        init_imports = self._parse_init_imports()
        
        # Run validation checks
        self._check_decorated_functions_in_init(source_functions, init_imports)
        self._check_decorated_functions_in_csv(source_functions, csv_functions)
        self._check_csv_entries_have_functions(csv_functions, source_functions)
        self._check_init_imports_exist(init_imports)
        self._check_decorator_syntax(source_functions)
        self._check_duplicate_function_names(source_functions)
        self._investigate_missing_functions(csv_functions, source_functions)
        
        # Print results
        self._print_results()
        
        return self.result
    
    def _scan_source_functions(self) -> Dict[str, FunctionInfo]:
        """Scan all Python files for functions with @api_function decorators"""
        functions = {}
        
        if not self.functions_dir.exists():
            self.result.errors.append(f"Functions directory not found: {self.functions_dir}")
            return functions
            
        for py_file in self.functions_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            try:
                functions.update(self._scan_file_for_functions(py_file))
            except Exception as e:
                self.result.warnings.append(f"Error scanning {py_file}: {e}")
                
        return functions
    
    def _scan_file_for_functions(self, file_path: Path) -> Dict[str, FunctionInfo]:
        """Scan a single file for functions with decorators"""
        functions = {}
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.splitlines()
            
            # Look for @api_function decorators and associated functions
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                
                # Check for commented @api_function
                if line_stripped.startswith("# @api_function"):
                    func_name, protocols = self._extract_function_from_commented_decorator(lines, i)
                    if func_name:
                        functions[func_name] = FunctionInfo(
                            name=func_name,
                            file_path=file_path,
                            has_decorator=False,
                            decorator_commented=True,
                            decorator_protocols=protocols,
                            line_number=i + 1
                        )
                
                # Check for active @api_function
                elif line_stripped.startswith("@api_function"):
                    func_name, protocols = self._extract_function_from_active_decorator(lines, i)
                    if func_name:
                        functions[func_name] = FunctionInfo(
                            name=func_name,
                            file_path=file_path,
                            has_decorator=True,
                            decorator_commented=False,
                            decorator_protocols=protocols,
                            line_number=i + 1
                        )
                        
        except Exception as e:
            self.result.warnings.append(f"Error reading {file_path}: {e}")
            
        return functions
    
    def _extract_function_from_commented_decorator(self, lines: List[str], start_idx: int) -> Tuple[Optional[str], List[str]]:
        """Extract function name and protocols from commented decorator block"""
        # Look for the function definition after commented decorator block
        for i in range(start_idx, min(start_idx + 10, len(lines))):
            line = lines[i].strip()
            if line.startswith("def ") or line.startswith("async def "):
                match = re.search(r'def\s+(\w+)', line)
                if match:
                    func_name = match.group(1)
                    # Try to extract protocols from commented decorator
                    protocols = self._extract_protocols_from_lines(lines[start_idx:i])
                    return func_name, protocols
        return None, []
    
    def _extract_function_from_active_decorator(self, lines: List[str], start_idx: int) -> Tuple[Optional[str], List[str]]:
        """Extract function name and protocols from active decorator"""
        # Look for the function definition after decorator
        for i in range(start_idx, min(start_idx + 10, len(lines))):
            line = lines[i].strip()
            if line.startswith("def ") or line.startswith("async def "):
                match = re.search(r'def\s+(\w+)', line)
                if match:
                    func_name = match.group(1)
                    # Extract protocols from decorator
                    protocols = self._extract_protocols_from_lines(lines[start_idx:i+1])
                    return func_name, protocols
        return None, []
    
    def _extract_protocols_from_lines(self, lines: List[str]) -> List[str]:
        """Extract protocol list from decorator lines"""
        protocols = []
        text = ' '.join(line.strip() for line in lines)
        
        # Look for protocols=["mcp", "rest"] pattern
        protocol_match = re.search(r'protocols\s*=\s*\[(.*?)\]', text)
        if protocol_match:
            protocol_str = protocol_match.group(1)
            # Extract quoted strings
            for match in re.finditer(r'["\'](\w+)["\']', protocol_str):
                protocols.append(match.group(1))
                
        return protocols
    
    def _load_csv_functions(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Load functions from all CSV files"""
        csv_data = {}
        
        for csv_file in self.csv_files:
            if not os.path.exists(csv_file):
                self.result.warnings.append(f"CSV file not found: {csv_file}")
                continue
                
            csv_data[csv_file] = {}
            try:
                with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        func_name = row.get('Function Name', '').strip()
                        if func_name:
                            csv_data[csv_file][func_name] = {
                                'mcp': row.get('MCP', '').strip().upper() == 'YES',
                                'rest': row.get('REST', '').strip().upper() == 'YES',
                                'description': row.get('Description', '').strip()
                            }
            except Exception as e:
                self.result.errors.append(f"Error reading CSV {csv_file}: {e}")
                
        return csv_data
    
    def _parse_init_imports(self) -> Set[str]:
        """Parse __init__.py to find imported modules and submodules"""
        init_file = self.functions_dir / "__init__.py"
        imports = set()
        
        if not init_file.exists():
            self.result.errors.append(f"__init__.py not found: {init_file}")
            return imports
            
        try:
            content = init_file.read_text(encoding='utf-8')
            lines = content.splitlines()
            
            for line in lines:
                line = line.strip()
                if line.startswith('#'):
                    continue
                    
                # Look for: from . import module_name
                match = re.search(r'from\s+\.\s+import\s+(\w+)', line)
                if match:
                    imports.add(match.group(1))
                
                # Look for: from .subdir import module_name  
                # This handles cases like: from .webui_functions import conversation_functions
                match = re.search(r'from\s+\.(\w+)\s+import\s+(\w+)', line)
                if match:
                    subdir = match.group(1)
                    module = match.group(2)
                    imports.add(module)  # Add the actual module name being imported
                    imports.add(subdir)   # Also add the subdirectory for completeness
                    
        except Exception as e:
            self.result.errors.append(f"Error reading __init__.py: {e}")
            
        return imports
    
    def _check_decorated_functions_in_init(self, source_functions: Dict[str, FunctionInfo], init_imports: Set[str]):
        """Check that all files with @api_function decorators are imported in __init__.py"""
        missing_imports = set()
        
        for func_info in source_functions.values():
            if func_info.has_decorator:
                module_name = func_info.file_path.stem
                
                # Check if module is directly imported
                if module_name in init_imports:
                    continue
                    
                # Check if this is a subdirectory module that's imported via parent
                # e.g., conversation_functions in webui_functions/conversation_functions.py
                # should be satisfied by "from .webui_functions import conversation_functions"
                parent_dir = func_info.file_path.parent.name
                if parent_dir != "functions" and parent_dir in init_imports:
                    # This is a subdirectory module, check if it's in init_imports
                    continue
                    
                # Module is not properly imported
                missing_imports.add(module_name)
                    
        if missing_imports:
            self.result.errors.append(
                f"Modules with @api_function decorators missing from __init__.py: {sorted(missing_imports)}"
            )
            for module in sorted(missing_imports):
                # Check if this is a subdirectory module
                func_info = next((f for f in source_functions.values() if f.file_path.stem == module), None)
                if func_info and func_info.file_path.parent.name != "functions":
                    parent_dir = func_info.file_path.parent.name
                    self.result.recommendations.append(
                        f"Add to __init__.py: from .{parent_dir} import {module}"
                    )
                else:
                    self.result.recommendations.append(
                        f"Add to __init__.py: from . import {module}"
                    )
    
    def _check_decorated_functions_in_csv(self, source_functions: Dict[str, FunctionInfo], csv_functions: Dict[str, Dict[str, Dict[str, str]]]):
        """Check that all @api_function decorated functions are in CSV files"""
        for csv_file, csv_data in csv_functions.items():
            missing_from_csv = []
            
            for func_name, func_info in source_functions.items():
                if func_info.has_decorator and func_name not in csv_data:
                    missing_from_csv.append(func_name)
                    
            if missing_from_csv:
                self.result.errors.append(
                    f"Functions with @api_function missing from {csv_file}: {sorted(missing_from_csv)}"
                )
                for func_name in sorted(missing_from_csv):
                    func_info = source_functions[func_name]
                    protocols = func_info.decorator_protocols
                    mcp = "YES" if "mcp" in protocols else ""
                    rest = "YES" if "rest" in protocols else ""
                    self.result.recommendations.append(
                        f"Add to {csv_file}: {func_name},{mcp},{rest},<description>"
                    )
    
    def _check_csv_entries_have_functions(self, csv_functions: Dict[str, Dict[str, Dict[str, str]]], source_functions: Dict[str, FunctionInfo]):
        """Check that all CSV entries have matching functions in source code"""
        for csv_file, csv_data in csv_functions.items():
            missing_functions = []
            
            for func_name in csv_data.keys():
                if func_name not in source_functions:
                    missing_functions.append(func_name)
                    
            if missing_functions:
                self.result.warnings.append(
                    f"CSV entries in {csv_file} with no matching source functions: {sorted(missing_functions)}"
                )
                self.result.recommendations.append(
                    f"Investigate missing functions in {csv_file} - may need decorator uncommented or CSV cleanup"
                )
    
    def _check_init_imports_exist(self, init_imports: Set[str]):
        """Check that all imports in __init__.py correspond to actual files or directories"""
        missing_files = []
        
        for module_name in init_imports:
            # Check if it's a direct .py file
            module_file = self.functions_dir / f"{module_name}.py"
            # Check if it's a subdirectory with __init__.py
            module_dir = self.functions_dir / module_name / "__init__.py"
            
            if not module_file.exists() and not module_dir.exists():
                # Check if this module is imported from a subdirectory
                # Look for it in any subdirectory
                found_in_subdir = False
                for subdir in self.functions_dir.iterdir():
                    if subdir.is_dir() and subdir.name != "__pycache__":
                        submodule_file = subdir / f"{module_name}.py"
                        if submodule_file.exists():
                            found_in_subdir = True
                            break
                
                if not found_in_subdir:
                    missing_files.append(module_name)
                
        if missing_files:
            self.result.errors.append(
                f"__init__.py imports modules that don't exist: {sorted(missing_files)}"
            )
            for module in sorted(missing_files):
                self.result.recommendations.append(
                    f"Remove from __init__.py or create missing file: {module}.py"
                )
    
    def _check_decorator_syntax(self, source_functions: Dict[str, FunctionInfo]):
        """Check for decorator syntax issues"""
        syntax_issues = []
        
        for func_name, func_info in source_functions.items():
            if func_info.has_decorator:
                # Check for required description
                try:
                    content = func_info.file_path.read_text(encoding='utf-8')
                    lines = content.splitlines()
                    
                    # Find decorator block
                    decorator_lines = []
                    found_decorator = False
                    
                    for i, line in enumerate(lines):
                        if found_decorator:
                            if line.strip().startswith("def ") or line.strip().startswith("async def "):
                                break
                            decorator_lines.append(line)
                        elif line.strip().startswith("@api_function"):
                            found_decorator = True
                            decorator_lines.append(line)
                    
                    decorator_text = ' '.join(decorator_lines)
                    
                    # Check for description parameter
                    if 'description=' not in decorator_text:
                        syntax_issues.append(f"{func_name} ({func_info.file_path}:{func_info.line_number})")
                        
                except Exception as e:
                    self.result.warnings.append(f"Error checking decorator syntax for {func_name}: {e}")
                    
        if syntax_issues:
            self.result.errors.append(
                f"Functions missing required 'description' parameter in @api_function: {syntax_issues}"
            )
    
    def _check_duplicate_function_names(self, source_functions: Dict[str, FunctionInfo]):
        """Check for duplicate function names across files"""
        name_to_files = {}
        
        for func_name, func_info in source_functions.items():
            if func_name not in name_to_files:
                name_to_files[func_name] = []
            name_to_files[func_name].append(func_info.file_path)
            
        duplicates = {name: files for name, files in name_to_files.items() if len(files) > 1}
        
        if duplicates:
            for func_name, files in duplicates.items():
                self.result.errors.append(
                    f"Duplicate function name '{func_name}' found in: {[str(f) for f in files]}"
                )
                self.result.recommendations.append(
                    f"Rename duplicate functions to be unique: {func_name}"
                )
    
    def _investigate_missing_functions(self, csv_functions: Dict[str, Dict[str, Dict[str, str]]], source_functions: Dict[str, FunctionInfo]):
        """Investigate CSV entries that have no matching decorated functions"""
        for csv_file, csv_data in csv_functions.items():
            for func_name in csv_data.keys():
                if func_name not in source_functions:
                    # Check if function exists with commented decorator
                    commented_func = None
                    for name, func_info in source_functions.items():
                        if name == func_name and func_info.decorator_commented:
                            commented_func = func_info
                            break
                    
                    if commented_func:
                        self.result.recommendations.append(
                            f"FOUND COMMENTED: {func_name} in {commented_func.file_path}:{commented_func.line_number} "
                            f"- Uncomment decorator and set protocols=[] in {csv_file} to disable"
                        )
                    else:
                        # Check if function exists without any decorator
                        if self._function_exists_without_decorator(func_name):
                            self.result.recommendations.append(
                                f"FOUND UNDECORATED: {func_name} exists but missing @api_function decorator"
                            )
                        else:
                            self.result.recommendations.append(
                                f"MISSING COMPLETELY: {func_name} not found in codebase - remove from {csv_file}"
                            )
    
    def _function_exists_without_decorator(self, func_name: str) -> bool:
        """Check if a function exists in the codebase without @api_function decorator"""
        for py_file in self.functions_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            try:
                content = py_file.read_text(encoding='utf-8')
                if re.search(rf'def\s+{re.escape(func_name)}\s*\(', content):
                    return True
            except:
                continue
        return False
    
    def _print_results(self):
        """Print validation results in a clear format"""
        print("\n🎯 VALIDATION RESULTS")
        print("=" * 70)
        
        if self.result.is_valid:
            print("✅ ALL CHECKS PASSED! Function architecture is valid.")
        else:
            print(f"❌ VALIDATION FAILED ({len(self.result.errors)} errors)")
        
        if self.result.errors:
            print(f"\n❌ ERRORS ({len(self.result.errors)}):")
            for i, error in enumerate(self.result.errors, 1):
                print(f"  {i}. {error}")
        
        if self.result.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.result.warnings)}):")
            for i, warning in enumerate(self.result.warnings, 1):
                print(f"  {i}. {warning}")
        
        if self.result.recommendations:
            print(f"\n💡 RECOMMENDATIONS ({len(self.result.recommendations)}):")
            for i, rec in enumerate(self.result.recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "=" * 70)


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        src_dir = sys.argv[1]
    else:
        src_dir = "src"
    
    validator = FunctionValidator(src_dir)
    result = validator.validate_all()
    
    # Exit with error code if validation failed
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()