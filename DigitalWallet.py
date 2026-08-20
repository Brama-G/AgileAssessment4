import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
import threading
import random


class Transaction:
    """Represents a single transaction in the wallet."""

    def __init__(self, transaction_id: str, transaction_type: str, amount: float,
                 from_account: str, to_account: str = None, timestamp: datetime = None):
        self.transaction_id = transaction_id
        self.transaction_type = transaction_type  # 'deposit', 'withdrawal', 'transfer'
        self.amount = amount
        self.from_account = from_account
        self.to_account = to_account
        self.timestamp = timestamp or datetime.now()
        self.status = 'pending'  # pending, completed, failed, flagged
        self.flag_reason = None

    def to_dict(self) -> Dict:
        return {
            'transaction_id': self.transaction_id,
            'transaction_type': self.transaction_type,
            'amount': self.amount,
            'from_account': self.from_account,
            'to_account': self.to_account,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'flag_reason': self.flag_reason
        }


class FraudDetectionEngine:
    """Fraud detection system for the digital wallet."""

    def __init__(self):
        self.transaction_history = defaultdict(list)  # account_id -> list of transactions
        self.failed_pin_attempts = defaultdict(int)  # account_id -> count
        self.last_pin_attempt_time = defaultdict(datetime)
        self.lock = threading.Lock()

        # Configuration
        self.TRANSACTION_WINDOW_SECONDS = 600  # 10 minutes
        self.MAX_TRANSACTIONS_IN_WINDOW = 5
        self.LARGE_TRANSACTION_THRESHOLD = 10000
        self.MAX_PIN_ATTEMPTS = 3
        self.PIN_LOCKOUT_MINUTES = 15
        self.UNUSUAL_AMOUNT_THRESHOLD = 50000

    def check_transaction(self, account_id: str, amount: float,
                          transaction_type: str = 'transfer') -> Tuple[bool, Optional[str]]:
        """
        Check if a transaction is suspicious.
        Returns: (is_suspicious, reason)
        """
        with self.lock:
            flags = []
            current_time = datetime.now()
            window_start = current_time - timedelta(seconds=self.TRANSACTION_WINDOW_SECONDS)

            # 1. Check for multiple transactions in time window
            # Clean old transactions and count recent ones
            self.transaction_history[account_id] = [
                t for t in self.transaction_history[account_id]
                if t.timestamp > window_start
            ]

            recent_transactions = len(self.transaction_history[account_id])
            if recent_transactions >= self.MAX_TRANSACTIONS_IN_WINDOW:
                flags.append(f"More than {self.MAX_TRANSACTIONS_IN_WINDOW} transactions in 10 minutes")

            # 2. Check for large transaction
            if amount > self.LARGE_TRANSACTION_THRESHOLD:
                flags.append(f"Large transaction: ${amount:,.2f}")

            # 3. Check for unusual transaction amount
            if amount > self.UNUSUAL_AMOUNT_THRESHOLD:
                flags.append(f"Unusual amount: ${amount:,.2f}")

            # 4. Check for failed PIN attempts
            if account_id in self.failed_pin_attempts:
                attempts = self.failed_pin_attempts[account_id]
                if attempts >= self.MAX_PIN_ATTEMPTS:
                    time_since_last = (current_time - self.last_pin_attempt_time[account_id]).seconds / 60
                    if time_since_last < self.PIN_LOCKOUT_MINUTES:
                        flags.append(f"Too many failed PIN attempts: {attempts}")

            # 5. Check for duplicate transactions (same amount and same recipient in quick succession)
            duplicate_amounts = [t for t in self.transaction_history[account_id]
                                 if t.amount == amount and
                                 t.transaction_type == transaction_type and
                                 abs((current_time - t.timestamp).seconds) < 60]

            # Count duplicates (including current transaction)
            duplicate_count = len(duplicate_amounts) + 1
            if duplicate_count >= 3:
                flags.append("Duplicate transaction amount detected")

            if flags:
                return True, "; ".join(flags)

            return False, None

    def record_transaction(self, transaction: Transaction):
        """Record a transaction for fraud detection."""
        with self.lock:
            if transaction.from_account:
                self.transaction_history[transaction.from_account].append(transaction)
            if transaction.to_account and transaction.to_account != transaction.from_account:
                self.transaction_history[transaction.to_account].append(transaction)

    def record_failed_pin(self, account_id: str):
        """Record a failed PIN attempt."""
        with self.lock:
            self.failed_pin_attempts[account_id] += 1
            self.last_pin_attempt_time[account_id] = datetime.now()

    def reset_pin_attempts(self, account_id: str):
        """Reset failed PIN attempts for an account."""
        with self.lock:
            self.failed_pin_attempts[account_id] = 0

    def is_account_locked(self, account_id: str) -> bool:
        """Check if an account is locked due to failed PIN attempts."""
        with self.lock:
            if account_id not in self.failed_pin_attempts:
                return False

            attempts = self.failed_pin_attempts[account_id]
            if attempts < self.MAX_PIN_ATTEMPTS:
                return False

            time_since_last = (datetime.now() - self.last_pin_attempt_time[account_id]).seconds / 60
            return time_since_last < self.PIN_LOCKOUT_MINUTES


class Account:
    """Represents a user account in the digital wallet."""

    def __init__(self, account_id: str, name: str, pin: str, initial_balance: float = 0):
        self.account_id = account_id
        self.name = name
        self.pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        self.balance = initial_balance
        self.created_at = datetime.now()
        self.is_active = True
        self.daily_transactions = []
        self.daily_limit = 50000  # Daily transaction limit

    def verify_pin(self, pin: str) -> bool:
        """Verify the account PIN."""
        return hashlib.sha256(pin.encode()).hexdigest() == self.pin_hash

    def get_daily_total(self) -> float:
        """Get total amount transacted today."""
        today = datetime.now().date()
        total = sum(t.amount for t in self.daily_transactions
                    if t.timestamp.date() == today and
                    t.transaction_type in ['withdrawal', 'transfer'])
        return total

    def can_transact(self, amount: float) -> Tuple[bool, str]:
        """Check if transaction is allowed based on daily limit."""
        daily_total = self.get_daily_total()
        if daily_total + amount > self.daily_limit:
            return False, f"Daily limit of ${self.daily_limit:,.2f} exceeded"
        if not self.is_active:
            return False, "Account is deactivated"
        return True, "OK"

    def to_dict(self) -> Dict:
        return {
            'account_id': self.account_id,
            'name': self.name,
            'balance': self.balance,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'daily_limit': self.daily_limit
        }


class DigitalWallet:
    """Main digital wallet system with fraud detection."""

    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self.transactions: List[Transaction] = []
        self.fraud_engine = FraudDetectionEngine()
        self.transaction_counter = 0
        self.lock = threading.Lock()

    def create_account(self, account_id: str, name: str, pin: str,
                       initial_balance: float = 0) -> Tuple[bool, str]:
        """Create a new account."""
        with self.lock:
            if account_id in self.accounts:
                return False, "Account already exists"
            if initial_balance < 0:
                return False, "Initial balance cannot be negative"

            account = Account(account_id, name, pin, initial_balance)
            self.accounts[account_id] = account

            # Record initial deposit as transaction
            if initial_balance > 0:
                self._record_transaction('deposit', account_id, initial_balance, None)

            return True, "Account created successfully"

    def authenticate(self, account_id: str, pin: str) -> Tuple[bool, str]:
        """Authenticate a user with PIN."""
        if account_id not in self.accounts:
            return False, "Account not found"

        account = self.accounts[account_id]

        # Check if account is locked
        if self.fraud_engine.is_account_locked(account_id):
            return False, "Account locked due to multiple failed PIN attempts"

        if account.verify_pin(pin):
            self.fraud_engine.reset_pin_attempts(account_id)
            return True, "Authentication successful"
        else:
            self.fraud_engine.record_failed_pin(account_id)
            remaining = self.fraud_engine.MAX_PIN_ATTEMPTS - self.fraud_engine.failed_pin_attempts[account_id]
            return False, f"Invalid PIN. {remaining} attempts remaining"

    def deposit(self, account_id: str, amount: float) -> Tuple[bool, str]:
        """Deposit money into an account."""
        with self.lock:
            if account_id not in self.accounts:
                return False, "Account not found"
            if amount <= 0:
                return False, "Deposit amount must be positive"

            account = self.accounts[account_id]
            if not account.is_active:
                return False, "Account is deactivated"

            # Check for suspicious deposit
            is_suspicious, reason = self.fraud_engine.check_transaction(
                account_id, amount, 'deposit'
            )

            # Process deposit
            account.balance += amount
            transaction = self._record_transaction('deposit', account_id, amount, None)

            if is_suspicious:
                transaction.status = 'flagged'
                transaction.flag_reason = reason
                return True, f"Deposit successful. Transaction flagged: {reason}"

            return True, "Deposit successful"

    def withdraw(self, account_id: str, pin: str, amount: float) -> Tuple[bool, str]:
        """Withdraw money from an account."""
        # First authenticate
        auth_result, auth_message = self.authenticate(account_id, pin)
        if not auth_result:
            return False, auth_message

        with self.lock:
            account = self.accounts[account_id]

            if amount <= 0:
                return False, "Withdrawal amount must be positive"

            # Check balance
            if account.balance < amount:
                return False, f"Insufficient balance. Available: ${account.balance:,.2f}"

            # Check daily limit
            allowed, message = account.can_transact(amount)
            if not allowed:
                return False, message

            # Check for suspicious withdrawal
            is_suspicious, reason = self.fraud_engine.check_transaction(
                account_id, amount, 'withdrawal'
            )

            # Process withdrawal
            account.balance -= amount
            transaction = self._record_transaction('withdrawal', account_id, amount, None)

            # Add to daily transactions
            account.daily_transactions.append(transaction)

            if is_suspicious:
                transaction.status = 'flagged'
                transaction.flag_reason = reason
                return True, f"Withdrawal successful. Transaction flagged: {reason}"

            return True, "Withdrawal successful"

    def transfer(self, from_account_id: str, pin: str, to_account_id: str,
                 amount: float) -> Tuple[bool, str]:
        """Transfer money between accounts."""
        # First authenticate
        auth_result, auth_message = self.authenticate(from_account_id, pin)
        if not auth_result:
            return False, auth_message

        with self.lock:
            if from_account_id not in self.accounts:
                return False, "Source account not found"
            if to_account_id not in self.accounts:
                return False, "Destination account not found"
            if from_account_id == to_account_id:
                return False, "Cannot transfer to same account"
            if amount <= 0:
                return False, "Transfer amount must be positive"

            from_account = self.accounts[from_account_id]
            to_account = self.accounts[to_account_id]

            # Check if both accounts are active
            if not from_account.is_active or not to_account.is_active:
                return False, "One or both accounts are deactivated"

            # Check balance
            if from_account.balance < amount:
                return False, f"Insufficient balance. Available: ${from_account.balance:,.2f}"

            # Check daily limit for sender
            allowed, message = from_account.can_transact(amount)
            if not allowed:
                return False, message

            # Check for suspicious transfer
            is_suspicious, reason = self.fraud_engine.check_transaction(
                from_account_id, amount, 'transfer'
            )

            # Process transfer
            from_account.balance -= amount
            to_account.balance += amount
            transaction = self._record_transaction('transfer', from_account_id, amount, to_account_id)

            # Add to daily transactions for sender
            from_account.daily_transactions.append(transaction)

            if is_suspicious:
                transaction.status = 'flagged'
                transaction.flag_reason = reason
                return True, f"Transfer successful. Transaction flagged: {reason}"

            return True, "Transfer successful"

    def _record_transaction(self, transaction_type: str, from_account: str,
                            amount: float, to_account: Optional[str]) -> Transaction:
        """Record a transaction."""
        self.transaction_counter += 1
        transaction_id = f"TXN{self.transaction_counter:010d}"

        transaction = Transaction(
            transaction_id, transaction_type, amount,
            from_account, to_account
        )
        transaction.status = 'completed'
        self.transactions.append(transaction)

        # Record in fraud detection engine
        self.fraud_engine.record_transaction(transaction)

        return transaction

    def get_transaction_history(self, account_id: str, limit: int = 50) -> List[Dict]:
        """Get transaction history for an account."""
        if account_id not in self.accounts:
            return []

        account_transactions = []
        for t in reversed(self.transactions):
            if t.from_account == account_id or t.to_account == account_id:
                account_transactions.append(t.to_dict())
                if len(account_transactions) >= limit:
                    break

        return account_transactions

    def get_flagged_transactions(self) -> List[Dict]:
        """Get all flagged/suspicious transactions."""
        return [t.to_dict() for t in self.transactions if t.status == 'flagged']

    def get_balance(self, account_id: str) -> Tuple[bool, float]:
        """Get balance for an account."""
        if account_id not in self.accounts:
            return False, 0

        return True, self.accounts[account_id].balance

    def verify_balance(self, account_id: str, expected_amount: float) -> bool:
        """Verify account balance matches expected amount."""
        success, balance = self.get_balance(account_id)
        if not success:
            return False
        return abs(balance - expected_amount) < 0.01

    def get_account_summary(self, account_id: str) -> Optional[Dict]:
        """Get comprehensive account summary."""
        if account_id not in self.accounts:
            return None

        account = self.accounts[account_id]
        daily_total = account.get_daily_total()

        return {
            'account_id': account.account_id,
            'name': account.name,
            'balance': account.balance,
            'daily_limit': account.daily_limit,
            'daily_transactions_total': daily_total,
            'daily_remaining': account.daily_limit - daily_total,
            'is_active': account.is_active,
            'is_locked': self.fraud_engine.is_account_locked(account_id)
        }


def main():
    """Demonstrate the digital wallet functionality."""
    wallet = DigitalWallet()

    print("=" * 80)
    print("DIGITAL WALLET DEMO")
    print("=" * 80)

    # 1. Create accounts
    print("\nCreating accounts...")
    wallet.create_account("ACC001", "Alice", "1234", 1000)
    wallet.create_account("ACC002", "Bob", "5678", 500)
    wallet.create_account("ACC003", "Charlie", "9012", 2000)
    print("Accounts created successfully")

    # 2. Display initial balances
    print("\nInitial Balances:")
    for acc_id in ["ACC001", "ACC002", "ACC003"]:
        success, balance = wallet.get_balance(acc_id)
        print(f"{acc_id}: ${balance:,.2f}")

    # 3. Perform transactions
    print("\n" + "=" * 80)
    print("PERFORMING TRANSACTIONS")
    print("=" * 80)

    # Normal deposit
    result, message = wallet.deposit("ACC001", 500)
    print(f"\nDeposit $500 to ACC001: {message}")

    # Normal transfer
    result, message = wallet.transfer("ACC001", "1234", "ACC002", 300)
    print(f"Transfer $300 from ACC001 to ACC002: {message}")

    # Withdrawal
    result, message = wallet.withdraw("ACC002", "5678", 100)
    print(f"Withdraw $100 from ACC002: {message}")

    # 4. Test fraud detection - multiple transactions
    print("\n" + "=" * 80)
    print("FRAUD DETECTION TESTS")
    print("=" * 80)

    # Multiple transactions in short time
    print("\nTesting multiple transactions in 10 minutes...")
    for i in range(6):
        result, message = wallet.transfer("ACC003", "9012", "ACC001", 10)
        print(f"Transfer {i + 1}: {message[:50]}...")
        time.sleep(0.1)  # Small delay

    # Large transaction
    print("\nTesting large transaction (> $10,000)...")
    wallet.deposit("ACC003", 50000)  # Top up
    result, message = wallet.transfer("ACC003", "9012", "ACC002", 15000)
    print(f"Large transfer: {message}")

    # Failed PIN attempts
    print("\nTesting failed PIN attempts...")
    for i in range(4):
        result, message = wallet.transfer("ACC001", "9999", "ACC002", 100)
        print(f"Attempt {i + 1}: {message}")
        time.sleep(0.1)

    # 5. Display flagged transactions
    print("\n" + "=" * 80)
    print("FLAGGED/SUSPICIOUS TRANSACTIONS")
    print("=" * 80)
    flagged = wallet.get_flagged_transactions()
    for t in flagged:
        print(f"\nTransaction: {t['transaction_id']}")
        print(f"  Type: {t['transaction_type']}")
        print(f"  Amount: ${t['amount']:,.2f}")
        print(f"  From: {t['from_account']}")
        print(f"  Status: {t['status']}")
        print(f"  Reason: {t['flag_reason']}")

    # 6. Display transaction history
    print("\n" + "=" * 80)
    print("TRANSACTION HISTORY (ACC001)")
    print("=" * 80)
    history = wallet.get_transaction_history("ACC001", 10)
    for t in history:
        print(f"{t['timestamp'][:19]} | {t['transaction_type']:10} | ${t['amount']:8,.2f} | {t['status']}")

    # 7. Account summary
    print("\n" + "=" * 80)
    print("ACCOUNT SUMMARY")
    print("=" * 80)
    for acc_id in ["ACC001", "ACC002", "ACC003"]:
        summary = wallet.get_account_summary(acc_id)
        if summary:
            print(f"\n{summary['name']} ({summary['account_id']})")
            print(f"  Balance: ${summary['balance']:,.2f}")
            print(f"  Daily Transactions: ${summary['daily_transactions_total']:,.2f}")
            print(f"  Daily Limit Remaining: ${summary['daily_remaining']:,.2f}")
            print(f"  Active: {summary['is_active']}")
            print(f"  Locked: {summary['is_locked']}")


if __name__ == "__main__":
    main()
