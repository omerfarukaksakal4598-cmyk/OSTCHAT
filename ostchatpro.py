import streamlit as st
from datetime import datetime
import json
import os

# WebRTC Kamera/Ses için
try:
    from streamlit_webrtc import webrtc_streamer
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False

# Sayfa Konfigürasyonu
st.set_page_config(
    page_title="östchat PRO",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GELİŞMİŞ CSS (WHATSAPP LOOK & FEEL) ---
st.markdown("""
<style>
    /* WhatsApp Web Arka Planı */
    .stApp {
        background-color: #efeae2;
        background-image: url("https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png");
        background-repeat: repeat;
        background-size: 400px;
        opacity: 0.95;
    }
    
    /* Sidebar (Sol Menü) */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #d1d7db;
    }
    
    /* Giriş Ekranı Container */
    .login-container {
        background: white;
        padding: 40px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        max-width: 500px;
        margin: 50px auto;
        text-align: center;
        border-top: 5px solid #00a884;
    }

    /* Mesaj Balonları Alanı */
    .chat-container {
        height: 50vh;
        overflow-y: auto;
        padding: 20px;
        background: rgba(239, 234, 226, 0.3);
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    .message-sent {
        display: flex;
        justify-content: flex-end;
        margin: 8px 0;
    }
    
    .message-received {
        display: flex;
        justify-content: flex-start;
        margin: 8px 0;
    }
    
    .message-bubble-sent {
        background-color: #d9fdd3;
        color: #111b21;
        padding: 8px 12px;
        border-radius: 8px 0 8px 8px;
        max-width: 65%;
        box-shadow: 0 1px 0.5px rgba(11,20,26,.13);
        font-size: 14.5px;
    }
    
    .message-bubble-received {
        background-color: #ffffff;
        color: #111b21;
        padding: 8px 12px;
        border-radius: 0 8px 8px 8px;
        max-width: 65%;
        box-shadow: 0 1px 0.5px rgba(11,20,26,.13);
        font-size: 14.5px;
    }
    
    /* Simüle Arama Ekranı Tasarımı */
    .call-screen {
        text-align: center;
        background: linear-gradient(135deg, #075E54 0%, #128C7E 100%);
        color: white;
        padding: 80px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# --- VERİTABANI İŞLEMLERİ (KALICILIK) ---
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
if "active_call" not in st.session_state: st.session_state.active_call = None

# --- GİRİŞ EKRANI ---
if not st.session_state.logged_in:
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.title("💬 östchat PRO")
    st.write("Sisteme giriş yapmak için bilgilerinizi girin.")
    
    phone_input = st.text_input("Telefon Numaranız:")
    name_input = st.text_input("Adınız ve Soyadınız:")
    
    if st.button("Giriş Yap", type="primary"):
        if phone_input and name_input:
            data = load_data()
            data["users"][phone_input] = {"name": name_input}
            save_data(data)
            st.session_state.my_phone = phone_input
            st.session_state.my_name = name_input
            st.session_state.logged_in = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

else:
    # --- ANA EKRAN ---
    data = load_data()
    
    # Sidebar (Menü)
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.my_name}")
        if st.button("🚪 Çıkış Yap"):
            st.session_state.logged_in = False
            st.session_state.selected_contact = None
            st.rerun()
            
        tab1, tab2 = st.tabs(["💬 Sohbetler", "➕ Rehber/Grup"])
        
        with tab1:
            st.write("#### Kişiler")
            for phone, info in data["users"].items():
                if phone != st.session_state.my_phone:
                    if st.button(f"👤 {info['name']}", key=f"user_{phone}"):
                        st.session_state.selected_contact = phone
                        st.session_state.is_group_chat = False
                        st.rerun()
            st.write("#### Gruplar")
            for g_name, g_info in data["groups"].items():
                if st.session_state.my_phone in g_info.get("members", []):
                    if st.button(f"👥 {g_name}", key=f"grp_{g_name}"):
                        st.session_state.selected_contact = g_name
                        st.session_state.is_group_chat = True
                        st.rerun()
        
        with tab2:
            st.write("#### Yeni Kişi Ekle")
            new_phone = st.text_input("Numara:", key="np")
            new_name = st.text_input("İsim:", key="nn")
            if st.button("Kaydet"):
                if new_phone and new_name:
                    data["users"][new_phone] = {"name": new_name}
                    save_data(data)
                    st.success("Kişi eklendi!")
                    st.rerun()
            
            st.markdown("---")
            st.write("#### Grup Kur")
            g_name = st.text_input("Grup Adı:", key="gn")
            if st.button("Grubu Oluştur"):
                if g_name and g_name not in data["groups"]:
                    data["groups"][g_name] = {"members": [st.session_state.my_phone]}
                    save_data(data)
                    st.rerun()

    # --- SOHBET VE ARAMA ALANI ---
    if st.session_state.selected_contact:
        target = st.session_state.selected_contact
        
        # Arama Modu
        if st.session_state.active_call:
            st.markdown(f"<div class='call-screen'><h1>📞 {target} aranıyor...</h1></div>", unsafe_allow_html=True)
            if WEBRTC_AVAILABLE:
                webrtc_streamer(key="call", media_stream_constraints={"video": False, "audio": True})
            if st.button("🔴 Aramayı Bitir"):
                st.session_state.active_call = False
                st.rerun()
        else:
            # Sohbet Ekranı
            header_col1, header_col2 = st.columns([4, 1])
            with header_col1:
                st.header(target)
            with header_col2:
                if st.button("📞 Sesli Ara"):
                    st.session_state.active_call = True
                    st.rerun()
            
            # Mesajlar
            conv_key = f"CHAT_{target}" if st.session_state.is_group_chat else f"CHAT_{''.join(sorted([st.session_state.my_phone, target]))}"
            if conv_key not in data["conversations"]: data["conversations"][conv_key] = []
            
            st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
            for msg in data["conversations"][conv_key]:
                if msg["sender"] == st.session_state.my_phone:
                    st.markdown(f"<div class='message-sent'><div class='message-bubble-sent'>{msg['text']}</div></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='message-received'><div class='message-bubble-received'>{msg['text']}</div></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Input
            msg_input = st.text_input("Bir mesaj yazın...", key="input")
            if st.button("Gönder"):
                if msg_input:
                    data["conversations"][conv_key].append({"sender": st.session_state.my_phone, "text": msg_input})
                    save_data(data)
                    st.rerun()
    else:
        st.write("Sol menüden bir kişi veya grup seçin ve sohbete başlayın.")
