import streamlit as st
import google.generativeai as genai
import json
import pypdf

# Configurazione della pagina web
st.set_page_config(page_title="Comparatore Bollette AI Professionale", layout="wide")
st.title("📊 Calcolatore Energetico Professionale con AI")
st.write("Analisi completa della bolletta Luce: include materia prima, quote potenza, oneri ARERA, accise, IVA e Canone RAI.")

# Configurazione Chiave API di Gemini
GEMINI_API_KEY = "AQ.Ab8RN6LVlwDycplVBQb2sjK7QgCXBulvVDdqC1Zz8urQDlA6Hw" 
genai.configure(api_key=GEMINI_API_KEY)

# 1. PARAMETRI DI MERCATO E FISCALI (Valori ARERA IV Trimestre 2026)
st.header("1. Parametri di Mercato e Tariffe Autorità (ARERA 2026)")
col_pun, col_disp, col_oneri = st.columns(3)
with col_pun:
    pun_corrente = st.number_input("Valore PUN del mese (€/kWh)", value=0.2740, format="%.4f")
with col_disp:
    dispacciamento = st.number_input("Dispacciamento ARERA (€/kWh)", value=0.0185, format="%.4f")
with col_oneri:
    oneri_sistema_quota_energia = st.number_input("Oneri di Sistema - Quota Energia (€/kWh)", value=0.0332, format="%.4f")

# DATABASE GESTORI (Edison @ 0.1989)
if "gestori" not in st.session_state:
    st.session_state.gestori = [
        {"nome": "Windtre", "tipo": "Indicizzata", "fissa_mese": 7.5, "spread_luce": 0.0139, "luce_fisso": 0.0},
        {"nome": "Fastweb", "tipo": "Fissa", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1190},
        {"nome": "TIM Energia", "tipo": "Fissa", "fissa_mese": 11.5, "spread_luce": 0.0, "luce_fisso": 0.1965},
        {"nome": "Segno Verde", "tipo": "Fissa", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1466},
        {"nome": "Duferco", "tipo": "Indicizzata", "fissa_mese": 15.0, "spread_luce": 0.0000, "luce_fisso": 0.0},
        {"nome": "Eni Plenitude", "tipo": "Fissa", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1351},
        {"nome": "Enel Energia", "tipo": "Fissa", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1790},
        {"nome": "Edison", "tipo": "Fissa", "fissa_mese": 6.66, "spread_luce": 0.0, "luce_fisso": 0.1989}
    ]

# Sezione Caricamento File
st.header("2. Carica la Bolletta (PDF)")
file_caricato = st.file_uploader("Trascina qui il PDF della bolletta Luce", type=["pdf"])

if file_caricato is not None:
    with st.spinner("🤖 L'intelligenza artificiale sta leggendo i dati tecnici e la tipologia di utenza..."):
        try:
            lettore_pdf = pypdf.PdfReader(file_caricato)
            testo_bolletta = "".join([pagina.extract_text() for pagina in lettore_pdf.pages])
            
            # Prompt per estrarre anche la tipologia di utenza (residente o meno)
            prompt = f"""
            Analizza questo testo di una bolletta ed estrai i dati in formato JSON puro.
            Campi richiesti:
            - tipo_fornitura (stringa: 'Luce')
            - consumo_totale (numero: i kWh totali consumati)
            - mesi_periodo (numero: i mesi del periodo fatturato, es. 1 o 2)
            - spesa_totale (numero: l'importo totale della bolletta)
            - potenza_impegnata (numero: i kW di potenza del contatore, solitamente 3, 4.5 o 6. Se non lo trovi, metti 3)
            - residente (booleano: true se trovi scritto 'Domestico Residente' o 'Utenza Residente', false se trovi 'Non Residente' o 'Altri Usi')

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
            
            # Permetti comunque all'utente di modificare la scelta dell'AI tramite interfaccia
            st.success("✨ Dati estratti correttamente!")
            
            st.subheader("Verifica e conferma i dati estratti dall'AI:")
            col_res, col_pot = st.columns(2)
            with col_res:
                scelta_residenza = st.radio("Tipologia Utenza", ["Domestico Residente", "Domestico Non Residente"], index=0 if residente else 1)
                is_residente = True if scelta_residenza == "Domestico Residente" else False
            with col_pot:
                potenza = st.number_input("Potenza Impegnata (kW)", value=potenza, step=0.5)

            c1, c2, c3 = st.columns(3)
            c1.metric("Consumo Rilevato", f"{consumo} kWh")
            c2.metric("Mesi Periodo", mesi)
            c3.metric("Spesa Vecchio Fornitore", f"{spesa_pdf} €")
            
            # 3. CALCOLO STRUTTURATO DELLA BOLLETTA
            st.header("3. Analisi Comparativa dei Costi Reali Finiti (Compreso di Tasse e Canone RAI)")
            
            # --- CALCOLO QUOTE FISSE RETE E ONERI (ARERA) ---
            if is_residente:
                quota_fissa_rete = (1.80 * mesi) + (1.71 * potenza * mesi)
                quota_fissa_oneri = 0.0
                canone_rai_totale = 7.00 * mesi  # 7€ al mese per i residenti
            else:
                # I non residenti pagano quote fisse di rete diverse e la quota fissa annua sugli oneri (135€/anno)
                quota_fissa_rete = (2.20 * mesi) + (1.71 * potenza * mesi)
                quota_fissa_oneri = (135.0 / 12) * mesi
                canone_rai_totale = 0.0  # Niente canone rai sulle seconde case / non residenti
            
            quota_variabile_rete = consumo * 0.0085  # Tariffa per l'uso della rete (quota energia)
            totale_oneri_variabili = consumo * oneri_sistema_quota_energia
            
            # --- CALCOLO ACCISE ---
            consumo_tassabile = consumo
            if is_residente and potenza <= 3.0:
                soglia_esenzione = 150.0 * mesi
                consumo_tassabile = max(0.0, consumo - soglia_esenzione)
            accise_totali = consumo_tassabile * 0.0227
            
            risultati = []
            for g in st.session_state.gestori:
                # Spesa Materia Energia del Gestore
                commercializzazione = g["fissa_mese"] * mesi
                if g["luce_fisso"] > 0:
                    prezzo_materia = g["luce_fisso"]
                else:
                    prezzo_materia = pun_corrente + g["spread_luce"]
                
                spesa_consumo_energia = consumo * prezzo_materia
                spesa_dispacciamento = consumo * dispacciamento
                
                # Somma di tutte le voci imponibili IVA
                totale_imponibile = (
                    commercializzazione + spesa_consumo_energia + spesa_dispacciamento +
                    quota_fissa_rete + quota_variabile_rete + 
                    quota_fissa_oneri + totale_oneri_variabili + accise_totali
                )
                
                # Calcolo IVA 10%
                iva = totale_imponibile * 0.10
                
                # Il Canone RAI si aggiunge alla fine fuori dall'applicazione dell'IVA
                totale_bolletta_finito = totale_imponibile + iva + canone_rai_totale
                
                risultati.append({
                    "Gestore": g["nome"],
                    "Tipo Offerta": g["tipo"],
                    "Prezzo Materia (€/kWh)": f"{round(prezzo_materia, 4)}",
                    "Spesa Energia + Disp.": f"{round(spesa_consumo_energia + spesa_dispacciamento, 2)} €",
                    "Quote Fisse Gestore + Rete": f"{round(commercializzazione + quota_fissa_rete + quota_fissa_oneri, 2)} €",
                    "Oneri + Rete Variabile": f"{round(totale_oneri_variabili + quota_variabile_rete, 2)} €",
                    "Imposte (Accise + IVA 10%)": f"{round(accise_totali + iva, 2)} €",
                    "Canone RAI": f"{round(canone_rai_totale, 2)} €",
                    "TOTALE FINITO IN BOLLETTA (€)": round(totale_bolletta_finito, 2)
                })
            
            risultati_ordinati = sorted(risultati, key=lambda x: x["TOTALE FINITO IN BOLLETTA (€)"])
            st.table(risultati_ordinati)
            
        except Exception as e:
            st.error(f"Errore nei calcoli: {e}")
