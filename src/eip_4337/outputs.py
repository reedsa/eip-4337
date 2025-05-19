from typing import Any, Dict, List

from eth_typing import ChecksumAddress
from web3 import Web3
from web3.providers import (
    AsyncHTTPProvider,
    EthereumTesterProvider,
    HTTPProvider,
    WebSocketProvider,
)

from eip_4337.accounts import AccountManager
from eip_4337.contracts import ContractManager

PROVIDER_TYPES = {
    "http": HTTPProvider,
    "ws": WebSocketProvider,
    "async": AsyncHTTPProvider,
    "test": EthereumTesterProvider,
}


def show_error_message(message: str, show_space: bool = True) -> None:
    print(f"❌ {message}")
    if show_space:
        print()


def show_warning_message(message: str, show_space: bool = True) -> None:
    print(f"⚠️ {message}")
    if show_space:
        print()


def show_success_message(message: str, show_space: bool = True) -> None:
    print(f"✅ {message}")
    if show_space:
        print()


def show_transaction_receipt(receipt: Dict[str, Any]) -> None:
    print("\nTransaction receipt:\n")
    print(f"Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
    print(f"Gas Used: {receipt['gasUsed']}")
    print(f"Block Number: {receipt['blockNumber']}")


def show_transaction_logs(logs: List[Dict[str, Any]]) -> None:
    print("\nTransaction logs:\n")
    for log in logs:
        print(f"{log['source']} emitted log: {log['event']}")
        for arg in log["args"]:
            print(f"{arg}: {log['args'][arg]}")
        print()


def show_welcome_message() -> None:
    print("\n=== 🧰 Welcome to the EIP-4337 Tool ===\n")
    print("This tool will help you interact with the EIP-4337 protocol.")
    print(
        "You can initialize accounts, deploy contracts, fund accounts, and execute user operations."
    )
    print("You can also view the status of the node, accounts, and contracts.\n")


def show_chain_state(w3: Web3) -> None:
    print("\n=== ♢ Chain state ===\n")
    print(f"Block number: {w3.eth.block_number}")
    print(f"Chain ID: {w3.eth.chain_id}")
    print(f"Gas price: {w3.eth.gas_price}")
    print(f"Max priority fee: {w3.eth.max_priority_fee}")
    print(f"Default account: {w3.eth.default_account}")
    print(f"Syncing: {w3.eth.syncing}")


def show_contract_state(w3: Web3, contracts: ContractManager) -> bool:
    print("\n=== 📝 Contracts ===\n")

    has_error = False
    contract_addresses = contracts.get_contract_addresses()

    if contract_addresses["EntryPoint"] and contract_addresses["SimpleAccount"]:
        # Get the balance from EntryPoint
        simple_account_balance = contracts.entry_point.functions.balanceOf(
            contracts.simple_account.address
        ).call()

        print(f"EntryPoint contract: {contract_addresses['EntryPoint']}")
        print(
            f"Balance: {w3.from_wei(w3.eth.get_balance(contract_addresses['EntryPoint']), 'ether')} ETH"
        )
        print()

        print(f"SimpleAccount: {contract_addresses['SimpleAccount']}")
        print(
            f"Balance: {w3.from_wei(w3.eth.get_balance(contract_addresses['SimpleAccount']), 'ether')} ETH"
        )
        print(
            f"Gas balance (via EntryPoint): {w3.from_wei(simple_account_balance, 'ether')} ETH"
        )
        print()
    else:
        show_error_message("No contracts are available!")
        has_error = True

    return has_error


def show_account_state(
    w3: Web3, account_address: ChecksumAddress, account_type: str
) -> None:
    account_text = "{} account: {} with balance {} ETH"
    print(
        account_text.format(
            account_type.capitalize(),
            account_address,
            w3.from_wei(w3.eth.get_balance(account_address), "ether"),
        )
    )


def show_node_accounts(w3: Web3) -> None:
    print("\n=== 🔓 Node accounts ===\n")

    for i, account in enumerate(w3.eth.accounts):
        show_account_state(w3, account, f"account[{i}]")


def show_accounts_state(w3: Web3, accounts: AccountManager) -> bool:
    print("\n=== 🔑 Accounts ===\n")

    has_error = False

    default_account = w3.eth.default_account
    if default_account:
        show_account_state(w3, default_account, "default")
    else:
        has_error = True
        show_error_message("Default account not initialized!", show_space=False)

    for account_type, account_address in accounts.get_account_addresses().items():
        if account_address:
            show_account_state(w3, account_address, account_type)
        else:
            has_error = True
            show_error_message(
                f"Account {account_type} not initialized", show_space=False
            )
    print()

    return has_error


def show_tool_info() -> None:
    print("\n=== EIP-4337 Tool ===\n")
    print("This tool is a simple CLI for learning about EIP-4337 Account Abstraction.")
    print(
        "It is designed to help you understand the flow of EIP-4337 and Account Abstraction."
    )
    print("Please refer to the spec for more information.")
    print("https://eips.ethereum.org/EIPS/eip-4337")
    print()


def show_eip_4337_info() -> None:
    print("\n=== EIP-4337 ===\n")
    print("EIP-4337 and Account Abstraction:")
    print("EIP-4337 is a specification for account abstraction on Ethereum.")
    print(
        "It allows you to create and fund accounts, deploy contracts, and execute user operations."
    )
    print("Please refer to the spec for more information.")
    print("https://eips.ethereum.org/EIPS/eip-4337")
    print()


def show_account_abstraction_info() -> None:
    print("\n=== Account Abstraction ===\n")
    print(
        "Account Abstraction is a concept that allows you to create and fund accounts, deploy contracts, and execute user operations."
    )
    print("Please refer to the spec for more information.")
    print("https://eips.ethereum.org/EIPS/eip-4337")
    print()


def show_accounts_info() -> None:
    print("\n=== Accounts ===\n")
    print("This tool will create and fund the following accounts:")
    print(
        "  owner       : Your main externally owned account (EOA), which controls the SimpleAccount and deploys contracts."
    )
    print(
        "  bundler     : An account that submits UserOperations to the EntryPoint (simulates a bundler/relayer)."
    )
    print(
        "  beneficiary : An account that receives fees or rewards from the EntryPoint (simulates a miner/beneficiary).\n"
    )
    print(
        "You can use these accounts to test and interact with the EIP-4337 Account Abstraction flow."
    )
    print("You may change the default funding amounts if you wish.")
    print()


def show_contracts_info() -> None:
    print("\n=== Contracts ===\n")
    print("This tool will deploy the following contracts:")
    print(
        "  EntryPoint   : The central contract that receives UserOperations, verifies them, and manages gas and execution."
    )
    print(
        "  SimpleAccount: A minimal smart contract wallet (account abstraction) that is controlled by the owner EOA."
    )
    print()


def show_user_ops_info() -> None:
    print("\n=== User Operations ===\n")
    print("This tool will execute a UserOperation on the EntryPoint.")
    print("A UserOperation is a transaction that is sent to the EntryPoint.")
    print("It is a way to execute a transaction on the EntryPoint.")
    print("Please refer to the spec for more information.")
    print("https://eips.ethereum.org/EIPS/eip-4337")
    print()


def show_entry_point_info() -> None:
    print("\n=== EntryPoint Contract ===\n")
    print(
        "The EntryPoint is the central contract that receives UserOperations, verifies them, and manages gas and execution."
    )
    print("Please refer to the spec for more information.")
    print("https://eips.ethereum.org/EIPS/eip-4337")
    print()


def show_simple_account_info() -> None:
    print("\n=== SimpleAccount Contract ===\n")
    print(
        "The SimpleAccount is a minimal smart contract wallet (account abstraction) that is controlled by the owner EOA."
    )
    print("Please refer to the spec for more information.")
    print("https://eips.ethereum.org/EIPS/eip-4337")
    print()


def show_bundler_info() -> None:
    print("\n=== Bundler ===\n")
    print("The Bundler is an account that submits UserOperations to the EntryPoint.")
    print("It is a way to submit UserOperations to the EntryPoint.")
    print("Please refer to the spec for more information.")
    print("https://eips.ethereum.org/EIPS/eip-4337")
    print()


def show_beneficiary_info() -> None:
    print("\n=== Beneficiary ===\n")
    print(
        "The Beneficiary is an account that receives fees or rewards from the EntryPoint."
    )
    print("It is a way to receive fees or rewards from the EntryPoint.")
    print("Please refer to the spec for more information.")
    print("https://eips.ethereum.org/EIPS/eip-4337")
    print()


def show_relayer_info() -> None:
    print("\n=== Relayer ===\n")
    print("The Relayer is an account that relays UserOperations to the EntryPoint.")
    print("It is a way to relay UserOperations to the EntryPoint.")
    print("Please refer to the spec for more information.")
    print("https://eips.ethereum.org/EIPS/eip-4337")
    print()


def show_miner_info() -> None:
    print("\n=== Miner ===\n")
    print("The Miner is an account that mines UserOperations to the EntryPoint.")
    print("It is a way to mine UserOperations to the EntryPoint.")
    print("Please refer to the spec for more information.")
    print("https://eips.ethereum.org/EIPS/eip-4337")
    print()
