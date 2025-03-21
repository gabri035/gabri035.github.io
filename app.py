from flask import Flask, render_template, request, jsonify, url_for
import numpy as np
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index.html')
def home():
    return render_template('index.html')

@app.route('/index1.html')
def payoff_page():
    return render_template('index1.html')

@app.route('/index2.html')
def about():
    return render_template('index2.html')

from flask import send_from_directory

@app.route('/image/<path:filename>')
def image(filename):
    return send_from_directory('image', filename)

@app.route('/generate_payoff', methods=['POST'])
def generate_payoff():
    S = float(request.form['S'])
    K = float(request.form['K'])
    option_price = float(request.form['X'])

    # Calcolo Payoff Call
    S_range = np.linspace(S * 0.75, S * 1.25, 100)
    payoff = np.maximum(S_range - K, 0) - option_price

    # Plot del payoff
    plt.figure(figsize=(8,5))
    plt.plot(S_range, payoff, linewidth=2, label='Payoff a scadenza')
    plt.axhline(0, color='black', linewidth=0.8)
    plt.axvline(K, color='grey', linestyle='--', label='Strike Price (K)')
    plt.xlabel('Prezzo del sottostante a scadenza')
    plt.ylabel('Profit/Loss')
    plt.title('Grafico Payoff a Scadenza')
    plt.legend()
    plt.grid(True)

    image_path = os.path.join('image', 'payoff.png')
    plt.savefig(image_path)
    plt.close()

    if S > K + option_price:
        commento = "L'opzione è già In The Money (ITM), alta probabilità di profitto."
    elif K < S <= K + option_price:
        commento = "L'opzione è leggermente In The Money, break-even vicino."
    elif S == K:
        commento = "Prezzo del sottostante uguale allo strike, situazione ATM."
    else:
        commento = "L'opzione è Out of The Money (OTM), rischio più elevato."

    
    return jsonify({'image_url': url_for('image', filename='payoff'), 'analisi':commento})

if __name__ == '__main__':
    app.run(debug=True)