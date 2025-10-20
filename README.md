# budget analyzer

a private, local-first personal finance tool to analyze spending, manage debt, and build a powerful, automated budget.

## features

-   **automated transaction sync**: securely syncs with all your bank accounts and credit cards via plaid.
-   **deep spending analysis**: identifies top spending categories, merchants, and locations.
-   **intelligent subscription detection**: finds recurring charges based on patterns, not just keywords.
-   **debt payoff strategies**: models debt avalanche & snowball methods to create a clear payoff plan.
-   **impulse buy prevention**: a "cooling-off" period for wants to ensure thoughtful purchases.
-   **inventory & expiration tracking**: tracks recurring purchases (like groceries or supplies) and alerts you to expiration dates.
-   **privacy-focused**: all your financial data stays on your local machine. nothing is stored in the cloud.

## architecture

the application is built with a modular design, separating data models, business logic (analyzers), and reporting.

-   `models/`: defines the core data structures (`transaction`, `debtaccount`, etc.).
-   `analyzers/`: contains all the business logic for processing financial data.
-   `reports/`: generates the final human-readable summary.
-   `scripts/`: provides interactive cli tools for managing different parts of the application.
-   `main.py`: the main entry point that runs the entire analysis pipeline.

## setup

### prerequisites

-   python 3.9+
-   a free plaid developer account (for bank syncing)

### installation

1.  **clone the repository**
    ```bash
    git clone https://github.com/mjs243/budget-analyzer.git
    cd budget-analyzer
    ```

2.  **run the setup script**
    this creates a python virtual environment (`venv`) and installs dependencies.
    ```bash
    # macos/linux
    bash setup.sh

    # windows
    setup.bat
    ```

3.  **activate the virtual environment**
    ```bash
    # macos/linux
    source venv/bin/activate

    # windows
    call venv\scripts\activate.bat
    ```

4.  **configure plaid**
    -   copy `config/.env.example` to `config/.env`.
    -   add your plaid `client_id` and `secret` to `config/.env`.
    -   run the interactive setup script to link your bank accounts:
        ```bash
        python scripts/plaid_setup.py
        ```
    -   follow the on-screen prompts. this will securely generate and save `access_tokens` to your `.env` file.

## usage

### running the main analysis

to run the full pipeline (sync transactions, analyze, and generate a report), simply run:

```bash
python main.py
```

the full report will be printed to the console and saved in `data/output/report.txt`.

### using the interactive cli tools

several cli tools are available in the `scripts/` directory for managing specific features:

-   **manage subscriptions**:
    ```bash
    python scripts/manage_subscriptions.py
    ```
-   **manage recurring purchases**:
    ```bash
    python scripts/manage_recurring_purchases.py
    ```
-   **manage your "wants" list**:
    ```bash
    python scripts/manage_wants.py
    ```
-   **manually sync from plaid**:
    ```bash
    python scripts/sync_plaid.py
    ```

## contributing

contributions are welcome! please open an issue or submit a pull request.

1.  fork the repository.
2.  create a new branch (`git checkout -b feature/amazing-feature`).
3.  commit your changes (`git commit -m 'add some amazing feature'`).
4.  push to the branch (`git push origin feature/amazing-feature`).
5.  open a pull request.

## license

this project is licensed under the mit license.