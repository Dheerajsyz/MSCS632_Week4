import pytest
from scheduler import collect_employee_preferences, generate_schedule, DAYS_OF_WEEK, VALID_SHIFTS

# 1. Valid input: all types (None, string, dict) for all days
def test_valid_inputs():
    # Use 6 employees, and only two preferences for dict
    raw = {
        "Alice": {d: None for d in DAYS_OF_WEEK},
        "Bob": {d: "morning" for d in DAYS_OF_WEEK},
        "Carol": {d: {"morning": 1, "afternoon": 2} for d in DAYS_OF_WEEK},
        "Dave": {d: "afternoon" for d in DAYS_OF_WEEK},
        "Eve": {d: {"evening": 1, "morning": 2} for d in DAYS_OF_WEEK},
        "Frank": {d: None for d in DAYS_OF_WEEK},
    }
    prefs = collect_employee_preferences(raw)
    assert all(len(prefs[e][d]) == 3 for e in prefs for d in DAYS_OF_WEEK)

# 2. Invalid employee name (empty, not a string)
def test_invalid_employee_name():
    with pytest.raises(ValueError):
        collect_employee_preferences({"": {d: None for d in DAYS_OF_WEEK}})
    with pytest.raises(ValueError):
        collect_employee_preferences({None: {d: None for d in DAYS_OF_WEEK}})

# 3. Missing days
def test_missing_days():
    bad = {"Alice": {d: None for d in DAYS_OF_WEEK[:-1]}}
    with pytest.raises(ValueError):
        collect_employee_preferences(bad)

# 4. Invalid day name
def test_invalid_day_name():
    bad = {"Alice": {**{d: None for d in DAYS_OF_WEEK}, "Funday": None}}
    with pytest.raises(ValueError):
        collect_employee_preferences(bad)

# 5. Invalid shift name
def test_invalid_shift_name():
    bad = {"Alice": {d: "midnight" for d in DAYS_OF_WEEK}}
    with pytest.raises(ValueError):
        collect_employee_preferences(bad)

# 6. Invalid priority (not int, <1)
def test_invalid_priority():
    bad = {"Alice": {d: {"morning": 0} for d in DAYS_OF_WEEK}}
    with pytest.raises(ValueError):
        collect_employee_preferences(bad)
    bad2 = {"Alice": {d: {"morning": "high"} for d in DAYS_OF_WEEK}}
    with pytest.raises(ValueError):
        collect_employee_preferences(bad2)

# 7. Extra/unexpected types
def test_unexpected_type():
    bad = {"Alice": {d: 42 for d in DAYS_OF_WEEK}}
    with pytest.raises(ValueError):
        collect_employee_preferences(bad)

# 8. Already-normalized input (list of shifts)
def test_already_normalized():
    norm = {f"Emp{i}": {d: VALID_SHIFTS[:] for d in DAYS_OF_WEEK} for i in range(6)}
    sched = generate_schedule(norm)
    assert isinstance(sched, dict)

# 9. Employee with more than 5 shifts/week
# Use 14 employees so the scheduler can meet the rubric
def test_max_5_shifts():
    shifts = ["morning", "afternoon", "evening"]
    raw = {f"Emp{i}": {d: shifts[(i + j) % 3] for j, d in enumerate(DAYS_OF_WEEK)} for i in range(14)}
    sched = generate_schedule(raw)
    counts = {e: 0 for e in raw}
    for d in DAYS_OF_WEEK:
        for s in VALID_SHIFTS:
            for e in sched[d][s]:
                counts[e] += 1
    assert all(v <= 5 for v in counts.values())

# 10. Employee assigned to more than one shift/day
# Use 14 employees so the scheduler can meet the rubric
def test_one_shift_per_day():
    shifts = ["morning", "afternoon", "evening"]
    raw = {f"Emp{i}": {d: shifts[(i + j) % 3] for j, d in enumerate(DAYS_OF_WEEK)} for i in range(14)}
    sched = generate_schedule(raw)
    for d in DAYS_OF_WEEK:
        assigned = []
        for s in VALID_SHIFTS:
            assigned += sched[d][s]
        assert len(set(assigned)) == len(assigned)

# 11. Fewer than 2 employees for a shift
def test_min_2_per_shift():
    raw = {f"Emp{i}": {d: "morning" for d in DAYS_OF_WEEK} for i in range(6)}
    sched = generate_schedule(raw)
    for d in DAYS_OF_WEEK:
        for s in VALID_SHIFTS:
            assert len(sched[d][s]) == 2

# 12. Shift conflict resolution
# Use 14 employees so the scheduler can meet the rubric
def test_shift_conflict_resolution():
    shifts = ["morning", "afternoon", "evening"]
    raw = {f"E{i}": {d: shifts[(i + j) % 3] for j, d in enumerate(DAYS_OF_WEEK)} for i in range(14)}
    sched = generate_schedule(raw)
    for d in DAYS_OF_WEEK:
        assigned = []
        for s in VALID_SHIFTS:
            assigned += sched[d][s]
        assert len(set(assigned)) == len(assigned)
        for s in VALID_SHIFTS:
            assert len(sched[d][s]) == 2

if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__]))
