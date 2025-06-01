// static/js/employees_py.js

// Because Flask’s Jinja2 has injected DAYS and SHIFTS into the HTML, we can
// read them from <script> tags or a global variable. For simplicity, we assume
// that in your Flask layout you did something like:
//   <script>window.DAYS_OF_WEEK = {{ DAYS|tojson }}; window.VALID_SHIFTS = {{ SHIFTS|tojson }};</script>
// just before this file is included. So here, we simply read those globals.

const DAYS_OF_WEEK = window.DAYS_OF_WEEK || [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];
const VALID_SHIFTS = window.VALID_SHIFTS || ["morning", "afternoon", "evening"];

let employees = [];

/**
 * showAlert(message, type)
 */
function showAlert(message, type = "danger") {
  const container = document.getElementById("alert-container");
  if (!container) return console.warn("No #alert-container found");
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
 */
function fillModal(index) {
  const emp = employees[index];
  if (!emp) return console.warn("No employee at index", index);
  const nameInput = document.getElementById("employee-name-input");
  const editingIndex = document.getElementById("editing-index");
  if (nameInput) nameInput.value = emp.name;
  if (editingIndex) editingIndex.value = index.toString();

  DAYS_OF_WEEK.forEach((day) => {
    const priMap = emp.prefs[day];
    const p1 = document.getElementById(`pref-${day}-1`);
    const p2 = document.getElementById(`pref-${day}-2`);
    if (!p1 || !p2) return;
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
 */
function renderEmployeeTable() {
  const tbody = document.querySelector("#employee-table tbody");
  if (!tbody) return console.warn("No #employee-table tbody found");
  tbody.innerHTML = "";

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

    // Name
    const nameCell = document.createElement("td");
    nameCell.textContent = emp.name;
    row.appendChild(nameCell);

    // Preferences
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

    // Actions
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
 */
function isDuplicateName(name) {
  return employees.some(
    (emp) => emp.name.trim().toLowerCase() === name.trim().toLowerCase()
  );
}

/**
 * editEmployee(index)
 */
function editEmployee(index) {
  fillModal(index);
  $("#employeeModal").modal("show");
}

/**
 * removeEmployee(index)
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
 */
function isPythonBackendResponse(data) {
  return data && typeof data.success === "boolean";
}

/**
 * “Generate Schedule” Click Handler
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
 * “Clear All Employees” Click Handler
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
 * “Add/Edit Employee” Form Submit Handler
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
 * On DOMContentLoaded: just render the table (Flask already replaced EJS with real <th>),
 * so we only need to repaint the employee rows. No need to build <thead> here.
 */
document.addEventListener("DOMContentLoaded", () => {
  console.log("employees_py.js loaded (Python mode).");
  renderEmployeeTable();
});
