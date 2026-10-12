# Database Lab 2 - Login & To-Do Application

A Flask + MySQL web application: sign-up, login and a personal to-do list.

## 1. Team

| Name | ID | Contribution |
|---|---|---|
| Omar Abdelkareem | 2304060 | Worked alone: database, back end, front end, README |

## 2. Technology

- Back end: Python 3 + Flask
- Front end: HTML (Jinja templates), CSS (own style, no framework), JavaScript
- Database: MySQL, database `registration`; plain SQL with parameters (mysql-connector-python), no ORM
- Passwords: bcrypt hashes; login state: Flask session (server-side check on every private page)

## 3. How to run it (from an empty machine, macOS)

1. Install Python 3 and MySQL Server.
2. Get the code and open a Terminal in its folder:

        git clone https://github.com/omarabdelkareem99/db-lab2-omar.git
        cd db-lab2-omar

3. Create and activate a virtual environment, then install the packages:

        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt

4. Create the database (this DROPS and recreates `registration`):

        mysql -u root -p < database/schema.sql

5. Create your local settings file and edit it (MySQL password, a long random SESSION_SECRET):

        cp .env.example .env

6. Start the server and open http://127.0.0.1:5000

        python app.py

## 4. Features

| # | Requirement | Done |
|---|---|---|
| R1 | Register (name, e-mail, password, confirm); duplicate e-mail shows `Email Already Exists`; user is logged in afterwards | yes |
| R2 | Login; wrong e-mail and wrong password give the same `Invalid email or password`; logout ends the session | yes |
| R3 | The list is private; visitors are redirected to the login page; each user sees only their own to-dos, newest first | yes |
| R4-R7 | Add, edit title, mark done / not done, delete (with an "are you sure?" question) | yes |
| R8 | Validation in the browser (JavaScript) and again on the server, with the exact messages of the lab | yes |
| R9 | bcrypt hashes; only the given queries, always with parameters; user_id always from the session | yes |
| R10 | One consistent black-and-white style, responsive (phone and laptop), error messages near the fields, visible done state, friendly empty-list text, name and logout button, animated background and a welcome message | yes |

## 5. Extra (not required by the lab): password reset by e-mail

A "Forgot password?" link on the login page sends a 4-digit code to the user's e-mail (valid 10 minutes, 5 attempts, stored only as an HMAC hash), then lets the user choose a new password. It needs one extra table and Gmail SMTP settings:

- run `database/extras_password_reset.sql` after `schema.sql`
- fill the `MAIL_*` values in `.env` (a Gmail App Password, never the real password)

The rest of the application works without it. `database/schema.sql` contains only the two tables required by the lab.

## 6. Screenshots

1. Register page with error messages: ![register](screenshots/register.png)
2. Login page: ![login](screenshots/login.png)
3. List with several to-dos (one done): ![list](screenshots/list.png)
4. Phone-sized window: ![mobile](screenshots/mobile.png)

## 7. Answers

**(a) Why do UPDATE and DELETE contain `AND user_id = ?`, and what changes if you remove it?**
The id of a to-do comes from the browser, so anybody can send somebody else's number. With `AND user_id = ?` (taken from the session) the statement changes zero rows when the to-do is not yours. Without it, any logged-in user could edit, mark or delete other users' to-dos just by guessing or changing the number.

**(b) What happens if you insert a to-do for a user_id that does not exist, and which constraint is that?**
MySQL rejects the INSERT with error 1452 (a foreign key constraint fails), because there is no row in `users` with that user_id. This is the foreign-key constraint, i.e. referential integrity.

**(c) Why do you store a hash and not the password?**
If the database leaks, the passwords must not be readable. A bcrypt hash is one-way, salted (equal passwords give different hashes) and slow on purpose, so it cannot be reversed and is expensive to guess. At login the typed password is compared with the stored hash by the library.

**(d) The name column is NOT NULL: why did you still need your own check for an empty name?**
NOT NULL only refuses the value NULL. An empty text '' (or only spaces) is a value, so MySQL accepts it. Only the application's own check (browser and server) can refuse an empty name.

## 8. Self-check done

- Open /todos without logging in: redirected to the login page.
- Register with empty fields: one message per empty field; same messages from the server.
- Same e-mail twice: `Email Already Exists`.
- Wrong password and unknown e-mail: the same `Invalid email or password`.
- A login e-mail like ' OR '1'='1' --: not logged in.
- Two users in two browsers: each sees only their own to-dos.
- `SELECT password_hash FROM users`: only values like $2b$12$...

## 9. Security notes

- `.env` is in `.gitignore` and is never committed; `.env.example` has fake values only.
- Every SQL value is passed as a parameter.
- Debug mode is off (`debug=False`), so no stack traces are shown.
