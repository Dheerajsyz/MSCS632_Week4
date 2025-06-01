// static/js/employees.js

// 1) Define DAYS_OF_WEEK and VALID_SHIFTS if not already present
if (typeof window.DAYS_OF_WEEK === "undefined") {
  window.DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
  ];
}
if (typeof window.VALID_SHIFTS === "undefined") {
  window.VALID_SHIFTS = ["morning", "afternoon", "evening"];
}
const DAYS_OF_WEEK = window.DAYS_OF_WEEK;
const VALID_SHIFTS = window.VALID_SHIFTS;

// In-memory employees array
let employees = [];

/**
 * showAlert(message, type)
 * Displays a Bootstrap‐style alert in the top right. type = "success" or "danger".
 */
function showAlert(message, type = "danger") {
  const container = document.getElementById("alert-container");
  if (!container) return console.warn("Alert container not found");
  const wrapper = document.createElement("div");
  const icon =
    type === "success"
      ? '<i class="fas fa-check-circle mr-2"></i>'
      : '<i class="fas fa-exclamation-circle mr-2"></i>';
  wrapper.innerHTML = `
    <div class="alert alert-${type} alert-dismissible fade show shadow-lg" role="alert"
         style="pointer-events:auto; min-width:300px;">
      ${icon}<span class="font-weight-bold">${message}</span>
      <button type="button" class="close" data-dismiss="alert" aria-label="Close">
        <span aria-hidden="true">&times;</span>
      </button>
    </div>
  `;
  container.appendChild(wrapper);
  setTimeout(() => {
    $(wrapper).alert("close");
  }, 5000);
}

/**
 * resetModal()
 * Clears the “Add/Edit Employee” modal fields and resets labels.
 */
function resetModal() {
  const nameInput = document.getElementById("employee-name-input");
  const editingIndex = document.getElementById("editing-index");
  if (nameInput) nameInput.value = "";
  if (editingIndex) editingIndex.value = "-1";
  DAYS_OF_WEEK.forEach((day) => {
    const p1 = document.getElementById(`pref-${day}-1`);
    const p2 = document.getElementById(`pref-${day}-2`);
    if (p1) p1.value = "";
    if (p2) p2.value = "";
  });
  const modalLabel = document.getElementById("employeeModalLabel");
  const saveBtn = document.getElementById("save-employee-btn");
  if (modalLabel) modalLabel.textContent = "Add Employee";
  if (saveBtn) saveBtn.textContent = "Save Employee";
}

/**
 * fillModal(index)
 * Pre-fills modal fields with data from employees[index].
 */
function fillModal(index) {
  const emp = employees[index];
  if (!emp) return console.warn("No employee at index", index);
  const nameInput = document.getElementById("employee-name-input");
  const editingIndex = document.getElementById("editing-index");
  if (nameInput) nameInput.value = emp.name;
  if (editingIndex) editingIndex.value = index.toString();

  DAYS_OF_WEEK.forEach((day) => {
    const priMap = emp.prefs[day]; // null or { shift: priority }
    const p1 = document.getElementById(`pref-${day}-1`);
    const p2 = document.getElementById(`pref-${day}-2`);
    if (!p1 || !p2) return; // might happen if DOM not fully built
    if (priMap === null) {
      p1.value = "";
      p2.value = "";
    } else {
      const items = Object.entries(priMap)
        .filter(([s, p]) => VALID_SHIFTS.includes(s) && Number.isInteger(p))
        .sort((a, b) => a[1] - b[1]);
      p1.value = items.length > 0 ? items[0][0] : "";
      p2.value = items.length > 1 ? items[1][0] : "";
    }
  });
  const modalLabel = document.getElementById("employeeModalLabel");
  const saveBtn = document.getElementById("save-employee-btn");
  if (modalLabel) modalLabel.textContent = "Edit Employee";
  if (saveBtn) saveBtn.textContent = "Save Changes";
}

/**
 * renderEmployeeTable()
 * Repaints the "Current Employees" table body, the badge, and the name list.
 */
function renderEmployeeTable() {
  const tbody = document.querySelector("#employee-table tbody");
  if (!tbody) return console.warn("#employee-table tbody not found");
  tbody.innerHTML = "";

  // Update badge & name list
  const badge = document.getElementById("employee-count-badge");
  if (badge) badge.textContent = employees.length.toString();
  const listDiv = document.getElementById("employee-list-names");
  if (listDiv) {
    listDiv.textContent =
      employees.length === 0
        ? "No employees added yet."
        : "Employees: " + employees.map((e) => e.name).join(", ");
  }

  if (employees.length === 0) {
    const row = document.createElement("tr");
    row.innerHTML = `<td colspan="${DAYS_OF_WEEK.length + 2}" class="text-center text-muted">
      No employees added yet. Click “Add Employee” to begin.
    </td>`;
    tbody.appendChild(row);
    return;
  }

  employees.forEach((emp, idx) => {
    const row = document.createElement("tr");

    // Name cell
    const nameCell = document.createElement("td");
    nameCell.textContent = emp.name;
    row.appendChild(nameCell);

    // Preferences cells
    DAYS_OF_WEEK.forEach((day) => {
      const cell = document.createElement("td");
      const priMap = emp.prefs[day];
      if (priMap === null) {
        cell.innerHTML = `<span class="text-muted">No Pref</span>`;
      } else {
        const items = Object.entries(priMap)
          .filter(([s, p]) => VALID_SHIFTS.includes(s) && Number.isInteger(p))
          .sort((a, b) => a[1] - b[1])
          .map(
            ([s, p]) =>
              `<small>${s.charAt(0).toUpperCase() + s.slice(1)}</small>`
          );
        cell.innerHTML = items.join(", ");
      }
      row.appendChild(cell);
    });

    // Action cell (Edit / Remove)
    const actionCell = document.createElement("td");
    actionCell.innerHTML = `
      <button class="btn btn-sm btn-info mr-1" onclick="editEmployee(${idx})">
        <i class="fas fa-edit"></i>
      </button>
      <button class="btn btn-sm btn-danger" onclick="removeEmployee(${idx})">
        <i class="fas fa-trash-alt"></i>
      </button>
    `;
    row.appendChild(actionCell);

    tbody.appendChild(row);
  });
}

/**
 * isDuplicateName(name)
 * Returns true if name (case‐insensitive) already exists.
 */
function isDuplicateName(name) {
  return employees.some(
    (emp) => emp.name.trim().toLowerCase() === name.trim().toLowerCase()
  );
}

/**
 * buildTablesDynamically()
 * Overwrites any EJS placeholders in both tables and builds real <thead> / <tbody>:
 * - Employee Table: headers = [Name, Monday, Tuesday, …, Sunday, Actions]
 * - Schedule Table: headers = [Shift \\ Day, Monday, …, Sunday]; rows = [Morning, Afternoon, Evening].
 */
function buildTablesDynamically() {
  console.log("employees.js: Building table headers/rows...");

  // Employee Table Header
  const empTheadRow = document.querySelector("#employee-table thead tr");
  if (!empTheadRow) {
    console.error("employees.js: Cannot find #employee-table thead tr");
  } else {
    empTheadRow.innerHTML = "";
    const empHeaders = ["Name", ...DAYS_OF_WEEK, "Actions"];
    empHeaders.forEach((text) => {
      const th = document.createElement("th");
      th.scope = "col";
      th.textContent = text;
      empTheadRow.appendChild(th);
    });
  }

  // Schedule Table Header
  const schedTheadRow = document.querySelector("#schedule-table thead tr");
  if (!schedTheadRow) {
    console.error("employees.js: Cannot find #schedule-table thead tr");
  } else {
    schedTheadRow.innerHTML = "";
    const schedHeaders = ["Shift \\ Day", ...DAYS_OF_WEEK];
    schedHeaders.forEach((text) => {
      const th = document.createElement("th");
      th.scope = "col";
      th.textContent = text;
      schedTheadRow.appendChild(th);
    });
  }

  // Schedule Table Body: one row per shift
  const schedTbody = document.querySelector("#schedule-table tbody");
  if (!schedTbody) {
    console.error("employees.js: Cannot find #schedule-table tbody");
  } else {
    schedTbody.innerHTML = "";
    VALID_SHIFTS.forEach((shift) => {
      const tr = document.createElement("tr");
      const th = document.createElement("th");
      th.scope = "row";
      th.textContent = shift.charAt(0).toUpperCase() + shift.slice(1);
      tr.appendChild(th);

      DAYS_OF_WEEK.forEach((day) => {
        const td = document.createElement("td");
        td.setAttribute("data-day", day);
        td.setAttribute("data-shift", shift);
        tr.appendChild(td);
      });

      schedTbody.appendChild(tr);
    });
  }
}

/**
 * editEmployee(index)
 * Opens the modal with pre-filled data.
 */
function editEmployee(index) {
  fillModal(index);
  $("#employeeModal").modal("show");
}

/**
 * removeEmployee(index)
 * Removes employee with confirmation.
 */
function removeEmployee(index) {
  const name = employees[index] ? employees[index].name : "(unknown)";
  if (confirm(`Are you sure you want to remove “${name}”?`)) {
    employees.splice(index, 1);
    showAlert(`Employee “${name}” removed.`, "success");
    renderEmployeeTable();
  }
}

/**
 * isPythonBackendResponse(data)
 * Checks if data has a boolean `success` field → treat as Python/Flask style.
 * Otherwise treat as Node/Express style.
 */
function isPythonBackendResponse(data) {
  return data && typeof data.success === "boolean";
}

/**
 * Handles “Generate Schedule” click.
 * Posts rawPrefs to /api/schedule and calls renderSchedule(...) on success.
 */
document
  .getElementById("generate-schedule-btn")
  .addEventListener("click", function () {
    if (employees.length < 6) {
      showAlert(
        "To meet the rubric, add at least 6 employees (2 per shift per day).",
        "danger"
      );
      return;
    }

    // Build rawPrefs = { "Alice": {Monday: {...}, ...}, "Bob": {...}, ... }
    const rawPrefs = {};
    employees.forEach((emp) => {
      rawPrefs[emp.name] = emp.prefs;
    });

    fetch("/api/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(rawPrefs),
    })
      .then(async (resp) => {
        let data;
        try {
          data = await resp.json();
        } catch (e) {
          showAlert("Server error: invalid JSON response.", "danger");
          return;
        }

        if (!resp.ok) {
          const msg = data && data.error ? data.error : "Unknown backend error.";
          showAlert("Error: " + msg, "danger");
          return;
        }

        if (isPythonBackendResponse(data)) {
          if (!data.success) {
            showAlert("Error: " + (data.error || "Unknown error."), "danger");
            return;
          }
          renderSchedule(data.schedule);
        } else {
          if (data.error) {
            showAlert("Error: " + data.error, "danger");
            return;
          }
          renderSchedule(data);
        }
      })
      .catch((err) => {
        showAlert("Network error: " + err, "danger");
      });
  });

/**
 * renderSchedule(schedule)
 * Reveals the schedule table and fills each <td> with assigned names.
 */
function renderSchedule(schedule) {
  const container = document.getElementById("schedule-container");
  if (container) container.style.display = "block";

  DAYS_OF_WEEK.forEach((day) => {
    VALID_SHIFTS.forEach((shift) => {
      const cell = document.querySelector(
        `#schedule-table td[data-day="${day}"][data-shift="${shift}"]`
      );
      if (!cell) return;
      const empList = schedule[day][shift];
      if (Array.isArray(empList) && empList.length > 0) {
        cell.innerHTML = empList.map((e) => `<div>${e}</div>`).join("");
      } else {
        cell.innerHTML = `<span class="text-muted">—</span>`;
      }
    });
  });
}

/**
 * Handles “Clear All Employees” click:
 * Empties the array, clears the table, and hides schedule.
 */
document
  .getElementById("clear-employees-btn")
  .addEventListener("click", function () {
    if (employees.length === 0) {
      showAlert("No employees to clear.", "info");
      return;
    }
    if (
      confirm(
        "Are you sure you want to remove all employees? This cannot be undone."
      )
    ) {
      employees = [];
      renderEmployeeTable();
      showAlert("All employees cleared.", "success");
      const container = document.getElementById("schedule-container");
      if (container) container.style.display = "none";
    }
  });

/**
 * Handles “Add/Edit Employee” form submission.
 * Validates and prevents duplicate names & duplicate prefs.
 */
document.getElementById("employee-form").addEventListener("submit", function (
  e
) {
  e.preventDefault();
  const nameInput = document.getElementById("employee-name-input");
  const name = nameInput ? nameInput.value.trim() : "";
  if (!name) {
    showAlert("Employee name cannot be empty.", "danger");
    return false;
  }
  const editingIndex = parseInt(
    document.getElementById("editing-index").value,
    10
  );
  if (editingIndex < 0 && isDuplicateName(name)) {
    showAlert(`Employee with name “${name}” already exists.`, "danger");
    return false;
  }

  let duplicatePrefError = false;
  const prefs = {};
  DAYS_OF_WEEK.forEach((day) => {
    const p1 = document.getElementById(`pref-${day}-1`).value;
    const p2 = document.getElementById(`pref-${day}-2`).value;
    if (p1 && p2 && p1 === p2) duplicatePrefError = true;

    const used = new Set();
    const priMap = {};
    let rank = 1;
    [p1, p2].forEach((val) => {
      if (val && VALID_SHIFTS.includes(val) && !used.has(val)) {
        priMap[val] = rank;
        used.add(val);
        rank++;
      }
    });
    prefs[day] = Object.keys(priMap).length === 0 ? null : priMap;
  });
  if (duplicatePrefError) {
    showAlert("No duplicate preferences allowed for the same day.", "danger");
    return false;
  }

  if (editingIndex >= 0) {
    employees[editingIndex] = { name, prefs };
    showAlert(`Employee “${name}” updated.`, "success");
  } else {
    employees.push({ name, prefs });
    showAlert(`Employee “${name}” added.`, "success");
  }

  renderEmployeeTable();
  $("#employeeModal").modal("hide");
  resetModal();
  return false;
});

/**
 * On DOMContentLoaded:
 * 1) Log to confirm employees.js is loaded.
 * 2) Call buildTablesDynamically in a setTimeout to ensure DOM is fully ready.
 * 3) Render the (initially empty) employee table.
 */
document.addEventListener("DOMContentLoaded", () => {
  console.log("employees.js loaded.");
  setTimeout(() => {
    console.log("employees.js: Building tables dynamically...");
    buildTablesDynamically();
    renderEmployeeTable();
  }, 0);
});
