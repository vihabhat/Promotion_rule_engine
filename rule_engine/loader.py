"""
YAML rule loader for the promotion rule engine.
Handles loading and validation of promotion rules from YAML configuration.
"""

import yaml
import os
from typing import List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class RuleLoader:
    
    def __init__(self, rules_file: str):
        self.rules_file = rules_file
        self.last_modified = None
    
    def load_rules(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.rules_file):
            raise FileNotFoundError(f"Rules file not found: {self.rules_file}")
        
        # Check if file has been modified
        current_modified = os.path.getmtime(self.rules_file)
        if self.last_modified and current_modified <= self.last_modified:
            logger.debug("Rules file not modified, skipping reload")
        
        self.last_modified = current_modified
        
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                
            if not data:
                logger.warning("Empty or invalid YAML file")
                return []
            
            # Extract rules from the configuration
            rules = data.get('rules', [])
            if not isinstance(rules, list):
                raise ValueError("Rules must be a list")
            
            # Validate each rule
            validated_rules = []
            for i, rule in enumerate(rules):
                try:
                    validated_rule = self._validate_rule(rule, i)
                    validated_rules.append(validated_rule)
                except ValueError as e:
                    logger.error(f"Rule {i} validation failed: {e}")
                    # Continue with other rules instead of failing completely
                    continue
            
            logger.info(f"Successfully loaded {len(validated_rules)} valid rules")
            return validated_rules
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading rules: {e}")
            raise
    
    def _validate_rule(self, rule: Dict[str, Any], rule_index: int) -> Dict[str, Any]:
        if not isinstance(rule, dict):
            raise ValueError(f"Rule {rule_index} must be a dictionary")
        
        # Required fields
        required_fields = ['id', 'priority', 'conditions', 'promotion']
        for field in required_fields:
            if field not in rule:
                raise ValueError(f"Rule {rule_index} missing required field: {field}")
        
        # Validate rule ID
        if not isinstance(rule['id'], str) or not rule['id'].strip():
            raise ValueError(f"Rule {rule_index} 'id' must be a non-empty string")
        
        # Validate priority (higher number = higher priority)
        if not isinstance(rule['priority'], int):
            raise ValueError(f"Rule {rule_index} 'priority' must be an integer")
        
        # Validate conditions
        conditions = rule['conditions']
        if not isinstance(conditions, dict):
            raise ValueError(f"Rule {rule_index} 'conditions' must be a dictionary")
        
        self._validate_conditions(conditions, rule_index)
        
        # Validate promotion
        promotion = rule['promotion']
        if not isinstance(promotion, dict):
            raise ValueError(f"Rule {rule_index} 'promotion' must be a dictionary")
        
        self._validate_promotion(promotion, rule_index)
        
        # Add default values for optional fields
        rule.setdefault('enabled', True)
        rule.setdefault('description', f"Promotion rule {rule['id']}")
        
        # Validate extensibility hooks (if present)
        if 'weight' in rule and not isinstance(rule['weight'], (int, float)):
            raise ValueError(f"Rule {rule_index} 'weight' must be a number")
        
        if 'ab_bucket' in rule and not isinstance(rule['ab_bucket'], str):
            raise ValueError(f"Rule {rule_index} 'ab_bucket' must be a string")
        
        if 'time_window' in rule:
            self._validate_time_window(rule['time_window'], rule_index)
        
        return rule
    
    def _validate_conditions(self, conditions: Dict[str, Any], rule_index: int):
        valid_operators = ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'not_in', 'contains', 'regex']
        valid_fields = [
            'level', 'spend_tier', 'country', 'days_since_last_purchase',
            'total_spent', 'current_balance', 'registration_date', 'player_id'
        ]
        
        for field, condition in conditions.items():
            if field not in valid_fields:
                logger.warning(f"Rule {rule_index}: Unknown condition field '{field}'")
            
            if isinstance(condition, dict):
                # Complex condition with operator
                if len(condition) != 1:
                    raise ValueError(f"Rule {rule_index} condition '{field}' must have exactly one operator")
                
                operator = list(condition.keys())[0]
                if operator not in valid_operators:
                    raise ValueError(f"Rule {rule_index} condition '{field}' has invalid operator '{operator}'")
                
                value = condition[operator]
                
                # Validate operator-specific value constraints
                if operator in ['in', 'not_in'] and not isinstance(value, list):
                    raise ValueError(f"Rule {rule_index} condition '{field}' with operator '{operator}' must have a list value")
                
            # Simple equality condition is also valid (field: value)
    
    def _validate_promotion(self, promotion: Dict[str, Any], rule_index: int):
        required_promotion_fields = ['id', 'type']
        for field in required_promotion_fields:
            if field not in promotion:
                raise ValueError(f"Rule {rule_index} promotion missing required field: {field}")
        
        if not isinstance(promotion['id'], str) or not promotion['id'].strip():
            raise ValueError(f"Rule {rule_index} promotion 'id' must be a non-empty string")
        
        if not isinstance(promotion['type'], str) or not promotion['type'].strip():
            raise ValueError(f"Rule {rule_index} promotion 'type' must be a non-empty string")
        
        # Validate numeric fields if present
        numeric_fields = ['amount', 'multiplier', 'duration_hours']
        for field in numeric_fields:
            if field in promotion and not isinstance(promotion[field], (int, float)):
                raise ValueError(f"Rule {rule_index} promotion '{field}' must be a number")
    
    def _validate_time_window(self, time_window: Dict[str, Any], rule_index: int):
        if not isinstance(time_window, dict):
            raise ValueError(f"Rule {rule_index} 'time_window' must be a dictionary")
        
        # Validate start and end times if present
        for time_field in ['start_time', 'end_time']:
            if time_field in time_window:
                time_value = time_window[time_field]
                if not isinstance(time_value, str):
                    raise ValueError(f"Rule {rule_index} time_window '{time_field}' must be a string")
                
                # Try to parse time format (HH:MM)
                try:
                    datetime.strptime(time_value, '%H:%M')
                except ValueError:
                    raise ValueError(f"Rule {rule_index} time_window '{time_field}' must be in HH:MM format")
        
        # Validate days of week if present
        if 'days_of_week' in time_window:
            days = time_window['days_of_week']
            if not isinstance(days, list):
                raise ValueError(f"Rule {rule_index} time_window 'days_of_week' must be a list")
            
            valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in days:
                if day.lower() not in valid_days:
                    raise ValueError(f"Rule {rule_index} time_window invalid day: {day}")
    
    def get_rules_info(self) -> Dict[str, Any]:
        if not os.path.exists(self.rules_file):
            return {'exists': False}
        
        stat = os.stat(self.rules_file)
        return {
            'exists': True,
            'path': self.rules_file,
            'size_bytes': stat.st_size,
            'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'readable': os.access(self.rules_file, os.R_OK)
        }