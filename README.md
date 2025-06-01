# Employee Shift Scheduler

A web application for managing weekly employee shift schedules, implemented in both **Python (Flask)** and **JavaScript (Node.js/Express)**. The app allows employees to specify their shift preferences (with priority ranking) for each day, and generates a fair, conflict-free schedule that meets all business requirements.

---

## Features
- Add employees one at a time, specifying two ranked shift preferences (or "None") for each day of the week.
- Prevents duplicate employee names and duplicate shift preferences for the same day.
- Enforces all business rules:
  - No employee works more than one shift per day.
  - No employee works more than 5 days per week.
  - At least 2 employees per shift per day.
  - Handles conflicts and fills shifts fairly and deterministically.
- Modern, responsive Bootstrap UI for both input and output.
- Clear error messages and robust validation.
- Works in both Python and JavaScript environments.

---

## How It Works
1. **Input:**
   - Add each employee with their name and two shift preferences for each day (or "None").
   - The UI prevents invalid input and shows errors immediately.
2. **Scheduling:**
   - The backend normalizes preferences, checks for all rubric constraints, and generates a weekly schedule.
   - If a preferred shift is full, the scheduler assigns the employee to another available shift, using fair tie-breaking.
   - If not enough employees are available, the scheduler randomly assigns from those who have not worked 5 days yet, and as a last resort, allows double-shifts.
3. **Output:**
   - The final schedule is displayed in a clear, organized table, showing all assignments per shift and day.

---

## Setup & Usage

### Python (Flask) Version
1. **Install dependencies:**
   ```bash
   cd python_app
   pip install -r requirements.txt
   ```
2. **Run the app:**
   ```bash
   python python_app.py
   ```
3. **Open your browser:**
   - Go to [http://localhost:8080](http://localhost:8080)
4. **Use the UI:**
   - Add employees, set preferences, and generate the schedule.

### JavaScript (Node.js/Express) Version
1. **Install dependencies:**
   ```bash
   cd js_app
   npm install
   ```
2. **Run the app:**
   ```bash
   npm start
   # or
   node app.js
   ```
3. **Open your browser:**
   - Go to [http://localhost:3000](http://localhost:3000)
4. **Use the UI:**
   - Add employees, set preferences, and generate the schedule.

---

## Screenshots
**Add employee form:**
![CleanShot 2025-06-01 at 05 41 04@2x](https://github.com/user-attachments/assets/f23cc812-5ed9-47d4-9adf-b334e81d14c9)
![CleanShot 2025-06-01 at 05 44 57@2x](https://github.com/user-attachments/assets/f60f6aba-929e-4f62-aa8a-0c85963ecf19)
**Error handling:**
![CleanShot 2025-06-01 at 05 42 46@2x](https://github.com/user-attachments/assets/115a77b0-8775-463b-9377-ba0d881a39ad)
![CleanShot 2025-06-01 at 05 44 03@2x](https://github.com/user-attachments/assets/127308fd-0f66-4b3c-a09b-4df864224eab)
**Schedule output:**
![CleanShot 2025-06-01 at 05 46 39@2x](https://github.com/user-attachments/assets/91b4eceb-fd90-4809-97e5-8c6d9c8ac1ea)









---

## Project Structure
```
week4-git/
├── python_app/           # Python Flask app
│   ├── python_app.py
│   ├── scheduler.py
│   ├── requirements.txt
│   ├── templates/
│   └── static/
├── js_app/               # JavaScript/Node.js app
│   ├── app.js
│   ├── package.json
│   ├── templates/
│   └── static/
└── README.md
```

---

## Notes
- Must add at least **6 employees** to generate a valid schedule (2 per shift per day).
- Both versions are functionally equivalent and have matching UIs and logic.

---

## License
MIT License 
