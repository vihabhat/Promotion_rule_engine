import datetime
import re
import hashlib
import random

class RuleMatcher:
    def __init__(self, time_provider=None):
        self.time_provider = time_provider or (lambda: datetime.datetime.now())

    def set_rules(self, rules):
        self.rules = rules

    def evaluate(self, player_data):
        if not player_data or 'player_id' not in player_data:
            raise ValueError("Player data must contain 'player_id'")

        normalized_data = self._normalize_player_data(player_data)
        applicable_rules = []

        for rule in self.rules:
            if not rule.get("enabled", True):
                continue
            if not self._match_conditions(rule.get("conditions", {}), player_data):
                continue
            if not self._within_time_window(rule.get("time_window")):
                continue
            if not self._within_ab_bucket(rule.get("ab_bucket"), player_data.get("player_id", "")):
                continue
            applicable_rules.append(rule)

        if not applicable_rules:
            return None

        # NEW: Return all matched promotions instead of selecting just one
        matched_promotions = [rule.get("promotion") for rule in applicable_rules]
        return matched_promotions


    def _normalize_player_data(self, player_data):
        normalized = player_data.copy()
    
        # Convert numeric fields
        numeric_fields = ['level', 'total_spent', 'days_since_last_purchase']
        for field in numeric_fields:
            if field in normalized:
                try:
                    normalized[field] = float(normalized[field])
                except (ValueError, TypeError):
                    normalized[field] = 0.0  # Default invalid numbers to 0
        return normalized
            
    def _match_conditions(self, conditions, player_data):
        for field, condition in conditions.items():
            player_value = player_data.get(field)
            if isinstance(condition, dict):
                for op, expected in condition.items():
                    if not self._apply_operator(op, player_value, expected):
                        return False
            else:
                if player_value != condition:
                    return False
        return True

    def _apply_operator(self, op, actual, expected):
        if actual is None:
            return False
        if op in ('gt', 'gte', 'lt', 'lte'):
            try:
                actual = float(actual)
                expected = float(expected)
            except (ValueError, TypeError):
                return False
        if op == "eq":
            return actual == expected
        elif op == "ne":
            return actual != expected
        elif op == "gt":
            return actual > expected
        elif op == "gte":
            return actual >= expected
        elif op == "lt":
            return actual < expected
        elif op == "lte":
            return actual <= expected
        elif op == "in":
            return actual in expected
        elif op == "not_in":
            return actual not in expected
        elif op == "contains":
            return isinstance(actual, (list, str)) and expected in actual
        elif op == "regex":
            return isinstance(actual, str) and re.match(expected, actual)
        return False

    def _within_time_window(self, time_window):
        if not time_window:
            return True

        now = self.time_provider()
        current_day = now.strftime("%A").lower()
        current_time = now.time()

        days = time_window.get("days_of_week")
        start = time_window.get("start_time")
        end = time_window.get("end_time")

        if days and current_day not in [d.lower() for d in days]:
            return False

        if start:
            start_time = datetime.datetime.strptime(start, "%H:%M").time()
            if current_time < start_time:
                return False

        if end:
            end_time = datetime.datetime.strptime(end, "%H:%M").time()
            if current_time > end_time:
                return False

        return True

    def _within_ab_bucket(self, ab_bucket, player_id):
        if not ab_bucket:
            return True
        bucket = self._get_ab_bucket(player_id)
        return bucket < ab_bucket.get('percentage', 0)

    def _get_ab_bucket(self, player_id):
        hash_val = int(hashlib.sha256(player_id.encode()).hexdigest(), 16)
        return hash_val % 100
    
    def _apply_weighted_selection(self, rules):
        total_weight = sum(rule.get('weight', 1.0) for rule in rules)
        if total_weight <= 0:
            return None
            
        rand = random.uniform(0, total_weight)
        cumulative = 0.0
        
        for rule in rules:
            cumulative += rule.get('weight', 1.0)
            if rand <= cumulative:
                return rule
        return rules[-1]  # fallback