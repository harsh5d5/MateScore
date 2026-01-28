import requests
from bs4 import BeautifulSoup
import json
import time

def get_team_squad_url(team_name):
    """Searches for a team and returns its squad URL."""
    search_url = f"https://onefootball.com/en/search?q={team_name.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    try:
        print(f"Searching for team: {team_name}...")
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find the first team link in the search results
        # Usually inside a "Teams" section
        team_link = soup.find('a', href=lambda x: x and '/en/team/' in x)
        
        if team_link:
            base_team_url = team_link['href']
            if not base_team_url.startswith('http'):
                base_team_url = "https://onefootball.com" + base_team_url
            
            # Ensure it points to the squad page
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

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    print(f"Fetching squad for {official_name} from {squad_url}...")
    try:
        response = requests.get(squad_url, headers=headers)
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
            # Resolve profile URL
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

def get_player_details(profile_url):
    """Scrapes detailed stats for a specific player."""
    stats_url = profile_url.rstrip('/') + '/stats'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(stats_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        stats = {}
        
        # Target specific stat sections to avoid footer/nav links
        # OneFootball often groups stats in semantic containers
        stat_containers = soup.find_all(['div', 'section'], class_=lambda x: x and ('performance-stats' in x or 'stats-group' in x))
        
        # If no containers, look for specific stat list items
        if not stat_containers:
            stat_items = soup.find_all('li', class_=lambda x: x and 'stat-item' in x)
        else:
            stat_items = []
            for container in stat_containers:
                stat_items.extend(container.find_all('li'))

        for item in stat_items:
            # Look for Label and Value spans
            spans = item.find_all('span')
            if len(spans) >= 2:
                key = spans[0].get_text(strip=True)
                val = spans[1].get_text(strip=True)
                
                # Filter out obvious junk (longer than 30 chars or containing social links)
                if key and val and len(key) < 40 and len(val) < 20:
                    if not any(junk in key.lower() for junk in ['instagram', 'facebook', 'app store', 'google play']):
                        stats[key] = val
                    
        # Fallback for simple statistics if the above didn't find much
        if len(stats) < 3:
            keywords = ["Goals", "Assists", "Appearances", "Pass accuracy", "Tackles", "Yellow cards"]
            for kw in keywords:
                tag = soup.find(text=lambda t: t and kw in t)
                if tag:
                    parent = tag.parent
                    val_tag = parent.find_next(['span', 'div'])
                    if val_tag:
                        val = val_tag.get_text(strip=True)
                        if val and len(val) < 10:
                            stats[kw] = val

        return stats
    except Exception as e:
        print(f"Error fetching player details: {e}")
        return {}

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "Liverpool FC"
    scrape_squad(query)
