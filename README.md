# analisi-prysmian

Motore di analisi tecnica settimanale su Prysmian (PRY.MI), a scopo didattico.
Non produce consigli di investimento né segnali operativi.

## Come funziona

1. **Sabato 06:00 UTC** GitHub Actions esegue `analizza.py`: scarica la serie
   storica (Stooq, con Yahoo come riserva) e calcola RSI(14), medie mobili
   20/50/200, volume medio a 20 giorni e resistenza dei 60 giorni.
2. Il report viene salvato in `report/`:
   - `report/AAAA-MM-GG.txt` — archivio, un file per esecuzione;
   - `report/ultimo.txt` — sempre il report più recente;
   - `report/precedente.txt` — il report della settimana prima.
3. **Domenica 17:48 (ora italiana)** un task programmato di Claude legge
   `ultimo.txt` e `precedente.txt`, cerca le notizie societarie della settimana
   e invia il report fuso per mail.

Il repository è pubblico perché il task di Claude possa leggere i file senza
credenziali. Contiene solo codice e dati di borsa: nessuna password, nessun
dato personale. Non aggiungere qui file privati.

## Indirizzi fissi

- https://raw.githubusercontent.com/Diego-Bortolato/analisi-prysmian/main/report/ultimo.txt
- https://raw.githubusercontent.com/Diego-Bortolato/analisi-prysmian/main/report/precedente.txt

## Lanciarlo a mano

Scheda **Actions** → **Analisi Prysmian** → **Run workflow**.

## Altro titolo

In `analizza.py` cambiare solo `TICKER` e `NOME` (Borsa Italiana usa il
suffisso `.MI`).
