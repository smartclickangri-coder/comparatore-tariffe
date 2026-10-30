import streamlit as st
import google.generativeai as genai
import json
import pypdf

# Configurazione della pagina web
st.set_page_config(page_title="Comparatore Bollette AI Professionale", layout="wide")
st.title("📊 Calcolatore Energetico Professionale con AI")
st.write("Confronto basato sulla media mensile reale degli acquisti d'energia (PUN Index GME).")

# Configurazione Chiave API di Gemini
GEMINI_API_KEY = "AQ.Ab8RN6LVlwDycplVBQb2sjK7QgCXBulvVDdqC1Zz8urQDlA6Hw" 
genai.configure(api_key=GEMINI_API_KEY)

# 1. PARAMETRI DI MERCATO ATTUALI (Medie Mensili Correnti)
st.header("1. Media Mensile degli Acquisti dell'Energia (Mese Corrente)")
col_pun, col_disp, col_oneri = st.columns(3)
with col_pun:
    pun_attuale = st.number_input("PUN Medio Mensile Corrente (€/kWh)", value=0.2075, format="%.4f")
with col_disp:
    dispacciamento = st.number_input("Dispacciamento ARERA (€/kWh)", value=0.0185, format="%.4f")
with col_oneri:
    oneri_sistema_quota_energia = st.number_input("Oneri di Sistema (€/kWh)", value=0.0332, format="%.4f")

# DATABASE GESTORI PREDEFINITI
if "gestori" not in st.session_state:
    st.session_state.gestori = [
        {"nome": "Windtre", "tipo": "Indicizzata", "fissa_mese": 7.5, "spread_luce": 0.0139, "luce_fisso": 0.0},
        {"nome": "Fastweb", "tipo": "Fissa", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1190},
        {"nome": "TIM Energia", "tipo": "Fissa", "fissa_mese": 11.5, "spread_luce": 0.0, "luce_fisso": 0.1965},
        {"nome": "Segno Verde", "tipo": "Fissa", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1466},
        {"nome": "Duferco", "tipo": "Indicizzata", "fissa_mese": 15.0, "spread_luce": 0.0000, "luce_fisso": 0.0},
        {"nome": "Eni Plenitude", "tipo": "Fissa", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1351},
        {"nome": "Enel Energia", "tipo": "Fissa", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1790},
        {"nome": "Edison", "tipo": "Fissa", "fissa_mese": 6.66, "spread_luce": 0.0, "luce_fisso": 0.1989}  # Corretto definitivamente a 0.1989
    ]

# Sezione Caricamento File
st.header("2. Carica la Bolletta (PDF)")
file_caricato = st.file_uploader("Trascina qui il PDF della bolletta Luce", type=["pdf"])

if file_caricato is not None:
    with st.spinner("🤖 L'intelligenza artificiale sta analizzando il documento e calcolando le medie acquisti del mese di riferimento..."):
        try:
            lettore_pdf = pypdf.PdfReader(file_caricato)
            testo_bolletta = "".join([pagina.extract_text() for pagina in lettore_pdf.pages])
            
            # Prompt focalizzato sull'estrazione del mese e sulla ricostruzione della media PUN di quel periodo
            prompt = f"""
            Analizza questo testo di una bolletta ed estrai i dati in formato JSON puro.
            Identifica il mese e l'anno esatto di fatturazione dei consumi. 
            Estrai o stima il valore consuntivo medio mensile del PUN (media degli acquisti sul mercato) relativo a quel preciso mese e anno storico.
            
            Campi richiesti:
            - tipo_fornitura (stringa: 'Luce')
            - consumo_totale (numero: i kWh totali consumati)
            - mesi_periodo (numero: i mesi del periodo fatturato, es. 1 o 2)
            - spesa_totale (numero: l'importo totale della bolletta)
            - potenza_impegnata (numero: i kW di potenza. Se non trovi, metti 3)
            - residente (booleano: true o false)
            - mese_anno_bolletta (stringa: es. 'Mese Anno')
            - pun_storico_bolletta (numero: il valore del PUN medio mensile di quel mese/anno storico in euro/kWh)

            Testo: {testo_bolletta}
            """
            
            modello = genai.GenerativeModel("gemini-3.8-flash")
            risposta = modello.generate_content(prompt)
            dati_estratti = json.loads(risposta.text.strip().replace("```json", "").replace("```", ""))
            
            consumo = float(dati_estratti.get("consumo_totale", 0.0))
            mesi = int(dati_estratti.get("mesi_periodo", 2))
            spesa_pdf = float(dati_estratti.get("spesa_totale", 0.0))
            potenza = float(dati_estratti.get("potenza_impegnata", 3.0))
            residente = bool(dati_estratti.get("residente", True))
            mese_anno = dati_estratti.get("mese_anno_bolletta", "Non rilevato")
            pun_storico = float(dati_estratti.get("pun_storico_bolletta", 0.1200))
            
            st.success("✨ Dati estratti con successo!")
            
            # Pannello di verifica e allineamento dati
            st.subheader("Verifica i dati strutturati estrapolati:")
            col_res, col_pot, col_pun_st = st.columns(3)
            with col_res:
                scelta_residenza = st.selectbox("Tipologia Utenza", ["Domestico Residente", "Domestico Non Residente"], index=0 if residente else 1)
                is_residente = True if scelta_residenza == "Domestico Residente" else False
            with col_pot:
                potenza = st.number_input("Potenza Impegnata (kW)", value=potenza, step=0.5)
            with col_pun_st:
                pun_storico = st.number_input(f"Media Mensile PUN Storica [{mese_anno}] (€/kWh)", value=pun_storico, format="%.4f")

            c1, c2, c3 = st.columns(3)
            c1.metric("Consumo Rilevato", f"{consumo} kWh")
            c2.metric("Mesi Periodo", mesi)
            c3.metric("Spesa Reale da PDF", f"{spesa_pdf} €")
            
            # BLOCCO LOGICO DI CALCOLO UNIFICATO
            def calcola_tabella(pun_da_usare):
                if is_residente:
                    quota_fissa_rete = (1.80 * mesi) + (1.71 * potenza * mesi)
                    quota_fissa_oneri = 0.0
                    canone_rai_totale = 7.00 * mesi
                else:
                    quota_fissa_rete = (2.20 * mesi) + (1.71 * potenza * mesi)
                    quota_fissa_oneri = (135.0 / 12) * mesi
                    canone_rai_totale = 0.0
                
                quota_variabile_rete = consumo * 0.0085
                totale_oneri_variabili = consumo * oneri_sistema_quota_energia
                
                consumo_tassabile = consumo
                if is_residente and potenza <= 3.0:
                    soglia_esenzione = 150.0 * mesi
                    consumo_tassabile = max(0.0, consumo - soglia_esenzione)
                accise_totali = consumo_tassabile * 0.0227
                
                tabella_risultati = []
                for g in st.session_state.gestori:
                    commercializzazione = g["fissa_mese"] * mesi
                    prezzo_materia = g["luce_fisso"] if g["luce_fisso"] > 0 else (pun_da_usare + g["spread_luce"])
                    
                    spesa_consumo_energia = consumo * prezzo_materia
                    spesa_dispacciamento = consumo * dispacciamento
                    
                    totale_imponibile = (
                        commercializzazione + spesa_consumo_energia + spesa_dispacciamento +
                        quota_fissa_rete + quota_variabile_rete + 
                        quota_fissa_oneri + totale_oneri_variabili + accise_totali
                    )
                    
                    iva = totale_imponibile * 0.10
                    totale_bolletta_finito = totale_imponibile + iva + canone_rai_totale
                    
                    tabella_risultati.append({
                        "Gestore": g["nome"],
                        "Tipo Offerta": g["tipo"],
                        "Prezzo Base (€/kWh)": round(prezzo_materia, 4),
                        "Materia Energia + Disp.": f"{round(spesa_consumo_energia + spesa_dispacciamento, 2)} €",
                        "Quote Fisse (Rete+Gestore)": f"{round(commercializzazione + quota_fissa_rete + quota_fissa_oneri, 2)} €",
                        "Imposte, Oneri e Canone": f"{round(totale_oneri_variabili + quota_variabile_rete + accise_totali + iva + canone_rai_totale, 2)} €",
                        "TOTALE IN BOLLETTA (€)": round(totale_bolletta_finito, 2)
                    })
                return sorted(tabella_risultati, key=lambda x: x["TOTALE IN BOLLETTA (€)"])

            # STAMPA SCHERMATE DUALI
            st.header(f"📊 TABELLA 1: Verifica Storica Reale (Mese della Bolletta: {mese_anno})")
            st.write(f"Confronto fedele calcolato sulla **media mensile degli acquisti** di quel periodo (`{pun_storico} €/kWh`). Serve a ricreare i {spesa_pdf} € della bolletta caricata.")
            st.table(calcola_tabella(pun_storico))
            
            st.header("🚀 TABELLA 2: Proiezione di Mercato Attuale (Se cambiasse contratto oggi)")
            st.write(f"Simulazione basata sulla **media mensile degli acquisti d'energia del mese in corso** (`{pun_attuale} €/kWh`).")
            st.table(calcola_tabella(pun_attuale))
            
        except Exception as e:
            st.error(f"Errore nei calcoli: {e}")
