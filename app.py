import streamlit as st
import google.generativeai as genai
import json
import pypdf

# Configurazione della pagina web
st.set_page_config(page_title="Comparatore Bollette AI", layout="wide")
st.title("📊 Comparatore Bollette Automatico con AI")
st.write("Carica il PDF della bolletta: l'AI estrarrà i consumi e ricalcolerà i costi in base ai valori di mercato.")

# Configurazione Chiave API di Gemini
GEMINI_API_KEY = "AQ.Ab8RN6LVlwDycplVBQb2sjK7QgCXBulvVDdqC1Zz8urQDlA6Hw" 
genai.configure(api_key=GEMINI_API_KEY)

# 1. VALORI DI MERCATO REALI AGGIORNATI (Ottobre 2026)
st.header("1. Indici di Mercato del Mese Corrente")
st.write("I valori preimpostati riflettono le quotazioni reali correnti. Modificali se desideri fare simulazioni con mesi precedenti.")

col_pun, col_psv = st.columns(2)
with col_pun:
    pun_corrente = st.number_input("Valore PUN attuale (€/kWh)", min_value=0.0000, value=0.2740, format="%.4f", step=0.005)
with col_psv:
    psv_corrente = st.number_input("Valore PSV attuale (€/Smc)", min_value=0.0000, value=0.4550, format="%.4f", step=0.010)

# DATABASE DEI GESTORI PREDEFINITI CORRETTO (Edison @ 0.1989)
if "gestori" not in st.session_state:
    st.session_state.gestori = [
        {"nome": "Windtre", "tipo": "Indicizzata", "fissa_mese": 7.5, "spread_luce": 0.0139, "spread_gas": 0.483, "luce_fisso": 0.0, "gas_fisso": 0.0},
        {"nome": "Fastweb", "tipo": "Mista/Fissa", "fissa_mese": 12.0, "spread_luce": 0.0, "spread_gas": 0.120, "luce_fisso": 0.119, "gas_fisso": 0.0},
        {"nome": "TIM Energia", "tipo": "Mista/Fissa", "fissa_mese": 11.5, "spread_luce": 0.0, "spread_gas": 0.120, "luce_fisso": 0.1965, "gas_fisso": 0.0},
        {"nome": "Segno Verde", "tipo": "Fissa", "fissa_mese": 12.0, "spread_luce": 0.0, "spread_gas": 0.0, "luce_fisso": 0.1466, "gas_fisso": 0.555},
        {"nome": "Duferco", "tipo": "Indicizzata", "fissa_mese": 15.0, "spread_luce": 0.0000, "spread_gas": 0.000, "luce_fisso": 0.0, "gas_fisso": 0.0},
        {"nome": "Eni Plenitude", "tipo": "Fissa", "fissa_mese": 12.0, "spread_luce": 0.0, "spread_gas": 0.0, "luce_fisso": 0.1351, "gas_fisso": 0.5655},
        {"nome": "Enel Energia", "tipo": "Fissa", "fissa_mese": 12.0, "spread_luce": 0.0, "spread_gas": 0.0, "luce_fisso": 0.179, "gas_fisso": 0.690},
        {"nome": "Edison", "tipo": "Fissa", "fissa_mese": 6.66, "spread_luce": 0.0, "spread_gas": 0.0, "luce_fisso": 0.1989, "gas_fisso": 0.0899}
    ]

# Sezione Caricamento File
st.header("2. Carica la Bolletta (PDF)")
file_caricato = st.file_uploader("Trascina o seleziona il PDF della bolletta attuale", type=["pdf"])

if file_caricato is not None:
    with st.spinner("🤖 L'intelligenza artificiale sta estraendo i consumi..."):
        try:
            # Estrazione testo dal PDF
            lettore_pdf = pypdf.PdfReader(file_caricato)
            testo_bolletta = ""
            for pagina in lettore_pdf.pages:
                testo_bolletta += pagina.extract_text()
            
            # Prompt ottimizzato per estrarre i dati
            prompt = f"""
            Analizza il seguente testo estratto da una bolletta energetica italiana ed estrai le seguenti informazioni in formato JSON puro, senza formattazione markdown.
            Se non trovi un valore, metti null.
            Campi richiesti:
            - tipo_fornitura (stringa: 'Luce' oppure 'Gas')
            - consumo_totale (numero: i kWh totali o i Smc totali consumati nel periodo)
            - mesi_periodo (numero: quanti mesi copre la bolletta, solitamente 1 o 2)
            - spesa_totale (numero: l'importo totale della bolletta in euro)

            Testo della bolletta:
            {testo_bolletta}
            """
            
            modello = genai.GenerativeModel("gemini-3.8-flash")
            risposta = modello.generate_content(prompt)
            
            dati_puliti = risposta.text.strip().replace("```json", "").replace("```", "")
            dati_estratti = json.loads(dati_puliti)
            
            tipo = dati_estratti.get("tipo_fornitura", "Luce")
            consumo = float(dati_estratti.get("consumo_totale", 0.0)) if dati_estratti.get("consumo_totale") else 0.0
            mesi = int(dati_estratti.get("mesi_periodo", 2)) if dati_estratti.get("mesi_periodo") else 2
            spesa = float(dati_estratti.get("spesa_totale", 0.0)) if dati_estratti.get("spesa_totale") else 0.0
            unita = "kWh" if "Luce" in tipo else "Smc"
            
            # Visualizzazione Dati Rilevati
            st.success("✨ Dati estratti con successo dalla bolletta!")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Tipo Fornitura", tipo)
            col2.metric("Consumo Estratto", f"{consumo} {unita}")
            col3.metric("Mesi Fatturati", mesi)
            col4.metric("Spesa Attuale", f"{spesa} €")
            
            # 3. CALCOLO AUTOMATICO DEL CONFRONTO
            st.header("3. Classifica della Spesa Stimata con i tuoi Gestori")
            
            risultati = []
            
            for g in st.session_state.gestori:
                costo_fissato = g["fissa_mese"] * mesi
                
                # Calcolo basato sul tipo di fornitura rilevato
                if "Luce" in tipo:
                    if g["luce_fisso"] > 0:
                        prezzo_finale_materia = g["luce_fisso"]
                        formula_usata = f"{g['luce_fisso']} €/kWh (Fisso)"
                    else:
                        prezzo_finale_materia = pun_corrente + g["spread_luce"]
                        formula_usata = f"PUN ({pun_corrente}) + {g['spread_luce']}"
                else:  # Gas
                    if g["gas_fisso"] > 0:
                        prezzo_finale_materia = g["gas_fisso"]
                        formula_usata = f"{g['gas_fisso']} €/Smc (Fisso)"
                    else:
                        prezzo_finale_materia = psv_corrente + g["spread_gas"]
                        formula_usata = f"PSV ({psv_corrente}) + {g['spread_gas']}"
                
                costo_variabile = consumo * prezzo_finale_materia
                totale_stimato = costo_fissato + costo_variabile
                
                risultati.append({
                    "Gestore": g["nome"],
                    "Tipo Tariffa": g["tipo"],
                    "Dettaglio Prezzo Applicato": formula_usata,
                    "Commercializzazione Fissa": f"{round(costo_fissato, 2)} €",
                    "Costo Consumo Stimato": f"{round(costo_variabile, 2)} €",
                    "Totale Stimato (€)": round(totale_stimato, 2)
                })
            
            risultati_ordinati = sorted(risultati, key=lambda x: x["Totale Stimato (€)"])
            st.table(risultati_ordinati)
                
        except Exception as e:
            st.error(f"Errore di lettura o elaborazione: {e}")
