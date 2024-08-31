from flask import Flask, render_template, request, jsonfy
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
db = SQLAlchemy(app)
client = Groq(api_key=os.getenv('GROQ_API_KEY'))
df = pd.read_excel('Data.xlsx')
data = df.to_string(index=False)



@app.route("/")
@app.route("/index")
def index():
	return render_template("index.html")

if __name__ == '__main__':
	app.run(debug=True)