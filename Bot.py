claude
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
import random

# -------------------- INTENTS --------------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------- CONFIG --------------------
LEADER_ROLE_NAME = "LEADER"
MODERATOR_ROLE_NAME = "MODERATOR"

# CRITICAL: Use persistent volume for data storage
DATA_DIR = os.getenv("DATA_DIR", "/data")
DATA_FILE = os.path.join(DATA_DIR, "squad_data.json")
os.makedirs(DATA_DIR, exist_ok=True)

# Royal color scheme
ROYAL_PURPLE = 0x6a0dad
ROYAL_GOLD = 0xffd700
ROYAL_BLUE = 0x4169e1
ROYAL_RED = 0xdc143c
ROYAL_GREEN = 0x2ecc71

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

# Fun battle quotes
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

SQUAD_MOODS = {
    "fire": {"emoji": "🔥", "status": "ON FIRE", "desc": "Unstoppable momentum!"},
    "rising": {"emoji": "📈", "status": "RISING", "desc": "Building strength!"},
    "steady": {"emoji": "⚖️", "status": "STEADY", "desc": "Maintaining course"},
    "struggling": {"emoji": "😰", "status": "STRUGGLING", "desc": "Needs regrouping"},
    "crisis": {"emoji": "💀", "status": "IN CRISIS", "desc": "Dark times ahead..."}
}

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
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for match in data.get("matches", []):
                if "team1_participants" not in match:
                    match["team1_participants"] = []
                if "team2_participants" not in match:
                    match["team2_participants"] = []
            return data

    data = {"squads": {}, "players": {}, "matches": []}
    for squad_name in SQUADS.keys():
        data["squads"][squad_name] = {
            "wins": 0, "draws": 0, "losses": 0, "points": 0,
            "titles": [], "championship_wins": 0, "logo_url": None,
            "main_roster": [], "subs": [], "match_history": [],
            "current_streak": {"type": "none", "count": 0},
            "achievements": [], "biggest_win_streak": 0, "biggest_loss_streak": 0
        }
    save_data(data)
    return data


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, indent=2, fp=f, ensure_ascii=False)


squad_data = load_data()


# -------------------- LOGGING --------------------
async def log_action(guild: discord.Guild, title: str, description: str):
    if guild is None:
        return
    channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if channel is None:
        return
    embed = discord.Embed(title=title, description=description, color=ROYAL_PURPLE, timestamp=datetime.utcnow())
    embed.set_footer(text="⚜️ Majestic Archives")
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
    player_key = str(player_id)
    if player_key not in squad_data["players"]:
        squad_data["players"][player_key] = {
            "discord_id": player_id, "ingame_name": "", "ingame_id": "",
            "highest_rank": "", "role": "", "squad": new_squad, "squad_history": []
        }
    player_data = squad_data["players"][player_key]
    if old_squad and old_squad != new_squad:
        entry = {"squad": old_squad, "left_date": datetime.utcnow().isoformat()}
        if "squad_history" not in player_data:
            player_data["squad_history"] = []
        player_data["squad_history"].append(entry)
    player_data["squad"] = new_squad
    save_data(squad_data)


def get_squad_ranking():
    rankings = []
    for squad_name, data in squad_data["squads"].items():
        total = data["wins"] + data["draws"] + data["losses"]
        wr = (data["wins"] / total * 100) if total > 0 else 0.0
        rankings.append({
            "name": squad_name, "tag": SQUADS[squad_name], "points": data["points"],
            "wins": data["wins"], "draws": data["draws"], "losses": data["losses"],
            "win_rate": wr, "total_matches": total
        })
    sorted_r = sorted(rankings, key=lambda x: x["points"], reverse=True)
    for i, s in enumerate(sorted_r, 1):
        s["rank"] = i
    return sorted_r


def get_squad_rank(squad_name):
    for s in get_squad_ranking():
        if s["name"] == squad_name:
            return s["rank"]
    return None


def get_player_stats(player_id):
    player_key = str(player_id)
    player_data = squad_data["players"].get(player_key)
    if not player_data:
        return None
    matches_played = wins = losses = draws = 0
    squad_name = player_data.get("squad")
    if squad_name and squad_name != "Free Agent":
        for match in squad_data["matches"]:
            if match["team1"] == squad_name:
                participants = match.get("team1_participants", [])
            elif match["team2"] == squad_name:
                participants = match.get("team2_participants", [])
            else:
                continue
            if not participants or player_id in participants:
                matches_played += 1
                try:
                    s1, s2 = map(int, match["score"].split('-'))
                    if match["team1"] == squad_name:
                        if s1 > s2: wins += 1
                        elif s2 > s1: losses += 1
                        else: draws += 1
                    else:
                        if s2 > s1: wins += 1
                        elif s1 > s2: losses += 1
                        else: draws += 1
                except:
                    pass
    return {"matches_played": matches_played, "wins": wins, "losses": losses, "draws": draws,
            "win_rate": (wins / matches_played * 100) if matches_played > 0 else 0}


def find_match_by_id(match_id):
    for i, match in enumerate(squad_data["matches"]):
        if match.get("match_id") == match_id:
            return i, match
    return None, None


def get_squad_mood(squad_name):
    squad_info = squad_data["squads"].get(squad_name, {})
    recent_matches = squad_info.get("match_history", [])[-5:]
    if len(recent_matches) < 3:
        return SQUAD_MOODS["steady"]
    recent_results = []
    for match in recent_matches:
        try:
            s1, s2 = map(int, match["score"].split('-'))
            if match["team1"] == squad_name:
                recent_results.append("W" if s1 > s2 else "L" if s1 < s2 else "D")
            else:
                recent_results.append("W" if s2 > s1 else "L" if s2 < s1 else "D")
        except:
            pass
    w = recent_results.count("W")
    l = recent_results.count("L")
    if w >= 4: return SQUAD_MOODS["fire"]
    elif w >= 3: return SQUAD_MOODS["rising"]
    elif l >= 4: return SQUAD_MOODS["crisis"]
    elif l >= 3: return SQUAD_MOODS["struggling"]
    return SQUAD_MOODS["steady"]


def update_streak(squad_name, result):
    si = squad_data["squads"][squad_name]
    cs = si.get("current_streak", {"type": "none", "count": 0})
    if cs["type"] == result:
        cs["count"] += 1
    else:
        cs = {"type": result, "count": 1}
    si["current_streak"] = cs
    if result == "win" and cs["count"] > si.get("biggest_win_streak", 0):
        si["biggest_win_streak"] = cs["count"]
    elif result == "loss" and cs["count"] > si.get("biggest_loss_streak", 0):
        si["biggest_loss_streak"] = cs["count"]
    return cs


def check_achievements(squad_name):
    si = squad_data["squads"][squad_name]
    achievements = si.get("achievements", [])
    new_ach = []
    if si["wins"] == 1 and "first_blood" not in achievements:
        achievements.append("first_blood"); new_ach.append(ACHIEVEMENTS["first_blood"])
    if si["points"] >= 100 and "century_club" not in achievements:
        achievements.append("century_club"); new_ach.append(ACHIEVEMENTS["century_club"])
    cs = si.get("current_streak", {})
    if cs.get("type") == "win" and cs.get("count") == 10 and "perfect_10" not in achievements:
        achievements.append("perfect_10"); new_ach.append(ACHIEVEMENTS["perfect_10"])
    if cs.get("type") == "win" and cs.get("count") == 5 and "undefeated_5" not in achievements:
        achievements.append("undefeated_5"); new_ach.append(ACHIEVEMENTS["undefeated_5"])
    total = si["wins"] + si["draws"] + si["losses"]
    if total >= 50 and "warrior_50" not in achievements:
        achievements.append("warrior_50"); new_ach.append(ACHIEVEMENTS["warrior_50"])
    if si.get("championship_wins", 0) >= 1 and "champion" not in achievements:
        achievements.append("champion"); new_ach.append(ACHIEVEMENTS["champion"])
    si["achievements"] = achievements
    return new_ach


def get_head_to_head(sq1, sq2):
    h2h = {"squad1_wins": 0, "squad2_wins": 0, "draws": 0, "total": 0}
    for m in squad_data["matches"]:
        if (m["team1"] == sq1 and m["team2"] == sq2) or (m["team1"] == sq2 and m["team2"] == sq1):
            h2h["total"] += 1
            s1, s2 = map(int, m["score"].split('-'))
            if m["team1"] == sq1:
                if s1 > s2: h2h["squad1_wins"] += 1
                elif s2 > s1: h2h["squad2_wins"] += 1
                else: h2h["draws"] += 1
            else:
                if s2 > s1: h2h["squad1_wins"] += 1
                elif s1 > s2: h2h["squad2_wins"] += 1
                else: h2h["draws"] += 1
    return h2h


def get_match_participants(squad_name):
    si = squad_data["squads"][squad_name]
    mr = si.get("main_roster", [])
    return mr.copy() if len(mr) == 5 else []


def recalculate_streak(squad_name):
    history = squad_data["squads"][squad_name].get("match_history", [])
    if not history:
        return {"type": "none", "count": 0}
    results = []
    for m in history:
        try:
            s1, s2 = map(int, m["score"].split('-'))
            if m["team1"] == squad_name:
                results.append("win" if s1 > s2 else "loss" if s1 < s2 else "draw")
            else:
                results.append("win" if s2 > s1 else "loss" if s2 < s1 else "draw")
        except:
            pass
    if not results:
        return {"type": "none", "count": 0}
    ct = results[-1]
    count = 1
    for i in range(len(results) - 2, -1, -1):
        if results[i] == ct:
            count += 1
        else:
            break
    return {"type": ct, "count": count}


# -------------------- MODALS --------------------
class PlayerSetupModal(Modal, title="⚜️ Majestic Profile Setup"):
    ingame_name = TextInput(label="In-Game Name", placeholder="Enter your IGN", required=False, max_length=50)
    ingame_id = TextInput(label="In-Game ID", placeholder="Enter your game ID", required=False, max_length=50)
    highest_rank = TextInput(label="Highest Rank", placeholder="e.g., Mythic Glory, Legend, etc.", required=False, max_length=50)

    def __init__(self, user_id: int, squad_name: str, role: str, existing_data: dict = None):
        super().__init__()
        self.user_id = user_id
        self.squad_name = squad_name
        self.player_role = role
        if existing_data:
            if existing_data.get("ingame_name"): self.ingame_name.default = existing_data["ingame_name"]
            if existing_data.get("ingame_id"): self.ingame_id.default = existing_data["ingame_id"]
            if existing_data.get("highest_rank"): self.highest_rank.default = existing_data["highest_rank"]

    async def on_submit(self, interaction: discord.Interaction):
        pk = str(self.user_id)
        pd = squad_data["players"].get(pk, {
            "discord_id": self.user_id, "ingame_name": "", "ingame_id": "",
            "highest_rank": "", "role": "", "squad": self.squad_name, "squad_history": []
        })
        if self.ingame_name.value: pd["ingame_name"] = self.ingame_name.value
        if self.ingame_id.value: pd["ingame_id"] = self.ingame_id.value
        if self.highest_rank.value: pd["highest_rank"] = self.highest_rank.value
        pd["role"] = self.player_role
        pd["squad"] = self.squad_name
        squad_data["players"][pk] = pd
        save_data(squad_data)

        embed = discord.Embed(title="✅ Profile Updated!", description="Your majestic warrior profile is now inscribed.", color=ROYAL_GOLD)
        embed.add_field(name="⚔️ IGN", value=pd["ingame_name"] or "Not set", inline=True)
        embed.add_field(name="🎯 ID", value=pd["ingame_id"] or "Not set", inline=True)
        embed.add_field(name="🏆 Rank", value=pd["highest_rank"] or "Not set", inline=True)
        embed.add_field(name="💼 Role", value=f"{ROLE_EMOJIS.get(self.player_role, '⚔️')} {self.player_role}", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(interaction.guild, "⚜️ Profile Updated", f"{interaction.user.mention} updated their warrior profile")


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

class SetLogoModal(Modal, title="🖼️ Set Kingdom Emblem"):
    logo_url = TextInput(label="Emblem URL", placeholder="Paste image URL", required=True, style=discord.TextStyle.long)

    def __init__(self, squad_name: str):
        super().__init__()
        self.squad_name = squad_name

    async def on_submit(self, interaction: discord.Interaction):
        squad_data["squads"][self.squad_name]["logo_url"] = self.logo_url.value
        save_data(squad_data)
        embed = discord.Embed(title="✅ Emblem Set!", description=f"The crest of **{self.squad_name}** has been updated!", color=ROYAL_GOLD)
        embed.set_thumbnail(url=self.logo_url.value)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(interaction.guild, "🖼️ Emblem Updated", f"{interaction.user.mention} updated emblem for **{self.squad_name}**")


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

class DeleteMatchModal(Modal, title="🗑️ Delete Match"):
    match_id = TextInput(label="Match ID", placeholder="Enter match ID", required=True, max_length=8)

    async def on_submit(self, interaction: discord.Interaction):
        idx, match = find_match_by_id(self.match_id.value)
        if match is None:
            await interaction.response.send_message(f"❌ Match `{self.match_id.value}` not found.", ephemeral=True)
            return
        t1, t2, score = match["team1"], match["team2"], match["score"]
        try:
            s1, s2 = map(int, score.split('-'))
        except:
            await interaction.response.send_message("❌ Invalid match data.", ephemeral=True)
            return

        t1d, t2d = squad_data["squads"][t1], squad_data["squads"][t2]
        if s1 > s2: t1d["wins"] -= 1; t1d["points"] -= 2; t2d["losses"] -= 1
        elif s2 > s1: t2d["wins"] -= 1; t2d["points"] -= 2; t1d["losses"] -= 1
        else: t1d["draws"] -= 1; t1d["points"] -= 1; t2d["draws"] -= 1; t2d["points"] -= 1

        squad_data["matches"].pop(idx)
        t1d["match_history"] = [m for m in t1d["match_history"] if m.get("match_id") != self.match_id.value]
        t2d["match_history"] = [m for m in t2d["match_history"] if m.get("match_id") != self.match_id.value]
        t1d["current_streak"] = recalculate_streak(t1)
        t2d["current_streak"] = recalculate_streak(t2)
        save_data(squad_data)

        embed = discord.Embed(title="🗑️ Match Deleted", description=f"**{t1}** vs **{t2}** ({score}) erased.", color=ROYAL_RED)
        embed.add_field(name="Match ID", value=f"`{self.match_id.value}`", inline=True)
        embed.set_footer(text="Points and records adjusted")
        await interaction.response.send_message(embed=embed)
        await log_action(interaction.guild, "🗑️ Match Deleted", f"{interaction.user.mention} deleted {self.match_id.value}: {t1} vs {t2} ({score})")


# -------------------- SQUAD INFO DISPLAY --------------------
async def show_squad_info(interaction, squad_role, squad_name, tag, public=False, edit=False):
    """Display squad info with embedded history button"""
    si = squad_data["squads"].get(squad_name, {})
    rank = get_squad_rank(squad_name)
    re = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "🏅"
    w, d, l = si.get('wins', 0), si.get('draws', 0), si.get('losses', 0)
    total = w + d + l
    wr = (w / total * 100) if total > 0 else 0.0

    embed = discord.Embed(
        title=f"🏰 {squad_name}",
        description=f"⚜️ *A Majestic kingdom of warriors*",
        color=squad_role.color if squad_role else ROYAL_PURPLE
    )
    embed.add_field(name="🏴 Tag", value=f"`{tag}`", inline=True)
    embed.add_field(name="💎 Points", value=f"**{si.get('points', 0)}**", inline=True)
    embed.add_field(name=f"{re} Rank", value=f"**#{rank}**" if rank else "—", inline=True)
    embed.add_field(name="⚔️ Record", value=f"🏆 {w}W • ⚔️ {d}D • 💀 {l}L\n📊 {total} battles | **{wr:.1f}%** WR", inline=False)

    cs = si.get("current_streak", {"type": "none", "count": 0})
    mood = get_squad_mood(squad_name)
    status = f"{mood['emoji']} **{mood['status']}** — {mood['desc']}"
    if cs["count"] >= 2:
        se = "🔥" if cs["type"] == "win" else "❄️" if cs["type"] == "loss" else "⚡"
        status += f"\n{se} **{cs['count']} {cs['type'].upper()} streak**"
    embed.add_field(name="💫 Status", value=status, inline=False)

    achievements = si.get("achievements", [])
    if achievements:
        at = "\n".join(ACHIEVEMENTS[a]["name"] for a in achievements[:5] if a in ACHIEVEMENTS)
        if len(achievements) > 5: at += f"\n*+{len(achievements)-5} more*"
        embed.add_field(name="🏅 Achievements", value=at, inline=False)

    titles = si.get('titles', [])
    cw = si.get('championship_wins', 0)
    if cw > 0 or titles:
        ht = ""
        if cw > 0: ht += f"🏆 {cw} Championship{'s' if cw != 1 else ''}\n"
        if titles: ht += "📜 " + "\n📜 ".join(titles)
        embed.add_field(name="🎖️ Honors", value=ht, inline=False)

    # Main roster
    mr = si.get('main_roster', [])
    if mr:
        rt = ""
        for pid in mr[:5]:
            pd = squad_data["players"].get(str(pid), {})
            mem = interaction.guild.get_member(pid) if interaction.guild else None
            if pd.get('ingame_name'):
                rme = ROLE_EMOJIS.get(pd.get('role', ''), '⚔️')
                dn = mem.display_name if mem else "Unknown"
                rt += f"{rme} **{dn}** — {pd['ingame_name']} (#{pd.get('ingame_id', '?')}) — {pd.get('highest_rank', '?')}\n"
            elif mem:
                rt += f"⚔️ **{mem.display_name}** — *No profile*\n"
            else:
                rt += f"⚔️ *Unknown Warrior*\n"
        if rt: embed.add_field(name=f"⭐ Main Roster ({len(mr)}/5)", value=rt, inline=False)

    subs = si.get('subs', [])
    if subs:
        st = ""
        for pid in subs[:3]:
            pd = squad_data["players"].get(str(pid), {})
            mem = interaction.guild.get_member(pid) if interaction.guild else None
            if pd.get('ingame_name'):
                rme = ROLE_EMOJIS.get(pd.get('role', ''), '⚔️')
                dn = mem.display_name if mem else "Unknown"
                st += f"{rme} **{dn}** — {pd['ingame_name']}\n"
            elif mem:
                st += f"⚔️ **{mem.display_name}** — *No profile*\n"
            else:
                st += f"⚔️ *Unknown Warrior*\n"
        if st: embed.add_field(name=f"🔄 Substitutes ({len(subs)}/3)", value=st, inline=False)

    # If no roster, show all members
    if not mr and not subs and squad_role:
        mt = ""
        for mem in squad_role.members[:15]:
            pd = squad_data["players"].get(str(mem.id), {})
            if pd.get('ingame_name'):
                rme = ROLE_EMOJIS.get(pd.get('role', ''), '⚔️')
                mt += f"{rme} **{mem.display_name}** — {pd['ingame_name']}\n"
            else:
                mt += f"⚔️ **{mem.display_name}**\n"
        if mt:
            embed.add_field(name=f"👥 Members ({len(squad_role.members)})", value=mt, inline=False)

    leaders = get_leaders_for_squad(interaction.guild, squad_role) if squad_role else []
    if leaders:
        embed.add_field(name="👑 Leaders", value=", ".join(leaders), inline=False)

    grn = GUEST_ROLES.get(squad_name)
    if grn:
        gr = discord.utils.get(interaction.guild.roles, name=grn)
        if gr and gr.members:
            embed.add_field(name="🎭 Guests", value=", ".join(m.display_name for m in gr.members[:10]), inline=False)

    if si.get('logo_url'):
        embed.set_thumbnail(url=si['logo_url'])

    embed.set_footer(text="⚜️ Majestic Archives | Use 📜 button for match history")

    view = SquadProfileView(squad_name)

    if edit:
        await interaction.response.edit_message(embed=embed, view=view)
    else:
        await interaction.response.send_message(embed=embed, view=view, ephemeral=not public)


class SquadProfileView(View):
    """Squad profile with history & rivalry buttons"""
    def __init__(self, squad_name):
        super().__init__(timeout=180)
        self.squad_name = squad_name

    @discord.ui.button(label="Match History", emoji="📜", style=discord.ButtonStyle.primary)
    async def history_btn(self, interaction: discord.Interaction, button: Button):
        await show_squad_match_history(interaction, self.squad_name)

    @discord.ui.button(label="View Rivalry", emoji="⚔️", style=discord.ButtonStyle.secondary)
    async def rivalry_btn(self, interaction: discord.Interaction, button: Button):
        view = SquadSelectorView(purpose="rivalry_step2", selected_squad1=self.squad_name)
        embed = discord.Embed(
            title="⚔️ Kingdom Rivalry",
            description=f"✅ First Kingdom: **{SQUADS[self.squad_name]} {self.squad_name}**\n\nSelect the rival kingdom:",
            color=ROYAL_BLUE
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def show_squad_match_history(interaction, squad_name):
    matches = [m for m in squad_data["matches"] if m["team1"] == squad_name or m["team2"] == squad_name]
    if not matches:
        embed = discord.Embed(title=f"📜 {squad_name} — No Battles Yet", description="This kingdom has not entered battle!", color=ROYAL_BLUE)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    recent = matches[-10:][::-1]
    embed = discord.Embed(title=f"📜 {SQUADS[squad_name]} {squad_name} — Battle History", description=f"Last {len(recent)} battles", color=ROYAL_BLUE)
    for m in recent:
        t1, t2, score, mid = m["team1"], m["team2"], m["score"], m.get("match_id", "?")
        try:
            dt = datetime.fromisoformat(m.get("date", ""))
            ds = dt.strftime("%b %d, %Y")
        except:
            ds = "Unknown"
        try:
            s1, s2 = map(int, score.split('-'))
            if t1 == squad_name:
                re, rt = ("🏆", "Victory") if s1 > s2 else ("💀", "Defeat") if s2 > s1 else ("⚖️", "Draw")
            else:
                re, rt = ("🏆", "Victory") if s2 > s1 else ("💀", "Defeat") if s1 > s2 else ("⚖️", "Draw")
        except:
            re, rt = "⚔️", "Battle"
        embed.add_field(name=f"{re} {SQUADS[t1]} vs {SQUADS[t2]} — {rt}", value=f"**{t1}** {score} **{t2}**\n📅 {ds} • 🆔 `{mid}`", inline=False)

    if len(matches) > 10:
        embed.set_footer(text=f"Showing last 10 of {len(matches)} battles")
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def show_player_profile(interaction, member: discord.Member, public=False):
    pk = str(member.id)
    pd = squad_data["players"].get(pk)
    if not pd or not pd.get("ingame_name"):
        embed = discord.Embed(title="⚜️ Profile Not Found", description=f"{member.mention} hasn't set up their profile yet.", color=ROYAL_BLUE)
        embed.add_field(name="💡 How to Create", value="Use `/member` → **Setup Profile** to create yours!", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=not public)
        return

    sn = pd.get("squad")
    sr = None; st = "?"
    if sn and sn in SQUADS:
        st = SQUADS[sn]
        sr = discord.utils.get(interaction.guild.roles, name=sn)

    stats = get_player_stats(member.id)

    rs = "⚔️ Warrior"
    if sn and sn in squad_data["squads"]:
        si = squad_data["squads"][sn]
        if member.id in si.get("main_roster", []):
            rs = "⭐ Main Roster"
        elif member.id in si.get("subs", []):
            rs = "🔄 Substitute"

    embed = discord.Embed(
        title=f"⚜️ {pd.get('ingame_name', 'Unknown')}",
        description=f"{member.mention}'s warrior profile",
        color=sr.color if sr else ROYAL_BLUE
    )
    embed.add_field(name="⚔️ IGN", value=pd.get('ingame_name', '?'), inline=True)
    embed.add_field(name="🎯 ID", value=f"#{pd.get('ingame_id', '?')}", inline=True)
    embed.add_field(name="🏆 Rank", value=pd.get('highest_rank', '?'), inline=True)

    role = pd.get('role', '?')
    embed.add_field(name="💼 Position", value=f"{ROLE_EMOJIS.get(role, '⚔️')} {role}", inline=True)

    if sn and sn != "Free Agent":
        embed.add_field(name="🏰 Kingdom", value=f"{st} **{sn}**\n{rs}", inline=True)
    else:
        embed.add_field(name="🏰 Kingdom", value="Free Agent", inline=True)

    sh = pd.get("squad_history", [])
    if sh:
        ht = "\n".join(f"{SQUADS.get(e.get('squad','?'), '?')} {e.get('squad','?')}" for e in sh[-3:])
        if len(sh) > 3: ht += f"\n*+{len(sh)-3} more*"
        embed.add_field(name="📜 Past Kingdoms", value=ht, inline=False)

    if stats and sn and sn != "Free Agent":
        embed.add_field(
            name="📊 Stats",
            value=f"⚔️ {stats['matches_played']} battles | 🏆 {stats['wins']}W ⚔️ {stats['draws']}D 💀 {stats['losses']}L | **{stats['win_rate']:.1f}%** WR",
            inline=False
        )

    if is_leader(member):
        embed.add_field(name="👑 Status", value="**LEADER**", inline=False)

    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="⚜️ Majestic Archives")
    await interaction.response.send_message(embed=embed, ephemeral=not public)


# -------------------- SQUAD SELECTOR VIEW --------------------
class SquadSelectorView(View):
    """Universal squad selector for browsing, rivalry, etc."""
    def __init__(self, purpose, step=1, selected_squad1=None, page=1):
        super().__init__(timeout=180)
        self.purpose = purpose
        self.step = step
        self.selected_squad1 = selected_squad1
        self.page = page

        all_squads = sorted(SQUADS.items())
        start = (page - 1) * 25
        end = start + 25
        page_squads = all_squads[start:end]

        placeholders = {
            "browse": "🏰 Select a kingdom to explore...",
            "rivalry_step2": "⚔️ Select the rival kingdom...",
        }
        ph = placeholders.get(purpose, "Select a kingdom...")

        options = [discord.SelectOption(label=n, value=n, emoji="🏰", description=f"Tag: {t}") for n, t in page_squads]
        select = Select(placeholder=ph, options=options)
        select.callback = self.selected
        self.add_item(select)

        if len(all_squads) > 25:
            if page > 1:
                b = Button(label="← Prev", style=discord.ButtonStyle.secondary)
                b.callback = self.prev_page
                self.add_item(b)
            if end < len(all_squads):
                b = Button(label="Next →", style=discord.ButtonStyle.secondary)
                b.callback = self.next_page
                self.add_item(b)

    async def prev_page(self, interaction):
        v = SquadSelectorView(self.purpose, self.step, self.selected_squad1, self.page - 1)
        await interaction.response.edit_message(view=v)

    async def next_page(self, interaction):
        v = SquadSelectorView(self.purpose, self.step, self.selected_squad1, self.page + 1)
        await interaction.response.edit_message(view=v)

    async def selected(self, interaction):
        sq = interaction.data["values"][0]
        if self.purpose == "browse":
            sr = discord.utils.get(interaction.guild.roles, name=sq)
            await show_squad_info(interaction, sr, sq, SQUADS.get(sq, "?"), public=True, edit=True)
        elif self.purpose == "rivalry_step2":
            await show_rivalry_stats(interaction, self.selected_squad1, sq)


async def show_rivalry_stats(interaction, sq1, sq2):
    if sq1 == sq2:
        await interaction.response.edit_message(content="❌ A kingdom cannot rival itself!", embed=None, view=None)
        return
    h2h = get_head_to_head(sq1, sq2)
    if h2h["total"] == 0:
        embed = discord.Embed(title="⚔️ No Rivalry Yet", description=f"**{sq1}** and **{sq2}** haven't battled!", color=ROYAL_BLUE)
        try:
            await interaction.response.edit_message(embed=embed, view=None)
        except:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    embed = discord.Embed(title="⚔️ Kingdom Rivalry", description=f"**{SQUADS[sq1]} {sq1}** vs **{SQUADS[sq2]} {sq2}**", color=ROYAL_RED)
    embed.add_field(name="📊 Head-to-Head", value=f"Total: **{h2h['total']}**\n\n🏆 {sq1}: **{h2h['squad1_wins']}**\n🏆 {sq2}: **{h2h['squad2_wins']}**\n🤝 Draws: **{h2h['draws']}**", inline=False)

    if h2h["squad1_wins"] > h2h["squad2_wins"]:
        dom = sq1; dw = h2h["squad1_wins"]
    elif h2h["squad2_wins"] > h2h["squad1_wins"]:
        dom = sq2; dw = h2h["squad2_wins"]
    else:
        dom = None

    if dom:
        embed.add_field(name="👑 Dominant", value=f"**{dom}** leads with **{(dw/h2h['total'])*100:.0f}%** dominance", inline=False)
    else:
        embed.add_field(name="⚖️ Balanced", value="Both kingdoms are perfectly matched!", inline=False)

    try:
        await interaction.response.edit_message(embed=embed, view=None)
    except:
        await interaction.response.send_message(embed=embed, ephemeral=True)


# -------------------- MEMBER SELECTOR VIEW --------------------
class MemberSelectorView(View):
    """Selector for add/remove/mains/subs actions (NOT for profile viewing)"""
    def __init__(self, action, squad_role=None, squad_name=None, guild=None, page=1):
        super().__init__(timeout=180)
        self.action = action
        self.squad_role = squad_role
        self.squad_name = squad_name
        self.guild = guild
        self.page = page

        if action in ["remove_member", "remove_guest", "set_main", "remove_main", "set_sub", "remove_sub", "promote_leader"]:
            members = squad_role.members if squad_role else []
        elif action == "clear_history":
            members = [m for m in guild.members if not m.bot and str(m.id) in squad_data["players"]]
        else:
            members = []

        start = (page - 1) * 25
        end = start + 25
        pm = members[start:end]
        if not pm: return

        labels = {
            "add_member": "⚔️ Select warrior to recruit...",
            "remove_member": "Select warrior to remove...",
            "set_main": "⭐ Select for main roster...",
            "remove_main": "Remove from main roster...",
            "set_sub": "🔄 Select for substitutes...",
            "remove_sub": "Remove from substitutes...",
            "promote_leader": "👑 Select to promote...",
            "give_guest": "🎭 Select for guest role...",
            "remove_guest": "Remove guest role...",
            "clear_history": "Select player to clear history..."
        }

        options = [discord.SelectOption(label=m.display_name[:100], value=str(m.id), description=f"@{m.name[:50]}") for m in pm]
        select = Select(placeholder=labels.get(action, "Select..."), options=options)
        select.callback = self.member_selected
        self.add_item(select)

        if len(members) > 25:
            if page > 1:
                b = Button(label="← Prev", style=discord.ButtonStyle.secondary)
                b.callback = self.prev_page
                self.add_item(b)
            if end < len(members):
                b = Button(label="Next →", style=discord.ButtonStyle.secondary)
                b.callback = self.next_page
                self.add_item(b)

    async def prev_page(self, i):
        await i.response.edit_message(view=MemberSelectorView(self.action, self.squad_role, self.squad_name, self.guild, self.page-1))

    async def next_page(self, i):
        await i.response.edit_message(view=MemberSelectorView(self.action, self.squad_role, self.squad_name, self.guild, self.page+1))

    async def member_selected(self, interaction):
        mid = int(interaction.data["values"][0])
        member = self.guild.get_member(mid)
        if not member:
            await interaction.response.edit_message(content="❌ Member not found!", embed=None, view=None)
            return

        handlers = {
            "add_member": self.h_add, "remove_member": self.h_remove,
            "set_main": self.h_set_main, "remove_main": self.h_rm_main,
            "set_sub": self.h_set_sub, "remove_sub": self.h_rm_sub,
            "promote_leader": self.h_promote, "give_guest": self.h_give_guest,
            "remove_guest": self.h_rm_guest, "clear_history": self.h_clear
        }
        await handlers[self.action](interaction, member)

    async def h_add(self, interaction, member):
        old_sr, _ = get_member_squad(member, self.guild)
        old_name = old_sr.name if old_sr else None
        for rn in SQUADS:
            r = discord.utils.get(self.guild.roles, name=rn)
            if r and r in member.roles: await member.remove_roles(r)
        await member.add_roles(self.squad_role)
        await safe_nick_update(member, self.squad_role, SQUADS.get(self.squad_name, ""))
        update_player_squad(member.id, self.squad_name, old_name)
        embed = discord.Embed(title="✅ Recruited!", description=f"{member.mention} joined **{self.squad_name}**!", color=ROYAL_GOLD)
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "➕ Recruited", f"{interaction.user.mention} recruited {member.mention} to **{self.squad_name}**")

    async def h_remove(self, interaction, member):
        si = squad_data["squads"][self.squad_name]
        if member.id in si.get("main_roster", []): si["main_roster"].remove(member.id)
        if member.id in si.get("subs", []): si["subs"].remove(member.id)
        await member.remove_roles(self.squad_role)
        await safe_nick_update(member, None, "")
        update_player_squad(member.id, "Free Agent", self.squad_name)
        save_data(squad_data)
        embed = discord.Embed(title="✅ Removed", description=f"{member.mention} removed from **{self.squad_name}**", color=ROYAL_PURPLE)
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "➖ Removed", f"{interaction.user.mention} removed {member.mention} from **{self.squad_name}**")

    async def h_set_main(self, interaction, member):
        si = squad_data["squads"][self.squad_name]
        mr = si.get("main_roster", [])
        if len(mr) >= 5: await interaction.response.edit_message(content="❌ Main roster full (5 max)!", embed=None, view=None); return
        if member.id in mr: await interaction.response.edit_message(content="❌ Already on main roster!", embed=None, view=None); return
        if member.id in si.get("subs", []): si["subs"].remove(member.id)
        mr.append(member.id); save_data(squad_data)
        embed = discord.Embed(title="⭐ Main Roster Updated!", description=f"{member.mention} → Main Roster ({len(mr)}/5)", color=ROYAL_GOLD)
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "⭐ Main Set", f"{member.mention} added to main roster")

    async def h_rm_main(self, interaction, member):
        si = squad_data["squads"][self.squad_name]
        mr = si.get("main_roster", [])
        if member.id not in mr: await interaction.response.edit_message(content="❌ Not on main roster!", embed=None, view=None); return
        mr.remove(member.id); save_data(squad_data)
        embed = discord.Embed(title="✅ Removed from Mains", description=f"{member.mention} removed from main roster", color=ROYAL_PURPLE)
        await interaction.response.edit_message(embed=embed, view=None)

    async def h_set_sub(self, interaction, member):
        si = squad_data["squads"][self.squad_name]
        subs = si.get("subs", [])
        if len(subs) >= 3: await interaction.response.edit_message(content="❌ Subs full (3 max)!", embed=None, view=None); return
        if member.id in subs: await interaction.response.edit_message(content="❌ Already a sub!", embed=None, view=None); return
        if member.id in si.get("main_roster", []): si["main_roster"].remove(member.id)
        subs.append(member.id); save_data(squad_data)
        embed = discord.Embed(title="🔄 Sub Added!", description=f"{member.mention} → Substitutes ({len(subs)}/3)", color=ROYAL_BLUE)
        await interaction.response.edit_message(embed=embed, view=None)

    async def h_rm_sub(self, interaction, member):
        si = squad_data["squads"][self.squad_name]
        subs = si.get("subs", [])
        if member.id not in subs: await interaction.response.edit_message(content="❌ Not a substitute!", embed=None, view=None); return
        subs.remove(member.id); save_data(squad_data)
        embed = discord.Embed(title="✅ Removed from Subs", description=f"{member.mention} removed from substitutes", color=ROYAL_PURPLE)
        await interaction.response.edit_message(embed=embed, view=None)

    async def h_promote(self, interaction, member):
        lr = discord.utils.get(self.guild.roles, name=LEADER_ROLE_NAME)
        if not lr: await interaction.response.edit_message(content="❌ Leader role not found!", embed=None, view=None); return
        await member.add_roles(lr)
        embed = discord.Embed(title="👑 Leader Promoted!", description=f"{member.mention} is now a **Leader** of **{self.squad_name}**!", color=ROYAL_GOLD)
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "👑 Promoted", f"{member.mention} → Leader of {self.squad_name}")

    async def h_give_guest(self, interaction, member):
        grn = GUEST_ROLES.get(self.squad_name)
        if not grn: await interaction.response.edit_message(content="❌ No guest role configured!", embed=None, view=None); return
        gr = discord.utils.get(self.guild.roles, name=grn)
        if not gr: await interaction.response.edit_message(content=f"❌ Role '{grn}' not found!", embed=None, view=None); return
        await member.add_roles(gr)
        embed = discord.Embed(title="🎭 Guest Added!", description=f"{member.mention} → Guest of **{self.squad_name}**", color=ROYAL_BLUE)
        await interaction.response.edit_message(embed=embed, view=None)

    async def h_rm_guest(self, interaction, member):
        grn = GUEST_ROLES.get(self.squad_name)
        if not grn: await interaction.response.edit_message(content="❌ No guest role!", embed=None, view=None); return
        gr = discord.utils.get(self.guild.roles, name=grn)
        if not gr or gr not in member.roles: await interaction.response.edit_message(content="❌ No guest role on member!", embed=None, view=None); return
        await member.remove_roles(gr)
        embed = discord.Embed(title="✅ Guest Removed", description=f"{member.mention}'s guest access revoked", color=ROYAL_PURPLE)
        await interaction.response.edit_message(embed=embed, view=None)

    async def h_clear(self, interaction, member):
        pk = str(member.id)
        if pk not in squad_data["players"]:
            await interaction.response.edit_message(content="❌ No profile found.", embed=None, view=None); return
        pd = squad_data["players"][pk]
        old_h = pd.get("squad_history", [])
        if not old_h:
            await interaction.response.edit_message(content="ℹ️ No history to clear.", embed=None, view=None); return
        pd["squad_history"] = []
        save_data(squad_data)
        embed = discord.Embed(title="🗑️ History Cleared", description=f"Cleared **{len(old_h)}** entries for {member.mention}", color=ROYAL_PURPLE)
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "🗑️ History Cleared", f"{interaction.user.mention} cleared history for {member.mention}")


# =====================================================================
#                     PANEL VIEWS — THE 3 MAIN CATEGORIES
# =====================================================================

# -------------------- 1. MAJESTIC MEMBER PANEL --------------------
class MemberPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Browse Kingdoms", style=discord.ButtonStyle.primary, emoji="🏰", row=0)
    async def browse_btn(self, interaction: discord.Interaction, button: Button):
        view = SquadSelectorView(purpose="browse")
        embed = discord.Embed(title="🏰 Kingdom Explorer", description="Select a kingdom to explore!", color=ROYAL_BLUE)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Rankings", style=discord.ButtonStyle.secondary, emoji="🏆", row=0)
    async def rankings_btn(self, interaction: discord.Interaction, button: Button):
        rankings = get_squad_ranking()
        tp = (len(rankings) + 14) // 15
        embed = discord.Embed(title="🏆 Leaderboard", description=f"Page 1/{tp}", color=ROYAL_GOLD)
        for s in rankings[:15]:
            i = s["rank"]
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            embed.add_field(name=f"{medal} {s['tag']} {s['name']}", value=f"💎 **{s['points']}** pts | {s['wins']}W-{s['draws']}D-{s['losses']}L | **{s['win_rate']:.1f}%** WR", inline=False)
        embed.set_footer(text=f"All {len(rankings)} kingdoms")
        view = RankingsView(page=1) if tp > 1 else None
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="View Profile", emoji="👤", style=discord.ButtonStyle.primary)
async def view_profile(self, interaction: discord.Interaction, button: discord.ui.Button):

    await interaction.response.send_message(
        "Reply and **mention the member** whose profile you want to view.",
        ephemeral=True
    )

    def check(m):
        return (
            m.author.id == interaction.user.id
            and m.reference
            and m.reference.message_id == interaction.message.id
            and len(m.mentions) == 1
        )

    try:
        msg = await bot.wait_for("message", timeout=60, check=check)
    except asyncio.TimeoutError:
        return

    member = msg.mentions[0]
    await msg.delete()

    await send_profile(interaction, member)

    @discord.ui.button(label="My Kingdom", style=discord.ButtonStyle.success, emoji="🛡️", row=0)
    async def my_squad_btn(self, interaction: discord.Interaction, button: Button):
        role, tag = get_member_squad(interaction.user, interaction.guild)
        if not role:
            await interaction.response.send_message("❌ You're not in any kingdom.", ephemeral=True)
            return
        await show_squad_info(interaction, role, role.name, tag, public=False)

    @discord.ui.button(label="My Profile", style=discord.ButtonStyle.success, emoji="⚜️", row=1)
    async def my_profile_btn(self, interaction: discord.Interaction, button: Button):
        await show_player_profile(interaction, interaction.user, public=False)

    @discord.ui.button(label="Setup Profile", style=discord.ButtonStyle.primary, emoji="⚙️", row=1)
    async def setup_btn(self, interaction: discord.Interaction, button: Button):
        role, _ = get_member_squad(interaction.user, interaction.guild)
        sn = role.name if role else "Free Agent"
        view = RoleSelectView(interaction.user.id, sn)
        embed = discord.Embed(title="⚙️ Profile Setup", description="Choose your battle position first:", color=ROYAL_PURPLE)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Fun Stats", style=discord.ButtonStyle.secondary, emoji="🎲", row=1)
    async def fun_btn(self, interaction: discord.Interaction, button: Button):
        await show_fun_stats(interaction)

    @discord.ui.button(label="Leave Kingdom", style=discord.ButtonStyle.danger, emoji="🚪", row=2)
    async def leave_btn(self, interaction: discord.Interaction, button: Button):
        role, _ = get_member_squad(interaction.user, interaction.guild)
        if not role:
            await interaction.response.send_message("❌ You're not in any kingdom.", ephemeral=True)
            return
        cv = View(timeout=60)
        async def confirm(ci):
            if ci.user.id != interaction.user.id: return await ci.response.send_message("❌ Not yours.", ephemeral=True)
            update_player_squad(interaction.user.id, None, role.name)
            await interaction.user.remove_roles(role)
            await safe_nick_update(interaction.user, None, None)
            await ci.response.send_message(f"🚪 You left **{role.name}**. Your profile is preserved.", ephemeral=True)
            await log_action(interaction.guild, "🚪 Left Kingdom", f"{interaction.user.mention} left **{role.name}**")
        async def cancel(ci):
            if ci.user.id != interaction.user.id: return await ci.response.send_message("❌ Not yours.", ephemeral=True)
            await ci.response.send_message("✅ Cancelled.", ephemeral=True)
        cb = Button(label="✓ Confirm", style=discord.ButtonStyle.danger); cb.callback = confirm
        xb = Button(label="✗ Cancel", style=discord.ButtonStyle.secondary); xb.callback = cancel
        cv.add_item(cb); cv.add_item(xb)
        await interaction.response.send_message(f"⚠️ Leave **{role.name}**? Your profile will be preserved.", view=cv, ephemeral=True)


class RoleSelectView(View):
    def __init__(self, user_id, squad_name):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.squad_name = squad_name
        options = [discord.SelectOption(label=r, emoji=ROLE_EMOJIS.get(r, "⚔️"), description=f"Play as {r}") for r in ROLES]
        select = Select(placeholder="⚔️ Choose your position...", options=options)
        select.callback = self.role_selected
        self.add_item(select)

    async def role_selected(self, interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Not your setup.", ephemeral=True)
        role = interaction.data["values"][0]
        existing = squad_data["players"].get(str(self.user_id), {})
        await interaction.response.send_modal(PlayerSetupModal(self.user_id, self.squad_name, role, existing))


class RankingsView(View):
    def __init__(self, page=1):
        super().__init__(timeout=180)
        self.page = page
        rankings = get_squad_ranking()
        tp = (len(rankings) + 14) // 15
        if page > 1:
            b = Button(label="← Prev", style=discord.ButtonStyle.secondary, emoji="⬅️"); b.callback = self.prev; self.add_item(b)
        if page < tp:
            b = Button(label="Next →", style=discord.ButtonStyle.secondary, emoji="➡️"); b.callback = self.nxt; self.add_item(b)

    async def prev(self, i): await self.show(i, self.page - 1)
    async def nxt(self, i): await self.show(i, self.page + 1)

    async def show(self, interaction, page):
        rankings = get_squad_ranking()
        tp = (len(rankings) + 14) // 15
        start = (page - 1) * 15
        ps = rankings[start:start+15]
        embed = discord.Embed(title="🏆 Leaderboard", description=f"Page {page}/{tp}", color=ROYAL_GOLD)
        for s in ps:
            i = s["rank"]
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            embed.add_field(name=f"{medal} {s['tag']} {s['name']}", value=f"💎 **{s['points']}** pts | {s['wins']}W-{s['draws']}D-{s['losses']}L | **{s['win_rate']:.1f}%** WR", inline=False)
        await interaction.response.edit_message(embed=embed, view=RankingsView(page=page))


# -------------------- 2. MAJESTIC LEADER PANEL --------------------
class LeaderPanelView(View):
    def __init__(self, squad_role, tag, squad_name, guest_role):
        super().__init__(timeout=None)
        self.squad_role = squad_role
        self.tag = tag
        self.squad_name = squad_name
        self.guest_role = guest_role

    @discord.ui.button(label="Add Member", emoji="➕", style=discord.ButtonStyle.success)
async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):

    await interaction.response.send_message(
        "Reply to this message and **mention the member** you want to add.",
        ephemeral=True
    )

    def check(m):
        return (
            m.author.id == interaction.user.id
            and m.reference
            and m.reference.message_id == interaction.message.id
            and len(m.mentions) == 1
        )

    try:
        msg = await bot.wait_for("message", timeout=60, check=check)
    except asyncio.TimeoutError:
        return

    member = msg.mentions[0]
    guild = interaction.guild

    # Remove any old squad role
    for squad_name in SQUADS:
        role = discord.utils.get(guild.roles, name=squad_name)
        if role and role in member.roles:
            await member.remove_roles(role)

    # Give ONLY the squad role (not leader)
    await member.add_roles(self.squad_role)

    await safe_nick_update(member, self.squad_role, SQUADS[self.squad_name])

    old_role, _ = get_member_squad(member, guild)
    update_player_squad(
        member.id,
        self.squad_name,
        old_role.name if old_role else None
    )

    await msg.delete()

    await interaction.edit_original_response(
        content=f"✅ {member.mention} added to **{self.squad_name}**."
    )


    @discord.ui.button(label="Remove Member", emoji="➖", style=discord.ButtonStyle.danger, row=0)
    async def rm_btn(self, interaction: discord.Interaction, button: Button):
        v = MemberSelectorView("remove_member", self.squad_role, self.squad_name, interaction.guild)
        e = discord.Embed(title="➖ Remove Warrior", description="Select a member to remove:", color=ROYAL_RED)
        await interaction.response.send_message(embed=e, view=v, ephemeral=True)

    @discord.ui.button(label="View Kingdom", emoji="🏰", style=discord.ButtonStyle.primary, row=0)
    async def view_btn(self, interaction: discord.Interaction, button: Button):
        await show_squad_info(interaction, self.squad_role, self.squad_name, self.tag, public=False)

    @discord.ui.button(label="Set Main", emoji="⭐", style=discord.ButtonStyle.primary, row=1)
    async def main_btn(self, interaction: discord.Interaction, button: Button):
        v = MemberSelectorView("set_main", self.squad_role, self.squad_name, interaction.guild)
        e = discord.Embed(title="⭐ Set Main Roster", description="Select a member (max 5):", color=ROYAL_GOLD)
        await interaction.response.send_message(embed=e, view=v, ephemeral=True)

    @discord.ui.button(label="Remove Main", emoji="❌", style=discord.ButtonStyle.secondary, row=1)
    async def rm_main_btn(self, interaction: discord.Interaction, button: Button):
        v = MemberSelectorView("remove_main", self.squad_role, self.squad_name, interaction.guild)
        e = discord.Embed(title="❌ Remove from Mains", description="Select to remove:", color=ROYAL_PURPLE)
        await interaction.response.send_message(embed=e, view=v, ephemeral=True)

    @discord.ui.button(label="Set Sub", emoji="🔄", style=discord.ButtonStyle.primary, row=2)
    async def sub_btn(self, interaction: discord.Interaction, button: Button):
        v = MemberSelectorView("set_sub", self.squad_role, self.squad_name, interaction.guild)
        e = discord.Embed(title="🔄 Set Substitute", description="Select a member (max 3):", color=ROYAL_BLUE)
        await interaction.response.send_message(embed=e, view=v, ephemeral=True)

    @discord.ui.button(label="Remove Sub", emoji="❌", style=discord.ButtonStyle.secondary, row=2)
    async def rm_sub_btn(self, interaction: discord.Interaction, button: Button):
        v = MemberSelectorView("remove_sub", self.squad_role, self.squad_name, interaction.guild)
        e = discord.Embed(title="❌ Remove from Subs", description="Select to remove:", color=ROYAL_PURPLE)
        await interaction.response.send_message(embed=e, view=v, ephemeral=True)

    @discord.ui.button(label="Promote Leader", emoji="👑", style=discord.ButtonStyle.primary, row=3)
    async def promote_btn(self, interaction: discord.Interaction, button: Button):
        v = MemberSelectorView("promote_leader", self.squad_role, self.squad_name, interaction.guild)
        e = discord.Embed(title="👑 Promote Leader", description="Select a member:", color=ROYAL_GOLD)
        await interaction.response.send_message(embed=e, view=v, ephemeral=True)

    @discord.ui.button(label="give_guest", emoji="➕", style=discord.ButtonStyle.success)
async def add_member(self, interaction: discord.Interaction, button: discord.ui.Button):

    await interaction.response.send_message(
        "Reply to this message and **mention the member** you want to add.",
        ephemeral=True
    )

    def check(m):
        return (
            m.author.id == interaction.user.id
            and m.reference
            and m.reference.message_id == interaction.message.id
            and len(m.mentions) == 1
        )

    try:
        msg = await bot.wait_for("message", timeout=60, check=check)
    except asyncio.TimeoutError:
        return

    member = msg.mentions[0]
    guild = interaction.guild


    # Give ONLY the squad role (not leader)
    await member.add_roles(GUEST_ROLE)

    await safe_nick_update(member, self.squad_role, SQUADS[self.squad_name])

    old_role, _ = get_member_squad(member, guild)
    update_player_squad(
        member.id,
        self.squad_name,
        old_role.name if old_role else None
    )

    await msg.delete()

    await interaction.edit_original_response(
        content=f"✅ {member.mention} is now a **{self.squad_name}** guest."
    )


    @discord.ui.button(label="Remove Guest", emoji="❌", style=discord.ButtonStyle.secondary, row=3)
    async def rm_guest_btn(self, interaction: discord.Interaction, button: Button):
        v = MemberSelectorView("remove_guest", self.squad_role, self.squad_name, interaction.guild)
        e = discord.Embed(title="❌ Revoke Guest", description="Select to remove:", color=ROYAL_PURPLE)
        await interaction.response.send_message(embed=e, view=v, ephemeral=True)

    @discord.ui.button(label="Set Logo", emoji="🖼️", style=discord.ButtonStyle.primary, row=4)
    async def logo_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SetLogoModal(self.squad_name))


# -------------------- 3. MODERATOR PANEL (Separate, Mod-only) --------------------
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
    async def del_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(DeleteMatchModal())

    @discord.ui.button(label="Recent Matches", style=discord.ButtonStyle.secondary, emoji="📜", row=1)
    async def recent_btn(self, interaction: discord.Interaction, button: Button):
        await show_recent_matches(interaction, limit=10)

    @discord.ui.button(label="Clear History", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
    async def clear_btn(self, interaction: discord.Interaction, button: Button):
        v = MemberSelectorView("clear_history", guild=interaction.guild)
        e = discord.Embed(title="🗑️ Clear Squad History", description="Select a player:", color=ROYAL_RED)
        await interaction.response.send_message(embed=e, view=v, ephemeral=True)

    @discord.ui.button(label="Download Backup", style=discord.ButtonStyle.secondary, emoji="💾", row=2)
    async def backup_btn(self, interaction: discord.Interaction, button: Button):
        if not os.path.exists(DATA_FILE):
            await interaction.response.send_message("❌ No data file found.", ephemeral=True)
            return
        try:
            await interaction.response.send_message(
                "💾 **Data Backup**",
                file=discord.File(DATA_FILE, filename=f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"),
                ephemeral=True
            )
            await log_action(interaction.guild, "💾 Backup", f"{interaction.user.mention} downloaded backup")
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)


async def show_recent_matches(interaction, limit=10):
    recent = squad_data["matches"][-limit:][::-1]
    if not recent:
        await interaction.response.send_message("📜 No matches recorded yet.", ephemeral=True)
        return
    embed = discord.Embed(title="📜 Recent Battles", description=f"Last {len(recent)} matches", color=ROYAL_PURPLE)
    for m in recent:
        mid, t1, t2, score = m.get("match_id", "?"), m["team1"], m["team2"], m["score"]
        try:
            ds = datetime.fromisoformat(m.get("date", "")).strftime("%b %d, %Y %H:%M")
        except:
            ds = "?"
        embed.add_field(name=f"⚔️ {SQUADS.get(t1, '?')} vs {SQUADS.get(t2, '?')}", value=f"**{t1}** {score} **{t2}**\n🆔 `{mid}` • 📅 {ds}", inline=False)
    embed.set_footer(text="Use Delete Match to remove entries")
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def show_fun_stats(interaction):
    tm = len(squad_data["matches"])
    tp = sum(s["points"] for s in squad_data["squads"].values())
    tw = sum(s["wins"] for s in squad_data["squads"].values())
    td = sum(s["draws"] for s in squad_data["squads"].values())

    lws_name, lws = None, 0
    mas_name, mas_count = None, 0
    mach_name, mach_count = None, 0

    for sn, d in squad_data["squads"].items():
        if d.get("biggest_win_streak", 0) > lws: lws = d["biggest_win_streak"]; lws_name = sn
        mc = d["wins"] + d["draws"] + d["losses"]
        if mc > mas_count: mas_count = mc; mas_name = sn
        ac = len(d.get("achievements", []))
        if ac > mach_count: mach_count = ac; mach_name = sn

    rankings = get_squad_ranking()[:3]

    embed = discord.Embed(title="🎲 Realm Statistics", description="Fun facts from the chronicles!", color=ROYAL_GOLD)
    embed.add_field(name="📊 Global", value=f"⚔️ {tm} battles | 💎 {tp} points | 🏆 {tw} victories | 🤝 {td} draws", inline=False)
    if lws_name and lws > 0:
        embed.add_field(name="🔥 Best Win Streak", value=f"**{lws_name}** — {lws} in a row!", inline=False)
    if mas_name and mas_count > 0:
        embed.add_field(name="⚔️ Most Active", value=f"**{mas_name}** — {mas_count} battles", inline=False)
    if rankings:
        podium = "\n".join(f"{'🥇🥈🥉'[i]} **{s['name']}** ({s['points']} pts)" for i, s in enumerate(rankings))
        embed.add_field(name="👑 Top 3", value=podium, inline=False)

    facts = [
        f"🏰 **{len(SQUADS)}** kingdoms compete for glory!",
        f"💎 Average points: **{tp // len(SQUADS)}** per kingdom",
        f"⚔️ **{(td/tm*100):.0f}%** of battles end in draws!" if tm > 0 else "⚔️ First battles await!",
    ]
    embed.add_field(name="💡 Did You Know?", value=random.choice(facts), inline=False)
    embed.set_footer(text="⚜️ History is written by the victorious!")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# -------------------- MAJESTIC HELP VIEW --------------------
class HelpView(View):
    def __init__(self):
        super().__init__(timeout=180)
        options = [
            discord.SelectOption(label="Majestic Member", value="member", emoji="👥", description="Commands for all warriors"),
            discord.SelectOption(label="Majestic Leader", value="leader", emoji="👑", description="Commands for squad leaders"),
            discord.SelectOption(label="Majestic Help", value="help", emoji="📜", description="General help & tips"),
        ]
        select = Select(placeholder="📜 Choose a category...", options=options)
        select.callback = self.cat_selected
        self.add_item(select)

    async def cat_selected(self, interaction):
        cat = interaction.data["values"][0]
        if cat == "member":
            embed = discord.Embed(title="👥 Majestic Member", description="Everything accessible from `/member`", color=ROYAL_BLUE)
            embed.add_field(name="🏰 Browse Kingdoms", value="Explore any kingdom's profile, roster, and match history", inline=False)
            embed.add_field(name="🏆 Rankings", value="View the full leaderboard with points and win rates", inline=False)
            embed.add_field(name="🛡️ My Kingdom", value="View your own kingdom's detailed profile", inline=False)
            embed.add_field(name="⚜️ My Profile", value="See your warrior profile and stats", inline=False)
            embed.add_field(name="⚙️ Setup Profile", value="Create or update your IGN, ID, rank, and role", inline=False)
            embed.add_field(name="🎲 Fun Stats", value="Interesting realm-wide statistics and trivia", inline=False)
            embed.add_field(name="🚪 Leave Kingdom", value="Leave your current kingdom (profile preserved)", inline=False)
            embed.add_field(name="\n📌 Profile Viewing", value="Use `/profile @user` to view anyone's profile publicly!", inline=False)
        elif cat == "leader":
            embed = discord.Embed(title="👑 Majestic Leader", description="Everything accessible from `/leader`", color=ROYAL_GOLD)
            embed.add_field(name="➕ Add Member", value="Recruit free agents to your kingdom", inline=True)
            embed.add_field(name="➖ Remove Member", value="Dismiss warriors from your kingdom", inline=True)
            embed.add_field(name="⭐ Set Main (5 max)", value="Designate main roster players", inline=True)
            embed.add_field(name="🔄 Set Sub (3 max)", value="Designate substitute players", inline=True)
            embed.add_field(name="👑 Promote Leader", value="Grant leadership to a member", inline=True)
            embed.add_field(name="🎭 Guest Access", value="Grant or revoke guest roles", inline=True)
            embed.add_field(name="🖼️ Set Logo", value="Update your kingdom's emblem", inline=True)
            embed.add_field(name="🏰 View Kingdom", value="See your kingdom's full profile", inline=True)
        else:  # help
            embed = discord.Embed(title="📜 Majestic Help", description="Quick guide to all commands", color=ROYAL_PURPLE)
            embed.add_field(name="🎯 Slash Commands", value=(
                "`/member` — Main member panel (all features)\n"
                "`/leader` — Leader management panel\n"
                "`/profile @user` — View anyone's profile\n"
                "`/help` — This help menu"
            ), inline=False)
            embed.add_field(name="💡 Tips", value=(
                "• **Profiles use @mentions** — tag someone to view their profile\n"
                "• **Squad history** lives inside each kingdom's profile (📜 button)\n"
                "• **Rivalries** can be checked from any kingdom's profile (⚔️ button)\n"
                "• Everything is button-based — minimal typing needed!\n"
                "• Moderator panel (`/mod`) is separate and private"
            ), inline=False)

        embed.set_footer(text="⚜️ Majestic Bot — May glory guide your path!")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# =====================================================================
#                     SLASH COMMANDS (Clean & Minimal)
# =====================================================================

@bot.tree.command(name="member", description="⚜️ Open the Majestic Member panel")
async def member_command(interaction: discord.Interaction):
    view = MemberPanelView()
    ur, ut = get_member_squad(interaction.user, interaction.guild)
    sq_text = f"\n🛡️ **Your Kingdom:** {ut} {ur.name}" if ur else "\n⚔️ **Status:** Free Agent"

    rankings = get_squad_ranking()
    top = rankings[0] if rankings else None
    tm = len(squad_data["matches"])

    embed = discord.Embed(
        title="⚜️ Majestic Member Hall",
        description=f"Welcome, **{interaction.user.display_name}**!{sq_text}",
        color=ROYAL_BLUE
    )
    embed.add_field(name="🌟 Realm", value=f"🏰 {len(SQUADS)} kingdoms • ⚔️ {tm} battles" + (f" • 👑 {top['name']} leads" if top else ""), inline=False)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text="⚜️ Use the buttons below!")
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="leader", description="👑 Open the Majestic Leader panel")
async def leader_command(interaction: discord.Interaction):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Only **Leaders** can access this.", ephemeral=True)
        return
    sr, tag = get_member_squad(interaction.user, interaction.guild)
    if not sr:
        await interaction.response.send_message("❌ You must be in a kingdom.", ephemeral=True)
        return
    grn = GUEST_ROLES.get(sr.name)
    gr = discord.utils.get(interaction.guild.roles, name=grn) if grn else None

    view = LeaderPanelView(sr, tag, sr.name, gr)
    si = squad_data["squads"].get(sr.name, {})
    mr_count = len(si.get("main_roster", []))
    sub_count = len(si.get("subs", []))

    embed = discord.Embed(
        title=f"👑 {sr.name} — Leader Chamber",
        description=f"Manage your kingdom, **{interaction.user.display_name}**!",
        color=sr.color if sr.color != discord.Color.default() else ROYAL_GOLD
    )
    embed.add_field(name="📊 Quick Status", value=f"👥 {len(sr.members)} members • ⭐ {mr_count}/5 mains • 🔄 {sub_count}/3 subs", inline=False)
    embed.set_footer(text="⚜️ Lead with honor! | All actions via buttons below")
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="mod", description="🛡️ Open the Moderator panel")
async def mod_command(interaction: discord.Interaction):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("❌ Only **Moderators** can access this.", ephemeral=True)
        return
    view = ModeratorPanelView()
    embed = discord.Embed(
        title="🛡️ Moderator Chamber",
        description="Manage tournaments, matches, and records.",
        color=ROYAL_PURPLE
    )
    embed.add_field(name="📊 Stats", value=f"⚔️ {len(squad_data['matches'])} matches recorded • 🏰 {len(SQUADS)} kingdoms", inline=False)
    embed.set_footer(text="⚜️ Govern with fairness!")
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="profile", description="⚜️ View a warrior's profile")
@app_commands.describe(member="Tag the warrior to view")
async def profile_command(interaction: discord.Interaction, member: discord.Member):
    await show_player_profile(interaction, member, public=True)


@bot.tree.command(name="help", description="📜 Majestic Help — command guide")
async def help_command(interaction: discord.Interaction):
    view = HelpView()
    embed = discord.Embed(
        title="📜 Majestic Help",
        description="Select a category below to learn more!",
        color=ROYAL_PURPLE
    )
    embed.add_field(name="🎯 Commands", value=(
        "`/member` — Member panel (browse, rankings, profile, etc.)\n"
        "`/leader` — Leader panel (manage roster & kingdom)\n"
        "`/mod` — Moderator panel (matches & titles)\n"
        "`/profile @user` — View anyone's profile\n"
        "`/help` — This menu"
    ), inline=False)
    embed.set_footer(text="⚜️ Majestic Bot")
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# -------------------- EVENTS --------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    safety_sync.start()
    print(f"✅ Logged in as {bot.user}")
    print(f"⚜️ Majestic Bot is ready!")
    for guild in bot.guilds:
        for member in guild.members:
            role, tag = get_member_squad(member, guild)
            await safe_nick_update(member, role, tag)
    print("✅ Initial sync done")


@bot.event
async def on_member_update(before, after):
    role, tag = get_member_squad(after, after.guild)
    await bot.wait_until_ready()
    await safe_nick_update(after, role, tag)


@tasks.loop(minutes=5)
async def safety_sync():
    for guild in bot.guilds:
        for member in guild.members:
            role, tag = get_member_squad(member, guild)
            await safe_nick_update(member, role, tag)


# -------------------- RUN --------------------
bot.run(os.getenv("DISCORD_TOKEN"))
