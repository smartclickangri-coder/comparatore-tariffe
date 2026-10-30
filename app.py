import streamlit as st
import google.generativeai as genai
import json
import pypdf

# Configurazione della pagina web
st.set_page_config(page_title="Comparatore Bollette AI", layout="wide")
st.title("📊 Comparatore Bollette Automatico con AI")
st.write("Carica il PDF della bolletta: l'AI estrarrà i consumi e calcolerà la spesa con i tuoi gestori predefiniti.")

# Configurazione Chiave API di Gemini
GEMINI_API_KEY = "AQ.Ab8RN6LVlwDycplVBQb2sjK7QgCXBulvVDdqC1Zz8urQDlA6Hw" 
genai.configure(api_key=GEMINI_API_KEY)

# Valori di mercato stimati per le offerte indicizzate
PUN_RIFERIMENTO = 0.125  # Valore stimato PUN (€/kWh)
PSV_RIFERIMENTO = 0.420  # Valore stimato PSV (€/Smc)

# DATABASE DEI GESTORI PREDEFINITI (Dalla tua tabella)
if "gestori" not in st.session_state:
    st.session_state.gestori = [
        {"nome": "Windtre", "tipo": "Indicizzata", "fissa_mese": 7.5, "luce": "PUN + 0.0139", "gas": "PSV + 0.483", "luce_fisso": 0.0, "gas_fisso": 0.0},
        {"nome": "Fastweb", "tipo": "Mista/Fissa", "fissa_mese": 12.0, "luce": "Fisso", "gas": "PSV + 0.120", "luce_fisso": 0.119, "gas_fisso": 0.0},
        {"nome": "TIM Energia", "tipo": "Mista/Fissa", "fissa_mese": 11.5, "luce": "Fisso", "gas": "PSV + 0.120", "luce_fisso": 0.1965, "gas_fisso": 0.0},
        {"nome": "Segno Verde", "tipo": "Fissa", "fissa_mese": 12.0, "luce": "Fisso", "gas": "Fisso", "luce_fisso": 0.1466, "gas_fisso": 0.555},
        {"nome": "Duferco", "tipo": "Indicizzata", "fissa_mese": 15.0, "luce": "PUN + 0.0000", "gas": "PSV + 0.000", "luce_fisso": 0.0, "gas_fisso": 0.0},
        {"nome": "Eni Plenitude", "tipo": "Fissa", "fissa_mese": 12.0, "luce": "Fisso", "gas": "Fisso", "luce_fisso": 0.1351, "gas_fisso": 0.5655},
        {"nome": "Enel Energia", "tipo": "Fissa", "fissa_mese": 12.0, "luce": "Fisso", "gas": "Fisso", "luce_fisso": 0.179, "gas_fisso": 0.690},
        {"nome": "Edison", "tipo": "Fissa", "fissa_mese": 6.66, "luce": "Fisso", "gas": "Fisso", "luce_fisso": 0.01989, "gas_fisso": 0.0899}
    ]

# Sezione Caricamento File
st.header("1. Carica la Bolletta (PDF)")
file_caricato = st.file_uploader("Trascina o seleziona il PDF della bolletta attuale", type=["pdf"])

if file_caricato is not None:
    with st.spinner("🤖 L'intelligenza artificiale sta analizzando il documento..."):
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
            consumo = dati_estratti.get("consumo_totale", 0.0)
            mesi = dati_estratti.get("mesi_periodo", 2)
            spesa = dati_estratti.get("spesa_totale", 0.0)
            unita = "kWh" if tipo == "Luce" else "Smc"
            
            # Visualizzazione Dati Rilevati
            st.success("✨ Dati estratti con successo dalla bolletta!")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Tipo Fornitura", tipo)
            col2.metric(f"Consumo Estratto", f"{consumo} {unita}")
            col3.metric("Mesi Fatturati", mesi)
            col4.metric("Spesa Attuale", f"{spesa} €")
            
            # 2. CALCOLO AUTOMATICO DEL CONFRONTO
            st.header("2. Classifica della Spesa Stimata con i tuoi Gestori")
            st.write(f"I calcoli includono la quota di commercializzazione fissa e la spesa variabile (PUN stimato a {PUN_RIFERIMENTO}€ e PSV stimato a {PSV_RIFERIMENTO}€ per le tariffe indicizzate).")
            
            risultati = []
            
            for g in st.session_state.gestori:
                # 1. Calcolo quota fissa per i mesi della bolletta
                costo_fissato = g["fissa_mese"] * mesi
                
                # 2. Calcolo prezzo della materia energia in base al tipo di offerta
                if tipo == "Luce":
                    if "PUN" in g["luce"]:
                        # Es: PUN + 0.0139
                        spread = float(g["luce"].split("+")[1].strip())
                        prezzo_finale_materia = PUN_RIFERIMENTO + spread
                    else:
                        prezzo_finale_materia = g["luce_fisso"]
                else:  # Gas
                    if "PSV" in g["gas"]:
                        # Es: PSV + 0.120
                        spread = float(g["gas"].split("+")[1].strip())
                        prezzo_finale_materia = PSV_RIFERIMENTO + spread
                    else:
                        prezzo_finale_materia = g["gas_fisso"]
                
                # 3. Costo Totale della Componente Materia Energia
                costo_variabile = consumo * prezzo_finale_materia
                totale_stimato = costo_fissato + costo_variabile
                
                risultati.append({
                    "Gestore": g["nome"],
                    "Tipo Tariffa": g["tipo"],
                    "Quota Commercializzazione": f"{round(costo_fissato, 2)} €",
                    "Costo Materia": f"{round(costo_variabile, 2)} €",
                    "Totale Stimato (€)": round(totale_stimato, 2)
                })
            
            # Ordina i risultati dal più economico al più caro
            risultati_ordinati = sorted(risultati, key=lambda x: x["Totale Stimato (€)"])
            st.table(risultati_ordinati)
                
        except Exception as e:
            st.error(f"Errore di lettura o elaborazione: {e}")
