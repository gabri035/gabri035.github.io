from flask import Flask, request, jsonify, render_template
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import io
import base64
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
    result = None
    plot_image = None
    if request.method == 'POST':
        # Estrai i dati dal form
        ticker = request.form.get("ticker", "").upper()  # per convenzione, ticker in maiuscolo
        timeframe = request.form.get("timeframe", "daily")
        
        # Mappatura dei parametri per yfinance in base al timeframe
        if timeframe == "15min":
            period = "5d"
            interval = "15m"
        elif timeframe == "1h":
            period = "60d"
            interval = "60m"
        elif timeframe == "4h":
            period = "60d"
            interval = "240m"  # 4 ore = 240 minuti (controlla che la tua versione di yfinance lo supporti)
        elif timeframe == "daily":
            period = "6mo"
            interval = "1d"
        else:
            period = "6mo"
            interval = "1d"
        
        # Scarica i dati
        data = yf.Ticker(ticker).history(period=period, interval=interval)
        
        if data.empty:
            result = f"Nessun dato trovato per il ticker {ticker}"
        else:
            result = f"Plot per {ticker} con timeframe {timeframe}"
            # Crea il grafico candlestick con mplfinance utilizzando returnfig=True
            fig, axlist = mpf.plot(data, type='candle', style='charles', volume=False, show_nontrading=True, returnfig=True)
            
            # Salva il grafico in un buffer e codificalo in base64
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches='tight')
            buf.seek(0)
            plot_image = base64.b64encode(buf.getvalue()).decode('utf-8')
            plt.close(fig)
            
    return render_template("index2.html", result=result, plot_image=plot_image)


if __name__ == '__main__':
    app.run(debug=True)