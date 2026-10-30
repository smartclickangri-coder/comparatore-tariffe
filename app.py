import streamlit as st

# Configurazione della pagina web professionale
st.set_page_config(page_title="Comparatore Bollette AI Professionale", layout="wide")
st.title("📊 Calcolatore Energetico e Generatore Fac-Simile")
st.write("Inserisci i dati e confronta le tariffe. In fondo trovi il Fac-Simile pronto da stampare con Ctrl+P.")

# 1. PARAMETRI REALI DALLA BOLLETTA
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

# DATABASE GESTORI PREDEFINITI CON MAPPA COLORI BRANDING
if "gestori" not in st.session_state:
    st.session_state.gestori = [
        {"nome": "Windtre", "tipo": "Indicizzata", "fissa_mese": 7.5, "spread_luce": 0.0278, "luce_fisso": 0.0, "colore": "#F4364C"},
        {"nome": "Fastweb", "tipo": "Fissa Monoraria", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1190, "colore": "#1A1A1A"},
        {"nome": "TIM Energia", "tipo": "Fissa Monoraria", "fissa_mese": 11.5, "spread_luce": 0.0, "luce_fisso": 0.1965, "colore": "#00206B"},
        {"nome": "Segno Verde", "tipo": "Fissa Monoraria", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1466, "colore": "#2E7D32"},
        {"nome": "Duferco", "tipo": "Indicizzata Monoraria", "fissa_mese": 15.0, "spread_luce": 0.0000, "luce_fisso": 0.0, "colore": "#0288D1"},
        {"nome": "Eni Plenitude", "tipo": "Fissa Monoraria", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1351, "colore": "#FFDE00"},
        {"nome": "Enel Energia", "tipo": "Fissa Monoraria", "fissa_mese": 12.0, "spread_luce": 0.0, "luce_fisso": 0.1790, "colore": "#E30613"},
        {"nome": "Edison", "tipo": "Fissa Monoraria", "fissa_mese": 6.66, "spread_luce": 0.0, "luce_fisso": 0.1989, "colore": "#005CA9"}
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
st.info(f"📊 Consumo Totale inserito: {consumo_totale} kWh")

col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    mesi = st.number_input("Mesi del periodo di fatturazione", value=1, min_value=1, max_value=12)
with col_p2:
    potenza = st.number_input("Potenza impegnata contatore (kW)", value=3.0, step=0.5)
with col_p3:
    scelta_res = st.selectbox("Tipologia contrattuale", ("Residente", "Non Residente"))
    is_residente = True if scelta_res == "Residente" else False

st.subheader("🎁 Agevolazioni (Bonus Sociale Elettrico ARERA)")
attiva_bonus = st.checkbox("Il cliente ha diritto al Bonus Sociale?")
bonus_mensile = 0.0
if attiva_bonus:
    categoria_bonus = st.radio(
        "Seleziona la numerosità del nucleo familiare:",
        ("Nucleo 1-2 componenti (~11,70 €/mese)", "Nucleo 3-4 componenti (~14,30 €/mese)", "Nucleo >4 componenti (~16,10 €/mese)")
    )
    bonus_mensile = 11.70 if "1-2" in categoria_bonus else (14.30 if "3-4" in categoria_bonus else 16.10)

# Esegui calcoli interni
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

consumo_tassabile = consumo_totale
if is_residente and potenza <= 3.0:
    soglia_esenzione = 150.0 * mesi
    consumo_tassabile = max(0.0, consumo_totale - soglia_esenzione)
accise_totali = consumo_tassabile * 0.0227
pun_medio_pesato = ((pun_f1 * consumo_f1) + (pun_f2 * consumo_f2) + (pun_f3 * consumo_f3)) / consumo_totale if consumo_totale > 0 else pun_f1
bonus_totale_periodo = bonus_mensile * mesi

# Costruzione mappa risultati
mappa_risultati = {}
risultati_schermo = []

for g in st.session_state.gestori:
    commercializzazione = g["fissa_mese"] * mesi
    if g["nome"] == "Windtre":
        spesa_materia_pura = (consumo_f1 * (pun_f1 + corr_consumo_windtre)) + (consumo_f2 * (pun_f2 + corr_consumo_windtre)) + (consumo_f3 * (pun_f3 + corr_consumo_windtre))
        prezzo_medio_vis = pun_medio_pesato + corr_consumo_windtre
    else:
        prezzo_materia_unico = g["luce_fisso"] if g["luce_fisso"] > 0 else (pun_medio_pesato + g["spread_luce"])
        spesa_materia_pura = consumo_totale * prezzo_materia_unico
        prezzo_medio_vis = prezzo_materia_unico
        
    spesa_dispacciamento = consumo_totale * dispacciamento_bolletta
    imponibile = commercializzazione + spesa_materia_pura + spesa_dispacciamento + quota_fissa_rete + quota_fissa_oneri + quota_variabile_rete + totale_oneri_variabili + accise_totali
    iva_10 = imponibile * 0.10
    totale_lordo = imponibile + iva_10 + canone_rai_totale
    totale_finito = max(0.0, totale_lordo - bonus_totale_periodo)
    
    dati_calcolo = {
        "gestore": g["nome"], "tipo": g["tipo"], "prezzo_medio": prezzo_medio_vis,
        "materia": spesa_materia_pura + spesa_dispacciamento, "fisse": commercializzazione + quota_fissa_rete + quota_fissa_oneri,
        "oneri_rete": totale_oneri_variabili + quota_variabile_rete, "tasse": accise_totali + iva_10,
        "canone": canone_rai_totale, "bonus": bonus_totale_periodo, "totale": totale_finito, "colore": g["colore"]
    }
    mappa_risultati[g["nome"]] = dati_calcolo
    
    risultati_schermo.append({
        "Gestore": g["nome"], "Tipo Tariffa": g["tipo"], "Prezzo Medio (€/kWh)": round(prezzo_medio_vis, 4),
        "Materia + Disp.": f"{round(spesa_materia_pura + spesa_dispacciamento, 2)} €",
        "Quote Fisse": f"{round(commercializzazione + quota_fissa_rete + quota_fissa_oneri, 2)} €",
        "Oneri e Imposte": f"{round(totale_oneri_variabili + quota_variabile_rete + accise_totali + iva_10, 2)} €",
        "Canone RAI / Bonus": f"{round(canone_rai_totale - bonus_totale_periodo, 2)} €",
        "TOTALE FINITO (€)": round(totale_finito, 2)
    })

# 3. TABELLA DI CONFRONTO WEB
st.header("3. Risultati del Confronto a Schermo")
st.table(sorted(risultati_schermo, key=lambda x: x["TOTALE FINITO (€)"]))

# 4. GENERATORE DI FATTURA VISIVA DIRETTAMENTE IN APPLICAZIONE (A PROVA DI ERRORE)
st.header("🖨️ Anteprima della Bolletta Fac-Simile da Stampare")
st.write("Configura l'anagrafica. La bolletta sotto si aggiornerà da sola: premi **Ctrl + P** sulla tastiera per salvarla in PDF o stamparla.")

col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    gestore_scelto = st.selectbox("Scegli il Gestore da visualizzare:", [g["nome"] for g in st.session_state.gestori])
with col_p2:
    nome_cliente = st.text_input("Inserisci Nome e Cognome del cliente", value="Cliente Rossi")
with col_p3:
    codice_pod = st.text_input("Inserisci Codice POD", value="IT001E12345678")

# Recupero dati per il rendering grafico
dati_rendering = mappa_risultati[gestore_scelto]
colore_primario = dati_rendering["colore"]
colore_testo_intestazione = "#1A1A1A" if gestore_scelto == "Eni Plenitude" else "#FFFFFF"

# HTML/CSS Premium che riproduce la bolletta reale senza usare moduli PDF instabili
html_bolletta = f"""
<div style="border: 2px solid {colore_primario}; padding: 25px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #FFFFFF; border-radius: 8px; color: #333333; max-width: 800px; margin: auto;">
    
    <!-- BANNER INTESTAZIONE GESTORE -->
    <div style="background-color: {colore_primario}; color: {colore_testo_header if 'colore_testo_header' in locals() else colore_testo_intestazione}; padding: 20px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 26px; font-weight: bold; letter-spacing: 1px;">{gestore_scelto.upper()} ENERGIA</h1>
        <div style="text-align: right; font-size: 12px; line-height: 1.4;"><b>FORNITURA ELETTRETICA</b><br/>Mercato Libero Luce</div>
    </div>
    
    <!-- CONTENITORE DATI A DUE COLONNE (STILE FATTURA REALE) -->
    <div style="display: flex; gap: 20px; margin-bottom: 35px;">
        <!-- BOX SINISTRA: IMPORTO DA PAGARE -->
        <div style="flex: 1; background-color: #F9FAFB; border: 1.5px solid {colore_primario}; padding: 15px; border-radius: 6px; text-align: center;">
            <div style="font-size: 11px; color: #666666; font-weight: bold; letter-spacing: 0.5px;">TOTALE SPESA FINITA IN BOLLETTA</div>
            <div style="font-size: 32px; font-weight: bold; color: #111827; margin: 8px 0;">{round(dati_rendering['totale'], 2)} €</div>
            <div style="font-size: 10px; color: #EF4444; font-weight: bold;">Scadenza: Nei termini contrattuali</div>
            <div style="font-size: 9px; color: #6B7280; margin-top: 6px;">Fattura Fac-Simile Commerciale</div>
        </div>
        
        <!-- BOX DESTRA: INFORMAZIONI TECNICHE -->
