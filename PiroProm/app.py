import datetime
import json
import os
import re
import requests
import streamlit as st
from bs4 import BeautifulSoup

# Konfiguracja strony
st.set_page_config(
    page_title="PiroPromo - Agregator Pirotechniki",
    page_icon="🧨",
    layout="wide",
)

st.title("🧨 PiroPromo – Agregator Promocji Pirotechnicznych")
st.write(
    "Wszystkie aktualne okazje i kody rabatowe w jednym miejscu. Skanuj i"
    " oszczędzaj!"
)

PLIK_BAZY = "promocje_pirotechnika.json"

# Lista ścisłych adresów kategorii
SKLEPY = [
    {
        "nazwa": "Pirozaur",
        "urls": [
            "https://www.pirozaur.pl/4-wyrzutnie",
            "https://www.pirozaur.pl/5-petardy-i-emitery",
            "https://www.pirozaur.pl/6-rakiety",
            "https://www.pirozaur.pl/7-rzymskie-ognie-i-gatlingi",
            "https://www.pirozaur.pl/8-wulkany",
            "https://www.pirozaur.pl/12-dymyrace",
            "https://www.pirozaur.pl/10-pirobajery",
        ],
    },
    {
        "nazwa": "PiroShop",
        "urls": [
            "https://piroshop.pl/pl/14-petardy",
            "https://piroshop.pl/pl/16-swiece-dymne",
            "https://piroshop.pl/pl/15-wyrzutnie",
            "https://piroshop.pl/pl/17-stroboskopy",
            "https://piroshop.pl/pl/19-wulkany",
            "https://piroshop.pl/pl/20-single-shot",
            "https://piroshop.pl/pl/22-pirobajery",
        ],
    },
    {
        "nazwa": "PiroHit",
        "urls": [
            "https://pirohit.pl/Rakiety-c19",
            "https://pirohit.pl/Wyrzutnie-c20",
            "https://pirohit.pl/Wulkany-Fontanny-c18",
            "https://pirohit.pl/pl/race-i-flary-c28",
            "https://pirohit.pl/Stroboskopy-c21",
            (
                "https://pirohit.pl/pl/menu/ognie-wroclawskie-i-bengalskie-555.html"
            ),
            "https://pirohit.pl/Piro-Bajery-c16",
            "https://pirohit.pl/Rzymskie-ognie-c30",
            "https://pirohit.pl/Single-Shoty-Mozdzierze-c23",
        ],
    },
    {
        "nazwa": "TanieFajerwerki",
        "urls": [
            "https://taniefajerwerki.pl/kategoria/wyrzutnie/59",
            "https://taniefajerwerki.pl/kategoria/emiter-dzwieku/98",
            "https://taniefajerwerki.pl/kategoria/fontanny/63",
            "https://taniefajerwerki.pl/kategoria/mozdzierze/66",
            "https://taniefajerwerki.pl/kategoria/petardy/65",
            "https://taniefajerwerki.pl/kategoria/piro-bajery/80",
            "https://taniefajerwerki.pl/kategoria/rakiety/61",
            "https://taniefajerwerki.pl/kategoria/rzymskie-ognie/62",
        ],
    },
    {
        "nazwa": "PiroNet",
        "urls": [
            "https://pironet.pl/kategoria-produktu/piro-bajery/",
            "https://pironet.pl/kategoria-produktu/wyrzutnie/",
            "https://pironet.pl/kategoria-produktu/rakiety/",
            "https://pironet.pl/kategoria-produktu/single-shoty/",
            "https://pironet.pl/kategoria-produktu/rzymskie-ognie/",
            "https://pironet.pl/kategoria-produktu/rzymskie-ognie/gatling/",
            "https://pironet.pl/kategoria-produktu/wulkany-i-fontanny/",
        ],
    },
    {
        "nazwa": "FajerwerkiMarket",
        "urls": [
            "https://www.fajerwerkimarket.pl/category/petardy",
            "https://www.fajerwerkimarket.pl/category/petardy-emitery-dzwieku",
            "https://www.fajerwerkimarket.pl/category/artykuly-rozne",
            "https://www.fajerwerkimarket.pl/category/single-shoty",
            "https://www.fajerwerkimarket.pl/category/motyle",
            "https://www.fajerwerkimarket.pl/category/co-poleca-machony-flash",
            "https://www.fajerwerkimarket.pl/category/fontanny",
            "https://www.fajerwerkimarket.pl/category/rakiety",
            "https://www.fajerwerkimarket.pl/category/wyrzutnie",
            "https://www.fajerwerkimarket.pl/category/rzymskie-ognie",
        ],
    },
    {
        "nazwa": "Odpalaj.pl",
        "urls": [
            "https://odpalaj.pl/pl/18-wyrzutnie-baterie-fajerwerkow",
            "https://odpalaj.pl/pl/16-single-shoty",
            "https://odpalaj.pl/pl/11-petardy",
            "https://odpalaj.pl/pl/17-rakiety",
            "https://odpalaj.pl/pl/19-rzymskie-ognie",
            "https://odpalaj.pl/pl/20-wulkany",
            "https://odpalaj.pl/pl/64-stroboskopy-petardy",
        ],
    },
]

KODY_RABATOWE = {
    "Wszystkie sklepy": {"kod": "BRAK", "rabat": 0},
    "Pirozaur": {"kod": "PIROZAUR5", "rabat": 5},
    "PiroShop": {"kod": "SHOP10", "rabat": 10},
    "PiroHit": {"kod": "HITFIGHT", "rabat": 5},
    "TanieFajerwerki": {"kod": "TANIO15", "rabat": 15},
    "PiroNet": {"kod": "PIRONET5", "rabat": 5},
    "FajerwerkiMarket": {"kod": "MARKET10", "rabat": 10},
    "Odpalaj.pl": {"kod": "ODPALAJ5", "rabat": 5},
}

CZARNA_LISTA = [
    "sprzedaż",
    "najwyższej",
    "najniższej",
    "sortuj",
    "cena",
    "pokaż",
    "filtruj",
    "kategoria",
    "dodaj do koszyka",
    "promocje",
]


def czysc_cene(cena_str):
  if not cena_str:
    return 0.0
  cena_czysta = re.sub(r"[^\d,\.]", "", cena_str).replace(",", ".")
  try:
    return float(cena_czysta)
  except ValueError:
    return 0.0


def okresl_kategorie(nazwa, url_kategorii=""):
  url_L = url_kategorii.lower()
  nazwa_L = nazwa.lower()
  if "rakiet" in url_L or "rakiet" in nazwa_L:
    return "Rakiety"
  elif (
      "wyrzutni" in url_L
      or "wyrzutni" in nazwa_L
      or "bateria" in nazwa_L
      or "strzał" in nazwa_L
  ):
    return "Wyrzutnie"
  elif (
      "petard" in url_L
      or "petard" in nazwa_L
      or "emiter" in url_L
      or "dum bum" in nazwa_L
  ):
    return "Petardy"
  elif "wulkan" in url_L or "fontann" in url_L or "wulkan" in nazwa_L:
    return "Wulkany"
  elif "single" in url_L or "shot" in url_L:
    return "Single Shot"
  elif "dym" in url_L or "stroboskop" in url_L or "bajer" in nazwa_L:
    return "Piro-Bajery"
  return "Inne"


def uruchom_skaner():
  baza_promocji = []
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  for sklep in SKLEPY:
    nazwa_sklepu = sklep["nazwa"]
    for url in sklep["urls"]:
      try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
          continue
        soup = BeautifulSoup(response.text, "html.parser")
        produkty = soup.find_all(
            ["div", "li", "article", "section"],
            class_=re.compile(r"(product|item|box|oferta|col|elem)", re.I),
        )

        for item in produkty:
          link_elem = item.find("a", href=True)
          if not link_elem:
            continue
          nazwa = link_elem.text.strip()

          if len(nazwa) < 3:
            nazwa_elem = item.find(
                ["h2", "h3", "span", "a"],
                class_=re.compile(r"(name|title|product-name)", re.I),
            )
            if nazwa_elem:
              nazwa = nazwa_elem.text.strip()

          if (
              not nazwa
              or len(nazwa) < 3
              or any(bad in nazwa.lower() for bad in CZARNA_LISTA)
          ):
            continue

          link = link_elem["href"]
          if not link.startswith("http"):
            base_url = "/".join(url.split("/")[:3])
            link = (
                base_url + link
                if link.startswith("/")
                else base_url + "/" + link
            )

          ceny_tekst = item.find_all(string=re.compile(r"\d+[\.,]?\d*\s*zł"))
          if len(ceny_tekst) >= 2:
            cena_stara = czysc_cene(ceny_tekst[0])
            cena_nowa = czysc_cene(ceny_tekst[1])
            if cena_stara < cena_nowa:
              cena_stara, cena_nowa = cena_nowa, cena_stara

            if cena_stara > cena_nowa and cena_stara > 0:
              znizka_procent = round(
                  ((cena_stara - cena_nowa) / cena_stara) * 100
              )
              if 1 <= znizka_procent <= 80:
                kategoria = okresl_kategorie(nazwa, url)
                oferta = {
                    "sklep": nazwa_sklepu,
                    "kategoria": kategoria,
                    "nazwa": nazwa,
                    "cena_stara": cena_stara,
                    "cena_promocyjna": cena_nowa,
                    "znizka_procent": znizka_procent,
                    "link": link,
                }
                if oferta not in baza_promocji:
                  baza_promocji.append(oferta)
      except Exception:
        continue

  with open(PLIK_BAZY, "w", encoding="utf-8") as f:
    json.dump(baza_promocji, f, ensure_ascii=False, indent=4)


# PANEL BOCZNY
st.sidebar.header("🕒 Status i Skanowanie")
if os.path.exists(PLIK_BAZY):
  czas_modyfikacji = os.path.getmtime(PLIK_BAZY)
  data_ostatniego = datetime.datetime.fromtimestamp(
      czas_modyfikacji
  ).strftime("%H:%M:%S, %d-%m-%Y")
  st.sidebar.info(f"📡 Baza zaktualizowana:\n**{data_ostatniego}**")
else:
  st.sidebar.warning("⚠️ Brak bazy danych. Wymagane pierwsze skanowanie!")

if st.sidebar.button(
    "🔄 Przeszukaj sklepy od nowa", type="primary", use_container_width=True
):
  with st.spinner("⏳ Skanuję wszystkie sklepy..."):
    uruchom_skaner()
    st.rerun()

# Wczytywanie bazy danych
try:
  with open(PLIK_BAZY, "r", encoding="utf-8") as f:
    dane = json.load(f)
except FileNotFoundError:
  dane = []

st.sidebar.markdown("---")
st.sidebar.header("🎛️ Filtry i Kody")

unikalne_sklepy = sorted(list(set(p["sklep"] for p in dane))) if dane else []
wybrany_sklep_filter = st.sidebar.selectbox(
    "🛒 Filtruj po sklepie:", ["Wszystkie"] + unikalne_sklepy, index=0
)

# Reakcja na wybór kodu z automatycznym odświeżaniem
def aktualizuj_rabat():
  sklep = st.session_state.sklep_kod_select
  st.session_state.dodatkowy_rabat_slider = KODY_RABATOWE[sklep]["rabat"]


sklep_dla_kodu = st.sidebar.selectbox(
    "🎁 Wybierz sklep z kodem:",
    list(KODY_RABATOWE.keys()),
    index=0,
    key="sklep_kod_select",
    on_change=aktualizuj_rabat,
)

domyslny_rabat = KODY_RABATOWE[sklep_dla_kodu]["rabat"]
aktywny_kod = KODY_RABATOWE[sklep_dla_kodu]["kod"]

if "dodatkowy_rabat_slider" not in st.session_state:
  st.session_state.dodatkowy_rabat_slider = domyslny_rabat

if aktywny_kod != "BRAK":
  st.sidebar.success(
      f"✅ Kod dla **{sklep_dla_kodu}**: `{aktywny_kod}` (**-{domyslny_rabat}%**)"
  )

if dane:
  col_f1, col_f2 = st.columns(2)
  with col_f1:
    szukana_nazwa = st.text_input(
        "🔍 Szukaj produktu (np. Supernova, Dum Bum):"
    ).lower()
  with col_f2:
    kategorie = [
        "Wszystkie",
        "Wyrzutnie",
        "Rakiety",
        "Petardy",
        "Wulkany",
        "Single Shot",
        "Piro-Bajery",
        "Inne",
    ]
    wybrana_kategoria = st.selectbox(
        "📂 Wybierz kategorię:", kategorie, index=0
    )

  col_s1, col_s2 = st.columns(2)
  with col_s1:
    # Ustawiamy domyślny suwak na 0%, aby nie ucinało promocji
    min_procent = st.slider("📉 Minimalny % zniżki:", 0, 80, 0, step=1)
  with col_s2:
    dodatkowy_rabat = st.slider(
        "🎁 Dodatkowy rabat z kodu (%):",
        0,
        30,
        key="dodatkowy_rabat_slider",
        step=1,
    )

  przefiltrowane = []
  for p in dane:
    if any(bad in p["nazwa"].lower() for bad in CZARNA_LISTA):
      continue
    if szukana_nazwa and szukana_nazwa not in p["nazwa"].lower():
      continue
    if p["znizka_procent"] < min_procent:
      continue
    if (
        wybrana_kategoria != "Wszystkie"
        and p["kategoria"].lower() != wybrana_kategoria.lower()
    ):
      continue
    if (
        wybrany_sklep_filter != "Wszystkie"
        and p["sklep"] != wybrany_sklep_filter
    ):
      continue

    przefiltrowane.append(p)

  st.markdown(
      f"### 🎯 Znaleziono pasujących okazji: **{len(przefiltrowane)}**"
  )
  st.markdown("---")

  if not przefiltrowane:
    st.warning(
        "Brak produktów spełniających podane kryteria. Zmniejsz minimalną zniżkę"
        " na suwaku."
    )

  for p in przefiltrowane:
    cena_koncowa = p["cena_promocyjna"] * (1 - dodatkowy_rabat / 100)

    with st.container():
      st.markdown(
          """
            <style>
            .product-box {
                background-color: #161b22;
                border: 1px solid #30363d;
                padding: 18px;
                border-radius: 10px;
                margin-bottom: 15px;
            }
            .shop-btn {
                background-color: #ff4b4b;
                color: white !important;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                text-decoration: none;
                display: block;
                text-align: center;
            }
            .shop-btn:hover {
                background-color: #e03e3e;
            }
            </style>
            """,
          unsafe_allow_html=True,
      )

      st.markdown('<div class="product-box">', unsafe_allow_html=True)
      c1, c2 = st.columns([3, 1])

      with c1:
        st.subheader(f"🧨 {p['nazwa']}")
        st.write(
            f"🛒 **Sklep:** `{p['sklep']}` | 📂 **Kategoria:**"
            f" `{p['kategoria']}`"
        )
        st.write(
            f"💰 Stara cena: ~~{p['cena_stara']} zł~~ | Cena promocyjna:"
            f" **{p['cena_promocyjna']} zł** :red[**(-{p['znizka_procent']}%)**]"
        )
        if dodatkowy_rabat > 0:
          st.markdown(
              f"🎁 **Cena z kodem rabatowym (-{dodatkowy_rabat}%):**"
              f" :green[**{cena_koncowa:.2f} zł**]"
          )

      with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        # Poprawiony czysty przycisk bez błędnych znaczników
        st.markdown(
            f'<a href="{p["link"]}" target="_blank" class="shop-btn">🔗 Otwórz'
            " produkt</a>",
            unsafe_allow_html=True,
        )

      st.markdown("</div>", unsafe_allow_html=True)
else:
  st.warning(
      "Brak bazy danych! Kliknij przycisk **'Przeszukaj sklepy od nowa'** w"
      " panelu po lewej stronie."
  )