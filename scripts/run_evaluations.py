import yaml
import json
from scripts.generate_users import generate_users, save_users_to_json
from rule_engine.matcher import RuleMatcher

def load_rules_from_file(filepath="rules/rules.yaml"):
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
        return data.get("rules", [])

def evaluate_users(users, rules):
    matcher = RuleMatcher()
    matcher.set_rules(rules)

    results = []
    for user in users:
        promotion = matcher.evaluate(user)
        results.append({
            "player_id": user['player_id'],
            "matched_promotion": promotion,
            "user_profile": user
        })
    return results

def main(user_count=50):
    print("[1] Generating users...")
    users = generate_users(user_count)

    print("[2] Loading rules...")
    rules = load_rules_from_file()

    print("[3] Evaluating users...")
    results = evaluate_users(users, rules)

    output_path = "data/evaluation_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[✔] Evaluation complete! Results saved to {output_path}")

if __name__ == "__main__":
    main()
