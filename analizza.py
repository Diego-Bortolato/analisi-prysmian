#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motore di analisi tecnica per un singolo titolo.
Scritto per girare su GitHub Actions. Nessuna dipendenza fragile:
solo pandas + un downloader dati. Indicatori calcolati a mano.

Configurato per PRYSMIAN (PRY.MI). Per clonarlo su un altro titolo
basta cambiare TICKER e NOME qui sotto.
"""

import sys
import datetime as dt
import pandas as pd

# ----------------------------------------------------------------------
# CONFIGURAZIONE — l'unica parte da toccare per seguire un altro titolo
# ----------------------------------------------------------------------
TICKER = "PRY.MI"          # simbolo Borsa (Prysmian su Milano)
NOME   = "Prysmian"        # nome leggibile per il report
PERIODO_MESI = 14          # storico da scaricare (serve >200 giorni per SMA200)

# ----------------------------------------------------------------------
# 1. DATI — scaricati da Stooq (fonte gratuita, CSV, senza chiave)
#    Ordine di tentativi: Stooq -> Yahoo. Se una fonte cade, si prova l'altra.
# ----------------------------------------------------------------------
def scarica_dati(ticker: str) -> pd.DataFrame:
    errori = []

    # Tentativo A: Stooq (formato CSV diretto, molto stabile)
    try:
        # Stooq usa il suffisso in minuscolo; PRY.MI -> pry.mi
        url = f"https://stooq.com/q/d/l/?s={ticker.lower()}&i=d"
        df = pd.read_csv(url)
        if len(df) > 50 and "Close" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.sort_values("Date").set_index("Date")
            return df[["Open", "High", "Low", "Close", "Volume"]]
        errori.append("Stooq: risposta troppo corta o malformata")
    except Exception as e:
        errori.append(f"Stooq: {type(e).__name__} {e}")

    # Tentativo B: Yahoo via yfinance
    try:
        import yfinance as yf
        df = yf.download(ticker, period=f"{PERIODO_MESI}mo", interval="1d",
                         auto_adjust=True, progress=False)
        if df is not None and not df.empty:
            # yfinance può restituire colonne MultiIndex per un singolo ticker
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df[["Open", "High", "Low", "Close", "Volume"]]
        errori.append("Yahoo: dataframe vuoto")
    except Exception as e:
        errori.append(f"Yahoo: {type(e).__name__} {e}")

    raise RuntimeError("Nessuna fonte dati disponibile.\n  " + "\n  ".join(errori))


# ----------------------------------------------------------------------
# 2. INDICATORI — calcolati a mano, validati contro lo standard
# ----------------------------------------------------------------------
def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0)
    dn = -d.clip(upper=0)
    ru = up.ewm(alpha=1/n, adjust=False, min_periods=n).mean()
    rd = dn.ewm(alpha=1/n, adjust=False, min_periods=n).mean()
    rs = ru / rd
    return 100 - 100 / (1 + rs)


def calcola(df: pd.DataFrame) -> dict:
    close = df["Close"].astype(float)
    vol = df["Volume"].astype(float)

    df = df.copy()
    df["RSI"] = rsi(close, 14)
    df["SMA20"] = close.rolling(20).mean()
    df["SMA50"] = close.rolling(50).mean()
    df["SMA200"] = close.rolling(200).mean()
    df["VOL20"] = vol.rolling(20).mean()
    # massimo dei 60 giorni PRECEDENTI (esclusa oggi) = resistenza recente
    df["MAX60"] = close.rolling(60).max().shift(1)

    oggi = df.iloc[-1]
    ieri = df.iloc[-2]

    def val(x):
        return None if pd.isna(x) else round(float(x), 2)

    prezzo = float(oggi["Close"])
    vol_oggi = float(oggi["Volume"])
    vol_media = float(oggi["VOL20"]) if not pd.isna(oggi["VOL20"]) else None

    # Segnali booleani
    picco_volume = bool(vol_media and vol_oggi > vol_media * 1.5)
    breakout = bool(
        not pd.isna(oggi["MAX60"]) and prezzo > float(oggi["MAX60"]) and picco_volume
    )
    golden_20_50 = bool(
        not pd.isna(ieri["SMA20"]) and not pd.isna(ieri["SMA50"])
        and ieri["SMA20"] < ieri["SMA50"] and oggi["SMA20"] > oggi["SMA50"]
    )
    sopra_200 = bool(not pd.isna(oggi["SMA200"]) and prezzo > float(oggi["SMA200"]))

    return {
        "data": df.index[-1].date().isoformat(),
        "prezzo": round(prezzo, 2),
        "rsi": val(oggi["RSI"]),
        "sma20": val(oggi["SMA20"]),
        "sma50": val(oggi["SMA50"]),
        "sma200": val(oggi["SMA200"]),
        "vol_oggi": int(vol_oggi),
        "vol_media20": int(vol_media) if vol_media else None,
        "max60_prec": val(oggi["MAX60"]),
        "picco_volume": picco_volume,
        "breakout": breakout,
        "golden_cross_20_50": golden_20_50,
        "sopra_sma200": sopra_200,
    }


# ----------------------------------------------------------------------
# 3. LETTURA — traduce i numeri in osservazioni. NESSUN consiglio di trading:
#    solo descrizione di quali condizioni tecniche sono presenti.
# ----------------------------------------------------------------------
def leggi(d: dict) -> list:
    note = []

    r = d["rsi"]
    if r is not None:
        if r >= 70:
            note.append(f"RSI a {r}: zona di ipercomprato (il titolo ha corso molto).")
        elif r <= 30:
            note.append(f"RSI a {r}: zona di ipervenduto (forte pressione in vendita).")
        else:
            note.append(f"RSI a {r}: zona neutra.")

    if d["sma20"] and d["sma50"]:
        rel = "sopra" if d["sma20"] > d["sma50"] else "sotto"
        note.append(f"Media 20gg ({d['sma20']}) {rel} la media 50gg ({d['sma50']}): "
                    f"tendenza di breve {'positiva' if rel=='sopra' else 'debole'}.")

    if d["sma200"]:
        rel = "sopra" if d["sopra_sma200"] else "sotto"
        note.append(f"Prezzo {rel} la media 200gg ({d['sma200']}): "
                    f"quadro di lungo {'costruttivo' if d['sopra_sma200'] else 'sotto pressione'}.")

    if d["golden_cross_20_50"]:
        note.append("Incrocio rialzista media 20/50 avvenuto OGGI (segnale di momentum).")

    if d["picco_volume"]:
        note.append(f"Volume oggi ({d['vol_oggi']:,}) oltre +50% sulla media 20gg "
                    f"({d['vol_media20']:,}): partecipazione anomala.")

    if d["breakout"]:
        note.append(f"BREAKOUT: prezzo sopra il massimo dei 60 giorni precedenti "
                    f"({d['max60_prec']}) CON volume elevato. È il segnale più forte del set.")
    elif d["max60_prec"] and d["prezzo"] < d["max60_prec"]:
        dist = round((d["max60_prec"]/d["prezzo"] - 1)*100, 1)
        note.append(f"Ancora sotto la resistenza dei 60gg ({d['max60_prec']}), "
                    f"a circa {dist}% di distanza.")

    return note


# ----------------------------------------------------------------------
# 4. REPORT
# ----------------------------------------------------------------------
def componi_report(d: dict, note: list) -> str:
    gen = dt.datetime.now().strftime("%d/%m/%Y %H:%M")
    L = []
    L.append(f"REPORT TECNICO — {NOME} ({TICKER})")
    L.append(f"Dati al {d['data']} · generato il {gen}")
    L.append("=" * 52)
    L.append("")
    L.append(f"Prezzo di chiusura   {d['prezzo']} EUR")
    L.append(f"RSI (14)             {d['rsi']}")
    L.append(f"Media mobile 20gg    {d['sma20']}")
    L.append(f"Media mobile 50gg    {d['sma50']}")
    L.append(f"Media mobile 200gg   {d['sma200']}")
    L.append(f"Volume oggi          {d['vol_oggi']:,}")
    L.append(f"Volume medio 20gg    {d['vol_media20']:,}" if d['vol_media20'] else "Volume medio 20gg    N/D")
    L.append("")
    L.append("LETTURA DELLE CONDIZIONI TECNICHE")
    L.append("-" * 52)
    for n in note:
        L.append(f"• {n}")
    L.append("")
    L.append("-" * 52)
    L.append("Questo report descrive condizioni tecniche a scopo di studio.")
    L.append("Non è un consiglio di investimento né un segnale operativo.")
    return "\n".join(L)


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    # Uso senza argomenti: Prysmian, scrive report.txt (comportamento storico).
    # Uso con argomenti: python analizza.py "TICK1,TICK2" "Nome" file_uscita.txt
    #   TICK1,TICK2 = simboli alternativi dello stesso strumento, provati in ordine
    #   (utile per gli ETF quotati su più borse: si usa il primo che risponde).
    global TICKER, NOME
    candidati = [TICKER]
    uscita = "report.txt"
    if len(sys.argv) >= 4:
        candidati = [t.strip() for t in sys.argv[1].split(",") if t.strip()]
        NOME = sys.argv[2]
        uscita = sys.argv[3]

    df, errori = None, []
    for t in candidati:
        print(f"Scarico dati per {t}...", file=sys.stderr)
        try:
            df = scarica_dati(t)
            TICKER = t
            break
        except RuntimeError as e:
            errori.append(f"{t}: {e}")
    if df is None:
        raise RuntimeError("Nessun simbolo ha restituito dati.\n" + "\n".join(errori))

    print(f"Ricevute {len(df)} candele da {TICKER}. Calcolo indicatori...", file=sys.stderr)
    d = calcola(df)
    note = leggi(d)
    report = componi_report(d, note)
    print(report)
    # salva anche su file, così GitHub lo conserva come "risultato"
    with open(uscita, "w", encoding="utf-8") as f:
        f.write(report + "\n")


if __name__ == "__main__":
    main()
