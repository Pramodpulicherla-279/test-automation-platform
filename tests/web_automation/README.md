# Krishivaas Web Automation Framework

## Structure
```
krishivaas_framework/
├── conftest.py               ← single browser session + shared fixtures
├── pytest.ini                ← asyncio_mode=auto, allure output dir
├── requirements.txt
│
├── pages/
│   ├── login_page.py         ← LoginPage  (allure.step wrapped)
│   └── onboarding_page.py    ← OnboardingPage (allure.step wrapped)
│
├── locators/
│   ├── login.json            ← login selectors
│   └── onboarding.json       ← onboarding selectors
│
├── test_data/
│   └── test_data.json        ← credentials, URLs, farmer data
│
├── tests/
│   ├── test_login.py         ← Login suite  (TC_L001, TC_L002)
│   └── test_onboarding.py    ← Onboarding suite (TC_001–TC_010)
│
├── utils/
│   └── allure_steps.py       ← screenshot attach helper
│
└── reports/
    └── allure-results/       ← raw allure JSON (auto-created)
```

## Allure Report Hierarchy
```
Login  (Feature)
  └─ TC_L001 – Successful login  (Story)
       ├─ Open application URL   (Step)
       ├─ Perform login          (Step)
       │    ├─ Fill email        (Step)
       │    ├─ Fill password     (Step)
       │    └─ Click login button(Step)
       └─ Assert URL             (Step)

Onboarding  (Feature)
  └─ TC_001 – Add Farmer → Add Farm  (Story)
       ├─ Open hamburger menu   (Step)
       ├─ Navigate to Season    (Step)
       ├─ Add Farmer            (Step)
       │    ├─ Click Farmer List (Step)
       │    ├─ Fill Name        (Step)
       │    └─ ...
       └─ Save Farm             (Step)
```

## Setup
```bash
pip install -r requirements.txt
playwright install chromium
```

## Run all tests
```bash
pytest tests/
```

## Run only Login suite
```bash
pytest tests/test_login.py
```

## Run only Onboarding suite
```bash
pytest tests/test_onboarding.py
```

## Run a single TC
```bash
pytest tests/test_onboarding.py::TestOnboarding::test_tc_001
```

## Generate + open Allure report
```bash
allure serve reports/allure-results
# or export static HTML:
allure generate reports/allure-results -o reports/allure-html --clean
```

## Config
- **locators** → edit `locators/*.json` (no Python changes needed)
- **credentials / URLs / test data** → edit `test_data/test_data.json`
- **headless mode** → change `headless=False` → `True` in `conftest.py`
