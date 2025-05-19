from typing import Dict

from InquirerPy import inquirer
from InquirerPy.separator import Separator
from web3 import Web3

from eip_4337.accounts import AccountManager
from eip_4337.constants import (
    ACCOUNT_TYPES,
    DEFAULT_ETH_AMOUNTS,
    MINIMUM_DEFAULT_ACCOUNT_BALANCE,
)
from eip_4337.contracts import ContractManager, TransactionFailed
from eip_4337.outputs import (
    show_account_abstraction_info,
    show_accounts_info,
    show_accounts_state,
    show_beneficiary_info,
    show_bundler_info,
    show_chain_state,
    show_contract_state,
    show_contracts_info,
    show_eip_4337_info,
    show_entry_point_info,
    show_error_message,
    show_miner_info,
    show_node_accounts,
    show_relayer_info,
    show_simple_account_info,
    show_success_message,
    show_tool_info,
    show_transaction_logs,
    show_transaction_receipt,
    show_user_ops_info,
    show_warning_message,
    show_welcome_message,
)
from eip_4337.user_ops import UserOperationManager


def _get_amounts() -> Dict[str, int]:
    print("\nCreating accounts for {}.".format(", ".join(ACCOUNT_TYPES)))
    print("\nAccounts will be pre-funded with default amounts.")
    print("Default amounts:")
    amounts = DEFAULT_ETH_AMOUNTS.copy()
    for account, amt in amounts.items():
        print(f"  {account:<12}: {amt} ETH")
    print()

    change_defaults = inquirer.confirm(
        message="Would you like to change the default amounts?", default=False
    ).execute()
    print()

    if change_defaults:
        for account in ACCOUNT_TYPES:
            default_amount = amounts[account]
            amounts[account] = int(
                inquirer.text(
                    message=f"Amount of ETH to fund {account} with:",
                    default=str(default_amount),
                ).execute()
            )
    return amounts


def check_and_set_default_account_balance(
    w3: Web3,
) -> None:
    default_account = w3.eth.default_account
    if default_account and not AccountManager.sufficient_balance(
        w3, default_account, MINIMUM_DEFAULT_ACCOUNT_BALANCE
    ):
        if inquirer.confirm(
            message=f"Default account has insufficient balance. Would you like to fund it with {MINIMUM_DEFAULT_ACCOUNT_BALANCE} ETH?",
            default=True,
        ).execute():
            try:
                AccountManager.anvil_set_balance(
                    w3, default_account, MINIMUM_DEFAULT_ACCOUNT_BALANCE
                )
                show_success_message(
                    "Default account balance updated to {} ETH".format(
                        w3.from_wei(w3.eth.get_balance(default_account), "ether")
                    )
                )
            except Exception as e:
                raise Exception(
                    f"Failed to set balance for default account: {default_account}.\nError: {e}"
                )


def execute_user_operation(
    w3: Web3,
    accounts: AccountManager,
    contracts: ContractManager,
    user_ops: UserOperationManager,
) -> None:
    target = inquirer.text(
        message="Target address:", default=accounts.beneficiary.address
    ).execute()
    value = float(inquirer.text(message="Value (ETH):", default="0").execute())
    data = inquirer.text(message="Data (hex, 0x...):", default="0x").execute()
    value_wei = w3.to_wei(value, "ether")
    try:
        receipt = user_ops.execute_operation(target, value_wei, data)
        logs = contracts.retrieve_transaction_logs_from_receipt(receipt)

        show_success_message("Operation executed!")
        show_transaction_receipt(receipt)
        show_transaction_logs(logs)
    except Exception as e:
        raise Exception(f"Execute Operation failed: {e}")


def start() -> None:
    """Start an interactive EIP-4337 session."""
    import sys

    w3 = Web3(Web3.HTTPProvider("http://localhost:8545"))
    accounts = AccountManager(w3)
    contracts = ContractManager(w3)
    user_ops = UserOperationManager(w3, accounts, contracts)

    show_welcome_message()

    if not accounts.check_accounts_initialized():
        print("To initialize contracts, you must first initialize accounts.\n")

    print("What would you like to do?")

    def main_menu():
        menu_choices = [
            {
                "name": "Initialize accounts",
                "value": "Initialize accounts",
                "key": "a",
                "disabled": accounts.check_accounts_initialized(),
            },
            {
                "name": "Initialize contracts",
                "value": "Initialize contracts",
                "key": "c",
                "disabled": not accounts.check_accounts_initialized()
                or contracts.check_contracts_initialized(),
            },
            {
                "name": "User operation",
                "value": "User operation",
                "key": "u",
                "disabled": not accounts.check_accounts_initialized()
                or not contracts.check_contracts_initialized(),
            },
            {
                "name": "Fund accounts",
                "value": "Fund accounts",
                "key": "f",
                "disabled": not accounts.check_accounts_initialized(),
            },
            {"name": Separator()},
            {"name": "View status", "value": "View status", "key": "v"},
            {"name": "Help", "value": "Help", "key": "h"},
            {"name": "Exit", "value": "Exit", "key": "q"},
        ]

        select_prompt = inquirer.select(
            message="Choose an action:",
            choices=[c["name"] for c in menu_choices if not c.get("disabled")],
            pointer=">",
            qmark=">",
            instruction="(Use arrow keys or hotkeys: c/a/f/u/v/h/q)",
        )
        for c in menu_choices:
            key = c.get("key")
            value = c.get("value")
            if key:

                @select_prompt.register_kb(key)
                def _handler(event, value=value):
                    event.app.exit(result=value)

        return select_prompt.execute()

    while True:
        action = main_menu()
        if action == "Initialize accounts":
            print("\n=== Account Setup ===")
            print("Creating new accounts required for the EIP-4337 flow.\n")

            AccountManager.initialize_default_account(w3)

            try:
                check_and_set_default_account_balance(w3)
                accounts.initialize_accounts(_get_amounts())
            except Exception as e:
                show_error_message(str(e))
                continue

            show_success_message("Accounts created successfully.")
            show_accounts_state(w3, accounts)

        if action == "Initialize contracts":
            print("\n=== Contract Setup ===")
            print("This will deploy the EntryPoint and SimpleAccount contracts.\n")

            if inquirer.confirm(
                message="Are you sure you want to deploy the contracts? Any existing contracts will be lost.",
                default=True,
            ).execute():
                try:
                    entry_point = contracts.deploy_entry_point(accounts.owner)
                    show_success_message(
                        "EntryPoint deployed successfully @ {}".format(
                            entry_point.address
                        )
                    )

                    simple_account = contracts.deploy_simple_account(
                        accounts.owner, entry_point.address
                    )
                    show_success_message(
                        "SimpleAccount deployed successfully @ {}".format(
                            simple_account.address
                        )
                    )

                    # Fund the simple account
                    contracts.fund_simple_account(100, accounts.owner)
                except Exception as e:
                    if isinstance(e, TransactionFailed):
                        logs = contracts.retrieve_transaction_logs_from_receipt(
                            e.txn_receipt
                        )
                        if len(logs) > 0:
                            show_transaction_logs(logs)
                            continue
                        else:
                            try:
                                contracts.check_transaction_revert_reason(
                                    e.txn_receipt["transactionHash"],
                                    e.txn_receipt["blockNumber"],
                                )
                            except Exception as revert_reason:
                                show_error_message(
                                    str(f"Transaction reverted. {revert_reason}")
                                )
                                continue

                    show_error_message(str(e))
                    continue

                show_contract_state(w3, contracts)

        elif action == "User operation":
            print("\n=== User Operation ===")
            print("Execute a user operation on the EntryPoint.\n")

            try:
                execute_user_operation(w3, accounts, contracts, user_ops)
            except Exception as e:
                show_error_message(str(e))
                continue

            show_success_message("User operation executed successfully.")

        elif action == "Fund accounts":
            print("\n=== Fund Accounts ===")
            print("Top up accounts to the amounts specified.\n")

            try:
                check_and_set_default_account_balance(w3)
                accounts.fund_accounts(_get_amounts())
            except Exception as e:
                show_error_message(str(e))
                continue

            show_success_message("Accounts funded successfully.")
            show_accounts_state(w3, accounts)

        elif action == "View status":
            print("\n=== View Status ===")
            print("View the status of the node, accounts and contracts.\n")

            while True:
                status_action = inquirer.select(
                    message="Select an item to view the status:",
                    choices=[
                        "Show all",
                        "Chain state",
                        "Contracts",
                        "Accounts",
                        "Node accounts",
                        "Return to main menu",
                    ],
                    default="Show all",
                ).execute()

                has_errors = False
                if status_action == "Show all":
                    show_chain_state(w3)
                    has_errors = show_contract_state(w3, contracts)
                    has_errors = show_accounts_state(w3, accounts)
                    show_node_accounts(w3)
                if status_action == "Chain state":
                    show_chain_state(w3)

                if status_action == "Contracts":
                    has_errors = show_contract_state(w3, contracts)

                if status_action == "Accounts":
                    has_errors = show_accounts_state(w3, accounts)

                if status_action == "Node accounts":
                    show_node_accounts(w3)

                if status_action == "Return to main menu":
                    break

                if has_errors:
                    print()
                    show_warning_message(
                        "Contracts and accounts must be initialized before running this tool.\nRun the setup command to initialize them."
                    )

        elif action == "Help":
            print("\n=== Help ===")
            print("Find out more about this tool and the EIP-4337 flow.\n")

            while True:
                help_action = inquirer.select(
                    message="What would you like to learn?",
                    choices=[
                        "What is this tool?",
                        "What is EIP-4337?",
                        "What is account abstraction?",
                        "What accounts are needed?",
                        "What contracts are used?",
                        "What is a UserOperation?",
                        "What is an EntryPoint?",
                        "What is a SimpleAccount?",
                        "What is a bundler?",
                        "What is a beneficiary?",
                        "What is a relayer?",
                        "What is a miner?",
                        "Return to main menu",
                    ],
                ).execute()

                if help_action == "What is this tool?":
                    show_tool_info()
                elif help_action == "What is EIP-4337?":
                    show_eip_4337_info()
                elif help_action == "What is account abstraction?":
                    show_account_abstraction_info()
                elif help_action == "What accounts are needed?":
                    show_accounts_info()
                elif help_action == "What contracts are needed?":
                    show_contracts_info()
                elif help_action == "What is a UserOperation?":
                    show_user_ops_info()
                elif help_action == "What is an EntryPoint?":
                    show_entry_point_info()
                elif help_action == "What is a SimpleAccount?":
                    show_simple_account_info()
                elif help_action == "What is a bundler?":
                    show_bundler_info()
                elif help_action == "What is a beneficiary?":
                    show_beneficiary_info()
                elif help_action == "What is a relayer?":
                    show_relayer_info()
                elif help_action == "What is a miner?":
                    show_miner_info()
                elif help_action == "Return to main menu":
                    break

        elif action == "Exit":
            print("Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    start()
