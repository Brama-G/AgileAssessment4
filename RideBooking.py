from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
import json


class RideBooking:
    """Ride-Sharing Fare and Driver Allocation System"""

    # Vehicle configuration
    VEHICLE_TYPES = ['Bike', 'Sedan', 'SUV', 'Premium']

    # Base fares by vehicle type
    BASE_FARES = {
        'Bike': 25.0,
        'Sedan': 50.0,
        'SUV': 75.0,
        'Premium': 100.0
    }

    # Per km rates by vehicle type
    DISTANCE_RATES = {
        'Bike': 8.0,
        'Sedan': 15.0,
        'SUV': 20.0,
        'Premium': 30.0
    }

    # Passenger capacity by vehicle type
    PASSENGER_CAPACITY = {
        'Bike': 1,
        'Sedan': 4,
        'SUV': 7,
        'Premium': 4
    }

    # Surcharge percentages
    PEAK_HOUR_SURCHARGE = 1.25  # 25% extra
    NIGHT_SURCHARGE = 1.15  # 15% extra

    # Peak hours (6-9 AM, 5-8 PM)
    PEAK_HOURS = [
        (time(6, 0), time(9, 0)),
        (time(17, 0), time(20, 0))
    ]

    # Night hours (10 PM - 6 AM)
    NIGHT_HOURS = (time(22, 0), time(6, 0))

    # Promotional discounts - FIX: Added missing SAVE20
    PROMO_DISCOUNTS = {
        'WELCOME10': 0.10,  # 10% off
        'SAVE20': 0.20,  # 20% off
        'FLAT50': 50.0,  # Flat 50 off
        'DISCOUNT20': 0.20  # Alternative name for 20% off
    }

    def __init__(self):
        self.drivers = self._initialize_drivers()
        self.booking_counter = 0
        self.bookings = []

    def _initialize_drivers(self) -> Dict[str, Dict]:
        """Initialize driver database"""
        return {
            'D001': {
                'name': 'Raj Kumar',
                'vehicle': 'Sedan',
                'available': True,
                'rating': 4.8,
                'location': 'Downtown'
            },
            'D002': {
                'name': 'Priya Singh',
                'vehicle': 'Bike',
                'available': True,
                'rating': 4.9,
                'location': 'Airport'
            },
            'D003': {
                'name': 'Amit Sharma',
                'vehicle': 'SUV',
                'available': False,
                'rating': 4.7,
                'location': 'Mall'
            },
            'D004': {
                'name': 'Sneha Patel',
                'vehicle': 'Premium',
                'available': True,
                'rating': 4.9,
                'location': 'Station'
            },
            'D005': {
                'name': 'Vikram Reddy',
                'vehicle': 'Sedan',
                'available': True,
                'rating': 4.6,
                'location': 'Downtown'
            },
            'D006': {
                'name': 'Ananya Gupta',
                'vehicle': 'Bike',
                'available': True,
                'rating': 4.7,
                'location': 'Airport'
            },
            'D007': {
                'name': 'Rahul Verma',
                'vehicle': 'SUV',
                'available': True,
                'rating': 4.8,
                'location': 'Mall'
            },
            'D008': {
                'name': 'Meera Nair',
                'vehicle': 'Premium',
                'available': True,
                'rating': 4.9,
                'location': 'Downtown'
            }
        }

    def _is_peak_hour(self, booking_time: str) -> bool:
        """Check if booking time is during peak hours"""
        try:
            if isinstance(booking_time, str):
                t = datetime.fromisoformat(booking_time).time()
            else:
                t = booking_time

            for start, end in self.PEAK_HOURS:
                if start <= t <= end:
                    return True
            return False
        except:
            return False

    def _is_night_hour(self, booking_time: str) -> bool:
        """Check if booking time is during night hours"""
        try:
            if isinstance(booking_time, str):
                t = datetime.fromisoformat(booking_time).time()
            else:
                t = booking_time

            start, end = self.NIGHT_HOURS
            if start <= t or t <= end:
                return True
            return False
        except:
            return False

    def _validate_booking(self, customer_id: str, pickup: str, drop: str,
                          distance: float, passengers: int, vehicle_type: str,
                          booking_time: str) -> Tuple[bool, str]:
        """Validate booking parameters"""

        # Validate customer ID
        if not customer_id or len(customer_id) < 3:
            return False, "Invalid customer ID"

        # Validate pickup and drop locations
        if not pickup or not drop:
            return False, "Pickup and drop locations cannot be empty"
        if pickup.lower() == drop.lower():
            return False, "Pickup and drop locations cannot be same"

        # Validate distance
        if distance <= 0:
            return False, "Distance must be greater than zero"
        if distance > 100:
            return False, "Distance exceeds maximum limit (100 km)"

        # Validate passengers
        if passengers <= 0:
            return False, "Number of passengers must be greater than zero"

        max_passengers = self.PASSENGER_CAPACITY.get(vehicle_type, 0)
        if passengers > max_passengers:
            return False, f"Vehicle capacity exceeded. Maximum {max_passengers} passengers"

        # Validate vehicle type
        if vehicle_type not in self.VEHICLE_TYPES:
            return False, f"Invalid vehicle type. Choose from: {', '.join(self.VEHICLE_TYPES)}"

        # Validate booking time
        try:
            datetime.fromisoformat(booking_time)
        except:
            return False, "Invalid booking time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"

        return True, "Valid booking"

    def _find_available_driver(self, vehicle_type: str, pickup: str) -> Optional[Dict]:
        """Find an available driver for the given vehicle type"""
        available_drivers = []

        for driver_id, driver in self.drivers.items():
            if driver['available'] and driver['vehicle'] == vehicle_type:
                # Score drivers by rating and location proximity
                score = driver['rating'] * 10
                if driver['location'].lower() in pickup.lower():
                    score += 5
                available_drivers.append((driver_id, driver, score))

        if not available_drivers:
            return None

        # Sort by score (highest first)
        available_drivers.sort(key=lambda x: x[2], reverse=True)
        return available_drivers[0][1]

    def calculate_fare(self, customer_id: str, pickup: str, drop: str,
                       distance: float, passengers: int, vehicle_type: str,
                       booking_time: str, promo_code: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Calculate fare for a ride booking

        Returns: (success, message, fare_details)
        """

        # Validate booking
        is_valid, message = self._validate_booking(
            customer_id, pickup, drop, distance, passengers, vehicle_type, booking_time
        )
        if not is_valid:
            return False, message, None

        # Calculate base fare
        base_fare = self.BASE_FARES.get(vehicle_type, 0)

        # Calculate distance-based fare
        distance_fare = distance * self.DISTANCE_RATES.get(vehicle_type, 0)

        # Calculate surcharges
        peak_surcharge = 0
        if self._is_peak_hour(booking_time):
            peak_surcharge = (base_fare + distance_fare) * (self.PEAK_HOUR_SURCHARGE - 1)

        night_surcharge = 0
        if self._is_night_hour(booking_time):
            night_surcharge = (base_fare + distance_fare) * (self.NIGHT_SURCHARGE - 1)

        # Calculate passenger surcharge (extra for more passengers)
        passenger_surcharge = 0
        if passengers > 2:
            passenger_surcharge = (passengers - 2) * 10.0

        # Find available driver
        driver = self._find_available_driver(vehicle_type, pickup)
        if not driver:
            return False, "No available driver for the selected vehicle type", None

        # Calculate subtotal
        subtotal = base_fare + distance_fare + peak_surcharge + night_surcharge + passenger_surcharge

        # Apply promotional discount
        discount_amount = 0
        promo_name = None
        if promo_code and promo_code in self.PROMO_DISCOUNTS:
            promo_name = promo_code
            discount = self.PROMO_DISCOUNTS[promo_code]
            if promo_code == 'FLAT50':
                discount_amount = min(50.0, subtotal)
            else:
                discount_amount = subtotal * discount

        # Calculate final fare
        final_fare = subtotal - discount_amount
        final_fare = max(0, final_fare)  # Ensure fare is not negative

        # Generate booking ID
        self.booking_counter += 1
        booking_id = f"BK{self.booking_counter:04d}"

        # Create booking record
        booking = {
            'booking_id': booking_id,
            'customer_id': customer_id,
            'pickup': pickup,
            'drop': drop,
            'distance': distance,
            'passengers': passengers,
            'vehicle_type': vehicle_type,
            'booking_time': booking_time,
            'driver': driver,
            'driver_name': driver['name'],
            'base_fare': round(base_fare, 2),
            'distance_fare': round(distance_fare, 2),
            'peak_surcharge': round(peak_surcharge, 2),
            'night_surcharge': round(night_surcharge, 2),
            'passenger_surcharge': round(passenger_surcharge, 2),
            'promo_code': promo_name,
            'discount_amount': round(discount_amount, 2),
            'subtotal': round(subtotal, 2),
            'final_fare': round(final_fare, 2),
            'status': 'confirmed'
        }

        self.bookings.append(booking)

        # Mark driver as unavailable
        for driver_id, d in self.drivers.items():
            if d['name'] == driver['name']:
                d['available'] = False

        return True, "Booking confirmed successfully", booking

    def get_driver_status(self, driver_name: str = None) -> List[Dict]:
        """Get status of all drivers or a specific driver"""
        if driver_name:
            for driver_id, driver in self.drivers.items():
                if driver['name'] == driver_name:
                    return [driver]
            return []

        return list(self.drivers.values())

    def get_booking_history(self, customer_id: str = None) -> List[Dict]:
        """Get booking history for a customer or all bookings"""
        if customer_id:
            return [b for b in self.bookings if b['customer_id'] == customer_id]
        return self.bookings

    def calculate_average_fare(self, vehicle_type: str = None) -> float:
        """Calculate average fare for a vehicle type or all bookings"""
        relevant_bookings = self.bookings
        if vehicle_type:
            relevant_bookings = [b for b in self.bookings if b['vehicle_type'] == vehicle_type]

        if not relevant_bookings:
            return 0.0

        total_fare = sum(b['final_fare'] for b in relevant_bookings)
        return round(total_fare / len(relevant_bookings), 2)
