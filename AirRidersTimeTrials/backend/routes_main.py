from flask import Blueprint, request, jsonify, render_template, redirect, session
from extensions import db


bp_home = Blueprint('routes', __name__)

@bp_home.route("/", methods=["GET"])
def home():
    return render_template("index.html")