# 🎮 Game Price Finder

Eine Streamlit-Webanwendung zum Finden der besten Preise für PC-Spiele über verschiedene Online-Shops hinweg.


## Features

- **Spielsuche** - Durchsuche tausende PC-Spiele
- **Preisvergleich** - Vergleiche Preise über 30+ Online-Shops (Steam, GOG, Epic Games, etc.)
- **Zufallsgenerator** - Entdecke beliebte Spiele
- **Rabatt-Anzeige** - Sehe sofort welche Deals verfügbar sind
- **Shop-Filter** - Filtere nach deinen bevorzugten Shops
- **Detailinformationen** - Reviews, Tags, Systemanforderungen, Plattformen
- **Schnell** - Parallel-Requests und intelligentes Caching

## Schnellstart

### Installation

```bash
# Repository klonen
git clone https://github.com/deinusername/game-price-finder.git
cd game-price-finder

# Dependencies installieren
pip install -r requirements.txt
```

### API Key einrichten

Erstelle eine Datei `.streamlit/secrets.toml`:

```toml
API_KEY = "dein-isthereanydeal-api-key"
```

Hol dir einen kostenlosen API Key auf [IsThereAnyDeal.com](https://isthereanydeal.com/dev)

### App starten

```bash
streamlit run app.py
```

Die App öffnet sich automatisch unter `http://localhost:8501`

## Verwendung

1. **Spiel suchen**: Gib den Namen eines Spiels ein
2. **Shops wählen**: Filtere nach deinen bevorzugten Shops in den Einstellungen
3. **Preise vergleichen**: Sehe die besten 3 Deals für jedes Spiel
4. **Details ansehen**: Klicke auf die Expander für mehr Infos

## Technologien

- **Streamlit** - Web-Framework
- **IsThereAnyDeal API** - Spielpreis-Daten
- **Steam Web API** - Zusätzliche Spieldaten
- **Python Requests** - HTTP-Requests
- **ThreadPoolExecutor** - Parallele API-Calls

## Projektstruktur

```
game-price-finder/
├── app.py                      # Hauptanwendung
├── requirements.txt            # Dependencies
├── .streamlit/
│   └── secrets.toml           # API Keys


```


## 🙏 Credits

Powered by [IsThereAnyDeal.com](https://isthereanydeal.com)

---

⭐ Wenn dir dieses Projekt gefällt, gib ihm einen Star!