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

# DEFAULT seeds — only used on FIRST RUN when no data file exists
DEFAULT_SQUADS = {
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

DEFAULT_GUEST_ROLES = {
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

# LIVE dicts — populated from data file on startup, NOT hardcoded
SQUADS = {}
GUEST_ROLES = {}

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
ANNOUNCE_CHANNEL_NAME = "war-results"

# Glory Points system modifiers
GLORY_BASE_WIN = 3
GLORY_BASE_DRAW = 1
GLORY_STREAK_BONUS = 1        # 3+ win streak
GLORY_CLEAN_SHEET_BONUS = 1   # opponent scored 0
GLORY_EXPECTED_TAX = -1       # beating much weaker team (rank 8+ below)

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
def _new_squad_entry():
    return {
        "wins": 0, "draws": 0, "losses": 0, "points": 0,
        "titles": [], "championship_wins": 0, "logo_url": None,
        "main_roster": [], "subs": [], "match_history": [],
        "current_streak": {"type": "none", "count": 0},
        "achievements": [], "biggest_win_streak": 0, "biggest_loss_streak": 0
    }


def load_data():
    global ALL_TAGS
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for match in data.get("matches", []):
                if "team1_participants" not in match:
                    match["team1_participants"] = []
                if "team2_participants" not in match:
                    match["team2_participants"] = []

            # --- Rebuild SQUADS from data file (single source of truth) ---
            if "squad_registry" in data:
                SQUADS.clear()
                SQUADS.update(data["squad_registry"])
            else:
                # Migration: old data without registry
                SQUADS.clear()
                SQUADS.update(DEFAULT_SQUADS)
                for sn, info in data.get("dynamic_squads", {}).items():
                    SQUADS[sn] = info.get("tag", "?")
                for sn, si in data.get("squads", {}).items():
                    if si.get("disbanded") and sn in SQUADS:
                        del SQUADS[sn]
                data["squad_registry"] = dict(SQUADS)

            # --- Rebuild GUEST_ROLES from data file ---
            if "guest_registry" in data:
                GUEST_ROLES.clear()
                GUEST_ROLES.update(data["guest_registry"])
            else:
                GUEST_ROLES.clear()
                GUEST_ROLES.update(DEFAULT_GUEST_ROLES)
                for sn, info in data.get("dynamic_squads", {}).items():
                    if info.get("guest_role"):
                        GUEST_ROLES[sn] = info["guest_role"]
                for sn, si in data.get("squads", {}).items():
                    if si.get("disbanded") and sn in GUEST_ROLES:
                        del GUEST_ROLES[sn]
                data["guest_registry"] = dict(GUEST_ROLES)

            # Ensure every active squad has a data entry
            for sn in list(SQUADS.keys()):
                if sn not in data["squads"]:
                    data["squads"][sn] = _new_squad_entry()

            ALL_TAGS = list(SQUADS.values())
            save_data(data)
            return data

    # First run — seed from defaults
    SQUADS.clear()
    SQUADS.update(DEFAULT_SQUADS)
    GUEST_ROLES.clear()
    GUEST_ROLES.update(DEFAULT_GUEST_ROLES)
    ALL_TAGS = list(SQUADS.values())

    data = {
        "squads": {}, "players": {}, "matches": [],
        "squad_registry": dict(SQUADS),
        "guest_registry": dict(GUEST_ROLES),
    }
    for sn in SQUADS:
        data["squads"][sn] = _new_squad_entry()
    save_data(data)
    return data


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, indent=2, fp=f, ensure_ascii=False)


def init_squad_data(squad_name):
    if squad_name not in squad_data["squads"]:
        squad_data["squads"][squad_name] = _new_squad_entry()


async def add_new_squad(guild, squad_name: str, tag: str, guest_role_name: str = None):
    """Create a new squad: Discord role + guest role + data entries."""
    global ALL_TAGS

    # Create the squad Discord role
    squad_role = discord.utils.get(guild.roles, name=squad_name)
    if not squad_role:
        squad_role = await guild.create_role(
            name=squad_name,
            mentionable=True,
            reason=f"Majestic Bot: New kingdom '{squad_name}' created"
        )

    # Create the guest Discord role
    guest_role = None
    if guest_role_name:
        guest_role = discord.utils.get(guild.roles, name=guest_role_name)
        if not guest_role:
            guest_role = await guild.create_role(
                name=guest_role_name,
                mentionable=False,
                reason=f"Majestic Bot: Guest role for '{squad_name}'"
            )

    # Update runtime dicts
    SQUADS[squad_name] = tag
    if guest_role_name:
        GUEST_ROLES[squad_name] = guest_role_name
    ALL_TAGS = list(SQUADS.values())

    # Persist to registries (single source of truth)
    squad_data["squad_registry"] = dict(SQUADS)
    squad_data["guest_registry"] = dict(GUEST_ROLES)

    init_squad_data(squad_name)
    save_data(squad_data)

    return squad_role, guest_role


async def remove_existing_squad(guild, squad_name: str, delete_roles: bool = True):
    """Remove a squad: optionally delete Discord roles, clean up data."""
    global ALL_TAGS

    if delete_roles:
        # Delete squad role
        role = discord.utils.get(guild.roles, name=squad_name)
        if role:
            try:
                await role.delete(reason=f"Majestic Bot: Kingdom '{squad_name}' disbanded")
            except:
                pass

        # Delete guest role
        grn = GUEST_ROLES.get(squad_name)
        if grn:
            gr = discord.utils.get(guild.roles, name=grn)
            if gr:
                try:
                    await gr.delete(reason=f"Majestic Bot: Guest role for '{squad_name}' removed")
                except:
                    pass

    # Remove from runtime dicts
    SQUADS.pop(squad_name, None)
    GUEST_ROLES.pop(squad_name, None)
    ALL_TAGS = list(SQUADS.values())

    # Persist registries (single source of truth)
    squad_data["squad_registry"] = dict(SQUADS)
    squad_data["guest_registry"] = dict(GUEST_ROLES)

    # Keep squad_data["squads"] entry for historical records but mark disbanded
    if squad_name in squad_data["squads"]:
        squad_data["squads"][squad_name]["disbanded"] = True

    save_data(squad_data)


squad_data = load_data()
if "challenges" not in squad_data:
    squad_data["challenges"] = []
if "bounties" not in squad_data:
    squad_data["bounties"] = {}


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
        if squad_name not in SQUADS or data.get("disbanded"):
            continue
        total = data["wins"] + data["draws"] + data["losses"]
        wr = (data["wins"] / total * 100) if total > 0 else 0.0
        rankings.append({
            "name": squad_name, "tag": SQUADS.get(squad_name, "?"), "points": data["points"],
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


# -------------------- SMART MEMBER SEARCH --------------------
def search_members(guild, query: str):
    """Fuzzy search guild members by name, display name, or ID."""
    query = query.strip()
    results = []

    # Try exact ID match first
    if query.isdigit():
        member = guild.get_member(int(query))
        if member:
            return [member]

    # Strip leading @ or <@...> mention format
    if query.startswith("<@") and query.endswith(">"):
        try:
            uid = int(query.strip("<@!>"))
            member = guild.get_member(uid)
            if member:
                return [member]
        except:
            pass

    q = query.lower()
    for member in guild.members:
        if member.bot:
            continue
        # Check display name, username, and global name
        if (q in member.display_name.lower() or
            q in member.name.lower() or
            (member.global_name and q in member.global_name.lower())):
            results.append(member)

    return results[:25]  # Cap at 25 for selector limits


# -------------------- POWER RATING --------------------
RANK_TITLES = [
    (90, "🔮 Mythical Legend", "A force that reshapes the battlefield!"),
    (75, "⚡ Elite Warlord", "Fear their name, respect their blade!"),
    (60, "🛡️ Veteran Knight", "Battle-hardened and unshakeable!"),
    (45, "⚔️ Rising Warrior", "Growing stronger with every clash!"),
    (30, "🌱 Promising Squire", "The seeds of greatness are planted!"),
    (0,  "🐣 Fresh Recruit", "Every legend starts somewhere!"),
]

def calculate_power_rating(player_id):
    """Calculate a fun 'power rating' score 0-100 for a player."""
    stats = get_player_stats(player_id)
    if not stats or stats["matches_played"] == 0:
        return 0, RANK_TITLES[-1]

    # Weighted formula: win rate matters most, experience adds bonus
    wr_score = stats["win_rate"] * 0.7
    exp_bonus = min(stats["matches_played"] * 0.6, 20)  # Cap at 20
    streak_bonus = 0

    pk = str(player_id)
    pd = squad_data["players"].get(pk, {})
    sn = pd.get("squad")
    if sn and sn in squad_data["squads"]:
        cs = squad_data["squads"][sn].get("current_streak", {})
        if cs.get("type") == "win":
            streak_bonus = min(cs.get("count", 0) * 2, 10)

    power = min(int(wr_score + exp_bonus + streak_bonus), 100)

    rank_title = RANK_TITLES[-1]
    for threshold, title, desc in RANK_TITLES:
        if power >= threshold:
            rank_title = (threshold, title, desc)
            break

    return power, rank_title


RECRUIT_QUOTES = [
    "⚔️ A new warrior joins the ranks! The enemy trembles!",
    "🌟 The kingdom grows stronger! Welcome to glory!",
    "🔥 Fresh blood on the battlefield! Let the conquest begin!",
    "👑 Another brave soul answers the call to arms!",
    "💪 The army expands! Victory draws ever closer!",
    "🦅 A new eagle joins the flock! Soar to greatness!",
    "⚡ Power surges through the kingdom's veins!",
    "🎯 A new blade, sharp and ready for battle!",
]

GUEST_QUOTES = [
    "🎭 A noble visitor graces the kingdom with their presence!",
    "🤝 Alliances strengthen — welcome, honored guest!",
    "🌐 Diplomacy at its finest! A guest of distinction arrives!",
    "⭐ The gates open for a worthy traveler!",
]


# =====================================================================
#                     AI ENGINE — Prediction & Intelligence
# =====================================================================

def predict_match(team1: str, team2: str):
    """AI match prediction based on multiple factors. Returns dict with analysis."""
    t1d = squad_data["squads"].get(team1, {})
    t2d = squad_data["squads"].get(team2, {})

    # Factor 1: Win Rate (weight: 35%)
    t1_total = t1d.get("wins", 0) + t1d.get("draws", 0) + t1d.get("losses", 0)
    t2_total = t2d.get("wins", 0) + t2d.get("draws", 0) + t2d.get("losses", 0)
    t1_wr = (t1d.get("wins", 0) / t1_total * 100) if t1_total > 0 else 50
    t2_wr = (t2d.get("wins", 0) / t2_total * 100) if t2_total > 0 else 50

    # Factor 2: Head-to-Head (weight: 25%)
    h2h = get_head_to_head(team1, team2)
    if h2h["total"] > 0:
        t1_h2h = (h2h["squad1_wins"] / h2h["total"]) * 100
        t2_h2h = (h2h["squad2_wins"] / h2h["total"]) * 100
    else:
        t1_h2h = 50
        t2_h2h = 50

    # Factor 3: Current Form — last 5 matches (weight: 25%)
    def get_form_score(squad_name):
        history = squad_data["squads"].get(squad_name, {}).get("match_history", [])[-5:]
        if not history:
            return 50
        score = 0
        for i, m in enumerate(history):
            weight = 1 + (i * 0.2)  # Recent matches weighted more
            try:
                s1, s2 = map(int, m["score"].split('-'))
                if m["team1"] == squad_name:
                    score += (20 * weight) if s1 > s2 else (5 * weight) if s1 == s2 else 0
                else:
                    score += (20 * weight) if s2 > s1 else (5 * weight) if s1 == s2 else 0
            except:
                pass
        return min(score / len(history) * 5, 100)

    t1_form = get_form_score(team1)
    t2_form = get_form_score(team2)

    # Factor 4: Momentum / Streak (weight: 15%)
    t1_cs = t1d.get("current_streak", {"type": "none", "count": 0})
    t2_cs = t2d.get("current_streak", {"type": "none", "count": 0})

    def streak_score(cs):
        if cs["type"] == "win": return min(50 + cs["count"] * 10, 100)
        elif cs["type"] == "loss": return max(50 - cs["count"] * 10, 0)
        return 50

    t1_streak = streak_score(t1_cs)
    t2_streak = streak_score(t2_cs)

    # Factor 5: Roster completeness bonus
    t1_roster = 10 if len(t1d.get("main_roster", [])) == 5 else 0
    t2_roster = 10 if len(t2d.get("main_roster", [])) == 5 else 0

    # Weighted composite score
    t1_score = (t1_wr * 0.35) + (t1_h2h * 0.25) + (t1_form * 0.25) + (t1_streak * 0.15) + t1_roster
    t2_score = (t2_wr * 0.35) + (t2_h2h * 0.25) + (t2_form * 0.25) + (t2_streak * 0.15) + t2_roster

    # Normalize to percentages
    total_score = t1_score + t2_score
    if total_score > 0:
        t1_pct = round(t1_score / total_score * 100)
        t2_pct = 100 - t1_pct
    else:
        t1_pct = t2_pct = 50

    # Draw probability based on how close the scores are
    diff = abs(t1_pct - t2_pct)
    draw_pct = max(5, 30 - diff)
    t1_pct = round(t1_pct * (100 - draw_pct) / 100)
    t2_pct = 100 - t1_pct - draw_pct

    # Confidence level
    data_points = t1_total + t2_total + h2h["total"]
    if data_points >= 20: confidence = "🟢 HIGH"
    elif data_points >= 8: confidence = "🟡 MEDIUM"
    else: confidence = "🔴 LOW"

    # Narrative
    if t1_pct > t2_pct + 20:
        narrative = f"**{team1}** holds a commanding advantage! Their superior form and record make them the clear favorite."
    elif t2_pct > t1_pct + 20:
        narrative = f"**{team2}** holds a commanding advantage! Their superior form and record make them the clear favorite."
    elif abs(t1_pct - t2_pct) <= 10:
        narrative = "This is an **extremely close matchup**! Both kingdoms are evenly matched — expect a thrilling battle!"
    elif t1_pct > t2_pct:
        narrative = f"**{team1}** has a slight edge, but **{team2}** could easily pull off an upset. This one's unpredictable!"
    else:
        narrative = f"**{team2}** has a slight edge, but **{team1}** could easily pull off an upset. This one's unpredictable!"

    # Key factors text
    factors = []
    if h2h["total"] > 0:
        factors.append(f"⚔️ H2H: {h2h['squad1_wins']}-{h2h['draws']}-{h2h['squad2_wins']} ({h2h['total']} meetings)")
    if t1_cs["count"] >= 3:
        se = "🔥" if t1_cs["type"] == "win" else "❄️"
        factors.append(f"{se} {team1} on a **{t1_cs['count']} {t1_cs['type']}** streak")
    if t2_cs["count"] >= 3:
        se = "🔥" if t2_cs["type"] == "win" else "❄️"
        factors.append(f"{se} {team2} on a **{t2_cs['count']} {t2_cs['type']}** streak")
    if t1_wr > 0 or t2_wr > 0:
        factors.append(f"📊 Win Rates: {t1_wr:.0f}% vs {t2_wr:.0f}%")

    return {
        "t1_pct": t1_pct, "t2_pct": t2_pct, "draw_pct": draw_pct,
        "confidence": confidence, "narrative": narrative, "factors": factors,
        "h2h": h2h, "t1_wr": t1_wr, "t2_wr": t2_wr,
    }


def generate_squad_report(squad_name: str):
    """Generate an AI intelligence report for a squad."""
    si = squad_data["squads"].get(squad_name, {})
    w, d, l = si.get("wins", 0), si.get("draws", 0), si.get("losses", 0)
    total = w + d + l
    wr = (w / total * 100) if total > 0 else 0

    report = {"strengths": [], "weaknesses": [], "threat_level": 0, "form_trend": "", "rival": None, "insights": []}

    # Threat Level (0-100)
    rank = get_squad_rank(squad_name) or len(SQUADS)
    rank_score = max(0, 100 - (rank - 1) * (100 / len(SQUADS)))
    wr_score = wr
    cs = si.get("current_streak", {"type": "none", "count": 0})
    momentum = 10 if cs.get("type") == "win" else -10 if cs.get("type") == "loss" else 0
    momentum *= min(cs.get("count", 0), 5) / 5
    roster_bonus = 15 if len(si.get("main_roster", [])) == 5 else 0
    title_bonus = min(si.get("championship_wins", 0) * 5, 15)

    threat = min(100, max(0, int(rank_score * 0.4 + wr_score * 0.3 + momentum + roster_bonus + title_bonus)))
    report["threat_level"] = threat

    # Threat Tier
    if threat >= 85: report["threat_tier"] = ("☠️ LETHAL", "Extremely dangerous — approach with caution!")
    elif threat >= 70: report["threat_tier"] = ("🔥 DANGEROUS", "A serious contender in any battle!")
    elif threat >= 50: report["threat_tier"] = ("⚔️ COMPETITIVE", "Capable of winning against most opponents")
    elif threat >= 30: report["threat_tier"] = ("🛡️ DEVELOPING", "Building strength, not to be underestimated")
    else: report["threat_tier"] = ("🌱 EMERGING", "Early stages — potential yet to be unlocked")

    # Form Trend (last 10 vs previous 10)
    history = si.get("match_history", [])
    if len(history) >= 10:
        def count_wins(matches, sn):
            wins = 0
            for m in matches:
                try:
                    s1, s2 = map(int, m["score"].split('-'))
                    if (m["team1"] == sn and s1 > s2) or (m["team2"] == sn and s2 > s1):
                        wins += 1
                except:
                    pass
            return wins
        recent_wins = count_wins(history[-5:], squad_name)
        older_wins = count_wins(history[-10:-5], squad_name)
        if recent_wins > older_wins + 1:
            report["form_trend"] = "📈 **ASCENDING** — Performance is improving rapidly!"
        elif recent_wins < older_wins - 1:
            report["form_trend"] = "📉 **DECLINING** — Recent form has dropped off"
        else:
            report["form_trend"] = "➡️ **STABLE** — Consistent performance maintained"
    elif len(history) >= 3:
        report["form_trend"] = "📊 **EARLY DAYS** — Not enough data for trend analysis"
    else:
        report["form_trend"] = "🆕 **NEW** — Just getting started!"

    # Strengths
    if wr >= 60: report["strengths"].append("🏆 Elite win rate")
    if cs.get("type") == "win" and cs.get("count", 0) >= 3: report["strengths"].append(f"🔥 Hot streak ({cs['count']} wins)")
    if len(si.get("main_roster", [])) == 5: report["strengths"].append("⭐ Full main roster")
    if si.get("championship_wins", 0) > 0: report["strengths"].append(f"👑 Championship pedigree ({si['championship_wins']}x)")
    if d > 0 and total > 0 and (d / total) < 0.15: report["strengths"].append("⚡ Decisive — rarely draws")
    if si.get("biggest_win_streak", 0) >= 5: report["strengths"].append(f"💪 Historic dominance ({si['biggest_win_streak']} best streak)")

    # Weaknesses
    if wr < 40 and total >= 5: report["weaknesses"].append("💀 Low win rate")
    if cs.get("type") == "loss" and cs.get("count", 0) >= 3: report["weaknesses"].append(f"❄️ Cold streak ({cs['count']} losses)")
    if len(si.get("main_roster", [])) < 5: report["weaknesses"].append(f"⚠️ Incomplete roster ({len(si.get('main_roster', []))}/5)")
    if total > 0 and l > w: report["weaknesses"].append("📉 More losses than wins")
    if total < 3: report["weaknesses"].append("🆕 Limited match experience")

    if not report["strengths"]: report["strengths"].append("🌱 Potential waiting to bloom!")
    if not report["weaknesses"]: report["weaknesses"].append("✨ No major weaknesses detected!")

    # Find biggest rival (most matches played against)
    rival_counts = {}
    for m in history:
        opponent = m["team2"] if m["team1"] == squad_name else m["team1"]
        rival_counts[opponent] = rival_counts.get(opponent, 0) + 1
    if rival_counts:
        rival_name = max(rival_counts, key=rival_counts.get)
        h2h = get_head_to_head(squad_name, rival_name)
        report["rival"] = {"name": rival_name, "matches": h2h["total"], "h2h": h2h}

    # Fun insights
    if total > 0:
        report["insights"].append(f"🎯 Point efficiency: **{si.get('points', 0) / total:.1f}** pts per match")
    if si.get("biggest_win_streak", 0) > 0:
        report["insights"].append(f"🏔️ Peak performance: **{si['biggest_win_streak']}** consecutive victories")
    if len(si.get("achievements", [])) > 0:
        report["insights"].append(f"🏅 **{len(si['achievements'])}** achievements unlocked")

    return report


def generate_realm_news():
    """Generate dynamic realm news bulletin from recent data."""
    headlines = []
    matches = squad_data["matches"]
    rankings = get_squad_ranking()

    # 1. Latest match result
    if matches:
        last = matches[-1]
        t1, t2, score = last["team1"], last["team2"], last["score"]
        try:
            s1, s2 = map(int, score.split('-'))
            if s1 > s2:
                headlines.append(f"⚔️ **{SQUADS.get(t1, "?")} {t1}** triumphs over **{SQUADS.get(t2, "?")} {t2}** ({score}) in the latest battle!")
            elif s2 > s1:
                headlines.append(f"⚔️ **{SQUADS.get(t2, "?")} {t2}** triumphs over **{SQUADS.get(t1, "?")} {t1}** ({score}) in the latest battle!")
            else:
                headlines.append(f"⚖️ **{SQUADS.get(t1, "?")} {t1}** and **{SQUADS.get(t2, "?")} {t2}** battle to a stalemate ({score})!")
        except:
            pass

    # 2. Hottest streak in the realm
    hottest_name, hottest_count = None, 0
    coldest_name, coldest_count = None, 0
    for sn, d in squad_data["squads"].items():
        cs = d.get("current_streak", {"type": "none", "count": 0})
        if cs.get("type") == "win" and cs.get("count", 0) > hottest_count:
            hottest_name, hottest_count = sn, cs["count"]
        if cs.get("type") == "loss" and cs.get("count", 0) > coldest_count:
            coldest_name, coldest_count = sn, cs["count"]

    if hottest_name and hottest_count >= 2:
        headlines.append(f"🔥 **{SQUADS.get(hottest_name, "?")} {hottest_name}** is ON FIRE with a **{hottest_count}-win streak**! Who can stop them?")
    if coldest_name and coldest_count >= 3:
        headlines.append(f"❄️ **{SQUADS.get(coldest_name, "?")} {coldest_name}** struggles through a **{coldest_count}-loss streak**. Can they turn it around?")

    # 3. Championship leader
    if rankings:
        leader = rankings[0]
        if leader["points"] > 0:
            if len(rankings) > 1:
                gap = leader["points"] - rankings[1]["points"]
                headlines.append(f"👑 **{leader['tag']} {leader['name']}** leads the realm with **{leader['points']} pts** ({'+' + str(gap) if gap > 0 else 'TIED'} over #{2})")
            else:
                headlines.append(f"👑 **{leader['tag']} {leader['name']}** leads the realm with **{leader['points']} pts**!")

    # 4. Rising kingdom (biggest positive point change potential)
    underdogs = [s for s in rankings if s["total_matches"] >= 3 and s["rank"] > 5 and s["win_rate"] > 55]
    if underdogs:
        rising = random.choice(underdogs)
        headlines.append(f"📈 **{rising['tag']} {rising['name']}** is a dark horse — ranked #{rising['rank']} but winning **{rising['win_rate']:.0f}%** of their battles!")

    # 5. Rivalry alert — find most contested matchup
    matchup_counts = {}
    for m in matches[-20:]:
        key = tuple(sorted([m["team1"], m["team2"]]))
        matchup_counts[key] = matchup_counts.get(key, 0) + 1
    if matchup_counts:
        hottest_pair = max(matchup_counts, key=matchup_counts.get)
        if matchup_counts[hottest_pair] >= 2:
            headlines.append(f"⚔️ Rivalry Watch: **{SQUADS.get(hottest_pair[0], '?')} {hottest_pair[0]}** vs **{SQUADS.get(hottest_pair[1], '?')} {hottest_pair[1]}** — {matchup_counts[hottest_pair]} clashes recently!")

    # 6. Random fun fact
    total_matches = len(matches)
    total_players = len([p for p in squad_data["players"].values() if p.get("ingame_name")])
    fun_facts = [
        f"📊 The realm has witnessed **{total_matches}** battles so far!",
        f"🗡️ **{total_players}** warriors have registered their profiles!",
        f"🏰 **{len(SQUADS)}** kingdoms compete for eternal glory!",
    ]
    if total_matches > 0:
        total_draws = sum(1 for m in matches if len(set(m["score"].split('-'))) == 1)
        fun_facts.append(f"🤝 **{total_draws}** battles ended in a draw ({total_draws/total_matches*100:.0f}%)")
    headlines.append(random.choice(fun_facts))

    return headlines


# =====================================================================
#                     AI VIEWS — Prediction & Reports
# =====================================================================

class MatchPredictorStep1View(View):
    """Step 1: Pick first team for prediction"""
    def __init__(self, page=1):
        super().__init__(timeout=180)
        self.page = page
        all_squads = sorted(SQUADS.items())
        start = (page - 1) * 25
        end = start + 25
        page_squads = all_squads[start:end]

        options = [discord.SelectOption(label=n, value=n, emoji="🏰", description=f"Tag: {t}") for n, t in page_squads]
        select = Select(placeholder="🔮 Select FIRST kingdom...", options=options)
        select.callback = self.team1_selected
        self.add_item(select)

        if len(all_squads) > 25:
            if page > 1:
                b = Button(label="← Prev", style=discord.ButtonStyle.secondary); b.callback = self.prev; self.add_item(b)
            if end < len(all_squads):
                b = Button(label="Next →", style=discord.ButtonStyle.secondary); b.callback = self.nxt; self.add_item(b)

    async def prev(self, i): await i.response.edit_message(view=MatchPredictorStep1View(self.page - 1))
    async def nxt(self, i): await i.response.edit_message(view=MatchPredictorStep1View(self.page + 1))

    async def team1_selected(self, interaction):
        team1 = interaction.data["values"][0]
        embed = discord.Embed(
            title="🔮 War Oracle — Step 2",
            description=f"✅ Kingdom 1: **{SQUADS.get(team1, "?")} {team1}**\n\nNow select the **opponent**:",
            color=ROYAL_PURPLE
        )
        await interaction.response.edit_message(embed=embed, view=MatchPredictorStep2View(team1))


class MatchPredictorStep2View(View):
    """Step 2: Pick second team and show prediction"""
    def __init__(self, team1, page=1):
        super().__init__(timeout=180)
        self.team1 = team1
        self.page = page
        all_squads = sorted(SQUADS.items())
        start = (page - 1) * 25
        end = start + 25
        page_squads = all_squads[start:end]

        options = [discord.SelectOption(label=n, value=n, emoji="🏰", description=f"Tag: {t}") for n, t in page_squads]
        select = Select(placeholder="🔮 Select OPPONENT kingdom...", options=options)
        select.callback = self.team2_selected
        self.add_item(select)

        if len(all_squads) > 25:
            if page > 1:
                b = Button(label="← Prev", style=discord.ButtonStyle.secondary); b.callback = self.prev; self.add_item(b)
            if end < len(all_squads):
                b = Button(label="Next →", style=discord.ButtonStyle.secondary); b.callback = self.nxt; self.add_item(b)

    async def prev(self, i): await i.response.edit_message(view=MatchPredictorStep2View(self.team1, self.page - 1))
    async def nxt(self, i): await i.response.edit_message(view=MatchPredictorStep2View(self.team1, self.page + 1))

    async def team2_selected(self, interaction):
        team2 = interaction.data["values"][0]
        if team2 == self.team1:
            await interaction.response.edit_message(content="❌ A kingdom cannot battle itself!", embed=None)
            return

        pred = predict_match(self.team1, team2)

        # Build visual prediction bars
        t1_bar = "🟦" * (pred["t1_pct"] // 10) + "⬜" * (10 - pred["t1_pct"] // 10)
        t2_bar = "🟥" * (pred["t2_pct"] // 10) + "⬜" * (10 - pred["t2_pct"] // 10)

        embed = discord.Embed(
            title=f"🔮 War Oracle — Match Prediction",
            description=f"**{SQUADS.get(self.team1, "?")} {self.team1}** ⚔️ **{SQUADS.get(team2, "?")} {team2}**\n\n{pred['narrative']}",
            color=ROYAL_PURPLE
        )

        embed.add_field(
            name=f"📊 Win Probabilities",
            value=(
                f"🟦 **{self.team1}**: **{pred['t1_pct']}%** {t1_bar}\n"
                f"🟥 **{team2}**: **{pred['t2_pct']}%** {t2_bar}\n"
                f"⚖️ **Draw**: **{pred['draw_pct']}%**"
            ),
            inline=False
        )

        if pred["factors"]:
            embed.add_field(name="🔑 Key Factors", value="\n".join(pred["factors"]), inline=False)

        embed.add_field(name="📡 Confidence", value=f"{pred['confidence']} (based on {sum(1 for _ in squad_data['matches'])} total realm battles)", inline=False)
        embed.set_footer(text="🔮 The Oracle speaks — but fate is written on the battlefield!")
        await interaction.response.edit_message(embed=embed, view=None)


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





# -------------------- SQUAD INFO DISPLAY --------------------
async def show_squad_info(interaction, squad_role, squad_name, tag, public=False, edit=False):
    """Display squad info with embedded history button"""
    # Auto-create data entry if missing (e.g. newly added squad)
    if squad_name not in squad_data["squads"]:
        squad_data["squads"][squad_name] = _new_squad_entry()
        save_data(squad_data)
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
    """Squad profile with history, rivalry & AI analysis buttons"""
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
            description=f"✅ First Kingdom: **{SQUADS.get(self.squad_name, "?")} {self.squad_name}**\n\nSelect the rival kingdom:",
            color=ROYAL_BLUE
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="AI Analysis", emoji="🧠", style=discord.ButtonStyle.success)
    async def analysis_btn(self, interaction: discord.Interaction, button: Button):
        report = generate_squad_report(self.squad_name)
        si = squad_data["squads"].get(self.squad_name, {})

        # Threat bar visual
        tl = report["threat_level"]
        threat_bar = "█" * (tl // 10) + "░" * (10 - tl // 10)
        tier_name, tier_desc = report["threat_tier"]

        embed = discord.Embed(
            title=f"🧠 Intelligence Report — {SQUADS.get(self.squad_name, "?")} {self.squad_name}",
            description=f"{tier_name} — *{tier_desc}*",
            color=ROYAL_PURPLE
        )

        embed.add_field(
            name=f"☠️ Threat Level: {tl}/100",
            value=f"`{threat_bar}` **{tl}%**",
            inline=False
        )

        embed.add_field(name="📈 Form Trend", value=report["form_trend"], inline=False)
        embed.add_field(name="💪 Strengths", value="\n".join(report["strengths"]), inline=True)
        embed.add_field(name="⚠️ Weaknesses", value="\n".join(report["weaknesses"]), inline=True)

        if report["rival"]:
            r = report["rival"]
            h = r["h2h"]
            embed.add_field(
                name=f"🎯 Biggest Rival: {SQUADS.get(r['name'], '?')} {r['name']}",
                value=f"Met **{r['matches']}** times | Record: {h['squad1_wins']}W-{h['draws']}D-{h['squad2_wins']}L",
                inline=False
            )

        if report["insights"]:
            embed.add_field(name="💡 Insights", value="\n".join(report["insights"]), inline=False)

        embed.set_footer(text="🧠 Majestic AI — Powered by data, driven by glory!")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(interaction.guild, "🧠 AI Analysis", f"{interaction.user.mention} ran **AI Analysis** on **{self.squad_name}**")


async def show_squad_match_history(interaction, squad_name):
    matches = [m for m in squad_data["matches"] if m["team1"] == squad_name or m["team2"] == squad_name]
    if not matches:
        embed = discord.Embed(title=f"📜 {squad_name} — No Battles Yet", description="This kingdom has not entered battle!", color=ROYAL_BLUE)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    recent = matches[-10:][::-1]
    embed = discord.Embed(title=f"📜 {SQUADS.get(squad_name, "?")} {squad_name} — Battle History", description=f"Last {len(recent)} battles", color=ROYAL_BLUE)
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
        # Show glory points earned
        pts_info = ""
        if t1 == squad_name:
            pts_earned = m.get("t1_pts", "?")
        else:
            pts_earned = m.get("t2_pts", "?")
        if pts_earned and pts_earned != "?" and pts_earned > 0:
            pts_info = f" | 💎 +{pts_earned}"
        embed.add_field(name=f"{re} {SQUADS.get(t1, '?')} vs {SQUADS.get(t2, '?')} — {rt}", value=f"**{t1}** {score} **{t2}**\n📅 {ds} • 🆔 `{mid}`{pts_info}", inline=False)

    if len(matches) > 10:
        embed.set_footer(text=f"Showing last 10 of {len(matches)} battles")
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def show_player_profile(interaction, member: discord.Member, public=False):
    embed, _ = build_profile_embed(member, interaction.guild)
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
        if not all_squads:
            return
        start = (page - 1) * 25
        end = start + 25
        page_squads = all_squads[start:end]
        if not page_squads:
            return

        placeholders = {
            "browse": "🏰 Select a kingdom to explore...",
            "rivalry_step2": "⚔️ Select the rival kingdom...",
        }
        ph = placeholders.get(purpose, "Select a kingdom...")

        options = [discord.SelectOption(label=str(n)[:100], value=str(n)[:100], description=f"Tag: {t}"[:100]) for n, t in page_squads]
        select = Select(placeholder=ph, options=options)
        select.callback = self.selected
        self.add_item(select)

        total_pages = (len(all_squads) + 24) // 25
        if total_pages > 1:
            if page > 1:
                b = Button(label="← Prev", style=discord.ButtonStyle.secondary)
                b.callback = self.prev_page
                self.add_item(b)
            if page < total_pages:
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
        try:
            sq = interaction.data["values"][0]
            if self.purpose == "browse":
                sr = discord.utils.get(interaction.guild.roles, name=sq)
                await show_squad_info(interaction, sr, sq, SQUADS.get(sq, "?"), public=True, edit=True)
            elif self.purpose == "rivalry_step2":
                await show_rivalry_stats(interaction, self.selected_squad1, sq)
        except Exception as e:
            try:
                await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
            except:
                pass


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

    embed = discord.Embed(title="⚔️ Kingdom Rivalry", description=f"**{SQUADS.get(sq1, "?")} {sq1}** vs **{SQUADS.get(sq2, "?")} {sq2}**", color=ROYAL_RED)
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

        if action == "remove_guest":
            # Show members with the GUEST role, not the squad role
            grn = GUEST_ROLES.get(squad_name)
            if grn:
                gr = discord.utils.get(guild.roles, name=grn) if guild else None
                members = gr.members if gr else []
            else:
                members = []
        elif action in ["remove_member", "set_main", "remove_main", "set_sub", "remove_sub", "promote_leader"]:
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
        await log_action(self.guild, "❌ Main Removed", f"{interaction.user.mention} removed {member.mention} from **{self.squad_name}** main roster")

    async def h_set_sub(self, interaction, member):
        si = squad_data["squads"][self.squad_name]
        subs = si.get("subs", [])
        if len(subs) >= 3: await interaction.response.edit_message(content="❌ Subs full (3 max)!", embed=None, view=None); return
        if member.id in subs: await interaction.response.edit_message(content="❌ Already a sub!", embed=None, view=None); return
        if member.id in si.get("main_roster", []): si["main_roster"].remove(member.id)
        subs.append(member.id); save_data(squad_data)
        embed = discord.Embed(title="🔄 Sub Added!", description=f"{member.mention} → Substitutes ({len(subs)}/3)", color=ROYAL_BLUE)
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "🔄 Sub Set", f"{interaction.user.mention} added {member.mention} to **{self.squad_name}** substitutes")

    async def h_rm_sub(self, interaction, member):
        si = squad_data["squads"][self.squad_name]
        subs = si.get("subs", [])
        if member.id not in subs: await interaction.response.edit_message(content="❌ Not a substitute!", embed=None, view=None); return
        subs.remove(member.id); save_data(squad_data)
        embed = discord.Embed(title="✅ Removed from Subs", description=f"{member.mention} removed from substitutes", color=ROYAL_PURPLE)
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "❌ Sub Removed", f"{interaction.user.mention} removed {member.mention} from **{self.squad_name}** substitutes")

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
        await log_action(self.guild, "🎭 Guest Added", f"{interaction.user.mention} gave {member.mention} guest access to **{self.squad_name}**")

    async def h_rm_guest(self, interaction, member):
        grn = GUEST_ROLES.get(self.squad_name)
        if not grn: await interaction.response.edit_message(content="❌ No guest role!", embed=None, view=None); return
        gr = discord.utils.get(self.guild.roles, name=grn)
        if not gr or gr not in member.roles: await interaction.response.edit_message(content="❌ No guest role on member!", embed=None, view=None); return
        await member.remove_roles(gr)
        embed = discord.Embed(title="✅ Guest Removed", description=f"{member.mention}'s guest access revoked", color=ROYAL_PURPLE)
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(self.guild, "❌ Guest Removed", f"{interaction.user.mention} revoked {member.mention}'s guest access to **{self.squad_name}**")

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
#                     GLORY POINTS SYSTEM
# =====================================================================

def calculate_glory_points(winner_name, loser_name, score1, score2, is_draw=False):
    """Calculate dynamic Glory Points based on rank difference, streaks, and performance."""
    if is_draw:
        return 1, 1, [], []  # t1_pts, t2_pts, t1_tags, t2_tags

    winner_rank = get_squad_rank(winner_name) or 999
    loser_rank = get_squad_rank(loser_name) or 999

    base = GLORY_BASE_WIN
    bonus = 0
    tags = []

    # --- Upset Bonus (winner was ranked LOWER = higher number) ---
    rank_diff = winner_rank - loser_rank  # positive = upset
    if rank_diff > 0:
        if loser_rank <= 3:
            bonus += 3
            tags.append("👑 **GIANT SLAYER** (+3)")
        elif rank_diff >= 8:
            bonus += 3
            tags.append("⚡ **MASSIVE UPSET** (+3)")
        elif rank_diff >= 4:
            bonus += 2
            tags.append("⚡ **UPSET** (+2)")
        else:
            bonus += 1
            tags.append("🎯 Underdog (+1)")
    elif rank_diff < -8:
        # Beating a much weaker team
        bonus += GLORY_EXPECTED_TAX
        tags.append("📉 Expected (-1)")

    # --- Streak Bonus ---
    winner_si = squad_data["squads"].get(winner_name, {})
    cs = winner_si.get("current_streak", {})
    if cs.get("type") == "win" and cs.get("count", 0) >= 2:  # will become 3 after this match
        bonus += GLORY_STREAK_BONUS
        tags.append(f"🔥 Streak Fire (+1)")

    # --- Clean Sheet Bonus ---
    # Winner's opponent scored 0
    winner_is_t1 = (winner_rank == get_squad_rank(winner_name))  # always true
    opp_score = score2 if winner_name != loser_name else score1
    # Actually determine by who won
    if score1 > score2:  # team1 won
        opp_score = score2
    else:
        opp_score = score1
    if opp_score == 0:
        bonus += GLORY_CLEAN_SHEET_BONUS
        tags.append("🧹 Clean Sheet (+1)")

    # --- Bounty Bonus ---
    bounty = squad_data.get("bounties", {}).get(loser_name)
    if bounty:
        bounty_pts = bounty.get("points", 2)
        bonus += bounty_pts
        tags.append(f"💰 **BOUNTY CLAIMED** (+{bounty_pts})")
        # Remove claimed bounty
        squad_data["bounties"].pop(loser_name, None)

    total = max(base + bonus, 1)  # minimum 1 point for a win
    return total, 0, tags, []


def refresh_bounties():
    """Auto-place bounties on top 3 kingdoms. Called after each match."""
    rankings = get_squad_ranking()
    if not rankings:
        return
    bounties = squad_data.get("bounties", {})

    # Auto-bounties on top 3 if they don't already have one
    tier_bounties = {1: 3, 2: 2, 3: 1}
    for r in rankings[:3]:
        if r["name"] not in bounties and r["total_matches"] >= 3:
            bounties[r["name"]] = {
                "points": tier_bounties[r["rank"]],
                "reason": f"🏆 #{r['rank']} Ranked Kingdom",
                "placed_by": "system",
                "date": datetime.utcnow().isoformat()
            }
    squad_data["bounties"] = bounties


# =====================================================================
#                     MATCH ANNOUNCEMENTS
# =====================================================================

async def announce_match(guild, embed):
    """Post match result to the public #war-results channel."""
    channel = discord.utils.get(guild.text_channels, name=ANNOUNCE_CHANNEL_NAME)
    if channel:
        try:
            await channel.send(embed=embed)
        except:
            pass


async def announce_challenge(guild, embed, content=None):
    """Post challenge updates to #war-results channel."""
    channel = discord.utils.get(guild.text_channels, name=ANNOUNCE_CHANNEL_NAME)
    if channel:
        try:
            await channel.send(content=content, embed=embed)
        except:
            pass


# =====================================================================
#                     CHALLENGE SYSTEM
# =====================================================================

def get_active_challenges(squad_name=None):
    """Get all pending/accepted challenges, optionally filtered by squad."""
    challenges = squad_data.get("challenges", [])
    active = [c for c in challenges if c["status"] in ("pending", "accepted")]
    if squad_name:
        active = [c for c in active if c["challenger"] == squad_name or c["challenged"] == squad_name]
    return active


def has_pending_challenge(squad1, squad2):
    """Check if there's already an active challenge between two squads."""
    for c in squad_data.get("challenges", []):
        if c["status"] in ("pending", "accepted"):
            if (c["challenger"] == squad1 and c["challenged"] == squad2) or \
               (c["challenger"] == squad2 and c["challenged"] == squad1):
                return True
    return False


class ChallengeStep1View(View):
    """Leader selects which kingdom to challenge."""
    def __init__(self, challenger_name, page=1):
        super().__init__(timeout=180)
        self.challenger_name = challenger_name
        self.page = page

        # Show all squads EXCEPT the challenger
        all_squads = sorted([(n, t) for n, t in SQUADS.items() if n != challenger_name])
        if not all_squads:
            return
        start = (page - 1) * 25
        end = start + 25
        page_squads = all_squads[start:end]
        if not page_squads:
            return

        options = [discord.SelectOption(label=str(n)[:100], value=str(n)[:100], description=f"Tag: {t}"[:100]) for n, t in page_squads]
        select = Select(placeholder="⚔️ Select kingdom to challenge...", options=options)
        select.callback = self.selected
        self.add_item(select)

        total_pages = (len(all_squads) + 24) // 25
        if total_pages > 1:
            if page > 1:
                b = Button(label="← Prev", style=discord.ButtonStyle.secondary); b.callback = self.prev; self.add_item(b)
            if page < total_pages:
                b = Button(label="Next →", style=discord.ButtonStyle.secondary); b.callback = self.nxt; self.add_item(b)

    async def prev(self, i):
        await i.response.edit_message(view=ChallengeStep1View(self.challenger_name, self.page - 1))
    async def nxt(self, i):
        await i.response.edit_message(view=ChallengeStep1View(self.challenger_name, self.page + 1))

    async def selected(self, interaction):
        target = interaction.data["values"][0]
        if has_pending_challenge(self.challenger_name, target):
            await interaction.response.edit_message(
                content=f"❌ There's already an active challenge between **{self.challenger_name}** and **{target}**!",
                embed=None, view=None)
            return
        await interaction.response.send_modal(ChallengeMessageModal(self.challenger_name, target))


class ChallengeMessageModal(Modal, title="⚔️ War Declaration"):
    war_message = TextInput(
        label="War Declaration (optional)",
        placeholder="Send a message to your opponents! Leave blank for none.",
        required=False,
        max_length=200,
        style=discord.TextStyle.paragraph
    )

    def __init__(self, challenger, challenged):
        super().__init__()
        self.challenger = challenger
        self.challenged = challenged

    async def on_submit(self, interaction: discord.Interaction):
        msg = self.war_message.value.strip() if self.war_message.value else ""

        challenge_id = str(uuid.uuid4())[:8]
        challenge = {
            "id": challenge_id,
            "challenger": self.challenger,
            "challenged": self.challenged,
            "status": "pending",
            "date": datetime.utcnow().isoformat(),
            "accepted_date": None,
            "message": msg,
            "challenger_user_id": interaction.user.id,
        }
        squad_data["challenges"].append(challenge)
        save_data(squad_data)

        # Confirm to challenger
        embed = discord.Embed(
            title="⚔️ Challenge Sent!",
            description=(
                f"**{SQUADS.get(self.challenger, '?')} {self.challenger}** has challenged "
                f"**{SQUADS.get(self.challenged, '?')} {self.challenged}** to battle!\n\n"
                f"🆔 Challenge: `{challenge_id}`\n"
                f"⏳ Waiting for opponent's leaders to respond..."
            ),
            color=ROYAL_RED
        )
        if msg:
            embed.add_field(name="📜 War Declaration", value=f"*\"{msg}\"*", inline=False)
        await interaction.response.edit_message(embed=embed, view=None)

        # Public announcement in #war-results
        pub_embed = discord.Embed(
            title="⚔️ WAR CHALLENGE ISSUED!",
            description=(
                f"**{SQUADS.get(self.challenger, '?')} {self.challenger}** has thrown down the gauntlet!\n\n"
                f"🎯 Target: **{SQUADS.get(self.challenged, '?')} {self.challenged}**\n"
                f"⏳ Status: **PENDING RESPONSE**"
            ),
            color=ROYAL_RED
        )
        if msg:
            pub_embed.add_field(name="📜 War Declaration", value=f"*\"{msg}\"*", inline=False)
        pub_embed.set_footer(text=f"Challenge ID: {challenge_id} | Leaders of {self.challenged} — accept or decline!")

        # Mention the challenged squad's role
        challenged_role = discord.utils.get(interaction.guild.roles, name=self.challenged)
        mention_text = challenged_role.mention if challenged_role else f"**{self.challenged}**"

        # Send to #war-results with response buttons
        announce_ch = discord.utils.get(interaction.guild.text_channels, name=ANNOUNCE_CHANNEL_NAME)
        if announce_ch:
            try:
                response_view = ChallengeResponseView(challenge_id, self.challenger, self.challenged)
                await announce_ch.send(
                    content=f"🚨 {mention_text} — You've been challenged!",
                    embed=pub_embed,
                    view=response_view
                )
            except:
                pass

        await log_action(interaction.guild, "⚔️ Challenge Issued",
            f"{interaction.user.mention} (**{self.challenger}**) challenged **{self.challenged}**" + (f" — *\"{msg}\"*" if msg else ""))


class ChallengeResponseView(View):
    """Accept/Decline buttons shown in #war-results for opponent leaders."""
    def __init__(self, challenge_id, challenger, challenged):
        super().__init__(timeout=None)  # Persistent — no timeout
        self.challenge_id = challenge_id
        self.challenger = challenger
        self.challenged = challenged

    @discord.ui.button(label="Accept Challenge", style=discord.ButtonStyle.success, emoji="⚔️")
    async def accept_btn(self, interaction: discord.Interaction, button: Button):
        # Only leaders of the challenged kingdom can accept
        if not is_leader(interaction.user):
            await interaction.response.send_message("❌ Only **Leaders** can respond to challenges.", ephemeral=True)
            return
        user_squad, _ = get_member_squad(interaction.user, interaction.guild)
        if not user_squad or user_squad.name != self.challenged:
            await interaction.response.send_message(f"❌ Only leaders of **{self.challenged}** can accept.", ephemeral=True)
            return

        # Update challenge status
        for c in squad_data["challenges"]:
            if c["id"] == self.challenge_id and c["status"] == "pending":
                c["status"] = "accepted"
                c["accepted_date"] = datetime.utcnow().isoformat()
                c["accepted_by"] = interaction.user.id
                break
        else:
            await interaction.response.send_message("❌ Challenge no longer pending.", ephemeral=True)
            return
        save_data(squad_data)

        embed = discord.Embed(
            title="⚔️ CHALLENGE ACCEPTED!",
            description=(
                f"**{SQUADS.get(self.challenged, '?')} {self.challenged}** accepts the challenge from "
                f"**{SQUADS.get(self.challenger, '?')} {self.challenger}**!\n\n"
                f"🏟️ **THE BATTLE IS ON!**\n"
                f"📋 Moderators — please schedule this match!"
            ),
            color=ROYAL_GREEN
        )
        embed.set_footer(text=f"Challenge ID: {self.challenge_id} | Accepted by {interaction.user.display_name}")
        await interaction.response.edit_message(embed=embed, view=None)

        await log_action(interaction.guild, "⚔️ Challenge Accepted",
            f"{interaction.user.mention} (**{self.challenged}**) accepted challenge from **{self.challenger}** | ID: {self.challenge_id}")

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger, emoji="✋")
    async def decline_btn(self, interaction: discord.Interaction, button: Button):
        if not is_leader(interaction.user):
            await interaction.response.send_message("❌ Only **Leaders** can respond to challenges.", ephemeral=True)
            return
        user_squad, _ = get_member_squad(interaction.user, interaction.guild)
        if not user_squad or user_squad.name != self.challenged:
            await interaction.response.send_message(f"❌ Only leaders of **{self.challenged}** can decline.", ephemeral=True)
            return

        for c in squad_data["challenges"]:
            if c["id"] == self.challenge_id and c["status"] == "pending":
                c["status"] = "declined"
                break
        else:
            await interaction.response.send_message("❌ Challenge no longer pending.", ephemeral=True)
            return
        save_data(squad_data)

        embed = discord.Embed(
            title="✋ Challenge Declined",
            description=(
                f"**{SQUADS.get(self.challenged, '?')} {self.challenged}** has declined the challenge from "
                f"**{SQUADS.get(self.challenger, '?')} {self.challenger}**."
            ),
            color=discord.Color.greyple()
        )
        await interaction.response.edit_message(embed=embed, view=None)

        await log_action(interaction.guild, "✋ Challenge Declined",
            f"{interaction.user.mention} (**{self.challenged}**) declined challenge from **{self.challenger}**")


# =====================================================================
#                     BOUNTY BOARD
# =====================================================================

def build_bounty_embed():
    """Build the bounty board embed."""
    bounties = squad_data.get("bounties", {})
    embed = discord.Embed(
        title="💰 Bounty Board",
        description="*Defeat these kingdoms to earn bonus Glory Points!*\n\nBounties are auto-placed on the top 3 ranked kingdoms. Claim them by winning!",
        color=ROYAL_GOLD
    )
    if not bounties:
        embed.add_field(name="🏜️ No Active Bounties", value="The board is empty... for now.", inline=False)
    else:
        for name, info in sorted(bounties.items(), key=lambda x: x[1]["points"], reverse=True):
            rank = get_squad_rank(name)
            rank_text = f"#{rank}" if rank else "?"
            tier = "🔴" if info["points"] >= 3 else "🟡" if info["points"] >= 2 else "🟢"
            embed.add_field(
                name=f"{tier} {SQUADS.get(name, '?')} {name} — **+{info['points']} pts**",
                value=f"📊 Rank: **{rank_text}** | {info['reason']}\n💰 Beat them to claim **+{info['points']}** bonus Glory Points!",
                inline=False
            )
    embed.set_footer(text="⚜️ Bounties refresh after each match | Top 3 always have bounties")
    return embed


class BountyBoardView(View):
    """View for bounty board — members can view, mods can set manual bounties."""
    def __init__(self, is_mod=False):
        super().__init__(timeout=180)
        self.is_mod = is_mod
        if is_mod:
            pass  # Add manual bounty button for mods

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh_btn(self, interaction: discord.Interaction, button: Button):
        refresh_bounties()
        save_data(squad_data)
        await interaction.response.edit_message(embed=build_bounty_embed(), view=BountyBoardView())


class SetBountySquadView(View):
    """Mod: select squad to place manual bounty on."""
    def __init__(self, page=1):
        super().__init__(timeout=180)
        self.page = page
        all_squads = sorted(SQUADS.items())
        if not all_squads:
            return
        start = (page - 1) * 25
        end = start + 25
        page_squads = all_squads[start:end]
        if not page_squads:
            return

        options = [discord.SelectOption(label=str(n)[:100], value=str(n)[:100], description=f"Tag: {t}"[:100]) for n, t in page_squads]
        select = Select(placeholder="💰 Select kingdom for bounty...", options=options)
        select.callback = self.selected
        self.add_item(select)

    async def selected(self, interaction):
        target = interaction.data["values"][0]
        await interaction.response.send_modal(SetBountyModal(target))


class SetBountyModal(Modal, title="💰 Set Bounty"):
    bounty_points = TextInput(label="Bonus Points (1-5)", placeholder="e.g., 3", required=True, max_length=1)
    bounty_reason = TextInput(label="Reason", placeholder="e.g., 5-win streak domination", required=False, max_length=100)

    def __init__(self, target_name):
        super().__init__()
        self.target_name = target_name

    async def on_submit(self, interaction: discord.Interaction):
        try:
            pts = int(self.bounty_points.value)
            if pts < 1 or pts > 5:
                raise ValueError
        except:
            await interaction.response.send_message("❌ Points must be 1-5.", ephemeral=True)
            return

        reason = self.bounty_reason.value.strip() if self.bounty_reason.value else "Manual bounty"
        squad_data["bounties"][self.target_name] = {
            "points": pts,
            "reason": f"🎯 {reason}",
            "placed_by": str(interaction.user.id),
            "date": datetime.utcnow().isoformat()
        }
        save_data(squad_data)

        embed = discord.Embed(
            title="💰 Bounty Placed!",
            description=f"**+{pts} Glory Points** bounty on **{SQUADS.get(self.target_name, '?')} {self.target_name}**\n\n*{reason}*",
            color=ROYAL_GOLD
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Announce
        pub_embed = discord.Embed(
            title="💰 NEW BOUNTY!",
            description=f"A **+{pts} Glory Point** bounty has been placed on **{SQUADS.get(self.target_name, '?')} {self.target_name}**!\n\n*{reason}*\n\n⚔️ Defeat them to claim the bonus!",
            color=ROYAL_GOLD
        )
        await announce_challenge(interaction.guild, pub_embed)
        await log_action(interaction.guild, "💰 Bounty Set",
            f"{interaction.user.mention} placed **+{pts}** bounty on **{self.target_name}**: {reason}")


# =====================================================================
#                     WEEKLY DIGEST (Auto-post Sunday)
# =====================================================================

@tasks.loop(hours=1)
async def weekly_digest_task():
    """Check every hour if it's Sunday 18:00 UTC — post weekly digest."""
    now = datetime.utcnow()
    if now.weekday() != 6 or now.hour != 18:  # Sunday = 6, 18:00 UTC
        return

    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name=ANNOUNCE_CHANNEL_NAME)
        if not channel:
            continue

        rankings = get_squad_ranking()
        if not rankings:
            continue

        # Gather stats for the week (last 7 days)
        week_ago = datetime.utcnow().timestamp() - (7 * 86400)
        week_matches = []
        for m in squad_data["matches"]:
            try:
                md = datetime.fromisoformat(m["date"]).timestamp()
                if md >= week_ago:
                    week_matches.append(m)
            except:
                pass

        embed = discord.Embed(
            title="📰 WEEKLY REALM DIGEST",
            description=f"*Week of {now.strftime('%B %d, %Y')}*\n⚔️ **{len(week_matches)}** battles fought this week!",
            color=ROYAL_GOLD
        )

        # Top 3 kingdoms
        top3 = ""
        for r in rankings[:3]:
            medal = "🥇" if r["rank"] == 1 else "🥈" if r["rank"] == 2 else "🥉"
            top3 += f"{medal} **{r['tag']} {r['name']}** — {r['points']} pts ({r['wins']}W-{r['losses']}L)\n"
        embed.add_field(name="👑 Top 3 Kingdoms", value=top3 or "No data", inline=False)

        # Week's biggest mover — most wins this week
        week_wins = {}
        for m in week_matches:
            try:
                s1, s2 = map(int, m["score"].split("-"))
                if s1 > s2:
                    week_wins[m["team1"]] = week_wins.get(m["team1"], 0) + 1
                elif s2 > s1:
                    week_wins[m["team2"]] = week_wins.get(m["team2"], 0) + 1
            except:
                pass
        if week_wins:
            hot_name = max(week_wins, key=week_wins.get)
            embed.add_field(
                name="🔥 Hottest This Week",
                value=f"**{SQUADS.get(hot_name, '?')} {hot_name}** — {week_wins[hot_name]} wins this week!",
                inline=False
            )

        # Active streaks
        streak_text = ""
        for sn in SQUADS:
            si = squad_data["squads"].get(sn, {})
            cs = si.get("current_streak", {})
            if cs.get("count", 0) >= 3:
                se = "🔥" if cs["type"] == "win" else "❄️" if cs["type"] == "loss" else "⚡"
                streak_text += f"{se} **{SQUADS.get(sn, '?')} {sn}** — {cs['count']} {cs['type']} streak\n"
        if streak_text:
            embed.add_field(name="📊 Active Streaks", value=streak_text, inline=False)

        # Active challenges
        active_challenges = get_active_challenges()
        if active_challenges:
            ch_text = ""
            for c in active_challenges[:3]:
                status_emoji = "⏳" if c["status"] == "pending" else "⚔️"
                ch_text += f"{status_emoji} **{c['challenger']}** vs **{c['challenged']}** — {c['status'].upper()}\n"
            embed.add_field(name="🎯 Active Challenges", value=ch_text, inline=False)

        # Bounties
        bounties = squad_data.get("bounties", {})
        if bounties:
            b_text = ""
            for name, info in list(bounties.items())[:3]:
                b_text += f"💰 **{SQUADS.get(name, '?')} {name}** — +{info['points']} pts bounty\n"
            embed.add_field(name="💰 Active Bounties", value=b_text, inline=False)

        embed.set_footer(text="⚜️ Majestic Weekly Digest | Published every Sunday")

        try:
            await channel.send(embed=embed)
        except:
            pass


@weekly_digest_task.before_loop
async def before_weekly_digest():
    await bot.wait_until_ready()


# =====================================================================
#                     PANEL VIEWS — THE 3 MAIN CATEGORIES
# =====================================================================

# -------------------- HELPER: show profile embed builder --------------------
def build_profile_embed(member: discord.Member, guild: discord.Guild):
    """Build a profile embed for any member. Returns (embed, found_bool)."""
    pk = str(member.id)
    pd = squad_data["players"].get(pk)
    if not pd or not pd.get("ingame_name"):
        embed = discord.Embed(
            title="⚜️ Profile Not Found",
            description=f"{member.mention} hasn't set up their profile yet.",
            color=ROYAL_BLUE
        )
        embed.add_field(name="💡 How to Create", value="Use `/member` → **Setup Profile** to create yours!", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        return embed, False

    sn = pd.get("squad")
    sr = None; st = "?"
    if sn and sn in SQUADS:
        st = SQUADS.get(sn, "?")
        sr = discord.utils.get(guild.roles, name=sn)

    stats = get_player_stats(member.id)
    power, rank_info = calculate_power_rating(member.id)

    rs = "⚔️ Warrior"
    if sn and sn in squad_data["squads"]:
        si = squad_data["squads"][sn]
        if member.id in si.get("main_roster", []):
            rs = "⭐ Main Roster"
        elif member.id in si.get("subs", []):
            rs = "🔄 Substitute"

    embed = discord.Embed(
        title=f"⚜️ {pd.get('ingame_name', 'Unknown')}",
        description=f"{member.mention}'s warrior profile\n{rank_info[1]} — *{rank_info[2]}*",
        color=sr.color if sr else ROYAL_BLUE
    )
    embed.add_field(name="⚔️ IGN", value=pd.get('ingame_name', '?'), inline=True)
    embed.add_field(name="🎯 ID", value=f"#{pd.get('ingame_id', '?')}", inline=True)
    embed.add_field(name="🏆 Rank", value=pd.get('highest_rank', '?'), inline=True)

    role = pd.get('role', '?')
    embed.add_field(name="💼 Position", value=f"{ROLE_EMOJIS.get(role, '⚔️')} {role}", inline=True)
    embed.add_field(name="💪 Power Rating", value=f"**{power}/100** {'█' * (power // 10)}{'░' * (10 - power // 10)}", inline=True)

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
            name="📊 Battle Record",
            value=f"⚔️ {stats['matches_played']} battles | 🏆 {stats['wins']}W ⚔️ {stats['draws']}D 💀 {stats['losses']}L | **{stats['win_rate']:.1f}%** WR",
            inline=False
        )

    if is_leader(member):
        embed.add_field(name="👑 Status", value="**LEADER**", inline=False)

    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="⚜️ Majestic Archives")
    return embed, True


# -------------------- SEARCH MEMBER MODAL SYSTEM --------------------
class SearchMemberModal(Modal, title="🔍 Search Member"):
    """Modal that takes a search query and shows matching members."""
    search_query = TextInput(
        label="Enter name, display name, or ID",
        placeholder="e.g., John, Shadow, 123456789",
        required=True,
        max_length=100
    )

    def __init__(self, purpose: str, **kwargs):
        super().__init__()
        self.purpose = purpose  # "view_profile", "add_member", "give_guest"
        self.extra = kwargs     # squad_name, squad_role, etc.
        # Custom titles per purpose
        if purpose == "view_profile":
            self.title = "👤 Search Warrior Profile"
            self.search_query.label = "Who do you seek?"
            self.search_query.placeholder = "Enter their name or ID..."
        elif purpose == "add_member":
            self.title = "➕ Search Warrior to Recruit"
            self.search_query.label = "Who shall join your ranks?"
            self.search_query.placeholder = "Enter their name or ID..."
        elif purpose == "give_guest":
            self.title = "🎭 Search Guest to Honor"
            self.search_query.label = "Who deserves guest access?"
            self.search_query.placeholder = "Enter their name or ID..."

    async def on_submit(self, interaction: discord.Interaction):
        results = search_members(interaction.guild, self.search_query.value)

        if not results:
            embed = discord.Embed(
                title="🔍 No Warriors Found",
                description=f"No members matching **{self.search_query.value}** were found.\nTry a different name or check the spelling!",
                color=ROYAL_RED
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if len(results) == 1:
            # Single match — act immediately
            member = results[0]
            await self._execute_action(interaction, member)
        else:
            # Multiple matches — show selector
            view = SearchResultSelectorView(results, self.purpose, **self.extra)
            embed = discord.Embed(
                title=f"🔍 Found {len(results)} Warriors",
                description=f"Multiple matches for **{self.search_query.value}**\nSelect the correct warrior below:",
                color=ROYAL_BLUE
            )
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def _execute_action(self, interaction, member):
        if self.purpose == "view_profile":
            embed, _ = build_profile_embed(member, interaction.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif self.purpose == "add_member":
            squad_name = self.extra.get("squad_name")
            squad_role = self.extra.get("squad_role")
            guild = interaction.guild

            # Check if already in this squad
            existing_role, _ = get_member_squad(member, guild)
            if existing_role and existing_role.name == squad_name:
                await interaction.response.send_message(
                    f"⚠️ {member.mention} is already in **{squad_name}**!", ephemeral=True)
                return

            # Remove any old squad role
            for sn in SQUADS:
                role = discord.utils.get(guild.roles, name=sn)
                if role and role in member.roles:
                    await member.remove_roles(role)

            await member.add_roles(squad_role)
            await safe_nick_update(member, squad_role, SQUADS.get(squad_name, "?"))
            update_player_squad(member.id, squad_name, existing_role.name if existing_role else None)

            quote = random.choice(RECRUIT_QUOTES)
            embed = discord.Embed(
                title="➕ Warrior Recruited!",
                description=f"{member.mention} has joined **{SQUADS.get(squad_name, "?")} {squad_name}**!\n\n*{quote}*",
                color=ROYAL_GREEN
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await log_action(guild, "➕ Member Added", f"{interaction.user.mention} recruited {member.mention} to **{squad_name}**")

        elif self.purpose == "give_guest":
            squad_name = self.extra.get("squad_name")
            grn = GUEST_ROLES.get(squad_name)
            if not grn:
                await interaction.response.send_message("❌ No guest role configured for this kingdom.", ephemeral=True)
                return
            gr = discord.utils.get(interaction.guild.roles, name=grn)
            if not gr:
                await interaction.response.send_message(f"❌ Guest role '{grn}' not found in server.", ephemeral=True)
                return

            if gr in member.roles:
                await interaction.response.send_message(
                    f"⚠️ {member.mention} already has guest access to **{squad_name}**!", ephemeral=True)
                return

            await member.add_roles(gr)
            quote = random.choice(GUEST_QUOTES)
            embed = discord.Embed(
                title="🎭 Guest Access Granted!",
                description=f"{member.mention} is now a guest of **{SQUADS.get(squad_name, "?")} {squad_name}**!\n\n*{quote}*",
                color=ROYAL_GREEN
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await log_action(interaction.guild, "🎭 Guest Added", f"{interaction.user.mention} gave {member.mention} guest access to **{squad_name}**")


class SearchResultSelectorView(View):
    """Dropdown to pick from multiple search results."""
    def __init__(self, members: list, purpose: str, **kwargs):
        super().__init__(timeout=120)
        self.purpose = purpose
        self.extra = kwargs
        self.member_map = {}

        options = []
        for m in members[:25]:
            self.member_map[str(m.id)] = m
            role, tag = get_member_squad(m, m.guild)
            squad_info = f"{tag} {role.name}" if role else "Free Agent"
            options.append(discord.SelectOption(
                label=m.display_name[:100],
                value=str(m.id),
                description=f"@{m.name} • {squad_info}"[:100],
                emoji="👤"
            ))

        select = Select(placeholder="👤 Select the warrior...", options=options)
        select.callback = self.member_selected
        self.add_item(select)

    async def member_selected(self, interaction):
        member_id = interaction.data["values"][0]
        member = self.member_map.get(member_id)
        if not member:
            member = interaction.guild.get_member(int(member_id))
        if not member:
            await interaction.response.edit_message(content="❌ Member not found.", embed=None, view=None)
            return

        # Create a temporary modal-like object to reuse the execute logic
        handler = SearchMemberModal.__new__(SearchMemberModal)
        handler.purpose = self.purpose
        handler.extra = self.extra
        await handler._execute_action(interaction, member)


# -------------------- 1. MAJESTIC MEMBER PANEL --------------------
class MemberPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Browse Kingdoms", style=discord.ButtonStyle.primary, emoji="🏰", row=0)
    async def browse_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
        title="🏰 Kingdom Explorer",
        description="Select a kingdom from the menu below to browse its profile.",
        color=ROYAL_GOLD
    )
        view = SquadSelectorView(purpose="browse")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await log_action(interaction.guild, "🏰 Browse", f"{interaction.user.mention} opened **Kingdom Explorer**")

    @discord.ui.button(label="Rankings", style=discord.ButtonStyle.secondary, emoji="🏆", row=0)
    async def rankings_btn(self, interaction: discord.Interaction, button: Button):
        rankings = get_squad_ranking()
        tp = (len(rankings) + 14) // 15
        embed = discord.Embed(title="🏆 Leaderboard", description=f"Page 1/{tp}", color=ROYAL_GOLD)
        for s in rankings[:15]:
            i = s["rank"]
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            embed.add_field(name=f"{medal} {s['tag']} {s['name']}", value=f"💎 **{s['points']}** glory | {s['wins']}W-{s['draws']}D-{s['losses']}L | **{s['win_rate']:.1f}%** WR", inline=False)
        embed.set_footer(text=f"All {len(rankings)} kingdoms")
        view = RankingsView(page=1) if tp > 1 else None
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await log_action(interaction.guild, "🏆 Rankings", f"{interaction.user.mention} viewed **Leaderboard**")

    @discord.ui.button(label="View Profile", emoji="👤", style=discord.ButtonStyle.primary, row=0)
    async def view_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SearchMemberModal("view_profile"))
        await log_action(interaction.guild, "👤 View Profile", f"{interaction.user.mention} searched a **warrior profile**")

    @discord.ui.button(label="My Kingdom", style=discord.ButtonStyle.success, emoji="🛡️", row=1)
    async def my_squad_btn(self, interaction: discord.Interaction, button: Button):
        role, tag = get_member_squad(interaction.user, interaction.guild)
        if not role:
            await interaction.response.send_message("❌ You're not in any kingdom.", ephemeral=True)
            return
        await show_squad_info(interaction, role, role.name, tag, public=False)
        await log_action(interaction.guild, "🛡️ My Kingdom", f"{interaction.user.mention} viewed their kingdom **{role.name}**")

    @discord.ui.button(label="My Profile", style=discord.ButtonStyle.success, emoji="⚜️", row=1)
    async def my_profile_btn(self, interaction: discord.Interaction, button: Button):
        await show_player_profile(interaction, interaction.user, public=False)
        await log_action(interaction.guild, "⚜️ My Profile", f"{interaction.user.mention} viewed their **own profile**")

    @discord.ui.button(label="Setup Profile", style=discord.ButtonStyle.primary, emoji="⚙️", row=1)
    async def setup_btn(self, interaction: discord.Interaction, button: Button):
        role, _ = get_member_squad(interaction.user, interaction.guild)
        sn = role.name if role else "Free Agent"
        view = RoleSelectView(interaction.user.id, sn)
        embed = discord.Embed(title="⚙️ Profile Setup", description="Choose your battle position first:", color=ROYAL_PURPLE)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await log_action(interaction.guild, "⚙️ Setup", f"{interaction.user.mention} started **Profile Setup**")

    @discord.ui.button(label="Fun Stats", style=discord.ButtonStyle.secondary, emoji="🎲", row=2)
    async def fun_btn(self, interaction: discord.Interaction, button: Button):
        await show_fun_stats(interaction)
        await log_action(interaction.guild, "🎲 Fun Stats", f"{interaction.user.mention} viewed **Fun Stats**")

    @discord.ui.button(label="War Oracle", style=discord.ButtonStyle.primary, emoji="🔮", row=2)
    async def oracle_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🔮 War Oracle — Match Predictor",
            description="The Oracle will analyze two kingdoms and predict the outcome!\n\nSelect the **first** kingdom:",
            color=ROYAL_PURPLE
        )
        await interaction.response.send_message(embed=embed, view=MatchPredictorStep1View(), ephemeral=True)
        await log_action(interaction.guild, "🔮 War Oracle", f"{interaction.user.mention} consulted the **War Oracle**")

    @discord.ui.button(label="Realm News", style=discord.ButtonStyle.success, emoji="📰", row=2)
    async def news_btn(self, interaction: discord.Interaction, button: Button):
        headlines = generate_realm_news()
        embed = discord.Embed(
            title="📰 Majestic Realm News",
            description="*The latest from the chronicles of war!*",
            color=ROYAL_GOLD
        )
        for i, headline in enumerate(headlines[:6]):
            embed.add_field(name=f"{'📌' if i == 0 else '📄'} {'BREAKING' if i == 0 else f'Story #{i+1}'}", value=headline, inline=False)

        embed.set_footer(text=f"📰 Published {datetime.utcnow().strftime('%b %d, %Y %H:%M')} UTC | Majestic Press")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(interaction.guild, "📰 Realm News", f"{interaction.user.mention} read **Realm News**")

    @discord.ui.button(label="Bounties", style=discord.ButtonStyle.primary, emoji="💰", row=3)
    async def bounty_btn(self, interaction: discord.Interaction, button: Button):
        refresh_bounties()
        save_data(squad_data)
        await interaction.response.send_message(embed=build_bounty_embed(), view=BountyBoardView(), ephemeral=True)
        await log_action(interaction.guild, "💰 Bounties", f"{interaction.user.mention} viewed **Bounty Board**")

    @discord.ui.button(label="Challenges", style=discord.ButtonStyle.secondary, emoji="🎯", row=3)
    async def challenges_btn(self, interaction: discord.Interaction, button: Button):
        active = get_active_challenges()
        embed = discord.Embed(title="🎯 Active War Challenges", color=ROYAL_RED)
        if not active:
            embed.description = "*No active challenges right now. Leaders can issue challenges from their panel!*"
        else:
            for c in active[:10]:
                status = "⏳ PENDING" if c["status"] == "pending" else "⚔️ ACCEPTED — Battle is ON!"
                ds = ""
                try:
                    ds = datetime.fromisoformat(c["date"]).strftime("%b %d")
                except:
                    pass
                msg_text = f"\n📜 *\"{c['message']}\"*" if c.get("message") else ""
                embed.add_field(
                    name=f"{SQUADS.get(c['challenger'], '?')} {c['challenger']} vs {SQUADS.get(c['challenged'], '?')} {c['challenged']}",
                    value=f"{status}{msg_text}\n📅 {ds} | 🆔 `{c['id']}`",
                    inline=False
                )
        embed.set_footer(text="⚜️ Leaders issue challenges from /leader panel")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Leave Kingdom", style=discord.ButtonStyle.danger, emoji="🚪", row=4)
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
            embed.add_field(name=f"{medal} {s['tag']} {s['name']}", value=f"💎 **{s['points']}** glory | {s['wins']}W-{s['draws']}D-{s['losses']}L | **{s['win_rate']:.1f}%** WR", inline=False)
        await interaction.response.edit_message(embed=embed, view=RankingsView(page=page))


# -------------------- 2. MAJESTIC LEADER PANEL --------------------
class LeaderPanelView(View):
    def __init__(self, squad_role, tag, squad_name, guest_role):
        super().__init__(timeout=None)
        self.squad_role = squad_role
        self.tag = tag
        self.squad_name = squad_name
        self.guest_role = guest_role

    @discord.ui.button(label="Add Member", emoji="➕", style=discord.ButtonStyle.success, row=0)
    async def add_member_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            SearchMemberModal("add_member", squad_name=self.squad_name, squad_role=self.squad_role)
        )

    @discord.ui.button(label="Remove Member", emoji="➖", style=discord.ButtonStyle.danger, row=0)
    async def rm_btn(self, interaction: discord.Interaction, button: Button):
        v = MemberSelectorView("remove_member", self.squad_role, self.squad_name, interaction.guild)
        e = discord.Embed(title="➖ Remove Warrior", description="Select a member to remove:", color=ROYAL_RED)
        await interaction.response.send_message(embed=e, view=v, ephemeral=True)

    @discord.ui.button(label="View Kingdom", emoji="🏰", style=discord.ButtonStyle.primary, row=0)
    async def view_btn(self, interaction: discord.Interaction, button: Button):
        await show_squad_info(interaction, self.squad_role, self.squad_name, self.tag, public=False)
        await log_action(interaction.guild, "🏰 View Kingdom", f"{interaction.user.mention} viewed **{self.squad_name}** (leader)")

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

    @discord.ui.button(label="Give Guest", emoji="🎭", style=discord.ButtonStyle.success, row=3)
    async def give_guest_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            SearchMemberModal("give_guest", squad_name=self.squad_name)
        )

    @discord.ui.button(label="Remove Guest", emoji="❌", style=discord.ButtonStyle.secondary, row=3)
    async def rm_guest_btn(self, interaction: discord.Interaction, button: Button):
        v = MemberSelectorView("remove_guest", self.squad_role, self.squad_name, interaction.guild)
        e = discord.Embed(title="❌ Revoke Guest", description="Select to remove:", color=ROYAL_PURPLE)
        await interaction.response.send_message(embed=e, view=v, ephemeral=True)

    @discord.ui.button(label="Set Logo", emoji="🖼️", style=discord.ButtonStyle.primary, row=4)
    async def logo_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SetLogoModal(self.squad_name))

    @discord.ui.button(label="Challenge", emoji="⚔️", style=discord.ButtonStyle.danger, row=4)
    async def challenge_btn(self, interaction: discord.Interaction, button: Button):
        active = get_active_challenges(self.squad_name)
        if len(active) >= 3:
            await interaction.response.send_message("❌ You have too many active challenges (max 3).", ephemeral=True)
            return
        embed = discord.Embed(
            title="⚔️ Issue a War Challenge",
            description=f"**{SQUADS.get(self.squad_name, '?')} {self.squad_name}** wants to fight!\n\nSelect the kingdom to challenge:",
            color=ROYAL_RED
        )
        await interaction.response.send_message(embed=embed, view=ChallengeStep1View(self.squad_name), ephemeral=True)
        await log_action(interaction.guild, "⚔️ Challenge", f"{interaction.user.mention} started a **Challenge** from **{self.squad_name}**")


# -------------------- 3. MODERATOR PANEL (Selector-based) --------------------

# --- Record Battle: Step 1 pick team1, Step 2 pick team2, Step 3 enter score ---
class RecordBattleStep1View(View):
    """Step 1: Select first kingdom"""
    def __init__(self, page=1):
        super().__init__(timeout=180)
        all_squads = sorted(SQUADS.items())
        start = (page - 1) * 25
        end = start + 25
        page_squads = all_squads[start:end]
        self.page = page

        options = [discord.SelectOption(label=n, value=n, emoji="🏰", description=f"Tag: {t}") for n, t in page_squads]
        select = Select(placeholder="⚔️ Select FIRST kingdom...", options=options)
        select.callback = self.team1_selected
        self.add_item(select)

        if len(all_squads) > 25:
            if page > 1:
                b = Button(label="← Prev", style=discord.ButtonStyle.secondary); b.callback = self.prev; self.add_item(b)
            if end < len(all_squads):
                b = Button(label="Next →", style=discord.ButtonStyle.secondary); b.callback = self.nxt; self.add_item(b)

    async def prev(self, i): await i.response.edit_message(view=RecordBattleStep1View(self.page - 1))
    async def nxt(self, i): await i.response.edit_message(view=RecordBattleStep1View(self.page + 1))

    async def team1_selected(self, interaction):
        team1 = interaction.data["values"][0]
        embed = discord.Embed(
            title="⚔️ Record Battle — Step 2/3",
            description=f"✅ First Kingdom: **{SQUADS.get(team1, "?")} {team1}**\n\nNow select the **second** kingdom:",
            color=ROYAL_BLUE
        )
        await interaction.response.edit_message(embed=embed, view=RecordBattleStep2View(team1))


class RecordBattleStep2View(View):
    """Step 2: Select second kingdom"""
    def __init__(self, team1, page=1):
        super().__init__(timeout=180)
        self.team1 = team1
        self.page = page
        all_squads = sorted(SQUADS.items())
        start = (page - 1) * 25
        end = start + 25
        page_squads = all_squads[start:end]

        options = [discord.SelectOption(label=n, value=n, emoji="🏰", description=f"Tag: {t}") for n, t in page_squads]
        select = Select(placeholder="⚔️ Select SECOND kingdom...", options=options)
        select.callback = self.team2_selected
        self.add_item(select)

        if len(all_squads) > 25:
            if page > 1:
                b = Button(label="← Prev", style=discord.ButtonStyle.secondary); b.callback = self.prev; self.add_item(b)
            if end < len(all_squads):
                b = Button(label="Next →", style=discord.ButtonStyle.secondary); b.callback = self.nxt; self.add_item(b)

    async def prev(self, i): await i.response.edit_message(view=RecordBattleStep2View(self.team1, self.page - 1))
    async def nxt(self, i): await i.response.edit_message(view=RecordBattleStep2View(self.team1, self.page + 1))

    async def team2_selected(self, interaction):
        team2 = interaction.data["values"][0]
        if team2 == self.team1:
            await interaction.response.edit_message(content="❌ A kingdom cannot battle itself! Pick a different one.", embed=None, view=RecordBattleStep2View(self.team1, self.page))
            return

        # Show AI prediction before score entry
        pred = predict_match(self.team1, team2)
        t1_bar = "🟦" * (pred["t1_pct"] // 10) + "⬜" * (10 - pred["t1_pct"] // 10)
        t2_bar = "🟥" * (pred["t2_pct"] // 10) + "⬜" * (10 - pred["t2_pct"] // 10)

        embed = discord.Embed(
            title=f"🔮 Pre-Battle Oracle",
            description=(
                f"**{SQUADS.get(self.team1, "?")} {self.team1}** ⚔️ **{SQUADS.get(team2, "?")} {team2}**\n\n"
                f"{pred['narrative']}\n\n"
                f"🟦 {self.team1}: **{pred['t1_pct']}%** {t1_bar}\n"
                f"🟥 {team2}: **{pred['t2_pct']}%** {t2_bar}\n"
                f"⚖️ Draw: **{pred['draw_pct']}%**\n\n"
                f"📡 Confidence: {pred['confidence']}"
            ),
            color=ROYAL_PURPLE
        )
        embed.set_footer(text="Click below to enter the actual score!")

        # Continue button that opens the score modal
        view = View(timeout=120)
        continue_btn = Button(label="📝 Enter Score", style=discord.ButtonStyle.success, emoji="⚔️")
        async def open_score_modal(btn_interaction):
            await btn_interaction.response.send_modal(RecordBattleScoreModal(self.team1, team2))
        continue_btn.callback = open_score_modal
        view.add_item(continue_btn)

        await interaction.response.edit_message(embed=embed, view=view)


class RecordBattleScoreModal(Modal, title="⚔️ Enter Battle Score"):
    result = TextInput(label="Score (team1-team2)", placeholder="e.g., 2-0, 1-1, 0-2", required=True, max_length=10)

    def __init__(self, team1: str, team2: str):
        super().__init__()
        self.team1_name = team1
        self.team2_name = team2
        self.result.label = f"{SQUADS.get(team1, "?")} vs {SQUADS.get(team2, "?")} score"

    async def on_submit(self, interaction: discord.Interaction):
        try:
            score1, score2 = map(int, self.result.value.split('-'))
        except:
            await interaction.response.send_message("❌ Invalid format. Use X-Y (e.g., 2-0)", ephemeral=True)
            return

        # Pre-match prediction (before stats change)
        pred = predict_match(self.team1_name, self.team2_name)

        team1_data = squad_data["squads"][self.team1_name]
        team2_data = squad_data["squads"][self.team2_name]

        glory_tags_t1 = []
        glory_tags_t2 = []
        t1_pts = 0
        t2_pts = 0

        if score1 > score2:
            t1_pts, t2_pts, glory_tags_t1, glory_tags_t2 = calculate_glory_points(
                self.team1_name, self.team2_name, score1, score2)
            team1_data["wins"] += 1; team1_data["points"] += t1_pts; team2_data["losses"] += 1
            team1_streak = update_streak(self.team1_name, "win")
            team2_streak = update_streak(self.team2_name, "loss")
            result_text = f"🏆 **{self.team1_name}** has conquered **{self.team2_name}** in glorious battle!"
            flavor_quote = random.choice(VICTORY_QUOTES)
            actual_winner = self.team1_name
        elif score2 > score1:
            t2_pts, t1_pts, glory_tags_t2, glory_tags_t1 = calculate_glory_points(
                self.team2_name, self.team1_name, score2, score1)
            team2_data["wins"] += 1; team2_data["points"] += t2_pts; team1_data["losses"] += 1
            team1_streak = update_streak(self.team1_name, "loss")
            team2_streak = update_streak(self.team2_name, "win")
            result_text = f"🏆 **{self.team2_name}** has conquered **{self.team1_name}** in glorious battle!"
            flavor_quote = random.choice(VICTORY_QUOTES)
            actual_winner = self.team2_name
        else:
            t1_pts = 1; t2_pts = 1
            team1_data["draws"] += 1; team1_data["points"] += 1
            team2_data["draws"] += 1; team2_data["points"] += 1
            team1_streak = update_streak(self.team1_name, "draw")
            team2_streak = update_streak(self.team2_name, "draw")
            result_text = f"⚔️ **{self.team1_name}** and **{self.team2_name}** fought to an honorable stalemate!"
            flavor_quote = random.choice(DRAW_QUOTES)
            actual_winner = "draw"

        # Refresh bounties after match
        refresh_bounties()

        # Auto-complete any active challenge between these two
        for c in squad_data.get("challenges", []):
            if c["status"] == "accepted":
                if (c["challenger"] == self.team1_name and c["challenged"] == self.team2_name) or \
                   (c["challenger"] == self.team2_name and c["challenged"] == self.team1_name):
                    c["status"] = "completed"

        team1_achievements = check_achievements(self.team1_name)
        team2_achievements = check_achievements(self.team2_name)
        match_id = str(uuid.uuid4())[:8]
        team1_participants = get_match_participants(self.team1_name)
        team2_participants = get_match_participants(self.team2_name)

        match_data = {
            "match_id": match_id, "team1": self.team1_name, "team2": self.team2_name,
            "score": self.result.value, "date": datetime.utcnow().isoformat(),
            "added_by": interaction.user.id,
            "team1_participants": team1_participants, "team2_participants": team2_participants,
            "t1_pts": t1_pts, "t2_pts": t2_pts
        }
        squad_data["matches"].append(match_data)
        team1_data["match_history"].append(match_data)
        team2_data["match_history"].append(match_data)
        save_data(squad_data)

        embed = discord.Embed(title="📜 Battle Chronicles Updated", description=f"{result_text}\n\n*{flavor_quote}*", color=ROYAL_GOLD)
        embed.add_field(name="🆔 Match ID", value=f"`{match_id}`", inline=False)
        embed.add_field(name="⚔️ Score", value=f"**{self.result.value}**", inline=True)

        t1i = f"💎 {team1_data['points']} pts (**+{t1_pts}**) | 🏆 {team1_data['wins']}W ⚔️ {team1_data['draws']}D 💀 {team1_data['losses']}L"
        if glory_tags_t1:
            t1i += "\n" + " ".join(glory_tags_t1)
        if team1_streak["count"] >= 3:
            se = "🔥" if team1_streak["type"] == "win" else "❄️" if team1_streak["type"] == "loss" else "⚡"
            t1i += f"\n{se} **{team1_streak['count']} {team1_streak['type'].upper()} STREAK!**"
        embed.add_field(name=f"{SQUADS.get(self.team1_name, "?")} {self.team1_name}", value=t1i, inline=False)

        t2i = f"💎 {team2_data['points']} pts (**+{t2_pts}**) | 🏆 {team2_data['wins']}W ⚔️ {team2_data['draws']}D 💀 {team2_data['losses']}L"
        if glory_tags_t2:
            t2i += "\n" + " ".join(glory_tags_t2)
        if team2_streak["count"] >= 3:
            se = "🔥" if team2_streak["type"] == "win" else "❄️" if team2_streak["type"] == "loss" else "⚡"
            t2i += f"\n{se} **{team2_streak['count']} {team2_streak['type'].upper()} STREAK!**"
        embed.add_field(name=f"{SQUADS.get(self.team2_name, "?")} {self.team2_name}", value=t2i, inline=False)

        if team1_achievements or team2_achievements:
            at = ""
            if team1_achievements:
                at += f"🎖️ **{self.team1_name}** earned:\n"
                for a in team1_achievements: at += f"{a['name']} - *{a['desc']}*\n"
            if team2_achievements:
                at += f"🎖️ **{self.team2_name}** earned:\n"
                for a in team2_achievements: at += f"{a['name']} - *{a['desc']}*\n"
            embed.add_field(name="🏅 New Achievements!", value=at, inline=False)

        # Oracle verdict — was the prediction correct?
        predicted_winner = self.team1_name if pred["t1_pct"] > pred["t2_pct"] else self.team2_name if pred["t2_pct"] > pred["t1_pct"] else "draw"
        if actual_winner == "draw" and pred["draw_pct"] >= 20:
            oracle_text = "🔮✅ The Oracle sensed the balance of power — **Draw predicted!**"
        elif predicted_winner == actual_winner:
            oracle_text = f"🔮✅ The Oracle was **RIGHT!** Predicted {predicted_winner} to win ({max(pred['t1_pct'], pred['t2_pct'])}% confidence)"
        else:
            oracle_text = f"🔮❌ The Oracle was **WRONG!** Predicted {predicted_winner} ({max(pred['t1_pct'], pred['t2_pct'])}%) — fate had other plans!"
        embed.add_field(name="🔮 Oracle Verdict", value=oracle_text, inline=False)

        embed.set_footer(text=f"Match ID: {match_id} | May glory follow the victorious!")
        await interaction.response.send_message(embed=embed)
        await log_action(interaction.guild, "📜 Battle Recorded",
            f"{interaction.user.mention} recorded: {self.team1_name} vs {self.team2_name} ({self.result.value}) | ID: {match_id}")

        # --- Public announcement in #war-results ---
        pub_embed = discord.Embed(
            title="⚔️ BATTLE RESULT",
            description=f"{result_text}\n\n*{flavor_quote}*",
            color=ROYAL_GOLD if actual_winner != "draw" else ROYAL_BLUE
        )
        pub_embed.add_field(name="📊 Score", value=f"**{SQUADS.get(self.team1_name, '?')} {self.team1_name}** {self.result.value} **{SQUADS.get(self.team2_name, '?')} {self.team2_name}**", inline=False)
        if actual_winner != "draw":
            winner_name = actual_winner
            winner_pts = t1_pts if actual_winner == self.team1_name else t2_pts
            winner_tags = glory_tags_t1 if actual_winner == self.team1_name else glory_tags_t2
            pts_text = f"💎 **+{winner_pts} Glory Points** earned"
            if winner_tags:
                pts_text += "\n" + " ".join(winner_tags)
            pub_embed.add_field(name=f"🏆 {SQUADS.get(winner_name, '?')} {winner_name}", value=pts_text, inline=False)
        pub_embed.add_field(name="🔮 Oracle", value=oracle_text, inline=False)
        pub_embed.set_footer(text=f"Match #{match_id} | {datetime.utcnow().strftime('%b %d, %Y %H:%M')} UTC")
        await announce_match(interaction.guild, pub_embed)


# --- Award Title: Step 1 pick squad, Step 2 enter title + position ---
class AwardTitleSquadView(View):
    """Step 1: Select kingdom to award title"""
    def __init__(self, page=1):
        super().__init__(timeout=180)
        self.page = page
        all_squads = sorted(SQUADS.items())
        start = (page - 1) * 25
        end = start + 25
        page_squads = all_squads[start:end]

        options = [discord.SelectOption(label=n, value=n, emoji="🏰", description=f"Tag: {t}") for n, t in page_squads]
        select = Select(placeholder="🏆 Select kingdom to award...", options=options)
        select.callback = self.squad_selected
        self.add_item(select)

        if len(all_squads) > 25:
            if page > 1:
                b = Button(label="← Prev", style=discord.ButtonStyle.secondary); b.callback = self.prev; self.add_item(b)
            if end < len(all_squads):
                b = Button(label="Next →", style=discord.ButtonStyle.secondary); b.callback = self.nxt; self.add_item(b)

    async def prev(self, i): await i.response.edit_message(view=AwardTitleSquadView(self.page - 1))
    async def nxt(self, i): await i.response.edit_message(view=AwardTitleSquadView(self.page + 1))

    async def squad_selected(self, interaction):
        squad = interaction.data["values"][0]
        await interaction.response.send_modal(AwardTitleDetailsModal(squad))


class AwardTitleDetailsModal(Modal, title="🏆 Award Championship Title"):
    title_name = TextInput(label="Title Name", placeholder="e.g., Champion, Tournament Winner", required=True)
    position = TextInput(label="Position", placeholder="e.g., 1st, 2nd, 3rd", required=True, max_length=10)

    def __init__(self, squad_name: str):
        super().__init__()
        self.squad_name = squad_name

    async def on_submit(self, interaction: discord.Interaction):
        squad_info = squad_data["squads"][self.squad_name]
        full_title = f"{self.title_name.value} ({self.position.value} Place)"
        if "titles" not in squad_info: squad_info["titles"] = []
        squad_info["titles"].append(full_title)
        if self.position.value.lower() in ["1st", "first", "1"]:
            squad_info["championship_wins"] = squad_info.get("championship_wins", 0) + 1
        save_data(squad_data)

        pe = "🥇" if self.position.value.lower() in ["1st", "first", "1"] else "🥈" if self.position.value.lower() in ["2nd", "second", "2"] else "🥉"
        embed = discord.Embed(title="🏆 Royal Title Bestowed", description=f"{pe} **{self.squad_name}** has been awarded the title:\n\n**{full_title}**", color=ROYAL_GOLD)
        if self.position.value.lower() in ["1st", "first", "1"]:
            embed.add_field(name="👑 Championship Glory", value=f"Total Championships: **{squad_info['championship_wins']}**", inline=False)
        await interaction.response.send_message(embed=embed)
        await log_action(interaction.guild, "🏆 Title Awarded", f"{interaction.user.mention} awarded **{self.squad_name}** the title: {full_title}")


# --- Delete Match: Select from recent matches ---
class DeleteMatchSelectorView(View):
    """Select a match to delete from recent matches"""
    def __init__(self):
        super().__init__(timeout=180)
        recent = squad_data["matches"][-25:][::-1]
        if not recent:
            return

        options = []
        for m in recent:
            mid = m.get("match_id", "?")
            t1, t2, score = m["team1"], m["team2"], m["score"]
            label = f"{SQUADS.get(t1,'?')} vs {SQUADS.get(t2,'?')} ({score})"[:100]
            try:
                ds = datetime.fromisoformat(m.get("date", "")).strftime("%b %d")
            except:
                ds = "?"
            options.append(discord.SelectOption(label=label, value=mid, description=f"ID: {mid} • {ds}"))

        select = Select(placeholder="🗑️ Select a match to delete...", options=options)
        select.callback = self.match_selected
        self.add_item(select)

    async def match_selected(self, interaction):
        match_id = interaction.data["values"][0]
        idx, match = find_match_by_id(match_id)
        if match is None:
            await interaction.response.edit_message(content=f"❌ Match `{match_id}` not found.", embed=None, view=None)
            return

        t1, t2, score = match["team1"], match["team2"], match["score"]

        # Confirm deletion
        embed = discord.Embed(
            title="⚠️ Confirm Deletion",
            description=f"Delete **{t1}** vs **{t2}** ({score})?\nMatch ID: `{match_id}`",
            color=ROYAL_RED
        )
        view = View(timeout=60)

        async def confirm(ci):
            if ci.user.id != interaction.user.id:
                return await ci.response.send_message("❌ Not yours.", ephemeral=True)
            try:
                s1, s2 = map(int, score.split('-'))
            except:
                await ci.response.edit_message(content="❌ Invalid match data.", embed=None, view=None)
                return

            t1d, t2d = squad_data["squads"][t1], squad_data["squads"][t2]
            stored_t1_pts = squad_data["matches"][idx].get("t1_pts", 2)
            stored_t2_pts = squad_data["matches"][idx].get("t2_pts", 2)
            if s1 > s2: t1d["wins"] -= 1; t1d["points"] -= stored_t1_pts; t2d["losses"] -= 1
            elif s2 > s1: t2d["wins"] -= 1; t2d["points"] -= stored_t2_pts; t1d["losses"] -= 1
            else: t1d["draws"] -= 1; t1d["points"] -= 1; t2d["draws"] -= 1; t2d["points"] -= 1

            squad_data["matches"].pop(idx)
            t1d["match_history"] = [m for m in t1d["match_history"] if m.get("match_id") != match_id]
            t2d["match_history"] = [m for m in t2d["match_history"] if m.get("match_id") != match_id]
            t1d["current_streak"] = recalculate_streak(t1)
            t2d["current_streak"] = recalculate_streak(t2)
            save_data(squad_data)

            done = discord.Embed(title="🗑️ Match Deleted", description=f"**{t1}** vs **{t2}** ({score}) erased.", color=ROYAL_RED)
            done.add_field(name="Match ID", value=f"`{match_id}`", inline=True)
            done.set_footer(text="Points and records adjusted")
            await ci.response.edit_message(embed=done, view=None)
            await log_action(ci.guild, "🗑️ Match Deleted", f"{ci.user.mention} deleted {match_id}: {t1} vs {t2} ({score})")

        async def cancel(ci):
            if ci.user.id != interaction.user.id:
                return await ci.response.send_message("❌ Not yours.", ephemeral=True)
            await ci.response.edit_message(content="✅ Cancelled.", embed=None, view=None)

        cb = Button(label="✓ Delete", style=discord.ButtonStyle.danger); cb.callback = confirm
        xb = Button(label="✗ Cancel", style=discord.ButtonStyle.secondary); xb.callback = cancel
        view.add_item(cb); view.add_item(xb)
        await interaction.response.edit_message(embed=embed, view=view)


# --- Add Squad: Modal for name, tag, guest role ---
class AddSquadModal(Modal, title="🏰 Create New Kingdom"):
    squad_name = TextInput(label="Kingdom Name", placeholder="e.g., Phoenix Flames", required=True, max_length=50)
    squad_tag = TextInput(label="Tag (prefix for nicknames)", placeholder="e.g., PF, 🔥, etc.", required=True, max_length=10)
    guest_role_name = TextInput(label="Guest Role Name (optional)", placeholder="e.g., Phoenix.Flames_guest", required=False, max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.squad_name.value.strip()
        tag = self.squad_tag.value.strip()
        grn = self.guest_role_name.value.strip() if self.guest_role_name.value else None

        # Validate
        if name in SQUADS:
            await interaction.response.send_message(f"❌ Kingdom **{name}** already exists!", ephemeral=True)
            return
        if tag in ALL_TAGS:
            await interaction.response.send_message(f"❌ Tag `{tag}` is already used by another kingdom!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            squad_role, guest_role = await add_new_squad(interaction.guild, name, tag, grn)

            embed = discord.Embed(
                title="🏰 New Kingdom Founded!",
                description=f"**{tag} {name}** has risen from the ashes!",
                color=ROYAL_GREEN
            )
            embed.add_field(name="🏴 Tag", value=f"`{tag}`", inline=True)
            embed.add_field(name="📜 Role", value=squad_role.mention if squad_role else "Created", inline=True)
            if guest_role:
                embed.add_field(name="🎭 Guest Role", value=guest_role.mention, inline=True)
            embed.add_field(
                name="📋 Next Steps",
                value="• Assign the kingdom role to members\n• Leaders can use `/leader` to manage\n• The kingdom appears in all dropdowns now!",
                inline=False
            )
            embed.set_footer(text="⚜️ A new chapter begins in the realm chronicles!")
            await interaction.followup.send(embed=embed, ephemeral=True)
            await log_action(interaction.guild, "🏰 Kingdom Founded",
                f"{interaction.user.mention} created **{tag} {name}**" + (f" with guest role `{grn}`" if grn else ""))

        except discord.Forbidden:
            await interaction.followup.send("❌ Bot lacks permission to create roles. Check bot role hierarchy!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)


class RemoveSquadSelectorView(View):
    """Select a squad to remove/disband."""
    def __init__(self, page=1):
        super().__init__(timeout=180)
        self.page = page
        all_squads = sorted(SQUADS.items())
        start = (page - 1) * 25
        end = start + 25
        page_squads = all_squads[start:end]

        if not page_squads:
            return

        options = [discord.SelectOption(label=n, value=n, description=f"Tag: {t}") for n, t in page_squads]
        select = Select(placeholder="Select kingdom to disband...", options=options)
        select.callback = self.squad_selected
        self.add_item(select)

        total_pages = (len(all_squads) + 24) // 25
        if total_pages > 1:
            if page > 1:
                b = Button(label="← Prev", style=discord.ButtonStyle.secondary)
                b.callback = self.prev
                self.add_item(b)
            if page < total_pages:
                b = Button(label="Next →", style=discord.ButtonStyle.secondary)
                b.callback = self.nxt
                self.add_item(b)

    async def prev(self, interaction):
        embed = discord.Embed(title="💀 Disband Kingdom", description="⚠️ **This is a dangerous action!**\nSelect the kingdom to disband:", color=ROYAL_RED)
        await interaction.response.edit_message(embed=embed, view=RemoveSquadSelectorView(self.page - 1))

    async def nxt(self, interaction):
        embed = discord.Embed(title="💀 Disband Kingdom", description="⚠️ **This is a dangerous action!**\nSelect the kingdom to disband:", color=ROYAL_RED)
        await interaction.response.edit_message(embed=embed, view=RemoveSquadSelectorView(self.page + 1))

    async def squad_selected(self, interaction):
        try:
            squad_name = interaction.data["values"][0]
            si = squad_data["squads"].get(squad_name, {})
            member_count = 0
            role = discord.utils.get(interaction.guild.roles, name=squad_name)
            if role:
                member_count = len(role.members)

            w = si.get("wins", 0)
            d = si.get("draws", 0)
            l = si.get("losses", 0)

            embed = discord.Embed(
                title=f"⚠️ Disband {SQUADS.get(squad_name, '?')} {squad_name}?",
                description=(
                    f"**This will permanently remove this kingdom!**\n\n"
                    f"👥 **{member_count}** members will lose their kingdom role\n"
                    f"📊 Record: {w}W-{d}D-{l}L ({si.get('points', 0)} pts)\n"
                    f"🏆 {si.get('championship_wins', 0)} championship(s)\n\n"
                    f"⚠️ Match history will be preserved but the kingdom will be gone."
                ),
                color=ROYAL_RED
            )

            view = RemoveConfirmView(squad_name, member_count, interaction.user.id)
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            try:
                await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
            except:
                pass


class RemoveConfirmView(View):
    """Confirmation buttons for squad removal."""
    def __init__(self, squad_name: str, member_count: int, author_id: int):
        super().__init__(timeout=60)
        self.squad_name = squad_name
        self.member_count = member_count
        self.author_id = author_id

    @discord.ui.button(label="Delete + Roles", style=discord.ButtonStyle.danger, emoji="💀", row=0)
    async def delete_roles_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Not yours.", ephemeral=True)
        try:
            await remove_existing_squad(interaction.guild, self.squad_name, delete_roles=True)
            embed = discord.Embed(
                title="💀 Kingdom Disbanded",
                description=f"**{self.squad_name}** has fallen. Its roles have been destroyed.\n\n*The chronicles remember what once was...*",
                color=ROYAL_RED
            )
            await interaction.response.edit_message(embed=embed, view=None)
            await log_action(interaction.guild, "💀 Kingdom Disbanded",
                f"{interaction.user.mention} disbanded **{self.squad_name}** (roles deleted, {self.member_count} members affected)")
        except Exception as e:
            await interaction.response.edit_message(content=f"❌ Error: {e}", embed=None, view=None)

    @discord.ui.button(label="Remove (Keep Roles)", style=discord.ButtonStyle.primary, emoji="📋", row=0)
    async def keep_roles_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Not yours.", ephemeral=True)
        try:
            await remove_existing_squad(interaction.guild, self.squad_name, delete_roles=False)
            embed = discord.Embed(
                title="📋 Kingdom Removed (Roles Kept)",
                description=f"**{self.squad_name}** removed from the bot but Discord roles are preserved.\nYou can delete them manually if needed.",
                color=ROYAL_GOLD
            )
            await interaction.response.edit_message(embed=embed, view=None)
            await log_action(interaction.guild, "📋 Kingdom Removed",
                f"{interaction.user.mention} removed **{self.squad_name}** from bot (roles kept)")
        except Exception as e:
            await interaction.response.edit_message(content=f"❌ Error: {e}", embed=None, view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, row=0)
    async def cancel_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Not yours.", ephemeral=True)
        await interaction.response.edit_message(content="✅ Cancelled.", embed=None, view=None)


class EditSquadSelectorView(View):
    """Select a squad to edit its tag, role name, or guest role."""
    def __init__(self, page=1):
        super().__init__(timeout=180)
        self.page = page
        all_squads = sorted(SQUADS.items())
        if not all_squads:
            return
        start = (page - 1) * 25
        end = start + 25
        page_squads = all_squads[start:end]
        if not page_squads:
            return

        options = [discord.SelectOption(label=str(n)[:100], value=str(n)[:100], description=f"Tag: {t}"[:100]) for n, t in page_squads]
        select = Select(placeholder="✏️ Select kingdom to edit...", options=options)
        select.callback = self.squad_selected
        self.add_item(select)

        total_pages = (len(all_squads) + 24) // 25
        if total_pages > 1:
            if page > 1:
                b = Button(label="← Prev", style=discord.ButtonStyle.secondary)
                b.callback = self.prev
                self.add_item(b)
            if page < total_pages:
                b = Button(label="Next →", style=discord.ButtonStyle.secondary)
                b.callback = self.nxt
                self.add_item(b)

    async def prev(self, interaction):
        embed = discord.Embed(title="✏️ Edit Kingdom", description="Select the kingdom to edit:", color=ROYAL_GOLD)
        await interaction.response.edit_message(embed=embed, view=EditSquadSelectorView(self.page - 1))

    async def nxt(self, interaction):
        embed = discord.Embed(title="✏️ Edit Kingdom", description="Select the kingdom to edit:", color=ROYAL_GOLD)
        await interaction.response.edit_message(embed=embed, view=EditSquadSelectorView(self.page + 1))

    async def squad_selected(self, interaction):
        try:
            squad_name = interaction.data["values"][0]
            current_tag = SQUADS.get(squad_name, "?")
            current_guest = GUEST_ROLES.get(squad_name, "")
            await interaction.response.send_modal(EditSquadModal(squad_name, current_tag, current_guest))
        except Exception as e:
            try:
                await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
            except:
                pass


class EditSquadModal(Modal, title="✏️ Edit Kingdom"):
    def __init__(self, old_name, old_tag, old_guest):
        super().__init__()
        self.old_name = old_name
        self.old_tag = old_tag
        self.old_guest = old_guest

        self.new_name_input = TextInput(
            label="Kingdom Name",
            default=old_name,
            required=True,
            max_length=50,
            placeholder="Change to rename the kingdom + Discord role"
        )
        self.new_tag_input = TextInput(
            label="Tag (nickname prefix)",
            default=old_tag,
            required=True,
            max_length=10,
            placeholder="e.g., PF, 🔥, etc."
        )
        self.new_guest_input = TextInput(
            label="Guest Role Name (blank to remove)",
            default=old_guest,
            required=False,
            max_length=50,
            placeholder="Leave blank to remove guest role link"
        )
        self.add_item(self.new_name_input)
        self.add_item(self.new_tag_input)
        self.add_item(self.new_guest_input)

    async def on_submit(self, interaction: discord.Interaction):
        global ALL_TAGS

        new_name = self.new_name_input.value.strip()
        new_tag = self.new_tag_input.value.strip()
        new_guest = self.new_guest_input.value.strip() if self.new_guest_input.value else ""

        # Validate: if name changed, check it doesn't clash
        name_changed = new_name != self.old_name
        tag_changed = new_tag != self.old_tag
        guest_changed = new_guest != self.old_guest

        if not name_changed and not tag_changed and not guest_changed:
            await interaction.response.send_message("ℹ️ No changes detected.", ephemeral=True)
            return

        if name_changed and new_name in SQUADS:
            await interaction.response.send_message(f"❌ Kingdom **{new_name}** already exists!", ephemeral=True)
            return

        if tag_changed:
            other_tags = [t for n, t in SQUADS.items() if n != self.old_name]
            if new_tag in other_tags:
                await interaction.response.send_message(f"❌ Tag `{new_tag}` is already used!", ephemeral=True)
                return

        await interaction.response.defer(ephemeral=True)

        changes = []
        guild = interaction.guild

        try:
            # --- 1. Tag change ---
            if tag_changed:
                SQUADS[self.old_name] = new_tag
                changes.append(f"🏴 Tag: `{self.old_tag}` → `{new_tag}`")

                # Update nicknames for all members with this role
                role = discord.utils.get(guild.roles, name=self.old_name)
                if role:
                    for member in role.members:
                        try:
                            await safe_nick_update(member, role, new_tag)
                        except:
                            pass

            # --- 2. Kingdom name change (renames everything) ---
            if name_changed:
                old = self.old_name
                tag_to_use = new_tag if tag_changed else self.old_tag

                # Rename Discord squad role
                role = discord.utils.get(guild.roles, name=old)
                if role:
                    try:
                        await role.edit(name=new_name, reason=f"Majestic Bot: Renamed '{old}' → '{new_name}'")
                    except:
                        pass

                # Update SQUADS dict
                SQUADS[new_name] = tag_to_use
                del SQUADS[old]

                # Update GUEST_ROLES dict
                if old in GUEST_ROLES:
                    GUEST_ROLES[new_name] = GUEST_ROLES.pop(old)

                # Update squad_data["squads"]
                if old in squad_data["squads"]:
                    squad_data["squads"][new_name] = squad_data["squads"].pop(old)

                # Update match history references
                for match in squad_data["matches"]:
                    if match.get("team1") == old:
                        match["team1"] = new_name
                    if match.get("team2") == old:
                        match["team2"] = new_name

                # Update squad_data["squads"][new_name]["match_history"]
                si = squad_data["squads"].get(new_name, {})
                for mh in si.get("match_history", []):
                    if mh.get("team1") == old:
                        mh["team1"] = new_name
                    if mh.get("team2") == old:
                        mh["team2"] = new_name

                # Update player squad references
                for pk, pd in squad_data["players"].items():
                    if pd.get("squad") == old:
                        pd["squad"] = new_name
                    # Update squad_history entries
                    for hist in pd.get("squad_history", []):
                        if hist.get("squad") == old:
                            hist["squad"] = new_name

                changes.append(f"👑 Name: **{old}** → **{new_name}**")

            # --- 3. Guest role change ---
            actual_name = new_name if name_changed else self.old_name
            if guest_changed:
                old_grn = self.old_guest
                if new_guest:
                    # Rename existing guest role or create one
                    if old_grn:
                        old_gr = discord.utils.get(guild.roles, name=old_grn)
                        if old_gr and new_guest != old_grn:
                            try:
                                await old_gr.edit(name=new_guest, reason=f"Majestic Bot: Guest role renamed for '{actual_name}'")
                            except:
                                pass
                    else:
                        # No old guest role — create one
                        try:
                            await guild.create_role(
                                name=new_guest,
                                mentionable=False,
                                reason=f"Majestic Bot: Guest role for '{actual_name}'"
                            )
                        except:
                            pass
                    GUEST_ROLES[actual_name] = new_guest
                    changes.append(f"🎭 Guest Role: `{old_grn or 'None'}` → `{new_guest}`")
                else:
                    # Removing guest role link (don't delete the Discord role, just unlink)
                    GUEST_ROLES.pop(actual_name, None)
                    changes.append(f"🎭 Guest Role: `{old_grn}` → *removed*")

            # --- 4. Persist ---
            ALL_TAGS = list(SQUADS.values())
            squad_data["squad_registry"] = dict(SQUADS)
            squad_data["guest_registry"] = dict(GUEST_ROLES)
            save_data(squad_data)

            # --- 5. Response ---
            embed = discord.Embed(
                title=f"✅ Kingdom Updated!",
                description=f"**{SQUADS.get(actual_name, '?')} {actual_name}** has been modified.",
                color=ROYAL_GREEN
            )
            embed.add_field(name="📝 Changes Applied", value="\n".join(changes), inline=False)
            embed.set_footer(text="⚜️ The realm chronicles have been updated!")
            await interaction.followup.send(embed=embed, ephemeral=True)
            await log_action(guild, "✏️ Kingdom Edited",
                f"{interaction.user.mention} edited **{actual_name}**: " + ", ".join(changes))

        except discord.Forbidden:
            await interaction.followup.send("❌ Bot lacks permission to edit roles. Check bot role hierarchy!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)


class ModeratorPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Record Battle", style=discord.ButtonStyle.primary, emoji="⚔️", row=0)
    async def add_match_button(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="⚔️ Record Battle — Step 1/3", description="Select the **first** kingdom:", color=ROYAL_BLUE)
        await interaction.response.send_message(embed=embed, view=RecordBattleStep1View(), ephemeral=True)
        await log_action(interaction.guild, "⚔️ Record Battle", f"{interaction.user.mention} started **Record Battle**")

    @discord.ui.button(label="Award Title", style=discord.ButtonStyle.success, emoji="🏆", row=0)
    async def add_title_button(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="🏆 Award Title", description="Select the kingdom to award:", color=ROYAL_GOLD)
        await interaction.response.send_message(embed=embed, view=AwardTitleSquadView(), ephemeral=True)
        await log_action(interaction.guild, "🏆 Award Title", f"{interaction.user.mention} started **Award Title**")

    @discord.ui.button(label="Delete Match", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
    async def del_btn(self, interaction: discord.Interaction, button: Button):
        if not squad_data["matches"]:
            await interaction.response.send_message("📜 No matches to delete.", ephemeral=True)
            return
        embed = discord.Embed(title="🗑️ Delete Match", description="Select a match to delete:", color=ROYAL_RED)
        await interaction.response.send_message(embed=embed, view=DeleteMatchSelectorView(), ephemeral=True)
        await log_action(interaction.guild, "🗑️ Delete Match", f"{interaction.user.mention} started **Delete Match**")

    @discord.ui.button(label="Recent Matches", style=discord.ButtonStyle.secondary, emoji="📜", row=1)
    async def recent_btn(self, interaction: discord.Interaction, button: Button):
        await show_recent_matches(interaction, limit=10)
        await log_action(interaction.guild, "📜 Recent Matches", f"{interaction.user.mention} viewed **Recent Matches**")

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

    @discord.ui.button(label="War Oracle", style=discord.ButtonStyle.primary, emoji="🔮", row=2)
    async def oracle_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🔮 War Oracle — Pre-Battle Analysis",
            description="Predict the outcome before recording!\n\nSelect the **first** kingdom:",
            color=ROYAL_PURPLE
        )
        await interaction.response.send_message(embed=embed, view=MatchPredictorStep1View(), ephemeral=True)
        await log_action(interaction.guild, "🔮 War Oracle", f"{interaction.user.mention} consulted the **War Oracle** (mod)")

    @discord.ui.button(label="Add Kingdom", style=discord.ButtonStyle.success, emoji="🏰", row=3)
    async def add_squad_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(AddSquadModal())
        await log_action(interaction.guild, "🏰 Add Kingdom", f"{interaction.user.mention} started **Add Kingdom**")

    @discord.ui.button(label="Edit Kingdom", style=discord.ButtonStyle.primary, emoji="✏️", row=3)
    async def edit_squad_btn(self, interaction: discord.Interaction, button: Button):
        if not SQUADS:
            await interaction.response.send_message("❌ No kingdoms to edit.", ephemeral=True)
            return
        embed = discord.Embed(
            title="✏️ Edit Kingdom",
            description="Select the kingdom to edit its name, tag, or guest role:",
            color=ROYAL_GOLD
        )
        await interaction.response.send_message(embed=embed, view=EditSquadSelectorView(), ephemeral=True)
        await log_action(interaction.guild, "✏️ Edit Kingdom", f"{interaction.user.mention} started **Edit Kingdom**")

    @discord.ui.button(label="Remove Kingdom", style=discord.ButtonStyle.danger, emoji="💀", row=3)
    async def remove_squad_btn(self, interaction: discord.Interaction, button: Button):
        if not SQUADS:
            await interaction.response.send_message("❌ No kingdoms to remove.", ephemeral=True)
            return
        embed = discord.Embed(
            title="💀 Disband Kingdom",
            description="⚠️ **This is a dangerous action!**\nSelect the kingdom to disband:",
            color=ROYAL_RED
        )
        await interaction.response.send_message(embed=embed, view=RemoveSquadSelectorView(), ephemeral=True)
        await log_action(interaction.guild, "💀 Remove Kingdom", f"{interaction.user.mention} started **Remove Kingdom**")

    @discord.ui.button(label="Set Bounty", style=discord.ButtonStyle.primary, emoji="💰", row=4)
    async def bounty_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="💰 Set Manual Bounty", description="Select a kingdom to place a bounty on:", color=ROYAL_GOLD)
        await interaction.response.send_message(embed=embed, view=SetBountySquadView(), ephemeral=True)
        await log_action(interaction.guild, "💰 Set Bounty", f"{interaction.user.mention} started **Set Bounty**")

    @discord.ui.button(label="Challenges", style=discord.ButtonStyle.secondary, emoji="🎯", row=4)
    async def challenges_btn(self, interaction: discord.Interaction, button: Button):
        all_ch = squad_data.get("challenges", [])
        active = [c for c in all_ch if c["status"] in ("pending", "accepted")]
        embed = discord.Embed(title="🎯 Challenge Manager", color=ROYAL_RED)
        if not active:
            embed.description = "*No active challenges.*"
        else:
            for c in active[:10]:
                status = "⏳ PENDING" if c["status"] == "pending" else "⚔️ ACCEPTED"
                ds = ""
                try:
                    ds = datetime.fromisoformat(c["date"]).strftime("%b %d")
                except:
                    pass
                embed.add_field(
                    name=f"{SQUADS.get(c['challenger'], '?')} {c['challenger']} vs {SQUADS.get(c['challenged'], '?')} {c['challenged']}",
                    value=f"{status} | 📅 {ds} | 🆔 `{c['id']}`",
                    inline=False
                )
        embed.set_footer(text="Record a battle between challenged kingdoms to auto-complete the challenge")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(interaction.guild, "🎯 Challenges", f"{interaction.user.mention} viewed **Challenge Manager**")


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
            discord.SelectOption(label="Majestic Moderator", value="moderator", emoji="🛡️", description="Commands for moderators"),
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
            embed.add_field(name="👤 View Profile", value="Search any warrior by name and view their full profile with power rating", inline=False)
            embed.add_field(name="🛡️ My Kingdom", value="View your own kingdom's detailed profile", inline=False)
            embed.add_field(name="⚜️ My Profile", value="See your warrior profile and stats", inline=False)
            embed.add_field(name="⚙️ Setup Profile", value="Create or update your IGN, ID, rank, and role", inline=False)
            embed.add_field(name="🎲 Fun Stats", value="Interesting realm-wide statistics and trivia", inline=False)
            embed.add_field(name="🔮 War Oracle", value="AI-powered match predictor — see win probabilities before battles!", inline=False)
            embed.add_field(name="📰 Realm News", value="Auto-generated news bulletin with latest headlines", inline=False)
            embed.add_field(name="💰 Bounties", value="View the Bounty Board — beat top-ranked kingdoms for bonus Glory Points!", inline=False)
            embed.add_field(name="🎯 Challenges", value="See all active war challenges between kingdoms", inline=False)
            embed.add_field(name="🚪 Leave Kingdom", value="Leave your current kingdom (profile preserved)", inline=False)
            embed.add_field(name="\n📌 Profile Viewing", value="Use `/profile @user` or the **View Profile** button (smart search) to view anyone's profile!", inline=False)
        elif cat == "leader":
            embed = discord.Embed(title="👑 Majestic Leader", description="Everything accessible from `/leader`", color=ROYAL_GOLD)
            embed.add_field(name="➕ Add Member", value="Search by name to recruit warriors", inline=True)
            embed.add_field(name="➖ Remove Member", value="Select from dropdown to dismiss", inline=True)
            embed.add_field(name="⭐ Set Main (5 max)", value="Select from dropdown for main roster", inline=True)
            embed.add_field(name="🔄 Set Sub (3 max)", value="Select from dropdown for substitutes", inline=True)
            embed.add_field(name="👑 Promote Leader", value="Select from dropdown to promote", inline=True)
            embed.add_field(name="🎭 Give Guest", value="Search by name to grant guest access", inline=True)
            embed.add_field(name="❌ Remove Guest", value="Select from dropdown to revoke guest", inline=True)
            embed.add_field(name="🖼️ Set Logo", value="Update your kingdom's emblem", inline=True)
            embed.add_field(name="⚔️ Challenge", value="Challenge another kingdom to war!", inline=True)
            embed.add_field(name="🏰 View Kingdom", value="See your kingdom's full profile", inline=True)
        elif cat == "moderator":
            embed = discord.Embed(title="🛡️ Majestic Moderator", description="Everything accessible from `/mod`", color=ROYAL_PURPLE)
            embed.add_field(name="⚔️ Record Battle", value="Select both kingdoms from dropdowns, then enter the score", inline=False)
            embed.add_field(name="🏆 Award Title", value="Select a kingdom from dropdown, then enter title details", inline=False)
            embed.add_field(name="🗑️ Delete Match", value="Select a match from recent matches dropdown to delete", inline=False)
            embed.add_field(name="📜 Recent Matches", value="View the last 10 recorded battles", inline=False)
            embed.add_field(name="🗑️ Clear History", value="Select a player to clear their squad transfer history", inline=False)
            embed.add_field(name="💾 Download Backup", value="Download the full data file as JSON", inline=False)
            embed.add_field(name="🔮 War Oracle", value="AI match prediction before recording battles", inline=False)
            embed.add_field(name="🏰 Add Kingdom", value="Create a new kingdom with squad role, tag, and guest role", inline=False)
            embed.add_field(name="✏️ Edit Kingdom", value="Edit a kingdom's name, tag, or guest role — renames Discord roles too", inline=False)
            embed.add_field(name="💀 Remove Kingdom", value="Disband a kingdom — optionally delete Discord roles too", inline=False)
            embed.add_field(name="💰 Set Bounty", value="Place a manual Glory Points bounty on any kingdom", inline=False)
            embed.add_field(name="🎯 Challenges", value="View and manage all active war challenges", inline=False)
        else:  # help
            embed = discord.Embed(title="📜 Majestic Help", description="Quick guide to all commands", color=ROYAL_PURPLE)
            embed.add_field(name="🎯 Slash Commands", value=(
                "`/member` — Member panel (browse, rankings, profile, etc.)\n"
                "`/leader` — Leader panel (manage roster & kingdom)\n"
                "`/mod` — Moderator panel (matches & titles)\n"
                "`/profile @user` — View anyone's profile\n"
                "`/restore` — Restore data from backup (mod only)\n"
                "`/help` — This help menu"
            ), inline=False)
            embed.add_field(name="🧠 AI Features", value=(
                "• **🔮 War Oracle** — AI predicts match outcomes with win probabilities\n"
                "• **🧠 Squad Analysis** — Deep intelligence report on any kingdom\n"
                "• **📰 Realm News** — Auto-generated news from the chronicles\n"
                "• **💪 Power Rating** — Every profile shows a calculated power score\n"
                "• **🔮 Oracle Verdict** — After recording, see if the AI predicted correctly!"
            ), inline=False)
            embed.add_field(name="💎 Glory Points System", value=(
                "Wins earn **3 base points** + dynamic bonuses:\n"
                "• ⚡ **Upset Bonus** (+1 to +3) — Beat higher-ranked kingdoms\n"
                "• 👑 **Giant Slayer** (+3) — Beat a Top 3 kingdom\n"
                "• 🔥 **Streak Fire** (+1) — 3+ win streak\n"
                "• 🧹 **Clean Sheet** (+1) — Opponent scored 0\n"
                "• 💰 **Bounty** (+1 to +5) — Claim bounties on top kingdoms\n"
                "• 📉 **Expected** (-1) — Beating a much weaker team"
            ), inline=False)
            embed.add_field(name="⚔️ Challenges & Bounties", value=(
                "• Leaders can **challenge** other kingdoms from `/leader`\n"
                "• Challenges are announced in **#war-results**\n"
                "• Top 3 kingdoms always have **auto-bounties**\n"
                "• Mods can place **manual bounties** from `/mod`\n"
                "• **Weekly Digest** posted every Sunday in #war-results"
            ), inline=False)
            embed.add_field(name="💡 Tips", value=(
                "• **View Profile / Add Member / Give Guest** use smart search — just type part of a name!\n"
                "• **All mod actions** use dropdowns — no typing squad names needed!\n"
                "• Browse any kingdom and click **🧠 AI Analysis** for a full intelligence report\n"
                "• **Rivalries** can be checked from any kingdom's profile (⚔️ button)\n"
                "• Everything is button & modal-based — minimal typing needed!"
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
    embed.add_field(name="🌟 Realm", value=(
        f"🏰 {len(SQUADS)} kingdoms • ⚔️ {tm} battles" + (f" • 👑 {top['name']} leads" if top else "") +
        f"\n💰 {len(squad_data.get('bounties', {}))} bounties • 🎯 {len([c for c in squad_data.get('challenges', []) if c['status'] in ('pending', 'accepted')])} challenges"
    ), inline=False)

    # Show player's power rating if they have a profile
    power, rank_info = calculate_power_rating(interaction.user.id)
    if power > 0:
        embed.add_field(name="💪 Your Power", value=f"{rank_info[1]} — **{power}/100**", inline=False)

    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.set_footer(text="⚜️ Powered by Majestic AI • Use the buttons below!")
    await interaction.response.send_message(embed=embed, view=view)
    await log_action(interaction.guild, "📋 /member", f"{interaction.user.mention} opened **Member Panel**")


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

    # Show active challenges for this kingdom
    active_ch = get_active_challenges(sr.name)
    if active_ch:
        ch_text = ""
        for c in active_ch[:3]:
            opp = c["challenged"] if c["challenger"] == sr.name else c["challenger"]
            status_e = "⏳" if c["status"] == "pending" else "⚔️"
            direction = "→" if c["challenger"] == sr.name else "←"
            ch_text += f"{status_e} {direction} **{SQUADS.get(opp, '?')} {opp}** ({c['status']})\n"
        embed.add_field(name="🎯 Active Challenges", value=ch_text, inline=False)

    # Show if there's a bounty on this kingdom
    bounty = squad_data.get("bounties", {}).get(sr.name)
    if bounty:
        embed.add_field(name="💰 Bounty Alert!", value=f"**+{bounty['points']}** Glory Points bounty on your kingdom!", inline=False)

    embed.set_footer(text="⚜️ Lead with honor! | All actions via buttons below")
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    await log_action(interaction.guild, "📋 /leader", f"{interaction.user.mention} opened **Leader Panel** for **{sr.name}**")


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
    embed.add_field(name="📊 Stats", value=(
        f"⚔️ {len(squad_data['matches'])} matches • 🏰 {len(SQUADS)} kingdoms\n"
        f"🎯 {len([c for c in squad_data.get('challenges', []) if c['status'] in ('pending', 'accepted')])} active challenges • "
        f"💰 {len(squad_data.get('bounties', {}))} bounties"
    ), inline=False)
    embed.set_footer(text="⚜️ Govern with fairness!")
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    await log_action(interaction.guild, "📋 /mod", f"{interaction.user.mention} opened **Moderator Panel**")


@bot.tree.command(name="profile", description="⚜️ View a warrior's profile")
@app_commands.describe(member="Tag the warrior to view")
async def profile_command(interaction: discord.Interaction, member: discord.Member):
    await show_player_profile(interaction, member, public=True)
    await log_action(interaction.guild, "👤 /profile", f"{interaction.user.mention} viewed profile of {member.mention}")


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
        "`/restore` — Restore data from backup (mod only)\n"
        "`/help` — This menu"
    ), inline=False)
    embed.set_footer(text="⚜️ Majestic Bot")
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    await log_action(interaction.guild, "📜 /help", f"{interaction.user.mention} opened **Help Menu**")


@bot.tree.command(name="restore", description="💾 Restore data from a backup JSON file")
@app_commands.describe(backup="The backup JSON file to restore")
async def restore_command(interaction: discord.Interaction, backup: discord.Attachment):
    global squad_data

    # Only moderators can restore
    if not is_moderator(interaction.user):
        await interaction.response.send_message("❌ Only **Moderators** can restore data.", ephemeral=True)
        return

    # Validate file
    if not backup.filename.endswith(".json"):
        await interaction.response.send_message("❌ Please upload a `.json` file.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    try:
        # Download and parse
        file_bytes = await backup.read()
        new_data = json.loads(file_bytes.decode("utf-8"))

        # Basic validation — must have these keys
        if "squads" not in new_data or "matches" not in new_data:
            await interaction.followup.send("❌ Invalid backup — missing `squads` or `matches` keys.", ephemeral=True)
            return

        # Ensure required fields exist
        if "players" not in new_data:
            new_data["players"] = {}

        # Fill in any missing squad entries
        for match in new_data.get("matches", []):
            if "team1_participants" not in match:
                match["team1_participants"] = []
            if "team2_participants" not in match:
                match["team2_participants"] = []

        # Rebuild registries from backup
        if "squad_registry" in new_data:
            SQUADS.clear()
            SQUADS.update(new_data["squad_registry"])
        else:
            # Old backup format — rebuild from defaults + dynamic
            SQUADS.clear()
            SQUADS.update(DEFAULT_SQUADS)
            for sn, info in new_data.get("dynamic_squads", {}).items():
                SQUADS[sn] = info.get("tag", "?")
            for sn, si in new_data.get("squads", {}).items():
                if si.get("disbanded") and sn in SQUADS:
                    del SQUADS[sn]
            new_data["squad_registry"] = dict(SQUADS)

        if "guest_registry" in new_data:
            GUEST_ROLES.clear()
            GUEST_ROLES.update(new_data["guest_registry"])
        else:
            GUEST_ROLES.clear()
            GUEST_ROLES.update(DEFAULT_GUEST_ROLES)
            for sn, info in new_data.get("dynamic_squads", {}).items():
                if info.get("guest_role"):
                    GUEST_ROLES[sn] = info["guest_role"]
            for sn, si in new_data.get("squads", {}).items():
                if si.get("disbanded") and sn in GUEST_ROLES:
                    del GUEST_ROLES[sn]
            new_data["guest_registry"] = dict(GUEST_ROLES)

        ALL_TAGS = list(SQUADS.values())

        # Ensure new data fields exist
        if "challenges" not in new_data:
            new_data["challenges"] = []
        if "bounties" not in new_data:
            new_data["bounties"] = {}

        # Save to disk and update runtime
        save_data(new_data)
        squad_data = new_data

        # Stats for confirmation
        num_squads = len(new_data["squads"])
        num_matches = len(new_data["matches"])
        num_players = len(new_data["players"])

        embed = discord.Embed(
            title="✅ Data Restored Successfully!",
            description=f"Backup `{backup.filename}` has been loaded.",
            color=ROYAL_GREEN
        )
        embed.add_field(name="📊 Restored", value=(
            f"🏰 **{num_squads}** kingdoms\n"
            f"⚔️ **{num_matches}** matches\n"
            f"👤 **{num_players}** player profiles"
        ), inline=False)
        embed.set_footer(text="⚜️ The chronicles have been restored!")
        await interaction.followup.send(embed=embed, ephemeral=True)
        await log_action(interaction.guild, "💾 Data Restored",
            f"{interaction.user.mention} restored backup `{backup.filename}` ({num_squads} squads, {num_matches} matches, {num_players} players)")

    except json.JSONDecodeError:
        await interaction.followup.send("❌ Invalid JSON file — could not parse.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Restore failed: {e}", ephemeral=True)


# -------------------- EVENTS --------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    safety_sync.start()
    if not weekly_digest_task.is_running():
        weekly_digest_task.start()
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
