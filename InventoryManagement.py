import threading


class InventoryManager:
    def __init__(self):
        # Lock to handle concurrent orders safely
        self.lock = threading.Lock()

        # Suppliers storage: {supplier_id: name}
        self.suppliers = {}

        # Warehouse list
        self.warehouses = ["Warehouse A", "Warehouse B", "Warehouse C"]

        # Products storage:
        # {product_id: {"name": str, "supplier_id": str, "reorder_threshold": int}}
        self.products = {}

        # Inventory storage:
        # {warehouse: {product_id: stock_quantity}}
        self.inventory = {wh: {} for wh in self.warehouses}

    # --- Supplier Management ---
    def add_supplier(self, supplier_id, name):
        self.suppliers[supplier_id] = name

    # --- Product & Stock Operations ---
    def add_product(self, product_id, name, supplier_id, reorder_threshold=10):
        if product_id in self.products:
            raise ValueError(f"Product {product_id} already exists.")
        if supplier_id not in self.suppliers:
            raise ValueError(f"Supplier {supplier_id} does not exist.")

        self.products[product_id] = {
            "name": name,
            "supplier_id": supplier_id,
            "reorder_threshold": reorder_threshold
        }
        for wh in self.warehouses:
            self.inventory[wh][product_id] = 0

    def add_stock(self, warehouse, product_id, quantity):
        if quantity <= 0:
            raise ValueError("Quantity to add must be positive.")
        self._validate_product_and_wh(product_id, warehouse)

        with self.lock:
            self.inventory[warehouse][product_id] += quantity

    def remove_stock(self, warehouse, product_id, quantity):
        if quantity <= 0:
            raise ValueError("Quantity to remove must be positive.")
        self._validate_product_and_wh(product_id, warehouse)

        with self.lock:
            if self.inventory[warehouse][product_id] < quantity:
                raise ValueError("Insufficient inventory in selected warehouse.")
            self.inventory[warehouse][product_id] -= quantity

    def transfer_stock(self, from_wh, to_wh, product_id, quantity):
        self._validate_product_and_wh(product_id, from_wh)
        self._validate_product_and_wh(product_id, to_wh)
        if quantity <= 0:
            raise ValueError("Quantity to transfer must be positive.")

        with self.lock:
            if self.inventory[from_wh][product_id] < quantity:
                raise ValueError(f"Insufficient stock in {from_wh} to transfer.")
            self.inventory[from_wh][product_id] -= quantity
            self.inventory[to_wh][product_id] += quantity

    # --- Automatic Warehouse Selection & Fulfill ---
    def auto_fulfill_order(self, product_id, quantity):
        if product_id not in self.products:
            raise ValueError(f"Invalid product ID: {product_id}")
        if quantity <= 0:
            raise ValueError("Order quantity must be positive.")

        with self.lock:
            # Automatic selection: pick warehouse with highest stock that can fulfill
            best_wh = None
            max_stock = -1

            for wh in self.warehouses:
                current_stock = self.inventory[wh].get(product_id, 0)
                if current_stock >= quantity and current_stock > max_stock:
                    max_stock = current_stock
                    best_wh = wh

            if not best_wh:
                raise ValueError(f"Insufficient total stock across warehouses to fulfill order of {quantity}.")

            self.inventory[best_wh][product_id] -= quantity
            return best_wh

    # --- Low-Stock Detection & Reorder ---
    def check_low_stock(self, product_id):
        if product_id not in self.products:
            raise ValueError(f"Invalid product ID: {product_id}")

        total_stock = sum(self.inventory[wh][product_id] for wh in self.warehouses)
        threshold = self.products[product_id]["reorder_threshold"]
        return total_stock <= threshold, total_stock

    def reorder_product(self, product_id, quantity, target_wh="Warehouse A"):
        is_low, current_stock = self.check_low_stock(product_id)
        supplier_id = self.products[product_id]["supplier_id"]
        supplier_name = self.suppliers[supplier_id]

        # Place reorder and restock
        self.add_stock(target_wh, product_id, quantity)
        return f"Ordered {quantity} units of {product_id} from {supplier_name}. Added to {target_wh}."

    def _validate_product_and_wh(self, product_id, warehouse):
        if product_id not in self.products:
            raise ValueError(f"Invalid product ID: {product_id}")
        if warehouse not in self.warehouses:
            raise ValueError(f"Invalid warehouse: {warehouse}")
