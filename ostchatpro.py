import streamlit as st
from datetime import datetime
import json
import os

# Kamera ve Mikrofon için WebRTC Kütüphanesi
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

# Custom CSS (WhatsApp Tasarımı)
st.markdown("""
<style>
    .stApp {
        background-color: #efeae2;
        background-image: url("https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png");
        background-repeat: repeat;
        background-size: 400px;
        opacity: 0.95;
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #d1d7db;
    }
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
    .message-meta {
        font-size: 11px;
        color: #667781;
        margin-top: 4px;
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 4px;
    }
    .call-screen {
        text-align: center;
        background: linear-gradient(135deg, #075E54 0%, #128C7E 100%);
        color: white;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# Veri Dosyası (Database)
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
        except:
            pass
    return {"users": {}, "groups": {}, "conversations": {}}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_conversation_key(user1, user2, is_group=False):
    if is_group:
        return f"GROUP_{user1}"
    users = sorted([user1, user2])
    return f"PRIVATE_{users[0]}_{users[1]}"

def add_message(sender_phone, sender_name, receiver_id, message, is_group=False):
    data = load_data()
    conv_key = get_conversation_key(receiver_id if is_group else sender_phone, 
                                    None if is_group else receiver_id, 
                                    is_group)
    
    if conv_key not in data["conversations"]:
        data["conversations"][conv_key] = []
    
    data["conversations"][conv_key].append({
        "sender_phone": sender_phone,
        "sender_name": sender_name,
        "message": message,
        "timestamp": datetime.now().strftime("%H:%M"),
        "date": datetime.now().strftime("%d.%m.%Y")
    })
    save_data(data)

def create_group(group_name, members):
    data = load_data()
    if group_name not in data["groups"]:
        data["groups"][group_name] = {"members": members, "created_at": datetime.now().strftime("%d.%m.%Y")}
        save_data(data)
        return True
    return False

# Session State Değişkenleri
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "my_phone" not in st.session_state:
    st.session_state.my_phone = None
if "my_name" not in st.session_state:
    st.session_state.my_name = None
if "selected_contact" not in st.session_state:
    st.session_state.selected_contact = None
if "is_group_chat" not in st.session_state:
    st.session_state.is_group_chat = False
if "active_call" not in st.session_state:
    st.session_state.active_call = None

# ==========================================
# 1. GERÇEK KAMERA/ARAMA EKRANI MODU
# ==========================================
if st.session_state.logged_in and st.session_state.active_call:
    call_type = st.session_state.active_call
    target = st.session_state.selected_contact
    data = load_data()
    
    if st.session_state.is_group_chat:
        target_name = f"👥 {target} Grubu"
    else:
        target_name = data["users"].get(target, {}).get("name", target)

    st.markdown(f"""
    <div class="call-screen">
        <h2 style='font-size: 36px; font-weight: bold;'>{target_name}</h2>
        <p style='font-size: 18px; color: #d1d7db; letter-spacing: 1px;'>
            {"SESLİ ARAMA (MİKROFON AÇIK)" if call_type == 'voice' else "GÖRÜNTÜLÜ ARAMA (KAMERA AÇIK)"}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # GERÇEK WEBRTC KAMERA/MİKROFON BAĞLANTISI
    st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
    if WEBRTC_AVAILABLE:
        if call_type == 'video':
            st.info("Kameranız açılıyor... (Tarayıcı izinlerini kabul edin)")
            webrtc_streamer(key="video_call")
        elif call_type == 'voice':
            st.info("Mikrofonunuz açılıyor... (Tarayıcı izinlerini kabul edin)")
            # Sadece ses için webrtc ayarları
            webrtc_streamer(key="voice_call", media_stream_constraints={"video": False, "audio": True})
    else:
        st.error("Gerçek arama yapabilmek için 'streamlit-webrtc' kütüphanesi eksik! Lütfen requirements.txt dosyasına ekleyin.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔴 Aramayı Sonlandır", use_container_width=True, type="primary"):
        st.session_state.active_call = None
        st.rerun()
    st.stop()

# ==========================================
# 2. GİRİŞ EKRANI
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-container">
            <h1 style='color: #00a884; font-size: 60px; margin: 0;'>💬</h1>
            <h2 style='color: #111b21; font-weight: bold;'>östchat PRO v3.0</h2>
            <p style='color: #667781; margin-bottom: 25px;'>Gerçek Arama Özellikli Sürüm</p>
        </div>
        """, unsafe_allow_html=True)
        
        phone_input = st.text_input("📱 Telefon Numaranız", placeholder="Örn: 05551234567")
        name_input = st.text_input("👤 Adınız ve Soyadınız", placeholder="Örn: Ömer Faruk")
        
        if st.button("🚀 Giriş Yap / Kayıt Ol", use_container_width=True, type="primary"):
            if phone_input.strip() and name_input.strip():
                data = load_data()
                data["users"][phone_input] = {"name": name_input, "last_login": datetime.now().strftime("%d.%m.%Y %H:%M")}
                save_data(data)
                
                st.session_state.my_phone = phone_input
                st.session_state.my_name = name_input
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Lütfen tüm alanları eksiksiz doldurun!")

# ==========================================
# 3. ANA SOHBET MASASI
# ==========================================
else:
    data = load_data()
    all_users = data["users"]
    all_groups = data["groups"]
    
    with st.sidebar:
        st.markdown(f"""
        <div style='background-color: #00a884; padding: 15px; border-radius: 8px; color: white; margin-bottom: 15px;'>
            <h3 style='margin: 0; color: white;'>👤 {st.session_state.my_name}</h3>
            <p style='margin: 0; color: #e1f5fe; font-size: 12px;'>Numara: {st.session_state.my_phone}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Oturumu Kapat", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.selected_contact = None
            st.rerun()
            
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["📇 Kişiler", "👥 Gruplar"])
        
        with tab1:
            other_users = {p: u for p, u in all_users.items() if p != st.session_state.my_phone}
            if not other_users:
                st.info("Sistemde başka kayıtlı kullanıcı yok.")
            else:
                for phone, info in other_users.items():
                    if st.button(f"👤 {info['name']}", key=f"user_{phone}", use_container_width=True):
                        st.session_state.selected_contact = phone
                        st.session_state.is_group_chat = False
                        st.rerun()
        
        with tab2:
            my_groups = [g for g, details in all_groups.items() if st.session_state.my_phone in details["members"]]
            if not my_groups:
                st.info("Henüz dahil olduğunuz bir grup yok.")
            else:
                for grp in my_groups:
                    if st.button(f"👥 {grp}", key=f"grp_{grp}", use_container_width=True):
                        st.session_state.selected_contact = grp
                        st.session_state.is_group_chat = True
                        st.rerun()
                        
            st.markdown("---")
            st.markdown("##### ➕ Yeni Grup Oluştur")
            new_group_name = st.text_input("Grup İsmi:", key="group_name_input")
            
            available_members = list(other_users.keys())
            selected_members = st.multiselect("Üyeleri Seçin:", available_members, format_func=lambda x: all_users[x]["name"])
            
            if st.button("👥 Grubu Kur", use_container_width=True):
                if new_group_name.strip() and selected_members:
                    final_members = selected_members + [st.session_state.my_phone]
                    if create_group(new_group_name.strip(), final_members):
                        st.success(f"'{new_group_name}' grubu başarıyla kuruldu!")
                        st.rerun()
                    else:
                        st.error("Bu grup ismi zaten kullanılıyor.")
                else:
                    st.warning("Lütfen grup adı girin ve üye seçin.")

    if st.session_state.selected_contact:
        is_group = st.session_state.is_group_chat
        target_id = st.session_state.selected_contact
        
        if is_group:
            chat_title = f"👥 {target_id}"
            chat_subtitle = f"{len(all_groups[target_id]['members'])} Katılımcı"
            conv_key = get_conversation_key(target_id, None, is_group=True)
        else:
            chat_title = f"👤 {all_users[target_id]['name']}"
            chat_subtitle = f"Çevrimiçi | Numarası: {target_id}"
            conv_key = get_conversation_key(st.session_state.my_phone, target_id, is_group=False)

        header_col1, header_col2, header_col3 = st.columns([6, 1, 1])
        with header_col1:
            st.markdown(f"""
            <div style='background-color: #ffffff; padding: 12px 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 5px solid #00a884;'>
                <h3 style='margin: 0; color: #111b21;'>{chat_title}</h3>
                <span style='color: #667781; font-size: 13px;'>{chat_subtitle}</span>
            </div>
            """, unsafe_allow_html=True)
            
        with header_col2:
            if st.button("📞 Sesli", use_container_width=True):
                st.session_state.active_call = 'voice'
                st.rerun()
                
        with header_col3:
            if st.button("🎥 Video", use_container_width=True):
                st.session_state.active_call = 'video'
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)

        messages = data["conversations"].get(conv_key, [])
        
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        if messages:
            for msg in messages:
                if msg["sender_phone"] == st.session_state.my_phone:
                    st.markdown(f"""
                    <div class='message-sent'>
                        <div class='message-bubble-sent'>
                            <div style='font-weight:bold; font-size:12px; color:#00a884;'>Sen</div>
                            <div style='margin-top:2px;'>{msg['message']}</div>
                            <div class='message-meta'><span>{msg['timestamp']}</span> <span style='color:#53bdeb;'>✓✓</span></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class='message-received'>
                        <div class='message-bubble-received'>
                            <div style='font-weight:bold; font-size:12px; color:#e67e22;'>{msg['sender_name']}</div>
                            <div style='margin-top:2px;'>{msg['message']}</div>
                            <div class='message-meta'><span>{msg['timestamp']}</span></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='text-align:center; color:#667781; padding-top:20px;'>İlk mesajı siz yazın!</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5, col6 = st.columns([5, 0.6, 0.6, 0.6, 0.6, 1.2])
        
        with col1:
            message_text = st.text_input("Mesajınızı yazın...", placeholder="Bir mesaj yazın...", key="msg_input", label_visibility="collapsed")
        
        with col2:
            if st.button("😊", use_container_width=True):
                add_message(st.session_state.my_phone, st.session_state.my_name, target_id, message_text + " 😊" if message_text else "😊", is_group)
                st.rerun()
        with col3:
            if st.button("😂", use_container_width=True):
                add_message(st.session_state.my_phone, st.session_state.my_name, target_id, message_text + " 😂" if message_text else "😂", is_group)
                st.rerun()
        with col4:
            if st.button("❤️", use_container_width=True):
                add_message(st.session_state.my_phone, st.session_state.my_name, target_id, message_text + " ❤️" if message_text else "❤️", is_group)
                st.rerun()
        with col5:
            if st.button("👍", use_container_width=True):
                add_message(st.session_state.my_phone, st.session_state.my_name, target_id, message_text + " 👍" if message_text else "👍", is_group)
                st.rerun()
                
        with col6:
            if st.button("🚀 Gönder", use_container_width=True, type="primary"):
                if message_text.strip():
                    add_message(st.session_state.my_phone, st.session_state.my_name, target_id, message_text.strip(), is_group)
                    st.rerun()
                else:
                    st.warning("Boş mesaj gönderilemez!")
    else:
        st.markdown("""
        <div style='text-align: center; padding: 100px 20px; background: white; border-radius: 15px; margin-top: 30px;'>
            <h1 style='color: #00a884; font-size: 70px; margin-bottom: 10px;'>👋</h1>
            <h2 style='color: #111b21;'>Sohbete Başlayın</h2>
            <p style='color: #667781; font-size: 16px;'>Sol menüden bir kişi seçin, grup kurun veya mesajlaşın.</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #667781; font-size: 12px; font-weight: bold;'>⚡ östchat PRO v3.0 | WebRTC Altyapısı Eklendi</p>", unsafe_allow_html=True)
