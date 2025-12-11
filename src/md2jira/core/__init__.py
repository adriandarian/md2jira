"""
Core module - Pure domain logic with no external dependencies.

This module contains:
- domain/: Entities, value objects, and domain enums
- ports/: Abstract interfaces that adapters must implement
- services/: Domain services for business logic
"""

from .domain import *
from .ports import *

