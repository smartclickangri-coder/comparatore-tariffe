import streamlit as st
import google.generativeai as genai
import json
import pypdf

# Configurazione della pagina web
st.set_page_config(page_title="Comparatore Bollette AI", layout="centered")
st.title("📊 Comparatore Bollette Automatico con AI")
st.write("Carica il PDF della bolletta: l'intelligenza artificiale estrarrà i dati ed eseguirà il calcolo.")

# Configurazione Chiave API di Gemini (Inserisci la tua chiave qui)
# Puoi ottenerne una gratis su: https://google.com
GEMINI_API_KEY = "LA_TUA_GEMINI_API_KEY" 
genai.configure(api_key=GEMINI_API_KEY)

# Configurazione iniziale dei gestori da confrontare
if "gestori" not in st.session_state:
    st.session_state.gestori = [
        {"nome": "Fornitore Alfa", "quota_fissa_anno": 120.0, "prezzo_materia": 0.115},
        {"nome": "Fornitore Beta", "quota_fissa_anno": 90.0, "prezzo_materia": 0.132}
    ]

# Sezione Caricamento File
st.header("1. Carica la Bolletta (PDF)")
file_caricato = st.file_uploader("Trascina o seleziona il PDF della bolletta attuale", type=["pdf"])

if file_caricato is not None:
    with st.spinner("🤖 L'intelligenza artificiale sta analizzando la bolletta..."):
        try:
            # Estrazione testo dal PDF
            lettore_pdf = pypdf.PdfReader(file_caricato)
            testo_bolletta = ""
            for pagina in lettore_pdf.pages:
                testo_bolletta += pagina.extract_text()
            
            # Prompt per istruire Gemini a estrarre i dati in formato strutturato JSON
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
            
            # Chiamata al modello AI
            modello = genai.GenerativeModel("gemini-1.5-flash")
            risposta = modello.generate_content(prompt)
            
            # Pulizia e parsing del JSON ricevuto dall'AI
            dati_puliti = risposta.text.strip().replace("```json", "").replace("```", "")
            dati_estratti = json.loads(dati_puliti)
            
            # Recupero variabili estratte
            tipo = dati_estratti.get("tipo_fornitura", "Luce")
            consumo = dati_estratti.get("consumo_totale", 0.0)
            mesi = dati_estratti.get("mesi_periodo", 2)
            spesa = dati_estratti.get("spesa_totale", 0.0)
            unita = "kWh" if tipo == "Luce" else "Smc"
            
            # Mostra i dati rilevati all'utente per conferma
            st.success("✨ Dati estratti con successo!")
            col1, col2, col3 = st.columns(3)
            col1.metric("Tipo Fornitura", tipo)
            col2.metric(f"Consumo Rilevato ({unita})", f"{consumo} {unita}")
            col3.metric("Mesi Periodo", mesi)
            st.info(f"Spesa attuale registrata nel PDF: **{spesa} €**")
            
            # 2. CALCOLO AUTOMATICO DEL CONFRONTO
            st.header("2. Risultati del Confronto Automatico")
            st.write("Ecco quanto pagheresti nel medesimo periodo con i gestori da te indicati:")
            
            for g in st.session_state.gestori:
                # Calcolo quota fissa proporzionata ai mesi rilevati dal PDF
                fissa_periodo = (g["quota_fissa_anno"] / 12) * mesi
                # Calcolo quota variabile in base ai consumi del PDF
                variabile_periodo = consumo * g["prezzo_materia"]
                costo_materia_stimato = fissa_periodo + variabile_periodo
                
                st.subheader(f"🔹 {g['nome']}")
                st.write(f"Costo stimato della sola Componente Energia nel periodo: **{round(costo_materia_stimato, 2)} €**")
                
        except Exception as e:
            st.error(f"Si è verificato un errore nell'elaborazione del PDF: {e}")

# Spazio di gestione per aggiungere manualmente altri gestori nel database locale
with st.sidebar:
    st.header("⚙️ Gestione Tariffe")
    with st.expander("Aggiungi Nuovo Gestore"):
        nuovo_nome = st.text_input("Nome Gestore")
        fissa_anno = st.number_input("Quota Fissa Annuale (€/anno)", value=120.0)
        prezzo_mat = st.number_input("Prezzo Energia (€/unità)", value=0.125, format="%.3f")
        if st.button("Aggiungi"):
            if nuovo_nome:
                st.session_state.gestori.append({"nome": nuovo_nome, "quota_fissa_anno": fissa_anno, "prezzo_materia": prezzo_mat})
                st.success(f"{nuovo_nome} aggiunto!")
