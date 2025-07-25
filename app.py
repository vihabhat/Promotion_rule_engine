from flask import Flask, request, jsonify
from promotion_evaluator import load_rules_from_yaml
from rule_engine.matcher import RuleMatcher

app = Flask(__name__)

# Load rules into memory at startup
matcher = RuleMatcher()
matcher.set_rules(load_rules_from_yaml())

@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json()
    if not data or 'user_profile' not in data:
        return jsonify({"error": "Missing 'user_profile' in request"}), 400

    user_profile = data['user_profile']
    promotion = matcher.evaluate(user_profile)

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

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "Promotion Rule Engine is running.",
        "endpoints": ["/evaluate (POST)", "/reload_rules (POST)"]
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
