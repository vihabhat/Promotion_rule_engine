
##  Promotion Rule Engine Microservice — Documentation

###  Objective

Design a small REST microservice that selects the most appropriate in-game promotion for a player based on configurable business rules defined in YAML format.

---

##  Technology Stack

* **Language:** Python 3.12
* **Framework:** Flask
* **Config Format:** YAML
* **Data Handling:** In-memory
* **Testing:** `curl`, Postman, PowerShell
* **AI Help:** ChatGPT (disclosed below)

---

##  Core Features

### 1. **Promotion Evaluation API**

* **Endpoint:** `POST /evaluate`
* **Request Body:** JSON with `user_profile` object
* **Response:** The most suitable promotion for the player, or `null` if none match.

### 2. **Hot Rule Reload**

* **Endpoint:** `POST /reload_rules`
* **Purpose:** Reload rules from `rules/rules.yaml` into memory without restarting the server.

### 3. **Metrics API**

* **Endpoint:** `GET /metrics`
* **Response:** JSON with:

  * Total evaluations
  * Hit count (rules matched)
  * Miss count (no rule matched)
  * Average latency in ms

---

##  Folder Structure

```
Promotion_rule_engine_microservice/
│
├── app.py # Flask API layer
├── promotion_evaluator.py # Main promotion interface
├── metrices.py
├── yaml_loader.py
├── rules
│  └── rules.yaml # Promotion rules config
├── rule_engine/
│ └── matcher.py # Core rule evaluation logic
│ └── loader.py
│ └── models.py
│
├── scripts/
│ ├── generate_users.py # Random user generator
│ ├── run_evaluations.py # Evaluate users in batch
│
├── data/
│ └── evaluation_results.json # Evaluation outputs
├── user/
│ └── generated_user.json # random users generated by faker
│
├── tests/
│ └── test_engine.py # Pytest unit tests
│
└── requirements.txt # Python dependencies

---

##  Sample Rules (YAML)

```yaml
rules:
  - id: promo1
    enabled: true
    conditions:
      level: { min: 10, max: 30 }
      country: [US, CA]
      spend_tier: vip
    time_window:
      start: "2024-01-01"
      end: "2025-12-31"
    promotion: "Double Gems Bonus"
```

---

##  Sample Request (PowerShell)

```powershell
$headers = @{ "Content-Type" = "application/json" }
$body = @{
  user_profile = @{
    player_id = "user123"
    level = 25
    total_spent = 5000
    current_balance = 1000
    country = "US"
    spend_tier = "vip"
    days_since_last_purchase = 15
    registration_date = "2023-01-01"
  }
}
$bodyJson = $body | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri http://localhost:5000/evaluate -Method POST -Headers $headers -Body $bodyJson

##  Installation

```bash
git clone https://github.com/vihabhat/Promotion_rule_engine_microservice.git
cd Promotion_rule_engine_microservice
pip install -r requirements.txt

Rules Configurations are stored in rules.yaml file

##  Runings

Running tests: 
"pytest"
There are 16 test cases all needs to be cleared.

Command to generate bulk users and save to JSON:
"python -m scripts.generate_users"

This script Simulates a list of user profiles with realistic values (like level, total_spent, spend_tier, etc.)

Saves the output to:
data/sample_users.json

Simulating Bulk Users:
"python -m scripts.run_evaluations"
this outputs the results to data/evaluation_results.json

Running the API:
"python app.py"

Test using powershell:
$headers = @{ "Content-Type" = "application/json" }
$body = @{
  user_profile = @{
    player_id = "test_user_001"
    level = 20
    total_spent = 12000
    current_balance = 1500
    country = "US"
    spend_tier = "vip"
    days_since_last_purchase = 10
    registration_date = "2022-05-12"
  }
}
$bodyJson = $body | ConvertTo-Json -Depth 5
Invoke-RestMethod -Uri http://localhost:5000/evaluate -Method POST -Headers $headers -Body $bodyJson

API Response :
{
  "player_id": "test_user_001",
  "matched_promotion": [
    {
      "id": "vip_bonus",
      "type": "bonus_credits",
      "amount": 200.0
    },
    {
      "id": "us_bonus",
      "type": "bonus_credits",
      "amount": 50.0
    }
  ]
}
---

##  Reflection and Rationale

### a. **Design Choices**

* Used Flask for a lightweight, quick-to-implement REST API.
* Rules are kept in YAML for human-readability and easy reconfiguration.
* Separated rule logic (`matcher.py`) from app logic (`app.py`) to maintain modularity and scalability.
* Metrics were stored in a global dictionary to reduce DB dependency.

### b. **Trade-offs**

| Choice                 | Trade-off Made                              |
| ---------------------- | ------------------------------------------- |
| In-memory rule loading | Fast access, but not persistent             |
| Simple YAML parsing    | Easy editing, but no schema validation      |
| Flask over FastAPI     | Less strict typing, but quicker prototyping |

### c. **Areas of Uncertainty**

* Considered whether to evaluate all matching rules or just return the first match. Chose first match, assuming business priority ordering in YAML.
* Unsure whether performance metrics should persist across restarts. Currently reset on server restart.

### d. **AI Assistance Disclosure**

* Used **ChatGPT** for:

  * Structuring `matcher.py` and `evaluate_user_promotions`.
  * Generating sample user evaluation code in PowerShell.
  * YAML rule formatting.

---

##  API Summary

| Endpoint        | Method | Description                          |
| --------------- | ------ | ------------------------------------ |
| `/`             | GET    | Service info and available endpoints |
| `/evaluate`     | POST   | Evaluate player for promotion        |
| `/reload_rules` | POST   | Reload rules from YAML               |
| `/metrics`      | GET    | Returns usage statistics             |

---

##  Good Coding Practices

 **Encapsulation:** Rule matching logic is inside `RuleMatcher` class.
 **Separation of Concerns:** YAML loading, rule matching, and API logic are split.
 **Error Handling:** Handles invalid input with meaningful 400 errors.
 **Modularity:** Each core logic exists in separate functions/files.
 **Naming:** Used meaningful and consistent variable/function names.
 **Docs:** Inline comments and structured `README.md` included.

---

##  Testing Tips

* Make sure to keep `rules.yaml` inside the `rules/` folder.
* Reload rules using:
  `Invoke-RestMethod -Uri http://localhost:5000/reload_rules -Method POST`
* Evaluate a player profile using:
  `Invoke-RestMethod -Uri http://localhost:5000/evaluate -Method POST -Headers $headers -Body $bodyJson`
* Fetch usage metrics with:
  `Invoke-RestMethod -Uri http://localhost:5000/metrics -Method GET`

---

 Designed For

1. Casino operators to run marketing experiments (A/B test promotions)
2. Scalable integration with player segmentation and user retention logic
3. Extendable rule system without code changes (just update YAML)


 Author
Viha Suhas Bhat
Built as part of an internship assignment with focus on backend microservice design, config-driven systems, and rule-based automation.