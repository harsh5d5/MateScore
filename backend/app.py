from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from scraper import scrape_squad
import os

app = Flask(__name__)
CORS(app) # Enable CORS for frontend requests

@app.route('/')
def index():
    return send_from_directory('../client', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('../client', path)

@app.route('/api/search')
def search_team():
    team_name = request.args.get('team', 'Liverpool FC')
    if not team_name:
        return jsonify({"error": "Team name is required"}), 400
    
    print(f"API Request: Searching for {team_name}...")
    result = scrape_squad(team_name)
    
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": f"Could not find squad for '{team_name}'"}), 404

@app.route('/api/player_details')
def player_details():
    from scraper import get_player_details
    profile_url = request.args.get('url')
    if not profile_url:
        return jsonify({"error": "Profile URL is required"}), 400
    
    print(f"API Request: Fetching details for {profile_url}...")
    stats = get_player_details(profile_url)
    return jsonify(stats)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
