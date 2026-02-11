import requests
import csv
import os
from datetime import datetime

API_URL = "https://multitheftauto.com/count/"
DATA_FILE = "data/mta_history.csv"

def collect():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        
        parts = response.text.strip().split(',')
        
        if len(parts) >= 2:
            players = int(parts[0])
            servers = int(parts[1])
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            file_exists = os.path.isfile(DATA_FILE)
            
            with open(DATA_FILE, mode='a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["ds", "y", "servers"]) # ds=time, y=players
                
                writer.writerow([timestamp, players, servers])
                print(f"Saved: {timestamp} | P: {players} | S: {servers}")
        else:
            print("Invalid data format from API")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    collect()