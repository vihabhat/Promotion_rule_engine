from flask import Flask, request, jsonify
from promotion_evaluator import load_rules_from_yaml
from rule_engine.matcher import RuleMatcher
from metrices import MetricsCollector
import time

app = Flask(__name__)

# Initialize matcher and metrics
matcher = RuleMatcher()
matcher.set_rules(load_rules_from_yaml())
metrics = MetricsCollector()

@app.route('/evaluate', methods=['POST'])
def evaluate():
    start_time = time.time()

    data = request.get_json()
    if not data or 'user_profile' not in data:
        return jsonify({"error": "Missing 'user_profile' in request"}), 400

    user_profile = data['user_profile']
    try:
        promotion = matcher.evaluate(user_profile)
        hit = promotion is not None
    except Exception:
        metrics.record_evaluation_error()
        raise

    # Calculate latency and record metrics
    latency_ms = (time.time() - start_time) * 1000
    if hit and isinstance(promotion, list) and len(promotion) > 0:
        metrics.record_evaluation(
            latency_ms=latency_ms,
            hit=True,
            rule_id=promotion[0].get('id'),
            promotion_type=promotion[0].get('type'),
            country=user_profile.get('country'),
            spend_tier=user_profile.get('spend_tier')
        )
    else:
        metrics.record_evaluation(
            latency_ms=latency_ms,
            hit=False,
            country=user_profile.get('country'),
            spend_tier=user_profile.get('spend_tier')
        )

    return jsonify({
        "player_id": user_profile.get("player_id", "unknown"),
        "matched_promotion": promotion
    }), 200

@app.route('/reload_rules', methods=['POST'])
def reload_rules():
    new_rules = load_rules_from_yaml()
    matcher.set_rules(new_rules)
    print("[INFO] Rules reloaded via /reload_rules")
    return jsonify({"status": "Rules reloaded successfully"}), 200

@app.route('/metrics', methods=['GET'])
def get_metrics():
    return jsonify(metrics.get_metrics()), 200

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "Promotion Rule Engine is running.",
        "endpoints": ["/evaluate (POST)", "/reload_rules (POST)", "/metrics (GET)"]
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
