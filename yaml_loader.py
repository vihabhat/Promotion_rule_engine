import yaml

def load_rules_from_yaml(yaml_file='rules.yaml'):
    with open(yaml_file, 'r') as f:
        return yaml.safe_load(f)
