from flask import Flask, request, jsonify, render_template
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")
  
@app.route("/index")
def callz():
    return render_template("index.html")

@app.route("/index1")
def chisiamo_page():
    return render_template("index1.html")

@app.route("/index2", methods=['GET', 'POST'])
def index2():
    result=None
    if request.method == 'POST':
        result=int(request.form.get("ticker","0"))
        print(result)
        # Se il metodo è GET, restituisce la pagina HTML index2.html
    return render_template("index2.html", result=result)

if __name__ == '__main__':
    app.run(debug=True)