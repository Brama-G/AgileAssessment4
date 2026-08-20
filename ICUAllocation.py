class ICUAllocationSystem:
    def __init__(self, total_beds=3):
        self.total_beds = total_beds
        self.allocated_beds = {}  # {patient_id: patient_info}
        self.waiting_list = []  # list of patient_info dicts
        self.patient_ids = set()  # track duplicates

    def calculate_priority_score(self, oxygen_level, heart_rate, bp_sys, temp, age, conditions):
        score = 0

        # Vital score assessments
        if oxygen_level < 90:
            score += 40
        elif oxygen_level <= 94:
            score += 20

        if heart_rate < 50 or heart_rate > 120:
            score += 25
        elif heart_rate > 100:
            score += 10

        if bp_sys < 90 or bp_sys > 180:
            score += 20

        if temp > 39.0 or temp < 35.0:
            score += 15

        if age >= 65:
            score += 10

        if conditions:
            score += len(conditions) * 5

        return score

    def classify_patient(self, score, emergency=False):
        if emergency or score >= 60:
            return "CRITICAL"
        elif score >= 40:
            return "HIGH"
        elif score >= 20:
            return "MEDIUM"
        else:
            return "LOW"

    def validate_vitals(self, oxygen_level, heart_rate):
        if not (0 <= oxygen_level <= 100):
            raise ValueError(f"Invalid oxygen level: {oxygen_level}%. Must be 0-100.")
        if not (0 <= heart_rate <= 300):
            raise ValueError(f"Invalid heart rate: {heart_rate} bpm. Must be 0-300.")

    def add_patient(self, patient_id, age, oxygen_level, heart_rate, bp_sys, temp, conditions=None, emergency=False):
        if patient_id in self.patient_ids:
            raise ValueError(f"Duplicate Patient ID '{patient_id}' rejected.")

        self.validate_vitals(oxygen_level, heart_rate)

        if conditions is None:
            conditions = []

        score = self.calculate_priority_score(oxygen_level, heart_rate, bp_sys, temp, age, conditions)
        category = self.classify_patient(score, emergency)

        patient = {
            "patient_id": patient_id,
            "age": age,
            "score": score,
            "category": category,
            "emergency": emergency
        }

        self.patient_ids.add(patient_id)
        return self._process_allocation(patient)

    def _process_allocation(self, patient):
        # Allocation rule: Bed available -> Allocate directly
        if len(self.allocated_beds) < self.total_beds:
            self.allocated_beds[patient["patient_id"]] = patient
            return f"Allocated ICU Bed to {patient['patient_id']} ({patient['category']})"

        # Emergency override rule: Replace lowest priority non-critical patient if full
        if patient["emergency"] or patient["category"] == "CRITICAL":
            lowest_patient = min(self.allocated_beds.values(), key=lambda x: (x["emergency"], x["score"]))
            if not lowest_patient["emergency"] and patient["score"] > lowest_patient["score"]:
                # Bump lowest patient to waiting list
                del self.allocated_beds[lowest_patient["patient_id"]]
                self.waiting_list.append(lowest_patient)
                self.allocated_beds[patient["patient_id"]] = patient
                return f"Emergency/Critical Override: Allocated Bed to {patient['patient_id']}. Moved {lowest_patient['patient_id']} to Waiting List."

        # Otherwise add to waiting list sorted by priority score
        self.waiting_list.append(patient)
        self.waiting_list.sort(key=lambda x: (x["emergency"], x["score"]), reverse=True)
        return f"No Bed Available. Placed {patient['patient_id']} ({patient['category']}) on Waiting List."
