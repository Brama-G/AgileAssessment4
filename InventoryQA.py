import unittest
import threading
from InventoryManagement import InventoryManager


class TestInventoryManagement(unittest.TestCase):

    def setUp(self):
        self.im = InventoryManager()
        self.im.add_supplier("SUP1", "TechCorp")
        self.im.add_product("PROD1", "Laptop", "SUP1", reorder_threshold=10)

    # 1. Stock Availability Test
    def test_stock_availability(self):
        print("\n--- Running Test 1: Stock Availability ---")
        print("Input: Add 15 units of 'PROD1' to Warehouse A.")
        self.im.add_stock("Warehouse A", "PROD1", 15)

        is_low, total_stock = self.im.check_low_stock("PROD1")
        print(f"Output: Total Stock calculated = {total_stock} units. Low stock warning = {is_low}.")

        self.assertEqual(total_stock, 15)
        print("Result: [PASS]")

    # 2. Insufficient Inventory Test
    def test_insufficient_inventory(self):
        print("\n--- Running Test 2: Insufficient Inventory ---")
        print("Input: Add 5 units to Warehouse A, then attempt to remove 10 units.")
        self.im.add_stock("Warehouse A", "PROD1", 5)

        try:
            self.im.remove_stock("Warehouse A", "PROD1", 10)
        except ValueError as e:
            print(f"Output Caught Expected Error: '{e}'")

        with self.assertRaises(ValueError):
            self.im.remove_stock("Warehouse A", "PROD1", 10)
        print("Result: [PASS]")

    # 3. Warehouse Transfer Test
    def test_warehouse_transfer(self):
        print("\n--- Running Test 3: Warehouse Transfer ---")
        print("Input: Add 20 units to Warehouse A. Transfer 10 units to Warehouse B.")
        self.im.add_stock("Warehouse A", "PROD1", 20)
        self.im.transfer_stock("Warehouse A", "Warehouse B", "PROD1", 10)

        stock_a = self.im.inventory["Warehouse A"]["PROD1"]
        stock_b = self.im.inventory["Warehouse B"]["PROD1"]
        print(f"Output: Warehouse A Stock = {stock_a}, Warehouse B Stock = {stock_b}")

        self.assertEqual(stock_a, 10)
        self.assertEqual(stock_b, 10)
        print("Result: [PASS]")

    # 4. Concurrent Orders Test
    def test_concurrent_orders(self):
        print("\n--- Running Test 4: Concurrent Orders ---")
        print("Input: Stock 100 units in Warehouse A. Launch 5 parallel threads placing 10 orders each (50 total).")
        self.im.add_stock("Warehouse A", "PROD1", 100)

        def place_order():
            for _ in range(10):
                self.im.auto_fulfill_order("PROD1", 1)

        threads = [threading.Thread(target=place_order) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        remaining_stock = self.im.inventory["Warehouse A"]["PROD1"]
        print(f"Output: Expected 50 remaining units. Actual remaining = {remaining_stock}")

        self.assertEqual(remaining_stock, 50)
        print("Result: [PASS]")

    # 5. Reorder Threshold Test
    def test_reorder_threshold(self):
        print("\n--- Running Test 5: Reorder Threshold ---")
        print("Input: Add 8 units to Warehouse A (Threshold is 10). Check low stock, then reorder 20 units.")
        self.im.add_stock("Warehouse A", "PROD1", 8)

        is_low, current_stock = self.im.check_low_stock("PROD1")
        print(f"Output Step 1: Current Stock = {current_stock}, Low Stock Flag = {is_low}")

        msg = self.im.reorder_product("PROD1", 20, target_wh="Warehouse A")
        is_low_after, stock_after = self.im.check_low_stock("PROD1")
        print(f"Output Step 2: System Message -> '{msg}'")
        print(f"Output Step 3: Updated Stock = {stock_after}, Low Stock Flag = {is_low_after}")

        self.assertTrue(is_low)
        self.assertFalse(is_low_after)
        self.assertEqual(stock_after, 28)
        print("Result: [PASS]")

    # 6. Invalid Product Test
    def test_invalid_product(self):
        print("\n--- Running Test 6: Invalid Product ---")
        print("Input: Attempt to add 10 units to product 'INVALID_ID'.")

        try:
            self.im.add_stock("Warehouse A", "INVALID_ID", 10)
        except ValueError as e:
            print(f"Output Caught Expected Error: '{e}'")

        with self.assertRaises(ValueError):
            self.im.add_stock("Warehouse A", "INVALID_ID", 10)
        print("Result: [PASS]")

    # 7. Negative Inventory Test
    def test_negative_inventory(self):
        print("\n--- Running Test 7: Negative Inventory ---")
        print("Input: Attempt to add -5 units, then attempt to remove -5 units.")

        try:
            self.im.add_stock("Warehouse A", "PROD1", -5)
        except ValueError as e:
            print(f"Output Caught Expected Error (Add): '{e}'")

        try:
            self.im.remove_stock("Warehouse A", "PROD1", -5)
        except ValueError as e:
            print(f"Output Caught Expected Error (Remove): '{e}'")

        with self.assertRaises(ValueError):
            self.im.add_stock("Warehouse A", "PROD1", -5)
        with self.assertRaises(ValueError):
            self.im.remove_stock("Warehouse A", "PROD1", -5)
        print("Result: [PASS]")

    # 8. Multiple Warehouses & Auto-Selection Test
    def test_multiple_warehouses_and_selection(self):
        print("\n--- Running Test 8: Multiple Warehouses Auto-Selection ---")
        print("Input Setup: Warehouse A = 5 units, Warehouse B = 25 units, Warehouse C = 10 units.")
        print("Input Action: Auto-fulfill an order of 15 units.")
        self.im.add_stock("Warehouse A", "PROD1", 5)
        self.im.add_stock("Warehouse B", "PROD1", 25)
        self.im.add_stock("Warehouse C", "PROD1", 10)

        selected_wh = self.im.auto_fulfill_order("PROD1", 15)
        remaining_b = self.im.inventory["Warehouse B"]["PROD1"]
        print(f"Output: System selected '{selected_wh}'. Warehouse B remaining stock = {remaining_b}")

        self.assertEqual(selected_wh, "Warehouse B")
        self.assertEqual(remaining_b, 10)
        print("Result: [PASS]")


if __name__ == "__main__":
    unittest.main()
