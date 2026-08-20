import unittest
import time
import threading
from datetime import datetime
from DigitalWallet import DigitalWallet, FraudDetectionEngine


class TestDigitalWallet(unittest.TestCase):
    """Comprehensive test suite for the Digital Wallet system."""

    def setUp(self):
        """Set up test environment before each test."""
        self.wallet = DigitalWallet()
        self.wallet.create_account("TEST001", "Test User", "1234", 10000)
        self.wallet.create_account("TEST002", "Test User2", "5678", 5000)
        self.wallet.create_account("TEST003", "Test User3", "9012", 5000)

    def test_1_normal_transaction(self):
        """Test normal transaction flow."""
        print("\n" + "=" * 80)
        print("TEST 1: Normal Transaction")
        print("=" * 80)

        # Deposit
        result, message = self.wallet.deposit("TEST001", 500)
        self.assertTrue(result)
        print(f"Deposit: {message}")

        # Transfer
        result, message = self.wallet.transfer("TEST001", "1234", "TEST002", 300)
        self.assertTrue(result)
        print(f"Transfer: {message}")

        # Verify balances
        success, balance = self.wallet.get_balance("TEST001")
        self.assertTrue(success)
        self.assertEqual(balance, 10200)  # 10000 + 500 - 300
        print(f"Balance TEST001: ${balance:,.2f}")

        success, balance = self.wallet.get_balance("TEST002")
        self.assertTrue(success)
        self.assertEqual(balance, 5300)  # 5000 + 300
        print(f"Balance TEST002: ${balance:,.2f}")

        print("✓ Normal transaction test passed")

    def test_2_insufficient_balance(self):
        """Test insufficient balance handling."""
        print("\n" + "=" * 80)
        print("TEST 2: Insufficient Balance")
        print("=" * 80)

        # Try to withdraw more than balance
        result, message = self.wallet.withdraw("TEST001", "1234", 15000)
        self.assertFalse(result)
        print(f"Withdraw attempt: {message}")
        self.assertIn("Insufficient balance", message)

        # Verify balance unchanged
        success, balance = self.wallet.get_balance("TEST001")
        self.assertTrue(success)
        self.assertEqual(balance, 10000)
        print(f"Balance unchanged: ${balance:,.2f}")

        print("✓ Insufficient balance test passed")

    def test_3_daily_limit(self):
        """Test daily transaction limit."""
        print("\n" + "=" * 80)
        print("TEST 3: Daily Transaction Limit")
        print("=" * 80)

        # Set a lower daily limit for testing
        self.wallet.accounts["TEST001"].daily_limit = 1000

        # Make transactions up to limit
        for i in range(3):
            result, message = self.wallet.transfer("TEST001", "1234", "TEST002", 300)
            print(f"Transfer {i + 1}: {message}")

        # Try to exceed limit
        result, message = self.wallet.transfer("TEST001", "1234", "TEST002", 200)
        self.assertFalse(result)
        print(f"Exceed limit attempt: {message}")
        self.assertIn("Daily limit", message)

        print("✓ Daily limit test passed")

    def test_4_multiple_failed_pins(self):
        """Test multiple failed PIN attempts and account lockout."""
        print("\n" + "=" * 80)
        print("TEST 4: Multiple Failed PIN Attempts")
        print("=" * 80)

        # Try with wrong PIN multiple times
        for i in range(3):
            result, message = self.wallet.transfer("TEST001", "9999", "TEST002", 100)
            print(f"Failed attempt {i + 1}: {message}")
            self.assertFalse(result)

        # Account should be locked
        result, message = self.wallet.transfer("TEST001", "1234", "TEST002", 100)
        self.assertFalse(result)
        print(f"After lockout: {message}")
        self.assertIn("locked", message)

        print("✓ Multiple failed PIN test passed")

    def test_5_suspicious_transaction(self):
        """Test suspicious transaction detection."""
        print("\n" + "=" * 80)
        print("TEST 5: Suspicious Transaction Detection")
        print("=" * 80)

        # Deposit enough money for large transaction
        result, message = self.wallet.deposit("TEST001", 100000)
        self.assertTrue(result)
        print(f"Deposit for large transaction: {message}")

        # Large transaction
        result, message = self.wallet.transfer("TEST001", "1234", "TEST002", 50000)
        self.assertTrue(result)
        print(f"Large transaction: {message}")
        self.assertIn("flagged", message)

        # Multiple transactions in short time - use TEST003 which has balance
        for i in range(6):
            result, message = self.wallet.transfer("TEST003", "9012", "TEST001", 10)
            print(f"Rapid transaction {i + 1}: {message}")
            self.assertTrue(result)
            time.sleep(0.05)

        # Check flagged transactions
        flagged = self.wallet.get_flagged_transactions()
        self.assertGreater(len(flagged), 0)
        print(f"Total flagged transactions: {len(flagged)}")

        print("✓ Suspicious transaction test passed")

    def test_6_duplicate_transaction(self):
        """Test duplicate transaction detection."""
        print("\n" + "=" * 80)
        print("TEST 6: Duplicate Transaction Detection")
        print("=" * 80)

        # Reset PIN attempts before this test
        self.wallet.fraud_engine.reset_pin_attempts("TEST001")

        # Create 3 identical transactions in quick succession
        for i in range(3):
            result, message = self.wallet.transfer("TEST001", "1234", "TEST002", 100)
            print(f"Duplicate transaction {i + 1}: {message}")
            self.assertTrue(result)
            time.sleep(0.05)

        # Check if flagged
        flagged = self.wallet.get_flagged_transactions()
        duplicate_flags = [t for t in flagged if t.get('flag_reason') and "Duplicate transaction" in t['flag_reason']]
        print(f"Duplicate transactions flagged: {len(duplicate_flags)}")
        self.assertGreater(len(duplicate_flags), 0)

        print("✓ Duplicate transaction test passed")

    def test_7_negative_amount(self):
        """Test handling of negative amounts."""
        print("\n" + "=" * 80)
        print("TEST 7: Negative Amount Handling")
        print("=" * 80)

        # Try deposit with negative amount
        result, message = self.wallet.deposit("TEST001", -100)
        self.assertFalse(result)
        print(f"Negative deposit: {message}")
        self.assertIn("positive", message.lower())

        # Try withdrawal with negative amount
        result, message = self.wallet.withdraw("TEST001", "1234", -50)
        self.assertFalse(result)
        print(f"Negative withdrawal: {message}")
        self.assertIn("positive", message.lower())

        # Try transfer with negative amount
        result, message = self.wallet.transfer("TEST001", "1234", "TEST002", -30)
        self.assertFalse(result)
        print(f"Negative transfer: {message}")
        self.assertIn("positive", message.lower())

        # Verify balances unchanged
        success, balance = self.wallet.get_balance("TEST001")
        self.assertEqual(balance, 10000)
        print(f"Balance unchanged: ${balance:,.2f}")

        print("✓ Negative amount test passed")

    def test_8_concurrent_transactions(self):
        """Test concurrent transactions and thread safety."""
        print("\n" + "=" * 80)
        print("TEST 8: Concurrent Transactions")
        print("=" * 80)

        # Reset PIN attempts
        self.wallet.fraud_engine.reset_pin_attempts("TEST001")

        def concurrent_transfer(amount):
            result, message = self.wallet.transfer("TEST001", "1234", "TEST002", amount)
            print(f"Concurrent transfer ${amount}: {message}")
            return result

        # Create threads for concurrent transactions
        threads = []
        amounts = [100, 200, 150, 50]

        for amount in amounts:
            thread = threading.Thread(target=concurrent_transfer, args=(amount,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify final balance
        success, final_balance = self.wallet.get_balance("TEST001")
        expected_balance = 10000 - sum(amounts)
        self.assertTrue(success)
        print(f"Final balance: ${final_balance:,.2f}")
        print(f"Expected balance: ${expected_balance:,.2f}")
        self.assertEqual(final_balance, expected_balance)

        print("✓ Concurrent transactions test passed")

    def test_9_balance_verification(self):
        """Test balance verification functionality."""
        print("\n" + "=" * 80)
        print("TEST 9: Balance Verification")
        print("=" * 80)

        # Reset PIN attempts
        self.wallet.fraud_engine.reset_pin_attempts("TEST001")

        # Perform some transactions
        self.wallet.deposit("TEST001", 500)
        self.wallet.transfer("TEST001", "1234", "TEST002", 200)

        # Verify exact balance
        verified = self.wallet.verify_balance("TEST001", 10300)  # 10000 + 500 - 200
        self.assertTrue(verified)
        print(f"Balance 10300 verified: {verified}")

        # Verify incorrect balance
        verified = self.wallet.verify_balance("TEST001", 10000)
        self.assertFalse(verified)
        print(f"Balance 10000 verified: {verified}")

        print("✓ Balance verification test passed")

    def test_10_fraud_detection_summary(self):
        """Comprehensive fraud detection summary test."""
        print("\n" + "=" * 80)
        print("TEST 10: Fraud Detection Summary")
        print("=" * 80)

        # Reset PIN attempts at start
        self.wallet.fraud_engine.reset_pin_attempts("TEST001")

        # First, deposit more money to TEST001 for large transactions
        self.wallet.deposit("TEST001", 100000)

        # Generate various transactions to test all fraud rules
        print("Generating test transactions...")

        # 1. Large transaction (> $10,000)
        print("\n1. Testing Large Transaction (> $10,000)...")
        result, msg = self.wallet.transfer("TEST001", "1234", "TEST002", 25000)
        print(f"   Result: {msg}")
        self.assertTrue(result, "Large transaction should succeed")

        # 2. Multiple transactions (will trigger rapid transaction rule)
        print("\n2. Testing Rapid Transactions (6 in 10 minutes)...")
        for i in range(6):
            result, msg = self.wallet.transfer("TEST003", "9012", "TEST001", 10)
            print(f"   Rapid {i + 1}: {msg}")
            self.assertTrue(result, f"Rapid transaction {i + 1} should succeed")
            time.sleep(0.05)

        # 3. Failed PIN attempts - use a separate account to avoid locking TEST001
        print("\n3. Testing Failed PIN Attempts...")
        for i in range(3):
            result, msg = self.wallet.transfer("TEST002", "9999", "TEST003", 100)
            print(f"   Failed PIN {i + 1}: {msg}")
            self.assertFalse(result, f"Failed PIN {i + 1} should fail")
            time.sleep(0.05)

        # Reset PIN attempts for TEST001 before duplicate transactions
        self.wallet.fraud_engine.reset_pin_attempts("TEST001")

        # 4. Duplicate transactions (3 identical in quick succession)
        print("\n4. Testing Duplicate Transactions...")
        for i in range(3):
            result, msg = self.wallet.transfer("TEST001", "1234", "TEST002", 77)
            print(f"   Duplicate {i + 1}: {msg}")
            self.assertTrue(result, f"Duplicate transaction {i + 1} should succeed")
            time.sleep(0.05)

        # Get all flagged transactions
        flagged = self.wallet.get_flagged_transactions()

        print(f"\n{'=' * 80}")
        print(f"Total flagged transactions: {len(flagged)}")
        print(f"{'=' * 80}")

        # Display all flagged transactions
        if flagged:
            for t in flagged:
                print(f"\nTransaction: {t['transaction_id']}")
                print(f"  Type: {t['transaction_type']}")
                print(f"  Amount: ${t['amount']:,.2f}")
                print(f"  From: {t['from_account']}")
                print(f"  To: {t['to_account']}")
                print(f"  Reason: {t['flag_reason']}")

        # Categorize flagged transactions
        categories = {
            'large': 0,
            'rapid': 0,
            'pin_attempts': 0,
            'duplicate': 0
        }

        for t in flagged:
            reason = t.get('flag_reason', '')
            if 'Large transaction' in reason:
                categories['large'] += 1
            if 'transactions in 10 minutes' in reason:
                categories['rapid'] += 1
            if 'failed PIN attempts' in reason:
                categories['pin_attempts'] += 1
            if 'Duplicate transaction' in reason:
                categories['duplicate'] += 1

        print("\nFlagged transaction breakdown:")
        for category, count in categories.items():
            print(f"  {category}: {count}")

        # Verify each fraud detection rule was triggered
        print("\n" + "=" * 80)
        print("VERIFYING FRAUD DETECTION RULES")
        print("=" * 80)

        # Check large transaction
        self.assertGreater(categories['large'], 0, "Large transaction should be flagged!")
        print("✓ Large transaction detection works")

        # Check rapid transactions
        self.assertGreater(categories['rapid'], 0, "Rapid transactions should be flagged!")
        print("✓ Rapid transaction detection works")

        # Check duplicate transactions
        self.assertGreater(categories['duplicate'], 0, "Duplicate transactions should be flagged!")
        print("✓ Duplicate transaction detection works")

        # Note: Failed PIN attempts don't create transactions, so they won't be in flagged transactions
        # But we verify they were recorded correctly
        pin_attempts = self.wallet.fraud_engine.failed_pin_attempts.get("TEST002", 0)
        print(f"✓ Failed PIN attempts recorded: {pin_attempts} attempts")
        self.assertGreaterEqual(pin_attempts, 3, "Failed PIN attempts should be tracked")

        print("\n" + "=" * 80)
        print("✓ All fraud detection rules triggered successfully!")
        print("✓ Fraud detection summary test passed")

    def run_all_tests(self):
        """Run all tests and generate summary."""
        print("\n" + "=" * 80)
        print("DIGITAL WALLET - COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        test_methods = [method for method in dir(self) if method.startswith('test_')]

        passed = 0
        failed = 0
        failures = []

        for test in test_methods:
            try:
                self.setUp()
                print(f"\n--- Running {test} ---")
                getattr(self, test)()
                passed += 1
                print(f"✓ {test} PASSED")
            except Exception as e:
                print(f"\n❌ {test} FAILED: {str(e)}")
                failed += 1
                failures.append((test, str(e)))

        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {passed + failed}")
        print(f"✓ Passed: {passed}")
        print(f"✗ Failed: {failed}")
        print(f"Success Rate: {(passed / (passed + failed) * 100):.1f}%")
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if failures:
            print("\nFailed Tests:")
            for test, error in failures:
                print(f"  - {test}: {error}")


if __name__ == "__main__":
    # Run all tests
    test_suite = TestDigitalWallet()
    test_suite.run_all_tests()
