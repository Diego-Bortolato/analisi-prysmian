# analisi-prysmian

Motore di analisi tecnica settimanale, a scopo didattico. Segue tre strumenti:

| Strumento | Simboli provati in ordine | Cartella |
| :--- | :--- | :--- |
| Prysmian | PRY.MI | `report/` |
| iShares MSCI Global Semiconductors UCITS ETF USD (Acc), IE000I8KRLL9 | SEMI.MI, SEC0.DE | `report/etf-semiconduttori/` |
| Vanguard FTSE All-World UCITS ETF USD (Acc), IE00BK5BQT80 | VWCE.MI, VWCE.DE | `report/etf-all-world/` |

Non produce consigli di investimento né segnali operativi.

## Come funziona

1. **Sabato 06:00 UTC** GitHub Actions esegue `analizza.py` per ciascuno
   strumento: scarica la serie storica (Stooq, con Yahoo come riserva) e
   calcola RSI(14), medie mobili 20/50/200, volume medio a 20 giorni e
   resistenza dei 60 giorni. Per gli ETF si usa il primo simbolo che
   restituisce dati; il simbolo usato è scritto nel report. Prezzi in euro.
2. In ogni cartella il report viene salvato tre volte:
   - `AAAA-MM-GG.txt` — archivio, un file per esecuzione;
   - `ultimo.txt` — sempre il report più recente;
   - `precedente.txt` — il report della settimana prima.
3. **Domenica** due task programmati di Claude leggono i file, cercano le
   notizie della settimana e inviano il report fuso per mail:
   - 17:48 — "Report Prysmian";
   - 18:03 — "Report ETF" (entrambi gli ETF in una mail).

Se un ETF non risponde, Prysmian viene archiviato comunque.

Il repository è pubblico perché i task di Claude possano leggere i file senza
credenziali. Contiene solo codice e dati di borsa: nessuna password, nessun
dato personale. Non aggiungere qui file privati.

## Indirizzi fissi

Base: `https://raw.githubusercontent.com/Diego-Bortolato/analisi-prysmian/main/`

- `report/ultimo.txt`, `report/precedente.txt`
- `report/etf-semiconduttori/ultimo.txt`, `report/etf-semiconduttori/precedente.txt`
- `report/etf-all-world/ultimo.txt`, `report/etf-all-world/precedente.txt`

## Lanciarlo a mano

Scheda **Actions** → **Analisi Prysmian** → **Run workflow**.

## Aggiungere uno strumento

Aggiungere in `.github/workflows/analisi.yml` un passo
`python analizza.py "SIMBOLO1,SIMBOLO2" "Nome" report_nome.txt` e una riga
`archivia report_nome.txt report/cartella` nel passo di archiviazione.
