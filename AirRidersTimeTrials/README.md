Kirby Air Riders WR Tracker
Made by: Tahir Peele, Jimmy Lynch, Aidan McNamara

Make sure you first do:
pip install flask flask-sqlalchemy flask-marshmallow marshmallow-sqlalchemy flask-jwt-extended flask-cors werkzeug faker

To run, enter into your terminal: python backend/app.py
-If you get a "no such file or directory error", try running this instead: python AirRidersTimeTrials\backend\app.py

Once it is running, paste this into the browser: http://127.0.0.1:5000/



--Note for developers--
If you need to change styles.css, do this after you make changes to the file:

-Run this in the terminal to install tailwind (if you haven't installed it in this project yet):
npm install tailwindcss @tailwindcss/cli
  (https://tailwindcss.com/docs/installation/tailwind-cli)

-Then run this in the terminal:
npx @tailwindcss/cli -i AirRidersTimeTrials\static\styles.css -o AirRidersTimeTrials\static\compiledStyles.css --watch

-any changes that you made to styles.css should be compiled and good to go!
