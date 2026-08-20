import unittest
from datetime import datetime, timedelta
from RideBooking import RideBooking


class TestRideBookingQA(unittest.TestCase):
    """QA Test Suite for Ride-Sharing Fare and Driver Allocation System"""

    def setUp(self):
        """Initialize system before each test"""
        self.system = RideBooking()
        self.test_customer = "CUST001"
        self.test_pickup = "Downtown"
        self.test_drop = "Airport"
        self.test_time = "2024-01-15T14:30:00"

    def test_1_normal_booking(self):
        """Test normal booking with standard conditions"""
        print("\n" + "=" * 60)
        print("TEST 1: Normal Booking")
        print("=" * 60)

        success, message, booking = self.system.calculate_fare(
            customer_id="CUST001",
            pickup="Downtown",
            drop="Airport",
            distance=10.0,
            passengers=2,
            vehicle_type="Sedan",
            booking_time="2024-01-15T14:30:00"
        )

        self.assertTrue(success)
        self.assertEqual(message, "Booking confirmed successfully")
        self.assertIsNotNone(booking)
        self.assertEqual(booking['vehicle_type'], 'Sedan')
        self.assertEqual(booking['distance'], 10.0)
        self.assertEqual(booking['passengers'], 2)
        self.assertGreater(booking['final_fare'], 0)

        # Verify fare components
        self.assertEqual(booking['base_fare'], 50.0)  # Sedan base fare
        self.assertEqual(booking['distance_fare'], 150.0)  # 10 * 15
        self.assertEqual(booking['peak_surcharge'], 0)  # Not peak hour
        self.assertEqual(booking['night_surcharge'], 0)  # Not night
        self.assertEqual(booking['passenger_surcharge'], 0)  # Passengers <= 2
        self.assertEqual(booking['discount_amount'], 0)  # No promo
        self.assertEqual(booking['final_fare'], 200.0)  # 50 + 150

        print(f"✓ Booking ID: {booking['booking_id']}")
        print(f"✓ Vehicle: {booking['vehicle_type']}")
        print(f"✓ Driver: {booking['driver_name']}")
        print(f"✓ Final Fare: ₹{booking['final_fare']}")
        print("✓ Test passed")

    def test_2_peak_hour_booking(self):
        """Test booking during peak hours (6-9 AM or 5-8 PM)"""
        print("\n" + "=" * 60)
        print("TEST 2: Peak-Hour Booking")
        print("=" * 60)

        # Morning peak hour
        success, message, booking = self.system.calculate_fare(
            customer_id="CUST002",
            pickup="Station",
            drop="Office",
            distance=8.0,
            passengers=1,
            vehicle_type="Bike",
            booking_time="2024-01-15T08:30:00"  # Peak hour
        )

        self.assertTrue(success)
        self.assertGreater(booking['peak_surcharge'], 0)

        # Verify peak surcharge calculation
        base_fare = self.system.BASE_FARES['Bike']  # 25
        distance_fare = 8 * self.system.DISTANCE_RATES['Bike']  # 8 * 8 = 64
        expected_surcharge = (base_fare + distance_fare) * 0.25  # 89 * 0.25 = 22.25
        self.assertAlmostEqual(booking['peak_surcharge'], expected_surcharge, places=2)

        print(f"✓ Peak Surcharge: ₹{booking['peak_surcharge']}")
        print(f"✓ Final Fare: ₹{booking['final_fare']}")
        print("✓ Test passed")

    def test_3_night_booking(self):
        """Test booking during night hours (10 PM - 6 AM)"""
        print("\n" + "=" * 60)
        print("TEST 3: Night Booking")
        print("=" * 60)

        success, message, booking = self.system.calculate_fare(
            customer_id="CUST003",
            pickup="Mall",
            drop="Home",
            distance=12.0,
            passengers=3,
            vehicle_type="SUV",
            booking_time="2024-01-15T23:30:00"  # Night hour
        )

        self.assertTrue(success)
        self.assertGreater(booking['night_surcharge'], 0)

        # Verify night surcharge calculation
        base_fare = self.system.BASE_FARES['SUV']  # 75
        distance_fare = 12 * self.system.DISTANCE_RATES['SUV']  # 12 * 20 = 240
        expected_surcharge = (base_fare + distance_fare) * 0.15  # 315 * 0.15 = 47.25
        self.assertAlmostEqual(booking['night_surcharge'], expected_surcharge, places=2)

        print(f"✓ Night Surcharge: ₹{booking['night_surcharge']}")
        print(f"✓ Passenger Surcharge: ₹{booking['passenger_surcharge']}")
        print(f"✓ Final Fare: ₹{booking['final_fare']}")
        print("✓ Test passed")

    def test_4_invalid_distance(self):
        """Test booking with invalid distance (zero or negative)"""
        print("\n" + "=" * 60)
        print("TEST 4: Invalid Distance")
        print("=" * 60)

        # Test zero distance
        success, message, booking = self.system.calculate_fare(
            customer_id="CUST004",
            pickup="Downtown",
            drop="Airport",
            distance=0,
            passengers=2,
            vehicle_type="Sedan",
            booking_time=self.test_time
        )

        self.assertFalse(success)
        self.assertIn("Distance", message)
        print(f"✓ Zero distance: {message}")

        # Test negative distance
        success, message, booking = self.system.calculate_fare(
            customer_id="CUST004",
            pickup="Downtown",
            drop="Airport",
            distance=-5.0,
            passengers=2,
            vehicle_type="Sedan",
            booking_time=self.test_time
        )

        self.assertFalse(success)
        self.assertIn("Distance", message)
        print(f"✓ Negative distance: {message}")

        # Test excessive distance
        success, message, booking = self.system.calculate_fare(
            customer_id="CUST004",
            pickup="Downtown",
            drop="Airport",
            distance=150.0,
            passengers=2,
            vehicle_type="Sedan",
            booking_time=self.test_time
        )

        self.assertFalse(success)
        self.assertIn("exceeds maximum", message.lower())
        print(f"✓ Excessive distance: {message}")
        print("✓ Test passed")

    def test_5_invalid_passenger_count(self):
        """Test booking with invalid passenger count"""
        print("\n" + "=" * 60)
        print("TEST 5: Invalid Passenger Count")
        print("=" * 60)

        # Test zero passengers
        success, message, booking = self.system.calculate_fare(
            customer_id="CUST005",
            pickup="Downtown",
            drop="Airport",
            distance=10.0,
            passengers=0,
            vehicle_type="Bike",
            booking_time=self.test_time
        )

        self.assertFalse(success)
        self.assertIn("passengers", message.lower())
        print(f"✓ Zero passengers: {message}")

        # Test negative passengers
        success, message, booking = self.system.calculate_fare(
            customer_id="CUST005",
            pickup="Downtown",
            drop="Airport",
            distance=10.0,
            passengers=-2,
            vehicle_type="Bike",
            booking_time=self.test_time
        )

        self.assertFalse(success)
        self.assertIn("passengers", message.lower())
        print(f"✓ Negative passengers: {message}")

        # Test exceeding capacity
        success, message, booking = self.system.calculate_fare(
            customer_id="CUST005",
            pickup="Downtown",
            drop="Airport",
            distance=10.0,
            passengers=5,
            vehicle_type="Bike",  # Bike capacity is 1
            booking_time=self.test_time
        )

        self.assertFalse(success)
        self.assertIn("capacity", message.lower())
        print(f"✓ Exceeding capacity: {message}")
        print("✓ Test passed")

    def test_6_unavailable_driver(self):
        """Test booking when no driver is available"""
        print("\n" + "=" * 60)
        print("TEST 6: Unavailable Driver")
        print("=" * 60)

        # Mark all Sedan drivers as unavailable
        for driver_id, driver in self.system.drivers.items():
            if driver['vehicle'] == 'Sedan':
                driver['available'] = False

        success, message, booking = self.system.calculate_fare(
            customer_id="CUST006",
            pickup="Downtown",
            drop="Airport",
            distance=10.0,
            passengers=2,
            vehicle_type="Sedan",
            booking_time=self.test_time
        )

        self.assertFalse(success)
        self.assertIn("No available driver", message)
        print(f"✓ Unavailable driver: {message}")
        print("✓ Test passed")

    def test_7_maximum_discount(self):
        """Test maximum promotional discount"""
        print("\n" + "=" * 60)
        print("TEST 7: Maximum Discount")
        print("=" * 60)

        # Test 10% discount
        success, message, booking = self.system.calculate_fare(
            customer_id="CUST007",
            pickup="Downtown",
            drop="Airport",
            distance=20.0,
            passengers=2,
            vehicle_type="Premium",
            booking_time=self.test_time,
            promo_code="WELCOME10"
        )

        self.assertTrue(success, f"Booking failed: {message}")
        self.assertEqual(booking['promo_code'], 'WELCOME10')
        self.assertGreater(booking['discount_amount'], 0)

        # Verify 10% discount
        subtotal = booking['subtotal']
        expected_discount = subtotal * 0.10
        self.assertAlmostEqual(booking['discount_amount'], expected_discount, places=2)
        print(f"✓ 10% Discount: ₹{booking['discount_amount']}")

        # Reset driver availability for next booking
        for driver_id, driver in self.system.drivers.items():
            if driver['vehicle'] == 'Premium':
                driver['available'] = True

        # Test 20% discount
        success, message, booking = self.system.calculate_fare(
            customer_id="CUST007",
            pickup="Downtown",
            drop="Airport",
            distance=20.0,
            passengers=2,
            vehicle_type="Premium",
            booking_time=self.test_time,
            promo_code="SAVE20"
        )

        self.assertTrue(success, f"Booking failed: {message}")
        expected_discount = booking['subtotal'] * 0.20
        self.assertAlmostEqual(booking['discount_amount'], expected_discount, places=2)
        print(f"✓ 20% Discount: ₹{booking['discount_amount']}")

        # Reset driver availability for next booking
        for driver_id, driver in self.system.drivers.items():
            if driver['vehicle'] == 'Premium':
                driver['available'] = True

        # Test flat 50 discount
        success, message, booking = self.system.calculate_fare(
            customer_id="CUST007",
            pickup="Downtown",
            drop="Airport",
            distance=20.0,
            passengers=2,
            vehicle_type="Premium",
            booking_time=self.test_time,
            promo_code="FLAT50"
        )

        self.assertTrue(success, f"Booking failed: {message}")
        self.assertEqual(booking['discount_amount'], 50.0)
        print(f"✓ Flat 50 Discount: ₹{booking['discount_amount']}")
        print("✓ Test passed")

    def test_8_multiple_vehicle_types(self):
        """Test booking with all vehicle types"""
        print("\n" + "=" * 60)
        print("TEST 8: Multiple Vehicle Types")
        print("=" * 60)

        vehicle_types = ['Bike', 'Sedan', 'SUV', 'Premium']
        expected_base_fares = [25.0, 50.0, 75.0, 100.0]

        # Reset all drivers before test
        for driver_id, driver in self.system.drivers.items():
            driver['available'] = True

        for idx, (vehicle_type, expected_base) in enumerate(zip(vehicle_types, expected_base_fares)):
            # Find an available driver of this type
            available = False
            for driver_id, driver in self.system.drivers.items():
                if driver['vehicle'] == vehicle_type and driver['available']:
                    available = True
                    break

            if not available:
                print(f"⚠ No available {vehicle_type} driver, skipping...")
                continue

            success, message, booking = self.system.calculate_fare(
                customer_id=f"CUST008{idx}",
                pickup="Downtown",
                drop="Airport",
                distance=5.0,
                passengers=1,
                vehicle_type=vehicle_type,
                booking_time=self.test_time
            )

            self.assertTrue(success, f"{vehicle_type} booking failed: {message}")
            self.assertEqual(booking['vehicle_type'], vehicle_type)
            self.assertEqual(booking['base_fare'], expected_base)

            # Verify distance fare
            distance_fare = 5 * self.system.DISTANCE_RATES[vehicle_type]
            self.assertEqual(booking['distance_fare'], distance_fare)

            print(f"✓ {vehicle_type}: Base ₹{booking['base_fare']}, "
                  f"Distance ₹{booking['distance_fare']}, "
                  f"Total ₹{booking['final_fare']}")

        print("✓ Test passed")

    def test_9_boundary_fare_values(self):
        """Test boundary fare values"""
        print("\n" + "=" * 60)
        print("TEST 9: Boundary Fare Values")
        print("=" * 60)

        # Test minimum distance (just above zero)
        success, message, booking = self.system.calculate_fare(
            customer_id="CUST009",
            pickup="Downtown",
            drop="Airport",
            distance=0.1,
            passengers=1,
            vehicle_type="Bike",
            booking_time=self.test_time
        )

        self.assertTrue(success)
        self.assertGreater(booking['final_fare'], 0)
        print(f"✓ Minimum distance (0.1 km): ₹{booking['final_fare']}")

        # Test maximum passengers
        success, message, booking = self.system.calculate_fare(
            customer_id="CUST009",
            pickup="Downtown",
            drop="Airport",
            distance=10.0,
            passengers=7,
            vehicle_type="SUV",
            booking_time=self.test_time
        )

        self.assertTrue(success)
        self.assertEqual(booking['passengers'], 7)
        print(f"✓ Maximum passengers (7): ₹{booking['final_fare']}")

        # Test maximum distance
        success, message, booking = self.system.calculate_fare(
            customer_id="CUST009",
            pickup="Downtown",
            drop="Airport",
            distance=99.9,
            passengers=1,
            vehicle_type="Sedan",
            booking_time=self.test_time
        )

        self.assertTrue(success)
        self.assertGreater(booking['final_fare'], 0)
        print(f"✓ Maximum distance (99.9 km): ₹{booking['final_fare']}")

        # Test peak hour + night hour overlap
        success, message, booking = self.system.calculate_fare(
            customer_id="CUST009",
            pickup="Downtown",
            drop="Airport",
            distance=10.0,
            passengers=2,
            vehicle_type="Sedan",
            booking_time="2024-01-15T23:30:00"  # Night
        )

        self.assertTrue(success)
        print(f"✓ Night booking: ₹{booking['final_fare']}")
        print("✓ Test passed")

    def test_10_driver_allocation_logic(self):
        """Test driver allocation logic"""
        print("\n" + "=" * 60)
        print("TEST 10: Driver Allocation Logic")
        print("=" * 60)

        # Reset driver availability
        for driver_id, driver in self.system.drivers.items():
            driver['available'] = True

        # Test driver selection
        success, message, booking = self.system.calculate_fare(
            customer_id="CUST010",
            pickup="Downtown",  # Should prefer drivers near Downtown
            drop="Airport",
            distance=10.0,
            passengers=2,
            vehicle_type="Sedan",
            booking_time=self.test_time
        )

        self.assertTrue(success, f"Booking failed: {message}")
        driver = booking['driver']

        # Driver should be available
        self.assertTrue(driver['available'] is False)  # Now marked unavailable
        print(f"✓ Allocated driver: {driver['name']}")
        print(f"✓ Vehicle: {driver['vehicle']}")
        print(f"✓ Rating: {driver['rating']}")
        print(f"✓ Location: {driver['location']}")

        # Test driver becomes unavailable after booking
        driver_name = driver['name']
        driver_status = self.system.get_driver_status(driver_name)
        self.assertEqual(len(driver_status), 1)
        self.assertFalse(driver_status[0]['available'])
        print(f"✓ Driver '{driver_name}' marked as unavailable")

        # Test multiple bookings - FIX: Use different vehicle types to ensure availability
        vehicle_types = ['Bike', 'Bike', 'SUV']  # Use different vehicle types
        for i in range(3):
            success, message, booking = self.system.calculate_fare(
                customer_id=f"CUST010_{i}",
                pickup="Mall",
                drop="Station",
                distance=8.0,
                passengers=1,
                vehicle_type=vehicle_types[i],
                booking_time=self.test_time
            )
            self.assertTrue(success, f"Booking {i + 1} failed: {message}")
            print(f"✓ Booking {i + 1}: {booking['driver_name']} ({booking['vehicle_type']})")

        print("✓ Test passed")

    def run_all_tests(self):
        """Run all tests with summary"""
        print("\n" + "=" * 60)
        print("RIDE-BOOKING SYSTEM - COMPLETE TEST SUITE")
        print("=" * 60)

        tests = [test for test in dir(self) if test.startswith('test_')]
        passed = 0
        failed = 0

        for test_name in tests:
            try:
                self.setUp()
                print(f"\n--- Running {test_name} ---")
                getattr(self, test_name)()
                passed += 1
            except Exception as e:
                print(f"\n❌ {test_name} FAILED: {str(e)}")
                failed += 1

        print("\n" + "=" * 60)
        print(f"TEST SUMMARY: {passed} passed, {failed} failed")
        print(f"Success Rate: {(passed / (passed + failed) * 100):.1f}%")
        print("=" * 60)


if __name__ == "__main__":
    # Run tests
    test_suite = TestRideBookingQA()
    test_suite.run_all_tests()
