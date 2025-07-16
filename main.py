
# stock_analysis_app.py
import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import date

st.set_page_config(page_title="Options Trade Analyzer", layout="wide")

# Initialize number of stocks in session state
if 'n_stocks' not in st.session_state:
    st.session_state.n_stocks = 1
int()

# Sidebar: portfolio value
port_value = st.sidebar.number_input(
    "Total portfolio value ($)", min_value=0.0, value=10000.0, step=1000.0
)

st.title("🔍 Multi-Stock Options Trade Analyzer")

# Add another stock button
def add_stock():
    st.session_state.n_stocks += 1

st.button("➕ Add another stock", on_click=add_stock)

# Prepare containers for inputs
tickers = []
call1s = []
call2s = []
put1s = []
put2s = []
expiries = []

# Render input columns for each stock
df_inputs = []
cols = st.columns(st.session_state.n_stocks)
for i in range(st.session_state.n_stocks):
    with cols[i]:
        st.markdown(f"**Stock {i+1}**")
        t = st.text_input(f"Ticker {i+1}", key=f"ticker_{i}").upper()
        c1 = st.number_input(f"Call1 BE@EX {i+1}", key=f"c1_{i}")
        c2 = st.number_input(f"Call2 BE@EX {i+1}", key=f"c2_{i}")
        p1 = st.number_input(f"Put1 BE@EX {i+1}", key=f"p1_{i}")
        p2 = st.number_input(f"Put2 BE@EX {i+1}", key=f"p2_{i}")
        exp_date = st.date_input(f"Expiry {i+1}", key=f"exp_{i}")
        df_inputs.append((t, c1, c2, p1, p2, exp_date))

# Analyze button
if st.button("🔎 Analyze Portfolio"):
    results = []
    for t, c1, c2, p1, p2, exp_date in df_inputs:
        if not t:
            continue
        call_avg = (c1 + c2)/2
        put_avg = (p1 + p2)/2
        # price fetch
        tk = yf.Ticker(t)
        try:
            price = tk.fast_info['lastPrice']
        except:
            price = tk.history(period='1d')['Close'].iloc[-1]
        # distances & dir
        call_dist = abs(call_avg - price)
        put_dist  = abs(put_avg  - price)
        direction = 'Short' if call_dist>put_dist else 'Long' if put_dist>call_dist else 'Equal'
        rr = (put_dist/call_dist if direction=='Long' else call_dist/put_dist) if direction!='Equal' else 0
        prob = 1 - (1/rr) if rr>2 else 0
                # volatility (daily vol k)
        hist = yf.download(t, start="2024-01-01", end=date.today().isoformat())
        if not hist.empty:
            k_raw = hist['Close'].pct_change().std()
            try:
                k = float(k_raw)
            except:
                k = k_raw.iloc[0] if hasattr(k_raw, 'iloc') else 0.0
        else:
            k = 0.0

        # TP/SL
        if direction=='Long': sl=price-put_dist*1.2; tp=price+put_dist*0.8
        elif direction=='Short': sl=price+call_dist*1.2; tp=price-call_dist*0.8
        else: sl=tp=price
        dollar_sl, dollar_tp = abs(sl-price), abs(tp-price)
        # time factors
        days = (exp_date - date.today()).days
        time_to_sl = (dollar_sl/price)/k if k>0 else 0
        dtf = days/time_to_sl if time_to_sl>0 else 0
        # expected return
        ex = (dollar_tp*prob)/(dollar_sl*(k/2))*dtf if prob>0 and dollar_sl>0 and k>0 else 0
        results.append({
            'Ticker': t,
            'Price': round(price,2),
            'Direction': direction,
            'Days to Expiry': days,
            'k(daily vol)': round(k,4),
            'Win Prob (%)': round(prob*100,2),
            'TP': round(tp,2),
            'SL': round(sl,2),
            'R:R': round(rr,2),
            'Exp Return': round(ex,4)
        })
    df = pd.DataFrame(results)
    total = df['Exp Return'].sum()
    df['Allocation ($)'] = df['Exp Return']/total*port_value if total>0 else 0
    st.write("---")
    st.write("## Portfolio Analysis")
    st.dataframe(df)

