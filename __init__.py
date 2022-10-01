from flask import Flask, render_template, redirect, session
from flask import request
from flask_session import Session
from datetime import timedelta
import sqlite3

app = Flask('Flask Lab')