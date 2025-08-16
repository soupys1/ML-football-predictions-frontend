import os
import json
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import ML modules
from ml.game_winner_model import train_game_winner_model, predict_game_winner
from ml.team_player_features import rank_mvp_candidates, rank_top_players_for_team
from ml.csv_loader import read_csv_smart

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"], supports_credentials=True)

# Initialize AWS S3 client
s3_client = boto3.client('s3') if os.getenv('AWS_ACCESS_KEY_ID') else None

def load_data_from_s3(bucket_name, file_key, local_path):
    """Load data from S3 or fall back to local file"""
    if s3_client and bucket_name:
        try:
            s3_client.download_file(bucket_name, file_key, local_path)
            print(f"Downloaded {file_key} from S3")
        except Exception as e:
            print(f"Failed to download from S3: {e}, using local file")
    return local_path

def save_model_to_s3(model_path, bucket_name, file_key):
    """Save trained model to S3"""
    if s3_client and bucket_name:
        try:
            s3_client.upload_file(model_path, bucket_name, file_key)
            print(f"Uploaded model to S3: {file_key}")
        except Exception as e:
            print(f"Failed to upload model to S3: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'football-predictor-backend',
        'version': '1.0.0'
    })

@app.route('/api/football/leagues/summary', methods=['GET'])
def get_leagues_summary():
    """Get summary of available leagues"""
    try:
        # Load data from S3 or local
        data_bucket = os.getenv('DATA_BUCKET')
        games_path = load_data_from_s3(data_bucket, 'data/games.csv', 'data/games.csv')
        leagues_path = load_data_from_s3(data_bucket, 'data/leagues.csv', 'data/leagues.csv')
        
        games_df = read_csv_smart(games_path)
        leagues_df = read_csv_smart(leagues_path)
        
        # Merge and aggregate
        merged = games_df.merge(leagues_df[['leagueID', 'name']], on='leagueID', how='left')
        league_summary = merged.groupby(['leagueID', 'name']).size().reset_index(name='numGames')
        
        return jsonify({
            'leagues': league_summary.to_dict('records')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/football/teams/<int:league_id>', methods=['GET'])
def get_teams(league_id):
    """Get teams for a specific league"""
    try:
        # Load data from S3 or local
        data_bucket = os.getenv('DATA_BUCKET')
        games_path = load_data_from_s3(data_bucket, 'data/games.csv', 'data/games.csv')
        teams_path = load_data_from_s3(data_bucket, 'data/teams.csv', 'data/teams.csv')
        
        games_df = read_csv_smart(games_path)
        teams_df = read_csv_smart(teams_path)
        
        # Get teams from the specified league
        league_games = games_df[games_df['leagueID'] == league_id]
        home_teams = league_games[['homeTeamID']].drop_duplicates()
        away_teams = league_games[['awayTeamID']].drop_duplicates()
        
        all_team_ids = pd.concat([home_teams, away_teams]).drop_duplicates()
        league_teams = teams_df[teams_df['teamID'].isin(all_team_ids.iloc[:, 0])]
        
        return jsonify({
            'teams': league_teams.to_dict('records')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/football/game/predict-by-teams', methods=['POST'])
def game_predict_by_teams():
    """Predict match outcome between two teams"""
    print(f"DEBUG: Received {request.method} request to /api/football/game/predict-by-teams")  # Debug log
    print(f"DEBUG: Request headers: {dict(request.headers)}")  # Debug log
    
    try:
        data = request.get_json()
        print(f"DEBUG: Received data: {data}")  # Debug log
        
        if data is None:
            print("DEBUG: No JSON data received")
            return jsonify({'error': 'No JSON data received'}), 400
        
        league_id = data.get('leagueID')
        home_id = data.get('homeTeamID')
        away_id = data.get('awayTeamID')
        
        print(f"DEBUG: league_id={league_id}, home_id={home_id}, away_id={away_id}")  # Debug log
        
        if not all([league_id, home_id, away_id]):
            print(f"DEBUG: Missing parameters - league_id: {league_id}, home_id: {home_id}, away_id: {away_id}")  # Debug log
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Load data from S3 or local
        data_bucket = os.getenv('DATA_BUCKET')
        games_path = load_data_from_s3(data_bucket, 'data/games.csv', 'data/games.csv')
        teams_path = load_data_from_s3(data_bucket, 'data/teams.csv', 'data/teams.csv')
        
        # Check if model exists
        model_bucket = os.getenv('MODEL_BUCKET')
        model_path = load_data_from_s3(model_bucket, 'models/game_winner_model.joblib', 'models/game_winner_model.joblib')
        
        if os.path.exists(model_path):
            # Use trained model
            result = predict_game_winner(games_path, teams_path, model_path, league_id, home_id, away_id)
        else:
            # Fallback prediction (simple random-based)
            import random
            random.seed(hash(f"{home_id}_{away_id}") % 1000)  # Deterministic based on teams
            winner = random.choice(['Home', 'Away', 'Draw'])
            result = {
                "winner": winner,
                "probabilities": {
                    "Home": 0.33,
                    "Away": 0.33,
                    "Draw": 0.34
                },
                "trained_samples": 0,
                "note": "Using fallback prediction - train model for better accuracy"
            }
        
        # Add MVP candidates from players.csv if present
        players_path = load_data_from_s3(data_bucket, 'data/players_with_teams.csv', 'data/players_with_teams.csv')
        if os.path.exists(players_path):
            mvps = rank_mvp_candidates(players_path, int(home_id), int(away_id), top_k=5)
            if mvps:
                result["mvpCandidates"] = mvps
            # Also provide top 5 per team
            result["homeTopPlayers"] = rank_top_players_for_team(players_path, int(home_id), top_k=5)
            result["awayTopPlayers"] = rank_top_players_for_team(players_path, int(away_id), top_k=5)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/football/game/train-with-teams-players', methods=['POST'])
def train_with_team_player_features():
    """Train the model with team and player features"""
    try:
        payload = request.get_json() or {}
        
        # Load data from S3 or local
        data_bucket = os.getenv('DATA_BUCKET')
        games_path = load_data_from_s3(data_bucket, 'data/games.csv', 'data/games.csv')
        teams_path = load_data_from_s3(data_bucket, 'data/teams.csv', 'data/teams.csv')
        players_path = load_data_from_s3(data_bucket, 'data/players_with_teams.csv', 'data/players_with_teams.csv')
        
        # Train model
        result = train_game_winner_model(
            games_csv=games_path,
            teams_csv=teams_path,
            players_csv=players_path if os.path.exists(players_path) else None
        )
        
        # Save model to S3 if configured
        model_bucket = os.getenv('MODEL_BUCKET')
        if model_bucket:
            save_model_to_s3('models/game_winner_model.joblib', model_bucket, 'models/game_winner_model.joblib')
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/football/data/upload', methods=['POST'])
def upload_data():
    """Upload data files to S3"""
    try:
        if not s3_client:
            return jsonify({'error': 'S3 not configured'}), 400
        
        data_bucket = os.getenv('DATA_BUCKET')
        if not data_bucket:
            return jsonify({'error': 'DATA_BUCKET not configured'}), 400
        
        # Upload CSV files
        files = ['games.csv', 'leagues.csv', 'teams.csv', 'players_with_teams.csv']
        uploaded_files = []
        
        for file_name in files:
            local_path = f'data/{file_name}'
            if os.path.exists(local_path):
                s3_client.upload_file(local_path, data_bucket, f'data/{file_name}')
                uploaded_files.append(file_name)
        
        return jsonify({
            'message': 'Data uploaded successfully',
            'uploaded_files': uploaded_files
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/football/model/status', methods=['GET'])
def model_status():
    """Check model status and availability"""
    try:
        model_bucket = os.getenv('MODEL_BUCKET')
        data_bucket = os.getenv('DATA_BUCKET')
        
        status = {
            'model_available': False,
            'data_available': False,
            's3_configured': s3_client is not None
        }
        
        # Check local model
        if os.path.exists('models/game_winner_model.joblib'):
            status['model_available'] = True
        
        # Check local data
        if os.path.exists('data/games.csv'):
            status['data_available'] = True
        
        # Check S3 if configured
        if s3_client and model_bucket:
            try:
                s3_client.head_object(Bucket=model_bucket, Key='models/game_winner_model.joblib')
                status['model_available'] = True
            except:
                pass
        
        if s3_client and data_bucket:
            try:
                s3_client.head_object(Bucket=data_bucket, Key='data/games.csv')
                status['data_available'] = True
            except:
                pass
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')



