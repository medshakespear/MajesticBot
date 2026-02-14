import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select, Modal, TextInput
from discord import app_commands
import asyncio
import os
import json
from datetime import datetime
from typing import Optional
import uuid

# -------------------- INTENTS --------------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------- CONFIG --------------------
LEADER_ROLE_NAME = "LEADER"
MODERATOR_ROLE_NAME = "MODERATOR"

# CRITICAL: Use persistent volume for data storage
# Railway Volume mount path: /data
# This ensures data survives redeployments!
DATA_DIR = os.getenv("DATA_DIR", "/data")
DATA_FILE = os.path.join(DATA_DIR, "squad_data.json")

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# Royal color scheme
ROYAL_PURPLE = 0x6a0dad
ROYAL_GOLD = 0xffd700
ROYAL_BLUE = 0x4169e1
ROYAL_RED = 0xdc143c

SQUADS = {
    "Manschaft": "V",
    "Zero Vision": "ZVS",
    "SAT": "SAT",
    "Exeed": "수",
    "Eclypse": "☯",
    "Axiom eSports": "Axs",
    "Shadow Angels": "SɅ",
    "NONKAR": "🔱",
    "ROYALS": "立",
    "Kite buu": "KITE",
    "One More Esports": "1M",
    "The void": "VD",
    "SRG": "SRG",
    "Blood Moon": "Blod",
    "Red Raptors": "RED",
    "TEENYI BAMBUSEL": "TNY",
    "Force X": "X͠",
    "Impuls": "IP",
    "Agartha": "AG",
    "Emberblaze": "EMBR",
    "broken stars": "ᯓ✰",
    "Meta breakers": "MB",
    "NOX ZENITH CULT": "NZCT",
    "asgard warriors": "AW",
    "NR Esports.": "NR",
    "Autobots": "AB",
    "ENNEAD": "EN",
    "Ethereal": "ÆTH",
    "浪 Ronin'": "DVNA",
    "Death Dose": "DD•",
}

GUEST_ROLES = {
    "浪 Ronin'": "浪 Ronin'_guest",
    "Ethereal": "Ethereal_guest",
    "ENNEAD": "Ennead_guest",
    "Shadow Angels": "Shadow.Angels_guest",
    "Autobots": "Autobots_guest",
    "Zero Vision": "Zero.Vision_guest",
    "SAT": "Sat_guest",
    "The void": "The.Void_guest",
    "Meta breakers": "Meta.Breakers_guest",
    "NOX ZENITH CULT": "Nox.Zenith.Cult_guest",
    "Agartha": "Agartha_guest",
    "Force X": "Force.X_guest",
    "Impuls": "Impuls_guest",
    "Axiom eSports": "Axiom.Esports_guest",
    "Emberblaze": "Emberblaze_guest",
    "Eclypse": "Eclypse_guest",
    "Blood Moon": "Blood.Moon_guest",
    "NR Esports.": "NR.Esports_guest",
    "TEENYI BAMBUSEL": "TeenyI.Bambusel_guest",
    "Kite buu": "Kite.buu_guest",
    "Red Raptors": "Red.Raptors_guest",
    "SRG": "SRG_guest",
    "NONKAR": "Nonkar_guest",
    "Exeed": "Exeed_guest",
    "One More Esports": "One.More.Esports_guest",
    "asgard warriors": "Asguard.Warriors_guest",
    "Manschaft": "Manschaft_guest",
    "Death Dose": "death.dose_guest",
}

ROLES = ["Gold Lane", "Mid Lane", "Exp Lane", "Jungler", "Roamer"]
ROLE_EMOJIS = {
    "Gold Lane": "👑",
    "Mid Lane": "⚜️",
    "Exp Lane": "🛡️",
    "Jungler": "⚔️",
    "Roamer": "🏇"
}

ALL_TAGS = list(SQUADS.values())
LOG_CHANNEL_NAME = "bot-logs"

# Fun battle quotes for match results
VICTORY_QUOTES = [
    "💥 Absolute domination on the battlefield!",
    "🔥 They came, they saw, they conquered!",
    "⚡ Swift and merciless victory!",
    "🌟 Legends were born in this battle!",
    "👑 True royalty shines through combat!",
    "💫 The stars aligned for victory!",
    "🎯 Precision, power, perfection!",
    "🦅 They soared above their opponents!",
    "⚔️ Blades sang the song of triumph!",
    "🏆 Champions forge their legacy!"
]

DEFEAT_QUOTES = [
    "💀 A bitter lesson learned today...",
    "🌑 Darkness fell upon the battlefield...",
    "⛈️ The storm proved too fierce...",
    "🥀 Even roses must wither sometimes...",
    "🌊 Overwhelmed by the tide of battle...",
    "❄️ Frozen by the opponent's might...",
    "🔻 The higher they climb, the harder they fall...",
    "🌪️ Swept away by superior tactics...",
    "⚰️ Today belongs to their rivals...",
    "🗡️ Outmatched, but not defeated in spirit!"
]

DRAW_QUOTES = [
    "⚖️ Perfectly balanced, as all things should be!",
    "🤝 Honor shared between equals!",
    "🌓 Two forces meet in harmony!",
    "⭐ Both sides shine with equal brilliance!",
    "🎭 A tale of two kingdoms!",
    "🔄 The wheel of fate spins evenly!",
    "💠 Matched in skill, united in glory!",
    "🎪 A spectacle of balanced power!",
    "🌐 The universe maintains its equilibrium!",
    "⚡ Lightning strikes twice with equal force!"
]

# Squad status based on recent performance
SQUAD_MOODS = {
    "fire": {"emoji": "🔥", "status": "ON FIRE", "desc": "Unstoppable momentum!"},
    "rising": {"emoji": "📈", "status": "RISING", "desc": "Building strength!"},
    "steady": {"emoji": "⚖️", "status": "STEADY", "desc": "Maintaining course"},
    "struggling": {"emoji": "😰", "status": "STRUGGLING", "desc": "Needs regrouping"},
    "crisis": {"emoji": "💀", "status": "IN CRISIS", "desc": "Dark times ahead..."}
}

# Achievement thresholds
ACHIEVEMENTS = {
    "first_blood": {"name": "🩸 First Blood", "desc": "Win your first match"},
    "undefeated_5": {"name": "💪 Undefeated Streak (5)", "desc": "Win 5 matches without a loss"},
    "comeback_king": {"name": "👑 Comeback King", "desc": "Win after a 3+ loss streak"},
    "century_club": {"name": "💯 Century Club", "desc": "Reach 100 points"},
    "warrior_50": {"name": "⚔️ 50 Battles Veteran", "desc": "Play 50 total matches"},
    "perfect_10": {"name": "✨ Perfect 10", "desc": "Win 10 matches in a row"},
    "champion": {"name": "🏆 Champion", "desc": "Win a championship title"},
}

# -------------------- DATA MANAGEMENT --------------------
def load_data():
    """Load squad data from JSON file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Backward compatibility: Add participants to old matches
            for match in data.get("matches", []):
                if "team1_participants" not in match:
                    match["team1_participants"] = []  # Empty = count all
                if "team2_participants" not in match:
                    match["team2_participants"] = []
            
            return data
    
    # Initialize default data structure
    data = {
        "squads": {},
        "players": {},
        "matches": []
    }
    
    # Initialize each squad
    for squad_name in SQUADS.keys():
        data["squads"][squad_name] = {
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "points": 0,
            "titles": [],
            "championship_wins": 0,
            "logo_url": None,
            "main_roster": [],
            "subs": [],
            "match_history": [],
            "current_streak": {"type": "none", "count": 0},  # win, loss, draw
            "achievements": [],
            "biggest_win_streak": 0,
            "biggest_loss_streak": 0
        }
    
    save_data(data)
    return data

def save_data(data):
    """Save squad data to JSON file"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, indent=2, fp=f, ensure_ascii=False)

# Global data
squad_data = load_data()

# -------------------- LOGGING HELPER --------------------
async def log_action(guild: discord.Guild, title: str, description: str):
    if guild is None:
        return
    
    channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if channel is None:
        return
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=ROYAL_PURPLE,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="⚜️ Royal Squad Archives")
    
    try:
        await channel.send(embed=embed)
    except Exception as e:
        print(f"[LOGGING ERROR] {e}")

# -------------------- HELPERS --------------------
def remove_all_tags(name):
    for tag in ALL_TAGS:
        if name.startswith(f"{tag} "):
            return name[len(f"{tag} "):]
    return name

def is_leader(member):
    return any(role.name == LEADER_ROLE_NAME for role in member.roles)

def is_moderator(member):
    return any(role.name == MODERATOR_ROLE_NAME for role in member.roles)

def get_member_squad(member, guild):
    for role_name, tag in SQUADS.items():
        role = discord.utils.get(guild.roles, name=role_name)
        if role and role in member.roles:
            return role, tag
    return None, None

def get_leaders_for_squad(guild, squad_role):
    leader_role = discord.utils.get(guild.roles, name=LEADER_ROLE_NAME)
    if not leader_role:
        return []
    return [m.display_name for m in leader_role.members if squad_role in m.roles]

async def safe_nick_update(member, role, tag):
    clean = remove_all_tags(member.display_name)
    desired = f"{tag} {clean}" if role else clean
    
    if member.display_name == desired:
        return
    
    try:
        await member.edit(nick=desired)
        await asyncio.sleep(0.4)
    except:
        pass

def update_player_squad(player_id, new_squad=None, old_squad=None):
    """Update player's squad in their profile and track history"""
    player_key = str(player_id)
    
    # Initialize player data if it doesn't exist
    if player_key not in squad_data["players"]:
        squad_data["players"][player_key] = {
            "discord_id": player_id,
            "ingame_name": "",
            "ingame_id": "",
            "highest_rank": "",
            "role": "",
            "squad": new_squad,
            "squad_history": []
        }
    
    player_data = squad_data["players"][player_key]
    
    # Add to squad history if changing squads
    if old_squad and old_squad != new_squad:
        history_entry = {
            "squad": old_squad,
            "left_date": datetime.utcnow().isoformat()
        }
        if "squad_history" not in player_data:
            player_data["squad_history"] = []
        player_data["squad_history"].append(history_entry)
    
    # Update current squad
    player_data["squad"] = new_squad
    save_data(squad_data)

def get_squad_ranking():
    """Get squads sorted by points with ranking position and win rate"""
    rankings = []
    for squad_name, data in squad_data["squads"].items():
        total_matches = data["wins"] + data["draws"] + data["losses"]
        win_rate = (data["wins"] / total_matches * 100) if total_matches > 0 else 0.0
        
        rankings.append({
            "name": squad_name,
            "tag": SQUADS[squad_name],
            "points": data["points"],
            "wins": data["wins"],
            "draws": data["draws"],
            "losses": data["losses"],
            "win_rate": win_rate,
            "total_matches": total_matches
        })
    
    sorted_rankings = sorted(rankings, key=lambda x: x["points"], reverse=True)
    
    # Add rank position
    for i, squad in enumerate(sorted_rankings, 1):
        squad["rank"] = i
    
    return sorted_rankings

def get_squad_rank(squad_name):
    """Get the ranking position of a specific squad"""
    rankings = get_squad_ranking()
    for squad in rankings:
        if squad["name"] == squad_name:
            return squad["rank"]
    return None

def get_player_stats(player_id):
    """Get comprehensive player statistics - only counts matches player participated in"""
    player_key = str(player_id)
    player_data = squad_data["players"].get(player_key)
    
    if not player_data:
        return None
    
    # Count matches the player actually participated in
    matches_played = 0
    wins = 0
    losses = 0
    draws = 0
    
    squad_name = player_data.get("squad")
    if squad_name and squad_name != "Free Agent":
        # Go through all matches and check participation
        for match in squad_data["matches"]:
            # Check if player's squad was in this match
            if match["team1"] == squad_name:
                participants = match.get("team1_participants", [])
                was_opposing = False
            elif match["team2"] == squad_name:
                participants = match.get("team2_participants", [])
                was_opposing = True
            else:
                continue  # Player's squad not in this match
            
            # Check if player participated
            # Empty participants list = count all (backward compat or <5 mains)
            if not participants or player_id in participants:
                matches_played += 1
                
                # Determine result for this player
                try:
                    score1, score2 = map(int, match["score"].split('-'))
                    if match["team1"] == squad_name:
                        # Player's team was team1
                        if score1 > score2:
                            wins += 1
                        elif score2 > score1:
                            losses += 1
                        else:
                            draws += 1
                    else:
                        # Player's team was team2
                        if score2 > score1:
                            wins += 1
                        elif score1 > score2:
                            losses += 1
                        else:
                            draws += 1
                except:
                    pass  # Skip malformed scores
    
    return {
        "matches_played": matches_played,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "win_rate": (wins / matches_played * 100) if matches_played > 0 else 0
    }

def find_match_by_id(match_id):
    """Find a match by its ID"""
    for i, match in enumerate(squad_data["matches"]):
        if match.get("match_id") == match_id:
            return i, match
    return None, None

def get_squad_mood(squad_name):
    """Determine squad mood based on recent performance"""
    squad_info = squad_data["squads"].get(squad_name, {})
    
    # Check recent match history (last 5 matches)
    recent_matches = squad_info.get("match_history", [])[-5:]
    if len(recent_matches) < 3:
        return SQUAD_MOODS["steady"]
    
    recent_results = []
    for match in recent_matches:
        if match["team1"] == squad_name:
            score1, score2 = map(int, match["score"].split('-'))
            if score1 > score2:
                recent_results.append("W")
            elif score1 < score2:
                recent_results.append("L")
            else:
                recent_results.append("D")
        else:
            score1, score2 = map(int, match["score"].split('-'))
            if score2 > score1:
                recent_results.append("W")
            elif score2 < score1:
                recent_results.append("L")
            else:
                recent_results.append("D")
    
    wins = recent_results.count("W")
    losses = recent_results.count("L")
    
    # Determine mood
    if wins >= 4:
        return SQUAD_MOODS["fire"]
    elif wins >= 3:
        return SQUAD_MOODS["rising"]
    elif losses >= 4:
        return SQUAD_MOODS["crisis"]
    elif losses >= 3:
        return SQUAD_MOODS["struggling"]
    else:
        return SQUAD_MOODS["steady"]

def update_streak(squad_name, result):
    """Update win/loss/draw streak for a squad"""
    squad_info = squad_data["squads"][squad_name]
    current_streak = squad_info.get("current_streak", {"type": "none", "count": 0})
    
    if current_streak["type"] == result:
        # Continue streak
        current_streak["count"] += 1
    else:
        # New streak
        current_streak = {"type": result, "count": 1}
    
    squad_info["current_streak"] = current_streak
    
    # Update biggest streaks
    if result == "win" and current_streak["count"] > squad_info.get("biggest_win_streak", 0):
        squad_info["biggest_win_streak"] = current_streak["count"]
    elif result == "loss" and current_streak["count"] > squad_info.get("biggest_loss_streak", 0):
        squad_info["biggest_loss_streak"] = current_streak["count"]
    
    return current_streak

def check_achievements(squad_name):
    """Check and award achievements"""
    squad_info = squad_data["squads"][squad_name]
    achievements = squad_info.get("achievements", [])
    new_achievements = []
    
    # First blood
    if squad_info["wins"] == 1 and "first_blood" not in achievements:
        achievements.append("first_blood")
        new_achievements.append(ACHIEVEMENTS["first_blood"])
    
    # Century club
    if squad_info["points"] >= 100 and "century_club" not in achievements:
        achievements.append("century_club")
        new_achievements.append(ACHIEVEMENTS["century_club"])
    
    # Perfect 10
    if squad_info.get("current_streak", {}).get("type") == "win" and squad_info.get("current_streak", {}).get("count") == 10 and "perfect_10" not in achievements:
        achievements.append("perfect_10")
        new_achievements.append(ACHIEVEMENTS["perfect_10"])
    
    # Undefeated 5
    if squad_info.get("current_streak", {}).get("type") == "win" and squad_info.get("current_streak", {}).get("count") == 5 and "undefeated_5" not in achievements:
        achievements.append("undefeated_5")
        new_achievements.append(ACHIEVEMENTS["undefeated_5"])
    
    # Warrior 50
    total_matches = squad_info["wins"] + squad_info["draws"] + squad_info["losses"]
    if total_matches >= 50 and "warrior_50" not in achievements:
        achievements.append("warrior_50")
        new_achievements.append(ACHIEVEMENTS["warrior_50"])
    
    # Champion
    if squad_info.get("championship_wins", 0) >= 1 and "champion" not in achievements:
        achievements.append("champion")
        new_achievements.append(ACHIEVEMENTS["champion"])
    
    squad_info["achievements"] = achievements
    return new_achievements

def get_head_to_head(squad1_name, squad2_name):
    """Get head-to-head record between two squads"""
    h2h = {"squad1_wins": 0, "squad2_wins": 0, "draws": 0, "total": 0}
    
    for match in squad_data["matches"]:
        if (match["team1"] == squad1_name and match["team2"] == squad2_name) or \
           (match["team1"] == squad2_name and match["team2"] == squad1_name):
            h2h["total"] += 1
            score1, score2 = map(int, match["score"].split('-'))
            
            if match["team1"] == squad1_name:
                if score1 > score2:
                    h2h["squad1_wins"] += 1
                elif score2 > score1:
                    h2h["squad2_wins"] += 1
                else:
                    h2h["draws"] += 1
            else:
                if score2 > score1:
                    h2h["squad1_wins"] += 1
                elif score1 > score2:
                    h2h["squad2_wins"] += 1
                else:
                    h2h["draws"] += 1
    
    return h2h

# -------------------- MODALS --------------------
class PlayerSetupModal(Modal, title="🎭 Royal Profile Setup"):
    ingame_name = TextInput(
        label="In-Game Name",
        placeholder="Enter your IGN",
        required=False,
        max_length=50
    )
    
    ingame_id = TextInput(
        label="In-Game ID",
        placeholder="Enter your game ID",
        required=False,
        max_length=50
    )
    
    highest_rank = TextInput(
        label="Highest Rank",
        placeholder="e.g., Mythic Glory, Legend, etc.",
        required=False,
        max_length=50
    )
    
    def __init__(self, user_id: int, squad_name: str, role: str, existing_data: dict = None):
        super().__init__()
        self.user_id = user_id
        self.squad_name = squad_name
        self.player_role = role
        self.existing_data = existing_data or {}
        
        # Pre-fill fields with existing data
        if existing_data:
            if existing_data.get("ingame_name"):
                self.ingame_name.default = existing_data.get("ingame_name")
            if existing_data.get("ingame_id"):
                self.ingame_id.default = existing_data.get("ingame_id")
            if existing_data.get("highest_rank"):
                self.highest_rank.default = existing_data.get("highest_rank")
    
    async def on_submit(self, interaction: discord.Interaction):
        player_key = str(self.user_id)
        
        # Get existing data or create new
        if player_key in squad_data["players"]:
            player_data = squad_data["players"][player_key]
        else:
            player_data = {
                "discord_id": self.user_id,
                "ingame_name": "",
                "ingame_id": "",
                "highest_rank": "",
                "role": "",
                "squad": self.squad_name,
                "squad_history": []
            }
        
        # Update only filled fields (or keep existing if not changed)
        if self.ingame_name.value:
            player_data["ingame_name"] = self.ingame_name.value
        if self.ingame_id.value:
            player_data["ingame_id"] = self.ingame_id.value
        if self.highest_rank.value:
            player_data["highest_rank"] = self.highest_rank.value
        
        # Always update role and squad
        player_data["role"] = self.player_role
        player_data["squad"] = self.squad_name
        
        squad_data["players"][player_key] = player_data
        save_data(squad_data)
        
        embed = discord.Embed(
            title="✅ Royal Profile Updated",
            description=f"Your warrior profile has been updated in the royal archives!",
            color=ROYAL_GOLD
        )
        embed.add_field(name="⚔️ IGN", value=player_data["ingame_name"] or "Not set", inline=True)
        embed.add_field(name="🎯 ID", value=player_data["ingame_id"] or "Not set", inline=True)
        embed.add_field(name="🏆 Rank", value=player_data["highest_rank"] or "Not set", inline=True)
        embed.add_field(name="💼 Role", value=f"{ROLE_EMOJIS.get(self.player_role, '⚔️')} {self.player_role}", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(
            interaction.guild,
            "🎭 Royal Profile Updated",
            f"{interaction.user.mention} updated their warrior profile"
        )

def get_match_participants(squad_name):
    """Get list of player IDs who should count for match stats.
    
    RULE: Only track mains if exactly 5 are set, otherwise count all.
    """
    squad_info = squad_data["squads"][squad_name]
    main_roster = squad_info.get("main_roster", [])
    
    # Only track specific players if exactly 5 mains are set
    if len(main_roster) == 5:
        return main_roster.copy()
    else:
        # Empty list = count all squad members (backward compat)
        return []

class AddMatchModal(Modal, title="⚔️ Record Battle Result"):
    team1 = TextInput(
        label="First Kingdom",
        placeholder="Enter exact squad name",
        required=True
    )
    
    team2 = TextInput(
        label="Second Kingdom",
        placeholder="Enter exact squad name",
        required=True
    )
    
    result = TextInput(
        label="Battle Outcome (team1_score-team2_score)",
        placeholder="e.g., 2-0, 1-1, 0-2",
        required=True,
        max_length=10
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.team1.value not in SQUADS or self.team2.value not in SQUADS:
            await interaction.response.send_message(
                "❌ One or both kingdom names are invalid. Use exact squad names.",
                ephemeral=True
            )
            return
        
        try:
            score1, score2 = map(int, self.result.value.split('-'))
        except:
            await interaction.response.send_message(
                "❌ Invalid result format. Use format: X-Y (e.g., 2-0)",
                ephemeral=True
            )
            return
        
        import random
        
        team1_data = squad_data["squads"][self.team1.value]
        team2_data = squad_data["squads"][self.team2.value]
        
        # Determine result and update stats with streaks
        if score1 > score2:
            team1_data["wins"] += 1
            team1_data["points"] += 2
            team2_data["losses"] += 1
            
            # Update streaks
            team1_streak = update_streak(self.team1.value, "win")
            team2_streak = update_streak(self.team2.value, "loss")
            
            result_text = f"🏆 **{self.team1.value}** has conquered **{self.team2.value}** in glorious battle!"
            flavor_quote = random.choice(VICTORY_QUOTES)
            winner = self.team1.value
            loser = self.team2.value
            
        elif score2 > score1:
            team2_data["wins"] += 1
            team2_data["points"] += 2
            team1_data["losses"] += 1
            
            # Update streaks
            team1_streak = update_streak(self.team1.value, "loss")
            team2_streak = update_streak(self.team2.value, "win")
            
            result_text = f"🏆 **{self.team2.value}** has conquered **{self.team1.value}** in glorious battle!"
            flavor_quote = random.choice(VICTORY_QUOTES)
            winner = self.team2.value
            loser = self.team1.value
            
        else:
            team1_data["draws"] += 1
            team1_data["points"] += 1
            team2_data["draws"] += 1
            team2_data["points"] += 1
            
            # Update streaks
            team1_streak = update_streak(self.team1.value, "draw")
            team2_streak = update_streak(self.team2.value, "draw")
            
            result_text = f"⚔️ **{self.team1.value}** and **{self.team2.value}** fought to an honorable stalemate!"
            flavor_quote = random.choice(DRAW_QUOTES)
            winner = None
            loser = None
        
        # Check for achievements
        team1_achievements = check_achievements(self.team1.value)
        team2_achievements = check_achievements(self.team2.value)
        
        # Generate unique match ID
        match_id = str(uuid.uuid4())[:8]
        
        # Get participants (only if exactly 5 mains are set)
        team1_participants = get_match_participants(self.team1.value)
        team2_participants = get_match_participants(self.team2.value)
        
        match_data = {
            "match_id": match_id,
            "team1": self.team1.value,
            "team2": self.team2.value,
            "score": self.result.value,
            "date": datetime.utcnow().isoformat(),
            "added_by": interaction.user.id,
            "team1_participants": team1_participants,
            "team2_participants": team2_participants
        }
        
        squad_data["matches"].append(match_data)
        team1_data["match_history"].append(match_data)
        team2_data["match_history"].append(match_data)
        
        save_data(squad_data)
        
        # Create enhanced result embed
        embed = discord.Embed(
            title="📜 Battle Chronicles Updated",
            description=f"{result_text}\n\n*{flavor_quote}*",
            color=ROYAL_GOLD
        )
        embed.add_field(name="🆔 Match ID", value=f"`{match_id}`", inline=False)
        embed.add_field(name="⚔️ Score", value=f"**{self.result.value}**", inline=True)
        
        # Team 1 info with streak
        team1_info = f"💎 {team1_data['points']} points | 🏆 {team1_data['wins']}W ⚔️ {team1_data['draws']}D 💀 {team1_data['losses']}L"
        if team1_streak["count"] >= 3:
            streak_emoji = "🔥" if team1_streak["type"] == "win" else "❄️" if team1_streak["type"] == "loss" else "⚡"
            team1_info += f"\n{streak_emoji} **{team1_streak['count']} {team1_streak['type'].upper()} STREAK!**"
        embed.add_field(
            name=f"{SQUADS[self.team1.value]} {self.team1.value}",
            value=team1_info,
            inline=False
        )
        
        # Team 2 info with streak
        team2_info = f"💎 {team2_data['points']} points | 🏆 {team2_data['wins']}W ⚔️ {team2_data['draws']}D 💀 {team2_data['losses']}L"
        if team2_streak["count"] >= 3:
            streak_emoji = "🔥" if team2_streak["type"] == "win" else "❄️" if team2_streak["type"] == "loss" else "⚡"
            team2_info += f"\n{streak_emoji} **{team2_streak['count']} {team2_streak['type'].upper()} STREAK!**"
        embed.add_field(
            name=f"{SQUADS[self.team2.value]} {self.team2.value}",
            value=team2_info,
            inline=False
        )
        
        # Add achievements if any were earned
        if team1_achievements or team2_achievements:
            achievement_text = ""
            if team1_achievements:
                achievement_text += f"🎖️ **{self.team1.value}** earned:\n"
                for ach in team1_achievements:
                    achievement_text += f"{ach['name']} - *{ach['desc']}*\n"
            if team2_achievements:
                achievement_text += f"🎖️ **{self.team2.value}** earned:\n"
                for ach in team2_achievements:
                    achievement_text += f"{ach['name']} - *{ach['desc']}*\n"
            embed.add_field(name="🏅 New Achievements!", value=achievement_text, inline=False)
        
        embed.set_footer(text=f"Match ID: {match_id} | May glory follow the victorious!")
        
        await interaction.response.send_message(embed=embed)
        await log_action(
            interaction.guild,
            "📜 Battle Recorded",
            f"{interaction.user.mention} recorded: {self.team1.value} vs {self.team2.value} ({self.result.value}) | ID: {match_id}"
        )

class SetLogoModal(Modal, title="🖼️ Set Royal Emblem"):
    logo_url = TextInput(
        label="Emblem URL",
        placeholder="Paste Discord image link or Imgur URL",
        required=True,
        style=discord.TextStyle.long
    )
    
    def __init__(self, squad_name: str):
        super().__init__()
        self.squad_name = squad_name
    
    async def on_submit(self, interaction: discord.Interaction):
        squad_data["squads"][self.squad_name]["logo_url"] = self.logo_url.value
        save_data(squad_data)
        
        embed = discord.Embed(
            title="✅ Royal Emblem Established",
            description=f"The crest of **{self.squad_name}** has been emblazoned!",
            color=ROYAL_GOLD
        )
        embed.set_thumbnail(url=self.logo_url.value)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(
            interaction.guild,
            "🖼️ Emblem Updated",
            f"{interaction.user.mention} updated the royal emblem for **{self.squad_name}**"
        )

class AddTitleModal(Modal, title="🏆 Award Championship Title"):
    squad_name = TextInput(
        label="Kingdom Name",
        placeholder="Enter exact squad name",
        required=True
    )
    
    title = TextInput(
        label="Title Name",
        placeholder="e.g., Champion, Tournament Winner",
        required=True
    )
    
    position = TextInput(
        label="Position",
        placeholder="e.g., 1st, 2nd, 3rd",
        required=True,
        max_length=10
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.squad_name.value not in SQUADS:
            await interaction.response.send_message(
                f"❌ Kingdom `{self.squad_name.value}` not found. Use exact squad name.",
                ephemeral=True
            )
            return
        
        squad_info = squad_data["squads"][self.squad_name.value]
        
        # Format the title with position
        full_title = f"{self.title.value} ({self.position.value} Place)"
        
        # Add title to list
        if "titles" not in squad_info:
            squad_info["titles"] = []
        
        squad_info["titles"].append(full_title)
        
        # Increment championship wins for 1st place
        if self.position.value.lower() in ["1st", "first", "1"]:
            squad_info["championship_wins"] = squad_info.get("championship_wins", 0) + 1
        
        save_data(squad_data)
        
        # Determine emoji based on position
        position_emoji = "🥇" if self.position.value.lower() in ["1st", "first", "1"] else "🥈" if self.position.value.lower() in ["2nd", "second", "2"] else "🥉"
        
        embed = discord.Embed(
            title="🏆 Royal Title Bestowed",
            description=f"{position_emoji} **{self.squad_name.value}** has been awarded the title:\n\n**{full_title}**",
            color=ROYAL_GOLD
        )
        
        if self.position.value.lower() in ["1st", "first", "1"]:
            embed.add_field(
                name="👑 Championship Glory",
                value=f"Total Championships: **{squad_info['championship_wins']}**",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
        await log_action(
            interaction.guild,
            "🏆 Title Awarded",
            f"{interaction.user.mention} awarded **{self.squad_name.value}** the title: {full_title}"
        )

class DeleteMatchModal(Modal, title="🗑️ Delete Match Result"):
    match_id = TextInput(
        label="Match ID",
        placeholder="Enter the match ID to delete",
        required=True,
        max_length=8
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        index, match = find_match_by_id(self.match_id.value)
        
        if match is None:
            await interaction.response.send_message(
                f"❌ Match with ID `{self.match_id.value}` not found.",
                ephemeral=True
            )
            return
        
        team1 = match["team1"]
        team2 = match["team2"]
        score = match["score"]
        
        try:
            score1, score2 = map(int, score.split('-'))
        except:
            await interaction.response.send_message("❌ Invalid match data.", ephemeral=True)
            return
        
        # Reverse the match results
        team1_data = squad_data["squads"][team1]
        team2_data = squad_data["squads"][team2]
        
        if score1 > score2:
            team1_data["wins"] -= 1
            team1_data["points"] -= 2
            team2_data["losses"] -= 1
        elif score2 > score1:
            team2_data["wins"] -= 1
            team2_data["points"] -= 2
            team1_data["losses"] -= 1
        else:
            team1_data["draws"] -= 1
            team1_data["points"] -= 1
            team2_data["draws"] -= 1
            team2_data["points"] -= 1
        
        # Remove from main matches list
        squad_data["matches"].pop(index)
        
        # Remove from team match histories
        team1_data["match_history"] = [m for m in team1_data["match_history"] if m.get("match_id") != self.match_id.value]
        team2_data["match_history"] = [m for m in team2_data["match_history"] if m.get("match_id") != self.match_id.value]
        
        # Recalculate streaks from scratch for both teams
        def recalculate_streak(squad_name):
            """Recalculate current streak from match history"""
            history = squad_data["squads"][squad_name].get("match_history", [])
            if not history:
                return {"type": "none", "count": 0}
            
            # Get results in chronological order
            results = []
            for match in history:
                if match["team1"] == squad_name:
                    s1, s2 = map(int, match["score"].split('-'))
                    if s1 > s2:
                        results.append("win")
                    elif s1 < s2:
                        results.append("loss")
                    else:
                        results.append("draw")
                else:
                    s1, s2 = map(int, match["score"].split('-'))
                    if s2 > s1:
                        results.append("win")
                    elif s2 < s1:
                        results.append("loss")
                    else:
                        results.append("draw")
            
            # Count current streak from most recent
            if not results:
                return {"type": "none", "count": 0}
            
            current_type = results[-1]
            count = 1
            for i in range(len(results) - 2, -1, -1):
                if results[i] == current_type:
                    count += 1
                else:
                    break
            
            return {"type": current_type, "count": count}
        
        team1_data["current_streak"] = recalculate_streak(team1)
        team2_data["current_streak"] = recalculate_streak(team2)
        
        save_data(squad_data)
        
        embed = discord.Embed(
            title="🗑️ Match Deleted",
            description=f"⚜️ Match between **{team1}** and **{team2}** has been erased from the chronicles.",
            color=ROYAL_RED
        )
        embed.add_field(name="Match ID", value=f"`{self.match_id.value}`", inline=True)
        embed.add_field(name="Score", value=score, inline=True)
        embed.set_footer(text="Points and records have been adjusted")
        
        await interaction.response.send_message(embed=embed)
        await log_action(
            interaction.guild,
            "🗑️ Match Deleted",
            f"{interaction.user.mention} deleted match {self.match_id.value}: {team1} vs {team2} ({score})"
        )

# -------------------- VIEWS --------------------
class RoleSelectView(View):
    def __init__(self, user_id: int, squad_name: str):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.squad_name = squad_name
        
        options = [
            discord.SelectOption(
                label=role, 
                emoji=ROLE_EMOJIS.get(role, "⚔️"),
                description=f"Become a {role}"
            )
            for role in ROLES
        ]
        
        select = Select(
            placeholder="⚔️ Choose your battle position...",
            options=options,
            custom_id="role_select"
        )
        select.callback = self.role_selected
        self.add_item(select)
    
    async def role_selected(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your setup panel, Royal warrior.", ephemeral=True)
            return
        
        selected_role = interaction.data["values"][0]
        
        # Get existing player data if available
        player_key = str(self.user_id)
        existing_data = squad_data["players"].get(player_key, {})
        
        modal = PlayerSetupModal(self.user_id, self.squad_name, selected_role, existing_data)
        await interaction.response.send_modal(modal)

class SquadBrowserView(View):
    def __init__(self, guild, page=1):
        super().__init__(timeout=180)
        self.guild = guild
        self.page = page
        
        # Get all squads sorted alphabetically
        all_squads = sorted(SQUADS.items())
        
        # Paginate: 25 per page (Discord limit)
        if page == 1:
            squads_to_show = all_squads[:25]
        else:
            squads_to_show = all_squads[25:]
        
        options = []
        for squad_name, tag in squads_to_show:
            options.append(
                discord.SelectOption(
                    label=squad_name,
                    value=squad_name,
                    emoji="🏰",
                    description=f"Tag: {tag}"
                )
            )
        
        select = Select(
            placeholder=f"🏰 Choose a kingdom to explore... (Page {page})",
            options=options,
            custom_id=f"squad_browser_select_p{page}"
        )
        select.callback = self.squad_selected
        self.add_item(select)
        
        # Add page navigation buttons if needed
        if len(all_squads) > 25:
            if page == 1:
                next_button = Button(label="Next Page →", style=discord.ButtonStyle.primary, emoji="➡️")
                next_button.callback = self.next_page
                self.add_item(next_button)
            else:
                prev_button = Button(label="← Previous Page", style=discord.ButtonStyle.primary, emoji="⬅️")
                prev_button.callback = self.prev_page
                self.add_item(prev_button)
    
    async def next_page(self, interaction: discord.Interaction):
        view = SquadBrowserView(self.guild, page=2)
        embed = discord.Embed(
            title="🏰 Kingdom Explorer - Page 2",
            description="⚜️ Select a kingdom from the dropdown to view their Royal house!",
            color=ROYAL_BLUE
        )
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def prev_page(self, interaction: discord.Interaction):
        view = SquadBrowserView(self.guild, page=1)
        embed = discord.Embed(
            title="🏰 Kingdom Explorer - Page 1",
            description="⚜️ Select a kingdom from the dropdown to view their Royal house!",
            color=ROYAL_BLUE
        )
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def squad_selected(self, interaction: discord.Interaction):
        selected_squad = interaction.data["values"][0]
        squad_role = discord.utils.get(self.guild.roles, name=selected_squad)
        tag = SQUADS.get(selected_squad, "?")
        
        await show_squad_info(interaction, squad_role, selected_squad, tag, public=True)

async def show_squad_info(interaction, squad_role, squad_name, tag, public=False):
    """Enhanced squad information display with royal theme"""
    squad_info = squad_data["squads"].get(squad_name, {})
    
    # Get ranking position and win rate
    rank = get_squad_rank(squad_name)
    rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "🏅"
    
    wins = squad_info.get('wins', 0)
    draws = squad_info.get('draws', 0)
    losses = squad_info.get('losses', 0)
    total_battles = wins + draws + losses
    win_rate = (wins / total_battles * 100) if total_battles > 0 else 0.0
    
    embed = discord.Embed(
        title=f"🏰 Kingdom of {squad_name}",
        description=f"⚜️ *A Royal house in the realm of warriors*",
        color=squad_role.color if squad_role else ROYAL_PURPLE
    )
    
    # Basic info
    embed.add_field(name="🏴 Banner", value=f"`{tag}`", inline=True)
    embed.add_field(name="💎 Glory Points", value=f"**{squad_info.get('points', 0)}**", inline=True)
    embed.add_field(name=f"{rank_emoji} Ranking", value=f"**#{rank}**" if rank else "Unranked", inline=True)
    
    # Record with win rate
    embed.add_field(
        name="⚔️ Battle Record",
        value=f"🏆 {wins}W • ⚔️ {draws}D • 💀 {losses}L\n📊 Total: {total_battles} | Win Rate: **{win_rate:.1f}%**",
        inline=False
    )
    
    # Current streak and mood
    current_streak = squad_info.get("current_streak", {"type": "none", "count": 0})
    mood = get_squad_mood(squad_name)
    
    status_text = f"{mood['emoji']} **{mood['status']}** - {mood['desc']}"
    if current_streak["count"] >= 2:
        streak_emoji = "🔥" if current_streak["type"] == "win" else "❄️" if current_streak["type"] == "loss" else "⚡"
        status_text += f"\n{streak_emoji} Current Streak: **{current_streak['count']} {current_streak['type'].upper()}**"
    
    embed.add_field(name="💫 Kingdom Status", value=status_text, inline=False)
    
    # Achievements
    achievements = squad_info.get("achievements", [])
    if achievements:
        achievement_text = ""
        for ach_key in achievements[:5]:  # Show first 5
            if ach_key in ACHIEVEMENTS:
                achievement_text += f"{ACHIEVEMENTS[ach_key]['name']}\n"
        if len(achievements) > 5:
            achievement_text += f"*...and {len(achievements) - 5} more!*"
        embed.add_field(name="🏅 Achievements Unlocked", value=achievement_text, inline=False)
    
    # Championships and Titles
    champ_wins = squad_info.get('championship_wins', 0)
    titles = squad_info.get('titles', [])
    if champ_wins > 0 or titles:
        honor_text = ""
        if champ_wins > 0:
            honor_text += f"🏆 {champ_wins} Championship{'s' if champ_wins != 1 else ''}\n"
        if titles:
            honor_text += f"📜 " + "\n📜 ".join(titles)
        embed.add_field(name="🎖️ Honors & Titles", value=honor_text, inline=False)
    
    # Main Roster and Subs
    main_roster = squad_info.get('main_roster', [])
    subs = squad_info.get('subs', [])
    
    if main_roster:
        roster_text = ""
        for player_id in main_roster[:5]:
            player_data = squad_data["players"].get(str(player_id), {})
            # Try to get the actual member from guild
            member = interaction.guild.get_member(player_id) if interaction.guild else None
            
            if player_data and player_data.get('ingame_name'):
                # Player has profile setup
                role_emoji = ROLE_EMOJIS.get(player_data.get('role', ''), '⚔️')
                discord_name = member.display_name if member else "Unknown"
                roster_text += f"{role_emoji} **{discord_name}** - {player_data.get('ingame_name')} (#{player_data.get('ingame_id', 'N/A')}) - {player_data.get('highest_rank', 'Unranked')}\n"
            elif member:
                # Player exists but no profile
                roster_text += f"⚔️ **{member.display_name}** - *No profile setup*\n"
            else:
                # Player left server
                roster_text += f"⚔️ **Unknown Warrior** - *Member left*\n"
        
        if roster_text:
            embed.add_field(name="⭐ Elite Warriors (Main Roster)", value=roster_text, inline=False)
    
    if subs:
        subs_text = ""
        for player_id in subs[:3]:
            player_data = squad_data["players"].get(str(player_id), {})
            member = interaction.guild.get_member(player_id) if interaction.guild else None
            
            if player_data and player_data.get('ingame_name'):
                # Player has profile setup
                role_emoji = ROLE_EMOJIS.get(player_data.get('role', ''), '⚔️')
                discord_name = member.display_name if member else "Unknown"
                subs_text += f"{role_emoji} **{discord_name}** - {player_data.get('ingame_name')} (#{player_data.get('ingame_id', 'N/A')})\n"
            elif member:
                # Player exists but no profile
                subs_text += f"⚔️ **{member.display_name}** - *No profile setup*\n"
            else:
                # Player left server
                subs_text += f"⚔️ **Unknown Warrior** - *Member left*\n"
        
        if subs_text:
            embed.add_field(name="🔄 Reserve Warriors (Substitutes)", value=subs_text, inline=False)
    
    # If no roster set, show all squad members with Discord names
    if not main_roster and not subs and squad_role:
        all_members_text = ""
        for member in squad_role.members[:20]:  # Limit to 20
            player_data = squad_data["players"].get(str(member.id), {})
            if player_data and player_data.get('ingame_name'):
                role_emoji = ROLE_EMOJIS.get(player_data.get('role', ''), '⚔️')
                all_members_text += f"{role_emoji} **{member.display_name}** - {player_data.get('ingame_name')}\n"
            else:
                all_members_text += f"⚔️ **{member.display_name}** - *Warrior (no profile)*\n"
        
        if all_members_text:
            embed.add_field(
                name=f"👥 Kingdom Members ({len(squad_role.members)})",
                value=all_members_text or "No members",
                inline=False
            )
        elif squad_role:
            embed.add_field(
                name=f"👥 Kingdom Members",
                value=f"{len(squad_role.members)} Royal warriors",
                inline=False
            )
    
    # Leaders
    leaders = get_leaders_for_squad(interaction.guild, squad_role) if squad_role else []
    if leaders:
        embed.add_field(name="👑 Royal Leaders", value=", ".join(leaders), inline=False)
    
    # Guests
    guest_role_name = GUEST_ROLES.get(squad_name)
    if guest_role_name:
        guest_role = discord.utils.get(interaction.guild.roles, name=guest_role_name)
        if guest_role and guest_role.members:
            guests = [m.display_name for m in guest_role.members[:10]]
            embed.add_field(name="🎭 Honored Guests", value=", ".join(guests), inline=False)
    
    # Logo
    logo_url = squad_info.get('logo_url')
    if logo_url:
        embed.set_thumbnail(url=logo_url)
    
    embed.set_footer(text="⚜️ Royal Squad Archives | Click button below for match history")
    
    # Add view with match history button
    view = SquadInfoView(squad_name)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=not public)

class SquadInfoView(View):
    """View for squad info with match history button"""
    def __init__(self, squad_name):
        super().__init__(timeout=180)
        self.squad_name = squad_name
    
    @discord.ui.button(label="Match History", emoji="📜", style=discord.ButtonStyle.primary)
    async def match_history_button(self, interaction: discord.Interaction, button: Button):
        await show_squad_match_history(interaction, self.squad_name)

async def show_player_profile(interaction, member: discord.Member, public=False):
    """Display comprehensive player profile"""
    player_key = str(member.id)
    player_data = squad_data["players"].get(player_key)
    
    if not player_data or not player_data.get("ingame_name"):
        # Friendly message suggesting profile setup
        embed = discord.Embed(
            title="🎭 Warrior Profile Not Found",
            description=f"⚜️ {member.mention} hasn't established their warrior profile yet.",
            color=ROYAL_BLUE
        )
        embed.add_field(
            name="💡 How to Create Your Profile",
            value="Use `/panel` → Click **'Setup Profile'** to create your warrior profile!\n\nYou can setup your profile even without joining a squad!",
            inline=False
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=not public)
        return
    
    # Get squad info
    squad_name = player_data.get("squad")
    squad_role = None
    squad_tag = "?"
    
    if squad_name and squad_name in SQUADS:
        squad_tag = SQUADS[squad_name]
        squad_role = discord.utils.get(interaction.guild.roles, name=squad_name)
    
    # Get player stats
    stats = get_player_stats(member.id)
    
    # Determine roster status
    roster_status = "⚔️ Kingdom Warrior"
    if squad_name and squad_name in squad_data["squads"]:
        squad_info = squad_data["squads"][squad_name]
        if member.id in squad_info.get("main_roster", []):
            roster_status = "⭐ Elite Warrior (Main Roster)"
        elif member.id in squad_info.get("subs", []):
            roster_status = "🔄 Reserve Warrior (Substitute)"
    
    embed = discord.Embed(
        title=f"🎭 Warrior Profile: {player_data.get('ingame_name', 'Unknown')}",
        description=f"⚜️ *{member.mention}'s Royal chronicle*",
        color=squad_role.color if squad_role else ROYAL_BLUE
    )
    
    # Basic Info
    embed.add_field(
        name="⚔️ In-Game Identity",
        value=f"**IGN:** {player_data.get('ingame_name', 'Unknown')}\n**ID:** #{player_data.get('ingame_id', 'N/A')}",
        inline=True
    )
    
    role = player_data.get('role', 'Unknown')
    role_emoji = ROLE_EMOJIS.get(role, '⚔️')
    embed.add_field(
        name="💼 Battle Position",
        value=f"{role_emoji} **{role}**",
        inline=True
    )
    
    embed.add_field(
        name="🏆 Peak Achievement",
        value=player_data.get('highest_rank', 'Unranked'),
        inline=True
    )
    
    # Kingdom affiliation
    if squad_name and squad_name != "Free Agent":
        embed.add_field(
            name="🏰 Kingdom Allegiance",
            value=f"{squad_tag} **{squad_name}**\n{roster_status}",
            inline=False
        )
    elif squad_name == "Free Agent":
        embed.add_field(
            name="🏰 Kingdom Allegiance",
            value="⚔️ **Free Agent** - Not sworn to any kingdom",
            inline=False
        )
    
    # Squad History
    squad_history = player_data.get("squad_history", [])
    if squad_history:
        history_text = ""
        for entry in squad_history[-5:]:  # Show last 5 squads
            squad = entry.get("squad", "Unknown")
            tag = SQUADS.get(squad, "?")
            try:
                left_date = datetime.fromisoformat(entry.get("left_date", ""))
                date_str = left_date.strftime("%b %Y")
            except:
                date_str = "Unknown"
            history_text += f"{tag} **{squad}** _(left {date_str})_\n"
        
        if len(squad_history) > 5:
            history_text += f"*...and {len(squad_history) - 5} more*"
        
        embed.add_field(
            name="📜 Kingdom History",
            value=history_text,
            inline=False
        )
    
    # Statistics (if available)
    if stats and squad_name and squad_name != "Free Agent":
        win_rate = stats['win_rate']
        embed.add_field(
            name="📊 Battle Statistics",
            value=(
                f"⚔️ Battles: {stats['matches_played']}\n"
                f"🏆 Victories: {stats['wins']}\n"
                f"⚔️ Draws: {stats['draws']}\n"
                f"💀 Defeats: {stats['losses']}\n"
                f"📈 Win Rate: {win_rate:.1f}%"
            ),
            inline=False
        )
    
    # Leadership status
    if is_leader(member):
        embed.add_field(
            name="👑 Royal Status",
            value="**LEADER** - Royal commander of the kingdom",
            inline=False
        )
    
    # Set member avatar as thumbnail
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="⚜️ Glory to the warrior | Use /panel → Setup Profile to update")
    
    await interaction.response.send_message(embed=embed, ephemeral=not public)

class HelpCategoryView(View):
    def __init__(self):
        super().__init__(timeout=180)
        
        options = [
            discord.SelectOption(
                label="Member Commands",
                value="member",
                emoji="👥",
                description="Commands available to all warriors"
            ),
            discord.SelectOption(
                label="Leader Commands",
                value="leader",
                emoji="👑",
                description="Commands for squad leaders"
            ),
            discord.SelectOption(
                label="Moderator Commands",
                value="moderator",
                emoji="🛡️",
                description="Commands for tournament moderators"
            )
        ]
        
        select = Select(
            placeholder="📜 Choose a category...",
            options=options,
            custom_id="help_category_select"
        )
        select.callback = self.category_selected
        self.add_item(select)
    
    async def category_selected(self, interaction: discord.Interaction):
        category = interaction.data["values"][0]
        
        if category == "member":
            embed = discord.Embed(
                title="👥 Member Commands",
                description="*Main panel with all features accessible via buttons*",
                color=ROYAL_BLUE
            )
            embed.add_field(
                name="/panel",
                value="📖 Opens the main member panel with buttons for:\n• Browse Kingdoms\n• View Rankings\n• My Kingdom\n• My Profile\n• Setup Profile\n• View Rivalry\n• Match History\n• Fun Stats\n• Leave Kingdom\n\n*All features are button-based - no typing required!*",
                inline=False
            )
            embed.add_field(
                name="/profile @user",
                value="🎭 View any warrior's profile publicly\n*Example: `/profile @JohnDoe`*",
                inline=False
            )
            
        elif category == "leader":
            embed = discord.Embed(
                title="👑 Leader Commands",
                description="*Main panel with all management features*",
                color=ROYAL_GOLD
            )
            embed.add_field(
                name="/leader_panel",
                value="📖 Opens the leader panel with buttons for:\n• Add Member\n• Remove Member\n• Set Main Roster (max 5)\n• Remove from Mains\n• Set Substitute (max 3)\n• Remove from Subs\n• Promote Leader\n• Give Guest\n• Remove Guest\n• Set Logo\n• View Kingdom\n\n*All features are button-based!*",
                inline=False
            )
            
        else:  # moderator
            embed = discord.Embed(
                title="🛡️ Moderator Commands",
                description="*Main panel with all moderation features*",
                color=ROYAL_PURPLE
            )
            embed.add_field(
                name="/mod_panel",
                value="📖 Opens the moderator panel with buttons for:\n• Record Battle\n• Award Title\n• Delete Match\n• Recent Matches\n• Clear History\n• Download Backup\n\n*All features are button-based!*",
                inline=False
            )
        
        embed.set_footer(text="⚜️ Royal Command Archives | Everything is button-based!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

class RankingsView(View):
    """Paginated view for rankings"""
    def __init__(self, page=1):
        super().__init__(timeout=180)
        self.page = page
        
        rankings = get_squad_ranking()
        total_pages = (len(rankings) + 14) // 15
        
        # Add pagination buttons if needed
        if page > 1:
            prev_button = Button(label="← Previous", style=discord.ButtonStyle.secondary, emoji="⬅️")
            prev_button.callback = self.prev_page
            self.add_item(prev_button)
        
        if page < total_pages:
            next_button = Button(label="Next →", style=discord.ButtonStyle.secondary, emoji="➡️")
            next_button.callback = self.next_page
            self.add_item(next_button)
    
    async def prev_page(self, interaction: discord.Interaction):
        await self.show_rankings(interaction, self.page - 1)
    
    async def next_page(self, interaction: discord.Interaction):
        await self.show_rankings(interaction, self.page + 1)
    
    async def show_rankings(self, interaction: discord.Interaction, page: int):
        rankings = get_squad_ranking()
        total_squads = len(rankings)
        total_pages = (total_squads + 14) // 15
        
        # Calculate pagination
        start_idx = (page - 1) * 15
        end_idx = min(start_idx + 15, total_squads)
        page_rankings = rankings[start_idx:end_idx]
        
        embed = discord.Embed(
            title="🏆 Royal Leaderboard",
            description=f"⚜️ *Current standings of the Royal houses* (Page {page}/{total_pages})",
            color=ROYAL_GOLD
        )
        
        for squad in page_rankings:
            i = squad["rank"]
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"🏅 **{i}.**"
            embed.add_field(
                name=f"{medal} {squad['tag']} {squad['name']}",
                value=f"💎 **{squad['points']}** pts | 🏆 {squad['wins']}W-{squad['draws']}D-{squad['losses']}L | 📊 WR: **{squad['win_rate']:.1f}%**",
                inline=False
            )
        
        embed.set_footer(text=f"⚜️ Glory to the victorious! | Showing all {total_squads} kingdoms")
        
        view = RankingsView(page=page)
        await interaction.response.edit_message(embed=embed, view=view)

class MemberPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Browse Kingdoms", style=discord.ButtonStyle.primary, emoji="🏰", row=0)
    async def browse_squads_button(self, interaction: discord.Interaction, button: Button):
        view = SquadBrowserView(interaction.guild, page=1)
        embed = discord.Embed(
            title="🏰 Kingdom Explorer - Page 1",
            description="⚜️ Select a kingdom from the dropdown to view their Royal house!",
            color=ROYAL_BLUE
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Rankings", style=discord.ButtonStyle.secondary, emoji="🏆", row=0)
    async def rankings_button(self, interaction: discord.Interaction, button: Button):
        rankings = get_squad_ranking()
        total_squads = len(rankings)
        total_pages = (total_squads + 14) // 15  # 15 per page
        
        embed = discord.Embed(
            title="🏆 Royal Leaderboard",
            description=f"⚜️ *Current standings of the Royal houses* (Page 1/{total_pages})",
            color=ROYAL_GOLD
        )
        
        # Show first 15 squads
        for squad in rankings[:15]:
            i = squad["rank"]
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"🏅 **{i}.**"
            embed.add_field(
                name=f"{medal} {squad['tag']} {squad['name']}",
                value=f"💎 **{squad['points']}** pts | 🏆 {squad['wins']}W-{squad['draws']}D-{squad['losses']}L | 📊 WR: **{squad['win_rate']:.1f}%**",
                inline=False
            )
        
        embed.set_footer(text=f"⚜️ Glory to the victorious! | Showing all {total_squads} kingdoms")
        
        # Create view with pagination if needed
        view = RankingsView(page=1) if total_pages > 1 else None
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="My Kingdom", style=discord.ButtonStyle.success, emoji="🛡️", row=0)
    async def my_squad_button(self, interaction: discord.Interaction, button: Button):
        role, tag = get_member_squad(interaction.user, interaction.guild)
        if not role:
            await interaction.response.send_message("❌ You are not sworn to any kingdom, Royal warrior.", ephemeral=True)
            return
        
        await show_squad_info(interaction, role, role.name, tag, public=False)
    
    @discord.ui.button(label="My Profile", style=discord.ButtonStyle.success, emoji="🎭", row=1)
    async def my_profile_button(self, interaction: discord.Interaction, button: Button):
        await show_player_profile(interaction, interaction.user, public=False)
    
    @discord.ui.button(label="Setup Profile", style=discord.ButtonStyle.primary, emoji="⚙️", row=1)
    async def setup_profile_button(self, interaction: discord.Interaction, button: Button):
        role, _ = get_member_squad(interaction.user, interaction.guild)
        squad_name = role.name if role else "Free Agent"
        
        view = RoleSelectView(interaction.user.id, squad_name)
        embed = discord.Embed(
            title="🎭 Warrior Profile Setup",
            description="⚜️ Select your battle position to inscribe your legacy in the royal archives.",
            color=ROYAL_PURPLE
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="View Rivalry", style=discord.ButtonStyle.secondary, emoji="⚔️", row=2)
    async def rivalry_button(self, interaction: discord.Interaction, button: Button):
        view = SquadSelectorView(purpose="rivalry", step=1)
        embed = discord.Embed(
            title="⚔️ Kingdom Rivalry",
            description="Select the first kingdom to compare:",
            color=ROYAL_BLUE
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Match History", style=discord.ButtonStyle.secondary, emoji="📜", row=2)
    async def history_button(self, interaction: discord.Interaction, button: Button):
        view = SquadSelectorView(purpose="history", step=1)
        embed = discord.Embed(
            title="📜 Kingdom Match History",
            description="Select a kingdom to view their recent battles:",
            color=ROYAL_BLUE
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Fun Stats", style=discord.ButtonStyle.secondary, emoji="🎲", row=2)
    async def fun_stats_button(self, interaction: discord.Interaction, button: Button):
        await show_fun_stats(interaction)
    
    @discord.ui.button(label="Leave Kingdom", style=discord.ButtonStyle.danger, emoji="🚪", row=3)
    async def leave_squad_button(self, interaction: discord.Interaction, button: Button):
        role, _ = get_member_squad(interaction.user, interaction.guild)
        if not role:
            await interaction.response.send_message("❌ You are not sworn to any kingdom.", ephemeral=True)
            return
        
        # Create confirmation view
        confirm_view = View(timeout=60)
        
        async def confirm_leave(confirm_interaction: discord.Interaction):
            if confirm_interaction.user.id != interaction.user.id:
                await confirm_interaction.response.send_message("❌ This is not your confirmation.", ephemeral=True)
                return
            
            # Update player profile - remove squad affiliation and track history
            update_player_squad(interaction.user.id, None, role.name)
            
            await interaction.user.remove_roles(role)
            await safe_nick_update(interaction.user, None, None)
            await confirm_interaction.response.send_message(
                f"🚪 You have departed from **{role.name}**. Your journey continues, Royal warrior.\n\n*Your profile and history have been preserved.*",
                ephemeral=True
            )
            await log_action(
                interaction.guild,
                "🚪 Kingdom Departed",
                f"{interaction.user.mention} has left **{role.name}**"
            )
        
        async def cancel_leave(cancel_interaction: discord.Interaction):
            if cancel_interaction.user.id != interaction.user.id:
                await cancel_interaction.response.send_message("❌ This is not your confirmation.", ephemeral=True)
                return
            await cancel_interaction.response.send_message("✅ Cancelled. You remain in your kingdom.", ephemeral=True)
        
        confirm_button = Button(label="✓ Confirm Leave", style=discord.ButtonStyle.danger)
        confirm_button.callback = confirm_leave
        
        cancel_button = Button(label="✗ Cancel", style=discord.ButtonStyle.secondary)
        cancel_button.callback = cancel_leave
        
        confirm_view.add_item(confirm_button)
        confirm_view.add_item(cancel_button)
        
        await interaction.response.send_message(
            f"⚠️ **Confirm Departure**\n\nAre you sure you want to leave **{role.name}**?\n\n*Your profile will be preserved and this kingdom will be added to your history.*",
            view=confirm_view,
            ephemeral=True
        )

# -------------------- MEMBER SELECTOR VIEW (Universal) --------------------

class MemberSelectorView(View):
    """Universal member selector for all leader/moderator actions"""
    def __init__(self, action, squad_role=None, squad_name=None, guild=None, page=1):
        super().__init__(timeout=180)
        self.action = action
        self.squad_role = squad_role
        self.squad_name = squad_name
        self.guild = guild
        self.page = page
        
        # Get appropriate member list based on action
        if action == "add_member":
            # Show all guild members not in any squad
            all_members = [m for m in guild.members if not m.bot]
            members = []
            for m in all_members:
                has_squad = False
                for squad in SQUADS.keys():
                    role = discord.utils.get(guild.roles, name=squad)
                    if role and role in m.roles:
                        has_squad = True
                        break
                if not has_squad:
                    members.append(m)
        
        elif action in ["remove_member", "set_main", "remove_main", "set_sub", "remove_sub", "promote_leader"]:
            # Show squad members
            members = squad_role.members if squad_role else []
        
        elif action in ["give_guest", "remove_guest"]:
            # Show all guild members
            members = [m for m in guild.members if not m.bot]
        
        elif action == "clear_history":
            # Show all members with profiles
            members = []
            for m in guild.members:
                if not m.bot and str(m.id) in squad_data["players"]:
                    members.append(m)
        
        else:
            members = []
        
        # Pagination
        start_idx = (page - 1) * 25
        end_idx = start_idx + 25
        page_members = members[start_idx:end_idx]
        
        if not page_members:
            # No members available
            return
        
        # Create dropdown
        options = [
            discord.SelectOption(
                label=member.display_name[:100],  # Discord limit
                value=str(member.id),
                description=f"@{member.name[:50]}"  # Discord limit
            )
            for member in page_members
        ]
        
        action_labels = {
            "add_member": "⚔️ Select warrior to recruit...",
            "remove_member": "Select warrior to remove...",
            "set_main": "⭐ Select warrior for main roster...",
            "remove_main": "Select warrior to remove from mains...",
            "set_sub": "🔄 Select warrior for substitutes...",
            "remove_sub": "Select warrior to remove from subs...",
            "promote_leader": "👑 Select warrior to promote...",
            "give_guest": "🎭 Select person for guest role...",
            "remove_guest": "Select person to remove guest...",
            "clear_history": "Select player to clear history..."
        }
        
        select = Select(
            placeholder=action_labels.get(action, "Select a member..."),
            options=options
        )
        select.callback = self.member_selected
        self.add_item(select)
        
        # Pagination buttons
        if len(members) > 25:
            if page > 1:
                prev_btn = Button(label="← Previous", style=discord.ButtonStyle.secondary)
                prev_btn.callback = self.prev_page
                self.add_item(prev_btn)
            if end_idx < len(members):
                next_btn = Button(label="Next →", style=discord.ButtonStyle.secondary)
                next_btn.callback = self.next_page
                self.add_item(next_btn)
    
    async def prev_page(self, interaction):
        view = MemberSelectorView(self.action, self.squad_role, self.squad_name, self.guild, self.page - 1)
        await interaction.response.edit_message(view=view)
    
    async def next_page(self, interaction):
        view = MemberSelectorView(self.action, self.squad_role, self.squad_name, self.guild, self.page + 1)
        await interaction.response.edit_message(view=view)
    
    async def member_selected(self, interaction):
        member_id = int(interaction.data["values"][0])
        member = self.guild.get_member(member_id)
        
        if not member:
            await interaction.response.edit_message(content="❌ Member not found!", embed=None, view=None)
            return
        
        # Execute the action
        if self.action == "add_member":
            await self.handle_add_member(interaction, member)
        elif self.action == "remove_member":
            await self.handle_remove_member(interaction, member)
        elif self.action == "set_main":
            await self.handle_set_main(interaction, member)
        elif self.action == "remove_main":
            await self.handle_remove_main(interaction, member)
        elif self.action == "set_sub":
            await self.handle_set_sub(interaction, member)
        elif self.action == "remove_sub":
            await self.handle_remove_sub(interaction, member)
        elif self.action == "promote_leader":
            await self.handle_promote_leader(interaction, member)
        elif self.action == "give_guest":
            await self.handle_give_guest(interaction, member)
        elif self.action == "remove_guest":
            await self.handle_remove_guest(interaction, member)
        elif self.action == "clear_history":
            await self.handle_clear_history(interaction, member)
    
    async def handle_add_member(self, interaction, member):
        """Add member to squad"""
        old_squad_role, _ = get_member_squad(member, self.guild)
        old_squad_name = old_squad_role.name if old_squad_role else None
        
        # Remove from other squads
        for r_name in SQUADS.keys():
            r = discord.utils.get(self.guild.roles, name=r_name)
            if r and r in member.roles:
                await member.remove_roles(r)
        
        await member.add_roles(self.squad_role)
        tag = SQUADS.get(self.squad_name, "")
        await safe_nick_update(member, self.squad_role, tag)
        
        update_player_squad(member.id, self.squad_name, old_squad_name)
        
        embed = discord.Embed(
            title="✅ Warrior Recruited",
            description=f"⚜️ {member.mention} has sworn allegiance to **{self.squad_name}**!",
            color=ROYAL_GOLD
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "➕ Warrior Recruited", f"{interaction.user.mention} recruited {member.mention} to **{self.squad_name}**")
    
    async def handle_remove_member(self, interaction, member):
        """Remove member from squad"""
        squad_info = squad_data["squads"][self.squad_name]
        
        if member.id in squad_info.get("main_roster", []):
            squad_info["main_roster"].remove(member.id)
        if member.id in squad_info.get("subs", []):
            squad_info["subs"].remove(member.id)
        
        await member.remove_roles(self.squad_role)
        await safe_nick_update(member, None, "")
        update_player_squad(member.id, "Free Agent", self.squad_name)
        save_data(squad_data)
        
        embed = discord.Embed(
            title="✅ Warrior Dismissed",
            description=f"⚜️ {member.mention} has been released from **{self.squad_name}**",
            color=ROYAL_PURPLE
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "➖ Warrior Dismissed", f"{interaction.user.mention} removed {member.mention} from **{self.squad_name}**")
    
    async def handle_set_main(self, interaction, member):
        """Set member as main roster"""
        squad_info = squad_data["squads"][self.squad_name]
        main_roster = squad_info.get("main_roster", [])
        
        if len(main_roster) >= 5:
            await interaction.response.edit_message(content="❌ Main roster is full (maximum 5 warriors)!", embed=None, view=None)
            return
        
        if member.id in main_roster:
            await interaction.response.edit_message(content=f"❌ {member.mention} is already in the main roster!", embed=None, view=None)
            return
        
        if member.id in squad_info.get("subs", []):
            squad_info["subs"].remove(member.id)
        
        main_roster.append(member.id)
        save_data(squad_data)
        
        embed = discord.Embed(
            title="⭐ Elite Roster Updated",
            description=f"⚜️ {member.mention} has been promoted to the main roster of **{self.squad_name}**!",
            color=ROYAL_GOLD
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "⭐ Main Roster Set", f"{interaction.user.mention} added {member.mention} to main roster")
    
    async def handle_remove_main(self, interaction, member):
        """Remove from main roster"""
        squad_info = squad_data["squads"][self.squad_name]
        main_roster = squad_info.get("main_roster", [])
        
        if member.id not in main_roster:
            await interaction.response.edit_message(content=f"❌ {member.mention} is not in the main roster!", embed=None, view=None)
            return
        
        main_roster.remove(member.id)
        save_data(squad_data)
        
        embed = discord.Embed(
            title="✅ Roster Updated",
            description=f"⚜️ {member.mention} has been removed from the main roster",
            color=ROYAL_PURPLE
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "❌ Main Roster Removed", f"{interaction.user.mention} removed {member.mention} from main roster")
    
    async def handle_set_sub(self, interaction, member):
        """Set member as substitute"""
        squad_info = squad_data["squads"][self.squad_name]
        subs = squad_info.get("subs", [])
        
        if len(subs) >= 3:
            await interaction.response.edit_message(content="❌ Substitute roster is full (maximum 3 warriors)!", embed=None, view=None)
            return
        
        if member.id in subs:
            await interaction.response.edit_message(content=f"❌ {member.mention} is already a substitute!", embed=None, view=None)
            return
        
        if member.id in squad_info.get("main_roster", []):
            squad_info["main_roster"].remove(member.id)
        
        subs.append(member.id)
        save_data(squad_data)
        
        embed = discord.Embed(
            title="🔄 Reserve Roster Updated",
            description=f"⚜️ {member.mention} has been added to the reserve roster of **{self.squad_name}**!",
            color=ROYAL_BLUE
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "🔄 Substitute Set", f"{interaction.user.mention} added {member.mention} to substitutes")
    
    async def handle_remove_sub(self, interaction, member):
        """Remove from substitutes"""
        squad_info = squad_data["squads"][self.squad_name]
        subs = squad_info.get("subs", [])
        
        if member.id not in subs:
            await interaction.response.edit_message(content=f"❌ {member.mention} is not in the substitute roster!", embed=None, view=None)
            return
        
        subs.remove(member.id)
        save_data(squad_data)
        
        embed = discord.Embed(
            title="✅ Roster Updated",
            description=f"⚜️ {member.mention} has been removed from the substitute roster",
            color=ROYAL_PURPLE
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "❌ Substitute Removed", f"{interaction.user.mention} removed {member.mention} from substitutes")
    
    async def handle_promote_leader(self, interaction, member):
        """Promote member to leader"""
        leader_role = discord.utils.get(self.guild.roles, name=LEADER_ROLE_NAME)
        if not leader_role:
            await interaction.response.edit_message(content="❌ Leader role not found!", embed=None, view=None)
            return
        
        await member.add_roles(leader_role)
        
        embed = discord.Embed(
            title="👑 Leadership Bestowed",
            description=f"⚜️ {member.mention} has been promoted to **Royal Leader** of **{self.squad_name}**!",
            color=ROYAL_GOLD
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "👑 Leader Promoted", f"{interaction.user.mention} promoted {member.mention} to leader")
    
    async def handle_give_guest(self, interaction, member):
        """Give guest role"""
        guest_role_name = GUEST_ROLES.get(self.squad_name)
        if not guest_role_name:
            await interaction.response.edit_message(content="❌ Guest role not configured for this kingdom!", embed=None, view=None)
            return
        
        guest_role = discord.utils.get(self.guild.roles, name=guest_role_name)
        if not guest_role:
            await interaction.response.edit_message(content=f"❌ Guest role '{guest_role_name}' not found!", embed=None, view=None)
            return
        
        await member.add_roles(guest_role)
        
        embed = discord.Embed(
            title="🎭 Guest Privileges Granted",
            description=f"⚜️ {member.mention} has been granted guest access to **{self.squad_name}**!",
            color=ROYAL_BLUE
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "🎭 Guest Added", f"{interaction.user.mention} gave guest role to {member.mention}")
    
    async def handle_remove_guest(self, interaction, member):
        """Remove guest role"""
        guest_role_name = GUEST_ROLES.get(self.squad_name)
        if not guest_role_name:
            await interaction.response.edit_message(content="❌ Guest role not configured!", embed=None, view=None)
            return
        
        guest_role = discord.utils.get(self.guild.roles, name=guest_role_name)
        if not guest_role or guest_role not in member.roles:
            await interaction.response.edit_message(content=f"❌ {member.mention} doesn't have the guest role!", embed=None, view=None)
            return
        
        await member.remove_roles(guest_role)
        
        embed = discord.Embed(
            title="✅ Guest Privileges Revoked",
            description=f"⚜️ {member.mention}'s guest access has been removed",
            color=ROYAL_PURPLE
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "❌ Guest Removed", f"{interaction.user.mention} removed guest role from {member.mention}")
    
    async def handle_clear_history(self, interaction, member):
        """Clear player's squad history"""
        player_key = str(member.id)
        
        if player_key not in squad_data["players"]:
            await interaction.response.edit_message(
                content=f"❌ {member.mention} doesn't have a profile in the system.",
                embed=None,
                view=None
            )
            return
        
        player_data = squad_data["players"][player_key]
        old_history = player_data.get("squad_history", [])
        
        if not old_history:
            await interaction.response.edit_message(
                content=f"ℹ️ {member.mention} has no squad history to clear.",
                embed=None,
                view=None
            )
            return
        
        # Clear the history
        player_data["squad_history"] = []
        save_data(squad_data)
        
        embed = discord.Embed(
            title="🗑️ Squad History Cleared",
            description=f"⚜️ Cleared squad history for {member.mention}",
            color=ROYAL_PURPLE
        )
        embed.add_field(
            name="📜 Squads Removed from History",
            value=f"**{len(old_history)}** previous squad{'s' if len(old_history) != 1 else ''} cleared",
            inline=False
        )
        
        # List what was cleared
        if old_history:
            cleared_text = ""
            for entry in old_history[:5]:
                squad = entry.get("squad", "Unknown")
                tag = SQUADS.get(squad, "?")
                cleared_text += f"{tag} {squad}\n"
            if len(old_history) > 5:
                cleared_text += f"*...and {len(old_history) - 5} more*"
            embed.add_field(name="Cleared Squads", value=cleared_text, inline=False)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="This action cannot be undone")
        
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(
            self.guild,
            "🗑️ Squad History Cleared",
            f"{interaction.user.mention} cleared squad history for {member.mention}"
        )

# -------------------- LEADER PANEL VIEW (Complete Button-Based) --------------------

class LeaderPanelView(View):
    """Complete button-based leader panel"""
    def __init__(self, squad_role, tag: str, squad_name: str, guest_role):
        super().__init__(timeout=None)
        self.squad_role = squad_role
        self.tag = tag
        self.squad_name = squad_name
        self.guest_role = guest_role
    
    @discord.ui.button(label="Add Member", emoji="➕", style=discord.ButtonStyle.success, row=0)
    async def add_member_button(self, interaction: discord.Interaction, button: Button):
        view = MemberSelectorView("add_member", self.squad_role, self.squad_name, interaction.guild)
        embed = discord.Embed(title="➕ Recruit Warrior", description="Select a member to recruit to your kingdom:", color=ROYAL_GOLD)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Remove Member", emoji="➖", style=discord.ButtonStyle.danger, row=0)
    async def remove_member_button(self, interaction: discord.Interaction, button: Button):
        view = MemberSelectorView("remove_member", self.squad_role, self.squad_name, interaction.guild)
        embed = discord.Embed(title="➖ Remove Warrior", description="Select a member to remove from your kingdom:", color=ROYAL_PURPLE)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="View Kingdom", emoji="🏰", style=discord.ButtonStyle.primary, row=0)
    async def view_kingdom_button(self, interaction: discord.Interaction, button: Button):
        await show_squad_info(interaction, self.squad_role, self.squad_name, self.tag, public=False)
    
    @discord.ui.button(label="Set Main Roster", emoji="⭐", style=discord.ButtonStyle.primary, row=1)
    async def set_main_button(self, interaction: discord.Interaction, button: Button):
        view = MemberSelectorView("set_main", self.squad_role, self.squad_name, interaction.guild)
        embed = discord.Embed(title="⭐ Set Main Roster", description="Select a member to add to the main roster (max 5):", color=ROYAL_GOLD)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Remove from Mains", emoji="❌", style=discord.ButtonStyle.secondary, row=1)
    async def remove_main_button(self, interaction: discord.Interaction, button: Button):
        view = MemberSelectorView("remove_main", self.squad_role, self.squad_name, interaction.guild)
        embed = discord.Embed(title="❌ Remove from Main Roster", description="Select a member to remove from the main roster:", color=ROYAL_PURPLE)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Set Substitute", emoji="🔄", style=discord.ButtonStyle.primary, row=2)
    async def set_sub_button(self, interaction: discord.Interaction, button: Button):
        view = MemberSelectorView("set_sub", self.squad_role, self.squad_name, interaction.guild)
        embed = discord.Embed(title="🔄 Set Substitute", description="Select a member to add to substitutes (max 3):", color=ROYAL_BLUE)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Remove from Subs", emoji="❌", style=discord.ButtonStyle.secondary, row=2)
    async def remove_sub_button(self, interaction: discord.Interaction, button: Button):
        view = MemberSelectorView("remove_sub", self.squad_role, self.squad_name, interaction.guild)
        embed = discord.Embed(title="❌ Remove from Substitutes", description="Select a member to remove from substitutes:", color=ROYAL_PURPLE)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Promote Leader", emoji="👑", style=discord.ButtonStyle.primary, row=3)
    async def promote_leader_button(self, interaction: discord.Interaction, button: Button):
        view = MemberSelectorView("promote_leader", self.squad_role, self.squad_name, interaction.guild)
        embed = discord.Embed(title="👑 Promote Leader", description="Select a member to promote to leader:", color=ROYAL_GOLD)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Give Guest", emoji="🎭", style=discord.ButtonStyle.secondary, row=3)
    async def give_guest_button(self, interaction: discord.Interaction, button: Button):
        view = MemberSelectorView("give_guest", self.squad_role, self.squad_name, interaction.guild)
        embed = discord.Embed(title="🎭 Grant Guest Access", description="Select someone to give guest privileges:", color=ROYAL_BLUE)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Remove Guest", emoji="❌", style=discord.ButtonStyle.secondary, row=3)
    async def remove_guest_button(self, interaction: discord.Interaction, button: Button):
        view = MemberSelectorView("remove_guest", self.squad_role, self.squad_name, interaction.guild)
        embed = discord.Embed(title="❌ Revoke Guest Access", description="Select someone to remove guest privileges:", color=ROYAL_PURPLE)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Set Logo", emoji="🖼️", style=discord.ButtonStyle.primary, row=4)
    async def set_logo_button(self, interaction: discord.Interaction, button: Button):
        modal = SetLogoModal(self.squad_name)
        await interaction.response.send_modal(modal)

class ModeratorPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Record Battle", style=discord.ButtonStyle.primary, emoji="⚔️", row=0)
    async def add_match_button(self, interaction: discord.Interaction, button: Button):
        modal = AddMatchModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Award Title", style=discord.ButtonStyle.success, emoji="🏆", row=0)
    async def add_title_button(self, interaction: discord.Interaction, button: Button):
        modal = AddTitleModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Delete Match", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
    async def delete_match_button(self, interaction: discord.Interaction, button: Button):
        modal = DeleteMatchModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Recent Matches", style=discord.ButtonStyle.secondary, emoji="📜", row=1)
    async def recent_matches_button(self, interaction: discord.Interaction, button: Button):
        await show_recent_matches(interaction, limit=10)
    
    @discord.ui.button(label="Clear History", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
    async def clear_history_button(self, interaction: discord.Interaction, button: Button):
        view = MemberSelectorView("clear_history", guild=interaction.guild)
        embed = discord.Embed(
            title="🗑️ Clear Squad History",
            description="Select a player to clear their squad history:",
            color=ROYAL_RED
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Download Backup", style=discord.ButtonStyle.secondary, emoji="💾", row=2)
    async def download_button(self, interaction: discord.Interaction, button: Button):
        if not os.path.exists(DATA_FILE):
            await interaction.response.send_message("❌ No data file found.", ephemeral=True)
            return
        
        try:
            await interaction.response.send_message(
                "💾 **Squad Data Backup**\n\n⚜️ Here is your complete squad data file.\n\n*Save this file securely as a backup!*",
                file=discord.File(DATA_FILE, filename=f"squad_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"),
                ephemeral=True
            )
            await log_action(
                interaction.guild,
                "💾 Data Backup Downloaded",
                f"{interaction.user.mention} downloaded squad data backup"
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Error downloading file: {e}", ephemeral=True)

# -------------------- SQUAD SELECTOR & HELPER FUNCTIONS --------------------

class SquadSelectorView(View):
    """Universal squad selector dropdown for rivalry and match history"""
    def __init__(self, purpose, step=1, selected_squad1=None, page=1):
        super().__init__(timeout=180)
        self.purpose = purpose  # "rivalry" or "history"
        self.step = step
        self.selected_squad1 = selected_squad1
        self.page = page
        
        # Get squads for this page (25 per page due to Discord limit)
        all_squads = sorted(SQUADS.items())
        start_idx = (page - 1) * 25
        end_idx = start_idx + 25
        page_squads = all_squads[start_idx:end_idx]
        
        # Create dropdown options
        options = [
            discord.SelectOption(
                label=squad_name,
                value=squad_name,
                emoji="🏰",
                description=f"Tag: {tag}"
            )
            for squad_name, tag in page_squads
        ]
        
        # Set placeholder based on purpose
        placeholder_map = {
            ("rivalry", 1): "⚔️ Select first kingdom...",
            ("rivalry", 2): "⚔️ Select second kingdom...",
            ("history", 1): "📜 Select kingdom to view match history..."
        }
        placeholder = placeholder_map.get((purpose, step), "Select a kingdom...")
        
        select = Select(placeholder=placeholder, options=options)
        select.callback = self.squad_selected
        self.add_item(select)
        
        # Add pagination buttons if needed
        if len(all_squads) > 25:
            if page > 1:
                prev_btn = Button(label="← Previous", style=discord.ButtonStyle.secondary)
                prev_btn.callback = self.prev_page
                self.add_item(prev_btn)
            if end_idx < len(all_squads):
                next_btn = Button(label="Next →", style=discord.ButtonStyle.secondary)
                next_btn.callback = self.next_page
                self.add_item(next_btn)
    
    async def prev_page(self, interaction):
        view = SquadSelectorView(self.purpose, self.step, self.selected_squad1, self.page - 1)
        await interaction.response.edit_message(view=view)
    
    async def next_page(self, interaction):
        view = SquadSelectorView(self.purpose, self.step, self.selected_squad1, self.page + 1)
        await interaction.response.edit_message(view=view)
    
    async def squad_selected(self, interaction):
        selected = interaction.data["values"][0]
        
        if self.purpose == "rivalry":
            if self.step == 1:
                # Show squad 2 selector
                view = SquadSelectorView("rivalry", step=2, selected_squad1=selected)
                embed = discord.Embed(
                    title="⚔️ Kingdom Rivalry",
                    description=f"✅ First Kingdom: **{SQUADS[selected]} {selected}**\n\nNow select the second kingdom:",
                    color=ROYAL_BLUE
                )
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                # Show rivalry stats
                await show_rivalry_stats(interaction, self.selected_squad1, selected)
        
        elif self.purpose == "history":
            # Show squad match history
            await show_squad_match_history(interaction, selected)

async def show_rivalry_stats(interaction, squad1, squad2):
    """Display rivalry statistics between two squads"""
    if squad1 == squad2:
        await interaction.response.edit_message(
            content="❌ A kingdom cannot rival itself!",
            embed=None,
            view=None
        )
        return
    
    h2h = get_head_to_head(squad1, squad2)
    
    if h2h["total"] == 0:
        embed = discord.Embed(
            title="⚔️ Kingdom Rivalry",
            description=f"**{SQUADS[squad1]} {squad1}** and **{SQUADS[squad2]} {squad2}** have not yet clashed in battle!",
            color=ROYAL_BLUE
        )
        await interaction.response.edit_message(embed=embed, view=None)
        return
    
    # Determine dominant squad
    if h2h["squad1_wins"] > h2h["squad2_wins"]:
        dominant = squad1
        dominant_wins = h2h["squad1_wins"]
    elif h2h["squad2_wins"] > h2h["squad1_wins"]:
        dominant = squad2
        dominant_wins = h2h["squad2_wins"]
    else:
        dominant = None
    
    embed = discord.Embed(
        title="⚔️ Kingdom Rivalry",
        description=f"**{SQUADS[squad1]} {squad1}** vs **{SQUADS[squad2]} {squad2}**",
        color=ROYAL_RED
    )
    
    embed.add_field(
        name="📊 Head-to-Head Record",
        value=f"Total Battles: **{h2h['total']}**\n\n"
              f"🏆 {squad1}: **{h2h['squad1_wins']}** wins\n"
              f"🏆 {squad2}: **{h2h['squad2_wins']}** wins\n"
              f"🤝 Draws: **{h2h['draws']}**",
        inline=False
    )
    
    if dominant:
        dominance = (dominant_wins / h2h["total"]) * 100
        embed.add_field(
            name="👑 Dominant Kingdom",
            value=f"**{dominant}** leads the rivalry with **{dominance:.1f}%** dominance!",
            inline=False
        )
    else:
        embed.add_field(
            name="⚖️ Perfect Balance",
            value="The rivalry stands perfectly balanced! Both kingdoms are equally matched.",
            inline=False
        )
    
    embed.set_footer(text="⚜️ May the best kingdom prevail!")
    await interaction.response.edit_message(embed=embed, view=None)

async def show_squad_match_history(interaction, squad_name):
    """Show recent match history for a squad"""
    squad_matches = [
        m for m in squad_data["matches"]
        if m["team1"] == squad_name or m["team2"] == squad_name
    ]
    
    if not squad_matches:
        embed = discord.Embed(
            title=f"📜 {squad_name} Match History",
            description="⚜️ This kingdom has not yet entered battle!",
            color=ROYAL_BLUE
        )
        await interaction.response.edit_message(embed=embed, view=None)
        return
    
    # Show last 10 matches (newest first)
    recent = squad_matches[-10:][::-1]
    
    embed = discord.Embed(
        title=f"📜 {SQUADS[squad_name]} {squad_name} Match History",
        description=f"⚜️ Last {len(recent)} battles",
        color=ROYAL_BLUE
    )
    
    for match in recent:
        team1 = match["team1"]
        team2 = match["team2"]
        score = match["score"]
        match_id = match.get("match_id", "N/A")
        
        try:
            dt = datetime.fromisoformat(match.get("date", ""))
            date_str = dt.strftime("%b %d, %Y")
        except:
            date_str = "Unknown"
        
        # Determine result for this squad
        try:
            score1, score2 = map(int, score.split('-'))
            if team1 == squad_name:
                if score1 > score2:
                    result_emoji, result_text = "🏆", "Victory"
                elif score2 > score1:
                    result_emoji, result_text = "💀", "Defeat"
                else:
                    result_emoji, result_text = "⚖️", "Draw"
            else:
                if score2 > score1:
                    result_emoji, result_text = "🏆", "Victory"
                elif score1 > score2:
                    result_emoji, result_text = "💀", "Defeat"
                else:
                    result_emoji, result_text = "⚖️", "Draw"
        except:
            result_emoji, result_text = "⚔️", "Battle"
        
        embed.add_field(
            name=f"{result_emoji} {SQUADS[team1]} vs {SQUADS[team2]} - {result_text}",
            value=f"**{team1}** {score} **{team2}**\n📅 {date_str} • 🆔 `{match_id}`",
            inline=False
        )
    
    footer_text = f"⚜️ Showing last 10 of {len(squad_matches)} total battles" if len(squad_matches) > 10 else "⚜️ Glory to the warriors!"
    embed.set_footer(text=footer_text)
    
    await interaction.response.edit_message(embed=embed, view=None)

async def show_fun_stats(interaction):
    """Show interesting statistics and trivia"""
    
    # Calculate fun stats
    total_matches = len(squad_data["matches"])
    total_points = sum(s["points"] for s in squad_data["squads"].values())
    total_wins = sum(s["wins"] for s in squad_data["squads"].values())
    total_draws = sum(s["draws"] for s in squad_data["squads"].values())
    
    # Find squads with longest streaks
    longest_win_streak_squad = None
    longest_win_streak = 0
    for squad_name, data in squad_data["squads"].items():
        if data.get("biggest_win_streak", 0) > longest_win_streak:
            longest_win_streak = data.get("biggest_win_streak", 0)
            longest_win_streak_squad = squad_name
    
    # Find most active squad
    most_active_squad = None
    most_matches = 0
    for squad_name, data in squad_data["squads"].items():
        matches = data["wins"] + data["draws"] + data["losses"]
        if matches > most_matches:
            most_matches = matches
            most_active_squad = squad_name
    
    # Find squad with most achievements
    most_achievements_squad = None
    most_achievements = 0
    for squad_name, data in squad_data["squads"].items():
        ach_count = len(data.get("achievements", []))
        if ach_count > most_achievements:
            most_achievements = ach_count
            most_achievements_squad = squad_name
    
    # Get current top 3
    rankings = get_squad_ranking()[:3]
    
    embed = discord.Embed(
        title="🎲 Royal Realm Statistics & Trivia",
        description="⚜️ *Fascinating facts from the kingdom chronicles!*",
        color=ROYAL_GOLD
    )
    
    embed.add_field(
        name="📊 Global Stats",
        value=f"⚔️ Total Battles Fought: **{total_matches}**\n"
              f"💎 Total Glory Points: **{total_points}**\n"
              f"🏆 Total Victories: **{total_wins}**\n"
              f"🤝 Total Draws: **{total_draws}**",
        inline=False
    )
    
    if longest_win_streak_squad and longest_win_streak > 0:
        embed.add_field(
            name="🔥 Longest Win Streak",
            value=f"**{longest_win_streak_squad}** with **{longest_win_streak}** consecutive victories!",
            inline=False
        )
    
    if most_active_squad and most_matches > 0:
        embed.add_field(
            name="⚔️ Most Battle-Hardened",
            value=f"**{most_active_squad}** has fought in **{most_matches}** battles!",
            inline=False
        )
    
    if most_achievements_squad and most_achievements > 0:
        embed.add_field(
            name="🏅 Achievement Master",
            value=f"**{most_achievements_squad}** has unlocked **{most_achievements}** achievements!",
            inline=False
        )
    
    if rankings:
        podium = ""
        for i, squad in enumerate(rankings, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            podium += f"{medal} **{squad['name']}** ({squad['points']} pts)\n"
        embed.add_field(name="👑 Current Top 3", value=podium, inline=False)
    
    # Random fun fact
    import random
    fun_facts = [
        f"🎯 The realm has witnessed **{total_matches}** epic battles!",
        f"💎 Warriors have accumulated **{total_points}** glory points total!",
        f"🌟 On average, each kingdom has **{total_points // len(SQUADS):.1f}** points!",
        f"⚔️ **{(total_draws / total_matches * 100):.1f}%** of battles end in honorable draws!" if total_matches > 0 else "⚔️ The first battles are yet to be fought!",
        f"🏰 **{len(SQUADS)}** noble kingdoms vie for supremacy!",
    ]
    
    embed.add_field(
        name="💡 Did You Know?",
        value=random.choice(fun_facts),
        inline=False
    )
    
    embed.set_footer(text="⚜️ History is written by the victorious!")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

async def show_recent_matches(interaction, limit=10):
    """Show recent matches"""
    if limit < 1 or limit > 25:
        await interaction.response.send_message("❌ Limit must be between 1 and 25.", ephemeral=True)
        return
    
    recent = squad_data["matches"][-limit:][::-1]  # Last N matches, reversed
    
    if not recent:
        await interaction.response.send_message("📜 No matches recorded yet.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="📜 Recent Battle Chronicles",
        description=f"⚜️ *Last {len(recent)} recorded battles*",
        color=ROYAL_PURPLE
    )
    
    for match in recent:
        match_id = match.get("match_id", "unknown")
        team1 = match["team1"]
        team2 = match["team2"]
        score = match["score"]
        date = match.get("date", "Unknown date")
        
        try:
            dt = datetime.fromisoformat(date)
            date_str = dt.strftime("%b %d, %Y %H:%M")
        except:
            date_str = "Unknown date"
        
        embed.add_field(
            name=f"⚔️ {SQUADS.get(team1, '?')} vs {SQUADS.get(team2, '?')}",
            value=f"**{team1}** {score} **{team2}**\n🆔 `{match_id}` • 📅 {date_str}",
            inline=False
        )
    
    embed.set_footer(text="Use Delete Match button in mod panel to remove a match")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# -------------------- READY --------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    safety_sync.start()
    print(f"✅ Logged in as {bot.user}")
    print(f"⚜️ Royal Squad Bot is ready to serve!")
    
    for guild in bot.guilds:
        for member in guild.members:
            role, tag = get_member_squad(member, guild)
            await safe_nick_update(member, role, tag)
    
    print("✅ Initial sync done")

# -------------------- INSTANT ROLE SYNC --------------------
@bot.event
async def on_member_update(before, after):
    role, tag = get_member_squad(after, after.guild)
    await bot.wait_until_ready()
    await safe_nick_update(after, role, tag)

# -------------------- SAFETY SYNC --------------------
@tasks.loop(minutes=5)
async def safety_sync():
    for guild in bot.guilds:
        for member in guild.members:
            role, tag = get_member_squad(member, guild)
            await safe_nick_update(member, role, tag)

# -------------------- MAIN SLASH COMMANDS (Only 5 commands!) --------------------

@bot.tree.command(name="panel", description="👥 Open the main member panel")
async def panel_command(interaction: discord.Interaction):
    """Main member panel - all features accessible via buttons"""
    view = MemberPanelView()
    
    # Get quick stats
    total_squads = len(SQUADS)
    total_matches = len(squad_data["matches"])
    rankings = get_squad_ranking()
    top_squad = rankings[0] if rankings else None
    
    # Get user's squad if they have one
    user_role, user_tag = get_member_squad(interaction.user, interaction.guild)
    user_squad_text = f"\n\n🛡️ **Your Kingdom:** {user_tag} {user_role.name}" if user_role else "\n\n⚔️ **Status:** Free Agent"
    
    embed = discord.Embed(
        title="👥 Royal Member Hall",
        description=f"⚜️ *Welcome to the royal chambers, {interaction.user.display_name}.*{user_squad_text}",
        color=ROYAL_BLUE
    )
    
    # Realm stats
    embed.add_field(
        name="🌟 Realm Overview",
        value=(
            f"🏰 **{total_squads}** Noble Kingdoms\n"
            f"⚔️ **{total_matches}** Epic Battles\n" +
            (f"👑 Leading: **{top_squad['name']}** ({top_squad['points']} pts)" if top_squad else "")
        ),
        inline=False
    )
    
    embed.add_field(
        name="📜 Available Actions",
        value=(
            "Use the buttons below to access all features!\n"
            "🏰 Browse Kingdoms • 🏆 Rankings • 🛡️ My Kingdom\n"
            "🎭 My Profile • ⚙️ Setup Profile • ⚔️ View Rivalry\n"
            "📜 Match History • 🎲 Fun Stats • 🚪 Leave Kingdom"
        ),
        inline=False
    )
    
    embed.set_footer(text="⚜️ May honor guide your path | All features are button-based!")
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="leader_panel", description="👑 Open the leader panel")
async def leader_panel_command(interaction: discord.Interaction):
    """Leader panel - all management features accessible via buttons"""
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Only royal leaders may access this chamber.", ephemeral=True)
        return
    
    squad_role, tag = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You must be sworn to a kingdom.", ephemeral=True)
        return
    
    guest_role_name = GUEST_ROLES.get(squad_role.name)
    guest_role = discord.utils.get(interaction.guild.roles, name=guest_role_name) if guest_role_name else None
    
    view = LeaderPanelView(squad_role, tag, squad_role.name, guest_role)
    
    embed = discord.Embed(
        title=f"👑 Royal Leadership Chamber - {squad_role.name}",
        description="⚜️ *Manage your kingdom with the buttons below*\n\n**All actions are button-based - no typing needed!**",
        color=squad_role.color if squad_role.color != discord.Color.default() else ROYAL_GOLD
    )
    embed.add_field(
        name="🎯 Quick Guide",
        value=(
            "➕/➖ **Manage Members** - Recruit or dismiss warriors\n"
            "⭐/🔄 **Manage Rosters** - Set mains (5 max) & subs (3 max)\n"
            "👑/🎭 **Manage Roles** - Promote leaders & manage guests\n"
            "🖼️ **Set Logo** - Update your kingdom's emblem\n"
            "🏰 **View Kingdom** - See detailed kingdom info"
        ),
        inline=False
    )
    embed.set_footer(text="⚜️ Lead with honor and wisdom | Use buttons below")
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="mod_panel", description="🛡️ Open the moderator panel")
async def mod_panel_command(interaction: discord.Interaction):
    """Moderator panel - all moderation features accessible via buttons"""
    if not is_moderator(interaction.user):
        await interaction.response.send_message("❌ Only royal moderators may access this chamber.", ephemeral=True)
        return
    
    view = ModeratorPanelView()
    
    embed = discord.Embed(
        title="🛡️ Royal Overseer Chamber",
        description="⚜️ *Manage the realm's tournaments and records*\n\n**All actions are button-based!**",
        color=ROYAL_PURPLE
    )
    embed.add_field(
        name="📜 Quick Guide",
        value=(
            "⚔️ **Record Battle** - Add new match results\n"
            "🏆 **Award Title** - Grant championship titles\n"
            "🗑️ **Delete Match** - Remove match results\n"
            "📜 **Recent Matches** - View match history with IDs\n"
            "🗑️ **Clear History** - Clear player squad history\n"
            "💾 **Download Backup** - Save data backup file"
        ),
        inline=False
    )
    embed.set_footer(text="⚜️ Govern with fairness and strength | Use buttons below")
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="profile", description="🎭 View a warrior's profile")
async def profile_command(interaction: discord.Interaction, member: discord.Member):
    """View any warrior's profile - requires @ mention"""
    await show_player_profile(interaction, member, public=True)

@bot.tree.command(name="help", description="📜 View command help")
async def help_command(interaction: discord.Interaction):
    """Help command with selector for different categories"""
    view = HelpCategoryView()
    
    embed = discord.Embed(
        title="📜 Royal Command Archives",
        description="⚜️ *Select a category below to view available commands*\n\n**Almost everything is now button-based!**",
        color=ROYAL_PURPLE
    )
    embed.add_field(
        name="📋 Available Commands",
        value=(
            "`/panel` - Main member panel (button-based)\n"
            "`/leader_panel` - Leader management panel (button-based)\n"
            "`/mod_panel` - Moderator panel (button-based)\n"
            "`/profile @user` - View any warrior's profile\n"
            "`/help` - This help menu"
        ),
        inline=False
    )
    embed.add_field(
        name="💡 How It Works",
        value="Use the selector below to see detailed info for each role!",
        inline=False
    )
    embed.set_footer(text="⚜️ Knowledge is power | All features are button-based!")
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# -------------------- RUN --------------------
bot.run(os.getenv("DISCORD_TOKEN"))
