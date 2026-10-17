import streamlit as st
import pandas as pd
import requests

AIRTABLE_PAT = st.secrets["AIRTABLE_PAT"]
BASE_ID = st.secrets["BASE_ID"]
TABLE_NAME = st.secrets["TABLE_NAME"]

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}
BASE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

st.set_page_config(page_title="Hayvan Kayıt Sistemi", page_icon="🐾")

# --- GÜVENLİK DUVARI ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

if not st.session_state.giris_yapildi:
    st.subheader("🔒 Güvenli Giriş")
    # type="password" yazarken karakterleri nokta şeklinde gizler
    girilen_sifre = st.text_input("Lütfen 6 haneli erişim şifresini girin:", type="password")
    
    if st.button("Giriş Yap"):
       if girilen_sifre == st.secrets["SISTEM_SIFRESI"]::  # Kendi belirlediğin 6 haneli şifreyi buraya yaz
            st.session_state.giris_yapildi = True
            st.rerun()  # Sayfayı yenileyip sistemi açar
        else:
            st.error("Hatalı şifre! Lütfen tekrar deneyin.")
    
    # Şifre doğru girilene kadar kodun geri kalanını (veritabanı bağlantılarını) durdurur
    st.stop()  
# -----------------------

# Airtable'dan verileri canlı olarak çeken fonksiyon
def verileri_getir():
    response = requests.get(BASE_URL + "?view=Grid%20view", headers=HEADERS)
    if response.status_code == 200:
        kayitlar = response.json().get('records', [])
        data = []
        for r in kayitlar:
            row = r['fields']
            row['id'] = r['id']
            data.append(row)
        
        df = pd.DataFrame(data)
        beklenen_sutunlar = ["id", "İsim", "Tür", "Cinsiyet", "Aşı_Durumu", "Notlar"]
        for col in beklenen_sutunlar:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        st.error(f"Airtable Bağlantı Hatası: {response.text}")
        return pd.DataFrame()

def veri_ekle(isim, tur, cinsiyet, asi, notlar):
    data = {
        "records": [{"fields": {"İsim": isim, "Tür": tur, "Cinsiyet": cinsiyet, "Aşı_Durumu": asi, "Notlar": notlar}}]
    }
    requests.post(BASE_URL, headers=HEADERS, json=data)

def veri_guncelle(record_id, isim, tur, cinsiyet, asi, notlar):
    data = {
        "records": [{"id": record_id, "fields": {"İsim": isim, "Tür": tur, "Cinsiyet": cinsiyet, "Aşı_Durumu": asi, "Notlar": notlar}}]
    }
    requests.patch(BASE_URL, headers=HEADERS, json=data)

# --- ARAYÜZ ---
st.title("🐾 Hayvan Kayıt Sistemi (Bulut)")

menu = ["Yeni Kayıt Ekle", "Kayıtları Görüntüle", "Kayıt Düzenle"]
secim = st.sidebar.radio("Menü", menu)

df = verileri_getir()

if secim == "Yeni Kayıt Ekle":
    st.subheader("Yeni Hayvan Ekle")
    with st.form("kayit_formu", clear_on_submit=True):
        isim = st.text_input("Hayvanın Adı (Zorunlu)")
        tur = st.selectbox("Türü", ["Köpek", "Kedi", "Diğer"])
        cinsiyet = st.selectbox("Cinsiyeti", ["Dişi", "Erkek", "Bilinmiyor"])
        asi = st.text_input("Aşı / Parazit Bilgisi")
        notlar = st.text_area("Durum, Tedavi veya Notlar")
        
        if st.form_submit_button("Sisteme Kaydet"):
            if not isim.strip():
                st.error("Lütfen bir isim girin!")
            else:
                veri_ekle(isim.strip(), tur, cinsiyet, asi, notlar)
                st.success(f"✅ {isim} başarıyla eklendi! Listede görmek için sekmeyi yenileyin.")

elif secim == "Kayıtları Görüntüle":
    st.subheader("Kayıtlı Hayvanlar")
    if df.empty:
        st.info("Sistemde henüz hayvan bulunmuyor.")
    else:
        arama = st.text_input("🔍 İsim ile Ara:")
        gosterilecek_df = df.copy()
        
        if arama:
            gosterilecek_df = gosterilecek_df[gosterilecek_df["İsim"].astype(str).str.contains(arama, case=False, na=False)]
        
        gosterilecek_df = gosterilecek_df.drop(columns=["id"], errors="ignore")
        
        istenen_sira = ["İsim", "Tür", "Cinsiyet", "Aşı_Durumu", "Notlar"]
        mevcut_sutunlar = [col for col in istenen_sira if col in gosterilecek_df.columns]
        gosterilecek_df = gosterilecek_df[mevcut_sutunlar]
        
        gosterilecek_df.index = range(1, len(gosterilecek_df) + 1)
        st.dataframe(gosterilecek_df, use_container_width=True)

elif secim == "Kayıt Düzenle":
    st.subheader("Mevcut Kaydı Güncelle")
    if df.empty:
        st.info("Sistemde düzenlenecek hayvan bulunmuyor.")
    else:
        gecerli_isimler = df[df["İsim"] != ""]["İsim"].tolist()
        if not gecerli_isimler:
            st.info("Düzenlenecek geçerli bir isim bulunamadı.")
        else:
            secilen_isim = st.selectbox("Düzenlemek istediğiniz hayvanı seçin:", gecerli_isimler)
            
            if secilen_isim:
                secilen_satir = df[df["İsim"] == secilen_isim].iloc[0]
                record_id = secilen_satir["id"]
                
                with st.form("duzenleme_formu"):
                    yeni_isim = st.text_input("Hayvanın Adı", value=secilen_satir["İsim"])
                    
                    turler = ["Köpek", "Kedi", "Diğer"]
                    tur_idx = turler.index(secilen_satir["Tür"]) if secilen_satir["Tür"] in turler else 0
                    yeni_tur = st.selectbox("Türü", turler, index=tur_idx)
                    
                    cinsler = ["Dişi", "Erkek", "Bilinmiyor"]
                    cins_idx = cinsler.index(secilen_satir["Cinsiyet"]) if secilen_satir["Cinsiyet"] in cinsler else 2
                    yeni_cinsiyet = st.selectbox("Cinsiyeti", cinsler, index=cins_idx)
                    
                    mevcut_asi = "" if pd.isna(secilen_satir["Aşı_Durumu"]) else str(secilen_satir["Aşı_Durumu"])
                    yeni_asi = st.text_input("Aşı / Parazit Bilgisi", value=mevcut_asi)
                    
                    mevcut_not = "" if pd.isna(secilen_satir["Notlar"]) else str(secilen_satir["Notlar"])
                    yeni_notlar = st.text_area("Durum, Tedavi veya Notlar", value=mevcut_not)
                    
                    if st.form_submit_button("Değişiklikleri Kaydet"):
                        if not yeni_isim.strip():
                           st.error("İsim boş bırakılamaz!")
