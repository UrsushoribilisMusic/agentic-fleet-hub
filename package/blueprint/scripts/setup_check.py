import requests
import os
import json

PB_API = "http://localhost:8090/api"

def check_pb():
    try:
        r = requests.get(f"{PB_API}/collections/tasks/records")
        print(f"PocketBase check: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"PocketBase error: {e}")
        return False

def send_test_telegram():
    # Attempting to use the chat_id you confirmed
    chat_id = "997912895" 
    # Token fetch via shell for this one-off
    print("Please run this command to send the message:")
    print(f"export TG_TOKEN=$(infisical secrets get TELEGRAM_TOKEN --domain=https://eu.infisical.com/api --env=dev --plain --projectId=3233b7c1-8309-447d-af5a-6541e38dc1b3)")
    print("python3 -c \"import requests, os; r=requests.post('https://api.telegram.org/bot' + os.environ['TG_TOKEN'] + '/sendMessage', json={'chat_id': '" + chat_id + "', 'text': '⚓ Hello World from Flotilla!'}); print(r.text)\"")

if __name__ == "__main__":
    check_pb()
    send_test_telegram()
