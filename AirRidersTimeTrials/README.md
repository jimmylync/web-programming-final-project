Kirby Air Riders WR Tracker

Make sure you do

pip install flask flask-sqlalchemy flask-marshmallow marshmallow-sqlalchemy flask-jwt-extended flask-cors werkzeug faker

to run you will need 2 terminals

One will run: python backend/app.py
  -I was getting a "no such file or directory error"
  -Ended up needing to instead run: python AirRidersTimeTrials\backend\app.py

the other will run: python -m http.server 5500

after they are running paste this into browser http://127.0.0.1:5500/

What if I instead paste this: http://127.0.0.1:5500/AirRidersTimeTrials/