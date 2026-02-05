import streamlit as st
import requests
import pandas as pd
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, as_completed



api_key = st.secrets["API_KEY"]

st.title("Marvins Preisvergleich")

st.markdown("""
    <style>
    div[data-testid="stVerticalBlock"][data-test-scroll-behavior="normal"] {
        background: #eec06b !important;
        padding: 20px !important;
        border-radius: 12px !important;
        margin: 10px 0 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1), 
                    0 1px 3px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid #e0e0e0 !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="stVerticalBlock"][data-test-scroll-behavior="normal"]:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 12px 24px rgba(0, 104, 201, 0.15), 
                    0 6px 12px rgba(0, 0, 0, 0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)

form = st.form("form", border=False)

title = form.text_input("Welches Spiel suchst du?", value="")

endpoints = {"search": "https://api.isthereanydeal.com/games/search/v1",
             "gameinfo": "https://api.isthereanydeal.com/games/info/v2",
             "prices": "https://api.isthereanydeal.com/games/prices/v3",
             "price_overview": "https://api.isthereanydeal.com/games/overview/v2"
             }

headers = {"Accept": "application/json", "User-Agent": "my-test-client/1.0"}


def find_id_by_title(title: str, max_games=50) -> dict:
    url = endpoints.get("search")
    params = {"key": api_key, "title": title, "country": "DE", "results": max_games}
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    if resp.status_code == 200:
        resp = resp.json()
        results = []
        for item in resp:
             item_title = item.get("title")
             id = item.get("id")
             result = {"title": item_title,
                     "id": id} 
             results.append(result)
        return results
    else:
        return [] 
    
def get_game_info(id:str) -> dict:
    url = endpoints.get("gameinfo")
    params = {"key": api_key, "id": id} 
    resp = requests.get(url,params=params, headers=headers, timeout=15)
    if resp.status_code == 200:
        game = resp.json()
        assets = game.get("assets", {})
        result = {
            "title": game.get("title"),
            "image": assets.get("banner400"),
            "releasedate": game.get("releaseDate"),
            "publishers": game.get("publishers"),
            "developers": game.get("developers"),
            "tags": game.get("tags"),
            "reviews": game.get("reviews"),
            "type": game.get("type")
        }
        
        return result

def get_prices(ids: list) -> dict:
    url = endpoints.get("prices")
    params = {"key": api_key, "country": "DE"}
    resp = requests.post(url=url,params=params, headers=headers, json=ids, timeout=15)
    return resp.json()

def get_price_overview(ids: list) -> dict:
    url = endpoints.get("price_overview")
    params = {"key": api_key, "country": "DE"}
    resp = requests.post(url=url,params=params, headers=headers, json=ids, timeout=15)
    return resp.json()

def get_shops(country: str = "DE") -> list:
    """Holt alle verfügbaren Shops für ein Land"""
    url = "https://api.isthereanydeal.com/service/shops/v1"
    params = {
        "key": api_key,
        "country": country
    }
    
    resp = requests.get(url, params=params, headers=headers, timeout=15)

    return resp.json()

submit = form.form_submit_button("Los", type="primary")        
if submit:
    if not title.strip():
        st.toast("Du musst einen Titel eingeben.", icon=":material/warning:")
    else:
        st.toast(f"Suche {title}...", icon=":material/search:")
        ids = find_id_by_title(title=title)
        
        # Parallel fetchen
        with ThreadPoolExecutor(max_workers=5) as executor: #max 5 Worker gleichzeitig
            
            # Alle IDs sammeln
            id_list = [id_item.get("id") for id_item in ids]
        
            # Alle Requests starten
            future_to_id = {
                executor.submit(get_game_info, id_item.get("id")): id_item 
                for id_item in ids
            }

                
            # Preis-Request parallel starten (ein Request für alle IDs)
            price_future = executor.submit(get_prices, id_list)

            all_prices_list = price_future.result()
                        
            all_prices = {item.get("id"): item for item in all_prices_list}

            
            # Ergebnisse sammeln
            for future in as_completed(future_to_id):
                
                game_id = future_to_id[future].get("id")

                price_data = all_prices.get(game_id, {})
                
                deals = price_data.get("deals", [])
                
                info = future.result()
                
                is_game = False
                if info.get("type") == "game":
                    is_game = True

                if info and is_game:
                    with st.container(border=True):
                        st.subheader(info.get("title"), divider="yellow")
                        col1, col2 = st.columns(2)
                        with col1:
                            if info.get("image") != None:
                                st.image(info.get("image"))
                            else:
                                with st.container(width=400):
                                    st.warning("Kein Bild verfügbar")
                            
                            if deals:
                                with st.expander(expanded=True, label="Beste Preise", icon=":material/euro_symbol:"):
                                    for deal in deals[0:3]:
                                        #best_deal = deals[0]  # Erster ist meist der günstigste
                                        shop_name = deal.get("shop", {}).get("name", "Unknown")
                                        price = deal.get("price", {}).get("amount", 0)
                                        cut = deal.get("cut", 0)
                                        url = deal.get("url", "")
                                        if url:
                                            url = unquote(url)
                                            st.metric(
                                                label=f"Preis bei ({shop_name})",
                                                value=f"{price:.2f}€",
                                                delta=f"-{cut}%" if cut > 0 else None
                                            )
                                            if url:
                                                st.link_button("Zum Angebot", url, type="primary")
                                        else:
                                            st.warning("Keine Deals")

                        with col2:
                            if info.get("releasedate") != None:
                                st.metric("Release", value=info.get("releasedate"))
                            else: 
                                st.caption(f"Release: unbekannt")
                            if info.get("publishers"):
                                publishers = info.get("publishers")
                                publisher = publishers[0]
                                st.metric("Publisher", value=publisher.get("name"))                             
                                
                            else: 
                                st.caption("Publisher: unbekannt")
                            if info.get("tags") != None:
                                st.markdown("<sub>Tags</sub>", unsafe_allow_html=True)
                                with st.container(horizontal=True):
                                    tags = info.get("tags") 
                                    if tags:
                                        for tag in tags:
                                            st.badge(tag, color="orange")
                                    else:
                                        st.badge("keine Reviews", color="gray")
                            else: 
                                st.caption("keine Tags")
                            if info.get("reviews") != None:
                                reviews = info.get("reviews")
                                st.markdown("<sub>Reviews</sub>", unsafe_allow_html=True)
                                if reviews:
                                    for review in reviews:
                                        score = review.get("score")
                                        source = str(review.get("source"))
                                        col1, col2, col3 = st.columns([3,2,5])   
                                        with col1:
                                                st.caption(source)
                                        with col2:
                                            try:
                                                if score < 50:
                                                    st.badge(str(score), color="red")
                                                elif score >= 50 and score <= 75:
                                                    st.badge(str(score), color="orange")
                                                else:
                                                    st.badge(str(score), color="green")
                                            except:
                                                st.badge("/")
                                        with col3:
                                            st.empty()
                                else:
                                    st.badge("Keine Reviews", color="gray")

    
