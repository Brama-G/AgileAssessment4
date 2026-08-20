import unittest
from ICUAllocation import ICUAllocationSystem


class TestICUAllocation(unittest.TestCase):

    def setUp(self):
        # Initialize system with 2 beds for deterministic testing
        self.icu = ICUAllocationSystem(total_beds=2)

    # 1. Critical Patient Test
    def test_critical_patient(self):
        print("\n--- Test 1: Critical Patient Classification ---")
        print("Input: O2=85%, HR=130bpm, BP=85 (Critical vitals)")
        res = self.icu.add_patient("P1", age=70, oxygen_level=85, heart_rate=130, bp_sys=85, temp=38.0)
        patient = self.icu.allocated_beds["P1"]
        print(f"Output: Category = {patient['category']}, Priority Score = {patient['score']}. System Msg = '{res}'")
        self.assertEqual(patient["category"], "CRITICAL")
        print("Result: [PASS]")

    # 2. Normal Patient Test
    def test_normal_patient(self):
        print("\n--- Test 2: Normal/Low Priority Patient ---")
        print("Input: O2=98%, HR=72bpm, BP=120, Temp=36.8 (Healthy vitals)")
        res = self.icu.add_patient("P2", age=30, oxygen_level=98, heart_rate=72, bp_sys=120, temp=36.8)
        patient = self.icu.allocated_beds["P2"]
        print(f"Output: Category = {patient['category']}, Priority Score = {patient['score']}. System Msg = '{res}'")
        self.assertEqual(patient["category"], "LOW")
        print("Result: [PASS]")

    # 3. Emergency Case Test
    def test_emergency_case(self):
        print("\n--- Test 3: Emergency Case Flag ---")
        print("Input: Normal vitals, but emergency flag set to True")
        res = self.icu.add_patient("P3", age=25, oxygen_level=99, heart_rate=70, bp_sys=115, temp=36.5, emergency=True)
        patient = self.icu.allocated_beds["P3"]
        print(f"Output: Category = {patient['category']}, Emergency = {patient['emergency']}. System Msg = '{res}'")
        self.assertEqual(patient["category"], "CRITICAL")
        print("Result: [PASS]")

    # 4. No ICU Beds Available Test
    def test_no_icu_beds(self):
        print("\n--- Test 4: No ICU Beds Available (Waiting List) ---")
        print("Input: Fill 2 beds with LOW/MEDIUM priority patients, then add a 3rd LOW priority patient.")
        self.icu.add_patient("P_Bed1", 30, 98, 70, 120, 36.5)
        self.icu.add_patient("P_Bed2", 30, 98, 70, 120, 36.5)
        res = self.icu.add_patient("P_Wait", 30, 98, 70, 120, 36.5)
        print(f"Output: Waiting List Length = {len(self.icu.waiting_list)}. System Msg = '{res}'")
        self.assertEqual(len(self.icu.waiting_list), 1)
        self.assertEqual(self.icu.waiting_list[0]["patient_id"], "P_Wait")
        print("Result: [PASS]")

    # 5. Duplicate Patient Test
    def test_duplicate_patient(self):
        print("\n--- Test 5: Duplicate Patient ID Rejection ---")
        print("Input: Add 'DUP_01', then attempt to add 'DUP_01' again.")
        self.icu.add_patient("DUP_01", 40, 98, 75, 120, 36.6)
        try:
            self.icu.add_patient("DUP_01", 40, 98, 75, 120, 36.6)
        except ValueError as e:
            print(f"Output Caught Error: '{e}'")
        with self.assertRaises(ValueError):
            self.icu.add_patient("DUP_01", 40, 98, 75, 120, 36.6)
        print("Result: [PASS]")

    # 6. Invalid Oxygen Level Test
    def test_invalid_oxygen(self):
        print("\n--- Test 6: Invalid Oxygen Level Validation ---")
        print("Input: oxygen_level = 150%")
        try:
            self.icu.add_patient("P_BadO2", 50, 150, 80, 120, 36.5)
        except ValueError as e:
            print(f"Output Caught Error: '{e}'")
        with self.assertRaises(ValueError):
            self.icu.add_patient("P_BadO2", 50, 150, 80, 120, 36.5)
        print("Result: [PASS]")

    # 7. Invalid Heart Rate Test
    def test_invalid_heart_rate(self):
        print("\n--- Test 7: Invalid Heart Rate Validation ---")
        print("Input: heart_rate = -10 bpm")
        try:
            self.icu.add_patient("P_BadHR", 50, 95, -10, 120, 36.5)
        except ValueError as e:
            print(f"Output Caught Error: '{e}'")
        with self.assertRaises(ValueError):
            self.icu.add_patient("P_BadHR", 50, 95, -10, 120, 36.5)
        print("Result: [PASS]")

    # 8. Priority Boundary Values Test
    def test_priority_boundary_values(self):
        print("\n--- Test 8: Priority Boundary Values ---")
        # Boundary tests for score thresholds: LOW (<20), MEDIUM (20-39), HIGH (40-59), CRITICAL (>=60)
        print("Input: Vitals calibrated near boundaries (Score = 20 & Score = 60)")
        p_med_cat = self.icu.classify_patient(20)
        p_crit_cat = self.icu.classify_patient(60)
        print(f"Output: Score 20 Classified as '{p_med_cat}', Score 60 Classified as '{p_crit_cat}'")
        self.assertEqual(p_med_cat, "MEDIUM")
        self.assertEqual(p_crit_cat, "CRITICAL")
        print("Result: [PASS]")

    # 9. Multiple Patients Competing for Bed Test
    def test_multiple_patients_competing(self):
        print("\n--- Test 9: Multiple Patients Competing for Bed (Override & Priority Queue) ---")
        print("Setup: Fill ICU with 2 MEDIUM priority patients.")
        self.icu.add_patient("P_Med1", age=30, oxygen_level=93, heart_rate=75, bp_sys=120, temp=36.5)  # score 20
        self.icu.add_patient("P_Med2", age=30, oxygen_level=93, heart_rate=75, bp_sys=120, temp=36.5)  # score 20

        print("Action: Add high priority CRITICAL patient 'P_Crit' when 0 beds are free.")
        res = self.icu.add_patient("P_Crit", age=75, oxygen_level=80, heart_rate=130, bp_sys=80, temp=39.5)  # score 95

        print(f"Output: {res}")
        print(f"Current Allocated Beds: {list(self.icu.allocated_beds.keys())}")
        print(f"Current Waiting List: {[p['patient_id'] for p in self.icu.waiting_list]}")

        self.assertIn("P_Crit", self.icu.allocated_beds)
        self.assertIn("P_Med1", [p["patient_id"] for p in self.icu.waiting_list])
        print("Result: [PASS]")


if __name__ == "__main__":
    unittest.main()
