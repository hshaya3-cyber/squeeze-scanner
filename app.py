#!/usr/bin/env python3
"""
TTM SQUEEZE MULTI-TIMEFRAME SCANNER — Streamlit Web App
Scans: Daily | 4H | 1H | 30min | 10min | 5min

Deploy free on Streamlit Community Cloud (streamlit.io)
"""

import time, warnings
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st

warnings.filterwarnings('ignore')

# ─── PAGE CONFIG ───
st.set_page_config(
    page_title="TTM Squeeze Scanner",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM STYLING ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Outfit:wght@300;400;600;700&display=swap');

    /* Root theme */
    :root {
        --bg-primary: #0a0e17;
        --bg-card: #111827;
        --bg-hover: #1a2235;
        --cyan: #00d4ff;
        --orange: #ff6b35;
        --green: #34d399;
        --red: #ef4444;
        --gold: #fbbf24;
        --muted: #6b7280;
        --text: #e5e7eb;
    }

    .stApp { background-color: var(--bg-primary); }

    /* Title bar */
    .scanner-title {
        font-family: 'Outfit', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #00d4ff;
        letter-spacing: -0.5px;
        margin-bottom: 0;
        line-height: 1.2;
    }
    .scanner-subtitle {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #6b7280;
        letter-spacing: 1px;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #111827 0%, #1a2235 100%);
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        text-align: center;
    }
    .metric-value {
        font-family: 'Outfit', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .metric-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-top: 4px;
    }

    /* Squeeze badge styles */
    .sq-fired {
        background: linear-gradient(135deg, #ff6b35, #f97316);
        color: white; font-weight: 700; padding: 4px 10px;
        border-radius: 6px; display: inline-block; font-size: 0.85rem;
        font-family: 'JetBrains Mono', monospace;
        animation: pulse-fire 1.5s ease-in-out infinite;
    }
    .sq-bullish {
        background: linear-gradient(135deg, #059669, #34d399);
        color: white; font-weight: 700; padding: 4px 10px;
        border-radius: 6px; display: inline-block; font-size: 0.85rem;
        font-family: 'JetBrains Mono', monospace;
    }
    .sq-on {
        background: linear-gradient(135deg, #0284c7, #00d4ff);
        color: #0a0e17; font-weight: 700; padding: 4px 10px;
        border-radius: 6px; display: inline-block; font-size: 0.85rem;
        font-family: 'JetBrains Mono', monospace;
    }
    .sq-none {
        background: #1f2937; color: #4b5563;
        padding: 4px 10px; border-radius: 6px;
        display: inline-block; font-size: 0.85rem;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Momentum badges */
    .mom-strong { color: #34d399; font-weight: 700; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; }
    .mom-pos { color: #00d4ff; font-weight: 600; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; }
    .mom-rise { color: #fbbf24; font-weight: 600; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; }
    .mom-neg { color: #ef4444; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; }

    /* Score badge */
    .score-high { color: #34d399; font-weight: 700; font-size: 1.3rem; font-family: 'Outfit', sans-serif; }
    .score-mid { color: #00d4ff; font-weight: 600; font-size: 1.3rem; font-family: 'Outfit', sans-serif; }
    .score-low { color: #6b7280; font-size: 1.3rem; font-family: 'Outfit', sans-serif; }

    /* Action badges */
    .action-strong-buy {
        background: linear-gradient(135deg, #059669, #34d399);
        color: white; font-weight: 700; padding: 5px 12px;
        border-radius: 8px; display: inline-block; font-size: 0.8rem;
        font-family: 'JetBrains Mono', monospace;
    }
    .action-bullish {
        background: linear-gradient(135deg, #0284c7, #00d4ff);
        color: #0a0e17; font-weight: 700; padding: 5px 12px;
        border-radius: 8px; display: inline-block; font-size: 0.8rem;
        font-family: 'JetBrains Mono', monospace;
    }
    .action-fired {
        background: linear-gradient(135deg, #d97706, #fbbf24);
        color: #0a0e17; font-weight: 700; padding: 5px 12px;
        border-radius: 8px; display: inline-block; font-size: 0.8rem;
        font-family: 'JetBrains Mono', monospace;
    }
    .action-watch {
        background: #1f2937; color: #9ca3af;
        padding: 5px 12px; border-radius: 8px;
        display: inline-block; font-size: 0.8rem;
        font-family: 'JetBrains Mono', monospace;
    }

    @keyframes pulse-fire {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Ticker name */
    .ticker-name {
        font-family: 'Outfit', sans-serif;
        font-weight: 700; font-size: 1.1rem; color: #e5e7eb;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }

    /* Table container */
    .results-table {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 1rem;
        overflow-x: auto;
    }

    /* Progress bar custom */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #00d4ff, #34d399);
    }
</style>
""", unsafe_allow_html=True)


# ─── TTM SQUEEZE ENGINE (identical to your original) ───

def calc_sma(s, p):
    return s.rolling(window=p).mean()

def calc_ema(s, p):
    return s.ewm(span=p, adjust=False).mean()

def calc_atr(high, low, close, period=20):
    tr = pd.concat([
        high - low,
        abs(high - close.shift(1)),
        abs(low - close.shift(1))
    ], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calc_linreg(series, period):
    vals = []
    arr = series.values
    for i in range(len(arr)):
        if i < period - 1:
            vals.append(np.nan)
            continue
        y = arr[i - period + 1:i + 1]
        if np.any(np.isnan(y)):
            vals.append(np.nan)
            continue
        x = np.arange(period, dtype=float)
        n = period
        sx, sy = x.sum(), y.sum()
        sxy, sx2 = (x * y).sum(), (x * x).sum()
        d = n * sx2 - sx * sx
        if d == 0:
            vals.append(np.nan)
            continue
        slope = (n * sxy - sx * sy) / d
        intercept = (sy - slope * sx) / n
        vals.append(intercept + slope * (n - 1))
    return pd.Series(vals, index=series.index)

def calculate_ttm_squeeze(df, bb_len=20, bb_mult=2.0, kc_len=20, kc_mult=1.5, mom_len=20):
    if df is None or len(df) < max(bb_len, kc_len, mom_len) + 10:
        return None

    c = df['Close'].astype(float)
    h = df['High'].astype(float)
    l = df['Low'].astype(float)

    bb_mid = calc_sma(c, bb_len)
    bb_std = c.rolling(window=bb_len).std()
    bb_upper = bb_mid + bb_mult * bb_std
    bb_lower = bb_mid - bb_mult * bb_std

    kc_mid = calc_ema(c, kc_len)
    atr = calc_atr(h, l, c, kc_len)
    kc_upper = kc_mid + kc_mult * atr
    kc_lower = kc_mid - kc_mult * atr

    squeeze_on = (bb_lower > kc_lower) & (bb_upper < kc_upper)

    hh = h.rolling(window=kc_len).max()
    ll = l.rolling(window=kc_len).min()
    delta = c - (((hh + ll) / 2 + calc_sma(c, kc_len)) / 2)
    momentum = calc_linreg(delta, mom_len)

    sq = bool(squeeze_on.iloc[-1]) if pd.notna(squeeze_on.iloc[-1]) else False
    mv = float(momentum.iloc[-1]) if pd.notna(momentum.iloc[-1]) else 0.0
    pm = float(momentum.iloc[-2]) if len(momentum) > 1 and pd.notna(momentum.iloc[-2]) else 0.0
    mi = mv > pm

    sc = 0
    for i in range(len(squeeze_on) - 1, -1, -1):
        if pd.notna(squeeze_on.iloc[i]) and squeeze_on.iloc[i]:
            sc += 1
        else:
            break

    fired = (not sq and sc == 0 and len(squeeze_on) > 2
             and pd.notna(squeeze_on.iloc[-2]) and squeeze_on.iloc[-2])

    return {
        'squeeze_on': sq,
        'just_fired': fired,
        'momentum': mv,
        'momentum_increasing': mi,
        'momentum_positive': mv > 0,
        'squeeze_bars': sc,
        'bullish_setup': sq and (mv > 0 or mi)
    }


# ─── DATA FETCHING ───

TF_CONFIG = {
    'Daily':  {'interval': '1d', 'period': '6mo', 'min_bars': 60},
    '4H':     {'interval': '1h', 'period': '60d', 'min_bars': 200, 'resample': '4h'},
    '1H':     {'interval': '1h', 'period': '60d', 'min_bars': 60},
    '30min':  {'interval': '30m', 'period': '60d', 'min_bars': 60},
    '10min':  {'interval': '5m', 'period': '60d', 'min_bars': 60, 'resample': '10min'},
    '5min':   {'interval': '5m', 'period': '60d', 'min_bars': 60},
}

TIMEFRAME_LIST = list(TF_CONFIG.keys())

def fetch_tf(sym, tf_config, retries=3):
    for att in range(retries):
        try:
            df = yf.Ticker(sym).history(
                period=tf_config['period'],
                interval=tf_config['interval'],
                auto_adjust=True
            )
            if df is None or df.empty:
                time.sleep(1)
                continue
            if 'resample' in tf_config:
                df = df.resample(tf_config['resample']).agg({
                    'Open': 'first', 'High': 'max',
                    'Low': 'min', 'Close': 'last', 'Volume': 'sum'
                }).dropna()
            if df is not None and len(df) >= 30:
                return df
            time.sleep(1)
        except Exception:
            time.sleep(1.5)
    return None

def scan_stock(sym):
    res = {'ticker': sym}
    for tf, cfg in TF_CONFIG.items():
        try:
            df = fetch_tf(sym, cfg)
            sq = calculate_ttm_squeeze(df) if df is not None and len(df) >= 30 else None
            res[tf] = sq if sq else {'error': 'No data'}
        except Exception as e:
            res[tf] = {'error': str(e)[:50]}
        time.sleep(0.1)
    return res

def compute_score(r):
    s = 0
    for t in TIMEFRAME_LIST:
        d = r.get(t, {})
        if isinstance(d, dict) and 'error' not in d:
            if d.get('squeeze_on'):         s += 2
            if d.get('just_fired'):         s += 3
            if d.get('bullish_setup'):      s += 2
            if d.get('momentum_positive'):  s += 1
            if d.get('momentum_increasing'):s += 1
    return s


# ─── RENDERING HELPERS ───

def squeeze_badge(d):
    if isinstance(d, dict) and 'error' in d:
        return '<span class="sq-none">N/A</span>'
    so = d.get('squeeze_on', False)
    jf = d.get('just_fired', False)
    bu = d.get('bullish_setup', False)
    sb = d.get('squeeze_bars', 0)
    if jf:
        return '<span class="sq-fired">FIRED!</span>'
    elif so and bu:
        return f'<span class="sq-bullish">SQ({sb})</span>'
    elif so:
        return f'<span class="sq-on">SQ({sb})</span>'
    else:
        return '<span class="sq-none">No</span>'

def momentum_badge(d):
    if isinstance(d, dict) and 'error' in d:
        return '<span class="mom-neg">—</span>'
    mp = d.get('momentum_positive', False)
    mi = d.get('momentum_increasing', False)
    if mp and mi:
        return '<span class="mom-strong">▲ Strong</span>'
    elif mp:
        return '<span class="mom-pos">▲ Pos</span>'
    elif mi:
        return '<span class="mom-rise">↗ Rise</span>'
    else:
        return '<span class="mom-neg">▼ Neg</span>'

def score_badge(s):
    if s >= 15:
        return f'<span class="score-high">{s}</span>'
    elif s >= 8:
        return f'<span class="score-mid">{s}</span>'
    else:
        return f'<span class="score-low">{s}</span>'

def action_badge(r):
    stf, btf, ftf = [], [], []
    for t in TIMEFRAME_LIST:
        d = r.get(t, {})
        if isinstance(d, dict) and 'error' not in d:
            if d.get('squeeze_on'):    stf.append(t)
            if d.get('bullish_setup'): btf.append(t)
            if d.get('just_fired'):    ftf.append(t)
    if ftf and btf:
        return '<span class="action-strong-buy">★★★ STRONG BUY</span>'
    elif len(btf) >= 3:
        return '<span class="action-strong-buy">★★★ MULTI-TF BULLISH</span>'
    elif btf:
        return '<span class="action-bullish">★★ BULLISH</span>'
    elif ftf:
        return '<span class="action-fired">★★ FIRED</span>'
    elif stf:
        return '<span class="action-watch">★ WATCH</span>'
    else:
        return '<span class="action-watch">—</span>'


# ─── SIDEBAR ───

with st.sidebar:
    st.markdown('<div class="scanner-title">🔵 TTM Squeeze</div>', unsafe_allow_html=True)
    st.markdown('<div class="scanner-subtitle">MULTI-TIMEFRAME SCANNER</div>', unsafe_allow_html=True)
    st.markdown("---")

    # Ticker input
    st.markdown("##### Enter Tickers")
    ticker_input = st.text_area(
        "One per line or comma-separated",
        value="AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, AMD, NFLX, SPY",
        height=120,
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Presets
    st.markdown("##### Quick Presets")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏢 Mega Cap", use_container_width=True):
            st.session_state.preset = "AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, AVGO, BRK-B, JPM"
    with col2:
        if st.button("🚀 Growth", use_container_width=True):
            st.session_state.preset = "PLTR, SOFI, COIN, DKNG, RBLX, SHOP, SNOW, CRWD, NET, ARM"

    col3, col4 = st.columns(2)
    with col3:
        if st.button("⚡ Momentum", use_container_width=True):
            st.session_state.preset = "SMCI, MSTR, MARA, RIOT, COIN, HOOD, SQ, AFRM, UPST, IONQ"
    with col4:
        if st.button("📊 ETFs", use_container_width=True):
            st.session_state.preset = "SPY, QQQ, IWM, DIA, ARKK, XLF, XLE, XLK, SOXX, GLD"

    if 'preset' in st.session_state:
        ticker_input = st.session_state.preset
        del st.session_state.preset
        st.rerun()

    st.markdown("---")

    # Squeeze parameters
    st.markdown("##### Squeeze Parameters")
    bb_len = st.slider("BB Length", 10, 30, 20)
    bb_mult = st.slider("BB Multiplier", 1.0, 3.0, 2.0, 0.1)
    kc_mult = st.slider("KC Multiplier", 1.0, 3.0, 1.5, 0.1)

    st.markdown("---")

    # Scan button
    scan_btn = st.button("🔍  SCAN NOW", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown(f'<div class="scanner-subtitle">Last scan: {datetime.now().strftime("%H:%M:%S")}</div>',
                unsafe_allow_html=True)


# ─── PARSE TICKERS ───

def parse_tickers(text):
    tickers = []
    for part in text.replace('\n', ',').split(','):
        t = part.strip().upper()
        if t and t != 'NAN':
            tickers.append(t)
    return list(dict.fromkeys(tickers))  # dedupe preserving order


# ─── MAIN CONTENT ───

st.markdown('<div class="scanner-title">TTM Squeeze Scanner</div>', unsafe_allow_html=True)
st.markdown(f'<div class="scanner-subtitle">DAILY · 4H · 1H · 30MIN · 10MIN · 5MIN &nbsp;&nbsp;|&nbsp;&nbsp; {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>', unsafe_allow_html=True)
st.markdown("")

# Legend
st.markdown("""
<div style="display:flex; gap:16px; flex-wrap:wrap; margin-bottom:1rem;">
    <span class="sq-on">CYAN = Squeeze ON</span>
    <span class="sq-fired">ORANGE = Just Fired</span>
    <span class="sq-bullish">GREEN = Bullish Squeeze</span>
    <span class="sq-none">GRAY = No Squeeze</span>
</div>
""", unsafe_allow_html=True)

# ─── RUN SCAN ───

if scan_btn:
    tickers = parse_tickers(ticker_input)

    if not tickers:
        st.error("Please enter at least one ticker symbol.")
    else:
        results = []
        progress = st.progress(0, text=f"Scanning {len(tickers)} stocks...")
        status = st.empty()

        total = len(tickers)
        for i in range(0, total, 3):
            batch = tickers[i:i+3]
            with ThreadPoolExecutor(max_workers=3) as ex:
                futs = {ex.submit(scan_stock, t): t for t in batch}
                for f in as_completed(futs):
                    t = futs[f]
                    try:
                        r = f.result()
                        results.append(r)
                    except Exception:
                        results.append({'ticker': t})
                    done = len(results)
                    progress.progress(done / total, text=f"Scanning... {done}/{total} — {t}")
            if i + 3 < total:
                time.sleep(0.3)

        progress.empty()
        status.empty()

        # Sort by score
        sorted_results = sorted(results, key=compute_score, reverse=True)

        # Store in session
        st.session_state.results = sorted_results

if 'results' in st.session_state:
    sorted_results = st.session_state.results

    # ─── SUMMARY METRICS ───
    total_scanned = len(sorted_results)
    squeeze_count = sum(1 for r in sorted_results
                        if any(isinstance(r.get(t, {}), dict) and
                               (r.get(t, {}).get('squeeze_on') or r.get(t, {}).get('just_fired'))
                               for t in TIMEFRAME_LIST))
    bullish_count = sum(1 for r in sorted_results
                        if any(isinstance(r.get(t, {}), dict) and r.get(t, {}).get('bullish_setup')
                               for t in TIMEFRAME_LIST))
    fired_count = sum(1 for r in sorted_results
                      if any(isinstance(r.get(t, {}), dict) and r.get(t, {}).get('just_fired')
                             for t in TIMEFRAME_LIST))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#e5e7eb;">{total_scanned}</div>
            <div class="metric-label">SCANNED</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#00d4ff;">{squeeze_count}</div>
            <div class="metric-label">IN SQUEEZE</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#34d399;">{bullish_count}</div>
            <div class="metric-label">BULLISH</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#ff6b35;">{fired_count}</div>
            <div class="metric-label">JUST FIRED</div></div>""", unsafe_allow_html=True)

    st.markdown("")

    # ─── TABS ───
    tab1, tab2 = st.tabs(["📊 Full Dashboard", "🎯 Bullish Candidates"])

    with tab1:
        # Build HTML table
        header = '<tr><th style="padding:8px 12px;color:#00d4ff;font-family:JetBrains Mono;font-size:0.75rem;text-align:center;border-bottom:2px solid #1f2937;">#</th>'
        header += '<th style="padding:8px 12px;color:#00d4ff;font-family:JetBrains Mono;font-size:0.75rem;text-align:center;border-bottom:2px solid #1f2937;">TICKER</th>'
        for tf in TIMEFRAME_LIST:
            header += f'<th style="padding:8px 6px;color:#00d4ff;font-family:JetBrains Mono;font-size:0.7rem;text-align:center;border-bottom:2px solid #1f2937;">{tf}<br>Squeeze</th>'
            header += f'<th style="padding:8px 6px;color:#00d4ff;font-family:JetBrains Mono;font-size:0.7rem;text-align:center;border-bottom:2px solid #1f2937;">{tf}<br>Mom</th>'
        header += '<th style="padding:8px 12px;color:#00d4ff;font-family:JetBrains Mono;font-size:0.75rem;text-align:center;border-bottom:2px solid #1f2937;">SCORE</th></tr>'

        rows = ''
        for idx, r in enumerate(sorted_results):
            bg = '#0d1117' if idx % 2 == 0 else '#111827'
            row = f'<tr style="background:{bg};">'
            row += f'<td style="padding:6px 12px;text-align:center;color:#6b7280;font-family:JetBrains Mono;font-size:0.8rem;">{idx+1}</td>'
            row += f'<td style="padding:6px 12px;text-align:center;"><span class="ticker-name">{r["ticker"]}</span></td>'
            for tf in TIMEFRAME_LIST:
                d = r.get(tf, {})
                row += f'<td style="padding:6px;text-align:center;">{squeeze_badge(d)}</td>'
                row += f'<td style="padding:6px;text-align:center;">{momentum_badge(d)}</td>'
            sc = compute_score(r)
            row += f'<td style="padding:6px 12px;text-align:center;">{score_badge(sc)}</td>'
            row += '</tr>'
            rows += row

        table_html = f"""
        <div class="results-table">
            <table style="width:100%;border-collapse:collapse;">
                <thead>{header}</thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    with tab2:
        # Bullish candidates
        bullish_rows = ''
        count = 0
        for r in sorted_results:
            stf, btf, ftf = [], [], []
            for t in TIMEFRAME_LIST:
                d = r.get(t, {})
                if isinstance(d, dict) and 'error' not in d:
                    if d.get('squeeze_on'):    stf.append(t)
                    if d.get('bullish_setup'): btf.append(t)
                    if d.get('just_fired'):    ftf.append(t)
            if stf or ftf or btf:
                count += 1
                bg = '#0d1117' if count % 2 == 0 else '#111827'
                sc = compute_score(r)
                ab = action_badge(r)
                bullish_rows += f"""<tr style="background:{bg};">
                    <td style="padding:8px 12px;text-align:center;"><span class="ticker-name">{r['ticker']}</span></td>
                    <td style="padding:8px;text-align:center;color:#00d4ff;font-family:JetBrains Mono;font-size:0.8rem;">{', '.join(stf) or '—'}</td>
                    <td style="padding:8px;text-align:center;color:#34d399;font-family:JetBrains Mono;font-size:0.8rem;">{', '.join(btf) or '—'}</td>
                    <td style="padding:8px;text-align:center;color:#ff6b35;font-family:JetBrains Mono;font-size:0.8rem;">{', '.join(ftf) or '—'}</td>
                    <td style="padding:8px;text-align:center;">{score_badge(sc)}</td>
                    <td style="padding:8px;text-align:center;">{ab}</td>
                </tr>"""

        if bullish_rows:
            bh = """<tr>
                <th style="padding:8px 12px;color:#00d4ff;font-family:JetBrains Mono;font-size:0.75rem;text-align:center;border-bottom:2px solid #1f2937;">TICKER</th>
                <th style="padding:8px;color:#00d4ff;font-family:JetBrains Mono;font-size:0.75rem;text-align:center;border-bottom:2px solid #1f2937;">SQUEEZE TFs</th>
                <th style="padding:8px;color:#00d4ff;font-family:JetBrains Mono;font-size:0.75rem;text-align:center;border-bottom:2px solid #1f2937;">BULLISH TFs</th>
                <th style="padding:8px;color:#00d4ff;font-family:JetBrains Mono;font-size:0.75rem;text-align:center;border-bottom:2px solid #1f2937;">FIRED TFs</th>
                <th style="padding:8px;color:#00d4ff;font-family:JetBrains Mono;font-size:0.75rem;text-align:center;border-bottom:2px solid #1f2937;">SCORE</th>
                <th style="padding:8px;color:#00d4ff;font-family:JetBrains Mono;font-size:0.75rem;text-align:center;border-bottom:2px solid #1f2937;">ACTION</th>
            </tr>"""
            st.markdown(f"""<div class="results-table">
                <table style="width:100%;border-collapse:collapse;">
                    <thead>{bh}</thead>
                    <tbody>{bullish_rows}</tbody>
                </table>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("No bullish candidates found in this scan.")

else:
    # No results yet — show instructions
    st.markdown("""
    <div style="text-align:center; padding:4rem 2rem; color:#6b7280;">
        <div style="font-size:3rem; margin-bottom:1rem;">🔵</div>
        <div style="font-family:Outfit; font-size:1.3rem; color:#e5e7eb; margin-bottom:0.5rem;">
            Enter your tickers and hit SCAN NOW
        </div>
        <div style="font-family:JetBrains Mono; font-size:0.8rem;">
            Uses Yahoo Finance · All 6 timeframes · Free & unlimited
        </div>
    </div>
    """, unsafe_allow_html=True)
