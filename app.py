import streamlit as st
import requests
import pandas as pd
import random
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, as_completed


endpoints = {"search": "https://api.isthereanydeal.com/games/search/v1",
             "gameinfo": "https://api.isthereanydeal.com/games/info/v2",
             "prices": "https://api.isthereanydeal.com/games/prices/v3",
             "price_overview": "https://api.isthereanydeal.com/games/overview/v2",
             "game_lookup": "https://api.isthereanydeal.com/games/lookup/v1",
             "mostplayed": "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
             }

headers = {"Accept": "application/json", "User-Agent": "my-test-client/1.0"}


def find_id_by_title(title: str, max_games=100) -> dict:
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
    
def get_random_game_title():
    
    if "random_game" not in st.session_state:
        st.session_state.random_game = None

    while True:
        most_played_ids = get_most_played_games()
        random_appid = random.choice(most_played_ids)
        url = endpoints.get("game_lookup")
        params = {"key": api_key, "appid": random_appid}
        resp = requests.get(url=url,params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            resp = resp.json()

            game = resp.get("game")
            if game:
                st.session_state.random_game = game.get("title")
                return game.get("title")         

def get_most_played_games():
    url = endpoints.get("mostplayed")
    resp = requests.get(url=url, headers=headers)
    if resp.status_code == 200:
        resp = resp.json()
        resp = resp.get("response")
        ranks = (resp.get("ranks"))
        appids = []
        for rank in ranks:
            appid = rank.get("appid")
            appids.append(appid)
        return appids
    
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

def filter_deals_by_shops(deals, selected_shops, shops_dict):
    """Filtert Deals nach ausgewählten Shops"""
    valid_shops = [shops_dict[shop] for shop in selected_shops]
    
    filtered_deals = []
    for deal in deals:
        shop_id = deal["shop"]["id"]
        if shop_id in valid_shops:
            filtered_deals.append(deal)
    
    return filtered_deals

def is_valid_game(info):
    """Prüft ob ein gültiges Spiel mit Deals vorliegt"""
    is_game = info.get("type") == "game"
    return is_game

def load_custom_containers():
    st.markdown("""
        <style>
        div[data-testid="stVerticalBlock"][data-test-scroll-behavior="normal"] {
            background: #eec06b !important;
            padding: 20px !important;
            border-radius: 12px !important;
            margin: 10px 0 !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1), 
                        0 1px 3px rgba(0, 0, 0, 0.08) !important;
            border: 1px solid #03071E !important;
            transition: all 0.3s ease !important;
        }
        
        div[data-testid="stVerticalBlock"][data-test-scroll-behavior="normal"]:hover {
            transform: translateY(-5px) !important;
            box-shadow: 0 12px 24px rgba(0, 104, 201, 0.15), 
                        0 6px 12px rgba(0, 0, 0, 0.1) !important;
        }
        </style>
        """, unsafe_allow_html=True)

def init_counter():
    if "counter" not in st.session_state:
        st.session_state.counter = 0
    
def reset_counter():
    st.session_state.counter = 0

def display_counter_results():
    if "message_container" not in st.session_state:
        st.session_state.message_container = None

    if st.session_state.counter < 1:
        st.session_state.message_container.warning("Keine Deals in den ausgewählten Shops gefunden")

    if st.session_state.counter == 1:
        st.session_state.message_container.success(f"{st.session_state.counter} Spiel gefunden!", icon=":material/check_circle:")

    if st.session_state.counter > 1:
        st.session_state.message_container.success(f"{st.session_state.counter} Spiele gefunden!", icon=":material/check_circle:")

def display_game_image(image_url):
    """Zeigt Spielbild oder Fallback"""
    if image_url:
        st.image(image_url)
    else:
        with st.container(width=400):
            st.warning("Kein Bild verfügbar")

def display_best_deals(deal_shops):
    """Zeigt die besten 3 Deals"""
    if not deal_shops:
        st.warning("Keine Deals in den ausgewählten Shops :(")
        return
    
    with st.expander(expanded=True, label="Beste Preise", icon=":material/euro_symbol:"):
        for deal in deal_shops[0:3]:
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
                st.link_button("Zum Angebot", url, type="primary")

def display_game_metadata(info):
    """Zeigt Release, Publisher, Tags"""
    # Release Date
    release = info.get("releasedate")
    if release:
        st.metric("Release", value=release)
    else:
        st.caption("Release: unbekannt")
    
    # Publisher
    publishers = info.get("publishers")
    if publishers:
        st.metric("Publisher", value=publishers[0].get("name"))
    else:
        st.caption("Publisher: unbekannt")

def display_tags(tags):
    """Zeigt Tags als Badges"""
    st.markdown("<sub>Tags</sub>", unsafe_allow_html=True)
    with st.container(horizontal=True):
        if tags:
            for tag in tags:
                st.badge(tag, color="red")
        else:
            st.badge("keine Reviews", color="gray")

def display_reviews(reviews):
    """Zeigt Review-Scores"""
    st.markdown("<sub>Reviews</sub>", unsafe_allow_html=True)
    
    if not reviews:
        st.badge("Keine Reviews", color="gray")
        return
    
    for review in reviews:
        score = review.get("score")
        source = str(review.get("source"))
        
        col1, col2, col3 = st.columns([3, 2, 5])
        with col1:
            st.caption(source)
        with col2:
            _display_score_badge(score)
        with col3:
            st.empty()

def _display_score_badge(score):
    """Helper für Score-Badge-Farbe"""
    try:
        if score < 50:
            st.badge(str(score), color="red")
        elif score <= 75:
            st.badge(str(score), color="orange")
        else:
            st.badge(str(score), color="green")
    except:
        st.badge("/")

def display_game_card(info, deal_shops):
    """Zeigt eine komplette Spielkarte"""
    with st.container(border=True):
        st.subheader(f"{st.session_state.counter}. {info.get("title")}", divider="red",)
        
        col1, col2 = st.columns(2)
        
        with col1:
            display_game_image(info.get("image"))
            display_best_deals(deal_shops)
        
        with col2:
            display_game_metadata(info)
            
            if info.get("tags"):
                display_tags(info.get("tags"))
            else:
                st.caption("keine Tags")
            
            if info.get("reviews"):
                display_reviews(info.get("reviews"))

def get_secrets():
    try:
        api_key = st.secrets["API_KEY"]
        return api_key
    except KeyError:
        st.error("API Key nicht gefunden. Bitte füge deinen API Key in den Streamlit-Secrets hinzu.")
        st.stop()

api_key = get_secrets()

st.title("Hi!")
st.markdown("Gib den **Namen** eines Spiels ein und finde den <ins>günstigsten</ins> Preis.",unsafe_allow_html=True )


init_counter()

if 'selected_shops' not in st.session_state:
    st.session_state.selected_shops = ["Steam", "GOG"]

if "random_game" not in st.session_state:
    st.session_state.random_game = get_random_game_title()

# Shops Dict erstellen
shops = get_shops()
shops_dict = {}
for shop in shops:
    name = shop.get("title")
    id = shop.get("id")
    shops_dict[name] = id

col1, col2 = st.columns([9,1])
with col1:
    title = st.text_input("Welches Spiel suchst du?", value=st.session_state.random_game, label_visibility="collapsed")
with col2:
    randomizer_button = st.button("", on_click=get_random_game_title, icon=":material/autorenew:", width="stretch")    

with st.expander("Einstellungen", expanded=False):
    col1, col2 = st.columns(2, border=True)
    with col1:
        st.subheader("Nach Shops filtern")
        
        select_shops = st.multiselect(
            "Shops auswählen", 
            options=shops_dict.keys(),
            default=st.session_state.selected_shops
        )
        with st.container(horizontal=True):
            all_shops_btn = st.button("Alle Shops auswählen")
            remove_all_shops_btn = st.button("Alle Shops entfernen")
            default_btn = st.button("Auf Default zurücksetzen")
    with col2:
        st.subheader("nach Publisher filtern")

    max_res = st.select_slider("Max. Ergebnisse", options=range(1,101), value=50)

col1, col2 = st.columns([2,8])
with col1:
    submit = st.button("Los", type="primary", use_container_width=True)
with col2:
    message_placeholder = st.empty()
    st.session_state.message_container = message_placeholder

load_custom_containers()

# Buttons prüfen
if all_shops_btn:
    st.session_state.selected_shops = list(shops_dict.keys())
    st.rerun()

if remove_all_shops_btn:
    st.session_state.selected_shops = None
    st.rerun()

if default_btn:
    st.session_state.selected_shops = ["Steam", "GOG"]
    st.rerun()

if submit:
    reset_counter()

    if not title.strip():
        st.toast("Du musst einen Titel eingeben.", icon=":material/warning:")
    elif not select_shops:
        st.toast("Du musst mind. einen Shop auswählen", icon=":material/warning:")
    else:
        with st.spinner("Suche nach Spielen..."):
            ids = find_id_by_title(title=title, max_games=max_res)
            
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
                    reviews = info.get("reviews", [])
                    image = info.get("image")
                    tags = info.get("tags")
                    
                    is_game = is_valid_game(info)
                    
                    # Shops filtern
                    deal_shops = filter_deals_by_shops(deals, st.session_state.selected_shops, shops_dict)         

                    if is_game and deal_shops:
                        st.session_state.counter += 1
                        display_game_card(info, deal_shops)

st.markdown("""
            <small> powered by <a href="http://www.isthereanydeal.com">isthereanydeal.com</a> 
            </small>""", unsafe_allow_html=True)

