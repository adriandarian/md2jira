"""Tests for plugin hook system."""

import pytest
from md2jira.plugins import (
    Hook,
    HookPoint,
    HookManager,
    HookContext,
)


class TestHookContext:
    """Tests for HookContext."""
    
    def test_cancel(self):
        ctx = HookContext(hook_point=HookPoint.BEFORE_SYNC)
        assert not ctx.cancelled
        
        ctx.cancel()
        
        assert ctx.cancelled
    
    def test_set_result(self):
        ctx = HookContext(hook_point=HookPoint.BEFORE_SYNC)
        assert ctx.result is None
        
        ctx.set_result("new_result")
        
        assert ctx.result == "new_result"


class TestHook:
    """Tests for Hook."""
    
    def test_call(self):
        called = []
        
        def handler(ctx):
            called.append(True)
        
        hook = Hook("test", HookPoint.BEFORE_SYNC, handler)
        ctx = HookContext(hook_point=HookPoint.BEFORE_SYNC)
        
        hook(ctx)
        
        assert len(called) == 1
    
    def test_priority_comparison(self):
        hook1 = Hook("high", HookPoint.BEFORE_SYNC, lambda x: x, priority=10)
        hook2 = Hook("low", HookPoint.BEFORE_SYNC, lambda x: x, priority=100)
        
        assert hook1 < hook2


class TestHookManager:
    """Tests for HookManager."""
    
    @pytest.fixture
    def manager(self):
        return HookManager()
    
    def test_register(self, manager):
        hook = Hook("test", HookPoint.BEFORE_SYNC, lambda x: x)
        
        manager.register(hook)
        
        hooks = manager.get_hooks(HookPoint.BEFORE_SYNC)
        assert len(hooks) == 1
        assert hooks[0].name == "test"
    
    def test_unregister(self, manager):
        hook = Hook("test", HookPoint.BEFORE_SYNC, lambda x: x)
        manager.register(hook)
        
        result = manager.unregister("test")
        
        assert result is True
        assert len(manager.get_hooks(HookPoint.BEFORE_SYNC)) == 0
    
    def test_trigger(self, manager):
        results = []
        
        def handler(ctx):
            results.append(ctx.data["value"])
        
        manager.register(Hook("test", HookPoint.BEFORE_SYNC, handler))
        
        manager.trigger(HookPoint.BEFORE_SYNC, {"value": 42})
        
        assert results == [42]
    
    def test_trigger_priority_order(self, manager):
        order = []
        
        manager.register(Hook("last", HookPoint.BEFORE_SYNC, 
                              lambda x: order.append("last"), priority=100))
        manager.register(Hook("first", HookPoint.BEFORE_SYNC,
                              lambda x: order.append("first"), priority=10))
        manager.register(Hook("middle", HookPoint.BEFORE_SYNC,
                              lambda x: order.append("middle"), priority=50))
        
        manager.trigger(HookPoint.BEFORE_SYNC)
        
        assert order == ["first", "middle", "last"]
    
    def test_trigger_cancel(self, manager):
        order = []
        
        def cancel_hook(ctx):
            order.append("cancel")
            ctx.cancel()
        
        manager.register(Hook("cancel", HookPoint.BEFORE_SYNC, cancel_hook, priority=10))
        manager.register(Hook("after", HookPoint.BEFORE_SYNC,
                              lambda x: order.append("after"), priority=20))
        
        ctx = manager.trigger(HookPoint.BEFORE_SYNC)
        
        assert ctx.cancelled
        assert order == ["cancel"]  # "after" was not called
    
    def test_decorator(self, manager):
        results = []
        
        @manager.hook(HookPoint.BEFORE_SYNC)
        def my_hook(ctx):
            results.append("decorated")
        
        manager.trigger(HookPoint.BEFORE_SYNC)
        
        assert results == ["decorated"]
    
    def test_decorator_with_options(self, manager):
        order = []
        
        @manager.hook(HookPoint.BEFORE_SYNC, priority=10, name="custom_name")
        def first_hook(ctx):
            order.append("first")
        
        @manager.hook(HookPoint.BEFORE_SYNC, priority=20)
        def second_hook(ctx):
            order.append("second")
        
        manager.trigger(HookPoint.BEFORE_SYNC)
        
        assert order == ["first", "second"]
        
        # Check custom name
        hooks = manager.get_hooks(HookPoint.BEFORE_SYNC)
        assert hooks[0].name == "custom_name"
    
    def test_clear_specific(self, manager):
        manager.register(Hook("sync", HookPoint.BEFORE_SYNC, lambda x: x))
        manager.register(Hook("match", HookPoint.BEFORE_MATCH, lambda x: x))
        
        manager.clear(HookPoint.BEFORE_SYNC)
        
        assert len(manager.get_hooks(HookPoint.BEFORE_SYNC)) == 0
        assert len(manager.get_hooks(HookPoint.BEFORE_MATCH)) == 1
    
    def test_clear_all(self, manager):
        manager.register(Hook("sync", HookPoint.BEFORE_SYNC, lambda x: x))
        manager.register(Hook("match", HookPoint.BEFORE_MATCH, lambda x: x))
        
        manager.clear()
        
        assert len(manager.get_hooks(HookPoint.BEFORE_SYNC)) == 0
        assert len(manager.get_hooks(HookPoint.BEFORE_MATCH)) == 0

