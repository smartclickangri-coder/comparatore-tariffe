import streamlit as st

# Configurazione della pagina web
st.set_page_config(page_title="Comparatore Bollette Fasce AI", layout="wide")
st.title("📊 Calcolatore Energetico Professionale con Bonus Sociale")
st.write("Questo calcolatore applica la logica esatta della bolletta per fasce orarie, includendo tasse, canone RAI e l'agevolazione del Bonus Sociale ARERA.")

# 1. PARAMETRI REALI DALLA BOLLETTA WINDTRE
st.header("1. Riferimenti Economici della Bolletta Sotto Esame")
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    pun_f1 = st.number_input("PUN INDEX GME F1 (€/kWh)", value=0.226985, format="%.6f")
with col_f2:
    pun_f2 = st.number_input("PUN INDEX GME F2 (€/kWh)", value=0.250338, format="%.6f")
with col_f3:
    pun_f3 = st.number_input("PUN INDEX GME F3 (€/kWh)", value=0.216722, format="%.6f")

col_cc, col_disp, col_oneri = st.columns(3)
with col_cc:
    corr_consumo_windtre = st.number_input("Corrispettivo Consumo Spread Windtre (€/kWh)", value=0.027800, format="%.6f")
with col_disp:
    dispacciamento_bolletta = st.number_input("Dispacciamento da Bolletta (€/kWh)", value=0.015068, format="%.6f")
with col_oneri:
    oneri_sistema = st.number_input("Oneri di Sistema ARERA (€/kWh)", value=0.033200, format="%.6f")

# DATABASE GESTORI PREDEFINITI
if "gestori" not in st.session_state:
    st.session_state.gestori = [
        {"nome": "Windtre", "tipo": "Indicizzata", "fissa_mese": 7.5, "spread_luce": 0.0278, "luce_fisso": 0.0},
        {"nome": "Fastweb", "tipo": "Fissa Monoraria", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1190},
        {"nome": "TIM Energia", "tipo": "Fissa Monoraria", "fissa_mese": 11.5, "spread_luce": 0.0, "luce_fisso": 0.1965},
        {"nome": "Segno Verde", "tipo": "Fissa Monoraria", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1466},
        {"nome": "Duferco", "tipo": "Indicizzata Monoraria", "fissa_mese": 15.0, "spread_luce": 0.0000, "luce_fisso": 0.0},
        {"nome": "Eni Plenitude", "tipo": "Fissa Monoraria", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1351},
        {"nome": "Enel Energia", "tipo": "Fissa Monoraria", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1790},
        {"nome": "Edison", "tipo": "Fissa Monoraria", "fissa_mese": 6.66, "spread_luce": 0.0, "luce_fisso": 0.1989}
    ]

# 2. INSERIMENTO CONSUMI E DATI TECNICI
st.header("2. Inserisci i Dati della Bolletta e Configurazioni Cliente")
col_cf1, col_cf2, col_cf3 = st.columns(3)
with col_cf1:
    consumo_f1 = st.number_input("Consumo in Fascia F1 (kWh)", value=50.0, step=5.0)
with col_cf2:
    consumo_f2 = st.number_input("Consumo in Fascia F2 (kWh)", value=45.0, step=5.0)
with col_cf3:
    consumo_f3 = st.number_input("Consumo in Fascia F3 (kWh)", value=62.0, step=5.0)

consumo_totale = consumo_f1 + consumo_f2 + consumo_f3
st.info(f"📊 Consumo Totale inserito: **{consumo_totale} kWh**")

col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    mesi = st.number_input("Mesi del periodo di fatturazione", value=1, min_value=1, max_value=12)
with col_p2:
    potenza = st.number_input("Potenza impegnata contatore (kW)", value=3.0, step=0.5)
with col_p3:
    scelta_res = st.selectbox("Tipologia contrattuale", ["Residente", "Non Residente"])
    is_residente = True if scelta_res == "Residente" else False

# --- BLOCCO BONUS SOCIALE ---
st.subheader("🎁 Agevolazioni (Bonus Sociale Elettrico ARERA)")
attiva_bonus = st.checkbox("Il cliente ha diritto al Bonus Sociale per disagio economico?")

bonus_mensile = 0.0
if attiva_bonus:
    categoria_bonus = st.radio(
        "Seleziona la numerosità del nucleo familiare (Valori IV Trimestre 2026):",
        [
            "Nucleo familiare con 1-2 componenti (~11,70 €/mese)",
            "Nucleo familiare con 3-4 componenti (~14,30 €/mese)",
            "Nucleo familiare con più di 4 componenti (~16,10 €/mese)"
        ]
    )
    if "1-2" in categoria_bonus:
        bonus_mensile = 11.70
    elif "3-4" in categoria_bonus:
        bonus_mensile = 14.30
    else:
        bonus_mensile = 16.10

# 3. CALCOLO FINITO MATEMATICO
if st.button("🧮 Esegui Confronto Calibrato", type="primary"):
    st.header("3. Risultato del Confronto Reale Finito (Compreso Canone RAI e Bonus Sociale)")
    
    # Calcolo parametri fissi ARERA di rete uguali per tutti
    if is_residente:
        quota_fissa_rete = (1.80 * mesi) + (1.71 * potenza * mesi)
        quota_fissa_oneri = 0.0
        canone_rai_totale = 7.00 * mesi
    else:
        quota_fissa_rete = (2.20 * mesi) + (1.71 * potenza * mesi)
        quota_fissa_oneri = (135.0 / 12) * mesi
        canone_rai_totale = 0.0
        
    quota_variabile_rete = consumo_totale * 0.0085
    totale_oneri_variabili = consumo_totale * oneri_sistema
    
    # Calcolo Accise
    consumo_tassabile = consumo_totale
    if is_residente and potenza <= 3.0:
        soglia_esenzione = 150.0 * mesi
        consumo_tassabile = max(0.0, consumo_totale - soglia_esenzione)
    accise_totali = consumo_tassabile * 0.0227

    pun_medio_pesato = ((pun_f1 * consumo_f1) + (pun_f2 * consumo_f2) + (pun_f3 * consumo_f3)) / consumo_totale if consumo_totale > 0 else pun_f1
    bonus_totale_periodo = bonus_mensile * mesi

    risultati_finali = []
    
    for g in st.session_state.gestori:
        commercializzazione = g["fissa_mese"] * mesi
        
        if g["nome"] == "Windtre":
            materia_f1 = consumo_f1 * (pun_f1 + corr_consumo_windtre)
            materia_f2 = consumo_f2 * (pun_f2 + corr_consumo_windtre)
            materia_f3 = consumo_f3 * (pun_f3 + corr_consumo_windtre)
            spesa_materia_pura = materia_f1 + materia_f2 + materia_f3
            prezzo_medio_visualizzato = (pun_medio_pesato + corr_consumo_windtre)
        else:
            prezzo_materia_unico = g["luce_fisso"] if g["luce_fisso"] > 0 else (pun_medio_pesato + g["spread_luce"])
            spesa_materia_pura = consumo_totale * prezzo_materia_unico
            prezzo_medio_visualizzato = prezzo_materia_unico
            
        spesa_dispacciamento = consumo_totale * dispacciamento_bolletta
        
        # Totale imponibile
        imponibile = (
            commercializzazione + spesa_materia_pura + spesa_dispacciamento +
            quota_fissa_rete + quota_fissa_oneri + quota_variabile_rete +
            totale_oneri_variabili + accise_totali
        )
        
        iva_10 = imponibile * 0.10
        
        # Il bonus sociale riduce la bolletta (viene sottratto prima o dopo l'IVA a seconda della visualizzazione, qui applicato a storno del totale)
        totale_senza_bonus = imponibile + iva_10 + canone_rai_totale
        totale_finito_bolletta = max(0.0, totale_senza_bonus - bonus_totale_periodo)
        
        risultati_finali.append({
            "Gestore": g["nome"],
            "Tipo Tariffa": g["tipo"],
            "Prezzo Medio (€/kWh)": round(prezzo_medio_visualizzato, 4),
            "Spesa Energia + Disp.": f"{round(spesa_materia_pura + spesa_dispacciamento, 2)} €",
            "Quote Fisse (Rete+Gestore)": f"{round(commercializzazione + quota_fissa_rete + quota_fissa_oneri, 2)} €",
            "Imposte e Oneri (lordi)": f"{round(totale_oneri_variabili + quota_variabile_rete + accise_totali + iva_10 + canone_rai_totale, 2)} €",
            "Bonus Sociale Detratto": f"- {round(bonus_totale_periodo, 2)} €" if bonus_totale_periodo > 0 else "0.0 €",
            "TOTALE FINITO IN BOLLETTA (€)": round(totale_finito_bolletta, 2)
        })
        
    risultati_ordinati = sorted(risultati_finali, key=lambda x: x["TOTALE FINITO IN BOLLETTA (€)"])
    st.table(risultati_ordinati)
