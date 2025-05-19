from typing import Dict, Tuple

from web3 import Web3
from web3.types import TxReceipt

from eip_4337.accounts import AccountManager
from eip_4337.contracts import ContractManager


class UserOperationManager:
    """Manages user operation execution."""

    def __init__(
        self, w3: Web3, accounts: AccountManager, contracts: ContractManager
    ) -> None:
        """Initialize the user operation manager.

        Args:
            w3: Web3 instance to use for operation execution
        """
        self.w3 = w3
        self.accounts = accounts
        self.contracts = contracts

    def execute_operation(self, target: str, value: int, data: str) -> TxReceipt:
        """Execute a user operation.

        Args:
            target: Target address for the operation
            value: Value to send with the operation (in Wei)
            data: Data to send with the operation

        Returns:
            Transaction receipt
        """
        # Build the user operation
        user_op, account_gas_limits_bytes, gas_fees_bytes = self._build_operation(
            target, value, data
        )

        # Sign the operation
        user_op["signature"] = self._sign_operation(
            user_op, account_gas_limits_bytes, gas_fees_bytes
        )

        # Pack the operation for handleOps
        packed_user_op = self._pack_operation(
            user_op,
            account_gas_limits_bytes,
            gas_fees_bytes,
            user_op["signature"],
        )

        # Execute the operation
        try:
            tx = self.contracts.entry_point.functions.handleOps(
                [packed_user_op],
                self.accounts.beneficiary.address,
            ).build_transaction(
                {
                    "from": self.accounts.bundler.address,
                    "nonce": self.w3.eth.get_transaction_count(
                        self.accounts.bundler.address
                    ),
                    "maxFeePerGas": self.w3.eth.gas_price,
                    "maxPriorityFeePerGas": self.w3.eth.gas_price,
                    "chainId": self.w3.eth.chain_id,
                    "gas": 2_000_000,
                }
            )
        except Exception as e:
            raise Exception(f"Error building transaction: {e}")

        # Sign the transaction
        try:
            signed_tx = self.w3.eth.account.sign_transaction(
                tx, private_key=self.accounts.bundler.key
            )
        except Exception as e:
            raise Exception(f"Error signing transaction: {e}")

        # Send the transaction
        try:
            txn_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        except Exception as e:
            raise Exception(f"Error sending transaction: {e}")

        # Wait for the transaction to be mined
        try:
            txn_receipt = self.w3.eth.wait_for_transaction_receipt(txn_hash)

            if txn_receipt["status"] == 0:
                raise Exception("Transaction reverted")
        except Exception as e:
            raise Exception(f"Error waiting for transaction receipt: {e}")

        print(f"\nThere were {len(txn_receipt['logs'])} logs emitted.\n")

        return txn_receipt

    def _build_operation(
        self, target: str, value: int, data: str
    ) -> Tuple[Dict, bytes, bytes]:
        """Build a user operation.

        Args:
            target: Target address for the operation
            value: Value to send with the operation (in Wei)
            data: Data to send with the operation

        Returns:
            Tuple of (user operation dict, gas limits bytes, gas fees bytes)
        """
        # Encode the execute call
        call_data = self.contracts.simple_account.encode_abi(
            "execute", args=[target, value, data]
        )

        # Get the nonce from EntryPoint
        nonce = self.contracts.entry_point.functions.getNonce(
            self.contracts.simple_account.address, 0
        ).call()

        # Build the operation
        user_op = {
            "sender": self.contracts.simple_account.address,
            "nonce": nonce,
            "initCode": "0x",
            "callData": call_data,
            "callGasLimit": 1_000_000,
            "verificationGasLimit": 1_000_000,
            "preVerificationGas": 1_000_000,
            "maxFeePerGas": self.w3.to_wei(2, "gwei"),
            "maxPriorityFeePerGas": self.w3.to_wei(1, "gwei"),
            "paymasterAndData": "0x",
            "signature": "0x",
        }

        # Pack gas limits and fees
        vgas = user_op["verificationGasLimit"]
        cgas = user_op["callGasLimit"]
        maxPr = user_op["maxPriorityFeePerGas"]
        maxF = user_op["maxFeePerGas"]

        account_gas_limits = (vgas << 128) | cgas
        account_gas_limits_bytes = account_gas_limits.to_bytes(32, "big")

        gas_fees = (maxPr << 128) | maxF
        gas_fees_bytes = gas_fees.to_bytes(32, "big")

        return user_op, account_gas_limits_bytes, gas_fees_bytes

    def _sign_operation(
        self, user_op: Dict, account_gas_limits_bytes: bytes, gas_fees_bytes: bytes
    ) -> bytes:
        """Sign a user operation.

        Args:
            user_op: User operation dictionary
            account_gas_limits_bytes: Packed gas limits
            gas_fees_bytes: Packed gas fees

        Returns:
            Operation signature
        """
        # Use the _pack_operation method to pack the user operation for signature hash computation
        packed_user_op_no_sig = self._pack_operation(
            user_op, account_gas_limits_bytes, gas_fees_bytes
        )

        # Get the operation hash
        user_op_hash = self.contracts.entry_point.functions.getUserOpHash(
            packed_user_op_no_sig
        ).call()

        # Sign the hash
        signed_message = self.w3.eth.account._sign_hash(
            user_op_hash, private_key=self.accounts.owner.key
        )

        return signed_message.signature

    def _pack_operation(
        self,
        user_op: Dict,
        account_gas_limits_bytes: bytes,
        gas_fees_bytes: bytes,
        signature: bytes = b"",
    ) -> Tuple:
        """Pack a user operation for handleOps.

        Args:
            user_op: User operation dictionary
            account_gas_limits_bytes: Packed gas limits
            gas_fees_bytes: Packed gas fees

        Returns:
            Packed operation tuple
        """
        return (
            user_op["sender"],
            user_op["nonce"],
            self.w3.to_bytes(hexstr=user_op["initCode"][2:]),
            self.w3.to_bytes(hexstr=user_op["callData"][2:]),
            account_gas_limits_bytes,
            user_op["preVerificationGas"],
            gas_fees_bytes,
            self.w3.to_bytes(hexstr=user_op["paymasterAndData"][2:]),
            signature,
        )
