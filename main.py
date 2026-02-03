import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import os

# --- Data Management (Railway Volume Safe) ---
DATA_FOLDER = "/data"
DATA_FILE = os.path.join(DATA_FOLDER, "data.json")

def load_data():
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def add_bars(user_id, amount):
    data = load_data()
    uid_str = str(user_id)
    data[uid_str] = data.get(uid_str, 0) + amount
    save_data(data)

# --- Bot Setup ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Syncs slash commands with Discord
        await self.tree.sync()

bot = MyBot()

# --- Equation Logic & Buttons ---
class EquationView(discord.ui.View):
    def __init__(self, correct_answer, bars):
        super().__init__(timeout=30)
        self.correct_answer = correct_answer
        self.bars = bars

    async def handle_answer(self, interaction: discord.Interaction, chosen_answer):
        if chosen_answer == self.correct_answer:
            add_bars(interaction.user.id, self.bars)
            await interaction.response.edit_message(
                content=f"✅ You are correct! You earned **{self.bars}** chocolate bars!", 
                view=None
            )
        else:
            await interaction.response.edit_message(
                content=f"❌ Incorrect. The right answer was {self.correct_answer}.", 
                view=None
            )

# --- Commands ---

@bot.tree.command(name="extracredit", description="Ask for extra credit")
async def extracredit(interaction: discord.Interaction):
    await interaction.response.send_message("No extra credit in this class!")

@bot.tree.command(name="yesorno", description="Create a poll with reactions")
async def yesorno(interaction: discord.Interaction, question: str):
    await interaction.response.send_message(f"**Poll:** {question}")
    message = await interaction.original_response()
    await message.add_reaction("👍")
    await message.add_reaction("👎")

@bot.tree.command(name="equation", description="Solve a math problem for chocolate bars")
async def equation(interaction: discord.Interaction):
    a, b = random.randint(1, 20), random.randint(1, 20)
    correct = a + b
    
    # Generate 2 wrong answers
    wrongs = set()
    while len(wrongs) < 2:
        w = correct + random.randint(-5, 5)
        if w != correct and w > 0:
            wrongs.add(w)
    
    options = list(wrongs) + [correct]
    random.shuffle(options)

    bars = random.randint(1, 3)
    view = EquationView(correct, bars)

    for opt in options:
        btn = discord.ui.Button(label=str(opt), style=discord.ButtonStyle.secondary)
        btn.callback = lambda i, o=opt: view.handle_answer(i, o)
        view.add_item(btn)

    await interaction.response.send_message(f"Solve: **{a} + {b} = ?**\nReward: {bars} 🍫", view=view)

@bot.tree.command(name="barcount", description="Check the leaderboard")
async def barcount(interaction: discord.Interaction):
    data = load_data()
    if not data:
        return await interaction.response.send_message("The jar is empty! No chocolate bars found.")

    leaderboard = "**🍫 Current Chocolate Bar Counts:**\n"
    # Sort by bar count descending
    sorted_data = sorted(data.items(), key=lambda item: item[1], reverse=True)
    
    for uid, count in sorted_data:
        leaderboard += f"• <@{uid}>: {count} bars\n"
    
    await interaction.response.send_message(leaderboard)

# --- Execution ---
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
