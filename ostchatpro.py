import streamlit as st
from datetime import datetime
import json
import os
from pathlib import Path

# Sayfa Konfigürasyonu
st.set_page_config(
    page_title="östchat PRO",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (Advanced)
st.markdown("""
<style>
    /* Genel Stil */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .stApp {
        background: #f5f5f5;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Chat Container */
    .chat-container {
        height: 550px;
        overflow-y: auto;
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        border: 2px solid #e0e0e0;
    }
    
    /* Mesaj Stilleri */
    .message-sent {
        display: flex;
        justify-content: flex-end;
        margin: 12px 0;
        animation: slideIn 0.3s ease-in;
    }
    
    .message-received {
        display: flex;
        justify-content: flex-start;
        margin: 12px 0;
        animation: slideIn 0.3s ease-in;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .message-bubble-sent {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        max-width: 65%;
        word-wrap: break-word;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
    }
    
    .message-bubble-received {
        background: #e4e6eb;
        color: #000;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        max-width: 65%;
        word-wrap: break-word;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .message-meta {
        font-size: 11px;
        color: #999;
        margin-top: 6px;
        display: flex;
        gap: 8px;
        align-items: center;
    }
    
    /* Status İndikatörü */
    .status-online {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #31a24c;
        border-radius: 50%;
        margin-right: 4px;
    }
    
    .status-offline {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #ccc;
        border-radius: 50%;
        margin-right: 4px;
    }
    
    /* Stats Box */
    .stats-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Veri Dosyaları
DATA_FILE = "ostchat_pro_data.json"
USERS_FILE = "ostchat_users.json"

def load_data():
    """Mesajları yükle"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"conversations": {}}

def save_data(data):
    """Mesajları kaydet"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_users():
    """Kullanıcı bilgilerini yükle"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Kullanıcı bilgilerini kaydet"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def get_conversation_key(user1, user2):
    """Konuşma anahtarı"""
    users = sorted([user1, user2])
    return f"{users[0]}_{users[1]}"

def add_message(sender, receiver, message, emoji="👤"):
    """Mesaj ekle"""
    data = load_data()
    conv_key = get_conversation_key(sender, receiver)
    
    if conv_key not in data["conversations"]:
        data["conversations"][conv_key] = []
    
    data["conversations"][conv_key].append({
        "sender": sender,
        "receiver": receiver,
        "message": message,
        "timestamp": datetime.now().strftime("%H:%M"),
        "date": datetime.now().strftime("%d.%m.%Y"),
        "emoji": emoji,
        "read": False
    })
    
    save_data(data)

def mark_as_read(sender, receiver):
    """Mesajları okundu olarak işaretle"""
    data = load_data()
    conv_key = get_conversation_key(sender, receiver)
    
    if conv_key in data["conversations"]:
        for msg in data["conversations"][conv_key]:
            if msg["receiver"] == sender:
                msg["read"] = True
    
    save_data(data)

def get_messages(user1, user2):
    """Mesajları getir"""
    data = load_data()
    conv_key = get_conversation_key(user1, user2)
    return data["conversations"].get(conv_key, [])

def get_all_users():
    """Tüm kullanıcıları getir"""
    data = load_data()
    users = set()
    for conv_key in data["conversations"]:
        user1, user2 = conv_key.split("_")
        users.add(user1)
        users.add(user2)
    return sorted(list(users))

def get_unread_count(current_user):
    """Okunmamış mesaj sayısı"""
    data = load_data()
    count = 0
    for conv_key in data["conversations"]:
        for msg in data["conversations"][conv_key]:
            if msg["receiver"] == current_user and not msg.get("read", False):
                count += 1
    return count

# Session State
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "selected_contact" not in st.session_state:
    st.session_state.selected_contact = None
if "show_stats" not in st.session_state:
    st.session_state.show_stats = False

# Sidebar
with st.sidebar:
    st.markdown("## 💬 **östchat PRO**")
    st.markdown("*Advanced Chat v1.5*")
    st.markdown("---")
    
    # Kullanıcı Seçimi
    st.markdown("### 👤 Kullanıcı")
    
    all_users = get_all_users() + ["Yeni Kullanıcı"]
    selected = st.selectbox("Seç:", all_users, key="user_select")
    
    if selected == "Yeni Kullanıcı":
        new_user = st.text_input("Ad:", key="new_user", placeholder="Kullanıcı Adı")
        if st.button("✅ Oluştur", use_container_width=True):
            if new_user:
                st.session_state.current_user = new_user
                st.success(f"✅ {new_user} oluşturuldu!")
                st.rerun()
    else:
        st.session_state.current_user = selected
    
    if st.session_state.current_user:
        unread = get_unread_count(st.session_state.current_user)
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**{st.session_state.current_user}**")
        with col2:
            if unread > 0:
                st.markdown(f"🔴 **{unread}**")
        
        st.markdown("---")
        
        # İstatistikler
        if st.button("📊 İstatistikler", use_container_width=True):
            st.session_state.show_stats = not st.session_state.show_stats
        
        # Kişiler
        st.markdown("### 📇 Kişiler")
        all_users_list = [u for u in get_all_users() if u != st.session_state.current_user]
        
        if all_users_list:
            for contact in all_users_list:
                messages = get_messages(st.session_state.current_user, contact)
                unread_with_contact = sum(1 for m in messages 
                                         if m["receiver"] == st.session_state.current_user 
                                         and not m.get("read", False))
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    btn_text = f"👤 {contact}"
                    if unread_with_contact > 0:
                        btn_text += f" 🔴 {unread_with_contact}"
                    
                    if st.button(btn_text, key=f"contact_{contact}", use_container_width=True):
                        st.session_state.selected_contact = contact
                        mark_as_read(st.session_state.current_user, contact)
                
                with col2:
                    st.write("💬")
        
        st.markdown("---")
        st.markdown("### ➕ Yeni Sohbet")
        
        new_contact = st.text_input("Ad:", key="new_contact", placeholder="Kişi Adı")
        if st.button("✉️ Başlat", use_container_width=True):
            if new_contact and new_contact != st.session_state.current_user:
                st.session_state.selected_contact = new_contact
                st.success(f"✅ {new_contact} ile sohbet açıldı!")
                st.rerun()

# Ana İçerik
if st.session_state.current_user:
    # İstatistikler
    if st.session_state.show_stats:
        st.markdown("### 📊 İstatistikler")
        
        col1, col2, col3 = st.columns(3)
        
        data = load_data()
        total_convs = len(data["conversations"])
        total_msgs = sum(len(msgs) for msgs in data["conversations"].values())
        total_users = len(get_all_users())
        
        with col1:
            st.markdown(f"""
            <div class="stats-box">
                <h3>👥</h3>
                <h2>{total_users}</h2>
                <p>Toplam Kullanıcı</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stats-box">
                <h3>💬</h3>
                <h2>{total_convs}</h2>
                <p>Konuşma</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stats-box">
                <h3>📝</h3>
                <h2>{total_msgs}</h2>
                <p>Mesaj</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Sohbet Alanı
    if st.session_state.selected_contact:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 15px 20px; border-radius: 10px; margin-bottom: 15px;'>
            <h2 style='color: white; margin: 0;'>
                💬 {st.session_state.current_user} 
                <span style='color: #ccc;'>→</span> 
                {st.session_state.selected_contact}
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        messages = get_messages(st.session_state.current_user, st.session_state.selected_contact)
        
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        if messages:
            for msg in messages:
                if msg["sender"] == st.session_state.current_user:
                    st.markdown(f"""
                    <div class='message-sent'>
                        <div class='message-bubble-sent'>
                            <div>{msg['message']}</div>
                            <div class='message-meta'>
                                <span>{msg['timestamp']}</span>
                                <span>{'✓✓' if msg.get('read') else '✓'}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class='message-received'>
                        <div class='message-bubble-received'>
                            <strong>{msg['sender']}</strong>
                            <div style='margin-top: 5px;'>{msg['message']}</div>
                            <div class='message-meta'>
                                <span>{msg['timestamp']}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("📭 Sohbeti başlat!")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Mesaj Gönder
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns([4, 0.8, 0.8, 0.8])
        
        with col1:
            message = st.text_input("Mesaj:", placeholder="Yaz...", key="msg_input")
        
        with col2:
            if st.button("😊", help="Güldür"):
                if message:
                    add_message(st.session_state.current_user, 
                               st.session_state.selected_contact, 
                               message + " 😊", "😊")
                    st.success("✅")
                    st.rerun()
        
        with col3:
            if st.button("👍", help="Beğen"):
                add_message(st.session_state.current_user, 
                           st.session_state.selected_contact, 
                           "👍", "👍")
                st.rerun()
        
        with col4:
            if st.button("📤 Gönder"):
                if message.strip():
                    add_message(st.session_state.current_user, 
                               st.session_state.selected_contact, 
                               message)
                    st.success("✅")
                    st.rerun()
                else:
                    st.warning("Mesaj yazın!")
    
    else:
        st.markdown("""
        <div style='text-align: center; padding: 120px 20px;'>
            <h1 style='color: #667eea; font-size: 70px;'>💬</h1>
            <h2 style='font-size: 32px; color: #333;'>Sohbet Seç</h2>
            <p style='color: #666; font-size: 16px;'>
                Sol menüden kişi seç ya da yeni sohbet başlat
            </p>
        </div>
        """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style='text-align: center; padding: 150px 20px;'>
        <h1 style='color: #667eea; font-size: 90px; margin: 0;'>💬</h1>
        <h1 style='font-size: 48px; color: #333;'>östchat</h1>
        <p style='color: #666; font-size: 18px; margin-top: 20px;'>
            Modern Sohbet Platformu
        </p>
        <hr>
        <p style='color: #999;'>Giriş yapmak için sol menüyü kullan</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #999; font-size: 11px;'>"
    "östchat PRO v1.5 | Streamlit Powered | Made with ❤️</p>",
    unsafe_allow_html=True
)
