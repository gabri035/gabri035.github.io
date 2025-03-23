from flask import Flask, request, render_template
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Backend non interattivo
import matplotlib.pyplot as plt
import mplfinance as mpf
import io
import base64
from scipy.stats import norm, shapiro, jarque_bera, skew, kurtosis
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

@app.route("/pricing")
def pricing():
    return render_template("pricing.html")

@app.route("/strategie")
def strategie():
    return render_template("strategie.html")


        
@app.route("/index2", methods=['GET', 'POST'])
def index2():
    result = None
    candle_image = None
    dist_image = None
    dist_caption = None
    
    
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
        
        data = yf.Ticker(ticker).history(period=period, interval=interval)
        
        if data.empty:
            result = f"Nessun dato trovato per il ticker {ticker}"
        else:
            result = f"Grafici per {ticker} con timeframe {timeframe}"
            
            ## Grafico a candele
            # Creiamo il grafico a candele in una figura separata (lasciamo che mpf.plot crei la figura)
            fig_candle, _ = mpf.plot(data, type='candle', style='charles', volume=True,
                                     show_nontrading=False, returnfig=True, figsize=(8, 4))
            buf_temp = io.BytesIO()
            fig_candle.savefig(buf_temp, format="png", bbox_inches='tight')
            buf_temp.seek(0)
            candle_image = base64.b64encode(buf_temp.getvalue()).decode('utf-8')
            plt.close(fig_candle)
            
            ## Grafico della distribuzione dei rendimenti
            # Calcola i log-rendimenti
            returns = np.log(data['Close'] / data['Close'].shift(1)).dropna()
            # Calcola i parametri della distribuzione
            mu = returns.mean()
            sigma = returns.std()
            skewness = skew(returns)
            kurt = kurtosis(returns)
            shapiro_stat, shapiro_p = shapiro(returns)
            jb_stat, jb_p = jarque_bera(returns)
            
            # Prepara il range per la curva normale
            x = np.linspace(returns.min(), returns.max(), 100)
            pdf = norm.pdf(x, loc=mu, scale=sigma)
            
            # Crea il grafico: istogramma + curva normale
            fig_dist, ax = plt.subplots(figsize=(8, 4))
            n, bins, patches = ax.hist(returns, bins=30, density=True, alpha=0.6,
                                         color='skyblue', edgecolor='black', label='Empirica')
            ax.plot(x, pdf, 'r--', linewidth=2, label='Normale')
            ax.set_title("Distribuzione dei Rendimenti")
            ax.set_xlabel("Rendimento")
            ax.set_ylabel("Densità")
            ax.legend()
            
            buf2 = io.BytesIO()
            fig_dist.savefig(buf2, format="png", bbox_inches='tight')
            buf2.seek(0)
            dist_image = base64.b64encode(buf2.getvalue()).decode('utf-8')
            plt.close(fig_dist)
            
            # Prepara la didascalia per il grafico della distribuzione
            dist_caption = (
                f"Media: {mu:.4f}<br>"
                f"Deviazione Standard: {sigma:.4f}<br>"
                f"Skewness: {skewness:.4f}<br>"
                f"Curtosi: {kurt:.4f}<br>"
                f"Test di Shapiro-Wilk: stat={shapiro_stat:.4f}, p={shapiro_p:.4f}<br>"
                f"Test di Jarque-Bera: stat={jb_stat:.4f}, p={jb_p:.4f}"
            )
            
    return render_template("index2.html", result=result, candle_image=candle_image,
                           dist_image=dist_image, dist_caption=dist_caption)





def generate_payoff_chart(strike, optionType, tradeType):
    """
    Genera un grafico del payoff a scadenza.
    Per una call: payoff = max(S - strike, 0)
    Per una put: payoff = max(strike - S, 0)
    Se l'operazione è 'sell', il payoff viene invertito.
    """
    # Definiamo una gamma di prezzi del sottostante
    prices = np.linspace(strike * 0.5, strike * 1.5, 100)
    if optionType.lower() == 'call':
        payoff = np.maximum(prices - strike, 0)
    else:
        payoff = np.maximum(strike - prices, 0)
    
    # Se l'operazione è vendita, inverto il payoff
    if tradeType.lower() == 'sell':
        payoff = -payoff

    # Creazione del grafico
    fig, ax = plt.subplots()
    ax.plot(prices, payoff, label=f"{optionType.capitalize()} Payoff")
    ax.axhline(0, color='black', lw=0.5)
    ax.set_title('Payoff a Scadenza')
    ax.set_xlabel('Prezzo Sottostante')
    ax.set_ylabel('Payoff')
    ax.legend()

    # Converto il grafico in immagine Base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_payoff = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_payoff

def generate_atnow_chart(underlying, strike, days, vol, optionType, tradeType):
    """
    Genera un grafico dummy per il "Valore At Now" (valutazione attuale dell'opzione).
    Qui viene usata una funzione esponenziale decrescente per simulare la decadenza del valore,
    moltiplicata per il payoff intrinseco.
    """
    # Calcolo del tempo in anni (dummy)
    t = np.linspace(0, days / 365, 100)
    # Calcolo del payoff intrinseco al tempo zero
    if optionType.lower() == 'call':
        intrinsic = max(underlying - strike, 0)
    else:
        intrinsic = max(strike - underlying, 0)
    # Funzione dummy per il prezzo: decrescita esponenziale
    price = np.exp(-t) * intrinsic
    if tradeType.lower() == 'sell':
        price = -price

    fig, ax = plt.subplots()
    ax.plot(t * 365, price, label='Valore At Now')
    ax.set_title('Valore At Now (dummy)')
    ax.set_xlabel('Giorni')
    ax.set_ylabel('Prezzo Opzione')
    ax.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_atnow = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_atnow

@app.route('/option_calculator', methods=['GET', 'POST'])
def option_calculator():
    if request.method == 'POST':
        # Recupero dei dati dal form
        underlying_input = request.form.get('underlying')
        try:
            # Proviamo a convertire il sottostante in valore numerico (dummy)
            underlying_val = float(underlying_input)
        except (ValueError, TypeError):
            # Se non è possibile, usiamo un valore default
            underlying_val = 100.0

        strike = float(request.form.get('strike'))
        days = int(request.form.get('days'))
        vol = float(request.form.get('vol'))
        optionType = request.form.get('optionType')
        tradeType = request.form.get('tradeType')

        # Generazione dei grafici
        payoff_image = generate_payoff_chart(strike, optionType, tradeType)
        atnow_image = generate_atnow_chart(underlying_val, strike, days, vol, optionType, tradeType)

        # Renderizza il template passando le immagini generate
        return render_template(
            '/pricing.html',
            payoff_image=payoff_image,
            atnow_image=atnow_image
        )
    # Per GET visualizziamo semplicemente il form
    return render_template('/pricing.html')


if __name__ == '__main__':
    app.run(debug=True) 