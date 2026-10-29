import json
import re
import requests
from bs4 import BeautifulSoup

# Baza e plotë e linkut të kategorive për çdo dyqan
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
  if "rakiet" in url_L or "rakiet" in nazwa.lower():
    return "Rakiety"
  elif (
      "wyrzutni" in url_L
      or "wyrzutni" in nazwa.lower()
      or "bateria" in nazwa.lower()
      or "strzał" in nazwa.lower()
  ):
    return "Wyrzutnie"
  elif (
      "petard" in url_L
      or "petard" in nazwa.lower()
      or "emiter" in url_L
      or "dum bum" in nazwa.lower()
  ):
    return "Petardy"
  elif "wulkan" in url_L or "fontann" in url_L or "wulkan" in nazwa.lower():
    return "Wulkany"
  elif "single" in url_L or "shot" in url_L:
    return "Single Shot"
  elif "dym" in url_L or "stroboskop" in url_L or "bajer" in nazwa.lower():
    return "Piro-Bajery"
  return "Inne"


def skanuj_sklep(sklep_info):
  nazwa_sklepu = sklep_info["nazwa"]
  znalezione_promocje = []
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  for url in sklep_info["urls"]:
    print(
        f"🔎 Skanuję [ {nazwa_sklepu} ] -> {url} ...", end="", flush=True
    )
    try:
      response = requests.get(url, headers=headers, timeout=12)
      if response.status_code != 200:
        print(f" ⚠️ Status: {response.status_code}")
        continue

      soup = BeautifulSoup(response.text, "html.parser")
      produkty = soup.find_all(
          ["div", "li", "article", "section"],
          class_=re.compile(r"(product|item|box|oferta|col|elem)", re.I),
      )

      licznik = 0
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

        if not nazwa or len(nazwa) < 3:
          continue

        link = link_elem["href"]
        if not link.startswith("http"):
          base_url = "/".join(url.split("/")[:3])
          link = (
              base_url + link if link.startswith("/") else base_url + "/" + link
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
              if oferta not in znalezione_promocje:
                znalezione_promocje.append(oferta)
                licznik += 1

      print(f" ✅ Okazji: {licznik}")

    except Exception as e:
      print(f" ❌ Błąd: {e}")

  return znalezione_promocje


def glowny_skaner():
  baza_promocji = []
  for sklep in SKLEPY:
    wyniki = skanuj_sklep(sklep)
    baza_promocji.extend(wyniki)

  with open("promocje_pirotechnika.json", "w", encoding="utf-8") as f:
    json.dump(baza_promocji, f, ensure_ascii=False, indent=4)

  print(
      f"\n🎉 Skanowanie zakończone! Łączna liczba unikalnych okazji:"
      f" {len(baza_promocji)}"
  )


if __name__ == "__main__":
  glowny_skaner()