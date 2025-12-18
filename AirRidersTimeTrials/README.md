Kirby Air Riders WR Tracker

Make sure you do

pip install flask flask-sqlalchemy flask-marshmallow marshmallow-sqlalchemy flask-jwt-extended flask-cors werkzeug faker

to run you will need 2 terminals

One will run: python backend/app.py
  -I was getting a "no such file or directory error"
  -Ended up needing to instead run: python AirRidersTimeTrials\backend\app.py

the other will run: python -m http.server 5500

after they are running paste both of these into browser http://127.0.0.1:5500/ and http://127.0.0.1:5000/

What if I instead paste this: http://127.0.0.1:5500/AirRidersTimeTrials/ and http://127.0.0.1:5000/AirRidersTimeTrials/




If you need to change styles.css, do this after you make changes to the file:

-Run this in the terminal to install tailwind (if you haven't installed it in this project yet):
npm install tailwindcss @tailwindcss/cli
  (https://tailwindcss.com/docs/installation/tailwind-cli)

-Then run this in the terminal:
npx @tailwindcss/cli -i AirRidersTimeTrials\static\styles.css -o AirRidersTimeTrials\static\compiledStyles.css --watch

-any changes that you made to styles.css should be compiled and good to go!
