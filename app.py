import streamlit as st

# Configurazione della pagina web
st.set_page_config(page_title="Comparatore Bollette Energia", layout="centered")
st.title("📊 Comparatore di Tariffe Energetiche")
st.write("Inserisci i dati della bolletta attuale e confronta le offerte dei tuoi gestori.")

# 1. DATI DEL CLIENTE (Input da bolletta attuale)
st.header("1. Dati della Bolletta Attuale")
col1, col2 = st.columns(2)

with col1:
    tipo_fornitura = st.selectbox("Tipo di Fornitura", ["Luce (Elettricità)", "Gas"])
    periodo_mesi = st.number_input("Periodo della bolletta (in mesi)", min_value=1, max_value=12, value=2)

with col2:
    if tipo_fornitura == "Luce (Elettricità)":
        consumo = st.number_input("Consumo totale nel periodo (kWh)", min_value=0.0, value=350.0, step=10.0)
        unita = "kWh"
    else:
        consumo = st.number_input("Consumo totale nel periodo (Smc)", min_value=0.0, value=150.0, step=10.0)
        unita = "Smc"

spesa_attuale = st.number_input("Spesa Totale Attuale in Bolletta (€)", min_value=0.0, value=120.0, step=5.0)

# 2. INSERIMENTO GESTORI DA CONFRONTARE
st.header("2. Configura i Gestori da Confrontare")
st.write("Inserisci le condizioni economiche dei gestori che vuoi testare.")

# Inizializziamo lo stato per memorizzare i gestori
if "gestori" not in st.session_state:
    st.session_state.gestori = [
        {"nome": "Gestore A", "quota_fissa_anno": 120.0, "prezzo_materia": 0.13},
        {"nome": "Gestore B", "quota_fissa_anno": 90.0, "prezzo_materia": 0.15}
    ]

# Form per aggiungere un nuovo gestore
with st.expander("➕ Aggiungi / Modifica Gestore"):
    nuovo_nome = st.text_input("Nome del Gestore")
    nuova_fissa = st.number_input("Quota Fissa Annuale (€/anno)", min_value=0.0, value=120.0, step=5.0)
    nuovo_prezzo = st.number_input(f"Prezzo Materia Energia (€/{unita})", min_value=0.000, value=0.120, format="%.3f", step=0.005)
    
    if st.button("Salva Gestore"):
        if nuovo_nome:
            st.session_state.gestori.append({
                "nome": nuevo_nome,
                "quota_fissa_anno": nuova_fissa,
                "prezzo_materia": nuovo_prezzo
            })
            st.success(f"{nuovo_nome} aggiunto con successo!")
        else:
            st.error("Inserisci un nome valido per il gestore.")

# Mostra i gestori inseriti con opzione di rimozione
if st.session_state.gestori:
    st.write("### Gestori inseriti:")
    for idx, g in enumerate(st.session_state.gestori):
        st.text(f"• {g['nome']}: Fissa: {g['quota_fissa_anno']}€/anno | Variabile: {g['prezzo_materia']}€/{unita}")

# 3. CALCOLO E RISULTATI
if st.button("🚀 Calcola e Confronta Tariffe", type="primary"):
    st.header("3. Risultati del Confronto")
    
    # Stimiamo la quota fissa attuale proporzionata ai mesi della bolletta
    risultati = []
    
    for g in st.session_state.gestori:
        # Calcolo quota fissa per il periodo della bolletta
        fissa_periodo = (g["quota_fissa_anno"] / 12) * periodo_mesi
        # Calcolo quota variabile
        variabile_periodo = consumo * g["prezzo_materia"]
        # Costo totale stimato della materia energia nel periodo
        costo_stimato = fissa_periodo + variabile_periodo
        
        # Nota: assumiamo che le altre voci di rete e imposte siano uguali, 
        # quindi confrontiamo la differenza pura sulla materia energia rispetto alla bolletta attuale
        risultati.append({
            "Gestore": g["nome"],
            "Spesa Materia Stimata (€)": round(costo_stimato, 2),
        })
    
    # Mostra i risultati
    for ris in risultati:
        st.subheader(f"🔹 {ris['Gestore']}")
        st.write(f"Con questo gestore, la spesa stimata per la sola Componente Energia nel periodo di {periodo_mesi} mesi sarebbe di **{ris['Spesa Materia Stimata (€)']} €**.")
