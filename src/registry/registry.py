"""
Core Function Registry

Maintains a central registry of all @api_function decorated functions
and provides functionality to auto-generate MCP tools and REST endpoints.
"""

import inspect
from typing import Dict, List, Callable, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class Protocol(Enum):
    """Supported protocols for function exposure"""
    MCP = "mcp"
    REST = "rest"
    LOCAL = "local"  # Functions registered but not exposed via any protocol


@dataclass
class FunctionMeta:
    """Metadata for a registered API function"""
    name: str
    func: Callable
    protocols: List[Protocol]
    description: str
    rest_path: Optional[str] = None
    rest_method: str = "GET"
    tags: List[str] = field(default_factory=list)
    
    @property
    def docstring(self) -> str:
        """Get the function's docstring"""
        return inspect.getdoc(self.func) or self.description
    
    @property
    def signature(self) -> inspect.Signature:
        """Get the function's signature for type introspection"""
        return inspect.signature(self.func)
    
    @property
    def type_hints(self) -> Dict[str, Any]:
        """Get the function's type hints"""
        return getattr(self.func, '__annotations__', {})


class FunctionRegistry:
    """
    Central registry for all API functions.
    
    Maintains a registry of functions decorated with @api_function and provides
    methods to auto-generate MCP tools and FastAPI routes from the registry.
    """
    
    def __init__(self):
        self._functions: Dict[str, FunctionMeta] = {}
    
    def register(
        self, 
        func: Callable,
        protocols: List[Union[str, Protocol]],
        description: Optional[str] = None,
        rest_path: Optional[str] = None,
        rest_method: str = "GET",
        tags: Optional[List[str]] = None,
        name: Optional[str] = None
    ) -> FunctionMeta:
        """
        Register a function in the registry.
        
        Args:
            func: The function to register
            protocols: List of protocols to expose this function on
            description: Custom description (defaults to docstring)
            rest_path: REST API path pattern (for REST protocol)
            rest_method: HTTP method for REST endpoint
            tags: Tags for grouping functions
            name: Custom name (defaults to function name)
            
        Returns:
            FunctionMeta: The registered function metadata
        """
        # Normalize protocols
        normalized_protocols = []
        for p in protocols:
            if isinstance(p, str):
                normalized_protocols.append(Protocol(p.lower()))
            else:
                normalized_protocols.append(p)
        
        # Generate metadata
        func_name = name or func.__name__
        func_description = description or inspect.getdoc(func) or f"Execute {func_name}"
        
        meta = FunctionMeta(
            name=func_name,
            func=func,
            protocols=normalized_protocols,
            description=func_description,
            rest_path=rest_path,
            rest_method=rest_method.upper(),
            tags=tags or []
        )
        
        self._functions[func_name] = meta
        return meta
    
    def get_function(self, name: str) -> Optional[FunctionMeta]:
        """Get function metadata by name"""
        return self._functions.get(name)
    
    def get_functions_by_protocol(self, protocol: Union[str, Protocol]) -> List[FunctionMeta]:
        """Get all functions that support a specific protocol"""
        if isinstance(protocol, str):
            protocol = Protocol(protocol.lower())
        
        return [
            meta for meta in self._functions.values()
            if protocol in meta.protocols
        ]
    
    def get_all_functions(self) -> Dict[str, FunctionMeta]:
        """Get all registered functions"""
        return self._functions.copy()
    
    def get_mcp_functions(self) -> List[FunctionMeta]:
        """Get all functions that support MCP protocol"""
        return self.get_functions_by_protocol(Protocol.MCP)
    
    def get_rest_functions(self) -> List[FunctionMeta]:
        """Get all functions that support REST protocol"""
        return self.get_functions_by_protocol(Protocol.REST)
    
    def __len__(self) -> int:
        """Get number of registered functions"""
        return len(self._functions)
    
    def __contains__(self, name: str) -> bool:
        """Check if function is registered"""
        return name in self._functions


# Global registry instance
_global_registry = FunctionRegistry()


def get_registry() -> FunctionRegistry:
    """Get the global function registry instance"""
    return _global_registry