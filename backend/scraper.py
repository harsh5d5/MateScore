import requests
from bs4 import BeautifulSoup
import json
import time
from concurrent.futures import ThreadPoolExecutor

# Use a global session for connection pooling
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
})

def get_team_squad_url(team_name):
    """Searches for a team and returns its squad URL."""
    search_url = f"https://onefootball.com/en/search?q={team_name.replace(' ', '+')}"
    
    try:
        print(f"Searching for team: {team_name}...")
        response = session.get(search_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        team_link = soup.find('a', href=lambda x: x and '/en/team/' in x)
        
        if team_link:
            base_team_url = team_link['href']
            if not base_team_url.startswith('http'):
                base_team_url = "https://onefootball.com" + base_team_url
            
            if not base_team_url.endswith('/squad'):
                squad_url = base_team_url.rstrip('/') + '/squad'
            else:
                squad_url = base_team_url
                
            return squad_url, team_link.get_text(strip=True)
    except Exception as e:
        print(f"Error searching for team: {e}")
    
    return None, None

def scrape_squad(team_name="Liverpool FC"):
    squad_url, official_name = get_team_squad_url(team_name)
    
    if not squad_url:
        print(f"Could not find squad for '{team_name}'")
        return None

    print(f"Fetching squad for {official_name} from {squad_url}...")
    try:
        response = session.get(squad_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    squad = []
    
    player_cells = soup.find_all(['li', 'div'], class_=lambda x: x and ('squad-player' in x or 'player-card' in x))
    
    if not player_cells:
        links = soup.find_all('a', href=lambda x: x and '/en/player/' in x)
        player_cells = [link.find_parent(['li', 'div']) for link in links if link.find_parent(['li', 'div'])]

    for cell in player_cells:
        link = cell.find('a', href=lambda x: x and '/en/player/' in x)
        if not link: continue
            
        content = link.get_text(strip=True)
        if not content: continue
            
        img = cell.find('img')
        image_url = img.get('src') or img.get('data-src') if img else ""
        if image_url and image_url.startswith('/'):
            image_url = "https://onefootball.com" + image_url

        positions = ["Goalkeeper", "Defender", "Midfielder", "Forward"]
        player_position = "Unknown"
        player_name = content
        player_number = ""
        
        for pos in positions:
            if content.startswith(pos):
                player_position = pos
                rest = content[len(pos):]
                if "(" in rest and ")" in rest:
                    player_name = rest.split("(")[0].strip()
                    player_number = rest.split("(")[1].replace(")", "").strip()
                else:
                    player_name = rest
                break
        
        if not any(p['name'] == player_name for p in squad):
            profile_path = link['href']
            full_profile_url = profile_path if profile_path.startswith('http') else "https://onefootball.com" + profile_path
            
            squad.append({
                "name": player_name,
                "position": player_position,
                "number": player_number,
                "image": image_url,
                "profile_url": full_profile_url
            })

    if squad:
        result = {
            "team": official_name,
            "players": squad
        }
        with open("squad.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)
        print(f"Successfully scraped {len(squad)} players for {official_name}.")
        return result
    
    return None

def fetch_details_page(url):
    """Worker function for parallel fetching."""
    try:
        resp = session.get(url, timeout=5)
        if resp.status_code == 200:
            return BeautifulSoup(resp.content, "html.parser")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def get_player_details(profile_url):
    """Scrapes detailed stats for a specific player using parallel requests."""
    stats = {}
    stats_url = profile_url.rstrip('/') + '/stats'
    
    # 1. Fetch both pages in parallel for speed
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            'main': executor.submit(fetch_details_page, profile_url),
            'stats': executor.submit(fetch_details_page, stats_url)
        }
        
    main_soup = futures['main'].result()
    stats_soup = futures['stats'].result()

    # 2. Extract from Main Profile
    if main_soup:
        target_labels = ["Age", "Position", "Country", "Height", "Weight", "Preferred foot", "Date of birth", "Jersey number"]
        for label in target_labels:
            label_tag = main_soup.find(string=lambda t: t and t.strip() == label)
            if label_tag:
                parent = label_tag.parent
                container = parent.parent
                potential_values = container.find_all(string=True)
                for val in potential_values:
                    cleaned_val = val.strip()
                    if cleaned_val and cleaned_val != label and len(cleaned_val) < 25:
                        key_name = label
                        if label == "Country": key_name = "Nationality"
                        stats[key_name] = cleaned_val
                        break

    # 3. Extract from Stats Page
    if stats_soup:
        stat_items = stats_soup.find_all(['li', 'div'], class_=lambda x: x and any(k in x.lower() for k in ['stat-item', 'stats-group', 'performance']))
        for item in stat_items:
            spans = item.find_all('span')
            if len(spans) >= 2:
                key = spans[0].get_text(strip=True)
                val = spans[1].get_text(strip=True)
                if key and val and len(key) < 40 and len(val) < 20:
                    if key not in stats:
                        stats[key] = val
                            
    # Final cleanup
    if "Age" in stats and "(" in stats["Age"]:
        stats["Age"] = stats["Age"].split("(")[0].strip()
    
    if "Country" in stats:
        stats["Nationality"] = stats.pop("Country")

    return stats

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "Liverpool FC"
    scrape_squad(query)
