# Database Lab 2 — Login & To-Do Application

A Flask + MySQL implementation of the Lab 2 requirements. Work alone or with your partner and make sure you understand every part before submitting.

## Team
- Member 1: **Replace with your name and student ID** — **Describe contribution**
- Member 2 (if applicable): **Replace with name and student ID** — **Describe contribution**

## Technology
- Front end: HTML, CSS, JavaScript
- Back end: Python 3 + Flask
- Database: MySQL; direct SQL with parameterized queries (no ORM)

## Requirements
- Register and login, logout, duplicate-email handling and generic invalid-login message
- Bcrypt password hashes; session-based authentication
- Per-user private to-do list, newest first
- Add, edit, mark done/not done, delete with confirmation
- Browser-side and server-side validation
- Responsive styling

## Setup from an empty machine (macOS)
1. Install Python 3 and MySQL Server.
2. Open Terminal in this folder.
3. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
4. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
5. Create a local environment file:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your local MySQL credentials and a long random `SESSION_SECRET`.
6. Run the schema in MySQL Workbench or Terminal:
   ```bash
   mysql -u root -p < database/schema.sql
   ```
   The script drops and recreates `registration`, so it deletes any existing database with that name.
7. Start the app:
   ```bash
   python app.py
   ```
8. Open `http://127.0.0.1:5000` in your browser.

## Screenshots to add before submission
Add at least four real screenshots under `screenshots/` and reference them here:
1. Register form showing validation errors
2. Login page
3. To-do list with several tasks, including one completed
4. The site in a phone-sized viewport

## Required written answers
**(a) Why do UPDATE and DELETE contain `AND user_id = ?`, and what changes if removed?**  
The task ID comes from the browser and could refer to another user's task. Checking both the task ID and the logged-in user's ID prevents changing or deleting a task owned by someone else. Without the user ID condition, a user who obtains another task's ID could change or delete that task.

**(b) What happens if a to-do is inserted for a `user_id` that does not exist, and which constraint is that?**  
MySQL rejects the insert because the `user_id` value does not reference an existing row in `users`. This is the foreign-key constraint (referential integrity).

**(c) Why store a hash and not the password?**  
A password hash avoids storing the original password in readable form. During login, the entered password is checked against the stored bcrypt hash.

**(d) The name column is NOT NULL: why is a separate check needed for an empty name?**  
`NOT NULL` prevents SQL NULL values, but an empty string is still a non-NULL value. Application validation must reject empty or whitespace-only names.

## Security notes
- `.env` contains secrets and must never be committed. `.env.example` should contain fake/example values only.
- SQL values are passed separately as parameters.
- The user ID for task operations comes from the server-side session, never from a form.
- The development server uses `debug=True`; disable debug mode for any public deployment.

## Test checklist
- Register with empty fields and with mismatched passwords.
- Register the same email twice; expect `Email Already Exists`.
- Wrong email and wrong password both show `Invalid email or password`.
- Open `/todos` while logged out; it redirects to login.
- Log in as two users in separate browsers and verify task privacy.
- Try an email like `' OR '1'='1' --`; it must not log you in.
- Verify the database stores bcrypt hashes, not raw passwords.
