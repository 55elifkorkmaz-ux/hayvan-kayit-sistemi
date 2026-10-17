import streamlit as st
import pandas as pd
import requests

# --- BULUT VERİTABANI AYARLARI ---
AIRTABLE_PAT = "patXUITNrkOQB9zjX.2c2b9498057faf467e17fa47a825fb60590552367b57ee7da275ea9244015114"  # Buraya kendi PAT şifreni yaz
BASE_ID = "appo6RBZ3yvo3SOqh"      # Buraya kendi Base ID'ni yaz
TABLE_NAME = "tblDW7WjNTe1dgbs8"  # Buraya kendi Table ID'ni yaz

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}
BASE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

st.set_page_config(page_title="Hayvan Kayıt Sistemi", page_icon="🐾")

# Airtable'dan verileri canlı olarak çeken fonksiyon
def verileri_getir():
    # Görsel sırayı korumak için ?view=Grid%20view parametresi eklendi
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
        
        # Gizli ID'yi çıkar
        gosterilecek_df = gosterilecek_df.drop(columns=["id"], errors="ignore")
        
        # Sütunları mantıklı sıraya diz
        istenen_sira = ["İsim", "Tür", "Cinsiyet", "Aşı_Durumu", "Notlar"]
        mevcut_sutunlar = [col for col in istenen_sira if col in gosterilecek_df.columns]
        gosterilecek_df = gosterilecek_df[mevcut_sutunlar]
        
        # Sıralama numaralarını 1'den başlat
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
                        else:
                            veri_guncelle(record_id, yeni_isim.strip(), yeni_tur, yeni_cinsiyet, yeni_asi, yeni_notlar)
                            st.success(f"✅ {yeni_isim} bilgileri başarıyla güncellendi!")