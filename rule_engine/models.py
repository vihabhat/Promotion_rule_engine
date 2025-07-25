"""
Data models and structures for the promotion rule engine.
Provides type safety and validation for rule engine components.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum


class PromotionType(Enum):
    """Enumeration of supported promotion types."""
    BONUS_CREDITS = "bonus_credits"
    FREE_SPINS = "free_spins"
    CASHBACK = "cashback"
    MULTIPLIER = "multiplier"
    WELCOME_BONUS = "welcome_bonus"
    LOYALTY_REWARD = "loyalty_reward"
    SEASONAL_OFFER = "seasonal_offer"


class SpendTier(Enum):
    """Enumeration of player spend tiers."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"
    VIP = "vip"


class ConditionOperator(Enum):
    """Enumeration of supported condition operators."""
    EQUAL = "eq"
    NOT_EQUAL = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    REGEX = "regex"


@dataclass
class PlayerData:
    """
    Player data structure for rule evaluation.
    Contains all attributes that can be used in promotion rule conditions.
    """
    player_id: str
    level: Optional[int] = None
    spend_tier: Optional[str] = None
    country: Optional[str] = None
    days_since_last_purchase: Optional[int] = None
    total_spent: Optional[float] = None
    current_balance: Optional[float] = None
    registration_date: Optional[datetime] = None
    
    # Additional attributes for extensibility
    last_login_date: Optional[datetime] = None
    preferred_game_category: Optional[str] = None
    mobile_player: Optional[bool] = None
    vip_status: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert player data to dictionary format."""
        data = {}
        for key, value in self.__dict__.items():
            if value is not None:
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
                else:
                    data[key] = value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerData':
        """Create PlayerData instance from dictionary."""
        # Parse datetime fields
        datetime_fields = ['registration_date', 'last_login_date']
        for field in datetime_fields:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                except ValueError:
                    data[field] = None
        
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class Condition:
    """
    Represents a single rule condition.
    Supports various operators for flexible condition matching.
    """
    field: str
    operator: Union[str, ConditionOperator]
    value: Any
    
    def __post_init__(self):
        """Validate condition after initialization."""
        if isinstance(self.operator, str):
            # Convert string to enum if possible
            try:
                self.operator = ConditionOperator(self.operator)
            except ValueError:
                pass  # Keep as string for extensibility
    
    def evaluate(self, player_data: PlayerData) -> bool:
        player_value = getattr(player_data, self.field, None)
        if player_value is None:
            return False
        
        op = self.operator.value if isinstance(self.operator, ConditionOperator) else self.operator
        
        try:
            if op == 'eq':
                return player_value == self.value
            elif op == 'ne':
                return player_value != self.value
            elif op == 'gt':
                return float(player_value) > float(self.value)
            elif op == 'gte':
                return float(player_value) >= float(self.value)
            elif op == 'lt':
                return float(player_value) < float(self.value)
            elif op == 'lte':
                return float(player_value) <= float(self.value)
            elif op == 'in':
                return player_value in self.value
            elif op == 'not_in':
                return player_value not in self.value
            elif op == 'contains':
                return str(self.value).lower() in str(player_value).lower()
            elif op == 'regex':
                import re
                return bool(re.match(self.value, str(player_value)))
            else:
                return False
        except (ValueError, TypeError):
            return False


@dataclass
class TimeWindow:
    """
    Represents a time window for rule activation.
    Supports day-of-week and hour-of-day constraints.
    """
    start_time: Optional[str] = None  # HH:MM format
    end_time: Optional[str] = None    # HH:MM format
    days_of_week: Optional[List[str]] = None  # ['monday', 'tuesday', ...]
    timezone: str = 'UTC'
    
    def is_active(self, current_time: Optional[datetime] = None) -> bool:
        if current_time is None:
            current_time = datetime.utcnow()
        
        # Check day of week
        if self.days_of_week:
            current_day = current_time.strftime('%A').lower()
            if current_day not in [day.lower() for day in self.days_of_week]:
                return False
        
        # Check time range
        if self.start_time and self.end_time:
            current_time_str = current_time.strftime('%H:%M')
            
            if self.start_time <= self.end_time:
                # Same day range
                return self.start_time <= current_time_str <= self.end_time
            else:
                # Overnight range
                return current_time_str >= self.start_time or current_time_str <= self.end_time
        
        return True


@dataclass
class Promotion:
    """
    Represents a promotion that can be awarded to players.
    Contains all information needed to present and apply the promotion.
    """
    id: str
    type: Union[str, PromotionType]
    amount: Optional[float] = None
    description: Optional[str] = None
    multiplier: Optional[float] = None
    duration_hours: Optional[int] = None
    max_amount: Optional[float] = None
    min_amount: Optional[float] = None
    currency: str = 'USD'
    terms_and_conditions: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate promotion after initialization."""
        if isinstance(self.type, str):
            try:
                self.type = PromotionType(self.type)
            except ValueError:
                pass  # Keep as string for extensibility
        
        if not self.description:
            self.description = f"{self.type} promotion"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert promotion to dictionary format for API response."""
        data = {}
        for key, value in self.__dict__.items():
            if value is not None:
                if isinstance(value, datetime):
                    data[key] = value.isoformat() + 'Z'
                elif isinstance(value, Enum):
                    data[key] = value.value
                else:
                    data[key] = value
        return data
    
    def is_valid(self) -> bool:
        """Check if promotion is valid and not expired."""
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True


@dataclass
class Rule:
    """
    Represents a complete promotion rule.
    Contains conditions, promotion details, and metadata for rule evaluation.
    """
    id: str
    priority: int
    conditions: List[Condition]
    promotion: Promotion
    enabled: bool = True
    description: Optional[str] = None
    
    # Extensibility hooks
    weight: Optional[float] = None
    ab_bucket: Optional[str] = None
    time_window: Optional[TimeWindow] = None
    
    # Metadata
    created_at: Optional[datetime] = field(default_factory=datetime.utcnow)
    last_modified: Optional[datetime] = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    def evaluate(self, player_data: PlayerData) -> bool:
        if not self.enabled:
            return False
        
        # Check time window
        if self.time_window and not self.time_window.is_active():
            return False
        
        # Evaluate all conditions (AND logic)
        return all(condition.evaluate(player_data) for condition in self.conditions)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary format."""
        data = {
            'id': self.id,
            'priority': self.priority,
            'enabled': self.enabled,
            'description': self.description or f"Rule {self.id}",
            'conditions': {},
            'promotion': self.promotion.to_dict()
        }
        
        # Convert conditions to dictionary format
        for condition in self.conditions:
            op = condition.operator.value if isinstance(condition.operator, ConditionOperator) else condition.operator
            if op == 'eq':
                data['conditions'][condition.field] = condition.value
            else:
                data['conditions'][condition.field] = {op: condition.value}
        
        # Add extensibility hooks if present
        if self.weight is not None:
            data['weight'] = self.weight
        if self.ab_bucket:
            data['ab_bucket'] = self.ab_bucket
        if self.time_window:
            data['time_window'] = {
                'start_time': self.time_window.start_time,
                'end_time': self.time_window.end_time,
                'days_of_week': self.time_window.days_of_week,
                'timezone': self.time_window.timezone
            }
        
        return data


@dataclass
class EvaluationResult:
    """
    Result of a rule evaluation request.
    Contains the selected promotion and metadata about the evaluation process.
    """
    player_id: str
    promotion: Optional[Promotion]
    matched_rule_id: Optional[str] = None
    evaluation_time_ms: Optional[float] = None
    rules_evaluated: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert evaluation result to dictionary format."""
        return {
            'player_id': self.player_id,
            'promotion': self.promotion.to_dict() if self.promotion else None,
            'matched_rule_id': self.matched_rule_id,
            'evaluation_time_ms': self.evaluation_time_ms,
            'rules_evaluated': self.rules_evaluated,
            'timestamp': self.timestamp.isoformat() + 'Z'
        }


@dataclass
class ServiceMetrics:
    """
    Service-level metrics for monitoring and observability.
    Tracks performance and usage statistics.
    """
    total_evaluations: int = 0
    hits: int = 0
    misses: int = 0
    total_latency_ms: float = 0.0
    start_time: datetime = field(default_factory=datetime.utcnow)
    
    # Rule-specific metrics
    rule_hit_counts: Dict[str, int] = field(default_factory=dict)
    promotion_type_counts: Dict[str, int] = field(default_factory=dict)
    
    # Error tracking
    validation_errors: int = 0
    evaluation_errors: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage."""
        if self.total_evaluations == 0:
            return 0.0
        return self.hits / self.total_evaluations
    
    @property
    def average_latency_ms(self) -> float:
        """Calculate average latency in milliseconds."""
        if self.total_evaluations == 0:
            return 0.0
        return self.total_latency_ms / self.total_evaluations
    
    @property
    def uptime_seconds(self) -> float:
        """Calculate service uptime in seconds."""
        return (datetime.utcnow() - self.start_time).total_seconds()
    
    def record_evaluation(self, latency_ms: float, hit: bool, rule_id: Optional[str] = None, promotion_type: Optional[str] = None):
        """Record a new evaluation in the metrics."""
        self.total_evaluations += 1
        self.total_latency_ms += latency_ms
        
        if hit:
            self.hits += 1
            if rule_id:
                self.rule_hit_counts[rule_id] = self.rule_hit_counts.get(rule_id, 0) + 1
            if promotion_type:
                self.promotion_type_counts[promotion_type] = self.promotion_type_counts.get(promotion_type, 0) + 1
        else:
            self.misses += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format."""
        return {
            'total_evaluations': self.total_evaluations,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hit_rate,
            'average_latency_ms': self.average_latency_ms,
            'uptime_seconds': self.uptime_seconds,
            'rule_hit_counts': self.rule_hit_counts,
            'promotion_type_counts': self.promotion_type_counts,
            'validation_errors': self.validation_errors,
            'evaluation_errors': self.evaluation_errors
        }