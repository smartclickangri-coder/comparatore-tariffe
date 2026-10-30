import streamlit as st

# Configurazione della pagina web
st.set_page_config(page_title="Comparatore Bollette Fasce AI", layout="wide")
st.title("📊 Calcolatore Energetico Professionale a Tre Fasce (F1, F2, F3)")
st.write("Questo calcolatore applica la logica esatta della bolletta reale divisa per fasce orarie, comprensiva di perdite di rete.")

# 1. PARAMETRI REALI DALLA TUA BOLLETTA WINDTRE (Immagine inviata)
st.header("1. Riferimenti Economici della Bolletta Sotto Esame")
st.write("I valori sotto includono già le perdite di rete e corrispondono esattamente alla fattura caricata.")

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

# DATABASE GESTORI PREDEFINITI CON VERI DATI COMMERCIALI CORRETTI
# Edison impostata correttamente a 0.1989
if "gestori" not in st.session_state:
    st.session_state.gestori = [
        {"nome": "Windtre", "tipo": "Indicizzata", "fissa_mese": 7.5, "spread_luce": 0.0278, "luce_fisso": 0.0, "usa_fasce": True},
        {"nome": "Fastweb", "tipo": "Fissa Monoraria", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1190, "usa_fasce": False},
        {"nome": "TIM Energia", "tipo": "Fissa Monoraria", "fissa_mese": 11.5, "spread_luce": 0.0, "luce_fisso": 0.1965, "usa_fasce": False},
        {"nome": "Segno Verde", "tipo": "Fissa Monoraria", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1466, "usa_fasce": False},
        {"nome": "Duferco", "tipo": "Indicizzata Monoraria", "fissa_mese": 15.0, "spread_luce": 0.0000, "luce_fisso": 0.0, "usa_fasce": False},
        {"nome": "Eni Plenitude", "tipo": "Fissa Monoraria", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1351, "usa_fasce": False},
        {"nome": "Enel Energia", "tipo": "Fissa Monoraria", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1790, "usa_fasce": False},
        {"nome": "Edison", "tipo": "Fissa Monoraria", "fissa_mese": 6.66, "spread_luce": 0.0, "luce_fisso": 0.1989, "usa_fasce": False}
    ]

# 2. INSERIMENTO CONSUMI DIVISI PER FASCIA
st.header("2. Inserisci i Consumi della Bolletta")
col_cf1, col_cf2, col_cf3 = st.columns(3)
with col_cf1:
    consumo_f1 = st.number_input("Consumo in Fascia F1 (kWh)", value=50.0, step=5.0)
with col_cf2:
    consumo_f2 = st.number_input("Consumo in Fascia F2 (kWh)", value=45.0, step=5.0)
with col_cf3:
    consumo_f3 = st.number_input("Consumo in Fascia F3 (kWh)", value=62.0, step=5.0)

consumo_totale = consumo_f1 + consumo_f2 + consumo_f3
st.info(f"📊 Consumo Totale inserito: **{consumo_totale} kWh** (F1 + F2 + F3)")

col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    mesi = st.number_input("Mesi del periodo di fatturazione", value=1, min_value=1, max_value=12)
with col_p2:
    potenza = st.number_input("Potenza impegnata contatore (kW)", value=3.0, step=0.5)
with col_p3:
    scelta_res = st.selectbox("Tipologia contrattuale", ["Residente", "Non Residente"])
    is_residente = True if scelta_res == "Residente" else False

# 3. CALCOLO FINITO MATEMATICO
if st.button("🧮 Esegui Confronto Calibrato", type="primary"):
    st.header("3. Risultato del Confronto Reale Finito (Compreso IVA, Accise e Oneri)")
    
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
    
    # Calcolo Accise con soglia residenti
    consumo_tassabile = consumo_totale
    if is_residente and potenza <= 3.0:
        soglia_esenzione = 150.0 * mesi
        consumo_tassabile = max(0.0, consumo_totale - soglia_esenzione)
    accise_totali = consumo_tassabile * 0.0227

    # Calcolo PUN medio pesato per i gestori monorari indicizzati
    pun_medio_pesato = ((pun_f1 * consumo_f1) + (pun_f2 * consumo_f2) + (pun_f3 * consumo_f3)) / consumo_totale if consumo_totale > 0 else pun_f1

    risultati_finali = []
    
    for g in st.session_state.gestori:
        commercializzazione = g["fissa_mese"] * mesi
        
        # Logica differenziata per calcolo materia prima (Fasce vs Monoraria)
        if g["nome"] == "Windtre":
            # Calcolo esatto Windtre triorario con i parametri della foto
            materia_f1 = consumo_f1 * (pun_f1 + corr_consumo_windtre)
            materia_f2 = consumo_f2 * (pun_f2 + corr_consumo_windtre)
            materia_f3 = consumo_f3 * (pun_f3 + corr_consumo_windtre)
            spesa_materia_pura = materia_f1 + materia_f2 + materia_f3
            prezzo_medio_visualizzato = (pun_medio_pesato + corr_consumo_windtre)
        else:
            if g["luce_fisso"] > 0:
                prezzo_materia_unico = g["luce_fisso"]
            else:
                # Per gli altri indicizzati monorari usa il PUN medio pesato dei consumi del cliente
                prezzo_materia_unico = pun_medio_pesato + g["spread_luce"]
            
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
        totale_finito_bolletta = imponibile + iva_10 + canone_rai_totale
        
        risultati_finali.append({
            "Gestore": g["nome"],
            "Tipo Tariffa": g["tipo"],
            "Prezzo Medio Componente (€/kWh)": round(prezzo_medio_visualizzato, 4),
            "Quota Consumo + Dispacciamento": f"{round(spesa_materia_pura + spesa_dispacciamento, 2)} €",
            "Quote Fisse Totali (Rete+Gestore)": f"{round(commercializzazione + quota_fissa_rete + quota_fissa_oneri, 2)} €",
            "Oneri, Imposte e Canone RAI": f"{round(totale_oneri_variabili + quota_variabile_rete + accise_totali + iva_10 + canone_rai_totale, 2)} €",
            "TOTALE FINITO CALCOLATO (€)": round(totale_finito_bolletta, 2)
        })
        
    risultati_ordinati = sorted(risultati_finali, key=lambda x: x["TOTALE FINITO CALCOLATO (€)"])
    st.table(risultati_ordinati)
