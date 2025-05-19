from typing import Dict, cast

from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.types import RPCEndpoint

from eip_4337.constants import ACCOUNT_TYPES


class AccountManager:
    """Manages account setup and interaction."""

    owner: LocalAccount
    bundler: LocalAccount
    beneficiary: LocalAccount

    def __init__(self, w3: Web3) -> None:
        """Initialize the account manager.

        Args:
            w3: Web3 instance to use for account interaction
        """
        self.w3 = w3

    @staticmethod
    def initialize_default_account(
        w3: Web3,
    ) -> ChecksumAddress:
        # Set the default account
        w3.eth.default_account = w3.eth.accounts[0]
        return w3.eth.default_account

    @staticmethod
    def anvil_set_balance(w3: Web3, address: ChecksumAddress, amount: int) -> None:
        """Set the balance of an anvil account."""
        try:
            response = w3.provider.make_request(
                cast(RPCEndpoint, "anvil_setBalance"),
                [address, w3.to_hex(w3.to_wei(amount, "ether"))],
            )

            if "result" in response:
                return
            elif "error" in response:
                raise Exception(f"Request error: {response['error']}")
            else:
                raise Exception(f"Unexpected response: {response}")
        except Exception as e:
            raise Exception(
                f"Failed to set balance for account: {address}.\nError: {e}"
            )

    @staticmethod
    def sufficient_balance(w3: Web3, account: ChecksumAddress, amount: int) -> bool:
        """Check the default account for sufficient balance.

        Returns:
            True if the account has sufficient balance, False otherwise
        """
        if account and w3.eth.get_balance(account) >= w3.to_wei(amount, "ether"):
            return True
        return False

    def check_accounts_initialized(self) -> bool:
        """Check if the accounts are initialized.

        Returns:
            True if the accounts are initialized, False otherwise
        """
        owner = getattr(self, "owner", None)
        bundler = getattr(self, "bundler", None)
        beneficiary = getattr(self, "beneficiary", None)
        return owner is not None and bundler is not None and beneficiary is not None

    def initialize_accounts(self, amounts: Dict[str, int]) -> None:
        """Initialize the accounts."""

        for account_type in ACCOUNT_TYPES:
            # Create the account
            account = self.w3.eth.account.create()

            # Fund the account
            try:
                self.fund_account(account.address, amounts[account_type])
            except Exception as e:
                raise e

            # Update the account in the account manager
            setattr(self, account_type, account)

    def get_account_addresses(self) -> Dict[str, ChecksumAddress | None]:
        """Get the addresses of the accounts.

        Returns:
            Dictionary mapping account types to addresses
        """
        owner = getattr(self, "owner", None)
        bundler = getattr(self, "bundler", None)
        beneficiary = getattr(self, "beneficiary", None)
        return {
            "owner": owner.address if owner else None,
            "bundler": bundler.address if bundler else None,
            "beneficiary": beneficiary.address if beneficiary else None,
        }

    def get_account_by_address(self, address: ChecksumAddress) -> LocalAccount:
        """Get an account by address.

        Args:
            address: Address to get
        """
        for account_type in ACCOUNT_TYPES:
            account = self.get_account_by_type(account_type)
            if account and account.address == address:
                return account

        raise ValueError(f"Invalid account address: {address}")

    def get_account_by_type(self, account_type: str) -> LocalAccount | None:
        """Get an account by type.

        Args:
            account_type: Type of account to get
        """
        if account_type in ACCOUNT_TYPES:
            return getattr(self, account_type, None)
        else:
            raise ValueError(f"Invalid account type: {account_type}")

    def fund_account(self, to_addr: ChecksumAddress, amount_eth: int) -> None:
        """Fund an account with ETH.

        Args:
            to_addr: Address to send to
            amount_eth: Amount of ETH to send
        """
        try:
            txn_hash = self.w3.eth.send_transaction(
                {
                    "from": self.w3.eth.accounts[0],
                    "to": to_addr,
                    "value": self.w3.to_wei(amount_eth, "ether"),
                }
            )
            txn_receipt = self.w3.eth.wait_for_transaction_receipt(txn_hash)

            if txn_receipt["status"] != 1:
                raise Exception(f"Transaction failed (status: {txn_receipt['status']})")
        except Exception as e:
            raise Exception(
                f"Failed to fund account: {to_addr}. This is most likely due to the default account not having enough ETH.\nError: {e}"
            )

    def fund_accounts(self, amounts: Dict[str, int]) -> None:
        """Fund the accounts.

        Args:
            amounts: Dictionary mapping account types to amounts of ETH to fund
        """
        for account_type, amount in amounts.items():
            account = self.get_account_by_type(account_type)
            if account:
                try:
                    self.fund_account(account.address, amount)
                except Exception as e:
                    raise e
            else:
                print(f"Account {account_type} not found")
