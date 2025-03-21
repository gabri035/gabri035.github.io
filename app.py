from flask import Flask, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import io
import base64
import statsmodels.api as sm

app = Flask(__name__)

def get_data(ticker_symbol, timeframe):
    """
    Scarica i dati storici da yfinance in base al timeframe scelto.
    Restituisce un DataFrame contenente almeno 80 candele.
    """
    if timeframe == "15min":
        interval = "15m"
        period = "5d"  # sufficiente per ottenere almeno 80 candele intraday
        data = yf.Ticker(ticker_symbol).history(period=period, interval=interval)
        data = data.tail(80)
        return data
    elif timeframe == "1h":
        interval = "60m"
        period = "60d"
        data = yf.Ticker(ticker_symbol).history(period=period, interval=interval)
        data = data.tail(80)
        return data
    elif timeframe == "4h":
        # yfinance non supporta direttamente "4h": scarichiamo dati a 60m e li aggregiamo a 4h (240min)
        interval = "60m"
        period = "90d"
        data = yf.Ticker(ticker_symbol).history(period=period, interval=interval)
        data = data.resample('240min').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        data = data.tail(80)
        return data
    elif timeframe == "daily":
        interval = "1d"
        period = "6mo"
        data = yf.Ticker(ticker_symbol).history(period=period, interval=interval)
        data = data.tail(80)
        return data

@app.route("/templates/index2.html", methods=['POST'])
def calculate():
    # Estrae i dati in POST (assumiamo che vengano inviati in formato JSON)
    data_json = request.get_json()
    ticker_symbol = data_json.get('ticker')
    timeframe = data_json.get('timeframe')
    benchmark_flag = data_json.get('benchmark', False)
    benchmark_symbol = data_json.get('benchmarkTicker') if benchmark_flag else None

    # Scarica i dati per il ticker principale
    try:
        df = get_data(ticker_symbol, timeframe)
        if df.empty:
            return jsonify({'error': 'Nessun dato trovato per il ticker specificato'}), 400
    except Exception as e:
        return jsonify({'error': f'Errore nel download dei dati: {e}'}), 500

    # Genera il grafico candlestick delle ultime 80 candele utilizzando mplfinance
    try:
        fig, ax = plt.subplots(figsize=(8,4))
        mpf.plot(df, type='candle', style='charles', ax=ax, volume=False, show_nontrading=True)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)
    except Exception as e:
        return jsonify({'error': f'Errore nella generazione del grafico: {e}'}), 500

    # Calcola i rendimenti logaritmici e le loro statistiche
    df['Return'] = np.log(df['Close'] / df['Close'].shift(1))
    returns_mean = df['Return'].mean()
    returns_std = df['Return'].std()
    returns_analysis = f"Media dei rendimenti logaritmici: {returns_mean:.4f}<br>Volatilità: {returns_std:.4f}"

    # Analisi di regressione se è stato fornito un benchmark
    regression_result = ""
    if benchmark_flag and benchmark_symbol:
        try:
            benchmark_df = get_data(benchmark_symbol, timeframe)
            if benchmark_df.empty:
                regression_result = "Nessun dato trovato per il benchmark."
            else:
                benchmark_df['Return'] = np.log(benchmark_df['Close'] / benchmark_df['Close'].shift(1))
                # Allinea le serie per data
                df_returns = df['Return'].dropna()
                bm_returns = benchmark_df['Return'].dropna()
                combined = pd.concat([df_returns, bm_returns], axis=1, join='inner')
                combined.columns = ['TickerReturn', 'BenchmarkReturn']
                # Regressione: rendimento ticker come variabile dipendente, benchmark come indipendente
                X = combined['BenchmarkReturn']
                X = sm.add_constant(X)
                y = combined['TickerReturn']
                model = sm.OLS(y, X).fit()
                alpha = model.params['const']
                beta = model.params['BenchmarkReturn']
                regression_result = f"Alpha (costante): {alpha:.4f}<br>Beta: {beta:.4f}"
        except Exception as e:
            regression_result = f"Errore durante l'analisi di regressione: {e}"

    # Crea la risposta HTML con Bootstrap 5
    html_response = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Risultati Analisi per {ticker_symbol}</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
      <div class="container my-5">
        <h1 class="mb-4 text-center">Risultati per {ticker_symbol}</h1>
        <div class="card mb-4">
          <div class="card-header">
            Grafico Candlestick (Ultime 80 candele - {timeframe})
          </div>
          <div class="card-body text-center">
            <img src="data:image/png;base64,{image_base64}" class="img-fluid" alt="Grafico Candlestick">
          </div>
        </div>
        <div class="card mb-4">
          <div class="card-header">
            Analisi dei Rendimenti
          </div>
          <div class="card-body">
            <p>{returns_analysis}</p>
          </div>
        </div>
    """
    if benchmark_flag and benchmark_symbol:
        html_response += f"""
        <div class="card mb-4">
          <div class="card-header">
            Analisi di Regressione (Ticker vs Benchmark: {benchmark_symbol})
          </div>
          <div class="card-body">
            <p>{regression_result}</p>
          </div>
        </div>
        """
    html_response += """
      </div>
    </body>
    </html>
    """

    return html_response

if __name__ == '__main__':
    app.run(debug=True)