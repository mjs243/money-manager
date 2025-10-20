# developer & learner notes

this document contains deeper insights into the project's design, key python concepts used, and guidance for future development.

## 1. project philosophy & design rationale

-   **local first, always**: the primary design choice is that user financial data never leaves their machine. plaid provides a secure bridge for *importing* data, but we don't store anything on a third-party server. this is a key feature.
-   **modularity is key**: each piece of logic is in its own "analyzer" file. this makes the system easy to test, debug, and extend. want to add investment tracking? just create `analyzers/investment_analyzer.py` and plug it into `main.py` without touching existing code.
-   **data models are contracts**: the `models/` directory acts as the "source of truth" for our data structures. using python's `dataclasses` ensures that a `transaction` object always has the same shape, which prevents bugs.
-   **behavioral finance built-in**: features like the "wants cooling-off period" are intentionally designed to combat common financial pitfalls like impulse spending. the tool isn't just for reporting; it's designed to gently guide better financial habits.

## 2. pythonic principles for learners

this codebase uses several modern python features that are great to learn.

-   **`@dataclass`**: found in the `models/` directory. this decorator automatically generates methods like `__init__`, `__repr__`, etc. for classes that primarily store data. it saves a ton of boilerplate code.

    *before*:
    ```python
    class Transaction:
        def __init__(self, date, amount):
            self.date = date
            self.amount = amount
    ```
    *after*:
    ```python
    from dataclasses import dataclass
    @dataclass
    class Transaction:
        date: datetime
        amount: float
    ```

-   **`@property`**: this decorator lets you define a method that can be accessed like an attribute (without parentheses). it's perfect for calculated values. we use it in models to derive data, like `days_until_expiration`.

    ```python
    @property
    def is_expired(self) -> bool:
        return self.days_until_expiration == 0

    # usage:
    # if item.is_expired:  (not item.is_expired())
    ```

-   **type hinting**: notice how all function signatures and variables have types (e.g., `def my_func(name: str) -> bool:`). this doesn't change how the code runs, but it provides immense benefits:
    -   it makes the code self-documenting.
    -   it allows tools like vscode's intellisense to provide better autocompletion.
    -   it helps prevent type-related bugs.

-   **`pathlib` for file paths**: instead of using strings for file paths like `"data/output/report.txt"`, we use `from pathlib import path`. this makes path manipulation operating-system-agnostic (it works on windows, mac, and linux without changes).

## 3. algorithm deep dives

-   **subscription detection**: the core logic is in `analyzers/subscriptions.py`. we don't use keywords because they are unreliable (e.g., an "amazon" charge could be a one-time purchase or a recurring prime subscription). instead, we group all transactions by merchant, calculate the number of days between each transaction, and then find the *standard deviation* of those intervals. if the standard deviation is low, it means the charges are happening at very regular intervals, and we can confidently classify it as a subscription.
-   **credit card payment schedule**: the `credit_card_tracker` is designed to mimic a common debt-reduction strategy: paying off your card in full frequently to avoid interest. by automatically creating a payment plan for the 15th and end-of-month, it encourages paying down the balance before the statement period closes, which also helps keep credit utilization low.

## 4. how to extend the application (a tutorial)

let's say you want to add a new feature: **net worth tracking**.

1.  **create the model**: in `models/`, create `asset.py`. an asset could be a savings account balance, an investment account, or a physical asset like a car.
    ```python
    # models/asset.py
    @dataclass
    class Asset:
        name: str
        asset_type: str # 'cash', 'investment', 'physical'
        value: float
        last_updated: datetime
    ```

2.  **create the analyzer**: in `analyzers/`, create `net_worth_analyzer.py`.
    -   it would take a list of `asset` objects and the `debtanalyzer` as input.
    -   it would have a method `calculate_net_worth()` that sums all asset values and subtracts all debt balances.

3.  **create the manager**: create `analyzers/asset_manager.py` (similar to the subscription manager) to add/update assets stored in a new `data/assets.json` file.

4.  **plug into `main.py`**:
    -   import the new analyzer.
    -   initialize it: `asset_manager = assetmanager()` and `net_worth_analyzer = networthanalyzer(asset_manager.get_assets(), debt_analyzer)`.
    -   pass it to the `reporter`: `reporter.net_worth_analyzer = net_worth_analyzer`.

5.  **update the report**: in `reports/reporter.py`, add a new section to display the net worth calculation.




# Future Features

1. **Net Worth Tracking:** this is the single biggest missing piece. by combining your Plaid account balances (assets) with your debt balances (liabilities), you can track your total net worth over time, which is the ultimate measure of financial health.

2. **Budget vs. Actuals:** create a monthly process that compares your spending against the targets in config.py. it could generate a report showing where you were over or under budget, providing direct, actionable feedback.

3. **Interactive Web UI (with Flask):** a simple web dashboard would be a massive upgrade from the CLI. you could use libraries like plotly or chart.js to create interactive graphs of your spending, making the data much easier to visualize and understand.