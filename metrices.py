"""
Metrics collection and reporting for the promotion rule engine.
Tracks performance, usage statistics, and provides observability.
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    
    def __init__(self):
        """Initialize the metrics collector."""
        self._lock = Lock()
        self._start_time = datetime.utcnow()
        
        # Core metrics
        self._total_evaluations = 0
        self._hits = 0
        self._misses = 0
        self._total_latency_ms = 0.0
        
        # Detailed tracking
        self._rule_hit_counts: Dict[str, int] = {}
        self._promotion_type_counts: Dict[str, int] = {}
        self._country_distribution: Dict[str, int] = {}
        self._spend_tier_distribution: Dict[str, int] = {}
        
        # Error tracking
        self._validation_errors = 0
        self._evaluation_errors = 0
        self._rule_loading_errors = 0
        
        # Performance tracking
        self._latency_buckets = {
            '0-10ms': 0,
            '10-50ms': 0,
            '50-100ms': 0,
            '100-500ms': 0,
            '500ms+': 0
        }
        
        # Hourly statistics for trend analysis
        self._hourly_stats: Dict[str, Dict[str, int]] = {}
    
    def record_evaluation(self, latency_ms: float, hit: bool, rule_id: Optional[str] = None, 
                         promotion_type: Optional[str] = None, country: Optional[str] = None,
                         spend_tier: Optional[str] = None):
        with self._lock:
            # Core metrics
            self._total_evaluations += 1
            self._total_latency_ms += latency_ms
            
            if hit:
                self._hits += 1
                if rule_id:
                    self._rule_hit_counts[rule_id] = self._rule_hit_counts.get(rule_id, 0) + 1
                if promotion_type:
                    self._promotion_type_counts[promotion_type] = self._promotion_type_counts.get(promotion_type, 0) + 1
            else:
                self._misses += 1
            
            # Distribution tracking
            if country:
                self._country_distribution[country] = self._country_distribution.get(country, 0) + 1
            if spend_tier:
                self._spend_tier_distribution[spend_tier] = self._spend_tier_distribution.get(spend_tier, 0) + 1
            
            # Latency buckets
            self._update_latency_bucket(latency_ms)
            
            # Hourly statistics
            self._update_hourly_stats(hit)
    
    def record_validation_error(self):
        """Record a validation error."""
        with self._lock:
            self._validation_errors += 1
    
    def record_evaluation_error(self):
        """Record an evaluation error."""
        with self._lock:
            self._evaluation_errors += 1
    
    def record_rule_loading_error(self):
        """Record a rule loading error."""
        with self._lock:
            self._rule_loading_errors += 1
    
    def _update_latency_bucket(self, latency_ms: float):
        """Update latency distribution buckets."""
        if latency_ms < 10:
            self._latency_buckets['0-10ms'] += 1
        elif latency_ms < 50:
            self._latency_buckets['10-50ms'] += 1
        elif latency_ms < 100:
            self._latency_buckets['50-100ms'] += 1
        elif latency_ms < 500:
            self._latency_buckets['100-500ms'] += 1
        else:
            self._latency_buckets['500ms+'] += 1
    
    def _update_hourly_stats(self, hit: bool):
        """Update hourly statistics for trend analysis."""
        current_hour = datetime.utcnow().strftime('%Y-%m-%d-%H')
        
        if current_hour not in self._hourly_stats:
            self._hourly_stats[current_hour] = {
                'evaluations': 0,
                'hits': 0,
                'misses': 0
            }
        
        stats = self._hourly_stats[current_hour]
        stats['evaluations'] += 1
        if hit:
            stats['hits'] += 1
        else:
            stats['misses'] += 1
        
        # Keep only last 24 hours of data
        if len(self._hourly_stats) > 24:
            oldest_hour = min(self._hourly_stats.keys())
            del self._hourly_stats[oldest_hour]
    
    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            uptime_seconds = (datetime.utcnow() - self._start_time).total_seconds()
            
            # Calculate derived metrics
            hit_rate = self._hits / self._total_evaluations if self._total_evaluations > 0 else 0.0
            average_latency = self._total_latency_ms / self._total_evaluations if self._total_evaluations > 0 else 0.0
            evaluations_per_second = self._total_evaluations / uptime_seconds if uptime_seconds > 0 else 0.0
            
            return {
                # Core metrics
                'total_evaluations': self._total_evaluations,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': round(hit_rate, 4),
                'average_latency_ms': round(average_latency, 2),
                'uptime_seconds': round(uptime_seconds, 2),
                'evaluations_per_second': round(evaluations_per_second, 2),
                
                # Performance metrics
                'latency_distribution': self._latency_buckets.copy(),
                
                # Business metrics
                'rule_hit_counts': self._rule_hit_counts.copy(),
                'promotion_type_distribution': self._promotion_type_counts.copy(),
                'country_distribution': dict(list(self._country_distribution.items())[:10]),  # Top 10 countries
                'spend_tier_distribution': self._spend_tier_distribution.copy(),
                
                # Error metrics
                'errors': {
                    'validation_errors': self._validation_errors,
                    'evaluation_errors': self._evaluation_errors,
                    'rule_loading_errors': self._rule_loading_errors
                },
                
                # Trend data
                'hourly_stats': self._hourly_stats.copy(),
                
                # Metadata
                'service_start_time': self._start_time.isoformat() + 'Z',
                'metrics_generated_at': datetime.utcnow().isoformat() + 'Z'
            }
    
    def get_health_metrics(self) -> Dict[str, Any]:
        with self._lock:
            uptime_seconds = (datetime.utcnow() - self._start_time).total_seconds()
            hit_rate = self._hits / self._total_evaluations if self._total_evaluations > 0 else 0.0
            average_latency = self._total_latency_ms / self._total_evaluations if self._total_evaluations > 0 else 0.0
            
            # Calculate error rate
            total_errors = self._validation_errors + self._evaluation_errors + self._rule_loading_errors
            error_rate = total_errors / self._total_evaluations if self._total_evaluations > 0 else 0.0
            
            return {
                'status': self._get_health_status(hit_rate, average_latency, error_rate),
                'uptime_seconds': round(uptime_seconds, 2),
                'total_evaluations': self._total_evaluations,
                'hit_rate': round(hit_rate, 4),
                'average_latency_ms': round(average_latency, 2),
                'error_rate': round(error_rate, 4),
                'last_evaluation': self._get_last_evaluation_info()
            }
    
    def _get_health_status(self, hit_rate: float, average_latency: float, error_rate: float) -> str:
        # Define thresholds for health assessment
        if error_rate > 0.1:  # More than 10% errors
            return 'unhealthy'
        elif average_latency > 1000:  # More than 1 second average latency
            return 'degraded'
        elif hit_rate < 0.1 and self._total_evaluations > 100:  # Very low hit rate with sufficient data
            return 'warning'
        else:
            return 'healthy'
    
    def _get_last_evaluation_info(self) -> Optional[str]:
        """Get information about the last evaluation (simplified)."""
        if self._total_evaluations > 0:
            return f"Total: {self._total_evaluations}, Latest hit rate: {self._hits / self._total_evaluations:.2%}"
        return None
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing or maintenance)."""
        with self._lock:
            logger.warning("Resetting all metrics")
            
            self._start_time = datetime.utcnow()
            self._total_evaluations = 0
            self._hits = 0
            self._misses = 0
            self._total_latency_ms = 0.0
            
            self._rule_hit_counts.clear()
            self._promotion_type_counts.clear()
            self._country_distribution.clear()
            self._spend_tier_distribution.clear()
            
            self._validation_errors = 0
            self._evaluation_errors = 0
            self._rule_loading_errors = 0
            
            for bucket in self._latency_buckets:
                self._latency_buckets[bucket] = 0
            
            self._hourly_stats.clear()
    
    def get_top_rules(self, limit: int = 10) -> Dict[str, int]:
        with self._lock:
            sorted_rules = sorted(self._rule_hit_counts.items(), key=lambda x: x[1], reverse=True)
            return dict(sorted_rules[:limit])
    
    def get_performance_summary(self) -> Dict[str, Any]:
        with self._lock:
            uptime_hours = (datetime.utcnow() - self._start_time).total_seconds() / 3600
            
            return {
                'evaluations_total': self._total_evaluations,
                'evaluations_per_hour': round(self._total_evaluations / uptime_hours if uptime_hours > 0 else 0, 1),
                'success_rate': round(self._hits / self._total_evaluations * 100 if self._total_evaluations > 0 else 0, 1),
                'avg_response_time_ms': round(self._total_latency_ms / self._total_evaluations if self._total_evaluations > 0 else 0, 1),
                'fast_responses_pct': round(self._latency_buckets['0-10ms'] / self._total_evaluations * 100 if self._total_evaluations > 0 else 0, 1),
                'error_rate_pct': round((self._validation_errors + self._evaluation_errors) / self._total_evaluations * 100 if self._total_evaluations > 0 else 0, 2),
                'top_promotion_type': max(self._promotion_type_counts.items(), key=lambda x: x[1])[0] if self._promotion_type_counts else None,
                'most_active_rule': max(self._rule_hit_counts.items(), key=lambda x: x[1])[0] if self._rule_hit_counts else None
            }