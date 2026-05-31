import streamlit as st
import base64
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from dotenv import load_dotenv
import os



# 1. SAYFA AYARLARI
st.set_page_config(page_title="Tersane Üretim Dashboard", page_icon="🚢", layout="wide")

# --- CSS TASARIMI (SABİT YÜZEN BUTON VE PENCERE) ---
st.markdown("""
    <style>
        /* Açılır-kapanır (Popover) kapsayıcısını ekranın sağ altına sabitle */
        [data-testid="stPopover"] {
            position: fixed !important;
            bottom: 30px !important;
            right: 30px !important;
            z-index: 9999 !important;
        }
        
        /* Sağ alttaki chat butonunun yuvarlak ve fiyakalı görünmesini sağla */
        [data-testid="stPopover"] > button {
            border-radius: 50px !important;
            height: 65px !important;
            width: 65px !important;
            background-color: #2e66ff !important;
            color: white !important;
            border: none !important;
            box-shadow: 0px 8px 16px rgba(0,0,0,0.3) !important;
            font-size: 26px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        /* Chat butonu üzerine gelince oluşan hafif büyüme efekti */
        [data-testid="stPopover"] > button:hover {
            background-color: #1a4cd9 !important;
            transform: scale(1.08);
            transition: all 0.2s ease-in-out;
        }
        
        /* Popover açıldığında pencerenin dashboard bileşenlerinin önünde durmasını sağlama */
        [data-testid="stPopoverBody"] {
            box-shadow: 0px 10px 25px rgba(0,0,0,0.3) !important;
            border-radius: 12px !important;
        }
    </style>
""", unsafe_allow_html=True)

# 2. VERİYİ YÜKLEME
@st.cache_data
def load_data():
    return pd.read_csv("tersane_blok_uretim_verisi.csv")

df = load_data()

# 3. YAN MENÜ (Sidebar)
st.sidebar.image("logo.png", width=150) # Logomuz
st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.header("🔍 Filtreleme Paneli")

secilen_siparis = st.sidebar.multiselect(
    "Sipariş (Proje) Seçiniz:",
    options=df["Sipariş_Kodu"].unique(),
    default=df["Sipariş_Kodu"].unique()
)

df_filtrelenmis = df[df["Sipariş_Kodu"].isin(secilen_siparis)]

# 4. ANA EKRAN BAŞLIĞI VE SİNEMATİK VİDEO HEADER
def get_base64_video(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    video_base64 = get_base64_video("stock1.mp4")

    st.markdown(f"""
        <style>
        .video-container {{
            position: relative;
            width: 100%;
            height: 280px;
            border-radius: 15px;
            overflow: hidden;
            margin-bottom: 25px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        }}
        .video-container video {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .video-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(to right, rgba(15, 32, 39, 0.95), rgba(32, 58, 67, 0.7), rgba(44, 83, 100, 0.3));
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding-left: 50px;
        }}
        .video-overlay h1 {{
            color: white;
            font-size: 2.8rem !important;
            font-weight: 800;
            margin: 0;
            text-shadow: 2px 2px 10px rgba(0,0,0,0.8);
        }}
        .video-overlay p {{
            color: #00d4ff;
            font-size: 1.3rem;
            margin-top: 8px;
            font-weight: 500;
            text-shadow: 1px 1px 5px rgba(0,0,0,0.5);
        }}
        </style>

        <div class="video-container">
            <video autoplay loop muted playsinline>
                <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
            </video>
            <div class="video-overlay">
                <h1>Tersane Üretim & Blok Takip Merkezi</h1>
                <p>Yapay Zeka Destekli Operasyonel Yönetim Ekranı</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    st.title("🚢 Tersane Üretim & Blok Takip Merkezi")
    st.markdown("---")

# 5. JİLET GİBİ AÇILIR-KAPANIR GEMINI YAPAY ZEKA ASİSTANI (CSV Verisine Bağlı)


api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

with st.popover("🔮"):
    st.markdown("### 🤖 Gemini Operasyon Asistanı")
    st.markdown("---")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "Gemini", "content": "Merhaba! Üretim istasyonundaki darboğazlar veya bütçe sapmaları hakkında ne öğrenmek istersin?"}]
    
    for msg in st.session_state.messages:
        if msg["role"] == "Gemini":
            st.info(msg["content"])
        else:
            st.success(f"**Sen:** {msg['content']}")
            
    user_input = st.text_input("Gemini'ye sor...", key="gemini_soru")
    
    if st.button("Soruyu Gönder"):
        if user_input:
            st.session_state.messages.append({"role": "Sen", "content": user_input})
            
            with st.spinner("Canlı tersane verileri analiz ediliyor..."):
                try:
                    # Modelin 2.5-flash olarak ayarlandı, efsane çalışacak
                    model = genai.GenerativeModel('gemini-2.5-flash') 
                    
                    # --- AI'A GÖNDERİLECEK CANLI VERİ ÖZETİ (ETL PIPELINE) ---
                    toplam_blok = len(df_filtrelenmis)
                    planlanan_maliyet = df_filtrelenmis["Planlanan_Maliyet_USD"].sum()
                    gerceklesen_maliyet = df_filtrelenmis["Gerçekleşen_Maliyet_USD"].sum()
                    butce_sapmasi = gerceklesen_maliyet - planlanan_maliyet
                    istasyon_gecikmeleri = df_filtrelenmis.groupby("İstasyon")["Gecikme_Süresi_Gün"].sum().to_string()
                    kalite_ozeti = df_filtrelenmis["NDT_Sonucu"].value_counts().to_string()
                    
                    # --- JİLET GİBİ SİSTEM KOMUTU (PROMPT) ---
                    gelismis_prompt = f"""
                    Sen bir Tersane Operasyon Yönetim Asistanısın. Amacın, üretim müdürlerine hızla net veriler sunmaktır.
                    ASLA sözlük tanımları veya uzun teorik açıklamalar yapma. 
                    
                    [CANLI SİSTEM VERİLERİ]
                    - Toplam Üretim Bloğu: {toplam_blok}
                    - Toplam Planlanan Bütçe: ${planlanan_maliyet:,.0f}
                    - Şu Ana Kadar Gerçekleşen Maliyet: ${gerceklesen_maliyet:,.0f}
                    - Güncel Bütçe Sapması: ${butce_sapmasi:,.0f}
                    
                    [İSTASYON BAZLI GECİKME GÜNLERİ ÖZETİ]
                    {istasyon_gecikmeleri}
                    
                    [KALİTE KONTROL (NDT) SONUÇLARI]
                    {kalite_ozeti}
                    
                    Yöneticinin Sorusu: {user_input}
                    """
                    
                    # Promptu API'ye gönder
                    response = model.generate_content(gelismis_prompt)
                    cevap = response.text
                except Exception as e:
                    cevap = f"HATA! Detay: {e}"
            
            st.session_state.messages.append({"role": "Gemini", "content": cevap})
            st.rerun()


# 5. TEPEDEKİ ANA METRİKLER (KPIs)
st.subheader("📊 Genel Performans Göstergeleri")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

toplam_blok = len(df_filtrelenmis)
tamamlanan_blok = len(df_filtrelenmis[df_filtrelenmis["Durum"] == "Tamamlandı"])
planlanan_maliyet = df_filtrelenmis["Planlanan_Maliyet_USD"].sum()
gerceklesen_maliyet = df_filtrelenmis["Gerçekleşen_Maliyet_USD"].sum()

# İlerleme Yüzdesi
ilerleme_yuzdesi = int((tamamlanan_blok / toplam_blok) * 100) if toplam_blok > 0 else 0

kpi1.metric(label="Toplam Üretim Bloğu", value=toplam_blok)
kpi2.metric(label="Tamamlanan Blok", value=tamamlanan_blok, delta=f"%{ilerleme_yuzdesi} Tamamlandı", delta_color="normal")
kpi3.metric(label="Toplam Planlanan Bütçe", value=f"${planlanan_maliyet:,.0f}")
kpi4.metric(label="Gerçekleşen Maliyet (Şu Ana Kadar)", value=f"${gerceklesen_maliyet:,.0f}", delta=f"${gerceklesen_maliyet - planlanan_maliyet:,.0f} Bütçe Sapması", delta_color="inverse")

# Görsel İlerleme Çubuğu Eklemesi
st.markdown("<br>", unsafe_allow_html=True)
st.write(f"**Genel Proje İlerlemesi:** %{ilerleme_yuzdesi}")
st.progress(ilerleme_yuzdesi)
st.markdown("---")


# 6. GRAFİKLER BÖLÜMÜ (Transparan arka plan ile)
col1, col2 = st.columns(2)

with col1:
    st.subheader("⚠️ İstasyon Bazlı Gecikme Analizi")
    gecikme_df = df_filtrelenmis.groupby("İstasyon")["Gecikme_Süresi_Gün"].sum().reset_index()
    fig_gecikme = px.bar(gecikme_df, x="İstasyon", y="Gecikme_Süresi_Gün", 
                         color="Gecikme_Süresi_Gün", color_continuous_scale="Reds")
    # Grafiği arayüze gömme dokunuşu
    fig_gecikme.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20, l=0, r=0))
    st.plotly_chart(fig_gecikme, use_container_width=True)

with col2:
    st.subheader("🔎 NDT (Kalite Kontrol) Dağılımı")
    kalite_df = df_filtrelenmis[df_filtrelenmis["NDT_Sonucu"] != "Muaf"]
    fig_kalite = px.pie(kalite_df, names="NDT_Sonucu", hole=0.4, # Ortası delik şık 'donut' grafik
                        color="NDT_Sonucu", color_discrete_map={"Geçti":"#28a745", "Kaldı - Yeniden İşlem":"#dc3545", "Bekliyor":"#ffc107"})
    fig_kalite.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20, l=0, r=0))
    st.plotly_chart(fig_kalite, use_container_width=True)

st.markdown("---")

# 7. ALT GRAFİKLER
col3, col4 = st.columns(2)

with col3:
    st.subheader("👷 Ekip Bütçe Analizi")
    ekip_maliyet_df = df_filtrelenmis.groupby("Uygulayıcı_Ekip")[["Planlanan_Maliyet_USD", "Gerçekleşen_Maliyet_USD"]].sum().reset_index()
    fig_ekip = px.bar(ekip_maliyet_df, x="Uygulayıcı_Ekip", y=["Planlanan_Maliyet_USD", "Gerçekleşen_Maliyet_USD"], 
                      barmode='group')
    fig_ekip.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20, l=0, r=0), legend_title_text='Maliyet Tipi')
    st.plotly_chart(fig_ekip, use_container_width=True)

with col4:
    st.subheader("📦 Gecikme Faktörleri")
    neden_df = df_filtrelenmis[df_filtrelenmis["Gecikme_Nedeni"] != "Yok"]
    fig_neden = px.histogram(neden_df, x="Gecikme_Nedeni", color="İstasyon")
    fig_neden.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20, l=0, r=0))
    st.plotly_chart(fig_neden, use_container_width=True)

st.markdown("---")

# 8. YAPAY ZEKA TERSANE ASİSTANI
