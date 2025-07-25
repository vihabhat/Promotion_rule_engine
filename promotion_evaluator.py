# import yaml
# from rule_engine.matcher import RuleMatcher
# from yaml_loader import load_rules_from_yaml

# def load_rules_from_yaml(filepath="rules/rules.yaml"):
#     with open(filepath, 'r') as f:
#         return yaml.safe_load(f)

# def evaluate_user_promotions(user_profile):
#     config = load_rules_from_yaml()
#     rules = config.get("rules", [])   # ✅ this is the key fix
#     matcher = RuleMatcher()
#     matcher.set_rules(rules)
#     return matcher.evaluate(user_profile)
import yaml

def load_rules_from_yaml(filepath='rules/rules.yaml'):
    with open(filepath, 'r') as file:
        data = yaml.safe_load(file)
        return data['rules']  # Return only the rules list
