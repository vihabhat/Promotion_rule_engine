"""
Promotion Rule Engine Package

A flexible, high-performance rule engine for selecting appropriate 
in-game promotions based on configurable business rules.

Key Components:
- RuleLoader: Load and validate rules from YAML configuration
- RuleMatcher: Evaluate player data against rules and select promotions
- MetricsCollector: Track performance and usage statistics
- Data Models: Type-safe structures for rules, players, and promotions

Features:
- YAML-based rule configuration with hot-reloading
- Flexible condition operators (eq, gt, in, regex, etc.)
- Rule prioritization and conflict resolution
- Extensibility hooks for A/B testing, weighted selection, time windows
- Comprehensive metrics and monitoring
- Thread-safe operations for high-concurrency environments

Example Usage:
    from rule_engine import RuleLoader, RuleMatcher
    
    # Load rules from YAML
    loader = RuleLoader('rules.yaml')
    rules = loader.load_rules()
    
    # Initialize matcher
    matcher = RuleMatcher()
    matcher.set_rules(rules)
    
    # Evaluate player
    player_data = {
        'player_id': '12345',
        'level': 15,
        'spend_tier': 'gold',
        'country': 'US'
    }
    
    promotion = matcher.evaluate(player_data)
    if promotion:
        print(f"Awarded: {promotion['type']} - {promotion['description']}")
"""

from .loader import RuleLoader
from .matcher import RuleMatcher
from .models import (
    PlayerData, Condition, TimeWindow, Promotion, Rule, 
    EvaluationResult, ServiceMetrics, PromotionType, 
    SpendTier, ConditionOperator
)

# Package metadata
__version__ = '1.0.0'
__author__ = 'Casino Platform Team'
__description__ = 'Promotion Rule Engine Microservice'

# Public API
__all__ = [
    # Core components
    'RuleLoader',
    'RuleMatcher',
    
    # Data models
    'PlayerData',
    'Condition', 
    'TimeWindow',
    'Promotion',
    'Rule',
    'EvaluationResult',
    'ServiceMetrics',
    
    # Enums
    'PromotionType',
    'SpendTier', 
    'ConditionOperator',
    
    # Package info
    '__version__',
    '__author__',
    '__description__'
]

# Package-level configuration
DEFAULT_CONFIG = {
    'rules_file': 'rules.yaml',
    'enable_metrics': True,
    'enable_hot_reload': True,
    'default_timezone': 'UTC',
    'max_rules': 1000,
    'cache_size': 100
}

def get_version():
    """Get package version string."""
    return __version__

def get_default_config():
    """Get default configuration dictionary."""
    return DEFAULT_CONFIG.copy()