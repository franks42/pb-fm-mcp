"""
Auto-Generation Engine

Generates MCP tools and FastAPI routes from the function registry.
This is where the magic happens - turning single function definitions
into fully functional protocol endpoints.
"""

import inspect
from typing import Dict, Any, List, Optional, get_origin, get_args, Union
import json

from .registry import FunctionRegistry, FunctionMeta, Protocol


class MCPToolGenerator:
    """Generates MCP tool definitions from registered functions"""
    
    @staticmethod
    def generate_mcp_tool(meta: FunctionMeta) -> Dict[str, Any]:
        """
        Generate an MCP tool definition from function metadata.
        
        Args:
            meta: Function metadata from registry
            
        Returns:
            MCP tool definition dict
        """
        # Get function signature for parameter schema
        sig = meta.signature
        type_hints = meta.type_hints
        
        # Build input schema from function parameters
        input_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in sig.parameters.items():
            # Skip self/cls parameters
            if param_name in ('self', 'cls'):
                continue
                
            param_type = type_hints.get(param_name, str)
            param_schema = MCPToolGenerator._type_to_json_schema(param_type)
            
            # Add parameter description from docstring if available
            param_doc = MCPToolGenerator._extract_param_doc(meta.docstring, param_name)
            if param_doc:
                param_schema["description"] = param_doc
            
            input_schema["properties"][param_name] = param_schema
            
            # Required if no default value
            if param.default == param.empty:
                input_schema["required"].append(param_name)
        
        # Build MCP tool definition
        tool_def = {
            "name": meta.name,
            "description": meta.docstring,
            "inputSchema": input_schema
        }
        
        return tool_def
    
    @staticmethod
    def _type_to_json_schema(python_type: Any) -> Dict[str, Any]:
        """Convert Python type hints to JSON Schema"""
        if python_type == str:
            return {"type": "string"}
        elif python_type == int:
            return {"type": "integer"}
        elif python_type == float:
            return {"type": "number"}
        elif python_type == bool:
            return {"type": "boolean"}
        elif python_type == dict:
            return {"type": "object"}
        elif python_type == list:
            return {"type": "array"}
        elif get_origin(python_type) == Union:
            # Handle Optional[T] and Union types
            args = get_args(python_type)
            if len(args) == 2 and type(None) in args:
                # Optional type
                non_none_type = next(arg for arg in args if arg != type(None))
                schema = MCPToolGenerator._type_to_json_schema(non_none_type)
                # Don't mark as required in parent
                return schema
            else:
                # Complex union - default to string
                return {"type": "string"}
        else:
            # Default to string for unknown types
            return {"type": "string"}
    
    @staticmethod
    def _extract_param_doc(docstring: str, param_name: str) -> Optional[str]:
        """Extract parameter documentation from docstring"""
        if not docstring:
            return None
            
        lines = docstring.split('\n')
        in_args_section = False
        
        for line in lines:
            line = line.strip()
            if line.lower().startswith('args:'):
                in_args_section = True
                continue
            elif line.lower().startswith(('returns:', 'return:', 'raises:', 'examples:')):
                in_args_section = False
                continue
            
            if in_args_section and line.startswith(param_name + ':'):
                # Extract description after parameter name
                return line[len(param_name) + 1:].strip()
        
        return None


class FastAPIGenerator:
    """Generates FastAPI routes from registered functions"""
    
    @staticmethod
    def generate_openapi_schema(meta: FunctionMeta) -> Dict[str, Any]:
        """
        Generate OpenAPI schema for a REST function.
        
        Args:
            meta: Function metadata from registry
            
        Returns:
            OpenAPI schema dict for the endpoint
        """
        sig = meta.signature
        type_hints = meta.type_hints
        
        # Extract summary and description from docstring
        summary = meta.description
        description = meta.docstring
        
        # Build parameter schemas
        parameters = []
        request_body = None
        
        for param_name, param in sig.parameters.items():
            if param_name in ('self', 'cls'):
                continue
                
            param_type = type_hints.get(param_name, str)
            param_schema = FastAPIGenerator._type_to_openapi_schema(param_type)
            
            # Check if parameter is in path
            if meta.rest_path and f"{{{param_name}}}" in meta.rest_path:
                # Path parameter
                parameters.append({
                    "name": param_name,
                    "in": "path",
                    "required": True,
                    "schema": param_schema,
                    "description": MCPToolGenerator._extract_param_doc(meta.docstring, param_name) or f"{param_name} parameter"
                })
            elif meta.rest_method in ["POST", "PUT", "PATCH"]:
                # Body parameter for write operations
                if not request_body:
                    request_body = {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            }
                        }
                    }
                
                request_body["content"]["application/json"]["schema"]["properties"][param_name] = param_schema
                if param.default == param.empty:
                    request_body["content"]["application/json"]["schema"]["required"].append(param_name)
            else:
                # Query parameter
                parameters.append({
                    "name": param_name,
                    "in": "query",
                    "required": param.default == param.empty,
                    "schema": param_schema,
                    "description": MCPToolGenerator._extract_param_doc(meta.docstring, param_name) or f"{param_name} parameter"
                })
        
        # Build return type schema
        return_type = type_hints.get('return', dict)
        return_schema = FastAPIGenerator._type_to_openapi_schema(return_type)
        
        # Build complete OpenAPI operation
        operation = {
            "summary": summary,
            "description": description,
            "parameters": parameters,
            "responses": {
                "200": {
                    "description": FastAPIGenerator._extract_return_doc(meta.docstring) or "Successful response",
                    "content": {
                        "application/json": {
                            "schema": return_schema
                        }
                    }
                }
            }
        }
        
        if request_body:
            operation["requestBody"] = request_body
            
        if meta.tags:
            operation["tags"] = meta.tags
        
        return operation
    
    @staticmethod
    def _type_to_openapi_schema(python_type: Any) -> Dict[str, Any]:
        """Convert Python type hints to OpenAPI schema"""
        # Reuse the JSON schema conversion
        return MCPToolGenerator._type_to_json_schema(python_type)
    
    @staticmethod
    def _extract_return_doc(docstring: str) -> Optional[str]:
        """Extract return documentation from docstring"""
        if not docstring:
            return None
            
        lines = docstring.split('\n')
        in_returns_section = False
        
        for line in lines:
            line = line.strip()
            if line.lower().startswith(('returns:', 'return:')):
                in_returns_section = True
                # Check if description is on same line
                colon_pos = line.find(':')
                if colon_pos >= 0 and len(line) > colon_pos + 1:
                    return line[colon_pos + 1:].strip()
                continue
            elif line.lower().startswith(('args:', 'raises:', 'examples:')):
                in_returns_section = False
                continue
            
            if in_returns_section and line:
                return line
        
        return None


class RegistryGenerator:
    """Main generator that orchestrates MCP and REST generation"""
    
    def __init__(self, registry: FunctionRegistry):
        self.registry = registry
        self.mcp_generator = MCPToolGenerator()
        self.rest_generator = FastAPIGenerator()
    
    def generate_mcp_tools(self) -> List[Dict[str, Any]]:
        """Generate all MCP tool definitions"""
        tools = []
        for meta in self.registry.get_mcp_functions():
            tool = self.mcp_generator.generate_mcp_tool(meta)
            tools.append(tool)
        return tools
    
    def generate_openapi_paths(self) -> Dict[str, Any]:
        """Generate OpenAPI paths for all REST functions"""
        paths = {}
        for meta in self.registry.get_rest_functions():
            if not meta.rest_path:
                continue
                
            if meta.rest_path not in paths:
                paths[meta.rest_path] = {}
                
            operation = self.rest_generator.generate_openapi_schema(meta)
            paths[meta.rest_path][meta.rest_method.lower()] = operation
            
        return paths
    
    def get_function_by_name(self, name: str) -> Optional[FunctionMeta]:
        """Get function metadata by name"""
        return self.registry.get_function(name)