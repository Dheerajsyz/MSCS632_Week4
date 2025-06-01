# Filename: test_scheduler.py

import unittest
import inspect
import random

try:
    import scheduler
except ImportError:
    scheduler = None


class TestSchedulingLogic(unittest.TestCase):
    """
    Tests the core scheduling logic to ensure that:
      1. No employee works more than one shift per day.
      2. No employee works more than five days per week.
      3. Each shift (morning, afternoon, evening) has at least two employees every day.
      4. If fewer than two employees prefer a shift, additional employees are randomly assigned.
    """

    def setUp(self):
        # Example raw preferences for a small group of employees.
        self.raw_preferences = {
            "Alice": {
                "Monday":    "morning",
                "Tuesday":   "morning",
                "Wednesday": "afternoon",
                "Thursday":  "evening",
                "Friday":    "morning",
                "Saturday":  "afternoon",
                "Sunday":    "evening",
            },
            "Bob": {
                "Monday":    "morning",
                "Tuesday":   "afternoon",
                "Wednesday": "morning",
                "Thursday":  "afternoon",
                "Friday":    "evening",
                "Saturday":  "morning",
                "Sunday":    "afternoon",
            },
            "Carol": {
                "Monday":    "afternoon",
                "Tuesday":   "evening",
                "Wednesday": "morning",
                "Thursday":  "morning",
                "Friday":    "afternoon",
                "Saturday":  "evening",
                "Sunday":    "morning",
            },
            "Dave": {
                "Monday":    "evening",
                "Tuesday":   "morning",
                "Wednesday": "evening",
                "Thursday":  "afternoon",
                "Friday":    "morning",
                "Saturday":  "afternoon",
                "Sunday":    "evening",
            },
        }

        if scheduler and hasattr(scheduler, "collect_employee_preferences"):
            self.preferences = scheduler.collect_employee_preferences(self.raw_preferences)
        else:
            self.preferences = self.raw_preferences

    def test_minimum_two_per_shift(self):
        """
        Verifies that after schedule generation, each shift (morning, afternoon, evening)
        on each day has at least two employees assigned.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences)
        for day, shifts in final_schedule.items():
            for shift_name, assigned_employees in shifts.items():
                self.assertGreaterEqual(
                    len(assigned_employees),
                    2,
                    f"Shift '{shift_name}' on '{day}' has fewer than 2 employees assigned."
                )

    def test_no_employee_more_than_one_shift_per_day(self):
        """
        Verifies that no employee appears in more than one shift in a single day.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences)
        for day, shifts in final_schedule.items():
            seen_this_day = set()
            for assigned in shifts.values():
                for emp in assigned:
                    self.assertNotIn(
                        emp,
                        seen_this_day,
                        f"Employee '{emp}' is assigned to more than one shift on {day}."
                    )
                    seen_this_day.add(emp)

    def test_employee_max_five_days_per_week(self):
        """
        Verifies that no employee works more than five distinct days in the final schedule.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences)
        work_days_count = {}
        for day, shifts in final_schedule.items():
            for shift_name, assigned_employees in shifts.items():
                for emp in assigned_employees:
                    work_days_count[emp] = work_days_count.get(emp, set())
                    work_days_count[emp].add(day)

        for emp, days_worked in work_days_count.items():
            self.assertLessEqual(
                len(days_worked),
                5,
                f"Employee '{emp}' is scheduled for {len(days_worked)} days, exceeding the 5-day limit."
            )


class TestConflictResolution(unittest.TestCase):
    """
    Tests scenarios where an employee’s preferred shift is full and must be reassigned.
    Also verifies that conflicts do not lead to any shift falling below two employees,
    provided other employees are available.
    """

    def setUp(self):
        # Build a conflict scenario: eight employees all prefer Monday morning.
        self.raw_preferences_conflict = {
            "Alice":  {"Monday": "morning"},
            "Bob":    {"Monday": "morning"},
            "Carol":  {"Monday": "morning"},
            "Dave":   {"Monday": "morning"},
            "Eve":    {"Monday": "morning"},
            "Frank":  {"Monday": "morning"},
            "Grace":  {"Monday": "morning"},
            "Hank":   {"Monday": "morning"},
        }
        all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for name, prefs in self.raw_preferences_conflict.items():
            for day in all_days:
                prefs.setdefault(day, None)

        if scheduler and hasattr(scheduler, "collect_employee_preferences"):
            self.preferences_conflict = scheduler.collect_employee_preferences(self.raw_preferences_conflict)
        else:
            self.preferences_conflict = self.raw_preferences_conflict

    def test_conflict_reassignment(self):
        """
        When more than two employees prefer the same shift on a given day,
        at least two remain, and the rest get reassigned to other shifts on the same day
        or next day, ensuring no shift falls below the minimum.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences_conflict)
        monday_shifts = final_schedule.get("Monday", {})
        mon_morning_count = len(monday_shifts.get("morning", []))
        self.assertEqual(
            mon_morning_count,
            2,
            "Exactly two employees should remain on Monday morning when eight prefer it."
        )

        for shift_name, employees in monday_shifts.items():
            self.assertGreaterEqual(
                len(employees),
                2,
                f"After conflict resolution, Monday {shift_name} must have at least two employees."
            )

        monday_assigned = set(
            monday_shifts.get("morning", []) +
            monday_shifts.get("afternoon", []) +
            monday_shifts.get("evening", [])
        )
        tuesday_assigned = set(
            final_schedule.get("Tuesday", {}).get("morning", []) +
            final_schedule.get("Tuesday", {}).get("afternoon", []) +
            final_schedule.get("Tuesday", {}).get("evening", [])
        )

        all_preferring = set(self.raw_preferences_conflict.keys())
        assigned_either_day = monday_assigned.union(tuesday_assigned)

        self.assertSetEqual(
            all_preferring,
            assigned_either_day,
            "After conflict resolution, all employees must appear on Monday or Tuesday."
        )


class TestOutputFormat(unittest.TestCase):
    """
    Verifies that the final schedule output is organized as a dictionary of days,
    each containing 'morning', 'afternoon', and 'evening', with lists of names.
    """

    def setUp(self):
        self.raw_preferences_minimal = {
            "Alice":  {day: "morning" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Bob":    {day: "afternoon" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Carol":  {day: "evening" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Dave":   {day: None      for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Eve":    {day: None      for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
        }
        if scheduler and hasattr(scheduler, "collect_employee_preferences"):
            self.preferences_minimal = scheduler.collect_employee_preferences(self.raw_preferences_minimal)
        else:
            self.preferences_minimal = self.raw_preferences_minimal

    def test_structure_of_schedule(self):
        """
        Ensures that generate_schedule returns a dict with exactly seven day keys,
        each mapping to a dict with 'morning', 'afternoon', and 'evening'.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences_minimal)
        expected_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.assertCountEqual(
            final_schedule.keys(),
            expected_days,
            "Schedule must contain exactly the keys for each day of the week."
        )

        for day in expected_days:
            self.assertIsInstance(
                final_schedule[day],
                dict,
                f"Value for '{day}' must be a dictionary of shifts."
            )
            shift_keys = list(final_schedule[day].keys())
            self.assertCountEqual(
                shift_keys,
                ["morning", "afternoon", "evening"],
                f"Each day must have exactly 'morning', 'afternoon', and 'evening' keys."
            )

    def test_readable_output_content(self):
        """
        Checks that each list under a shift is a list of strings (employee names).
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences_minimal)
        for day, shifts in final_schedule.items():
            for shift_name, emp_list in shifts.items():
                self.assertIsInstance(
                    emp_list,
                    list,
                    f"Shift '{shift_name}' on '{day}' should map to a list of names."
                )
                for emp in emp_list:
                    self.assertIsInstance(
                        emp,
                        str,
                        f"Each assigned employee under '{shift_name}' on '{day}' must be a string."
                    )


class TestCodeQuality(unittest.TestCase):
    """
    Basic checks for code quality:
      - Each function in scheduler.py must have a non-empty docstring.
      - No function should exceed 50 lines of code, as a readability proxy.
    """

    def setUp(self):
        if scheduler is None:
            self.skipTest("scheduler module not found")

    def test_all_functions_have_docstrings(self):
        functions_in_scheduler = inspect.getmembers(scheduler, inspect.isfunction)
        own_functions = [
            func for name, func in functions_in_scheduler
            if func.__module__ == scheduler.__name__
        ]
        missing_doc = []
        for func in own_functions:
            doc = inspect.getdoc(func)
            if not doc or doc.strip() == "":
                missing_doc.append(func.__name__)
        self.assertListEqual(
            missing_doc,
            [],
            f"The following functions lack docstrings: {missing_doc}"
        )

    def test_function_length_under_50_lines(self):
        """
        Ensures that no single function exceeds 50 lines of code.
        """
        functions_in_scheduler = inspect.getmembers(scheduler, inspect.isfunction)
        own_functions = [
            (name, func) for name, func in functions_in_scheduler
            if func.__module__ == scheduler.__name__
        ]
        too_long = []
        for name, func in own_functions:
            source_lines = inspect.getsource(func).splitlines()
            if len(source_lines) > 50:
                too_long.append((name, len(source_lines)))
        self.assertEqual(
            len(too_long),
            0,
            f"Functions exceeding 50 lines: {too_long}"
        )


class TestMinimumStaffingExactMatch(unittest.TestCase):
    """
    Tests a scenario where exactly two employees prefer each shift for every day.
    Ensures that no extra random assignments are introduced.
    """

    def setUp(self):
        names = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace"]
        self.raw_preferences = {}
        for name in names:
            day_prefs = {}
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                if name in ["Alice", "Bob"]:
                    day_prefs[day] = "morning"
                elif name in ["Carol", "Dave"]:
                    day_prefs[day] = "afternoon"
                elif name in ["Eve", "Frank"]:
                    day_prefs[day] = "evening"
                else:
                    day_prefs[day] = None
            self.raw_preferences[name] = day_prefs

        if scheduler and hasattr(scheduler, "collect_employee_preferences"):
            self.preferences = scheduler.collect_employee_preferences(self.raw_preferences)
        else:
            self.preferences = self.raw_preferences

    def test_exact_two_per_shift_every_day(self):
        """
        Verifies that for each day, each shift has exactly two employees,
        and the employee with no preference is never assigned.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences)
        for day, shifts in final_schedule.items():
            for shift_name, assigned in shifts.items():
                self.assertEqual(
                    len(assigned),
                    2,
                    f"On {day} {shift_name}, expected exactly 2 employees but found {len(assigned)}."
                )
            all_assigned = (
                final_schedule[day]["morning"]
                + final_schedule[day]["afternoon"]
                + final_schedule[day]["evening"]
            )
            self.assertNotIn(
                "Grace",
                all_assigned,
                f"Grace should not be assigned on {day} because each shift already has two."
            )


class TestUnderstaffedSituation(unittest.TestCase):
    """
    Tests a scenario where only three employees exist. The scheduler cannot
    place two employees in every shift. It should still assign two to at least
    one shift and then place the third in another shift.
    """

    def setUp(self):
        self.raw_preferences = {
            "Alice":  {day: None for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Bob":    {day: None for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Carol":  {day: None for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
        }
        if scheduler and hasattr(scheduler, "collect_employee_preferences"):
            self.preferences = scheduler.collect_employee_preferences(self.raw_preferences)
        else:
            self.preferences = self.raw_preferences

    def test_three_employees_fill_shifts(self):
        """
        Verifies that, on each day, at least one shift has two employees
        and no shift is staffed with more employees than exist.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences)
        for day, shifts in final_schedule.items():
            total_positions = sum(len(lst) for lst in shifts.values())
            self.assertLessEqual(
                total_positions,
                3,
                f"On {day}, expected at most 3 assignments but found {total_positions}."
            )
            staffing_counts = [len(shifts[s]) for s in ["morning", "afternoon", "evening"]]
            self.assertTrue(
                any(c >= 2 for c in staffing_counts),
                f"On {day}, expected at least one shift to have 2 employees but got {staffing_counts}."
            )


class TestEmployeeWithNoPreferences(unittest.TestCase):
    """
    Ensures that an employee who lists None for every day is assigned only when needed,
    and does not exceed five days per week.
    """

    def setUp(self):
        self.raw_preferences = {
            "Alice":  {"Monday": "morning", "Tuesday": "morning", "Wednesday": "morning", "Thursday": None, "Friday": None, "Saturday": None, "Sunday": None},
            "Bob":    {"Monday": "afternoon", "Tuesday": "afternoon", "Wednesday": "afternoon", "Thursday": None, "Friday": None, "Saturday": None, "Sunday": None},
            "Carol":  {"Monday": "evening", "Tuesday": "evening", "Wednesday": "evening", "Thursday": None, "Friday": None, "Saturday": None, "Sunday": None},
            "Dave":   {day: None for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
        }
        if scheduler and hasattr(scheduler, "collect_employee_preferences"):
            self.preferences = scheduler.collect_employee_preferences(self.raw_preferences)
        else:
            self.preferences = self.raw_preferences

    def test_none_preference_fills_shifts(self):
        """
        Verifies that Dave (no preferences) is used only to fill understaffed shifts
        and does not exceed five assigned days.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences)
        work_days_count = {emp: 0 for emp in self.raw_preferences}
        for day, shifts in final_schedule.items():
            for shift_list in shifts.values():
                for emp in shift_list:
                    work_days_count[emp] += 1

        self.assertLessEqual(
            work_days_count["Dave"],
            5,
            f"Dave was assigned {work_days_count['Dave']} days but must not exceed 5."
        )
        # On Monday, Alice/Bob/Carol each fill one shift, so Dave must fill a second slot somewhere
        monday_total = sum(len(final_schedule["Monday"][s]) for s in ["morning", "afternoon", "evening"])
        self.assertGreaterEqual(
            monday_total,
            4,
            f"On Monday, expected at least 4 assignments (two per shift) but found {monday_total}."
        )


class TestEmployeeExceedsWeeklyLimit(unittest.TestCase):
    """
    Tests that if a single employee prefers every day, they are scheduled exactly five days.
    """

    def setUp(self):
        self.raw_preferences = {
            "Zack":  {day: "morning" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Alice": {day: "afternoon" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Bob":   {day: "evening" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Carol": {day: "afternoon" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Dave":  {day: "evening" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
        }
        if scheduler and hasattr(scheduler, "collect_employee_preferences"):
            self.preferences = scheduler.collect_employee_preferences(self.raw_preferences)
        else:
            self.preferences = self.raw_preferences

    def test_weekly_limit_for_zack(self):
        """
        Ensures that Zack is assigned to exactly five days, not more.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences)
        zack_days = sum(("Zack" in final_schedule[day]["morning"]) for day in final_schedule)
        self.assertEqual(
            zack_days,
            5,
            f"Zack appears {zack_days} times but should appear exactly 5 times."
        )


class TestConflictResolutionMultipleDays(unittest.TestCase):
    """
    Tests conflict resolution that carries overflow from Monday and Tuesday to Wednesday.
    """

    def setUp(self):
        names = ["A", "B", "C", "D", "E", "F"]
        self.raw_preferences = {}
        for name in names:
            day_prefs = {}
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                if day in ["Monday", "Tuesday"]:
                    day_prefs[day] = "morning"
                else:
                    day_prefs[day] = None
            self.raw_preferences[name] = day_prefs

        if scheduler and hasattr(scheduler, "collect_employee_preferences"):
            self.preferences = scheduler.collect_employee_preferences(self.raw_preferences)
        else:
            self.preferences = self.raw_preferences

    def test_conflict_carries_to_wednesday(self):
        """
        Verifies that after filling Monday and Tuesday morning with two each,
        the remaining are placed on Wednesday morning.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences)
        mon = set(final_schedule["Monday"]["morning"])
        tue = set(final_schedule["Tuesday"]["morning"])
        wed = set(final_schedule["Wednesday"]["morning"])

        self.assertEqual(len(mon), 2, f"Monday morning should have 2 but has {len(mon)}")
        self.assertEqual(len(tue), 2, f"Tuesday morning should have 2 but has {len(tue)}")
        self.assertEqual(len(wed), 2, f"Wednesday morning should have 2 but has {len(wed)}")

        all_assigned = mon.union(tue).union(wed)
        self.assertSetEqual(all_assigned, set(["A", "B", "C", "D", "E", "F"]),
                            "All six must appear on Monday, Tuesday, or Wednesday mornings.")


class TestMinimumStaffingExactMatch(unittest.TestCase):
    """
    Tests a scenario where exactly two employees prefer each shift for every day.
    Ensures that the remaining employee with no preference is never assigned.
    """

    def setUp(self):
        names = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace"]
        self.raw_preferences = {}
        for name in names:
            day_prefs = {}
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                if name in ["Alice", "Bob"]:
                    day_prefs[day] = "morning"
                elif name in ["Carol", "Dave"]:
                    day_prefs[day] = "afternoon"
                elif name in ["Eve", "Frank"]:
                    day_prefs[day] = "evening"
                else:
                    day_prefs[day] = None
            self.raw_preferences[name] = day_prefs

        if scheduler and hasattr(scheduler, "collect_employee_preferences"):
            self.preferences = scheduler.collect_employee_preferences(self.raw_preferences)
        else:
            self.preferences = self.raw_preferences

    def test_exact_two_per_shift_every_day(self):
        """
        Verifies that exactly two employees appear in each shift every day,
        and the extra employee is never scheduled.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences)
        for day, shifts in final_schedule.items():
            for shift_name, assigned in shifts.items():
                self.assertEqual(
                    len(assigned),
                    2,
                    f"On {day} {shift_name}, expected 2 employees but found {len(assigned)}."
                )
            combined = (
                final_schedule[day]["morning"]
                + final_schedule[day]["afternoon"]
                + final_schedule[day]["evening"]
            )
            self.assertNotIn(
                "Grace",
                combined,
                f"Grace should not be scheduled on {day} because each shift is exactly filled."
            )


class TestUnderstaffedSituation(unittest.TestCase):
    """
    Tests a scenario with only three employees, verifying that each day
    still has at least one shift staffed by two employees, and the third
    is assigned to another shift. 
    """

    def setUp(self):
        self.raw_preferences = {
            "Alice":  {day: None for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Bob":    {day: None for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Carol":  {day: None for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
        }
        if scheduler and hasattr(scheduler, "collect_employee_preferences"):
            self.preferences = scheduler.collect_employee_preferences(self.raw_preferences)
        else:
            self.preferences = self.raw_preferences

    def test_three_employees_fill_shifts(self):
        """
        Verifies that with only three employees, each day has at least two employees
        on one shift and there are no more assignments than employees available.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences)
        for day, shifts in final_schedule.items():
            total_assigned_positions = sum(len(lst) for lst in shifts.values())
            self.assertLessEqual(
                total_assigned_positions,
                3,
                f"On {day}, expected at most 3 assignments but found {total_assigned_positions}."
            )
            staffing_counts = [len(shifts[s]) for s in ["morning", "afternoon", "evening"]]
            self.assertTrue(
                any(count >= 2 for count in staffing_counts),
                f"On {day}, expected at least one shift with 2 employees but found {staffing_counts}."
            )


class TestEmployeeExceedsWeeklyLimit(unittest.TestCase):
    """
    Tests that an employee who prefers every day is scheduled exactly five times.
    """

    def setUp(self):
        self.raw_preferences = {
            "Zack":  {day: "morning" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Alice": {day: "afternoon" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Bob":   {day: "evening" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Carol": {day: "afternoon" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Dave":  {day: "evening" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
        }
        if scheduler and hasattr(scheduler, "collect_employee_preferences"):
            self.preferences = scheduler.collect_employee_preferences(self.raw_preferences)
        else:
            self.preferences = self.raw_preferences

    def test_weekly_limit_for_zack(self):
        """
        Verifies that Zack is scheduled exactly five times, not seven.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences)
        zack_count = sum("Zack" in final_schedule[day]["morning"] for day in final_schedule)
        self.assertEqual(
            zack_count,
            5,
            f"Zack appears {zack_count} times but should appear exactly 5 times."
        )


class TestConflictResolutionMultipleDays(unittest.TestCase):
    """
    Tests a scenario where Monday and Tuesday are both oversubscribed for morning.
    The overflow must be pushed to Wednesday morning.
    """

    def setUp(self):
        names = ["A", "B", "C", "D", "E", "F"]
        self.raw_preferences = {}
        for name in names:
            day_prefs = {}
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                if day in ["Monday", "Tuesday"]:
                    day_prefs[day] = "morning"
                else:
                    day_prefs[day] = None
            self.raw_preferences[name] = day_prefs

        if scheduler and hasattr(scheduler, "collect_employee_preferences"):
            self.preferences = scheduler.collect_employee_preferences(self.raw_preferences)
        else:
            self.preferences = self.raw_preferences

    def test_conflict_carries_to_wednesday(self):
        """
        Verifies that after Monday and Tuesday fill morning with two each,
        the remaining two appear on Wednesday morning.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences)
        mon_morn = set(final_schedule["Monday"]["morning"])
        tue_morn = set(final_schedule["Tuesday"]["morning"])
        wed_morn = set(final_schedule["Wednesday"]["morning"])

        self.assertEqual(len(mon_morn), 2, f"Monday morning should have 2 but has {len(mon_morn)}")
        self.assertEqual(len(tue_morn), 2, f"Tuesday morning should have 2 but has {len(tue_morn)}")
        self.assertEqual(len(wed_morn), 2, f"Wednesday morning should have 2 but has {len(wed_morn)}")

        combined = mon_morn.union(tue_morn).union(wed_morn)
        self.assertSetEqual(combined, set(names), "All six must appear on Mon, Tue, or Wed mornings.")


class TestOutputFormatAdditional(unittest.TestCase):
    """
    Verifies that no day is missing shift keys and that no shift list is None.
    """

    def setUp(self):
        self.raw_preferences = {
            "Alice":  {day: "morning" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Bob":    {day: "morning" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Carol":  {day: "morning" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Dave":   {day: None      for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Eve":    {day: None      for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            "Frank":  {day: None      for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
        }
        if scheduler and hasattr(scheduler, "collect_employee_preferences"):
            self.preferences = scheduler.collect_employee_preferences(self.raw_preferences)
        else:
            self.preferences = self.raw_preferences

    def test_no_missing_shift_keys(self):
        """
        Ensures that each day has all three shifts, even if no one prefers them.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences)
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            self.assertIn(
                "morning",
                final_schedule[day],
                f"{day} is missing 'morning' shift."
            )
            self.assertIn(
                "afternoon",
                final_schedule[day],
                f"{day} is missing 'afternoon' shift."
            )
            self.assertIn(
                "evening",
                final_schedule[day],
                f"{day} is missing 'evening' shift."
            )

    def test_no_shift_list_is_none(self):
        """
        Ensures that no shift list is None. Each must be a list.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        final_schedule = scheduler.generate_schedule(self.preferences)
        for day, shifts in final_schedule.items():
            for shift_name, emp_list in shifts.items():
                self.assertIsNotNone(
                    emp_list,
                    f"Shift list for {shift_name} on {day} is None instead of a list."
                )
                self.assertIsInstance(
                    emp_list,
                    list,
                    f"Shift list for {shift_name} on {day} is not a list."
                )


class TestCodeQualityExtended(unittest.TestCase):
    """
    Extends code quality checks by ensuring all functions have docstrings
    and that no function exceeds 50 lines of code.
    """

    def setUp(self):
        if scheduler is None:
            self.skipTest("scheduler module not found")

    def test_all_functions_have_docstrings(self):
        functions_in_scheduler = inspect.getmembers(scheduler, inspect.isfunction)
        own_functions = [
            func for name, func in functions_in_scheduler
            if func.__module__ == scheduler.__name__
        ]
        missing_doc = []
        for func in own_functions:
            doc = inspect.getdoc(func)
            if not doc or doc.strip() == "":
                missing_doc.append(func.__name__)
        self.assertListEqual(
            missing_doc,
            [],
            f"The following functions lack docstrings: {missing_doc}"
        )

    def test_function_length_under_50_lines(self):
        functions_in_scheduler = inspect.getmembers(scheduler, inspect.isfunction)
        own_functions = [
            (name, func) for name, func in functions_in_scheduler
            if func.__module__ == scheduler.__name__
        ]
        too_long = []
        for name, func in own_functions:
            source_lines = inspect.getsource(func).splitlines()
            if len(source_lines) > 50:
                too_long.append((name, len(source_lines)))
        self.assertEqual(
            len(too_long),
            0,
            f"Functions exceeding 50 lines: {too_long}"
        )


class TestBonusPriorityRankingTies(unittest.TestCase):
    """
    Verifies tie-breaking behavior when multiple employees share the same first preference.
    """

    def setUp(self):
        self.raw_preferences = {
            "Alice": {
                "Monday":   {"morning": 1, "afternoon": 2, "evening": 3},
                "Tuesday":  {"morning": 1, "afternoon": 2, "evening": 3},
                "Wednesday": {"morning": 1, "afternoon": 2, "evening": 3},
                "Thursday":  {"morning": 1, "afternoon": 2, "evening": 3},
                "Friday":    {"morning": 1, "afternoon": 2, "evening": 3},
                "Saturday":  {"morning": 1, "afternoon": 2, "evening": 3},
                "Sunday":    {"morning": 1, "afternoon": 2, "evening": 3},
            },
            "Bob": {
                "Monday":   {"morning": 1, "afternoon": 2, "evening": 3},
                "Tuesday":  {"morning": 1, "afternoon": 2, "evening": 3},
                "Wednesday": {"morning": 1, "afternoon": 2, "evening": 3},
                "Thursday":  {"morning": 1, "afternoon": 2, "evening": 3},
                "Friday":    {"morning": 1, "afternoon": 2, "evening": 3},
                "Saturday":  {"morning": 1, "afternoon": 2, "evening": 3},
                "Sunday":    {"morning": 1, "afternoon": 2, "evening": 3},
            },
            "Carol": {
                "Monday":   {"morning": 1, "afternoon": 2, "evening": 3},
                "Tuesday":  {"morning": 1, "afternoon": 2, "evening": 3},
                "Wednesday": {"morning": 1, "afternoon": 2, "evening": 3},
                "Thursday":  {"morning": 1, "afternoon": 2, "evening": 3},
                "Friday":    {"morning": 1, "afternoon": 2, "evening": 3},
                "Saturday":  {"morning": 1, "afternoon": 2, "evening": 3},
                "Sunday":    {"morning": 1, "afternoon": 2, "evening": 3},
            },
            "Dave": {
                "Monday":   {"afternoon": 1, "morning": 2, "evening": 3},
                "Tuesday":  {"afternoon": 1, "morning": 2, "evening": 3},
                "Wednesday": {"afternoon": 1, "morning": 2, "evening": 3},
                "Thursday":  {"afternoon": 1, "morning": 2, "evening": 3},
                "Friday":    {"afternoon": 1, "morning": 2, "evening": 3},
                "Saturday":  {"afternoon": 1, "morning": 2, "evening": 3},
                "Sunday":    {"afternoon": 1, "morning": 2, "evening": 3},
            },
        }
        if scheduler and hasattr(scheduler, "collect_employee_preferences"):
            self.preferences = scheduler.collect_employee_preferences(self.raw_preferences)
        else:
            self.preferences = self.raw_preferences

    def test_tie_breaking_for_first_preference(self):
        """
        Ensures that exactly two of Alice, Bob, and Carol appear on Monday morning,
        and that Dave occupies Monday afternoon by preference.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        random.seed(0)
        final_schedule = scheduler.generate_schedule(self.preferences)
        mon_morning = final_schedule["Monday"]["morning"]
        mon_afternoon = final_schedule["Monday"]["afternoon"]

        count_morning_preferrers = len([x for x in mon_morning if x in ["Alice", "Bob", "Carol"]])
        self.assertEqual(
            count_morning_preferrers,
            2,
            f"Exactly two of Alice, Bob, Carol should be on Monday morning but found {mon_morning}."
        )
        self.assertIn(
            "Dave",
            mon_afternoon,
            f"Dave should appear in Monday afternoon but afternoon is {mon_afternoon}."
        )
        excluded = set(["Alice", "Bob", "Carol"]) - set(mon_morning)
        self.assertEqual(
            len(excluded),
            1,
            f"Exactly one of Alice/Bob/Carol should be excluded from Monday morning; excluded: {excluded}"
        )


class TestInvalidInputs(unittest.TestCase):
    """
    Tests for invalid or malformed input scenarios, ensuring that scheduler
    raises ValueError or TypeError (adjust if you use a different exception).
    """

    def test_generate_schedule_with_non_dict_input(self):
        """
        Passing None or a list instead of a dictionary should raise an error.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        with self.assertRaises((TypeError, ValueError)):
            scheduler.generate_schedule(None)

        with self.assertRaises((TypeError, ValueError)):
            scheduler.generate_schedule(["Alice", "Bob"])

    def test_collect_preferences_with_non_dict(self):
        """
        If collect_employee_preferences exists, it should raise an error
        when given something other than a dict.
        """
        if scheduler is None or not hasattr(scheduler, "collect_employee_preferences"):
            self.skipTest("collect_employee_preferences not implemented or scheduler module missing")

        with self.assertRaises((TypeError, ValueError)):
            scheduler.collect_employee_preferences(None)

        with self.assertRaises((TypeError, ValueError)):
            scheduler.collect_employee_preferences(["Alice", "Monday", "morning"])

    def test_invalid_shift_string(self):
        """
        If a shift name is not 'morning', 'afternoon', or 'evening',
        generate_schedule should raise a ValueError.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        raw_prefs = {
            "Alice": {"Monday": "night", "Tuesday": None, "Wednesday": None, "Thursday": None, "Friday": None, "Saturday": None, "Sunday": None},
            "Bob":   {"Monday": "morning", "Tuesday": None, "Wednesday": None, "Thursday": None, "Friday": None, "Saturday": None, "Sunday": None},
        }

        if hasattr(scheduler, "collect_employee_preferences"):
            with self.assertRaises(ValueError):
                scheduler.collect_employee_preferences(raw_prefs)
        else:
            with self.assertRaises(ValueError):
                scheduler.generate_schedule(raw_prefs)

    def test_invalid_day_key(self):
        """
        If a day key is not one of the seven valid days,
        the scheduler should raise a ValueError.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        raw_prefs = {
            "Alice": {"Funday": "morning", "Tuesday": None, "Wednesday": None, "Thursday": None, "Friday": None, "Saturday": None, "Sunday": None},
            "Bob":   {"Monday": "morning", "Tuesday": None, "Wednesday": None, "Thursday": None, "Friday": None, "Saturday": None, "Sunday": None},
        }

        if hasattr(scheduler, "collect_employee_preferences"):
            with self.assertRaises(ValueError):
                scheduler.collect_employee_preferences(raw_prefs)
        else:
            with self.assertRaises(ValueError):
                scheduler.generate_schedule(raw_prefs)

    def test_employee_day_mapping_not_dict(self):
        """
        If an employee’s day→shift mapping is not a dictionary (for example, a list or a string),
        the scheduler should raise ValueError.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        raw_prefs = {
            "Alice": ["Monday", "morning"],  # Should be a dict, not a list
            "Bob":   {"Monday": "morning", "Tuesday": None, "Wednesday": None, "Thursday": None, "Friday": None, "Saturday": None, "Sunday": None},
        }

        if hasattr(scheduler, "collect_employee_preferences"):
            with self.assertRaises(ValueError):
                scheduler.collect_employee_preferences(raw_prefs)
        else:
            with self.assertRaises(ValueError):
                scheduler.generate_schedule(raw_prefs)

    def test_duplicate_employee_entries(self):
        """
        Since Python dict cannot truly have duplicate keys, we simulate
        duplicates by passing a list of tuples. The scheduler should detect
        that employee names are not unique and raise ValueError.
        """
        if scheduler is None:
            self.skipTest("scheduler module not found")

        # Simulate duplicates with a list of tuples, which is not the expected type.
        duplicate_list = [
            ("Alice", {"Monday": "morning", "Tuesday": None, "Wednesday": None, "Thursday": None, "Friday": None, "Saturday": None, "Sunday": None}),
            ("Alice", {"Monday": "afternoon", "Tuesday": None, "Wednesday": None, "Thursday": None, "Friday": None, "Saturday": None, "Sunday": None}),
        ]
        with self.assertRaises((TypeError, ValueError)):
            scheduler.generate_schedule(duplicate_list)


if __name__ == "__main__":
    random.seed(0)
    unittest.main()
