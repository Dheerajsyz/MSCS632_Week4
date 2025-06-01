/**
 * app.js
 *
 * Express backend for the Employee Shift Scheduler (JavaScript/Node.js version).
 * 
 * Routes:
 *   GET  /           → Serves templates/index.html (UI)
 *   POST /api/schedule → Accepts JSON, returns JSON schedule
 * 
 * Scheduler logic (validation, normalization, conflict resolution, bonus priority ranking)
 * is implemented in pure JavaScript within this file.
 */

const express = require("express");
const path = require("path");
const bodyParser = require("body-parser");

const app = express();

/**
 * Configuration
 */
const PORT = process.env.PORT || 3000;
const DAYS_OF_WEEK = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday"
];
const VALID_SHIFTS = ["morning", "afternoon", "evening"];

// ------------------------------------------------------------------------------
// Middleware
// ------------------------------------------------------------------------------
app.use(bodyParser.json()); // parse application/json
app.use("/static", express.static(path.join(__dirname, "static")));

// Set the view engine to plain HTML by serving from /templates
app.set("views", path.join(__dirname, "templates"));
app.engine("html", require("ejs").renderFile);
app.set("view engine", "html");

// Root route: render the main UI
app.get("/", (req, res) => {
  res.render("index.html", {
    DAYS: DAYS_OF_WEEK,
    SHIFTS: VALID_SHIFTS
  });
});

// ------------------------------------------------------------------------------
// Scheduler Logic (JavaScript Implementation)
// ------------------------------------------------------------------------------

/**
 * Validate and normalize raw employee preferences.
 * 
 * rawPreferences (object):
 *   {
 *     "Alice": {
 *       "Monday":   { "morning": 1, "afternoon": 2, "evening": 3 },
 *       "Tuesday":  null,
 *       ...
 *       "Sunday":   { "morning": 1, "afternoon": 2, "evening": 3 }
 *     },
 *     "Bob": { ... },
 *     ...
 *   }
 * 
 * Returns:
 *   {
 *     "Alice": {
 *       "Monday":   ["morning", "afternoon", "evening"],
 *       "Tuesday":  ["afternoon", "evening", "morning"], // alphabetic if null
 *       ...
 *       "Sunday":   ["morning", "afternoon", "evening"]
 *     },
 *     ...
 *   }
 * 
 * Throws Error if invalid.
 */
function collectEmployeePreferences(rawPreferences) {
  if (typeof rawPreferences !== "object" || rawPreferences === null || Array.isArray(rawPreferences)) {
    throw new Error("Top-level preferences must be an object mapping employee→preferences.");
  }

  // Explicitly check for no employees
  if (Object.keys(rawPreferences).length === 0) {
    throw new Error("No employees provided. Please add at least one employee.");
  }

  // Check for duplicate employee names (case-insensitive)
  const empNames = Object.keys(rawPreferences).map(n => n.trim().toLowerCase());
  const empNameSet = new Set(empNames);
  if (empNames.length !== empNameSet.size) {
    throw new Error("Duplicate employee names are not allowed (case-insensitive).");
  }

  const normalized = {};

  for (const empName in rawPreferences) {
    if (!Object.prototype.hasOwnProperty.call(rawPreferences, empName)) continue;

    // Employee name must be a non-empty string
    if (typeof empName !== "string" || empName.trim() === "") {
      throw new Error(`Invalid employee name: '${empName}'. Must be non-empty string.`);
    }

    const dayMap = rawPreferences[empName];
    if (typeof dayMap !== "object" || dayMap === null || Array.isArray(dayMap)) {
      throw new Error(`Preferences for '${empName}' must be an object mapping day→priority-object or null.`);
    }

    // Ensure every day of week is present
    for (const requiredDay of DAYS_OF_WEEK) {
      if (!(requiredDay in dayMap)) {
        throw new Error(`Employee '${empName}' missing preferences for '${requiredDay}'.`);
      }
    }

    normalized[empName] = {};

    for (const day in dayMap) {
      if (!Object.prototype.hasOwnProperty.call(dayMap, day)) continue;

      if (!DAYS_OF_WEEK.includes(day)) {
        throw new Error(`Invalid day '${day}' for employee '${empName}'. Must be one of ${DAYS_OF_WEEK.join(", ")}.`);
      }

      const priMap = dayMap[day];

      // Treat null or empty object as no preference, but NOT empty string
      if (
        priMap === null ||
        (typeof priMap === "object" && priMap !== null && !Array.isArray(priMap) && Object.keys(priMap).length === 0)
      ) {
        normalized[empName][day] = [...VALID_SHIFTS].sort();
        continue;
      }

      // Accept string as a shortcut for first preference (e.g., "morning")
      if (typeof priMap === "string") {
        const s = priMap.toLowerCase().trim();
        if (!VALID_SHIFTS.includes(s)) {
          throw new Error(`Invalid shift '${priMap}' for '${empName}' on '${day}'.`);
        }
        // Normalize to priority object
        const priorities = {};
        priorities[s] = 1;
        let p = 2;
        for (const other of VALID_SHIFTS) {
          if (other !== s) {
            priorities[other] = p++;
          }
        }
        // Sort shifts by (priority, shiftName) lexicographically
        const sortedArr = Object.entries(priorities).sort((a, b) => {
          if (a[1] !== b[1]) return a[1] - b[1];
          return a[0].localeCompare(b[0]);
        });
        normalized[empName][day] = sortedArr.map(item => item[0]);
        continue;
      }

      // Accept already-normalized input: array of shifts
      if (Array.isArray(priMap) && priMap.length === VALID_SHIFTS.length && priMap.every(s => VALID_SHIFTS.includes(s))) {
        normalized[empName][day] = priMap.slice();
        continue;
      }

      if (typeof priMap !== "object" || priMap === null || Array.isArray(priMap)) {
        throw new Error(`Preferences for '${empName}' on '${day}' must be an object mapping shift→priority integer or null.`);
      }

      const priorities = {};
      let prefCount = 0;
      const seenShifts = new Set();

      // Validate each shift→priority
      for (const shiftName in priMap) {
        if (!Object.prototype.hasOwnProperty.call(priMap, shiftName)) continue;

        if (typeof shiftName !== "string") {
          throw new Error(`Shift keys must be strings for '${empName}' on '${day}', got ${typeof shiftName}.`);
        }

        const sLower = shiftName.toLowerCase().trim();
        if (!VALID_SHIFTS.includes(sLower)) {
          throw new Error(`Invalid shift '${shiftName}' for '${empName}' on '${day}'.`);
        }
        if (seenShifts.has(sLower)) {
          throw new Error(`Duplicate shift preference '${shiftName}' for '${empName}' on '${day}'.`);
        }
        seenShifts.add(sLower);
        prefCount++;
        if (prefCount > 2) {
          throw new Error(`Only two preferences (primary and secondary) allowed for '${empName}' on '${day}'.`);
        }
        const p = priMap[shiftName];
        if (typeof p !== "number" || !Number.isInteger(p) || p < 1) {
          throw new Error(`Priority for '${shiftName}' must be a positive integer, got ${p}.`);
        }
        priorities[sLower] = p;
      }

      // Assign default large priority for any shift not mentioned
      let defaultP = 1;
      if (Object.keys(priorities).length > 0) {
        defaultP = Math.max(...Object.values(priorities)) + 10;
      }
      for (const s of VALID_SHIFTS) {
        if (!(s in priorities)) {
          priorities[s] = defaultP;
        }
      }

      // Sort shifts by (priority, shiftName) lexicographically
      const sortedArr = Object.entries(priorities).sort((a, b) => {
        if (a[1] !== b[1]) return a[1] - b[1];
        return a[0].localeCompare(b[0]);
      });
      normalized[empName][day] = sortedArr.map(item => item[0]);
    }
  }

  // Post-normalization: check every employee has all 7 days, and each day is a 3-shift array
  for (const empName in normalized) {
    for (const day of DAYS_OF_WEEK) {
      if (!normalized[empName][day] || !Array.isArray(normalized[empName][day]) || normalized[empName][day].length !== 3) {
        throw new Error(`Employee '${empName}' has invalid or incomplete preferences for '${day}'. Each day must have 3 ranked shifts.`);
      }
    }
  }

  return normalized;
}

/**
 * Generate a weekly schedule given raw preferences.
 * 
 * rawPreferences: same shape as collectEmployeePreferences expects.
 * 
 * Returns:
 *   {
 *     "Monday":    { "morning": ["Alice","Bob"], "afternoon": [...], "evening": [...] },
 *     "Tuesday":   { ... },
 *     ...
 *     "Sunday":    { ... }
 *   }
 * 
 * Throws Error if invalid.
 */
function generateSchedule(rawPreferences) {
  if (typeof rawPreferences !== "object" || rawPreferences === null || Array.isArray(rawPreferences)) {
    throw new Error("Top-level preferences must be an object mapping employee→preferences.");
  }

  const preferences = collectEmployeePreferences(rawPreferences);
  const employees = Object.keys(preferences);

  // Rubric: must have at least 6 employees (2 per shift per day)
  if (employees.length < 6) {
    throw new Error("At least 6 unique employees are required to generate a schedule (2 per shift per day). Please add more employees.");
  }

  // Initialize empty schedule
  const schedule = {};
  for (const day of DAYS_OF_WEEK) {
    schedule[day] = {};
    for (const shift of VALID_SHIFTS) {
      schedule[day][shift] = [];
    }
  }

  // Track how many days each employee has been assigned
  const assignedCount = {};
  for (const emp of employees) {
    assignedCount[emp] = 0;
  }

  // Deterministic random seed for tie-breaking
  // We use a simple pseudo-random approach with a fixed seed
  let randomSeed = 0;
  function pseudoRandom() {
    // xorshift32
    randomSeed ^= randomSeed << 13;
    randomSeed ^= randomSeed >>> 17;
    randomSeed ^= randomSeed << 5;
    return (randomSeed < 0 ? ~randomSeed + 1 : randomSeed) % 1000 / 1000;
  }
  randomSeed = 1; // non-zero seed

  // Shuffle helper (Fisher-Yates)
  function shuffle(array) {
    let m = array.length, t, i;
    while (m) {
      i = Math.floor(pseudoRandom() * m--);
      t = array[m];
      array[m] = array[i];
      array[i] = t;
    }
    return array;
  }

  for (const day of DAYS_OF_WEEK) {
    const assignedToday = new Set();

    for (const shift of VALID_SHIFTS) {
      // Build rank→employees map
      const rankMap = {};
      for (const emp of employees) {
        if (assignedCount[emp] >= 5 || assignedToday.has(emp)) {
          continue;
        }
        const prefList = preferences[emp][day];
        const rank = prefList.indexOf(shift);
        if (rank === -1) {
          // fallback rank
          rankMap[VALID_SHIFTS.length] = rankMap[VALID_SHIFTS.length] || [];
          rankMap[VALID_SHIFTS.length].push(emp);
        } else {
          rankMap[rank] = rankMap[rank] || [];
          rankMap[rank].push(emp);
        }
      }

      // Flatten in ascending rank, shuffling within each rank for tie-breaking
      const ordered = [];
      const ranks = Object.keys(rankMap).map(r => parseInt(r)).sort((a, b) => a - b);
      for (const r of ranks) {
        const group = rankMap[r].slice();
        shuffle(group);
        for (const emp of group) {
          ordered.push(emp);
        }
      }

      // Assign up to two from ordered
      let placed = 0;
      for (const emp of ordered) {
        if (assignedCount[emp] >= 5 || assignedToday.has(emp)) {
          continue;
        }
        schedule[day][shift].push(emp);
        assignedCount[emp]++;
        assignedToday.add(emp);
        placed++;
        if (placed >= 2) {
          break;
        }
      }
      // If fewer than two, fill from any available employee not already assigned today
      if (placed < 2) {
        for (const emp of employees) {
          if (placed >= 2) break;
          if (assignedCount[emp] < 5 && !assignedToday.has(emp)) {
            schedule[day][shift].push(emp);
            assignedCount[emp]++;
            assignedToday.add(emp);
            placed++;
          }
        }
      }
      // FINAL fallback: if still <2, allow double-shift for the day (to always fill 2)
      if (placed < 2) {
        for (const emp of employees) {
          if (placed >= 2) break;
          if (assignedCount[emp] < 5) {
            schedule[day][shift].push(emp);
            assignedCount[emp]++;
            placed++;
          }
        }
      }
    }
  }

  return schedule;
}

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Server listening on http://localhost:${PORT}`);
  });
}

// API route: generate schedule
app.post("/api/schedule", (req, res) => {
  try {
    const raw = req.body;
    // Validate input is a non-empty object
    if (!raw || typeof raw !== "object" || Array.isArray(raw) || Object.keys(raw).length === 0) {
      return res.status(400).json({ error: "Top-level preferences must be a non-empty object mapping employee→preferences." });
    }
    let schedule;
    try {
      schedule = generateSchedule(raw);
    } catch (err) {
      // Return error as JSON, not HTML
      return res.status(400).json({ error: err.message || "Invalid input." });
    }
    // Success: return schedule as JSON
    return res.json(schedule);
  } catch (err) {
    // Catch-all for unexpected errors
    return res.status(500).json({ error: "Unexpected server error: " + (err.message || err) });
  }
});

module.exports = {
  collectEmployeePreferences,
  generateSchedule,
  DAYS_OF_WEEK,
  VALID_SHIFTS
};
