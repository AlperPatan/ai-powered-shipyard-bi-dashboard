import streamlit as st
import base64
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# 1. SAYFA AYARLARI
st.set_page_config(page_title="Tersane Üretim Dashboard", page_icon="🚢", layout="wide")

# --- ÖZEL CSS TASARIMI (JİLET GİBİ GÖRÜNÜM İÇİN) ---
st.markdown("""
<style>
    
    [data-testid="stMetric"] {
        background-color: rgba(30, 30, 46, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        transition: all 0.3s ease-in-out;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-6px);
        border: 1px solid rgba(0, 212, 255, 0.8);
        box-shadow: 0 8px 20px rgba(0, 212, 255, 0.2);
    }
    /* Ana başlık tipografisi */
    h1 {
        font-weight: 700 !important;
        letter-spacing: 1px;
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
    # Klasöründeki stock1.mp4 dosyasını okuyoruz
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
    # Eğer isimlendirmede hata olursa uygulama çökmesin diye yedek başlık
    st.title("🚢 Tersane Üretim & Blok Takip Merkezi")
    st.markdown("---")

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
st.header("🤖 Akıllı Tersane Asistanı (Gemini AI)")
st.markdown("Tersane verilerindeki darboğazları veya verimlilik önerilerini yapay zekaya sorun.")

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-flash-latest') 
    
    kullanici_sorusu = st.text_input("Örn: Hangi taşeron firmayı değiştirmeliyiz? / En çok gecikme hangi siparişte?")
    
    if st.button("🔍 Verileri Analiz Et") and kullanici_sorusu:
        with st.spinner("Yapay zeka verileri analiz edip raporluyor..."):
            sorunlu_veri = df_filtrelenmis[df_filtrelenmis["Gecikme_Süresi_Gün"] > 0]
            if len(sorunlu_veri) > 50:
                sorunlu_veri = sorunlu_veri.head(50)
                
            veri_ozeti = sorunlu_veri.to_csv(index=False)
            genel_durum = f"""
            Toplam İncelenen Blok: {len(df_filtrelenmis)}
            Tamamlanan Blok: {len(df_filtrelenmis[df_filtrelenmis['Durum'] == 'Tamamlandı'])}
            Toplam Planlanan Bütçe: ${df_filtrelenmis['Planlanan_Maliyet_USD'].sum():,.0f}
            Toplam Gerçekleşen Bütçe: ${df_filtrelenmis['Gerçekleşen_Maliyet_USD'].sum():,.0f}
            """
            prompt = f"""
            Sen uzman bir Tersane Üretim Yöneticisi ve Veri Analistisin. 
            Aşağıda projenin genel durumu ve sadece 'gecikme/sorun yaşayan' kritik blokların tablosu verilmiştir.
            Genel Durum:\n{genel_durum}\nKritik (Gecikmeli) Bloklar:\n{veri_ozeti}
            Kullanıcının Sorusu: {kullanici_sorusu}
            Doğrudan bu verilere dayanarak kısa, net ve profesyonel bir analiz sun.
            """
            try:
                response = model.generate_content(prompt)
                st.info(response.text)
            except Exception as e:
                st.warning("⚠️ Yapay zeka ile bağlantı şu an kurulamadı. Lütfen birazdan tekrar deneyin.")
                
except KeyError:
    st.error("❌ Hata: API Key bulunamadı. Lütfen .streamlit/secrets.toml dosyasını kontrol edin.")