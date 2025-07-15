from app.discord_bot.discord_api import client, discord_token

if __name__ == '__main__':
    if not discord_token:
        print("❌ Error: DISCORD_TOKEN not found in environment variables.")
        print("Please check your .env file and ensure DISCORD_TOKEN is set.")
        exit(1)
    
    client.run(discord_token)