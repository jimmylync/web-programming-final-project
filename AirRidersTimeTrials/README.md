Kirby Air Riders WR Tracker
Database + Backend Setup Guide

This document explains how to build the backend for the Kirby Air Riders Time Trial website, including:

-How to install and configure the MySQL database
-Which tables to create (courses, machines, WR runs, users)
-How to structure API routes that the front-end (index.html + scripts.js) expects
-How to implement a simple login / registration system

1. Requirements

Before starting, make sure you have:

-Backend
- Python (Flask) 
the SQL schema is universal.

Database
MySQL 

Front-end

The existing site files:
index.html
styles.css
scripts.js
images/

2. Create the Database

Open MySQL Workbench or your terminal and run:

CREATE DATABASE air_riders;
USE air_riders;

3. Create Required Tables

These tables match how the front-end fetches course & machine data.

3.1 courses

Stores each Air Ride and Top Ride course.

CREATE TABLE courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_key VARCHAR(64) UNIQUE NOT NULL,   -- e.g., 'floria-fields'
    name VARCHAR(100) NOT NULL,               -- e.g., 'Floria Fields'
    map_icon VARCHAR(255)                     -- path to map image
);

3.2 machines

Each machine (Warp Star, Rex Wheelie, Hop Star, Bull Tank, etc.)

CREATE TABLE machines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(255) NOT NULL                -- image path
);

3.3 users

Login accounts for website users.

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,      -- never store plain passwords
    country_code VARCHAR(5)
);


Passwords must be hashed using bcrypt.

3.4 records

Stores world records for each course + machine.

CREATE TABLE records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    machine_id INT NOT NULL,
    user_id INT NOT NULL,
    wr_time VARCHAR(20) NOT NULL,              -- formatted "1'12\"501"
    date_set DATE NOT NULL,
    lap1 DECIMAL(6,3),
    lap2 DECIMAL(6,3),
    lap3 DECIMAL(6,3),

    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);


This matches what the front-end displays.

4. Populating the Database
4.1 Insert courses

Example:

INSERT INTO courses (course_key, name, map_icon) VALUES
('floria-fields', 'Floria Fields', 'images/mapICONS/Floria_Fields.png'),
('waveflow-waters', 'Waveflow Waters', 'images/mapICONS/Waveflow_Waters.png'),
('flower', 'Flower (Top Ride)', 'images/mapICONS/Flower.png'),
('flow', 'Flow (Top Ride)', 'images/mapICONS/Flow.png');

4.2 Insert machines
INSERT INTO machines (name, icon) VALUES
('Warp Star', 'images/machineICONS/KARs_Warp_Star_Icon.png'),
('Rex Wheelie', 'images/machineICONS/KARs_Rex_Wheelie_Icon.png'),
('Bull Tank', 'images/machineICONS/KARs_Bull_Tank_Icon.png'),
('Hop Star', 'images/machineICONS/KARs_Hop_Star_Icon.png');

5. API Routes (Backend)

The front-end expects JSON responses shaped EXACTLY like this.

Implement routes:

**5.1 GET /api/course/:course_key

Used when clicking a course in the sidebar.

Frontend call
fetch(`/api/course/floria-fields`)

Backend should return
{
  "name": "Floria Fields",
  "mapIcon": "images/mapICONS/Floria_Fields.png",
  "summary": {
    "totalMachineWrs": 18,
    "uniquePlayers": 7,
    "uniqueNations": 4,
    "uniqueMachines": 18
  },
  "currentMachineWrs": [
    {
      "machineName": "Warp Star",
      "machineIcon": "images/machineICONS/KARs_Warp_Star_Icon.png",
      "date": "2025-09-12",
      "time": "1'12\"501",
      "player": "petal",
      "nationCode": "us",
      "days": 20,
      "lap1": 23.5,
      "lap2": 24.0,
      "lap3": 25.0,
      "charIcon": "images/charICONS/KARs_Kirby_icon.png",
      "charAlt": "Kirby"
    }
  ],
  "statsByPlayer": [...],
  "statsByMachine": [...],
  "statsByNation": [...],
  "history": [...]
}


Your backend must:

Look up the course by course_key

Join its machines and WR records

Format the JSON exactly like above

6. Login System

A simple 3-file system:

6.1 login.html

A form:

<form action="/login" method="POST">
  <input type="text" name="username" placeholder="Username" required />
  <input type="password" name="password" placeholder="Password" required />
  <button type="submit">Log In</button>
</form>

6.2 Backend Route: POST /login
Pseudocode
1. Receive username + password
2. Look up user in MySQL:
     SELECT * FROM users WHERE username = ?
3. If no user → return error
4. Use bcrypt.compare() to check password
5. If correct:
      - create a session token (cookie)
      - redirect to homepage
6. Else:
      - show "invalid login"

Example in Node.js (Express)
const bcrypt = require("bcrypt");

app.post("/login", async (req, res) => {
  const { username, password } = req.body;

  const [rows] = await db.execute("SELECT * FROM users WHERE username = ?", [username]);
  if (rows.length === 0) return res.send("User not found");

  const user = rows[0];
  const valid = await bcrypt.compare(password, user.password_hash);

  if (!valid) return res.send("Incorrect password");

  req.session.userId = user.id;
  res.redirect("/");
});

6.3 Registration Route
POST /register

Pseudocode:

1. Receive username + password
2. Hash password using bcrypt.hash()
3. Insert new user into DB:
     INSERT INTO users (username, password_hash) VALUES (?, ?)


Password hashing example:

const hash = await bcrypt.hash(password, 10);

7. How the Front-End Connects to the Backend
scripts.js does:
fetch(`/api/course/${courseId}`)
  .then(res => res.json())
  .then(data => renderCourse(data));


So your backend must serve:

/api/course/floria-fields
/api/course/waveflow-waters
/api/course/flower
/api/course/flow
...and so on


Each returns a JSON object with:

course info

WR records

stats

history

8. Folder Structure
project/
│ index.html
│ styles.css
│ scripts.js
│ README.md
│
├── backend/
│   ├── app.js          (or server.py / index.php)
│   ├── db.js
│   └── routes/
│       └── api.js
│
├── images/
│   ├── machineICONS/
│   ├── mapICONS/
│   ├── charICONS/
    ├── country-flags-main/
│   └── logos/

9. Next Steps for the Group
Everyone should follow these tasks:
Member	Task
Front-end	Add all 27 course icons + images
Back-end	Build /api/course/:id DB query
Security	Build login + register routes
Database	Populate machines, courses, and test WRs
QA	Ensure JSON matches scripts.js expectations

11. Machine, Character, and Flag Integration Guide
11.1 Machines & Characters — IMPORTANT

All machines and characters used in the website must match the filenames inside the images/ folder.

Tell your team:

How to confirm names

Open the project folder

View these directories:

images/machineICONS/
images/charICONS/

Example machine files
KARs_Warp_Star_Icon.png
KARs_Rex_Wheelie_Icon.png
KARs_Bull_Tank_Icon.png
KARs_Hop_Star_Icon.png


Machine names for the database should match these filenames (minus the prefix):

File Name	Machine Name for DB
KARs_Warp_Star_Icon.png	Warp Star
KARs_Rex_Wheelie_Icon.png	Rex Wheelie
KARs_Bull_Tank_Icon.png	Bull Tank
KARs_Hop_Star_Icon.png	Hop Star

Example character files
KARs_Kirby_icon.png
KARs_Marx_icon.png
KARs_Taranza_icon.png
KARs_Meta_Knight_icon.png


Use Kirby, Marx, Taranza, Meta Knight, etc.

Why this matters

The frontend expects you to return JSON fields like:

{
  "machineIcon": "images/machineICONS/KARs_Rex_Wheelie_Icon.png",
  "charIcon": "images/charICONS/KARs_Marx_icon.png"
}


If filenames don’t match, images won’t load.

11.2 Implementing Country Flags

We are using the open-source flag pack made by Hampus Borgos:

Link:
https://hampusborgos.github.io/country-flags/

Inside our project, we include the SVG pack:

images/country-flags-main/svg/

 How it works

Every flag is named after its ISO 3166-1 alpha-2 code, for example:

Country	Code	File
United States	us	us.svg
Japan	jp	jp.svg
Canada	ca	ca.svg
Mexico	mx	mx.svg
How to use in the frontend

The WR tables already load flags like this:

<img src="images/country-flags-main/svg/us.svg" alt="USA" class="flag" />

 How to store this in the database

In the users table, add:

country_code VARCHAR(5)


Example values:

us
jp
ca
mx


When returning WR JSON, send:

{
  "nationCode": "jp"
}


The frontend automatically displays the correct flag using:

<img src="images/country-flags-main/svg/${row.nationCode}.svg">

11.3 How to assign flags in new WR entries

When adding new WR entries via your backend:

A player from the U.S. → "nationCode": "us"

A player from Japan → "nationCode": "jp"

A player from France → "nationCode": "fr"

This ensures correct rendering in all pages.

11.4 Summary for the Team

Please ensure the following:

Machines & characters must match the image filenames

Check images/machineICONS/ and images/charICONS/ before adding new data.

Country flags must use ISO 3166-1 two-letter codes

Make sure DB entries use lowercase codes ("us", "jp", "ca").
The frontend will auto-load the correct flag SVG.

All images follow this structure:
images/
    machineICONS/
    charICONS/
    mapICONS/
    logos/
    country-flags-main/