const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const SHIFTS = ["morning", "afternoon", "evening"];
const employeeList = [];

const employeeListElem = document.getElementById('employeeList');
const generateBtn = document.getElementById('generateBtn');
const employeeForm = document.getElementById('employeeForm');
const employeeWarning = document.getElementById('employeeWarning');
const employeeError = document.getElementById('employeeError');
const scheduleContainer = document.getElementById('scheduleContainer');
const scheduleTable = document.getElementById('scheduleTable');

function showEmployeeError(msg) {
    employeeError.textContent = msg;
    employeeError.style.display = '';
    setTimeout(() => { employeeError.style.display = 'none'; }, 4000);
}

function isDuplicateName(name) {
    return employeeList.some(emp => emp.name.trim().toLowerCase() === name.trim().toLowerCase());
}

function updateEmployeeList() {
    employeeListElem.innerHTML = '';
    employeeList.forEach((emp, idx) => {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        li.textContent = emp.name;
        const btn = document.createElement('button');
        btn.className = 'btn btn-sm btn-danger';
        btn.textContent = 'Remove';
        btn.onclick = () => {
            employeeList.splice(idx, 1);
            updateEmployeeList();
        };
        li.appendChild(btn);
        employeeListElem.appendChild(li);
    });
    generateBtn.disabled = employeeList.length < 6;
    employeeWarning.style.display = employeeList.length < 6 ? '' : 'none';
}

employeeForm.onsubmit = function(e) {
    e.preventDefault();
    const formData = new FormData(employeeForm);
    const name = document.getElementById('employeeName').value.trim();
    if (!name) {
        showEmployeeError('Employee name cannot be empty.');
        return;
    }
    if (isDuplicateName(name)) {
        showEmployeeError(`Employee with name “${name}” already exists.`);
        return;
    }
    const preferences = {};
    let duplicatePrefError = false;
    DAYS.forEach(day => {
        const first = formData.get(day + '_first');
        const second = formData.get(day + '_second');
        if (first && second && first !== 'none' && second !== 'none' && first === second) {
            duplicatePrefError = true;
        }
        preferences[day] = [first, second];
    });
    if (duplicatePrefError) {
        showEmployeeError('No duplicate preferences allowed for the same day.');
        return;
    }
    employeeList.push({ name, preferences });
    updateEmployeeList();
    employeeForm.reset();
};

generateBtn.onclick = function() {
    if (employeeList.length < 6) {
        showEmployeeError('At least 6 employees are required to generate a valid schedule.');
        return;
    }
    fetch('/api/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employees: employeeList })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showEmployeeError(data.error);
            scheduleContainer.style.display = 'none';
            return;
        }
        renderSchedule(data);
    })
    .catch(() => {
        showEmployeeError('Network or server error.');
        scheduleContainer.style.display = 'none';
    });
};

function renderSchedule(schedule) {
    scheduleContainer.style.display = '';
    // Clear all cells
    for (const row of scheduleTable.tBodies[0].rows) {
        for (let i = 1; i < row.cells.length; ++i) {
            row.cells[i].innerHTML = '-';
        }
    }
    // Fill in schedule
    DAYS.forEach((day, i) => {
        SHIFTS.forEach((shift, j) => {
            const cell = scheduleTable.tBodies[0].rows[i].cells[j+1];
            const emps = schedule[day][shift];
            if (emps && emps.length > 0) {
                cell.innerHTML = emps.map(e => `<div>${e}</div>`).join('');
            }
        });
    });
}

updateEmployeeList(); 