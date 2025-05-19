from typing import Any, Dict, List, Tuple, Union

from eth_typing import ChecksumAddress, HexStr
from solcx import compile_files, install_solc
from vyper import compile_code
from web3 import Web3
from web3.contract import Contract
from web3.types import TxParams, TxReceipt


class TransactionFailed(Exception):
    def __init__(self, message, txn_receipt):
        super().__init__(message)
        self.txn_receipt = txn_receipt


class ContractManager:
    """Manages contract deployment and interaction."""

    entry_point: Contract
    simple_account: Contract

    def __init__(self, w3: Web3) -> None:
        """Initialize the contract manager.

        Args:
            w3: Web3 instance to use for contract interaction
            owner: Web3 account object to use for deployment
        """
        self.w3 = w3

    def check_contracts_initialized(self) -> bool:
        """Check if the contracts are initialized.

        Returns:
            True if the contracts are initialized, False otherwise
        """
        entry_point = getattr(self, "entry_point", None)
        simple_account = getattr(self, "simple_account", None)
        return entry_point is not None and simple_account is not None

    def deploy_contract(
        self,
        owner: Any,
        abi: Dict[str, Any],
        bytecode: str,
        gas_limit: int,
        *args: Any,
    ) -> Contract:
        """Deploy a contract.

        Args:
            contract_name: Name of the contract to compile
            args: Arguments to pass to the contract constructor

        Returns:
            Deployed EntryPoint contract instance
        """
        if not owner:
            raise ValueError("Owner account must be set for contract deployment.")

        # Build deployment transaction
        tx: TxParams = {
            "from": owner.address,
            "gas": gas_limit,
            "nonce": self.w3.eth.get_transaction_count(owner.address),
        }

        # Deploy contract
        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        signed_tx = self.w3.eth.account.sign_transaction(
            contract.constructor(*args).build_transaction(tx), owner.key
        )
        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            raise e

        if receipt["status"] != 1 or receipt["contractAddress"] is None:
            raise Exception(f"Contract deployment failed: {receipt}")

        # Store contract instance
        return self.w3.eth.contract(address=receipt["contractAddress"], abi=abi)

    def compile_entry_point(self) -> Tuple[Dict[str, Any], str]:
        """Compile the EntryPoint contract.

        Returns:
            Tuple containing the ABI and bytecode of the compiled EntryPoint contract
        """
        install_solc("0.8.20")
        ep_compiled = compile_files(
            [
                "contracts/core/EntryPoint.sol",
            ],
            output_values=["abi", "bin"],
            base_path=".",
            import_remappings=[
                "@openzeppelin/contracts=node_modules/@openzeppelin/contracts/"
            ],
        )
        ep_abi = ep_compiled["contracts/core/EntryPoint.sol:EntryPoint"]["abi"]
        ep_bytecode = ep_compiled["contracts/core/EntryPoint.sol:EntryPoint"]["bin"]

        return ep_abi, ep_bytecode

    def deploy_entry_point(self, owner: Any) -> Contract:
        """Deploy the EntryPoint contract.

        Returns:
            Deployed EntryPoint contract instance
        """
        # Compile contract
        abi, bytecode = self.compile_entry_point()
        try:
            self.entry_point = self.deploy_contract(owner, abi, bytecode, 10_000_000)
        except Exception as e:
            raise e

        return self.entry_point

    def compile_simple_account(self) -> Tuple[Dict[str, Any], str]:
        """Compile the SimpleAccount contract.

        Returns:
            Tuple containing the ABI and bytecode of the compiled SimpleAccount contract
        """
        with open("contracts/SimpleAccount.vy", "r") as f:
            sa_source = f.read()
        sa_compiled = compile_code(sa_source, output_formats=["abi", "bytecode"])
        sa_abi = sa_compiled["abi"]
        sa_bytecode = sa_compiled["bytecode"]

        return sa_abi, sa_bytecode

    def deploy_simple_account(self, owner: Any, entry_point_address: str) -> Contract:
        """Deploy the SimpleAccount contract.

        Args:
            entry_point_address: Address of the EntryPoint contract

        Returns:
            Deployed SimpleAccount contract instance
        """
        # Compile contract
        abi, bytecode = self.compile_simple_account()
        try:
            self.simple_account = self.deploy_contract(
                owner, abi, bytecode, 5_000_000, owner.address, entry_point_address
            )
        except Exception as e:
            raise e

        return self.simple_account

    def get_contract_addresses(self) -> Dict[str, Union[ChecksumAddress, None]]:
        """Get addresses of deployed contracts.

        Returns:
            Dictionary mapping contract names to addresses
        """
        entry_point = getattr(self, "entry_point", None)
        simple_account = getattr(self, "simple_account", None)
        return {
            "EntryPoint": self.w3.to_checksum_address(entry_point.address)
            if entry_point
            else None,
            "SimpleAccount": self.w3.to_checksum_address(simple_account.address)
            if simple_account
            else None,
        }

    def check_transaction_revert_reason(
        self, txn_hash: HexStr, block_identifier: int
    ) -> None:
        """Check the revert reason of a transaction.

        Args:
            txn_receipt: Transaction receipt to check
        """
        try:
            tx = self.w3.eth.get_transaction(txn_hash)
            self.w3.eth.call(
                {
                    "to": tx["to"],
                    "from": tx["from"],
                    "data": tx["input"],
                    "value": tx["value"],
                    "gas": tx["gas"],
                },
                block_identifier=block_identifier,
            )
        except Exception as e:
            raise e

    def retrieve_transaction_logs_from_txn_hash(
        self, txn_hash: HexStr
    ) -> List[Dict[str, Any]]:
        """Retrieve and process logs from a transaction hash.

        Args:
            txn_hash: Transaction hash to retrieve logs from
        """
        txn_receipt = self.w3.eth.get_transaction_receipt(txn_hash)
        return self.retrieve_transaction_logs_from_receipt(txn_receipt)

    def retrieve_transaction_logs_from_receipt(
        self, txn_receipt: TxReceipt
    ) -> List[Dict[str, Any]]:
        """Retrieve and process logs from a transaction receipt.

        Args:
            txn_receipt: Transaction receipt containing logs
        """
        if len(txn_receipt["logs"]) == 0:
            return []

        # Process the logs
        transaction_logs = []
        try:
            for log in txn_receipt["logs"]:
                log_topic = Web3.to_hex(log["topics"][0])

                sa_events = self.simple_account.all_events()
                sa_topics = [event.topic for event in sa_events]
                sa_events_and_topics = zip(sa_events, sa_topics)

                ep_events = self.entry_point.all_events()
                ep_topics = [event.topic for event in ep_events]
                ep_events_and_topics = zip(ep_events, ep_topics)

                for event, topic in [*sa_events_and_topics, *ep_events_and_topics]:
                    if topic == log_topic:
                        processed_log = event.process_log(log)
                        contract_address = processed_log.address

                        if contract_address == self.simple_account.address:
                            log_source = "SimpleAddress"
                        elif contract_address == self.entry_point.address:
                            log_source = "EntryPoint"
                        else:
                            log_source = "Unknown"

                        transaction_logs.append(
                            {
                                "source": log_source,
                                "event": processed_log.event,
                                "args": processed_log.args,
                            }
                        )
        except Exception as e:
            raise e

        return transaction_logs

    def fund_simple_account(self, amount_eth: float, owner: Any) -> None:
        """Fund the simple account through the entry point.

        Args:
            amount_eth: Amount of ETH to deposit
            owner: Account to send the ETH from
        """
        entry_point = self.entry_point
        simple_account = self.simple_account

        # Deposit ETH to the simple account to send value with a user operation
        try:
            tx = {
                "from": owner.address,
                "to": simple_account.address,
                "value": self.w3.to_wei(amount_eth, "ether"),
                "gas": 100_000,
                "gasPrice": self.w3.eth.gas_price,
                "nonce": self.w3.eth.get_transaction_count(owner.address),
            }
            signed_tx = self.w3.eth.account.sign_transaction(tx, owner.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            txn_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if txn_receipt["status"] != 1:
                raise TransactionFailed("Transaction failed", txn_receipt)
        except Exception as e:
            if isinstance(e, TransactionFailed):
                raise
            raise Exception(f"Error funding SimpleAccount: {e}")

        # Deposit ETH to the entry point to cover gas fees for SimpleAccount
        tx = entry_point.functions.depositTo(
            simple_account.address,
        ).build_transaction(
            {
                "from": owner.address,
                "value": self.w3.to_wei(amount_eth, "ether"),
                "gas": 100_000,
                "nonce": self.w3.eth.get_transaction_count(owner.address),
            }
        )

        try:
            signed_tx = self.w3.eth.account.sign_transaction(tx, owner.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            print(
                f"Error funding EntryPoint to pay for gas on behalf of SimpleAccount: {e}"
            )
            raise e

        print(f"Initialized SimpleAccount with {amount_eth} ETH")
