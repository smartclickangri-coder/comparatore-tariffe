import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

# Configurazione della pagina web
st.set_page_config(page_title="Comparatore Bollette AI Professionale", layout="wide")
st.title("📊 Calcolatore Energetico e Generatore Fac-Simile PDF")
st.write("Inserisci i dati, confronta le tariffe e scarica il fac-simile della bolletta personalizzato per il cliente.")

# 1. PARAMETRI REALI DALLA BOLLETTA (Immagine inviata)
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

st.subheader("🎁 Agevolazioni (Bonus Sociale Elettrico ARERA)")
attiva_bonus = st.checkbox("Il cliente ha diritto al Bonus Sociale?")
bonus_mensile = 0.0
if attiva_bonus:
    categoria_bonus = st.radio(
        "Seleziona la numerosità del nucleo familiare:",
        ["Nucleo 1-2 componenti (~11,70 €/mese)", "Nucleo 3-4 componenti (~14,30 €/mese)", "Nucleo >4 componenti (~16,10 €/mese)"]
    )
    bonus_mensile = 11.70 if "1-2" in categoria_bonus else (14.30 if "3-4" in categoria_bonus else 16.10)

# Esegui calcoli interni per renderli disponibili alla generazione PDF
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

# Costruzione dizionario risultati per la tabella a schermo e per il PDF
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
        "canone": canone_rai_totale, "bonus": bonus_totale_periodo, "totale": totale_finito
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

# 4. PANNELLO LATERALE GENERAZIONE PDF FAC-SIMILE
with st.sidebar:
    st.header("🖨️ Stampa Fac-Simile Cliente")
    st.write("Scegli un gestore dall'elenco per generare e scaricare la simulazione in formato PDF da consegnare al cliente.")
    
    gestore_scelto = st.selectbox("Seleziona il Gestore per il PDF:", [g["nome"] for g in st.session_state.gestori])
    
    if st.button("📄 Genera PDF Fac-Simile"):
        dati_pdf = mappa_risultati[gestore_scelto]
        
        # Generazione PDF in memoria buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        elementi = []
        
        stili = getSampleStyleSheet()
        stile_titolo = ParagraphStyle('Titolo', parent=stili['Heading1'], fontSize=24, textColor=colors.HexColor('#002B49'), spaceAfter=15)
        stile_sottotitolo = ParagraphStyle('Sub', parent=stili['Normal'], fontSize=11, textColor=colors.gray, spaceAfter=25)
        stile_testo = ParagraphStyle('Testo', parent=stili['Normal'], fontSize=10, leading=14)
        stile_evidenziato = ParagraphStyle('Evid', parent=stili['Normal'], fontSize=14, leading=18, textColor=colors.HexColor('#D32F2F'), fontName='Helvetica-Bold')
        
        # Intestazione Documento
        elementi.append(Paragraph(f"FAC-SIMILE PROIEZIONE COMPRENSIVA LUCE: {dati_pdf['gestore'].upper()}", stile_titolo))
        elementi.append(Paragraph("Simulazione commerciale basata sulle condizioni contrattuali indicate e sui profili di consumo del cliente.", stile_sottotitolo))
        elementi.append(Spacer(1, 10))
        
        # Tabella Dati Tecnici Fornitura
        dati_tecnici = [
            [Paragraph("<b>Tipologia Contratto:</b>", stile_testo), Paragraph("Domestico " + ("Residente" if is_residente else "Non Residente"), stile_testo),
             Paragraph("<b>Consumo Periodo:</b>", stile_testo), Paragraph(f"{consumo_totale} kWh", stile_testo)],
            [Paragraph("<b>Potenza Impegnata:</b>", stile_testo), Paragraph(f"{potenza} kW", stile_testo),
             Paragraph("<b>Mesi Fatturati:</b>", stile_testo), Paragraph(f"{mesi} Mese/i", stile_testo)]
        ]
        t_tecnica = Table(dati_tecnici, colWidths=[130, 130, 130, 130])
        t_tecnica.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F5F7F8')), ('PADDING', (0,0), (-1,-1), 8), ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.lightgrey)]))
        elementi.append(t_tecnica)
        elementi.append(Spacer(1, 25))
        
        # Tabella Voci di Spesa
        elementi.append(Paragraph("<b>DETTAGLIO ECONOMICO STIMATO DELLA BOLLETTA</b>", stili['Heading3']))
        voci_spesa = [
