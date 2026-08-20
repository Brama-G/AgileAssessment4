import unittest
from CourseRegistration import CourseRegistrationSystem


class TestCourseRegistration(unittest.TestCase):

    def setUp(self):
        self.sys = CourseRegistrationSystem()

        # Add course catalog according to specifications
        self.sys.add_course("DBMS", "Database Systems", credits=4, prereq="Programming", capacity=2,
                            schedule=[("Mon", "9AM")], semester=2)
        self.sys.add_course("AI", "Artificial Intelligence", credits=4, prereq="Data Structures", capacity=30,
                            schedule=[("Mon", "9AM")], semester=2)
        self.sys.add_course("ML", "Machine Learning", credits=3, prereq="Statistics", capacity=30,
                            schedule=[("Tue", "10AM")], semester=2)
        self.sys.add_course("Cloud", "Cloud Computing", credits=3, prereq="Networking", capacity=30,
                            schedule=[("Wed", "2PM")], semester=2)

    # 1. Valid Registration Test
    def test_valid_registration(self):
        print("\n--- Test 1: Valid Registration ---")
        print("Input: Register student 'S101' for DBMS with completed prerequisite 'Programming'.")
        self.sys.register_student("S101", "CS", semester=2, credit_limit=15)
        res = self.sys.register_course("S101", "DBMS", completed_prereqs={"Programming"})

        total_credits = self.sys.get_total_credits("S101")
        print(f"Output: System Message = '{res}'. Total Registered Credits = {total_credits}.")
        self.assertEqual(total_credits, 4)
        print("Result: [PASS]")

    # 2. Missing Prerequisite Test
    def test_missing_prerequisite(self):
        print("\n--- Test 2: Missing Prerequisite ---")
        print("Input: Register 'S102' for AI without prerequisite 'Data Structures'.")
        self.sys.register_student("S102", "CS", semester=2, credit_limit=15)

        try:
            self.sys.register_course("S102", "AI", completed_prereqs=set())
        except ValueError as e:
            print(f"Output Caught Error: '{e}'")

        with self.assertRaises(ValueError):
            self.sys.register_course("S102", "AI", completed_prereqs=set())
        print("Result: [PASS]")

    # 3. Credit-Limit Violation Test
    def test_credit_limit_violation(self):
        print("\n--- Test 3: Credit-Limit Violation ---")
        print("Input: Student 'S103' with credit limit 5 tries registering for DBMS (4) and ML (3) = 7 credits.")
        self.sys.register_student("S103", "CS", semester=2, credit_limit=5)
        self.sys.register_course("S103", "DBMS", completed_prereqs={"Programming"})

        try:
            self.sys.register_course("S103", "ML", completed_prereqs={"Statistics"})
        except ValueError as e:
            print(f"Output Caught Error: '{e}'")

        with self.assertRaises(ValueError):
            self.sys.register_course("S103", "ML", completed_prereqs={"Statistics"})
        print("Result: [PASS]")

    # 4. Timetable Conflict Test
    def test_timetable_conflict(self):
        print("\n--- Test 4: Timetable Conflict ---")
        print("Input: Register DBMS and AI (Both scheduled at Mon 9AM).")
        self.sys.register_student("S104", "CS", semester=2, credit_limit=15)
        self.sys.register_course("S104", "DBMS", completed_prereqs={"Programming"})

        try:
            self.sys.register_course("S104", "AI", completed_prereqs={"Data Structures"})
        except ValueError as e:
            print(f"Output Caught Error: '{e}'")

        with self.assertRaises(ValueError):
            self.sys.register_course("S104", "AI", completed_prereqs={"Data Structures"})
        print("Result: [PASS]")

    # 5. Full Course Test
    def test_full_course(self):
        print("\n--- Test 5: Full Course Capacity ---")
        print("Input: Fill DBMS (capacity 2) with 2 students, then attempt 3rd registration.")
        self.sys.register_student("S_A", "CS", semester=2)
        self.sys.register_student("S_B", "CS", semester=2)
        self.sys.register_student("S_C", "CS", semester=2)

        self.sys.register_course("S_A", "DBMS", {"Programming"})
        self.sys.register_course("S_B", "DBMS", {"Programming"})

        try:
            self.sys.register_course("S_C", "DBMS", {"Programming"})
        except ValueError as e:
            print(f"Output Caught Error: '{e}'")

        with self.assertRaises(ValueError):
            self.sys.register_course("S_C", "DBMS", {"Programming"})
        print("Result: [PASS]")

    # 6. Duplicate Registration Test
    def test_duplicate_registration(self):
        print("\n--- Test 6: Duplicate Registration ---")
        print("Input: Register 'S105' twice for the same course 'ML'.")
        self.sys.register_student("S105", "CS", semester=2, credit_limit=15)
        self.sys.register_course("S105", "ML", {"Statistics"})

        try:
            self.sys.register_course("S105", "ML", {"Statistics"})
        except ValueError as e:
            print(f"Output Caught Error: '{e}'")

        with self.assertRaises(ValueError):
            self.sys.register_course("S105", "ML", {"Statistics"})
        print("Result: [PASS]")

    # 7. Invalid Course Test
    def test_invalid_course(self):
        print("\n--- Test 7: Invalid Course ---")
        print("Input: Attempt to register for non-existent course code 'CYBER101'.")
        self.sys.register_student("S106", "CS", semester=2)

        try:
            self.sys.register_course("S106", "CYBER101")
        except ValueError as e:
            print(f"Output Caught Error: '{e}'")

        with self.assertRaises(ValueError):
            self.sys.register_course("S106", "CYBER101")
        print("Result: [PASS]")

    # 8. Semester Restriction Test
    def test_semester_restriction(self):
        print("\n--- Test 8: Semester Restriction ---")
        print("Input: Semester 1 student attempts to register for Semester 2 course 'DBMS'.")
        self.sys.register_student("S107", "CS", semester=1)

        try:
            self.sys.register_course("S107", "DBMS", {"Programming"})
        except ValueError as e:
            print(f"Output Caught Error: '{e}'")

        with self.assertRaises(ValueError):
            self.sys.register_course("S107", "DBMS", {"Programming"})
        print("Result: [PASS]")

    # 9. Boundary Credit Values Test
    def test_boundary_credit_values(self):
        print("\n--- Test 9: Boundary Credit Values ---")
        print("Input: Student limit = 7. Register DBMS (4 credits) + Cloud (3 credits) = Exactly 7 credits.")
        self.sys.register_student("S108", "CS", semester=2, credit_limit=7)

        self.sys.register_course("S108", "DBMS", {"Programming"})
        res = self.sys.register_course("S108", "Cloud", {"Networking"})
        total_credits = self.sys.get_total_credits("S108")

        print(f"Output: System Message = '{res}'. Total Registered Credits = {total_credits}/7.")
        self.assertEqual(total_credits, 7)
        print("Result: [PASS]")


if __name__ == "__main__":
    unittest.main()
