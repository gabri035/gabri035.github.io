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
    if request.method == 'POST':
        # Estrae i dati in POST
        ticker = request.form.get('ticker', '').lower()
        # Puoi aggiungere qui ulteriori elaborazioni, ad esempio scaricare dati, generare grafici, ecc.
        # Creazione della risposta HTML con Bootstrap 5
        html_fragment = f"""
        <div class="alert alert-success text-center">
          <h2>{ticker}!</h2>
        </div>
        """
        # Puoi anche includere una risposta JSON se necessario, ad esempio:
        # return jsonify({'ticker': ticker, 'message': f'Analisi per {ticker}'})
        return html_fragment
    else:
        # Se il metodo è GET, restituisce la pagina HTML index2.html
        return render_template("index2.html")
if __name__ == '__main__':
    app.run(debug=True)