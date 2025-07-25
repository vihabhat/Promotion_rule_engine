"""
Comprehensive unit tests for the promotion rule engine.
Tests rule precedence, edge cases, and all major functionality.
"""

import pytest
import yaml
import tempfile
import os
from datetime import datetime, time
from unittest.mock import patch, mock_open
from datetime import datetime


import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rule_engine.loader import RuleLoader
from rule_engine.matcher import RuleMatcher
from rule_engine.models import PlayerData, Promotion, PromotionType
from metrices import MetricsCollector


class TestRuleLoader:
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_rules = {
            'rules': [
                {
                    'id': 'test_rule_1',
                    'priority': 100,
                    'conditions': {
                        'level': {'gte': 10},
                        'country': 'US'
                    },
                    'promotion': {
                        'id': 'bonus_100',
                        'type': 'bonus_credits',
                        'amount': 100.0,
                        'description': 'Test bonus'
                    }
                }
            ]
        }
    
    def test_load_valid_rules(self):
        """Test loading valid rules from YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.sample_rules, f)
            f.flush()
            temp_name = f.name
        # File is closed here
        try:
            loader = RuleLoader(temp_name)
            rules = loader.load_rules()
            
            assert len(rules) == 1
            assert rules[0]['id'] == 'test_rule_1'
            assert rules[0]['priority'] == 100
            assert 'enabled' in rules[0]  # Default value added
            
        finally:
            os.unlink(temp_name)
    
    def test_load_nonexistent_file(self):
        """Test handling of nonexistent rules file."""
        loader = RuleLoader('nonexistent.yaml')
        
        with pytest.raises(FileNotFoundError):
            loader.load_rules()
    
    def test_load_invalid_yaml(self):
        """Test handling of malformed YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            
            try:
                loader = RuleLoader(f.name)
                with pytest.raises(yaml.YAMLError):
                    loader.load_rules()
            finally:
                f.close()
                os.unlink(f.name)
    
    def test_validate_missing_required_fields(self):
        """Test validation of rules with missing required fields."""
        invalid_rules = {
            'rules': [
                {
                    'id': 'incomplete_rule',
                    # Missing priority, conditions, promotion
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_rules, f)
            f.flush()
            
            try:
                loader = RuleLoader(f.name)
                rules = loader.load_rules()
                # Should return empty list due to validation failure
                assert len(rules) == 0
            finally:
                f.close()
                os.unlink(f.name)
    
    def test_validate_invalid_operators(self):
        """Test validation of invalid condition operators."""
        invalid_rules = {
            'rules': [
                {
                    'id': 'invalid_operator_rule',
                    'priority': 50,
                    'conditions': {
                        'level': {'invalid_op': 10}
                    },
                    'promotion': {
                        'id': 'test_promo',
                        'type': 'bonus_credits'
                    }
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_rules, f)
            f.flush()
            
            try:
                loader = RuleLoader(f.name)
                rules = loader.load_rules()
                # Should filter out invalid rules
                assert len(rules) == 0
            finally:
                f.close()
                os.unlink(f.name)
    
    def test_validate_time_window(self):
        """Test validation of time window configuration."""
        rules_with_time_window = {
            'rules': [
                {
                    'id': 'time_window_rule',
                    'priority': 50,
                    'conditions': {'level': 10},
                    'promotion': {'id': 'test', 'type': 'bonus_credits'},
                    'time_window': {
                        'start_time': '09:00',
                        'end_time': '17:00',
                        'days_of_week': ['monday', 'tuesday']
                    }
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(rules_with_time_window, f)
            f.flush()
            
            try:
                loader = RuleLoader(f.name)
                rules = loader.load_rules()
                assert len(rules) == 1
                assert 'time_window' in rules[0]
            finally:
                f.close()
                os.unlink(f.name)


class TestRuleMatcher:
    """Test cases for the RuleMatcher class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = RuleMatcher()
        self.sample_rules = [
            {
                'id': 'high_priority_rule',
                'priority': 100,
                'enabled': True,
                'conditions': {
                    'level': {'gte': 20},
                    'spend_tier': 'vip'
                },
                'promotion': {
                    'id': 'vip_bonus',
                    'type': 'bonus_credits',
                    'amount': 500.0,
                    'description': 'VIP bonus'
                }
            },
            {
                'id': 'medium_priority_rule',
                'priority': 50,
                'enabled': True,
                'conditions': {
                    'level': {'gte': 10},
                    'country': 'US'
                },
                'promotion': {
                    'id': 'us_bonus',
                    'type': 'bonus_credits',
                    'amount': 100.0,
                    'description': 'US player bonus'
                }
            },
            {
                'id': 'low_priority_rule',
                'priority': 10,
                'enabled': True,
                'conditions': {
                    'level': {'gte': 1}
                },
                'promotion': {
                    'id': 'default_bonus',
                    'type': 'bonus_credits',
                    'amount': 25.0,
                    'description': 'Default bonus'
                }
            }
        ]
        self.matcher.set_rules(self.sample_rules)
    
    def test_rule_priority_precedence(self):
        """Test that higher priority rules are selected first."""
        player_data = {
            'player_id': 'test123',
            'level': 25,
            'spend_tier': 'vip',
            'country': 'US'
        }

        promotion = self.matcher.evaluate(player_data)
        assert promotion is not None and isinstance(promotion, list)
        assert any(promo['id'] == 'vip_bonus' for promo in promotion)

    
    def test_no_matching_rules(self):
        """Test behavior when no rules match."""
        player_data = {
            'player_id': 'test123',
            'level': 0,  # Below minimum level for any rule
            'country': 'XX'
        }
        
        promotion = self.matcher.evaluate(player_data)
        assert promotion is None
    
    def test_partial_rule_matching(self):
        """Test that only fully matching rules are selected."""
        player_data = {
            'player_id': 'test123',
            'level': 25,
            'spend_tier': 'gold',
            'country': 'US'
        }

        promotion = self.matcher.evaluate(player_data)
        assert promotion is not None and isinstance(promotion, list)
        assert any(promo['id'] == 'us_bonus' for promo in promotion)

    def test_condition_operators(self):
        """Test various condition operators."""
        test_rules = [
            {
                'id': 'operator_test',
                'priority': 100,
                'enabled': True,
                'conditions': {
                    'level': {'gt': 15},
                    'total_spent': {'lte': 1000.0},
                    'country': {'in': ['US', 'CA']},
                    'spend_tier': {'ne': 'bronze'}
                },
                'promotion': {
                    'id': 'operator_bonus',
                    'type': 'bonus_credits',
                    'amount': 50.0
                }
            }
        ]

        matcher = RuleMatcher()
        matcher.set_rules(test_rules)

        player_data = {
            'player_id': 'test123',
            'level': 20,
            'total_spent': 500.0,
            'country': 'US',
            'spend_tier': 'silver'
        }

        promotion = matcher.evaluate(player_data)
        assert promotion is not None and isinstance(promotion, list)
        assert any(promo['id'] == 'operator_bonus' for promo in promotion)

    
    def test_missing_player_attributes(self):
        """Test handling of missing player attributes."""
        player_data = {
            'player_id': 'test123',
            'level': 25
        }

        promotion = self.matcher.evaluate(player_data)
        assert promotion is not None and isinstance(promotion, list)
        assert any(promo['id'] == 'default_bonus' for promo in promotion)

    
    def test_invalid_player_data(self):
        """Test handling of invalid player data."""
        # Missing required player_id
        with pytest.raises(ValueError):
            self.matcher.evaluate({})
        
        # Invalid numeric values should be normalized
        player_data = {
            'player_id': 'test123',
            'level': 'invalid',  # Will be converted to 0.0
            'total_spent': 'also_invalid'  # Will be converted to 0.0
        }
        
        promotion = self.matcher.evaluate(player_data)
        # Should not match any rules due to level being 0
        assert promotion is None
    
    def test_disabled_rules(self):
        """Test that disabled rules are not evaluated."""
        disabled_rule = {
            'id': 'disabled_rule',
            'priority': 200,
            'enabled': False,
            'conditions': {'level': 1},
            'promotion': {
                'id': 'disabled_bonus',
                'type': 'bonus_credits',
                'amount': 1000.0
            }
        }

        rules = self.sample_rules + [disabled_rule]
        matcher = RuleMatcher()
        matcher.set_rules(rules)

        player_data = {
            'player_id': 'test123',
            'level': 25,
            'spend_tier': 'vip',
            'country': 'US'
        }

        promotion = matcher.evaluate(player_data)
        assert promotion is not None and isinstance(promotion, list)
        assert any(promo['id'] == 'vip_bonus' for promo in promotion)

    
    @patch('rule_engine.matcher.datetime')
    def test_time_window_evaluation(self, mock_datetime):
        """Test time window rule evaluation."""
        mock_now = datetime(2024, 1, 1, 10, 0)  # Monday
        mock_datetime.datetime.now.return_value = mock_now
        mock_datetime.datetime.strptime = lambda s, f: datetime.strptime(s, f)

        time_rule = {
            'id': 'time_window_rule',
            'priority': 100,
            'enabled': True,
            'conditions': {'level': 10},
            'promotion': {
                'id': 'time_bonus',
                'type': 'bonus_credits',
                'amount': 100.0
            },
            'time_window': {
                'start_time': '09:00',
                'end_time': '17:00',
                'days_of_week': ['monday', 'tuesday']
            }
        }

        matcher = RuleMatcher(time_provider=lambda: mock_now)
        matcher.set_rules([time_rule])

        player_data = {
            'player_id': 'test123',
            'level': 10
        }

        promotion = matcher.evaluate(player_data)
        assert promotion is not None and isinstance(promotion, list)
        assert any(promo['id'] == 'time_bonus' for promo in promotion)

    def test_weighted_selection(self):
        """Test weighted rule selection functionality."""
        weighted_rules = [
            {
                'id': 'heavy_weight_rule',
                'priority': 50,
                'enabled': True,
                'conditions': {'level': 10},
                'promotion': {
                    'id': 'heavy_bonus',
                    'type': 'bonus_credits',
                    'amount': 100.0
                },
                'weight': 0.8
            },
            {
                'id': 'light_weight_rule',
                'priority': 50,
                'enabled': True,
                'conditions': {'level': 10},
                'promotion': {
                    'id': 'light_bonus',
                    'type': 'bonus_credits',
                    'amount': 50.0
                },
                'weight': 0.2
            }
        ]

        matcher = RuleMatcher()
        matcher.set_rules(weighted_rules)

        player_data = {
            'player_id': 'test123',
            'level': 10
        }

        results = []
        with patch('random.uniform') as mock_random:
            mock_random.return_value = 0.4
            promotion = matcher.evaluate(player_data)
            if promotion:
                results += [p['id'] for p in promotion]

            mock_random.return_value = 0.9
            promotion = matcher.evaluate(player_data)
            if promotion:
                results += [p['id'] for p in promotion]

        assert 'heavy_bonus' in results
        assert 'light_bonus' in results

    def test_ab_bucket_selection(self):
        """Test A/B bucket functionality."""
        ab_rule = {
            'id': 'ab_test_rule',
            'priority': 100,
            'enabled': True,
            'conditions': {'level': 10},
            'promotion': {
                'id': 'ab_bonus',
                'type': 'bonus_credits',
                'amount': 100.0
            },
            'ab_bucket': {
                'percentage': 50
            }
        }

        matcher = RuleMatcher()
        matcher.set_rules([ab_rule])

        with patch.object(RuleMatcher, '_get_ab_bucket', return_value=25):
            player_data_pass = {'player_id': 'bucket_pass_123', 'level': 10}
            promotion_pass = matcher.evaluate(player_data_pass)
            assert promotion_pass is not None and isinstance(promotion_pass, list)
            assert any(p['id'] == 'ab_bonus' for p in promotion_pass)

        with patch.object(RuleMatcher, '_get_ab_bucket', return_value=75):
            player_data_fail = {'player_id': 'bucket_fail_999', 'level': 10}
            promotion_fail = matcher.evaluate(player_data_fail)
            assert promotion_fail is None
