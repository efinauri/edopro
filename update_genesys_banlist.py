import requests
from bs4 import BeautifulSoup
import sqlite3

# --- CONFIGURATION ---
GENESYS_URL = "https://www.yugioh-card.com/en/genesys/"
CARDS_TXT_PATH = "genesys_cards.txt"
CDB_PATH = "~/Games/ProjectIgnis/expansions/cards.cdb"
OUTPUT_BANLIST_PATH = "~/Games/ProjectIgnis/lflists/genesys.txt"


# --- STEP 1: Fetch & Parse Web Page ---
def fetch_genesys_html(url):
	resp = requests.get(url)
	resp.raise_for_status()
	return resp.text

def parse_cards(html):
	soup = BeautifulSoup(html, "html.parser")
	table = soup.find("table", id="tablepress-genesys")
	if not table:
		raise Exception("Couldn't find the table with id 'tablepress-genesys'.")

	rows = table.find("tbody").find_all("tr")
	cards = []
	for row in rows:
		cols = row.find_all("td")
		if len(cols) >= 2:
			name = cols[0].get_text(strip=True)
			points = cols[1].get_text(strip=True)
			cards.append((name, points))
	return cards


# --- STEP 2: Save as TSV ---
def save_cards_to_txt(cards, path):
	with open(path, "w", encoding="utf-8") as f:
		for name, points in cards:
			f.write(f"{name}\t{points}\n")


# --- STEP 3: Load TSV and Lookup IDs ---
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


# --- STEP 4: Generate Banlist ---
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

	with open(output_path, "w", encoding="utf-8") as f:
		f.write("!Genesys\n")
		for entry in banlist_entries:
			f.write(entry + "\n")

	print(f"[✓] Banlist written to: {output_path} ({len(banlist_entries)} cards)")
	if missing:
		print(f"[!] {len(missing)} cards were not found in the database:")
		for name, points in missing:
			print(f"  - {name} {points}")


# --- MAIN FLOW ---
def main():
	print("[*] Fetching Genesys page...")
	html = fetch_genesys_html(GENESYS_URL)

	print("[*] Parsing card table...")
	cards = parse_cards(html)

	print(f"[*] Saving {len(cards)} cards to TSV file...")
	save_cards_to_txt(cards, CARDS_TXT_PATH)

	print("[*] Reading TSV and looking up card IDs...")
	cards_from_file = read_cards_from_txt(CARDS_TXT_PATH)

	print("[*] Generating banlist...")
	generate_banlist(cards_from_file, CDB_PATH, OUTPUT_BANLIST_PATH)


if __name__ == "__main__":
	main()
