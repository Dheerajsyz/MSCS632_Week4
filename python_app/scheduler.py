import random
from collections import defaultdict, deque

# Constants
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
VALID_SHIFTS = ["morning", "afternoon", "evening"]  # Keep this for backward compatibility
SHIFTS = VALID_SHIFTS  # Add this for consistency with the Flask app

# Deterministic shuffle for tie-breaking (Fisher-Yates with fixed seed)
def deterministic_shuffle(arr, seed=1):
    arr = arr[:]
    random_seed = seed
    def pseudo_random():
        nonlocal random_seed
        random_seed ^= (random_seed << 13) & 0xFFFFFFFF
        random_seed ^= (random_seed >> 17)
        random_seed ^= (random_seed << 5) & 0xFFFFFFFF
        return abs(random_seed) % 1000 / 1000
    m = len(arr)
    while m:
        i = int(pseudo_random() * m)
        m -= 1
        arr[m], arr[i] = arr[i], arr[m]
    return arr

def collect_employee_preferences(raw_preferences):
    if not isinstance(raw_preferences, dict):
        raise ValueError("Top-level preferences must be an object mapping employee→preferences.")
    if not raw_preferences:
        raise ValueError("No employees provided. Please add at least one employee.")
    emp_names = [n.strip().lower() for n in raw_preferences.keys()]
    if len(emp_names) != len(set(emp_names)):
        raise ValueError("Duplicate employee names are not allowed (case-insensitive).")
    normalized = {}
    for emp_name, day_map in raw_preferences.items():
        if not isinstance(emp_name, str) or not emp_name.strip():
            raise ValueError(f"Invalid employee name: '{emp_name}'. Must be non-empty string.")
        if not isinstance(day_map, dict):
            raise ValueError(f"Preferences for '{emp_name}' must be an object mapping day→priority-object or null.")
        for required_day in DAYS_OF_WEEK:
            if required_day not in day_map:
                raise ValueError(f"Employee '{emp_name}' missing preferences for '{required_day}'.")
        normalized[emp_name] = {}
        for day, pri_map in day_map.items():
            if day not in DAYS_OF_WEEK:
                raise ValueError(f"Invalid day '{day}' for employee '{emp_name}'. Must be one of {', '.join(DAYS_OF_WEEK)}.")
            # Treat None or empty dict as no preference
            if pri_map is None or (isinstance(pri_map, dict) and not pri_map):
                normalized[emp_name][day] = sorted(VALID_SHIFTS)
                continue
            if isinstance(pri_map, str):
                s = pri_map.lower().strip()
                if s not in VALID_SHIFTS:
                    raise ValueError(f"Invalid shift '{pri_map}' for '{emp_name}' on '{day}'.")
                priorities = {s: 1}
                p = 2
                for other in VALID_SHIFTS:
                    if other != s:
                        priorities[other] = p
                        p += 1
                sorted_arr = sorted(priorities.items(), key=lambda x: (x[1], x[0]))
                normalized[emp_name][day] = [item[0] for item in sorted_arr]
                continue
            if isinstance(pri_map, list) and len(pri_map) == len(VALID_SHIFTS) and all(s in VALID_SHIFTS for s in pri_map):
                normalized[emp_name][day] = list(pri_map)
                continue
            if not isinstance(pri_map, dict):
                raise ValueError(f"Preferences for '{emp_name}' on '{day}' must be an object mapping shift→priority integer or null.")
            priorities = {}
            pref_count = 0
            seen_shifts = set()
            for shift_name, p in pri_map.items():
                if not isinstance(shift_name, str):
                    raise ValueError(f"Shift keys must be strings for '{emp_name}' on '{day}', got {type(shift_name)}.")
                s_lower = shift_name.lower().strip()
                if s_lower not in VALID_SHIFTS:
                    raise ValueError(f"Invalid shift '{shift_name}' for '{emp_name}' on '{day}'.")
                if s_lower in seen_shifts:
                    raise ValueError(f"Duplicate shift preference '{shift_name}' for '{emp_name}' on '{day}'.")
                seen_shifts.add(s_lower)
                pref_count += 1
                if pref_count > 2:
                    raise ValueError(f"Only two preferences (primary and secondary) allowed for '{emp_name}' on '{day}'.")
                if not isinstance(p, int) or p < 1:
                    raise ValueError(f"Priority for '{shift_name}' must be a positive integer, got {p}.")
                priorities[s_lower] = p
            default_p = max(priorities.values(), default=0) + 10 if priorities else 1
            for s in VALID_SHIFTS:
                if s not in priorities:
                    priorities[s] = default_p
            sorted_arr = sorted(priorities.items(), key=lambda x: (x[1], x[0]))
            normalized[emp_name][day] = [item[0] for item in sorted_arr]
        # Post-normalization: check every day is a 3-shift array
        for day in DAYS_OF_WEEK:
            if day not in normalized[emp_name] or not isinstance(normalized[emp_name][day], list) or len(normalized[emp_name][day]) != 3:
                raise ValueError(f"Employee '{emp_name}' has invalid or incomplete preferences for '{day}'. Each day must have 3 ranked shifts.")
    return normalized

def generate_schedule(raw_preferences):
    if not isinstance(raw_preferences, dict):
        raise ValueError("Top-level preferences must be an object mapping employee→preferences.")
    preferences = collect_employee_preferences(raw_preferences)
    employees = list(preferences.keys())
    if len(employees) < 6:
        raise ValueError("At least 6 unique employees are required to generate a schedule (2 per shift per day). Please add more employees.")
    schedule = {day: {shift: [] for shift in VALID_SHIFTS} for day in DAYS_OF_WEEK}
    assigned_count = {emp: 0 for emp in employees}
    for day in DAYS_OF_WEEK:
        assigned_today = set()
        for shift in VALID_SHIFTS:
            # Build rank→employees map
            rank_map = defaultdict(list)
            for emp in employees:
                if assigned_count[emp] >= 5 or emp in assigned_today:
                    continue
                pref_list = preferences[emp][day]
                try:
                    rank = pref_list.index(shift)
                except ValueError:
                    rank = len(VALID_SHIFTS)
                rank_map[rank].append(emp)
            # Flatten in ascending rank, shuffling within each rank for tie-breaking
            ordered = []
            for r in sorted(rank_map.keys()):
                group = deterministic_shuffle(rank_map[r], seed=1)
                ordered.extend(group)
            # Assign up to two from ordered
            placed = 0
            for emp in ordered:
                if assigned_count[emp] >= 5 or emp in assigned_today:
                    continue
                schedule[day][shift].append(emp)
                assigned_count[emp] += 1
                assigned_today.add(emp)
                placed += 1
                if placed >= 2:
                    break
            # If fewer than two, fill from any available employee not already assigned today
            if placed < 2:
                for emp in employees:
                    if placed >= 2:
                        break
                    if assigned_count[emp] < 5 and emp not in assigned_today:
                        schedule[day][shift].append(emp)
                        assigned_count[emp] += 1
                        assigned_today.add(emp)
                        placed += 1
            # FINAL fallback: if still <2, allow double-shift for the day (to always fill 2)
            if placed < 2:
                for emp in employees:
                    if placed >= 2:
                        break
                    if assigned_count[emp] < 5:
                        schedule[day][shift].append(emp)
                        assigned_count[emp] += 1
                        placed += 1
    return schedule


def schedule_courses(courses):
    """
    Generate a semester-by-semester schedule for courses based on prerequisites.
    
    Args:
        courses (dict): A dictionary mapping course names to their prerequisites
            Example: {'Algorithms': ['DataStructures'], 'DataStructures': ['Programming']}
    
    Returns:
        list: A list of lists, where each inner list represents the courses for a semester
        
    Raises:
        ValueError: If there is a circular dependency in prerequisites
    """
    if not courses:
        return []

    # Create adjacency list and in-degree count
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    all_courses = set()

    # Build the graph
    for course, prereqs in courses.items():
        all_courses.add(course)
        for prereq in prereqs:
            graph[prereq].append(course)
            in_degree[course] += 1
            all_courses.add(prereq)

    # Initialize queue with courses that have no prerequisites
    queue = deque([course for course in all_courses if in_degree[course] == 0])
    if not queue:
        raise ValueError("Circular dependency detected in course prerequisites")

    schedule = []
    while queue:
        # Current semester courses
        current_semester = []
        
        # Process all courses that can be taken this semester
        for _ in range(len(queue)):
            course = queue.popleft()
            current_semester.append(course)
            
            # Update courses that depend on this one
            for dependent in graph[course]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        schedule.append(sorted(current_semester))  # Sort courses within semester for consistency
    
    # Check if all courses were scheduled
    scheduled_courses = sum(len(semester) for semester in schedule)
    if scheduled_courses != len(all_courses):
        raise ValueError("Circular dependency detected in course prerequisites")
    
    return schedule
