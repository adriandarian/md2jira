"""
Hook System - Pre/post processing hooks for extensibility.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Optional
import logging


class HookPoint(Enum):
    """Points where hooks can be attached."""
    
    # Parsing
    BEFORE_PARSE = auto()
    AFTER_PARSE = auto()
    
    # Matching
    BEFORE_MATCH = auto()
    AFTER_MATCH = auto()
    ON_MATCH_FAILURE = auto()
    
    # Sync operations
    BEFORE_SYNC = auto()
    AFTER_SYNC = auto()
    
    # Individual operations
    BEFORE_UPDATE_DESCRIPTION = auto()
    AFTER_UPDATE_DESCRIPTION = auto()
    
    BEFORE_CREATE_SUBTASK = auto()
    AFTER_CREATE_SUBTASK = auto()
    
    BEFORE_ADD_COMMENT = auto()
    AFTER_ADD_COMMENT = auto()
    
    BEFORE_TRANSITION = auto()
    AFTER_TRANSITION = auto()
    
    # Error handling
    ON_ERROR = auto()


@dataclass
class HookContext:
    """Context passed to hook handlers."""
    
    hook_point: HookPoint
    data: dict = field(default_factory=dict)
    result: Any = None
    error: Optional[Exception] = None
    cancelled: bool = False
    
    def cancel(self) -> None:
        """Cancel the current operation."""
        self.cancelled = True
    
    def set_result(self, result: Any) -> None:
        """Override the result."""
        self.result = result


class Hook:
    """
    A hook that can be attached to a hook point.
    
    Hooks are called in priority order (lower = earlier).
    """
    
    def __init__(
        self,
        name: str,
        hook_point: HookPoint,
        handler: Callable[[HookContext], None],
        priority: int = 100,
    ):
        self.name = name
        self.hook_point = hook_point
        self.handler = handler
        self.priority = priority
    
    def __call__(self, context: HookContext) -> None:
        """Execute the hook."""
        self.handler(context)
    
    def __lt__(self, other: "Hook") -> bool:
        """Compare by priority for sorting."""
        return self.priority < other.priority


class HookManager:
    """
    Manages hooks and their execution.
    
    Usage:
        manager = HookManager()
        
        @manager.hook(HookPoint.BEFORE_SYNC)
        def my_hook(ctx):
            print("Before sync!")
        
        # Or register manually
        manager.register(Hook("my_hook", HookPoint.BEFORE_SYNC, my_handler))
        
        # Trigger hooks
        manager.trigger(HookPoint.BEFORE_SYNC, {"epic_key": "PROJ-123"})
    """
    
    def __init__(self):
        self._hooks: dict[HookPoint, list[Hook]] = {hp: [] for hp in HookPoint}
        self.logger = logging.getLogger("HookManager")
    
    def register(self, hook: Hook) -> None:
        """Register a hook."""
        self._hooks[hook.hook_point].append(hook)
        self._hooks[hook.hook_point].sort()  # Sort by priority
        self.logger.debug(f"Registered hook: {hook.name} at {hook.hook_point.name}")
    
    def unregister(self, hook_name: str) -> bool:
        """Unregister a hook by name."""
        for hook_point in HookPoint:
            for hook in self._hooks[hook_point]:
                if hook.name == hook_name:
                    self._hooks[hook_point].remove(hook)
                    return True
        return False
    
    def trigger(
        self,
        hook_point: HookPoint,
        data: Optional[dict] = None,
    ) -> HookContext:
        """
        Trigger all hooks at a hook point.
        
        Args:
            hook_point: The hook point to trigger
            data: Data to pass to hooks
            
        Returns:
            HookContext with results
        """
        context = HookContext(
            hook_point=hook_point,
            data=data or {},
        )
        
        for hook in self._hooks[hook_point]:
            try:
                hook(context)
                
                if context.cancelled:
                    self.logger.info(f"Operation cancelled by hook: {hook.name}")
                    break
                    
            except Exception as e:
                self.logger.error(f"Hook {hook.name} failed: {e}")
                context.error = e
        
        return context
    
    def hook(
        self,
        hook_point: HookPoint,
        priority: int = 100,
        name: Optional[str] = None,
    ) -> Callable:
        """
        Decorator to register a hook.
        
        Usage:
            @manager.hook(HookPoint.BEFORE_SYNC)
            def my_hook(ctx):
                print("Before sync!")
        """
        def decorator(func: Callable[[HookContext], None]) -> Callable:
            hook_name = name or func.__name__
            self.register(Hook(hook_name, hook_point, func, priority))
            return func
        return decorator
    
    def get_hooks(self, hook_point: HookPoint) -> list[Hook]:
        """Get all hooks for a hook point."""
        return self._hooks[hook_point].copy()
    
    def clear(self, hook_point: Optional[HookPoint] = None) -> None:
        """Clear hooks (all or for specific point)."""
        if hook_point:
            self._hooks[hook_point] = []
        else:
            for hp in HookPoint:
                self._hooks[hp] = []

