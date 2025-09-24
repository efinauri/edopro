import requests
import sqlite3
import os
from urllib.parse import urlencode

# --- CONFIGURATION ---
POINTS_API = "https://registration.yugioh-card.com/genesys/CardListSearch/PointsList"
CARDS_TXT_PATH = "genesys_cards.txt"

DELTA_LOCAL_CDB = os.path.expanduser("./repositories/babel-cdb/cards.delta.cdb")
DELTA_RAW_CDB_URL = "https://github.com/ProjectIgnis/BabelCDB/raw/refs/heads/master/cards.cdb"
OUTPUT_BANLIST_PATH = os.path.expanduser("~/Games/ProjectIgnis/lflists/genesys.txt")

DEFAULT_HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://registration.yugioh-card.com",
    "referer": "https://registration.yugioh-card.com/genesys/CardList/",
    "x-requested-with": "XMLHttpRequest",
    "user-agent": "Mozilla/5.0",
}
DEFAULT_COOKIES = {}

def ensure_delta_cdb_local(path=DELTA_LOCAL_CDB, remote=DELTA_RAW_CDB_URL):
    if os.path.isfile(path):
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    r = requests.get(remote, timeout=30)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    return path

def fetch_points_page(session, page, results_per_page=100):
    data = {
        "currentPage": page,
        "resultsPerPage": results_per_page,
        "searchTerm": "",
    }
    resp = session.post(POINTS_API, data=urlencode(data), timeout=30)
    resp.raise_for_status()
    return resp.json()

def fetch_all_cards():
    sess = requests.Session()
    sess.headers.update(DEFAULT_HEADERS)
    if DEFAULT_COOKIES:
        sess.cookies.update(DEFAULT_COOKIES)

    first = fetch_points_page(sess, 1)
    if first.get("Success") != "Success" or "Result" not in first:
        raise Exception("Unexpected API response for page 1")

    result = first["Result"]
    total_pages = int(result.get("TotalPages", 1))
    results = list(result.get("Results", []))

    for p in range(2, total_pages + 1):
        page_json = fetch_points_page(sess, p)
        if page_json.get("Success") != "Success" or "Result" not in page_json:
            raise Exception(f"Unexpected API response for page {p}")
        results.extend(page_json["Result"].get("Results", []))

    cards = []
    for r in results:
        name = (r.get("DisplayCardName") or r.get("Name") or "").strip()
        points = r.get("Points")
        if name and points is not None:
            cards.append((name, str(points)))
    return cards

def save_cards_to_txt(cards, path):
    with open(path, "w", encoding="utf-8") as f:
        for name, points in cards:
            f.write(f"{name}\t{points}\n")

def read_cards_from_txt(path):
    cards = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 2:
                name, points = parts
                cards.append((name, points))
    return cards

def get_card_id_from_name(conn, name):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM texts WHERE name = ?", (name,))
    result = cursor.fetchone()
    return result[0] if result else None

def generate_banlist(cards, db_path, output_path):
    conn = sqlite3.connect(db_path)
    banlist_entries = []
    missing = []

    for name, points in cards:
        card_id = get_card_id_from_name(conn, name)
        if card_id:
            banlist_entries.append(f"{card_id} 3 {points}")
        else:
            missing.append((name, points))

    conn.close()

    os.makedirs(os.path.dirname(os.path.expanduser(output_path)), exist_ok=True)
    with open(os.path.expanduser(output_path), "w", encoding="utf-8") as f:
        f.write("!Genesys\n")
        for entry in banlist_entries:
            f.write(entry + "\n")

    print(f"[✓] Banlist written to: {os.path.expanduser(output_path)} ({len(banlist_entries)} cards)")
    if missing:
        print(f"[!] {len(missing)} cards were not found in the database:")
        for name, points in missing:
            print(f"  - {name} {points}")

def main():
    print("[*] Resolving BabelCDB cards DB...")
    db_path = ensure_delta_cdb_local()
    print(f"    Using DB: {db_path}")

    print("[*] Fetching Genesys points from API...")
    cards = fetch_all_cards()
    print(f"[*] Retrieved {len(cards)} cards")

    print(f"[*] Saving {len(cards)} cards to TSV file...")
    save_cards_to_txt(cards, CARDS_TXT_PATH)

    print("[*] Reading TSV and looking up card IDs...")
    cards_from_file = read_cards_from_txt(CARDS_TXT_PATH)

    print("[*] Generating banlist...")
    generate_banlist(cards_from_file, db_path, OUTPUT_BANLIST_PATH)

if __name__ == "__main__":
    main()
