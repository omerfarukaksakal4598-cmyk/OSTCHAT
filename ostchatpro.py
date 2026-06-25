import streamlit as st
from datetime import datetime
import json
import os

# WebRTC için güvenli içe aktarma
try:
    from streamlit_webrtc import webrtc_streamer
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False

# Sayfa Konfigürasyonu
st.set_page_config(page_title="östchat PRO", page_icon="💬", layout="wide")

# Custom CSS - WhatsApp Teması
st.markdown("""
<style>
    .stApp { background-color: #efeae2; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #d1d7db; }
    .login-container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); max-width: 400px; margin: 50px auto; border-top: 5px solid #00a884; }
    .message-sent { display: flex; justify-content: flex-end; margin: 8px 0; }
    .message-received { display: flex; justify-content: flex-start; margin: 8px 0; }
    .message-bubble-sent { background-color: #d9fdd3; padding: 8px 12px; border-radius: 8px 0 8px 8px; max-width: 65%; font-size: 14px; }
    .message-bubble-received { background-color: #ffffff; padding: 8px 12px; border-radius: 0 8px 8px 8px; max-width: 65%; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# --- VERİTABANI İŞLEMLERİ ---
DATA_FILE = "ostchat_pro_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "users" not in data: data["users"] = {}
                if "groups" not in data: data["groups"] = {}
                if "conversations" not in data: data["conversations"] = {}
                return data
        except: pass
    return {"users": {}, "groups": {}, "conversations": {}}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "my_phone" not in st.session_state: st.session_state.my_phone = None
if "my_name" not in st.session_state: st.session_state.my_name = None
if "selected_contact" not in st.session_state: st.session_state.selected_contact = None
if "is_group_chat" not in st.session_state: st.session_state.is_group_chat = False

# --- GİRİŞ EKRANI ---
if not st.session_state.logged_in:
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.title("💬 Giriş Yap")
    phone = st.text_input("Telefon Numaranız")
    name = st.text_input("Adınız")
    if st.button("Giriş Yap"):
        if phone and name:
            data = load_data()
            data["users"][phone] = {"name": name}
            save_data(data)
            st.session_state.my_phone = phone
            st.session_state.my_name = name
            st.session_state.logged_in = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

else:
    # --- ANA EKRAN ---
    data = load_data()
    
    with st.sidebar:
        st.write(f"### 👤 {st.session_state.my_name}")
        if st.button("Çıkış Yap"):
            st.session_state.logged_in = False
            st.session_state.selected_contact = None
            st.rerun()
            
        tab1, tab2 = st.tabs(["💬 Sohbetler", "➕ Rehber Yönetimi"])
        
        with tab1:
            st.write("#### Kişiler ve Gruplar")
            # Kişileri listele
            for phone, info in data["users"].items():
                if phone != st.session_state.my_phone:
                    if st.button(f"👤 {info['name']}", key=f"user_{phone}"):
                        st.session_state.selected_contact = phone
                        st.session_state.is_group_chat = False
                        st.rerun()
            # Grupları listele
            for g_name, g_info in data["groups"].items():
                if st.session_state.my_phone in g_info["members"]:
                    if st.button(f"👥 {g_name}", key=f"grp_{g_name}"):
                        st.session_state.selected_contact = g_name
                        st.session_state.is_group_chat = True
                        st.rerun()
        
        with tab2:
            st.write("#### Yeni Kişi Ekle")
            new_phone = st.text_input("Telefon")
            new_name = st.text_input("İsim")
            if st.button("Kaydet"):
                if new_phone and new_name:
                    data["users"][new_phone] = {"name": new_name}
                    save_data(data)
                    st.success("Kişi eklendi!")
                    st.rerun()
                    
            st.markdown("---")
            st.write("#### Grup Kur")
            g_name = st.text_input("Grup Adı")
            if st.button("Grubu Oluştur"):
                if g_name and g_name not in data["groups"]:
                    data["groups"][g_name] = {"members": [st.session_state.my_phone]}
                    save_data(data)
                    st.rerun()

    # --- SOHBET ALANI ---
    if st.session_state.selected_contact:
        target = st.session_state.selected_contact
        
        if st.session_state.is_group_chat:
            st.header(f"👥 {target}")
            conv_key = f"GRP_{target}"
        else:
            target_name = data["users"].get(target, {}).get("name", target)
            st.header(f"👤 {target_name}")
            conv_key = f"CHAT_{''.join(sorted([st.session_state.my_phone, target]))}"
        
        # Arama Butonu (WebRTC)
        if st.button("📞 Sesli Arama Başlat"):
            if WEBRTC_AVAILABLE:
                webrtc_streamer(key="call", media_stream_constraints={"video": False, "audio": True})
            else:
                st.warning("WebRTC kütüphanesi kurulu değil!")
        
        # Mesajlaşma
        if conv_key not in data["conversations"]: data["conversations"][conv_key] = []
        
        for msg in data["conversations"][conv_key]:
            if msg["sender"] == st.session_state.my_phone:
                st.markdown(f"<div class='message-sent'><div class='message-bubble-sent'>{msg['text']}</div></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='message-received'><div class='message-bubble-received'>{msg['text']}</div></div>", unsafe_allow_html=True)
        
        msg_input = st.text_input("Mesaj yaz...", key="new_msg")
        if st.button("Gönder"):
            if msg_input:
                data["conversations"][conv_key].append({"sender": st.session_state.my_phone, "text": msg_input})
                save_data(data)
                st.rerun()
    else:
        st.write("Sol menüden bir kişi veya grup seçin.")
