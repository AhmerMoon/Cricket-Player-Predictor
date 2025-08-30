import streamlit as st
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeRegressor
import time
import json
from streamlit_lottie import st_lottie

# --- Load Lottie Animation ---
def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

lottie_animation = load_lottiefile("D:\\Project\\Cricket Player Prediction\\Animation.json")

# --- Page Config ---
st.set_page_config(page_title="🏏 Cricket Player Run Predictor", layout="wide")

# --- Custom Style ---
st.markdown("""
    <style>
    body {
        background-color: #0e1117;
        color: #e6e6e6;
    }
    div.stButton > button:first-child {
        background-color: #1f77b4;
        color: white;
        font-size: 20px;
        font-weight: bold;
        padding: 14px 28px;
        border-radius: 10px;
        transition: all 0.3s ease-in-out;
        margin: 0 auto;
        display: block;
        width: 100%;
        max-width: 300px;
    }
    div.stButton > button:first-child:hover {
        background-color: #00b386;
        transform: scale(1.05);
    }
    .big-font {
        font-size: 32px !important;
        font-weight: bold;
        color: #00ffcc;
    }
    .highlight {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #404040;
        color: #e6e6e6;
    }
    table {
        width: 90% !important;
        margin: 20px auto !important;
        border-collapse: separate !important;
        border-spacing: 0 12px !important;
        font-size: 18px;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    thead tr {
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
    }
    tbody tr {
        background-color: #181c22;
        color: #e6e6e6;
        transition: background-color 0.3s ease;
    }
    tbody tr:hover {
        background-color: #00b386;
        color: white;
        font-weight: bold;
    }
    th, td {
        padding: 14px 24px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- Load and Clean Data ---
df = pd.read_csv("D:\\Project\\Cricket Player Prediction\\newplayer.csv")
df['Opposition'] = df['Opposition'].str.replace('v ', '', regex=False)
df.dropna(inplace=True)
df = df[df['Overs'] >= 5.0]
df['Team Runs'] = df['Team Runs'].astype(str).str.replace('/', '.').astype(float, errors='ignore')

# --- Helper: Exact Match Finder (case-insensitive) ---
def find_best_match(user_input, valid_options):
    for option in valid_options:
        if user_input.strip().lower() == option.strip().lower():
            return option
    return None

# --- Initialize session_state for inputs if not present ---
if "player_input" not in st.session_state:
    st.session_state["player_input"] = ""
if "opposition_input" not in st.session_state:
    st.session_state["opposition_input"] = ""
if "bf" not in st.session_state:
    st.session_state["bf"] = 1
if "overs" not in st.session_state:
    st.session_state["overs"] = 0.0

# --- UI ---
st.markdown("<h1 style='text-align: center;'>🏏 Cricket Player Run Predictor</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    player_input = st.text_input("🎯 Enter Player Name", value=st.session_state["player_input"], key="player_input")
    opposition_input = st.text_input("🛡️ Enter Opposition Team", value=st.session_state["opposition_input"], key="opposition_input")
with col2:
    bf = st.number_input("⚾ Balls Faced", min_value=1, max_value=300, value=st.session_state["bf"], key="bf")
    overs = st.number_input("⏱️ Overs Played", min_value=0.0, step=0.1, format="%.2f", max_value=50.0, value=st.session_state["overs"], key="overs")

# --- Centered Predict Button ---
btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
with btn_col2:
    predict_clicked = st.button("🚀 Predict Runs", use_container_width=True)

# --- Prediction Logic with Validation ---
if predict_clicked:
    errors = []

    if bf > 300:
        errors.append("⚠️ Balls faced must be less than or equal to 300.")
    if overs < 5:
        errors.append("⚠️ Overs played must be at least 5 for a valid prediction.")
    if bf > overs * 6:
        errors.append("⚠️ Balls faced cannot be more than total balls in the overs (6 balls per over).")

    if errors:
        for err in errors:
            st.error(err)
        # Reset balls faced input field if invalid
        if bf > 300:
            st.session_state["bf"] = 1
    else:
        matched_player = find_best_match(player_input, df['Player'].unique())
        matched_oppo = find_best_match(opposition_input, df['Opposition'].unique())

        if matched_player is None:
            st.error(f"❌ Player '{player_input}' not found in dataset.")
        elif matched_oppo is None:
            st.error(f"❌ Opposition '{opposition_input}' not found in dataset.")
        else:
            if 'Country' in df.columns:
                player_country = df[df['Player'] == matched_player]['Country'].mode()[0]
                if player_country.lower() == matched_oppo.lower():
                    st.error(f"⚠️ {matched_player} cannot play against {matched_oppo} (same country).")
                    st.stop()
            else:
                st.warning("⚠️ Country info missing in dataset, skipping same-country validation.")

            # --- Show Lottie Animation during prediction ---
            loading_placeholder = st.empty()
            with loading_placeholder.container():
                st.markdown("<h3 style='text-align: center;'>🔄 Analyzing Match Data... Please Wait</h3>", unsafe_allow_html=True)
                st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
                st_lottie(lottie_animation, speed=1, loop=True, height=150, key="animation")
                st.markdown("</div>", unsafe_allow_html=True)
                time.sleep(3)

            # --- Remove Animation ---
            loading_placeholder.empty()

            # --- Prediction Logic ---
            filtered = df[(df['Player'] == matched_player) & (df['Opposition'] == matched_oppo)]
            if filtered.empty or len(filtered) < 5:
                filtered = df[df['Player'] == matched_player]

            filtered = filtered.copy()
            filtered['PlayerFlag'] = 1
            filtered['OppoFlag'] = 1
            X = filtered[['PlayerFlag', 'OppoFlag', 'BF', 'Overs']]
            y = filtered['Runs']

            model = DecisionTreeRegressor()
            model.fit(X, y)
            pred = model.predict([[1, 1, bf, overs]])
            predicted_runs = int(np.round(pred[0]))

            # --- Show Results ---
            st.markdown("---")
            st.markdown("### 📋 Match Input Summary", unsafe_allow_html=True)
            result_data = {
                "Player": [matched_player],
                "Opposition": [matched_oppo],
                "Balls Faced": [bf],
                "Overs Played": [overs],
                "Predicted Runs": [predicted_runs]
            }
            st.table(pd.DataFrame(result_data))

            st.markdown(f"<div class='highlight big-font' style='text-align: center;'>🏆 Predicted Score: {predicted_runs} Runs</div>", unsafe_allow_html=True)

           