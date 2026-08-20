class CourseRegistrationSystem:
    def __init__(self):
        # Master list of courses:
        # {code: {"title": str, "credits": int, "prereq": str|None, "capacity": int, "enrolled": int, "schedule": set((day, slot)), "semester": int}}
        self.courses = {}
        # Registered students map:
        # {student_id: {"program": str, "semester": int, "credit_limit": int, "courses": set()}}
        self.students = {}

    def add_course(self, code, title, credits, prereq=None, capacity=30, schedule=None, semester=1):
        self.courses[code] = {
            "title": title,
            "credits": credits,
            "prereq": prereq,
            "capacity": capacity,
            "enrolled": 0,
            "schedule": set(schedule) if schedule else set(),
            "semester": semester
        }

    def register_student(self, student_id, program, semester, credit_limit=15):
        if student_id in self.students:
            raise ValueError(f"Student {student_id} is already registered in the system.")
        self.students[student_id] = {
            "program": program,
            "semester": semester,
            "credit_limit": credit_limit,
            "courses": set()
        }

    def register_course(self, student_id, course_code, completed_prereqs=None):
        if completed_prereqs is None:
            completed_prereqs = set()

        # 1. Check student existence
        if student_id not in self.students:
            raise ValueError(f"Invalid Student ID: '{student_id}'.")

        # 2. Check valid course
        if course_code not in self.courses:
            raise ValueError(f"Invalid course code: '{course_code}'.")

        student = self.students[student_id]
        course = self.courses[course_code]

        # 3. Check duplicate registration
        if course_code in student["courses"]:
            raise ValueError(f"Duplicate registration: '{course_code}' is already registered.")

        # 4. Check semester restriction
        if course["semester"] > student["semester"]:
            raise ValueError(
                f"Semester restriction: '{course_code}' requires Semester {course['semester']} (Student is in Semester {student['semester']}).")

        # 5. Verify prerequisites
        if course["prereq"] and course["prereq"] not in completed_prereqs:
            raise ValueError(f"Missing prerequisite: '{course['prereq']}' required for '{course_code}'.")

        # 6. Check credit limits
        current_credits = self.get_total_credits(student_id)
        if current_credits + course["credits"] > student["credit_limit"]:
            raise ValueError(
                f"Credit limit exceeded: Adding {course['credits']} credits exceeds total limit of {student['credit_limit']}.")

        # 7. Check course capacity
        if course["enrolled"] >= course["capacity"]:
            raise ValueError(f"Course full: '{course_code}' has reached maximum capacity.")

        # 8. Detect timetable clashes
        student_schedule = self.get_student_schedule(student_id)
        clashes = student_schedule.intersection(course["schedule"])
        if clashes:
            raise ValueError(f"Timetable conflict detected for course '{course_code}' at slot(s) {clashes}.")

        # Successful registration
        student["courses"].add(course_code)
        course["enrolled"] += 1
        return f"Successfully registered {student_id} for {course_code}."

    def get_total_credits(self, student_id):
        if student_id not in self.students:
            raise ValueError(f"Invalid Student ID: '{student_id}'.")
        return sum(self.courses[code]["credits"] for code in self.students[student_id]["courses"])

    def get_student_schedule(self, student_id):
        schedule = set()
        for code in self.students[student_id]["courses"]:
            schedule.update(self.courses[code]["schedule"])
        return schedule
