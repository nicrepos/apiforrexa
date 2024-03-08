import hikari
from flask import Flask, jsonify, request
from flask_cors import CORS
import lightbulb
import requests
import json
from datetime import datetime
import validators

# Discord bot
bot = lightbulb.BotApp(token="your_token_here", intents=hikari.Intents.ALL)

# Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

access_status_message = 'Access Allowed'  # Default access status

announcements_file = "announcements.json"

url_file = "url.json"

def save_announcements():
    with open(announcements_file, 'w') as file:
        json.dump(announcements_data, file)

def load_url():
    global url_data
    try:
        with open(url_file, 'r') as file:
            data = file.read()
            url_data = json.loads(data) if data else []
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        url_data = []
    return url_data

def save_url():
    with open(url_file, 'w') as file:
        json.dump(url_data, file, default=str)

def load_announcements():
    global announcements_data
    try:
        with open(announcements_file, 'r') as file:
            announcements_data = json.load(file)
    except FileNotFoundError:
        announcements_data = []

load_announcements()

#overall just endpoints
@app.route('/api/version', methods=['GET'])
def get_version():
    # You can replace this with your actual version
    return jsonify(version='0.3')

@app.route('/api/access_status', methods=['GET'])
def get_access_status():
    return jsonify(message=access_status_message)

@app.route('/api/announcements', methods=['GET'])
def get_announcements():
    sorted_announcements = sorted(announcements_data, key=lambda x: x['datetime'], reverse=True)
    return jsonify({"announcements": sorted_announcements})

@app.route('/api/download', methods=['GET'])
def download():
    return jsonify(downloadurl=load_url())

#check server status
@bot.command()
@lightbulb.command("server-check", "Checks the Status of the Backend")
@lightbulb.implements(lightbulb.SlashCommand)
async def check_access(ctx: lightbulb.SlashContext) -> None:
    try:
        response = requests.get('http://127.0.0.1:5000/api/access_status')
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)

        data = response.json()
        print(data)

        if data["message"] == "Access Denied":
            await ctx.respond("Server is Offline!")
        elif data["message"] == "Access Allowed":
            await ctx.respond("Server is Online!")

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        await ctx.respond("Error checking server status.")

#announcement adder
@bot.command()
@lightbulb.option("message", "The message of the announcement", required=True)
@lightbulb.command("add-announcement", "Add a new announcement")
@lightbulb.implements(lightbulb.SlashCommand)
async def add_announcement_command(ctx: lightbulb.SlashContext) -> None:
    # Static variables for author and avatar change if needed
    author = ctx.member.display_name
    avatar = str(ctx.member.avatar_url)

    # Access the value of the "message" option
    message = ctx.options.message

    new_announcement = {
        "author": author,
        "message": message,
        "avatar": avatar,
        "datetime": str(datetime.utcnow())
    }
    announcements_data.append(new_announcement)
    save_announcements()
    await ctx.respond("Announcement added successfully")

@bot.command()
@lightbulb.option("url", "the url to download from", required=True)
@lightbulb.command("change-download-url", "change the download url in the launcher")
@lightbulb.implements(lightbulb.SlashCommand)
async def change_url(ctx: lightbulb.SlashContext) -> None:
    url = ctx.options.url
    new_url = {
        "downloadurl": url
    }
    url_data = load_url()  # Call load_url to get the data
    url_data.clear()
    url_data.append(new_url)  # Use append instead of insert
    save_url()
    await ctx.respond("Changed url!")

# Version command
@bot.command()
@lightbulb.command("version", "get the current version list")
@lightbulb.implements(lightbulb.SlashCommand)
async def get_version(ctx: lightbulb.SlashContext) -> None:
    try:
        response = requests.get('http://127.0.0.1:5000/api/version')
        response.raise_for_status()

        version_data = response.json()
        print(version_data)

        if version_data["version"] == "0.3":
            await ctx.respond(f"Launcher Version: 0.3\nBackend Version: Backend not Found!\nMatchmaker Version: Matchmaker not Found!\nGameserver Version: Gameserver not Found!")
        else:
            await ctx.respond("Error getting Version list!")

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        await ctx.respond("Error checking server status.")

# Run Flask
import threading

def run_flask():
    app.run(host='0.0.0.0', port=5000)

# Create threads for Flask
flask_thread = threading.Thread(target=run_flask)

# Start threads
flask_thread.start()

# Start bot
bot.run()