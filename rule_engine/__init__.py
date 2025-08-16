
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