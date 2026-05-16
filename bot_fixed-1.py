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
LOG_CHANNEL_NAME = "『🕹️』bot-logs"
ANNOUNCE_CHANNEL_NAME = "『🏆』war-results"
NEWS_CHANNEL_NAME = "『📢』𝐀𝐧𝐧𝐨𝐮𝐧𝐜𝐞𝐦𝐞𝐧𝐭𝐬"
TOURNAMENT_CHANNEL_NAME = "『🗞️』𝐓𝐨𝐮𝐫𝐧𝐚𝐦𝐞𝐧𝐭-𝐍𝐞𝐰𝐬"
BOT_COMMANDS_CHANNEL_NAME = "『👑』Majestic 𝐁𝐨𝐭-𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬"
MAJESTIC_ROLE_NAME = "MAJESTIC"
BOT_GUIDE_POSTED_KEY = "bot_guide_message_id"

# Logo files (place alongside bot.py)
LOGO_TRANSPARENT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_transparent.png")
LOGO_DARK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_dark.png")

ANNOUNCEMENT_CHANNELS = {
    "📢 Announcements": NEWS_CHANNEL_NAME,
    "🗞️ Tournament News": TOURNAMENT_CHANNEL_NAME,
    "🏆 War Results": ANNOUNCE_CHANNEL_NAME,
}

# Glory Points system modifiers
GLORY_BASE_WIN = 3
GLORY_BASE_DRAW = 1
GLORY_STREAK_BONUS = 1        # 3+ win streak
GLORY_CLEAN_SHEET_BONUS = 1   # opponent scored 0
GLORY_EXPECTED_TAX = -1       # beating much weaker team (rank 8+ below)

# Fun battle quotes
VICTORY_QUOTES = [
    "👑 The crown shines brightest after battle — glory to the victors!",
    "⚔️ By sword and sovereign will, the throne room echoes with triumph!",
    "🏰 The castle walls tremble before such royal might!",
    "🦁 The royal lions have feasted — none dare challenge their dominion!",
    "💎 Jewels are added to the crown — a majestic conquest!",
    "🗡️ The royal decree is written in steel — victory belongs to the worthy!",
    "👑 The throne recognizes true sovereignty — kneel before the champions!",
    "⚜️ Noble blood runs through the veins of the victorious!",
    "🔱 By the Trident of Dominion, they have claimed their birthright!",
    "🏰 The banners fly high — another conquest for the royal chronicles!",
    "👑 Majesty is not given — it is seized on the battlefield!",
    "⚔️ The court has spoken — the stronger kingdom prevails!",
]

DEFEAT_QUOTES = [
    "💀 Even kings must bow before greater sovereigns...",
    "🌑 The shadow of defeat falls upon the throne room...",
    "⛈️ A storm brews over the castle — the kingdom must rebuild...",
    "🥀 The royal gardens wither under the weight of loss...",
    "🌊 The tides of war have swept away their banners...",
    "❄️ A cold wind blows through the empty throne...",
    "🔻 The crown grows heavy in the hour of defeat...",
    "🌪️ The royal court is silenced by superior sovereignty...",
    "⚰️ A fallen banner — but the kingdom still stands...",
    "🗡️ Outruled, but the bloodline endures!",
]

DRAW_QUOTES = [
    "⚖️ The scales of dominion rest perfectly balanced — a stalemate of kings!",
    "🤝 Two sovereign powers lock in eternal equilibrium!",
    "🌓 Neither crown yields — honor is shared between thrones!",
    "⭐ The royal stars align for both kingdoms equally!",
    "🎭 A tale written in the chronicles of matched sovereignty!",
    "🔄 The Wheel of Dominion spins — both kingdoms emerge with honor!",
    "💠 Matched in royal might, united in majestic glory!",
    "🏰 Two castles stand unbroken — the realm trembles at their power!",
    "⚜️ The court declares no victor — both kingdoms reign supreme!",
    "⚡ Royal thunder clashes — neither bolt strikes harder!",
]

SQUAD_MOODS = {
    "fire": {"emoji": "🔥", "status": "ROYAL INFERNO", "desc": "Unstoppable sovereign power!"},
    "rising": {"emoji": "📈", "status": "ASCENDING", "desc": "The crown grows heavier with glory!"},
    "steady": {"emoji": "⚖️", "status": "FORTIFIED", "desc": "The castle walls hold strong"},
    "struggling": {"emoji": "😰", "status": "BESIEGED", "desc": "The kingdom calls for reinforcements"},
    "crisis": {"emoji": "💀", "status": "CRUMBLING", "desc": "The throne is under siege..."},
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
            reason=f"Majestic Dominion: New kingdom '{squad_name}' created"
        )

    # Create the guest Discord role
    guest_role = None
    if guest_role_name:
        guest_role = discord.utils.get(guild.roles, name=guest_role_name)
        if not guest_role:
            guest_role = await guild.create_role(
                name=guest_role_name,
                mentionable=False,
                reason=f"Majestic Dominion: Guest role for '{squad_name}'"
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
                await role.delete(reason=f"Majestic Dominion: Kingdom '{squad_name}' disbanded")
            except:
                pass

        # Delete guest role
        grn = GUEST_ROLES.get(squad_name)
        if grn:
            gr = discord.utils.get(guild.roles, name=grn)
            if gr:
                try:
                    await gr.delete(reason=f"Majestic Dominion: Guest role for '{squad_name}' removed")
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
# Cached URL for transparent logo (uploaded once on startup)
_transparent_logo_url = None


def get_bot_logo():
    """Get the transparent logo URL for use in embed thumbnails."""
    global _transparent_logo_url
    if _transparent_logo_url:
        return _transparent_logo_url
    # Fallback to bot avatar if not yet cached
    if bot.user:
        return bot.user.display_avatar.url
    return None


async def cache_transparent_logo(guild):
    """Upload transparent logo once to bot-logs and cache the URL."""
    global _transparent_logo_url
    if _transparent_logo_url:
        return
    # Check if we already have a cached URL in data
    cached = squad_data.get("_transparent_logo_url")
    if cached:
        _transparent_logo_url = cached
        return
    # Upload to log channel
    if not os.path.exists(LOGO_TRANSPARENT):
        return
    channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if not channel:
        return
    try:
        msg = await channel.send(
            content="⚜️ *Transparent logo cached for embed thumbnails — do not delete*",
            file=discord.File(LOGO_TRANSPARENT, filename="logo.png")
        )
        if msg.attachments:
            _transparent_logo_url = msg.attachments[0].url
            squad_data["_transparent_logo_url"] = _transparent_logo_url
            save_data(squad_data)
            print("✅ Transparent logo cached for embeds")
    except Exception as e:
        print(f"⚠️ Could not cache logo: {e}")


def apply_branding(embed, thumbnail=True, author=False):
    """Apply Majestic Dominion branding to an embed."""
    logo = get_bot_logo()
    if logo:
        if thumbnail:
            embed.set_thumbnail(url=logo)
        if author:
            embed.set_author(name="Majestic Dominion", icon_url=logo)
    return embed


async def log_action(guild: discord.Guild, title: str, description: str):
    if guild is None:
        return
    channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if channel is None:
        return
    embed = discord.Embed(title=title, description=description, color=ROYAL_PURPLE, timestamp=datetime.utcnow())
    logo = get_bot_logo()
    if logo:
        embed.set_author(name="Majestic Dominion", icon_url=logo)
    embed.set_footer(text="⚜️ Royal Archives")
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
    "⚔️ A new knight kneels before the throne — rise, warrior of the Dominion!",
    "🌟 The royal court welcomes a new champion! May your blade serve the crown!",
    "🔥 Fresh sovereign blood joins the ranks — the enemy kingdoms tremble!",
    "👑 By royal decree, a new warrior has sworn their oath to the crown!",
    "💪 The kingdom's army grows — another soul pledged to majestic glory!",
    "🦁 A new lion joins the pride — let the hunting grounds know their name!",
    "⚡ The court herald announces: a new warrior enters the royal guard!",
    "🗡️ A blade has been drawn in service of the throne — welcome, champion!",
    "🏰 The castle gates open for a worthy warrior — your legend begins now!",
    "⚜️ By the seal of Dominion, you are now sworn to this kingdom's banner!",
]

GUEST_QUOTES = [
    "🎭 A noble emissary graces the royal court with their presence!",
    "🤝 The Crown extends its hospitality — welcome, honored dignitary!",
    "🌐 By diplomatic decree, a guest of distinction enters the throne room!",
    "⭐ The royal gates open for a worthy traveler from distant lands!",
    "👑 The court recognizes a visiting noble — may your stay bring honor!",
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
        headlines.append(f"🔥 **{SQUADS.get(hottest_name, "?")} {hottest_name}** blazes with a ROYAL **{hottest_count}-win streak**! Who dares challenge the throne?")
    if coldest_name and coldest_count >= 3:
        headlines.append(f"❄️ **{SQUADS.get(coldest_name, "?")} {coldest_name}** endures a dark **{coldest_count}-loss streak**. The court watches with bated breath...")

    # 3. Championship leader
    if rankings:
        leader = rankings[0]
        if leader["points"] > 0:
            if len(rankings) > 1:
                gap = leader["points"] - rankings[1]["points"]
                headlines.append(f"👑 **{leader['tag']} {leader['name']}** rules the Dominion with **{leader['points']} pts** ({'+' + str(gap) if gap > 0 else 'TIED'} over #{2})")
            else:
                headlines.append(f"👑 **{leader['tag']} {leader['name']}** rules the Dominion with **{leader['points']} pts**!")

    # 4. Rising kingdom (biggest positive point change potential)
    underdogs = [s for s in rankings if s["total_matches"] >= 3 and s["rank"] > 5 and s["win_rate"] > 55]
    if underdogs:
        rising = random.choice(underdogs)
        headlines.append(f"📈 **{rising['tag']} {rising['name']}** is a rising sovereign — ranked #{rising['rank']} but winning **{rising['win_rate']:.0f}%** of their battles!")

    # 5. Rivalry alert — find most contested matchup
    matchup_counts = {}
    for m in matches[-20:]:
        key = tuple(sorted([m["team1"], m["team2"]]))
        matchup_counts[key] = matchup_counts.get(key, 0) + 1
    if matchup_counts:
        hottest_pair = max(matchup_counts, key=matchup_counts.get)
        if matchup_counts[hottest_pair] >= 2:
            headlines.append(f"⚔️ Royal Rivalry: **{SQUADS.get(hottest_pair[0], '?')} {hottest_pair[0]}** vs **{SQUADS.get(hottest_pair[1], '?')} {hottest_pair[1]}** — {matchup_counts[hottest_pair]} clashes in the royal arena!")

    # 6. Random fun fact
    total_matches = len(matches)
    total_players = len([p for p in squad_data["players"].values() if p.get("ingame_name")])
    fun_facts = [
        f"📊 The Dominion has witnessed **{total_matches}** royal battles in the chronicles!",
        f"🗡️ **{total_players}** warriors have sworn their oath to the Crown!",
        f"🏰 **{len(SQUADS)}** kingdoms vie for sovereign dominion!",
    ]
    if total_matches > 0:
        total_draws = sum(1 for m in matches if len(set(m["score"].split('-'))) == 1)
        fun_facts.append(f"🤝 **{total_draws}** battles ended in a royal stalemate ({total_draws/total_matches*100:.0f}%)")
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
    else:
        logo = get_bot_logo()
        if logo:
            embed.set_thumbnail(url=logo)

    embed.set_footer(text="⚜️ Majestic Dominion | Royal Archives")

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

        embed.set_footer(text="🧠 Majestic Dominion | Royal Intelligence Division")
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
    """Post match result to the public #『🏆』war-results channel."""
    apply_branding(embed, thumbnail=True, author=True)
    channel = discord.utils.get(guild.text_channels, name=ANNOUNCE_CHANNEL_NAME)
    if channel:
        try:
            await channel.send(embed=embed)
        except:
            pass


async def announce_challenge(guild, embed, content=None):
    """Post challenge updates to #『🏆』war-results channel."""
    apply_branding(embed, thumbnail=True, author=True)
    channel = discord.utils.get(guild.text_channels, name=ANNOUNCE_CHANNEL_NAME)
    if channel:
        try:
            await channel.send(content=content, embed=embed)
        except:
            pass


async def announce_event(guild, embed, content=None):
    """Post any live event to #『🏆』war-results."""
    apply_branding(embed, thumbnail=True, author=True)
    channel = discord.utils.get(guild.text_channels, name=ANNOUNCE_CHANNEL_NAME)
    if channel:
        try:
            await channel.send(content=content, embed=embed)
        except:
            pass


async def announce_major(guild, embed, content=None):
    """Post a major event with the dark logo banner."""
    apply_branding(embed, thumbnail=False, author=True)
    channel = discord.utils.get(guild.text_channels, name=ANNOUNCE_CHANNEL_NAME)
    if channel:
        try:
            if os.path.exists(LOGO_DARK):
                file = discord.File(LOGO_DARK, filename="banner.png")
                embed.set_image(url="attachment://banner.png")
                await channel.send(content=content, embed=embed, file=file)
            else:
                await channel.send(content=content, embed=embed)
        except:
            pass


async def announce_streak(guild, squad_name, streak_type, streak_count):
    """Announce streak milestones (3, 5, 7, 10+)."""
    if streak_count not in (3, 5, 7, 10) and streak_count < 10:
        return
    tag = SQUADS.get(squad_name, "?")
    if streak_type == "win":
        if streak_count >= 10:
            title, desc, color = "🔥🔥🔥 LEGENDARY ROYAL CONQUEST!", f"**{tag} {squad_name}** is on a **{streak_count}-WIN STREAK!**\nIs anyone brave enough to stop them?!", ROYAL_GOLD
        elif streak_count >= 7:
            title, desc, color = "🔥🔥 ROYAL DOMINATION!", f"**{tag} {squad_name}** is on a **{streak_count}-WIN STREAK!**\nThey look unstoppable!", ROYAL_GOLD
        elif streak_count >= 5:
            title, desc, color = "🔥 THE CROWN BLAZES!", f"**{tag} {squad_name}** is blazing with a **{streak_count}-WIN STREAK!**", ROYAL_RED
        else:
            title, desc, color = "🔥 Hot Streak!", f"**{tag} {squad_name}** has won **{streak_count} in a row!**", ROYAL_RED
    elif streak_type == "loss":
        if streak_count >= 7:
            title, desc, color = "💀 THE THRONE CRUMBLES!", f"**{tag} {squad_name}** has lost **{streak_count} straight!**\nDark times in the kingdom...", 0x2c2c2c
        elif streak_count >= 5:
            title, desc, color = "❄️ Cold Streak!", f"**{tag} {squad_name}** has lost **{streak_count} in a row...**\nThe court watches with bated breath...", 0x4a4a4a
        else:
            title, desc, color = "❄️ Struggling", f"**{tag} {squad_name}** has dropped **{streak_count} straight.**", 0x666666
    else:
        return
    embed = discord.Embed(title=title, description=desc, color=color)
    embed.set_footer(text="⚜️ Majestic Dominion | Streak Alert")
    await announce_event(guild, embed)


async def announce_rank_change(guild, squad_name, old_rank, new_rank):
    """Announce rank changes after matches."""
    if old_rank is None or new_rank is None or old_rank == new_rank:
        return
    tag = SQUADS.get(squad_name, "?")
    if new_rank < old_rank:
        # Moved UP
        if new_rank <= 3:
            embed = discord.Embed(
                title="📈 ROYAL COURT ASCENSION!",
                description=f"**{tag} {squad_name}** climbed to **#{new_rank}** (was #{old_rank})!",
                color=ROYAL_GOLD
            )
        elif new_rank == 1:
            embed = discord.Embed(
                title="👑 A NEW SOVEREIGN CLAIMS THE THRONE!",
                description=f"**{tag} {squad_name}** has taken the **THRONE!** (was #{old_rank})",
                color=ROYAL_GOLD
            )
        else:
            embed = discord.Embed(
                title="📈 Rank Up!",
                description=f"**{tag} {squad_name}** climbed from **#{old_rank}** → **#{new_rank}**",
                color=ROYAL_GREEN
            )
    else:
        # Moved DOWN
        if old_rank <= 3 and new_rank > 3:
            embed = discord.Embed(
                title="📉 ROYAL DETHRONEMENT!",
                description=f"**{tag} {squad_name}** dropped out of the Top 3! **#{old_rank}** → **#{new_rank}**",
                color=ROYAL_RED
            )
        else:
            # Only announce significant drops (3+)
            if new_rank - old_rank < 3:
                return
            embed = discord.Embed(
                title="📉 Falling!",
                description=f"**{tag} {squad_name}** dropped from **#{old_rank}** → **#{new_rank}**",
                color=0x666666
            )
    embed.set_footer(text="⚜️ Majestic Dominion | Rank Update")
    await announce_event(guild, embed)


DAILY_QUOTES = [
    "⚔️ *The royal arena awaits. Which sovereign will answer the Crown's call today?*",
    "👑 *Legends are not born of noble blood — they are forged in the fires of the Dominion.*",
    "🏰 *Every kingdom's destiny is written one battle at a time in the royal chronicles.*",
    "🔥 *Today's vassal could be tomorrow's sovereign. Seize your throne.*",
    "⚡ *Glory waits for no king. Issue a challenge and carve your name into history.*",
    "🗡️ *The Dominion grows restless. Sharpen your steel, warriors of the Crown.*",
    "🌅 *Dawn breaks over the royal battlegrounds. Fight with honor, reign with pride.*",
    "💀 *Defeat is but a trial set by the Crown. Rise stronger, rule harder.*",
    "🏆 *The throne is never secure. Defend your glory or watch it crumble.*",
    "🎯 *The Royal Bounty Board beckons — a king's ransom awaits the bold.*",
    "📊 *The rankings shift with every clash of steel. Where does your kingdom stand?*",
    "🤝 *True rivals forge each other into diamonds. Challenge one and become legend.*",
    "⚜️ *The Majestic Dominion remembers all who fight — will you be remembered as champion or challenger?*",
    "🦁 *Lions do not concern themselves with the opinions of sheep. Prove your sovereignty.*",
    "🔱 *By the Trident of Dominion — let the wars of kings begin.*",
    "👑 *Every crown was won, never given. Take yours on the battlefield.*",
]


@tasks.loop(hours=1)
async def daily_pulse_task():
    """Daily realm pulse — posts once per day at 12:00 UTC."""
    now = datetime.utcnow()
    if now.hour != 12:
        return

    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name=ANNOUNCE_CHANNEL_NAME)
        if not channel:
            continue

        rankings = get_squad_ranking()
        quote = random.choice(DAILY_QUOTES)

        embed = discord.Embed(
            title="⚜️ DAILY ROYAL DECREE",
            description=quote,
            color=ROYAL_PURPLE
        )

        # Today's stats
        today_str = now.strftime("%Y-%m-%d")
        today_matches = [m for m in squad_data["matches"] if m.get("date", "").startswith(today_str)]
        yesterday = (now.timestamp() - 86400)
        yesterday_str = datetime.utcfromtimestamp(yesterday).strftime("%Y-%m-%d")
        yesterday_matches = [m for m in squad_data["matches"] if m.get("date", "").startswith(yesterday_str)]

        embed.add_field(
            name="📊 Activity",
            value=f"⚔️ Yesterday: **{len(yesterday_matches)}** battles\n🏰 Total: **{len(squad_data['matches'])}** all-time",
            inline=True
        )

        # Current #1
        if rankings:
            top = rankings[0]
            embed.add_field(
                name="👑 Reigning Champion",
                value=f"**{top['tag']} {top['name']}**\n💎 {top['points']} glory | {top['win_rate']:.0f}% WR",
                inline=True
            )

        # Hot streaks
        hot = []
        for sn in SQUADS:
            si = squad_data["squads"].get(sn, {})
            cs = si.get("current_streak", {})
            if cs.get("count", 0) >= 3 and cs.get("type") == "win":
                hot.append(f"🔥 **{SQUADS.get(sn, '?')} {sn}** ({cs['count']}W)")
        if hot:
            embed.add_field(name="🔥 Hot Kingdoms", value="\n".join(hot[:5]), inline=False)

        # Active bounties teaser
        bounties = squad_data.get("bounties", {})
        if bounties:
            top_bounty = max(bounties.items(), key=lambda x: x[1]["points"])
            embed.add_field(
                name="💰 Biggest Bounty",
                value=f"**{SQUADS.get(top_bounty[0], '?')} {top_bounty[0]}** — +{top_bounty[1]['points']} Glory Points!",
                inline=True
            )

        # Active challenges
        active_ch = [c for c in squad_data.get("challenges", []) if c["status"] in ("pending", "accepted", "scheduled")]
        if active_ch:
            ch_text = ""
            for c in active_ch[:3]:
                emoji = "⏳" if c["status"] == "pending" else "📅" if c["status"] == "scheduled" else "⚔️"
                sched = f" — **{c['scheduled_date']}**" if c.get("scheduled_date") else ""
                ch_text += f"{emoji} {c['challenger']} vs {c['challenged']}{sched}\n"
            embed.add_field(name="🎯 Open Challenges", value=ch_text, inline=True)

        # Active events
        all_ev = squad_data.get("events", [])
        open_ev = [e for e in all_ev if e["status"] in ("open", "ongoing", "live")]
        if open_ev:
            ev_text = ""
            for ev in open_ev[:3]:
                si = "🟢" if ev["status"] == "open" else "⚔️"
                rc = len(ev.get("registrations", []))
                mx = f"/{ev['max_entries']}" if ev.get("max_entries") else ""
                if ev.get("type") == "fun":
                    sd_ev = ev.get("social_data", {})
                    done  = len([r for r in sd_ev.get("rounds",[]) if r.get("status")=="completed"])
                    lb_cnt = len(sd_ev.get("leaderboard",{}))
                    extra = f" | 🎉 {done} rounds | 👑 {lb_cnt} competitors"
                else:
                    extra = ""
                ev_text += f"{si} **{ev['name']}** — {ev.get('format','?')} | 👥 {rc}{mx}{extra}\n"
            embed.add_field(name="🎪 Active Events", value=ev_text.strip(), inline=False)

        # Oracle prediction for today — who will fight next?
        active_ch = [c for c in squad_data.get("challenges", []) if c["status"] == "scheduled"]
        if active_ch:
            next_match = active_ch[0]
            try:
                pred = predict_match(next_match["challenger"], next_match["challenged"])
                t1_tag = SQUADS.get(next_match["challenger"],"?")
                t2_tag = SQUADS.get(next_match["challenged"],"?")
                fav = next_match["challenger"] if pred["t1_pct"] > pred["t2_pct"] else next_match["challenged"]
                fav_pct = max(pred["t1_pct"], pred["t2_pct"])
                embed.add_field(
                    name=f"🔮 Oracle Watches: {t1_tag} vs {t2_tag}",
                    value=(f"📅 **{next_match.get('scheduled_date','TBD')}**\n"
                           f"👑 Favoured: **{fav}** ({fav_pct}%)\n"
                           f"*{pred['narrative'][:80]}...*"),
                    inline=False
                )
            except: pass

        # Bottom leaderboard teaser — who's climbing?
        if len(rankings) >= 3:
            bottom_3 = rankings[-3:][::-1]
            danger_text = " · ".join(f"{s['tag']} **{s['name']}** ({s['points']}pts)" for s in bottom_3)
            embed.add_field(name="⚠️ Kingdoms in the Shadows", value=danger_text, inline=False)

        embed.set_footer(text=f"📅 {now.strftime('%A, %B %d, %Y')} | ⚜️ Majestic Dominion — The Crown Watches All")
        apply_branding(embed, thumbnail=False, author=True)

        try:
            if os.path.exists(LOGO_DARK):
                file = discord.File(LOGO_DARK, filename="banner.png")
                embed.set_image(url="attachment://banner.png")
                await channel.send(embed=embed, file=file)
            else:
                await channel.send(embed=embed)
        except:
            pass


@daily_pulse_task.before_loop
async def before_daily_pulse():
    await bot.wait_until_ready()


# =====================================================================
#                     CHALLENGE SYSTEM
# =====================================================================

def get_active_challenges(squad_name=None):
    """Get all pending/accepted/scheduled challenges, optionally filtered by squad."""
    challenges = squad_data.get("challenges", [])
    active = [c for c in challenges if c["status"] in ("pending", "accepted", "scheduled")]
    if squad_name:
        active = [c for c in active if c["challenger"] == squad_name or c["challenged"] == squad_name]
    return active


def has_pending_challenge(squad1, squad2):
    """Check if there's already an active challenge between two squads."""
    for c in squad_data.get("challenges", []):
        if c["status"] in ("pending", "accepted", "scheduled"):
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

        # Public announcement in #『🏆』war-results
        # Rank context for challenge
        ch_rank  = get_squad_rank(self.challenger) or "?"
        cd_rank  = get_squad_rank(self.challenged) or "?"
        rank_txt = f"#{ch_rank} vs #{cd_rank}"
        upset_hint = ""
        if isinstance(ch_rank, int) and isinstance(cd_rank, int):
            if ch_rank > cd_rank:
                upset_hint = f"\n⚡ *#{ch_rank} challenging #{cd_rank} — an upset could shake the Dominion!*"
            elif ch_rank == 1:
                upset_hint = "\n👑 *The #1 kingdom goes hunting — none are safe!*"

        pub_embed = discord.Embed(
            title="⚔️ A WAR DECLARATION ECHOES THROUGH THE DOMINION!",
            description=(
                f"**{SQUADS.get(self.challenger, '?')} {self.challenger}** has drawn steel against\n"
                f"**{SQUADS.get(self.challenged, '?')} {self.challenged}**!\n\n"
                f"⚔️ *{rank_txt}*{upset_hint}\n\n"
                f"⏳ **Awaiting response from {self.challenged}...**"
            ),
            color=ROYAL_RED
        )
        if msg:
            pub_embed.add_field(name="📜 War Declaration", value=f"*\"{msg}\"*", inline=False)
        pub_embed.set_footer(text=f"Challenge ID: {challenge_id} | Leaders of {self.challenged} — the throne room awaits your answer!")

        # Mention the challenged squad's role
        challenged_role = discord.utils.get(interaction.guild.roles, name=self.challenged)
        mention_text = challenged_role.mention if challenged_role else f"**{self.challenged}**"

        # Send to #『🏆』war-results with response buttons
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
    """Accept/Decline buttons shown in #『🏆』war-results for opponent leaders."""
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
            title="⚔️ THE CHALLENGE IS ANSWERED!",
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
        title="💰 Royal Bounty Board",
        description=(
            "*The Crown has placed a price on these heads.*\n"
            "*Sharpen your steel. The bold shall be rewarded.*\n\n"
            "🏆 Top 3 kingdoms always carry an automatic bounty.\n"
            "⚔️ Defeat them in battle to claim the bonus Glory Points!"
        ),
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
    embed.set_footer(text="⚜️ Majestic Dominion | Royal bounties refresh after each battle")
    apply_branding(embed, thumbnail=True)
    return embed


class BountyBoardView(View):
    """View for bounty board — members can view."""
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh_btn(self, interaction: discord.Interaction, button: Button):
        refresh_bounties()
        save_data(squad_data)
        await interaction.response.edit_message(embed=build_bounty_embed(), view=BountyBoardView())


class ManageBountiesView(View):
    """Mod bounty manager — add, delete, refresh."""
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="Add Bounty", style=discord.ButtonStyle.success, emoji="➕", row=0)
    async def add_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="💰 Set Bounty", description="Select a kingdom:", color=ROYAL_GOLD)
        await interaction.response.edit_message(embed=embed, view=SetBountySquadView())

    @discord.ui.button(label="Remove Bounty", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
    async def remove_btn(self, interaction: discord.Interaction, button: Button):
        bounties = squad_data.get("bounties", {})
        if not bounties:
            await interaction.response.send_message("❌ No active bounties to remove.", ephemeral=True)
            return
        await interaction.response.edit_message(
            embed=discord.Embed(title="🗑️ Remove Bounty", description="Select a bounty to remove:", color=ROYAL_RED),
            view=DeleteBountyView()
        )

    @discord.ui.button(label="Clear All", style=discord.ButtonStyle.danger, emoji="💣", row=0)
    async def clear_all_btn(self, interaction: discord.Interaction, button: Button):
        bounties = squad_data.get("bounties", {})
        if not bounties:
            await interaction.response.send_message("❌ No bounties to clear.", ephemeral=True)
            return
        count = len(bounties)
        squad_data["bounties"] = {}
        save_data(squad_data)
        await interaction.response.edit_message(
            embed=discord.Embed(title="💣 All Bounties Cleared", description=f"Removed **{count}** bounties.", color=ROYAL_RED),
            view=None
        )
        await log_action(interaction.guild, "💣 Bounties Cleared", f"{interaction.user.mention} cleared all **{count}** bounties")

    @discord.ui.button(label="Refresh Board", style=discord.ButtonStyle.secondary, emoji="🔄", row=1)
    async def refresh_btn(self, interaction: discord.Interaction, button: Button):
        refresh_bounties()
        save_data(squad_data)
        embed = build_bounty_embed()
        embed.title = "💰 Bounty Manager"
        await interaction.response.edit_message(embed=embed, view=ManageBountiesView())


class DeleteBountyView(View):
    """Select a bounty to remove."""
    def __init__(self):
        super().__init__(timeout=180)
        bounties = squad_data.get("bounties", {})
        if not bounties:
            return
        options = []
        for name, info in sorted(bounties.items(), key=lambda x: x[1]["points"], reverse=True):
            label = f"{name} (+{info['points']} pts)"[:100]
            options.append(discord.SelectOption(label=label, value=name, description=info.get("reason", "")[:100]))
        if options:
            select = Select(placeholder="Select bounty to remove...", options=options[:25])
            select.callback = self.selected
            self.add_item(select)

    async def selected(self, interaction):
        target = interaction.data["values"][0]
        removed = squad_data.get("bounties", {}).pop(target, None)
        save_data(squad_data)
        if removed:
            embed = discord.Embed(
                title="🗑️ Bounty Removed",
                description=f"Removed **+{removed['points']}** bounty from **{SQUADS.get(target, '?')} {target}**",
                color=ROYAL_RED
            )
            await interaction.response.edit_message(embed=embed, view=None)
            await log_action(interaction.guild, "🗑️ Bounty Removed",
                f"{interaction.user.mention} removed bounty from **{target}** (+{removed['points']} pts)")
        else:
            await interaction.response.edit_message(content="❌ Bounty not found.", embed=None, view=None)


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
#                     CHALLENGE MANAGER (Moderator)
# =====================================================================

def build_challenge_manager_embed():
    """Build the challenge manager embed."""
    all_ch = squad_data.get("challenges", [])
    active = [c for c in all_ch if c["status"] in ("pending", "accepted", "scheduled")]
    embed = discord.Embed(title="🎯 Challenge Manager", color=ROYAL_RED)
    if not active:
        embed.description = "*No active challenges. Leaders can issue challenges from `/leader`.*"
    else:
        for c in active[:15]:
            if c["status"] == "pending":
                status = "⏳ PENDING"
            elif c["status"] == "accepted":
                status = "⚔️ ACCEPTED"
            else:
                status = "📅 SCHEDULED"
            ds = ""
            try:
                ds = datetime.fromisoformat(c["date"]).strftime("%b %d")
            except:
                pass
            sched = ""
            if c.get("scheduled_date"):
                sched = f"\n📅 **Match: {c['scheduled_date']}**"
            embed.add_field(
                name=f"{SQUADS.get(c['challenger'], '?')} {c['challenger']} vs {SQUADS.get(c['challenged'], '?')} {c['challenged']}",
                value=f"{status} | Issued {ds} | 🆔 `{c['id']}`{sched}",
                inline=False
            )
    total = len(all_ch)
    completed = len([c for c in all_ch if c["status"] == "completed"])
    declined = len([c for c in all_ch if c["status"] == "declined"])
    embed.set_footer(text=f"📊 {len(active)} active | {completed} completed | {declined} declined | {total} total all-time")
    apply_branding(embed, thumbnail=True)
    return embed


class ManageChallengesView(View):
    """Mod challenge manager — schedule, cancel, clear."""
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="Schedule Match", style=discord.ButtonStyle.success, emoji="📅", row=0)
    async def schedule_btn(self, interaction: discord.Interaction, button: Button):
        active = [c for c in squad_data.get("challenges", []) if c["status"] in ("accepted", "scheduled")]
        if not active:
            await interaction.response.send_message("❌ No accepted challenges to schedule. Challenges must be accepted first.", ephemeral=True)
            return
        await interaction.response.edit_message(
            embed=discord.Embed(title="📅 Schedule Match", description="Select the challenge to schedule:", color=ROYAL_GREEN),
            view=ScheduleChallengeSelectView()
        )

    @discord.ui.button(label="Cancel Challenge", style=discord.ButtonStyle.danger, emoji="❌", row=0)
    async def cancel_btn(self, interaction: discord.Interaction, button: Button):
        active = [c for c in squad_data.get("challenges", []) if c["status"] in ("pending", "accepted", "scheduled")]
        if not active:
            await interaction.response.send_message("❌ No active challenges to cancel.", ephemeral=True)
            return
        await interaction.response.edit_message(
            embed=discord.Embed(title="❌ Cancel Challenge", description="Select a challenge to cancel:", color=ROYAL_RED),
            view=CancelChallengeSelectView()
        )

    @discord.ui.button(label="Clear Old", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
    async def clear_btn(self, interaction: discord.Interaction, button: Button):
        before = len(squad_data.get("challenges", []))
        squad_data["challenges"] = [c for c in squad_data.get("challenges", [])
                                    if c["status"] in ("pending", "accepted", "scheduled")]
        after = len(squad_data["challenges"])
        removed = before - after
        save_data(squad_data)
        embed = build_challenge_manager_embed()
        if removed > 0:
            embed.description = f"🗑️ Cleared **{removed}** completed/declined challenges.\n\n" + (embed.description or "")
        else:
            embed.description = "ℹ️ No old challenges to clear.\n\n" + (embed.description or "")
        await interaction.response.edit_message(embed=embed, view=ManageChallengesView())
        if removed > 0:
            await log_action(interaction.guild, "🗑️ Challenges Cleared",
                f"{interaction.user.mention} cleared **{removed}** old challenges")

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.secondary, emoji="🔄", row=1)
    async def refresh_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(embed=build_challenge_manager_embed(), view=ManageChallengesView())


class ScheduleChallengeSelectView(View):
    """Select an accepted challenge to schedule."""
    def __init__(self):
        super().__init__(timeout=180)
        active = [c for c in squad_data.get("challenges", []) if c["status"] in ("accepted", "scheduled")]
        if not active:
            return
        options = []
        for c in active[:25]:
            tag1 = SQUADS.get(c["challenger"], "?")
            tag2 = SQUADS.get(c["challenged"], "?")
            label = f"{tag1} {c['challenger']} vs {tag2} {c['challenged']}"[:100]
            status_desc = f"{'📅 ' + c['scheduled_date'] if c.get('scheduled_date') else c['status'].upper()} | {c['id']}"[:100]
            options.append(discord.SelectOption(label=label, value=c["id"], description=status_desc))
        if options:
            select = Select(placeholder="📅 Select challenge to schedule...", options=options)
            select.callback = self.selected
            self.add_item(select)

    async def selected(self, interaction):
        cid = interaction.data["values"][0]
        # Find the challenge
        challenge = None
        for c in squad_data.get("challenges", []):
            if c["id"] == cid:
                challenge = c
                break
        if not challenge:
            await interaction.response.send_message("❌ Challenge not found.", ephemeral=True)
            return
        existing_date = challenge.get("scheduled_date", "")
        await interaction.response.send_modal(ScheduleDateModal(cid, existing_date))


class ScheduleDateModal(Modal, title="📅 Schedule Match Date"):
    def __init__(self, challenge_id, existing_date=""):
        super().__init__()
        self.challenge_id = challenge_id
        self.match_date = TextInput(
            label="Match Date & Time",
            placeholder="e.g., Feb 25, 8:00 PM EST",
            default=existing_date,
            required=True,
            max_length=100
        )
        self.match_notes = TextInput(
            label="Notes (optional)",
            placeholder="e.g., Best of 3, custom rules, etc.",
            required=False,
            max_length=200
        )
        self.add_item(self.match_date)
        self.add_item(self.match_notes)

    async def on_submit(self, interaction: discord.Interaction):
        date_str = self.match_date.value.strip()
        notes = self.match_notes.value.strip() if self.match_notes.value else ""

        # Find and update the challenge
        challenge = None
        for c in squad_data.get("challenges", []):
            if c["id"] == self.challenge_id:
                c["status"] = "scheduled"
                c["scheduled_date"] = date_str
                c["scheduled_notes"] = notes
                c["scheduled_by"] = interaction.user.id
                challenge = c
                break

        if not challenge:
            await interaction.response.send_message("❌ Challenge not found.", ephemeral=True)
            return

        save_data(squad_data)

        tag1 = SQUADS.get(challenge["challenger"], "?")
        tag2 = SQUADS.get(challenge["challenged"], "?")

        embed = discord.Embed(
            title="📅 Match Scheduled!",
            description=(
                f"**{tag1} {challenge['challenger']}** vs **{tag2} {challenge['challenged']}**\n\n"
                f"📅 **{date_str}**"
            ),
            color=ROYAL_GREEN
        )
        if notes:
            embed.add_field(name="📋 Notes", value=notes, inline=False)
        embed.set_footer(text=f"Challenge ID: {self.challenge_id}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Public announcement in #『🏆』war-results
        pub_embed = discord.Embed(
            title="📅 ROYAL BATTLE DECREE!",
            description=(
                f"**{tag1} {challenge['challenger']}** vs **{tag2} {challenge['challenged']}**\n\n"
                f"🗓️ **{date_str}**\n\n"
                f"*By order of the Crown — the royal arena has been prepared!*"
            ),
            color=ROYAL_GREEN
        )
        if notes:
            pub_embed.add_field(name="📋 Details", value=notes, inline=False)
        if challenge.get("message"):
            pub_embed.add_field(name="📜 War Declaration", value=f"*\"{challenge['message']}\"*", inline=False)
        pub_embed.set_footer(text=f"Challenge ID: {self.challenge_id} | ⚜️ May the best kingdom win!")

        # Ping both kingdom roles
        guild = interaction.guild
        r1 = discord.utils.get(guild.roles, name=challenge["challenger"])
        r2 = discord.utils.get(guild.roles, name=challenge["challenged"])
        mentions = []
        if r1: mentions.append(r1.mention)
        if r2: mentions.append(r2.mention)
        mention_text = " ".join(mentions) if mentions else ""

        await announce_major(guild, pub_embed, content=f"📅 {mention_text} — Your match is scheduled!" if mention_text else None)
        await log_action(guild, "📅 Match Scheduled",
            f"{interaction.user.mention} scheduled **{challenge['challenger']}** vs **{challenge['challenged']}** for **{date_str}**" +
            (f" | Notes: {notes}" if notes else ""))


class CancelChallengeSelectView(View):
    """Select a challenge to cancel."""
    def __init__(self):
        super().__init__(timeout=180)
        active = [c for c in squad_data.get("challenges", []) if c["status"] in ("pending", "accepted", "scheduled")]
        if not active:
            return
        options = []
        for c in active[:25]:
            tag1 = SQUADS.get(c["challenger"], "?")
            tag2 = SQUADS.get(c["challenged"], "?")
            label = f"{tag1} {c['challenger']} vs {tag2} {c['challenged']}"[:100]
            sched = f" | 📅 {c['scheduled_date']}" if c.get("scheduled_date") else ""
            status_desc = f"{c['status'].upper()}{sched} | {c['id']}"[:100]
            options.append(discord.SelectOption(label=label, value=c["id"], description=status_desc))
        if options:
            select = Select(placeholder="❌ Select challenge to cancel...", options=options)
            select.callback = self.selected
            self.add_item(select)

    async def selected(self, interaction):
        cid = interaction.data["values"][0]
        challenge = None
        for c in squad_data.get("challenges", []):
            if c["id"] == cid and c["status"] in ("pending", "accepted", "scheduled"):
                c["status"] = "cancelled"
                c["cancelled_by"] = interaction.user.id
                challenge = c
                break

        if not challenge:
            await interaction.response.send_message("❌ Challenge not found or already resolved.", ephemeral=True)
            return

        save_data(squad_data)
        tag1 = SQUADS.get(challenge["challenger"], "?")
        tag2 = SQUADS.get(challenge["challenged"], "?")

        embed = discord.Embed(
            title="❌ Challenge Cancelled",
            description=f"**{tag1} {challenge['challenger']}** vs **{tag2} {challenge['challenged']}** has been cancelled by a moderator.",
            color=ROYAL_RED
        )
        await interaction.response.edit_message(embed=embed, view=None)

        # Public announcement
        pub_embed = discord.Embed(
            title="❌ CHALLENGE CANCELLED",
            description=f"The challenge between **{tag1} {challenge['challenger']}** and **{tag2} {challenge['challenged']}** has been cancelled.",
            color=discord.Color.greyple()
        )
        pub_embed.set_footer(text=f"Cancelled by moderator | Challenge ID: {cid}")
        await announce_event(interaction.guild, pub_embed)
        await log_action(interaction.guild, "❌ Challenge Cancelled",
            f"{interaction.user.mention} cancelled challenge **{challenge['challenger']}** vs **{challenge['challenged']}** (ID: {cid})")


# =====================================================================
#                     ANNOUNCEMENT SYSTEM (Moderator)
# =====================================================================

class AnnouncementChannelView(View):
    """Step 1: Select which channel to announce in."""
    def __init__(self):
        super().__init__(timeout=180)
        options = [
            discord.SelectOption(label=label, value=ch_name, emoji=label[0])
            for label, ch_name in ANNOUNCEMENT_CHANNELS.items()
        ]
        select = Select(placeholder="📢 Select announcement channel...", options=options)
        select.callback = self.selected
        self.add_item(select)

    async def selected(self, interaction):
        channel_name = interaction.data["values"][0]
        # Check channel exists
        ch = discord.utils.get(interaction.guild.text_channels, name=channel_name)
        if not ch:
            await interaction.response.send_message(f"❌ Channel `{channel_name}` not found in this server.", ephemeral=True)
            return
        await interaction.response.send_modal(AnnouncementModal(channel_name))


class AnnouncementModal(Modal, title="📢 Royal Announcement"):
    def __init__(self, channel_name):
        super().__init__()
        self.channel_name = channel_name
        self.ann_title = TextInput(
            label="Announcement Title",
            placeholder="e.g., Season 3 Begins!",
            required=True,
            max_length=200
        )
        self.ann_body = TextInput(
            label="Announcement Body",
            placeholder="Write your announcement here...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=2000
        )
        self.ann_images = TextInput(
            label="Image URLs (one per line, optional)",
            placeholder="https://i.imgur.com/example.png\nhttps://...",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000
        )
        self.add_item(self.ann_title)
        self.add_item(self.ann_body)
        self.add_item(self.ann_images)

    async def on_submit(self, interaction: discord.Interaction):
        ch = discord.utils.get(interaction.guild.text_channels, name=self.channel_name)
        if not ch:
            await interaction.response.send_message(f"❌ Channel not found.", ephemeral=True)
            return

        title = self.ann_title.value.strip()
        body = self.ann_body.value.strip()
        image_text = self.ann_images.value.strip() if self.ann_images.value else ""

        # Parse image URLs
        image_urls = []
        if image_text:
            for line in image_text.split("\n"):
                url = line.strip()
                if url.startswith("http"):
                    image_urls.append(url)

        # Build main embed
        embed = discord.Embed(
            title=f"📢 {title}",
            description=body,
            color=ROYAL_GOLD,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"⚜️ Majestic Dominion | Announced by {interaction.user.display_name}")

        # Set first image as embed thumbnail/image
        if image_urls:
            embed.set_image(url=image_urls[0])

        # Find @MAJESTIC role
        majestic_role = discord.utils.get(interaction.guild.roles, name=MAJESTIC_ROLE_NAME)
        mention_text = majestic_role.mention if majestic_role else f"@{MAJESTIC_ROLE_NAME}"

        try:
            # Send main announcement — use dark logo as banner if no images
            if not image_urls and os.path.exists(LOGO_DARK):
                file = discord.File(LOGO_DARK, filename="banner.png")
                embed.set_image(url="attachment://banner.png")
                await ch.send(content=f"📢 {mention_text}", embed=embed, file=file)
            else:
                await ch.send(content=f"📢 {mention_text}", embed=embed)

            # Send additional images as separate messages
            for img_url in image_urls[1:]:
                extra_embed = discord.Embed(color=ROYAL_GOLD)
                extra_embed.set_image(url=img_url)
                await ch.send(embed=extra_embed)

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="✅ Royal Announcement Published!",
                    description=f"Posted to **{self.channel_name}** with {len(image_urls)} image(s).",
                    color=ROYAL_GREEN
                ),
                ephemeral=True
            )
            await log_action(interaction.guild, "📢 Announcement",
                f"{interaction.user.mention} published announcement **{title}** to `{self.channel_name}` ({len(image_urls)} images)")

        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot lacks permission to post in that channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)


# =====================================================================
#                     BOT COMMANDS CHANNEL SYSTEM
# =====================================================================

BOT_GUIDE_EMBED_PAGES = []

def build_bot_guide_embeds():
    """Build the permanent bot guide for the commands channel."""
    embeds = []

    # Page 1: Welcome
    e1 = discord.Embed(
        title="👑 WELCOME TO THE MAJESTIC DOMINION",
        description=(
            "⚜️ *This is the official command center of the Majestic Dominion.*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Use this channel to interact with the Royal Bot.\n"
            "Type any of the commands below to begin your journey.\n\n"
            "**All commands work right here — just type and go!**"
        ),
        color=ROYAL_GOLD
    )
    e1.add_field(
        name="⚔️ Available Commands",
        value=(
            "👤 `/member` — Open the Royal Court (your main hub)\n"
            "👑 `/leader` — Sovereign Command (leaders only)\n"
            "🛡️ `/mod` — Royal Council Chamber (moderators only)\n"
            "⚜️ `/profile @user` — View any warrior's royal scroll\n"
            "📜 `/help` — Open the Royal Codex\n"
        ),
        inline=False
    )
    embeds.append(e1)

    # Page 2: Member Guide
    e2 = discord.Embed(
        title="⚜️ THE ROYAL COURT — `/member`",
        description="*Everything a citizen of the Dominion needs.*",
        color=ROYAL_PURPLE
    )
    e2.add_field(
        name="🏰 Explore",
        value=(
            "**Browse Kingdoms** — Explore every kingdom's stats, history, and AI analysis\n"
            "**Rankings** — See the full Glory Points leaderboard\n"
            "**View Profile** — Search any warrior by name\n"
            "**Fun Stats** — Royal court curiosities and realm trivia\n"
            "**Realm News** — Auto-generated headlines from the chronicles"
        ),
        inline=False
    )
    e2.add_field(
        name="⚔️ Competition",
        value=(
            "**War Oracle** — AI predicts the outcome of any matchup\n"
            "**Bounties** — See who has a price on their crown\n"
            "**Challenges** — View all active war declarations"
        ),
        inline=False
    )
    e2.add_field(
        name="👤 Your Profile",
        value=(
            "**My Kingdom** — Your kingdom's stats and roster\n"
            "**My Profile** — Your warrior scroll\n"
            "**Setup Profile** — Register your IGN, Game ID, Rank, and Position\n"
            "**Leave Kingdom** — Leave your current kingdom"
        ),
        inline=False
    )
    embeds.append(e2)

    # Page 3: Glory Points & Challenges
    e3 = discord.Embed(
        title="💎 GLORY POINTS & CHALLENGES",
        description="*How the Dominion's ranking system works.*",
        color=ROYAL_RED
    )
    e3.add_field(
        name="💎 Glory Points",
        value=(
            "Wins don't all count the same. The Glory system rewards skill and courage:\n\n"
            "**Base:** Win = **3 pts** | Draw = **1 pt**\n\n"
            "⚡ **Upset** (+1 to +3) — Beat a higher-ranked kingdom\n"
            "👑 **Giant Slayer** (+3) — Beat a Top 3 kingdom\n"
            "🔥 **Streak Fire** (+1) — 3+ win streak\n"
            "🧹 **Clean Sheet** (+1) — Opponent scored 0\n"
            "💰 **Bounty Claimed** (+1 to +5) — Target had a bounty\n"
            "📉 **Expected** (-1) — Beat a much weaker kingdom"
        ),
        inline=False
    )
    e3.add_field(
        name="⚔️ Challenges",
        value=(
            "Kingdom leaders can declare war on other kingdoms!\n\n"
            "1️⃣ Leader uses `/leader` → ⚔️ **Challenge**\n"
            "2️⃣ Challenge posted in 『🏆』war-results\n"
            "3️⃣ Opponent leaders **Accept** or **Decline**\n"
            "4️⃣ Admin schedules the match date\n"
            "5️⃣ Match is played → admin records result"
        ),
        inline=False
    )
    e3.add_field(
        name="💰 Bounties",
        value=(
            "The **Top 3** kingdoms always have automatic bounties.\n"
            "Beat them and earn **bonus Glory Points** on top of your normal win!\n"
            "Check the bounty board anytime with `/member` → 💰 **Bounties**"
        ),
        inline=False
    )
    embeds.append(e3)

    # Page 4: Leader Guide
    e4 = discord.Embed(
        title="👑 LEADER'S GUIDE",
        description="*For kingdom leaders — your sovereign powers.*",
        color=ROYAL_GOLD
    )
    e4.add_field(
        name="👑 `/leader` Powers",
        value=(
            "➕ **Add Member** — Recruit warriors to your kingdom\n"
            "➖ **Remove Member** — Release warriors from service\n"
            "⭐ **Set Main** (5 max) — Your core competitive roster\n"
            "🔄 **Set Sub** (3 max) — Backup warriors\n"
            "👑 **Promote Leader** — Grant leader access\n"
            "🎭 **Give/Remove Guest** — Manage guest access\n"
            "🖼️ **Set Logo** — Your kingdom's royal emblem\n"
            "⚔️ **Challenge** — Declare war on another kingdom"
        ),
        inline=False
    )
    e4.add_field(
        name="⚠️ Important",
        value=(
            "• **Only main roster players count** in official matches\n"
            "• Set your mains before any match\n"
            "• Contact an admin to schedule after a challenge is accepted\n"
            "• Send a **screenshot** of results to admin after the match"
        ),
        inline=False
    )
    embeds.append(e4)

    # Page 5: Events Guide
    e_events = discord.Embed(
        title="🎪 THE MAJESTIC ARENA — `/events`",
        description="*Compete, register, and claim glory in official Dominion events.*",
        color=ROYAL_GOLD
    )
    e_events.add_field(
        name="📋 Event Types",
        value=(
            "**🏆 Tournament** — Competitive · fixed format (1v1 / 2v2 / 5v5…) · bracket system\n"
            "**🎉 Social Event** — Fun or themed events (Hide & Seek, FFA, custom rules…) · free format"
        ),
        inline=False
    )
    e_events.add_field(
        name="📝 How to Register",
        value=(
            "Type `/events`, pick an event from the dropdown, click **📝 Register**.\n\n"
            "**👤 Solo** — confirm with one click\n"
            "**👥 Small Team (2v2 / 3v3 / 4v4)** — leader registers + lists teammate IDs\n"
            "**👑 Squad 5v5** — only Kingdom **Leaders**; uses your existing main roster\n\n"
            "To cancel: open the event again → **❌ Cancel Registration**"
        ),
        inline=False
    )
    e_events.add_field(
        name="📊 Event Status",
        value=(
            "🟢 **Open** → Registration active\n"
            "⚔️ **Ongoing** → Event is live\n"
            "🔴 **Closed** → Event finished"
        ),
        inline=False
    )
    embeds.append(e_events)

    # Page 6: Oracle Guide
    e_oracle = discord.Embed(
        title="🔮 THE ROYAL ORACLE",
        description="*Your AI companion — available 24/7 in 『🔮』Royal Oracle.*",
        color=0x4B0082
    )
    e_oracle.add_field(
        name="💬 How to Use",
        value=(
            "Just type in **『🔮』Royal Oracle** or use `/oracle [question]` anywhere.\n"
            "No commands needed — just talk naturally."
        ),
        inline=False
    )
    e_oracle.add_field(
        name="📊 Server Info",
        value=(
            "🏆 **Who's winning?** — Live leaderboard with streaks\n"
            "🔥 **Who's on a streak?** — Kingdoms currently on fire\n"
            "💰 **Which kingdoms have bounties?** — Bounty board live\n"
            "📅 **What events are open?** — Registration status & dates\n"
            "⚔️ **What happened recently?** — Last 10 match results\n"
            "🎯 **Predict Phoenix vs Storm** — AI match prediction with analysis"
        ),
        inline=False
    )
    e_oracle.add_field(
        name="🎉 Just for Fun",
        value=(
            "😂 **Roast me** — Ask for a playful roast\n"
            "📊 **Rate my decision** — Get a 0-10 score on any life choice\n"
            "🎲 **Make up my horoscope** — Fake but specific and funny\n"
            "🦸 **Give me a superpower** — Based on your personality\n"
            "🏆 **Achievement unlocked** — For any mundane thing you did\n"
            "🎤 **Write a rap about ___** — 3 lines on any topic\n"
            "⚖️ **Settle a debate** — Bring any argument, Oracle judges\n"
            "🎭 **My villain origin story** — Describe a frustration, get a story\n"
            "🍀 **Fortune cookie** — Specific and actually funny\n"
            "📜 **Fake Wikipedia intro** — About yourself or anyone\n"
            "🎯 **Hot take on ___** — Oracle has opinions on everything\n"
            "🧠 **Two truths one lie** — Oracle uses real server data\n"
            "📣 **TED talk title** — For whatever you're going through"
        ),
        inline=False
    )
    e_oracle.add_field(
        name="⚡ Limits",
        value="15 second cooldown · 50 questions per person per day",
        inline=False
    )
    embeds.append(e_oracle)

    # Page 7: Stay Connected
    e5 = discord.Embed(
        title="📢 STAY CONNECTED",
        description="*Where to follow the action in the Dominion.*",
        color=ROYAL_PURPLE
    )
    e5.add_field(
        name="📺 Live Channels",
        value=(
            "**『🏆』war-results** — Match results · Streaks · Rank changes · Challenges · Event notices · Brackets · Schedules · Daily Pulse · Weekly Chronicle\n"
            "**『📢』Announcements** — New event full announcements (image + prize + rules) · Official royal decrees\n"
            "**『🗞️』Tournament News** — Tournament-specific announcements"
        ),
        inline=False
    )
    e5.add_field(
        name="🤖 Auto-Posts",
        value=(
            "⚜️ **Daily Royal Decree** — Posted daily at 12:00 UTC (includes active events)\n"
            "📰 **Weekly Royal Chronicle** — Posted every Sunday at 18:00 UTC (includes events)\n"
            "🔥 **Streak Alerts** — When kingdoms hit 3, 5, 7, 10+ streaks\n"
            "📈 **Rank Changes** — When kingdoms enter/leave the Top 3\n"
            "🏅 **Royal Honours** — Achievement unlocks"
        ),
        inline=False
    )
    e5.set_footer(text="⚜️ Majestic Dominion | Glory awaits. Type /member or /events to begin!")
    embeds.append(e5)

    return embeds


async def setup_bot_commands_channel(guild):
    """Post the permanent guide in the bot commands channel. Re-posts if any part is missing."""
    channel = discord.utils.get(guild.text_channels, name=BOT_COMMANDS_CHANNEL_NAME)
    if not channel:
        return

    # Check if guide is intact — we need BOTH the banner AND the guide embeds
    bot_messages = []
    try:
        async for message in channel.history(limit=50):
            if message.author == bot.user:
                bot_messages.append(message)
    except:
        pass

    # We need exactly 2 bot messages (banner + guide embeds)
    # If anything is missing or partial, wipe and re-post
    if len(bot_messages) >= 2:
        has_banner = any(m.attachments or m.content.startswith("👑") for m in bot_messages)
        has_guide = any(m.embeds and len(m.embeds) >= 3 for m in bot_messages)
        if has_banner and has_guide:
            return  # Guide fully intact, skip

    # Guide missing or partial — clear ALL old bot messages and re-post fresh
    for msg in bot_messages:
        try:
            await msg.delete()
        except:
            pass

    # Build and brand all guide embeds
    embeds = build_bot_guide_embeds()
    for e in embeds:
        apply_branding(e, thumbnail=True)

    try:
        # 1. Send dark logo as banner
        files = []
        if os.path.exists(LOGO_DARK):
            files.append(discord.File(LOGO_DARK, filename="majestic_dominion.png"))

        banner_msg = await channel.send(
            content="👑 **WELCOME TO THE MAJESTIC DOMINION** 👑\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            files=files
        )

        # 2. Send guide embeds
        guide_msg = await channel.send(embeds=embeds[:5])

        # Store both IDs
        squad_data[BOT_GUIDE_POSTED_KEY] = str(guide_msg.id)
        squad_data["bot_guide_banner_id"] = str(banner_msg.id)
        save_data(squad_data)
        print(f"👑 Bot guide posted in #{BOT_COMMANDS_CHANNEL_NAME}")
    except Exception as e:
        print(f"⚠️ Could not post guide: {e}")


@tasks.loop(hours=1)
async def bot_commands_cleanup_task():
    """Clean and REPOST the bot commands channel daily at 04:00 UTC."""
    now = datetime.utcnow()
    if now.hour != 4:
        return

    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name=BOT_COMMANDS_CHANNEL_NAME)
        if not channel:
            continue

        try:
            # Delete ALL messages (bot and non-bot) — full fresh repost
            deleted_count = 0
            async for message in channel.history(limit=200):
                try:
                    await message.delete()
                    deleted_count += 1
                except:
                    pass

            # Re-post the guide fresh
            await setup_bot_commands_channel(guild)

            if deleted_count > 0:
                await log_action(guild, "🧹 Daily Guide Repost",
                    f"Cleaned **{deleted_count}** messages and reposted guide in `{BOT_COMMANDS_CHANNEL_NAME}`")
        except discord.Forbidden:
            print(f"⚠️ No permission to clean #{BOT_COMMANDS_CHANNEL_NAME}")
        except Exception as e:
            print(f"⚠️ Cleanup/repost error: {e}")


@bot_commands_cleanup_task.before_loop
async def before_cleanup():
    await bot.wait_until_ready()


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
            title="📰 WEEKLY ROYAL CHRONICLE",
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

        # Upcoming events
        all_ev = squad_data.get("events", [])
        open_ev = [e for e in all_ev if e["status"] in ("open", "ongoing")]
        if open_ev:
            ev_text = ""
            for ev in open_ev[:4]:
                si = "🟢" if ev["status"] == "open" else "⚔️"
                rc = len(ev.get("registrations", []))
                ev_text += f"{si} **{ev['name']}** — {ev.get('format','?')} | 👥 {rc}\n"
            embed.add_field(name="🎪 Active Events", value=ev_text.strip(), inline=False)

        # Most active kingdom (most matches this week)
        if week_wins:
            total_week = {}
            for m in week_matches:
                total_week[m["team1"]] = total_week.get(m["team1"], 0) + 1
                total_week[m["team2"]] = total_week.get(m["team2"], 0) + 1
            if total_week:
                most_active = max(total_week, key=total_week.get)
                ma_tag = SQUADS.get(most_active, "?")
                embed.add_field(
                    name="⚔️ Most Active Kingdom",
                    value=f"**{ma_tag} {most_active}** — {total_week[most_active]} battles this week",
                    inline=True
                )

        # Fun stat of the week
        total_matches = len(squad_data["matches"])
        total_pts = sum(s["points"] for s in squad_data["squads"].values())
        fun_facts_weekly = [
            f"⚔️ The Dominion has witnessed **{total_matches}** total battles in its chronicles!",
            f"💎 A combined **{total_pts}** Glory Points have been earned across all kingdoms!",
            f"🏰 **{len(SQUADS)}** kingdoms are currently vying for the throne!",
            f"🔮 The Oracle has analysed **{total_matches}** clashes of steel — it has seen everything.",
        ]
        embed.add_field(name="📜 Chronicle Fact", value=random.choice(fun_facts_weekly), inline=False)

        embed.set_footer(text=f"⚜️ Majestic Dominion | Royal Chronicle | Week of {now.strftime('%B %d')} — *Glory awaits the bold*")
        apply_branding(embed, thumbnail=False, author=True)

        try:
            if os.path.exists(LOGO_DARK):
                file = discord.File(LOGO_DARK, filename="banner.png")
                embed.set_image(url="attachment://banner.png")
                await channel.send(embed=embed, file=file)
            else:
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

    power_bar = "█" * (power // 10) + "░" * (10 - power // 10)
    tier_icon = rank_info[1].split()[0] if rank_info else "⚜️"
    embed = discord.Embed(
        title=f"{tier_icon} {pd.get('ingame_name', 'Unknown')}",
        description=(
            f"{member.mention}\n"
            f"{rank_info[1]} — *{rank_info[2]}*\n"
            f"⚡ Power: `{power_bar}` **{power}/100**"
        ),
        color=sr.color if sr else ROYAL_BLUE
    )
    embed.add_field(name="⚔️ IGN", value=pd.get('ingame_name', '?'), inline=True)
    embed.add_field(name="🎯 ID", value=f"#{pd.get('ingame_id', '?')}", inline=True)
    embed.add_field(name="🏆 Rank", value=pd.get('highest_rank', '?'), inline=True)

    role = pd.get('role', '?')
    embed.add_field(name="💼 Position", value=f"{ROLE_EMOJIS.get(role, '⚔️')} {role}", inline=True)
    embed.add_field(name="💪 Power Tier", value=f"{rank_info[1]}", inline=True)

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
            description="*Select a kingdom from the royal archives to inspect:*",
            color=ROYAL_GOLD
        )
        apply_branding(embed, thumbnail=True)
        view = SquadSelectorView(purpose="browse")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await log_action(interaction.guild, "🏰 Browse", f"{interaction.user.mention} opened **Kingdom Explorer**")

    @discord.ui.button(label="Rankings", style=discord.ButtonStyle.secondary, emoji="🏆", row=0)
    async def rankings_btn(self, interaction: discord.Interaction, button: Button):
        rankings = get_squad_ranking()
        tp = (len(rankings) + 14) // 15
        embed = discord.Embed(title="👑 The Royal Leaderboard", description=f"Page 1/{tp}", color=ROYAL_GOLD)
        apply_branding(embed, thumbnail=True)
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
        embed = discord.Embed(title="⚙️ Royal Registration", description="*Declare your position before the Crown, warrior:*", color=ROYAL_PURPLE)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await log_action(interaction.guild, "⚙️ Setup", f"{interaction.user.mention} started **Profile Setup**")

    @discord.ui.button(label="Fun Stats", style=discord.ButtonStyle.secondary, emoji="🎲", row=2)
    async def fun_btn(self, interaction: discord.Interaction, button: Button):
        await show_fun_stats(interaction)
        await log_action(interaction.guild, "🎲 Fun Stats", f"{interaction.user.mention} viewed **Fun Stats**")

    @discord.ui.button(label="War Oracle", style=discord.ButtonStyle.primary, emoji="🔮", row=2)
    async def oracle_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🔮 The Royal Oracle — Prophecy of War",
            description="*The Royal Oracle peers into the mists of fate...*\n\nSelect the **first** kingdom:",
            color=ROYAL_PURPLE
        )
        await interaction.response.send_message(embed=embed, view=MatchPredictorStep1View(), ephemeral=True)
        await log_action(interaction.guild, "🔮 War Oracle", f"{interaction.user.mention} consulted the **War Oracle**")

    @discord.ui.button(label="Realm News", style=discord.ButtonStyle.success, emoji="📰", row=2)
    async def news_btn(self, interaction: discord.Interaction, button: Button):
        headlines = generate_realm_news()
        embed = discord.Embed(
            title="📰 Royal Court Gazette",
            description="*Official dispatches from the Royal Court of Majestic Dominion*",
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
                if c["status"] == "pending":
                    status = "⏳ PENDING"
                elif c["status"] == "scheduled":
                    status = f"📅 SCHEDULED — **{c.get('scheduled_date', '?')}**"
                else:
                    status = "⚔️ ACCEPTED — Awaiting schedule"
                ds = ""
                try:
                    ds = datetime.fromisoformat(c["date"]).strftime("%b %d")
                except:
                    pass
                msg_text = f"\n📜 *\"{c['message']}\"*" if c.get("message") else ""
                embed.add_field(
                    name=f"{SQUADS.get(c['challenger'], '?')} {c['challenger']} vs {SQUADS.get(c['challenged'], '?')} {c['challenged']}",
                    value=f"{status}{msg_text}\n📅 Issued {ds} | 🆔 `{c['id']}`",
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
        embed = discord.Embed(title="👑 The Royal Leaderboard", description=f"Page {page}/{tp}", color=ROYAL_GOLD)
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

        # Capture pre-match ranks for rank change announcements
        t1_old_rank = get_squad_rank(self.team1_name)
        t2_old_rank = get_squad_rank(self.team2_name)

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
            if c["status"] in ("accepted", "scheduled"):
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

        embed = discord.Embed(title="📜 The Royal Chronicles Are Written", description=f"{result_text}\n\n*{flavor_quote}*", color=ROYAL_GOLD)
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

        # --- Public announcement in #『🏆』war-results ---
        t1_tag = SQUADS.get(self.team1_name, "?")
        t2_tag = SQUADS.get(self.team2_name, "?")
        score_parts = self.result.value.split("-")
        s1_disp, s2_disp = score_parts[0], score_parts[1] if len(score_parts) > 1 else "?"

        if actual_winner != "draw":
            w_name = actual_winner
            l_name = self.team2_name if actual_winner == self.team1_name else self.team1_name
            w_tag  = SQUADS.get(w_name, "?")
            l_tag  = SQUADS.get(l_name, "?")
            w_pts  = t1_pts if actual_winner == self.team1_name else t2_pts
            l_pts  = t2_pts if actual_winner == self.team1_name else t1_pts
            w_tags = glory_tags_t1 if actual_winner == self.team1_name else glory_tags_t2
            w_si   = squad_data["squads"].get(w_name, {})
            l_si   = squad_data["squads"].get(l_name, {})
            pub_desc = (
                f"### {w_tag} {w_name} ⚔️ {l_tag} {l_name}\n"
                f"*{flavor_quote}*"
            )
            pub_embed = discord.Embed(title="⚔️ BATTLE CONCLUDED!", description=pub_desc, color=ROYAL_GOLD)
            pub_embed.add_field(
                name=f"🏆 {w_tag} {w_name} — VICTORY",
                value=(
                    f"**Score: {self.result.value}**\n"
                    f"💎 +**{w_pts}** Glory Points\n"
                    + (" ".join(w_tags) + "\n" if w_tags else "")
                    + f"📊 {w_si.get('wins',0)}W-{w_si.get('draws',0)}D-{w_si.get('losses',0)}L | {w_si.get('points',0)} pts total"
                ),
                inline=True
            )
            pub_embed.add_field(
                name=f"💀 {l_tag} {l_name} — Defeat",
                value=(
                    f"**Score: {self.result.value}**\n"
                    f"💎 +**{l_pts}** pts\n"
                    f"📊 {l_si.get('wins',0)}W-{l_si.get('draws',0)}D-{l_si.get('losses',0)}L | {l_si.get('points',0)} pts total"
                ),
                inline=True
            )
        else:
            w_si = squad_data["squads"].get(self.team1_name, {})
            l_si = squad_data["squads"].get(self.team2_name, {})
            pub_embed = discord.Embed(
                title="⚖️ THE THRONE STANDS STILL — DRAW!",
                description=f"### {t1_tag} {self.team1_name} ⚖️ {t2_tag} {self.team2_name}\n*{flavor_quote}*",
                color=ROYAL_BLUE
            )
            pub_embed.add_field(
                name=f"{t1_tag} {self.team1_name}",
                value=f"**{self.result.value}** | +1 pt | {w_si.get('points',0)} pts total", inline=True
            )
            pub_embed.add_field(
                name=f"{t2_tag} {self.team2_name}",
                value=f"**{self.result.value}** | +1 pt | {l_si.get('points',0)} pts total", inline=True
            )

        pub_embed.add_field(name="🔮 Oracle Verdict", value=oracle_text, inline=False)
        pub_embed.set_footer(text=f"⚔️ Match #{match_id} | {datetime.utcnow().strftime('%b %d, %Y · %H:%M')} UTC | ⚜️ Majestic Dominion")
        await announce_match(interaction.guild, pub_embed)

        # --- Live Streak Alerts ---
        await announce_streak(interaction.guild, self.team1_name, team1_streak["type"], team1_streak["count"])
        await announce_streak(interaction.guild, self.team2_name, team2_streak["type"], team2_streak["count"])

        # --- Rank Change Alerts ---
        t1_new_rank = get_squad_rank(self.team1_name)
        t2_new_rank = get_squad_rank(self.team2_name)
        await announce_rank_change(interaction.guild, self.team1_name, t1_old_rank, t1_new_rank)
        await announce_rank_change(interaction.guild, self.team2_name, t2_old_rank, t2_new_rank)

        # --- Achievement Alerts ---
        all_new_achievements = []
        if team1_achievements:
            for a in team1_achievements:
                all_new_achievements.append(f"{a['name']} — **{SQUADS.get(self.team1_name, '?')} {self.team1_name}**")
        if team2_achievements:
            for a in team2_achievements:
                all_new_achievements.append(f"{a['name']} — **{SQUADS.get(self.team2_name, '?')} {self.team2_name}**")
        if all_new_achievements:
            ach_embed = discord.Embed(
                title="🏅 THE CROWN BESTOWS HONOUR!",
                description=(
                    "*The royal trumpets sound across the Dominion...*\n\n"
                    + "\n".join(f"🎖️ {a}" for a in all_new_achievements)
                    + "\n\n*Glory earned in the fires of battle!*"
                ),
                color=ROYAL_GOLD
            )
            ach_embed.set_footer(text="⚜️ Majestic Dominion | Honour is forever inscribed in the chronicles")
            apply_branding(ach_embed, thumbnail=True)
            await announce_event(interaction.guild, ach_embed)


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

        # Public announcement
        pub = discord.Embed(
            title="🏆 THE CROWN BESTOWS A ROYAL TITLE!",
            description=f"{pe} **{SQUADS.get(self.squad_name, '?')} {self.squad_name}** has earned:\n\n**{full_title}**",
            color=ROYAL_GOLD
        )
        if self.position.value.lower() in ["1st", "first", "1"]:
            pub.add_field(name="👑 Championship!", value=f"Total Championships: **{squad_info['championship_wins']}**", inline=False)
            pub.description += "\n\n🎉 *All hail the champions of the Dominion!*"
        pub.set_footer(text="⚜️ Majestic Dominion | Glory to the victors!")
        await announce_major(interaction.guild, pub)


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
            embed.set_footer(text="⚜️ Majestic Dominion | A new chapter is written in the royal chronicles!")
            await interaction.followup.send(embed=embed, ephemeral=True)
            await log_action(interaction.guild, "🏰 Kingdom Founded",
                f"{interaction.user.mention} created **{tag} {name}**" + (f" with guest role `{grn}`" if grn else ""))

            # Public announcement
            pub = discord.Embed(
                title="🏰 A NEW SOVEREIGN POWER RISES!",
                description=f"**{tag} {name}** has been founded!\n\n*A new banner unfurls in the Majestic Dominion. Will they conquer or crumble?*",
                color=ROYAL_GREEN
            )
            pub.set_footer(text=f"Founded by {interaction.user.display_name} | ⚜️ Majestic Dominion")
            await announce_major(interaction.guild, pub)

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
            pub = discord.Embed(
                title="💀 A SOVEREIGN POWER HAS FALLEN!",
                description=f"**{self.squad_name}** has been disbanded.\n*{self.member_count} warriors left without a banner...*",
                color=ROYAL_RED
            )
            pub.set_footer(text="⚜️ Majestic Dominion | The Crown remembers.")
            await announce_major(interaction.guild, pub)
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
            pub = discord.Embed(
                title="💀 A SOVEREIGN POWER HAS FALLEN!",
                description=f"**{self.squad_name}** has been disbanded.\n*Their legacy fades from the chronicles...*",
                color=ROYAL_RED
            )
            pub.set_footer(text="⚜️ Majestic Dominion | The Crown remembers.")
            await announce_major(interaction.guild, pub)
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
                        await role.edit(name=new_name, reason=f"Majestic Dominion: Renamed '{old}' → '{new_name}'")
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
                                await old_gr.edit(name=new_guest, reason=f"Majestic Dominion: Guest role renamed for '{actual_name}'")
                            except:
                                pass
                    else:
                        # No old guest role — create one
                        try:
                            await guild.create_role(
                                name=new_guest,
                                mentionable=False,
                                reason=f"Majestic Dominion: Guest role for '{actual_name}'"
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
            embed.set_footer(text="⚜️ Majestic Dominion | The royal chronicles have been rewritten!")
            await interaction.followup.send(embed=embed, ephemeral=True)
            await log_action(guild, "✏️ Kingdom Edited",
                f"{interaction.user.mention} edited **{actual_name}**: " + ", ".join(changes))

            # Announce name changes publicly
            if name_changed:
                pub = discord.Embed(
                    title="✏️ A KINGDOM IS REBORN!",
                    description=f"**{self.old_name}** is now known as **{SQUADS.get(actual_name, '?')} {actual_name}**!\n\n*The royal scribes rewrite the chronicles — a new chapter begins.*",
                    color=ROYAL_PURPLE
                )
                pub.set_footer(text="⚜️ Majestic Dominion | The chronicles have been rewritten.")
                await announce_major(guild, pub)

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
            title="🔮 The Royal Oracle — Pre-Battle Prophecy",
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

    @discord.ui.button(label="Bounties", style=discord.ButtonStyle.primary, emoji="💰", row=4)
    async def bounty_btn(self, interaction: discord.Interaction, button: Button):
        refresh_bounties()
        save_data(squad_data)
        embed = build_bounty_embed()
        embed.title = "💰 Bounty Manager"
        await interaction.response.send_message(embed=embed, view=ManageBountiesView(), ephemeral=True)
        await log_action(interaction.guild, "💰 Bounties", f"{interaction.user.mention} opened **Bounty Manager**")

    @discord.ui.button(label="Challenges", style=discord.ButtonStyle.secondary, emoji="🎯", row=4)
    async def challenges_btn(self, interaction: discord.Interaction, button: Button):
        all_ch = squad_data.get("challenges", [])
        active = [c for c in all_ch if c["status"] in ("pending", "accepted", "scheduled")]
        embed = discord.Embed(title="🎯 Challenge Manager", color=ROYAL_RED)
        if not active:
            embed.description = "*No active challenges.*"
        else:
            for c in active[:10]:
                status = "⏳ PENDING" if c["status"] == "pending" else "⚔️ ACCEPTED" if c["status"] == "accepted" else "📅 SCHEDULED"
                ds = ""
                try:
                    ds = datetime.fromisoformat(c["date"]).strftime("%b %d")
                except:
                    pass
                sched = ""
                if c.get("scheduled_date"):
                    sched = f"\n📅 **Scheduled: {c['scheduled_date']}**"
                embed.add_field(
                    name=f"{SQUADS.get(c['challenger'], '?')} {c['challenger']} vs {SQUADS.get(c['challenged'], '?')} {c['challenged']}",
                    value=f"{status} | 📅 Issued {ds} | 🆔 `{c['id']}`{sched}",
                    inline=False
                )
        embed.set_footer(text="Use buttons below to manage challenges")
        await interaction.response.send_message(embed=embed, view=ManageChallengesView(), ephemeral=True)
        await log_action(interaction.guild, "🎯 Challenges", f"{interaction.user.mention} opened **Challenge Manager**")

    @discord.ui.button(label="Announce", style=discord.ButtonStyle.success, emoji="📢", row=4)
    async def announce_btn(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="📢 Royal Announcement",
            description="*Choose where to publish your decree, Your Grace:*",
            color=ROYAL_GOLD
        )
        await interaction.response.send_message(embed=embed, view=AnnouncementChannelView(), ephemeral=True)
        await log_action(interaction.guild, "📢 Announce", f"{interaction.user.mention} started **Royal Announcement**")

    @discord.ui.button(label="Events", style=discord.ButtonStyle.primary, emoji="🎪", row=4)
    async def events_btn(self, interaction: discord.Interaction, button: Button):
        embed = build_event_manager_embed()
        await interaction.response.send_message(embed=embed, view=EventManagerViewV2(), ephemeral=True)
        await log_action(interaction.guild, "🎪 Events", f"{interaction.user.mention} opened **Event Manager**")


async def show_recent_matches(interaction, limit=10):
    recent = squad_data["matches"][-limit:][::-1]
    if not recent:
        await interaction.response.send_message("📜 No matches recorded yet.", ephemeral=True)
        return
    embed = discord.Embed(title="📜 Recent Royal Decrees of War", description=f"Last {len(recent)} matches", color=ROYAL_PURPLE)
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
            embed = discord.Embed(title="👥 Majestic Member", description="*All powers granted to citizens of the Dominion via `/member`*", color=ROYAL_BLUE)
            embed.add_field(name="🏰 Browse Kingdoms", value="Explore any kingdom's profile, roster, and match history", inline=False)
            embed.add_field(name="🏆 Rankings", value="View the full leaderboard with points and win rates", inline=False)
            embed.add_field(name="👤 View Profile", value="Search any warrior by name and view their full profile with power rating", inline=False)
            embed.add_field(name="🛡️ My Kingdom", value="View your own kingdom's detailed profile", inline=False)
            embed.add_field(name="⚜️ My Profile", value="View your royal warrior scroll", inline=False)
            embed.add_field(name="⚙️ Setup Profile", value="Register your identity with the Crown", inline=False)
            embed.add_field(name="🎲 Fun Stats", value="Royal court curiosities and realm trivia", inline=False)
            embed.add_field(name="🔮 War Oracle", value="AI-powered match predictor — see win probabilities before battles!", inline=False)
            embed.add_field(name="📰 Realm News", value="Auto-generated news bulletin with latest headlines", inline=False)
            embed.add_field(name="💰 Bounties", value="View the Bounty Board — beat top-ranked kingdoms for bonus Glory Points!", inline=False)
            embed.add_field(name="🎯 Challenges", value="See all active war challenges between kingdoms", inline=False)
            embed.add_field(name="🚪 Leave Kingdom", value="Leave your current kingdom (profile preserved)", inline=False)
            embed.add_field(name="\n📌 Profile Viewing", value="Use `/profile @user` or the **View Profile** button (smart search) to view anyone's profile!", inline=False)
        elif cat == "leader":
            embed = discord.Embed(title="👑 Sovereign Commander's Guide", description="*All sovereign powers granted to kingdom leaders via `/leader`*", color=ROYAL_GOLD)
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
            embed = discord.Embed(title="🛡️ Royal Council Guide", description="*All council powers granted to moderators via `/mod`*", color=ROYAL_PURPLE)
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
            embed.add_field(name="💰 Bounties", value="Add, remove, or clear all bounties — full bounty manager", inline=False)
            embed.add_field(name="🎯 Challenges", value="Schedule matches, cancel challenges, clear old ones — full challenge manager", inline=False)
            embed.add_field(name="📢 Announce", value="Publish royal announcements to Announcements, Tournament News, or War Results with @MAJESTIC ping and images", inline=False)
            embed.add_field(name="🎪 Events", value="Create · Edit · Delete · Start · Close · View Registrations · Remove Registrant · Randomize (Single/Double/RR/Groups) · Schedule matches", inline=False)
            embed.add_field(name="📋 /profiles", value="Royal Census — view all registered warriors by kingdom", inline=False)
        else:  # help
            embed = discord.Embed(title="📜 Royal Codex of the Dominion", description="Quick guide to all commands", color=ROYAL_PURPLE)
            embed.add_field(name="🎯 Slash Commands", value=(
                "`/member` — Member panel (browse, rankings, profile, etc.)\n"
                "`/leader` — Leader panel (manage roster & kingdom)\n"
                "`/mod` — Moderator panel (matches & titles)\n"
                "`/profile @user` — View anyone's profile\n"
                "`/profiles` — Royal Census of registered warriors (council only)\n"
                "`/guide` — Re-post the bot guide in commands channel (council only)\n"
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
                "• Challenges are announced in **#『🏆』war-results**\n"
                "• Top 3 kingdoms always have **auto-bounties**\n"
                "• Mods can **manage bounties** (add/remove/clear) from `/mod`\n"
            ), inline=False)
            embed.add_field(name="📢 Live Channels", value=(
                "**『🏆』war-results** — Matches · Streaks · Ranks · Challenges · Event notices · Brackets · Schedules · Daily Pulse · Weekly Chronicle\n"
                "**『📢』Announcements** — New event full announcements (image, prize, details) · Official decrees\n"
                "**『🗞️』Tournament News** — Tournament-specific announcements"
            ), inline=False)
            embed.add_field(name="💡 Tips", value=(
                "• **View Profile / Add Member / Give Guest** use smart search — just type part of a name!\n"
                "• **All mod actions** use dropdowns — no typing squad names needed!\n"
                "• Browse any kingdom and click **🧠 AI Analysis** for a full intelligence report\n"
                "• **Rivalries** can be checked from any kingdom's profile (⚔️ button)\n"
                "• Everything is button & modal-based — minimal typing needed!"
            ), inline=False)

        embed.set_footer(text="⚜️ Majestic Dominion | May the Crown guide your path")
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# =====================================================================
#                     SLASH COMMANDS (Clean & Minimal)
# =====================================================================

@bot.tree.command(name="member", description="⚜️ Enter the Royal Court of the Dominion")
async def member_command(interaction: discord.Interaction):
    view = MemberPanelView()
    ur, ut = get_member_squad(interaction.user, interaction.guild)
    sq_text = f"\n🛡️ **Your Kingdom:** {ut} {ur.name}" if ur else "\n⚔️ **Status:** Free Agent"

    rankings = get_squad_ranking()
    top = rankings[0] if rankings else None
    tm = len(squad_data["matches"])

    embed = discord.Embed(
        title="⚜️ The Royal Court of Majestic Dominion",
        description=f"*Hail,* **{interaction.user.display_name}**! *Welcome to the Royal Court.*{sq_text}",
        color=ROYAL_BLUE
    )
    embed.add_field(name="🌟 The Realm", value=(
        f"🏰 {len(SQUADS)} kingdoms • ⚔️ {tm} battles" + (f" • 👑 {top['name']} leads" if top else "") +
        f"\n💰 {len(squad_data.get('bounties', {}))} bounties • 🎯 {len([c for c in squad_data.get('challenges', []) if c['status'] in ('pending', 'accepted')])} active challenges"
    ), inline=False)

    # Show open events in member panel
    open_events = [e for e in squad_data.get("events", []) if e["status"] in ("open", "ongoing")]
    if open_events:
        ev_lines = []
        for ev in open_events[:3]:
            si  = "🟢" if ev["status"] == "open" else "⚔️"
            rc  = len(ev.get("registrations", []))
            mx  = f"/{ev['max_entries']}" if ev.get("max_entries") else ""
            pp  = f" · 💰 {ev['prize_pool']}" if ev.get("prize_pool") else ""
            ev_lines.append(f"{si} **{ev['name']}** — {ev.get('format','?')} · 👥 {rc}{mx}{pp}")
        embed.add_field(
            name=f"🎪 Open Events ({len(open_events)})",
            value="\n".join(ev_lines) + "\n*Use `/events` to register!*",
            inline=False
        )

    # Show player's power rating if they have a profile
    power, rank_info = calculate_power_rating(interaction.user.id)
    if power > 0:
        embed.add_field(name="💪 Your Power", value=f"{rank_info[1]} — **{power}/100**", inline=False)

    embed.set_thumbnail(url=get_bot_logo() or interaction.user.display_avatar.url)
    embed.set_footer(text="⚜️ Majestic Dominion | Long live the Crown")
    await interaction.response.send_message(embed=embed, view=view)
    await log_action(interaction.guild, "📋 /member", f"{interaction.user.mention} opened **Member Panel**")


@bot.tree.command(name="leader", description="👑 Open your Sovereign Command Chamber")
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
        title=f"👑 {sr.name} — Sovereign Command",
        description=f"*Your Royal Highness,* **{interaction.user.display_name}** — *the throne awaits your command.*",
        color=sr.color if sr.color != discord.Color.default() else ROYAL_GOLD
    )
    embed.add_field(name="📊 Quick Status", value=f"👥 {len(sr.members)} members • ⭐ {mr_count}/5 mains • 🔄 {sub_count}/3 subs", inline=False)

    # Show active challenges for this kingdom
    active_ch = get_active_challenges(sr.name)
    if active_ch:
        ch_text = ""
        for c in active_ch[:3]:
            opp = c["challenged"] if c["challenger"] == sr.name else c["challenger"]
            status_e = "⏳" if c["status"] == "pending" else "📅" if c["status"] == "scheduled" else "⚔️"
            direction = "→" if c["challenger"] == sr.name else "←"
            sched = f" — **{c['scheduled_date']}**" if c.get("scheduled_date") else ""
            ch_text += f"{status_e} {direction} **{SQUADS.get(opp, '?')} {opp}** ({c['status']}){sched}\n"
        embed.add_field(name="🎯 Active Challenges", value=ch_text, inline=False)

    # Show if there's a bounty on this kingdom
    bounty = squad_data.get("bounties", {}).get(sr.name)
    if bounty:
        embed.add_field(name="💰 Bounty Alert!", value=f"**+{bounty['points']}** Glory Points bounty on your kingdom!", inline=False)

    embed.set_footer(text="⚜️ Majestic Dominion | Lead with honor, reign with glory")
    apply_branding(embed, thumbnail=True)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    await log_action(interaction.guild, "📋 /leader", f"{interaction.user.mention} opened **Leader Panel** for **{sr.name}**")


@bot.tree.command(name="mod", description="🛡️ Enter the Royal Council Chamber")
async def mod_command(interaction: discord.Interaction):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("❌ Only **Moderators** can access this.", ephemeral=True)
        return
    view = ModeratorPanelView()
    embed = discord.Embed(
        title="🛡️ Royal Council Chamber",
        description="*The Royal Council Chamber — govern the Dominion with wisdom and authority.*",
        color=ROYAL_PURPLE
    )
    embed.add_field(name="📊 Stats", value=(
        f"⚔️ {len(squad_data['matches'])} matches • 🏰 {len(SQUADS)} kingdoms\n"
        f"🎯 {len([c for c in squad_data.get('challenges', []) if c['status'] in ('pending', 'accepted')])} active challenges • "
        f"💰 {len(squad_data.get('bounties', {}))} bounties"
    ), inline=False)
    embed.set_footer(text="⚜️ Majestic Dominion | The Council sees all")
    apply_branding(embed, thumbnail=True)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    await log_action(interaction.guild, "📋 /mod", f"{interaction.user.mention} opened **Moderator Panel**")


@bot.tree.command(name="profile", description="⚜️ Inspect a warrior's royal scroll")
@app_commands.describe(member="Tag the warrior to view")
async def profile_command(interaction: discord.Interaction, member: discord.Member):
    await show_player_profile(interaction, member, public=True)
    await log_action(interaction.guild, "👤 /profile", f"{interaction.user.mention} viewed profile of {member.mention}")


@bot.tree.command(name="profiles", description="📜 Royal Census — view all registered warriors")
async def profiles_command(interaction: discord.Interaction):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("❌ Only the **Royal Council** may access the census.", ephemeral=True)
        return

    guild = interaction.guild
    completed = []

    for pk, pd in squad_data["players"].items():
        ign = pd.get("ingame_name", "")
        gid = pd.get("ingame_id", "")
        rank = pd.get("highest_rank", "")
        role = pd.get("role", "")
        squad = pd.get("squad", "")

        if not (ign and gid and rank and role):
            continue

        member = guild.get_member(int(pk)) if pk.isdigit() else None
        mention = member.mention if member else f"`{pk}`"
        completed.append({
            "mention": mention, "ign": ign, "id": gid,
            "rank": rank, "role": role, "squad": squad
        })

    if not completed:
        embed = discord.Embed(
            title="📜 Royal Census",
            description="*The scrolls are empty. No warriors have completed their registration.*",
            color=ROYAL_PURPLE
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Group by squad
    by_squad = {}
    for p in completed:
        sq = p["squad"] or "Free Agent"
        if sq not in by_squad:
            by_squad[sq] = []
        by_squad[sq].append(p)

    squad_names = sorted(by_squad.keys())
    await interaction.response.send_message(
        embed=build_census_page(by_squad, squad_names, 0, len(completed)),
        view=CensusPageView(by_squad, squad_names, 0, interaction.user.id, len(completed)),
        ephemeral=True
    )
    await log_action(guild, "📜 /profiles",
        f"{interaction.user.mention} viewed **Royal Census** — {len(completed)} registered warriors")


def build_census_page(by_squad, squad_names, page, total_warriors):
    """Build a single census page (one kingdom per page, or summary on page 0)."""
    total_pages = len(squad_names) + 1  # page 0 = summary, page 1+ = kingdoms

    if page == 0:
        # Summary page
        embed = discord.Embed(
            title="📜 Royal Census — Registered Warriors",
            description=f"**{total_warriors}** warriors have completed their registration across **{len(squad_names)}** kingdoms.\n\n*Use the buttons below to browse each kingdom's roster.*",
            color=ROYAL_GOLD
        )
        # Quick overview of each kingdom's count
        overview = ""
        for sq_name in squad_names:
            tag = SQUADS.get(sq_name, "⚔️")
            count = len(by_squad[sq_name])
            overview += f"{tag} **{sq_name}** — {count} warriors\n"
        if overview:
            embed.add_field(name="👑 Kingdom Overview", value=overview[:1024], inline=False)
        embed.set_footer(text=f"⚜️ Page 1/{total_pages} | Majestic Dominion Royal Census")
        return embed
    else:
        # Kingdom roster page
        idx = page - 1
        if idx >= len(squad_names):
            idx = len(squad_names) - 1
        sq_name = squad_names[idx]
        members_list = by_squad[sq_name]
        tag = SQUADS.get(sq_name, "⚔️")

        embed = discord.Embed(
            title=f"{tag} {sq_name} — Royal Roster",
            description=f"**{len(members_list)}** registered warriors",
            color=ROYAL_PURPLE
        )

        # Split into chunks of 10 to stay under field limits
        for i in range(0, len(members_list), 10):
            chunk = members_list[i:i+10]
            lines = []
            for p in chunk:
                lines.append(f"{p['mention']} — `{p['ign']}` | {p['rank']} | {p['role']}")
            text = "\n".join(lines)
            if len(text) > 1024:
                text = text[:1020] + "..."
            field_name = "⚔️ Warriors" if i == 0 else f"⚔️ Warriors (cont.)"
            embed.add_field(name=field_name, value=text, inline=False)
            if embed.fields and len(embed.fields) >= 5:
                break  # Safety: max 5 fields per page

        embed.set_footer(text=f"⚜️ Page {page + 1}/{total_pages} | Majestic Dominion Royal Census")
        return embed


class CensusPageView(View):
    """Paginated view for /profiles royal census."""
    def __init__(self, by_squad, squad_names, page, author_id, total_warriors):
        super().__init__(timeout=180)
        self.by_squad = by_squad
        self.squad_names = squad_names
        self.page = page
        self.author_id = author_id
        self.total_warriors = total_warriors
        self.total_pages = len(squad_names) + 1
        self._update_buttons()

    def _update_buttons(self):
        self.prev_btn.disabled = self.page <= 0
        self.next_btn.disabled = self.page >= self.total_pages - 1

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary, row=0)
    async def prev_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Not your census.", ephemeral=True)
        self.page = max(0, self.page - 1)
        self._update_buttons()
        await interaction.response.edit_message(
            embed=build_census_page(self.by_squad, self.squad_names, self.page, self.total_warriors),
            view=self
        )

    @discord.ui.button(label="▶ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Not your census.", ephemeral=True)
        self.page = min(self.total_pages - 1, self.page + 1)
        self._update_buttons()
        await interaction.response.edit_message(
            embed=build_census_page(self.by_squad, self.squad_names, self.page, self.total_warriors),
            view=self
        )


@bot.tree.command(name="guide", description="📖 Re-post the bot guide in the commands channel (Moderator only)")
async def guide_command(interaction: discord.Interaction):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("❌ Only the **Royal Council** may use this.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    channel = discord.utils.get(interaction.guild.text_channels, name=BOT_COMMANDS_CHANNEL_NAME)
    if not channel:
        await interaction.followup.send(f"❌ Channel `{BOT_COMMANDS_CHANNEL_NAME}` not found.", ephemeral=True)
        return

    # Delete all bot messages in the channel first
    try:
        async for message in channel.history(limit=50):
            if message.author == bot.user:
                try:
                    await message.delete()
                except:
                    pass
    except:
        pass

    # Clear stored IDs so setup re-posts
    squad_data.pop(BOT_GUIDE_POSTED_KEY, None)
    squad_data.pop("bot_guide_banner_id", None)
    save_data(squad_data)

    # Re-post
    await setup_bot_commands_channel(interaction.guild)

    await interaction.followup.send(
        embed=discord.Embed(
            title="✅ Guide Re-posted!",
            description=f"The bot guide has been refreshed in {channel.mention}.",
            color=ROYAL_GREEN
        ),
        ephemeral=True
    )
    await log_action(interaction.guild, "📖 /guide", f"{interaction.user.mention} re-posted the **Bot Guide**")


@bot.tree.command(name="help", description="📜 Open the Royal Codex of the Dominion")
async def help_command(interaction: discord.Interaction):
    view = HelpView()
    embed = discord.Embed(
        title="📜 Royal Codex of the Dominion",
        description="*The sacred texts of the Majestic Dominion — select a chapter:*",
        color=ROYAL_PURPLE
    )
    embed.add_field(name="🎯 Commands", value=(
        "`/member` — Royal Court — browse, rankings, oracle, bounties, challenges\n"
        "`/leader` — Sovereign Command — manage roster, set mains, challenge kingdoms\n"
        "`/mod` — Royal Council — record battles, manage events & bounties\n"
        "`/events` — Browse & register for upcoming events\n"
        "`/profile @user` — View any warrior's royal scroll\n"
        "`/profiles` — Royal Census (council only)\n"
        "`/guide` — Re-post bot guide (council only)\n"
        "`/restore` — Restore data from backup (council only)\n"
        "`/help` — This menu"
    ), inline=False)
    embed.add_field(name="🎪 Events Quick Guide", value=(
        "Use `/events` to see all open events.\n"
        "• 👤 **Solo** — one click to join\n"
        "• 👥 **Small Team** — leader registers + teammate IDs\n"
        "• 👑 **5v5** — kingdom leaders only, uses your squad\n"
        "• Click **❌ Cancel Registration** to withdraw"
    ), inline=False)
    embed.set_footer(text="⚜️ Majestic Dominion | Select a category below for full details")
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    await log_action(interaction.guild, "📜 /help", f"{interaction.user.mention} opened **Help Menu**")


@bot.tree.command(name="restore", description="💾 Restore the royal archives from a backup scroll")
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


# =====================================================================
#                    TOURNAMENT ENGINE v2
# =====================================================================

# =====================================================================
#                    TOURNAMENT ENGINE v2 — INTELLIGENT ESPORTS CORE
# =====================================================================
#
# Architecture:
#   TournamentEngine   — bracket logic, auto-progression, result recording
#   EventMatchViews    — mod tools: record results, manage registrants,
#                        force-advance, reschedule, live dashboard
#   ProfessionalAnnouncements — cinematic embeds for every event moment
#   Lifecycle states   — registration → check-in → seeding → live → ended
# =====================================================================

# ── Event & Match constants ───────────────────────────────────────────

EVENT_STATUS_LABELS = {
    "open":         ("🟢", "Registration Open"),
    "checkin":      ("⏰", "Check-In Phase"),
    "seeding":      ("🎲", "Seeding Phase"),
    "live":         ("⚔️", "Tournament Live"),
    "completed":    ("🏆", "Concluded"),
    "cancelled":    ("❌", "Cancelled"),
}

MATCH_STATUS_LABELS = {
    "pending":   ("⏳", "Pending"),
    "scheduled": ("📅", "Scheduled"),
    "live":      ("⚔️", "Live"),
    "completed": ("✅", "Completed"),
    "cancelled": ("❌", "Cancelled"),
    "bye":       ("🚪", "BYE"),
}

ROUND_NAMES_SE = [
    "Grand Final", "Semi-Finals", "Quarter-Finals",
    "Round of 16", "Round of 32", "Round of 64", "Round of 128"
]

BO_OPTIONS = {"bo1": "Best of 1", "bo3": "Best of 3", "bo5": "Best of 5"}


# ── TournamentEngine ─────────────────────────────────────────────────

class TournamentEngine:
    """
    Static methods that drive ALL bracket logic.
    Every method operates on the event dict in-place.
    """

    # ── Match lookup ─────────────────────────────────────────────────

    @staticmethod
    def all_matches(event) -> list:
        """Flat list of every match in bracket_data."""
        bd = event.get("bracket_data")
        if not bd:
            return []
        system = bd.get("system", "")
        out = []

        if system == "single_elim":
            for ri, rnd in enumerate(bd.get("rounds", [])):
                for m in rnd:
                    m2 = dict(m)
                    m2.setdefault("round_idx", ri)
                    m2.setdefault("status", "pending")
                    out.append(m2)

        elif system == "double_elim":
            for ri, rnd in enumerate(bd.get("winners", [])):
                for m in rnd:
                    m2 = dict(m); m2["round_idx"] = ri; m2["bracket"] = "wb"
                    m2.setdefault("status", "pending"); out.append(m2)
            for ri, rnd in enumerate(bd.get("losers", [])):
                for m in rnd:
                    m2 = dict(m); m2["round_idx"] = ri; m2["bracket"] = "lb"
                    m2.setdefault("status", "pending"); out.append(m2)
            gf = bd.get("grand_final")
            if gf:
                m2 = dict(gf); m2["bracket"] = "gf"
                m2.setdefault("status", "pending"); out.append(m2)

        elif system in ("round_robin", "groups", "group_bracket"):
            for m in bd.get("matches", []):
                m2 = dict(m); m2.setdefault("status", "pending"); out.append(m2)
            bracket = bd.get("bracket")
            if bracket:
                for ri, rnd in enumerate(bracket.get("rounds", [])):
                    for m in rnd:
                        m2 = dict(m); m2["round_idx"] = ri
                        m2.setdefault("status", "pending"); out.append(m2)

        elif system in ("random_draw", "random_teams"):
            for i, m in enumerate(bd.get("matches", [])):
                m2 = dict(m); m2.setdefault("status", "pending"); out.append(m2)

        return out

    @staticmethod
    def find_match(event, match_id) -> dict | None:
        """Find match by ID and return a REFERENCE (not copy) to the dict inside bracket_data."""
        bd = event.get("bracket_data")
        if not bd:
            return None
        system = bd.get("system", "")

        def _search(lst):
            for m in lst:
                if m.get("match_id") == match_id:
                    return m
            return None

        if system == "single_elim":
            for rnd in bd.get("rounds", []):
                m = _search(rnd)
                if m: return m

        elif system == "double_elim":
            for rnd in bd.get("winners", []):
                m = _search(rnd); 
                if m: return m
            for rnd in bd.get("losers", []):
                m = _search(rnd)
                if m: return m
            gf = bd.get("grand_final")
            if gf and gf.get("match_id") == match_id:
                return gf

        elif system in ("round_robin", "groups", "group_bracket"):
            m = _search(bd.get("matches", []))
            if m: return m
            bracket = bd.get("bracket")
            if bracket:
                for rnd in bracket.get("rounds", []):
                    m = _search(rnd)
                    if m: return m

        elif system in ("random_draw", "random_teams"):
            m = _search(bd.get("matches", []))
            if m: return m

        return None

    @staticmethod
    def pending_matches(event) -> list:
        """Matches that haven't been completed yet (excluding BYEs)."""
        return [m for m in TournamentEngine.all_matches(event)
                if m.get("status") not in ("completed", "cancelled", "bye")
                and m.get("team2") not in ("BYE", "TBD")
                and m.get("team1") not in ("BYE", "TBD")]

    @staticmethod
    def current_round_matches(event) -> list:
        """Matches belonging to the current active round."""
        bd = event.get("bracket_data")
        if not bd:
            return []
        system = bd.get("system", "")
        cur = bd.get("current_round", 0)

        if system == "single_elim":
            rounds = bd.get("rounds", [])
            if cur < len(rounds):
                return [m for m in rounds[cur]
                        if m.get("team2") != "BYE" and m.get("team1") != "BYE"]
        elif system in ("round_robin", "groups", "group_bracket", "random_draw", "random_teams"):
            return TournamentEngine.pending_matches(event)
        elif system == "double_elim":
            # For double elim, return all unfinished matches across both brackets
            return TournamentEngine.pending_matches(event)

        return []

    # ── Result recording + auto-progression ──────────────────────────

    @staticmethod
    def record_result(event, match_id, winner, score, recorded_by=None):
        """
        Record a match result in the bracket. Auto-advances bracket.
        Returns dict:
          match         — the updated match
          round_complete — bool, was the current round completed?
          tournament_complete — bool, is the whole event done?
          champion       — str | None
          next_matches   — list of new matches generated (if any)
          stage_name     — str, stage that just completed
        """
        bd = event.get("bracket_data")
        if not bd:
            return {"error": "No bracket data"}

        system = bd.get("system", "")
        match = TournamentEngine.find_match(event, match_id)
        if not match:
            return {"error": f"Match {match_id} not found"}

        loser = match["team2"] if winner == match["team1"] else match["team1"]

        # Update match in-place
        match["winner"]      = winner
        match["loser"]       = loser
        match["score"]       = score
        match["status"]      = "completed"
        match["recorded_at"] = datetime.utcnow().isoformat()
        if recorded_by:
            match["recorded_by"] = str(recorded_by)

        # Store in event match_results log
        if "match_results" not in event:
            event["match_results"] = []
        event["match_results"].append({
            "match_id":   match_id,
            "team1":      match["team1"],
            "team2":      match["team2"],
            "winner":     winner,
            "loser":      loser,
            "score":      score,
            "stage":      TournamentEngine.current_stage_name(event),
            "recorded_at": match["recorded_at"],
        })

        # Advance bracket based on system
        next_matches = []
        if system == "single_elim":
            next_matches = TournamentEngine._advance_se(bd, match_id, winner)
        elif system == "double_elim":
            next_matches = TournamentEngine._advance_de(bd, match_id, winner, loser)
        elif system in ("round_robin", "groups", "group_bracket"):
            # For RR, no advancement — just check if all done
            pass
        elif system in ("random_draw", "random_teams"):
            # For random, collect winners for next round
            next_matches = TournamentEngine._advance_random(event, bd, match_id, winner)

        round_complete    = TournamentEngine.is_round_complete(event)
        tournament_complete = TournamentEngine.is_complete(event)
        champion = TournamentEngine.champion(event) if tournament_complete else None

        if tournament_complete and champion:
            event["status"]   = "completed"
            event["champion"] = champion

        return {
            "match":              match,
            "winner":             winner,
            "loser":              loser,
            "round_complete":     round_complete,
            "tournament_complete": tournament_complete,
            "champion":           champion,
            "next_matches":       next_matches,
            "stage_name":         TournamentEngine.current_stage_name(event),
        }

    @staticmethod
    def _advance_se(bd, match_id, winner):
        """Single elim: push winner into next round's correct slot."""
        rounds = bd.get("rounds", [])
        next_matches = []

        for ri, rnd in enumerate(rounds):
            for mi, m in enumerate(rnd):
                if m.get("match_id") == match_id:
                    # Figure out which slot in the NEXT round
                    next_round_idx = ri + 1
                    next_slot_idx  = mi // 2
                    if next_round_idx < len(rounds):
                        nm = rounds[next_round_idx][next_slot_idx]
                        if mi % 2 == 0:
                            nm["team1"] = winner
                        else:
                            nm["team2"] = winner
                        nm.setdefault("status", "pending")
                        # Auto-complete BYE slots
                        if nm.get("team1") and nm.get("team2"):
                            if nm["team1"] == "BYE":
                                nm["winner"] = nm["team2"]
                                nm["status"] = "bye"
                            elif nm["team2"] == "BYE":
                                nm["winner"] = nm["team1"]
                                nm["status"] = "bye"
                                # Recurse for auto-BYE advancement
                                TournamentEngine._advance_se(bd, nm["match_id"], nm["winner"])
                        if nm.get("status") == "pending" and nm.get("team1") and nm.get("team2") and "TBD" not in [nm["team1"], nm["team2"]]:
                            next_matches.append(nm)
                    # Check if we've completed the current round
                    all_done = all(m2.get("status") in ("completed", "bye") for m2 in rnd)
                    if all_done and next_round_idx < len(rounds):
                        bd["current_round"] = next_round_idx
                    return next_matches

        return next_matches

    @staticmethod
    def _advance_de(bd, match_id, winner, loser):
        """Double elim: winners advance in WB, losers drop to LB."""
        # Find match
        match = None
        match_bracket = None
        match_ri = None
        match_mi = None

        for ri, rnd in enumerate(bd.get("winners", [])):
            for mi, m in enumerate(rnd):
                if m.get("match_id") == match_id:
                    match, match_bracket, match_ri, match_mi = m, "wb", ri, mi
        if not match:
            for ri, rnd in enumerate(bd.get("losers", [])):
                for mi, m in enumerate(rnd):
                    if m.get("match_id") == match_id:
                        match, match_bracket, match_ri, match_mi = m, "lb", ri, mi
        if not match and bd.get("grand_final", {}).get("match_id") == match_id:
            match, match_bracket = bd["grand_final"], "gf"

        if not match:
            return []

        next_matches = []

        if match_bracket == "wb":
            wb = bd.get("winners", [])
            lb = bd.get("losers", [])
            next_ri = match_ri + 1
            next_mi = match_mi // 2
            # Advance winner in WB
            if next_ri < len(wb):
                nm = wb[next_ri][next_mi]
                nm["team1" if match_mi % 2 == 0 else "team2"] = winner
                nm.setdefault("status", "pending")
                if nm.get("team1") and nm.get("team2") and "TBD" not in [nm["team1"], nm["team2"]]:
                    next_matches.append(nm)
            elif bd.get("grand_final"):
                gf = bd["grand_final"]
                gf["team1"] = winner
                gf.setdefault("status", "pending")
            # Drop loser into LB
            lb_target_ri = match_ri * 2
            if lb_target_ri < len(lb):
                for lm in lb[lb_target_ri]:
                    if lm.get("team1") == "TBD":
                        lm["team1"] = loser; break
                    elif lm.get("team2") == "TBD":
                        lm["team2"] = loser; break

        elif match_bracket == "lb":
            lb = bd.get("losers", [])
            next_ri = match_ri + 1
            next_mi = match_mi // 2
            if next_ri < len(lb):
                nm = lb[next_ri][next_mi]
                nm["team1" if match_mi % 2 == 0 else "team2"] = winner
                nm.setdefault("status", "pending")
                if nm.get("team1") and nm.get("team2") and "TBD" not in [nm["team1"], nm["team2"]]:
                    next_matches.append(nm)
            elif bd.get("grand_final"):
                gf = bd["grand_final"]
                gf["team2"] = winner
                gf.setdefault("status", "pending")
                if gf.get("team1") and gf["team1"] != "TBD":
                    next_matches.append(gf)

        elif match_bracket == "gf":
            # Tournament over
            bd["champion"] = winner

        return next_matches

    @staticmethod
    def _advance_random(event, bd, match_id, winner):
        """For random draw/teams: collect winners, generate next round when complete."""
        matches = bd.get("matches", [])
        completed = [m for m in matches if m.get("status") == "completed"]
        pending   = [m for m in matches if m.get("status") not in ("completed", "bye", "cancelled")]

        if pending:
            return []

        # All matches done — generate next round from winners
        winners = []
        for m in matches:
            w = m.get("winner")
            if w and w != "BYE":
                winners.append(w)

        if len(winners) < 2:
            bd["completed"] = True
            if winners:
                bd["champion"] = winners[0]
            return []

        # Generate next round
        random.shuffle(winners)
        round_num = bd.get("round_num", 1) + 1
        bd["round_num"] = round_num
        new_matches = []
        mid_start = bd.get("mid_counter", len(matches) + 1)
        for i in range(0, len(winners) - 1, 2):
            new_matches.append({
                "match_id": f"rd_{mid_start + i // 2}",
                "team1": winners[i], "team2": winners[i+1],
                "status": "pending", "round_label": f"Round {round_num}"
            })
        if len(winners) % 2 != 0:
            new_matches.append({
                "match_id": f"rd_{mid_start + len(winners)//2}",
                "team1": winners[-1], "team2": "BYE",
                "status": "bye", "winner": winners[-1]
            })
        bd["mid_counter"] = mid_start + len(new_matches)
        bd["matches"].extend(new_matches)
        return [m for m in new_matches if m.get("status") == "pending"]

    # ── Round / completion checks ─────────────────────────────────────

    @staticmethod
    def is_round_complete(event) -> bool:
        current = TournamentEngine.current_round_matches(event)
        return len(current) > 0 and all(m.get("status") in ("completed", "bye") for m in current)

    @staticmethod
    def is_complete(event) -> bool:
        bd = event.get("bracket_data")
        if not bd:
            return False
        system = bd.get("system", "")
        if system == "single_elim":
            rounds = bd.get("rounds", [])
            if rounds:
                last = rounds[-1]
                return all(m.get("status") in ("completed", "bye") for m in last)
        elif system == "double_elim":
            gf = bd.get("grand_final", {})
            return gf.get("status") == "completed"
        elif system in ("round_robin", "groups"):
            return all(m.get("status") in ("completed", "bye")
                       for m in bd.get("matches", []))
        elif system in ("random_draw", "random_teams"):
            return bd.get("completed", False)
        return False

    @staticmethod
    def champion(event) -> str | None:
        bd = event.get("bracket_data")
        if not bd:
            return None
        # Check stored champion first
        if bd.get("champion"):
            return bd["champion"]
        system = bd.get("system", "")
        if system == "single_elim":
            rounds = bd.get("rounds", [])
            if rounds:
                final = rounds[-1]
                if final and final[0].get("winner"):
                    return final[0]["winner"]
        elif system == "double_elim":
            gf = bd.get("grand_final", {})
            return gf.get("winner")
        return None

    @staticmethod
    def current_stage_name(event) -> str:
        bd = event.get("bracket_data")
        if not bd:
            return "Unknown Stage"
        system = bd.get("system", "")
        if system == "single_elim":
            rounds  = bd.get("rounds", [])
            cur_idx = bd.get("current_round", 0)
            total   = len(rounds)
            rn_idx  = total - 1 - cur_idx
            if 0 <= rn_idx < len(ROUND_NAMES_SE):
                return ROUND_NAMES_SE[rn_idx]
            return f"Round {cur_idx + 1}"
        elif system == "double_elim":
            # Simplified — check if GF is active
            gf = bd.get("grand_final", {})
            if gf.get("team1") and gf.get("team2") and "TBD" not in [gf.get("team1",""), gf.get("team2","")]:
                return "Grand Final"
            return "Elimination Stage"
        elif system in ("round_robin",):
            return "Round Robin"
        elif system in ("groups", "group_bracket"):
            stage = bd.get("bracket_stage", "groups")
            return "Group Stage" if stage == "groups" else "Knockout Stage"
        elif system in ("random_draw", "random_teams"):
            rn = bd.get("round_num", 1)
            return f"Round {rn}"
        return "Bracket"

    @staticmethod
    def standings_rr(event) -> list:
        """For round robin: return sorted standings."""
        bd = event.get("bracket_data")
        if not bd:
            return []
        teams = {}
        for m in bd.get("matches", []):
            for t in [m.get("team1"), m.get("team2")]:
                if t and t not in ("BYE", "TBD"):
                    teams.setdefault(t, {"name": t, "w": 0, "d": 0, "l": 0, "pts": 0, "gf": 0, "ga": 0})
            if m.get("status") == "completed" and m.get("winner"):
                w = m["winner"]; l = m["loser"]
                score = m.get("score", "0-0")
                try:
                    g1, g2 = map(int, score.split("-"))
                except:
                    g1, g2 = 0, 0
                if w in teams:
                    teams[w]["w"] += 1; teams[w]["pts"] += 3
                    teams[w]["gf"] += max(g1, g2); teams[w]["ga"] += min(g1, g2)
                if l in teams:
                    teams[l]["l"] += 1
                    teams[l]["gf"] += min(g1, g2); teams[l]["ga"] += max(g1, g2)
        return sorted(teams.values(), key=lambda x: (-x["pts"], -(x["gf"]-x["ga"]), -x["w"]))


# ── Professional Announcement Builders ───────────────────────────────

def build_match_card(event, match) -> discord.Embed:
    """Cinematic match announcement embed."""
    stage = TournamentEngine.current_stage_name(event)
    t1    = match.get("team1", "?")
    t2    = match.get("team2", "?")
    fmt   = event.get("format", "")
    bo    = BO_OPTIONS.get(event.get("settings", {}).get("bo_format", "bo1"), "Best of 1")

    # Get Glory Points context if squads are known
    t1_pts = squad_data["squads"].get(t1, {}).get("points", 0)
    t2_pts = squad_data["squads"].get(t2, {}).get("points", 0)
    t1_tag = SQUADS.get(t1, "⚔️")
    t2_tag = SQUADS.get(t2, "⚔️")

    embed = discord.Embed(
        title=f"⚔️ {stage.upper()} — MATCH ALERT",
        description=(
            f"## {t1_tag} {t1}  🆚  {t2_tag} {t2}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏆 **{event['name']}** · {fmt} · {bo}"
        ),
        color=ROYAL_RED,
        timestamp=datetime.utcnow()
    )
    sched = match.get("scheduled_date") or match.get("date")
    if sched:
        embed.add_field(name="📅 Scheduled", value=f"**{sched}**", inline=True)
    if t1_pts or t2_pts:
        embed.add_field(
            name="💎 Glory Standing",
            value=f"**{t1}**: {t1_pts} pts  ·  **{t2}**: {t2_pts} pts",
            inline=True
        )
    embed.add_field(name="🆔 Match ID", value=f"`{match.get('match_id','?')}`", inline=True)
    embed.set_footer(text=f"⚜️ Majestic Dominion | {event['name']}")
    apply_branding(embed, thumbnail=True)
    return embed


def build_result_card(event, result_info) -> discord.Embed:
    """Cinematic result announcement with advancement/elimination."""
    winner  = result_info["winner"]
    loser   = result_info["loser"]
    score   = result_info["match"].get("score", "?")
    stage   = result_info["stage_name"]
    t_complete = result_info["tournament_complete"]
    r_complete = result_info["round_complete"]
    next_ms    = result_info.get("next_matches", [])
    champion   = result_info.get("champion")

    w_tag = SQUADS.get(winner, "⚔️")
    l_tag = SQUADS.get(loser, "⚔️")

    if t_complete and champion:
        title = "🏆 WE HAVE A CHAMPION!"
        color = ROYAL_GOLD
        desc  = (
            f"## 👑 {w_tag} {winner}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"*The Crown recognizes the supreme sovereign of the Dominion!*\n\n"
            f"🏆 **{event['name']}** — TOURNAMENT CHAMPION\n"
            f"⚔️ Defeated **{l_tag} {loser}** · **{score}** in the {stage}"
        )
    elif r_complete and next_ms:
        next_stage = TournamentEngine.current_stage_name(event)
        title = f"🎯 {stage.upper()} COMPLETE — {next_stage.upper()} NEXT"
        color = ROYAL_PURPLE
        desc  = (
            f"## {w_tag} {winner} advances!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Defeated **{l_tag} {loser}** · **{score}**\n\n"
            f"⏭️ The **{next_stage}** is now set!\n"
            f"*{len(next_ms)} match(es) ready to be scheduled.*"
        )
    else:
        title = f"⚔️ RESULT — {stage}"
        color = ROYAL_GREEN
        desc  = (
            f"## {w_tag} {winner} ✅\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Defeated **{l_tag} {loser}** · **{score}**\n\n"
            f"💀 **{loser}** has been eliminated" if event.get("tournament_system") in ("single_elim",) else
            f"⚔️ Match recorded in **{event['name']}**"
        )

    embed = discord.Embed(title=title, description=desc, color=color, timestamp=datetime.utcnow())

    # Next opponents
    if next_ms and not t_complete:
        lines = []
        for m in next_ms[:4]:
            t1 = m.get("team1", "TBD")
            t2 = m.get("team2", "TBD")
            if "TBD" not in [t1, t2]:
                lines.append(f"⚔️ **{t1}** vs **{t2}**")
        if lines:
            embed.add_field(name="🔜 Next Matchups", value="\n".join(lines), inline=False)

    embed.set_footer(text=f"⚜️ {event['name']} | Majestic Dominion")
    apply_branding(embed, thumbnail=True)
    return embed


def build_round_complete_embed(event, stage_name, next_stage_name, next_matches) -> discord.Embed:
    """Announce round completion + show next round."""
    embed = discord.Embed(
        title=f"🏁 {stage_name.upper()} — ROUND COMPLETE",
        description=(
            f"*The dust settles on {stage_name}.*\n\n"
            f"⏭️ **{next_stage_name}** is now set!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=ROYAL_PURPLE,
        timestamp=datetime.utcnow()
    )
    if next_matches:
        lines = []
        for m in next_matches[:8]:
            t1 = m.get("team1", "TBD")
            t2 = m.get("team2", "TBD")
            sched = m.get("scheduled_date") or m.get("date", "")
            sched_txt = f" · 📅 {sched}" if sched else ""
            if "TBD" not in [t1, t2]:
                lines.append(f"⚔️ **{t1}** vs **{t2}**{sched_txt}")
        if lines:
            embed.add_field(name=f"⚔️ {next_stage_name} Matchups", value="\n".join(lines), inline=False)
    embed.set_footer(text=f"⚜️ {event['name']} | Majestic Dominion")
    apply_branding(embed, thumbnail=True)
    return embed


def build_champion_embed(event, champion) -> discord.Embed:
    """Grand cinematic champion announcement."""
    ch_tag = SQUADS.get(champion, "👑")
    results = event.get("match_results", [])
    wins = sum(1 for r in results if r.get("winner") == champion)

    embed = discord.Embed(
        title="👑 CHAMPION CROWNED!",
        description=(
            f"## 🏆 {ch_tag} {champion}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*The Crown of the Dominion has been claimed!*\n\n"
            f"**{event['name']}** has its champion.\n"
            f"*{wins} match(es) won through this tournament.*\n\n"
            f"⚜️ *All hail the sovereign victor — may their reign be glorious!*"
        ),
        color=ROYAL_GOLD,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=f"⚜️ Majestic Dominion | {event['name']} — Final")
    apply_branding(embed, thumbnail=False, author=True)
    return embed


def build_live_bracket_embed(event) -> discord.Embed:
    """Live bracket with winners/losers highlighted."""
    bd = event.get("bracket_data")
    if not bd:
        embed = discord.Embed(title="🏆 No Bracket", description="No bracket generated yet.", color=ROYAL_RED)
        apply_branding(embed, thumbnail=True)
        return embed

    system = bd.get("system", "")
    stage  = TournamentEngine.current_stage_name(event)
    champ  = TournamentEngine.champion(event)
    done   = TournamentEngine.is_complete(event)

    title_prefix = "🏆" if done else "⚔️"
    title_suffix = f" — 👑 {champ}" if done and champ else f" — {stage}"

    embed = discord.Embed(
        title=f"{title_prefix} {event['name']}{title_suffix}",
        description=(
            f"*{'Tournament concluded!' if done else 'Live bracket — results update automatically.'}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=ROYAL_GOLD if done else ROYAL_PURPLE,
        timestamp=datetime.utcnow()
    )

    per_field = 12

    if system == "single_elim":
        rounds = bd.get("rounds", [])
        total  = len(rounds)
        for ri, rnd in enumerate(rounds):
            rn_idx = total - 1 - ri
            rn = ROUND_NAMES_SE[rn_idx] if rn_idx < len(ROUND_NAMES_SE) else f"Round {ri+1}"
            lines = []
            for m in rnd:
                status = m.get("status", "pending")
                t1, t2 = m.get("team1","?"), m.get("team2","?")
                if status == "completed":
                    w = m.get("winner","?")
                    l = m.get("loser", t2 if w == t1 else t1)
                    sc = m.get("score","?")
                    lines.append(f"✅ **{w}** def. ~~{l}~~ · {sc}")
                elif status == "bye":
                    lines.append(f"🚪 **{t1}** — BYE")
                elif t2 in ("TBD", None) or t1 in ("TBD", None):
                    lines.append(f"⏳ TBD vs TBD")
                else:
                    lines.append(f"⏳ **{t1}** vs **{t2}**")
            for ci in range(0, len(lines), per_field):
                chunk = "\n".join(lines[ci:ci+per_field])[:1024]
                part  = f" ({ci//per_field+1})" if len(lines) > per_field else ""
                embed.add_field(name=f"⚔️ {rn}{part}", value=chunk, inline=False)
                if len(embed.fields) >= 24: break
            if len(embed.fields) >= 24: break

    elif system == "double_elim":
        for ri, rnd in enumerate(bd.get("winners", [])):
            lines = []
            for m in rnd:
                st = m.get("status","pending")
                if st == "completed":
                    lines.append(f"✅ **{m['winner']}** def. ~~{m['loser']}~~ · {m.get('score','?')}")
                elif st == "bye":
                    lines.append(f"🚪 **{m.get('team1','?')}** — BYE")
                else:
                    lines.append(f"⏳ **{m.get('team1','?')}** vs **{m.get('team2','?')}**")
            if lines:
                embed.add_field(name=f"🏆 WB Round {ri+1}", value="\n".join(lines)[:1024], inline=False)
            if len(embed.fields) >= 12: break
        for ri, rnd in enumerate(bd.get("losers", [])):
            lines = []
            for m in rnd:
                st = m.get("status","pending")
                if st == "completed":
                    lines.append(f"✅ **{m['winner']}** def. ~~{m['loser']}~~ · {m.get('score','?')}")
                else:
                    lines.append(f"⏳ {m.get('team1','TBD')} vs {m.get('team2','TBD')}")
            if lines:
                embed.add_field(name=f"💀 LB Round {ri+1}", value="\n".join(lines)[:1024], inline=False)
            if len(embed.fields) >= 20: break
        gf = bd.get("grand_final", {})
        if gf:
            st = gf.get("status","pending")
            val = (f"✅ **{gf['winner']}** def. ~~{gf['loser']}~~ · {gf.get('score','?')}"
                   if st == "completed" else
                   f"⏳ **{gf.get('team1','TBD')}** vs **{gf.get('team2','TBD')}**")
            embed.add_field(name="🎯 Grand Final", value=val, inline=False)

    elif system in ("round_robin", "groups", "group_bracket"):
        # Show standings
        standings = TournamentEngine.standings_rr(event)
        if standings:
            lines = ["**#  Team                W  L  Pts**"]
            for i, s in enumerate(standings[:15], 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                lines.append(f"{medal} **{s['name']}** — {s['w']}W {s['l']}L **{s['pts']}pts**")
            embed.add_field(name="📊 Standings", value="\n".join(lines)[:1024], inline=False)
        # Show recent results
        results = [m for m in bd.get("matches",[]) if m.get("status") == "completed"][-6:]
        if results:
            lines = [f"✅ **{m['winner']}** def. ~~{m['loser']}~~ · {m.get('score','?')}" for m in results]
            embed.add_field(name="📜 Recent Results", value="\n".join(lines)[:1024], inline=False)

    elif system in ("random_draw", "random_teams"):
        matches = bd.get("matches", [])
        pending_m   = [m for m in matches if m.get("status") == "pending"]
        completed_m = [m for m in matches if m.get("status") == "completed"]
        if completed_m:
            lines = [f"✅ **{m['winner']}** def. ~~{m['loser']}~~ · {m.get('score','?')}"
                     for m in completed_m[-8:]]
            embed.add_field(name=f"✅ Results ({len(completed_m)})", value="\n".join(lines)[:1024], inline=False)
        if pending_m:
            lines = [f"⏳ **{m['team1']}** vs **{m['team2']}**" for m in pending_m[:8]]
            embed.add_field(name=f"⏳ Pending ({len(pending_m)})", value="\n".join(lines)[:1024], inline=False)

    if champ and done:
        embed.add_field(name="👑 Champion", value=f"**{champ}**", inline=False)

    embed.set_footer(text=f"⚜️ {event['name']} | ID: {event['id']} | Majestic Dominion")
    apply_branding(embed, thumbnail=True)
    return embed


def build_standings_embed(event) -> discord.Embed:
    """Round-robin standings table."""
    standings = TournamentEngine.standings_rr(event)
    embed = discord.Embed(
        title=f"📊 Standings — {event['name']}",
        color=ROYAL_PURPLE,
        timestamp=datetime.utcnow()
    )
    if not standings:
        embed.description = "*No results recorded yet.*"
    else:
        lines = []
        for i, s in enumerate(standings, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            gd = s['gf'] - s['ga']
            lines.append(
                f"{medal} **{s['name']}** — {s['w']}W/{s['l']}L · **{s['pts']} pts** · GD {'+' if gd >= 0 else ''}{gd}"
            )
        embed.description = "\n".join(lines)[:2048]
    embed.set_footer(text=f"⚜️ Majestic Dominion | {event['name']}")
    apply_branding(embed, thumbnail=True)
    return embed


# ── Mod Tools: Event Match Recording ─────────────────────────────────

class EventMatchRecordView(View):
    """
    Mod tool: record a result for a match within an event.
    Automatically advances the bracket and announces results.
    """
    def __init__(self, event, matches, author_id):
        super().__init__(timeout=180)
        self.event     = event
        self.author_id = author_id

        if not matches:
            return

        opts = []
        for m in matches[:25]:
            t1    = m.get("team1", "?")
            t2    = m.get("team2", "?")
            label = f"{t1[:20]} vs {t2[:20]}"
            desc  = f"{m.get('round_display','') or m.get('round_label','')} · {m.get('match_id','')}"
            opts.append(discord.SelectOption(label=label[:100], value=m["match_id"],
                description=desc[:100], emoji="⚔️"))
        if opts:
            sel = Select(placeholder="⚔️ Select match to record result...", options=opts)
            sel.callback = self._selected
            self.add_item(sel)

    async def _selected(self, interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Not your session.", ephemeral=True)
        mid   = interaction.data["values"][0]
        match = TournamentEngine.find_match(self.event, mid)
        if not match:
            return await interaction.response.send_message("❌ Match not found.", ephemeral=True)
        await interaction.response.send_modal(
            EventMatchScoreModal(self.event, match, interaction.user.id)
        )


class EventMatchScoreModal(Modal, title="⚔️ Record Match Result"):
    score_input = TextInput(
        label="Score  (team1 - team2)",
        placeholder="e.g.  2-0  or  1-1",
        required=True, max_length=10
    )

    def __init__(self, event, match, author_id):
        super().__init__()
        self.event     = event
        self.match     = match
        self.author_id = author_id
        t1 = match.get("team1","?")
        t2 = match.get("team2","?")
        self.score_input.label = f"{t1[:15]} vs {t2[:15]}"

    async def on_submit(self, interaction: discord.Interaction):
        try:
            s1, s2 = map(int, self.score_input.value.strip().split("-"))
        except:
            return await interaction.response.send_message(
                "❌ Use format X-Y (e.g. 2-0)", ephemeral=True)

        t1 = self.match["team1"]
        t2 = self.match["team2"]
        if s1 == s2:
            return await interaction.response.send_message(
                "❌ Draws not supported in elimination brackets. Please re-enter.", ephemeral=True)

        winner = t1 if s1 > s2 else t2
        score  = self.score_input.value.strip()

        # Record via engine
        prev_stage  = TournamentEngine.current_stage_name(self.event)
        result_info = TournamentEngine.record_result(
            self.event, self.match["match_id"], winner, score, interaction.user.id
        )
        save_data(squad_data)

        # Confirm to mod
        conf = discord.Embed(
            title="✅ Result Recorded",
            description=(
                f"**{winner}** defeated **{t2 if winner == t1 else t1}** — **{score}**\n"
                f"Stage: {prev_stage}\n"
                + ("🏁 Round complete — bracket auto-advanced!" if result_info["round_complete"] else "")
                + ("🏆 **Tournament concluded!** Champion: " + (result_info["champion"] or "?") if result_info["tournament_complete"] else "")
            ),
            color=ROYAL_GREEN
        )
        apply_branding(conf, thumbnail=True)
        await interaction.response.send_message(embed=conf, ephemeral=True)

        # Professional announcement
        result_card = build_result_card(self.event, result_info)
        await announce_event(interaction.guild, result_card)

        # Champion announcement
        if result_info["tournament_complete"] and result_info["champion"]:
            champ_embed = build_champion_embed(self.event, result_info["champion"])
            await announce_major(interaction.guild, champ_embed)

        # Round complete announcement
        elif result_info["round_complete"] and result_info["next_matches"]:
            next_stage  = TournamentEngine.current_stage_name(self.event)
            round_embed = build_round_complete_embed(
                self.event, prev_stage, next_stage, result_info["next_matches"])
            await announce_event(interaction.guild, round_embed)

        await log_action(interaction.guild, "⚔️ Event Match Recorded",
            f"{interaction.user.mention} recorded **{winner}** def. **{t2 if winner == t1 else t1}** "
            f"({score}) in **{self.event['name']}** [{prev_stage}]")


# ── Mod Tools: Registration Management ───────────────────────────────

class ManageRegistrationsView(View):
    """Full registrant management for mods."""
    def __init__(self, event, author_id, guild):
        super().__init__(timeout=180)
        self.event     = event
        self.author_id = author_id
        self.guild     = guild

    @discord.ui.button(label="➕ Add Registrant", style=discord.ButtonStyle.success, row=0)
    async def add_btn(self, interaction, button):
        if interaction.user.id != self.author_id: return
        await interaction.response.send_modal(AddRegistrantModal(self.event, self.author_id))

    @discord.ui.button(label="🗑️ Remove Registrant", style=discord.ButtonStyle.danger, row=0)
    async def remove_btn(self, interaction, button):
        if interaction.user.id != self.author_id: return
        regs = self.event.get("registrations", [])
        if not regs:
            return await interaction.response.send_message("❌ No registrations.", ephemeral=True)
        opts = [discord.SelectOption(label=get_reg_name(r)[:100], value=str(i),
                    description=f"Registered {r.get('registered_at','')[:10]}")
                for i, r in enumerate(regs[:25])]
        embed = discord.Embed(title="🗑️ Remove Registrant", color=ROYAL_RED,
            description="Select who to remove:")
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=RemoveRegistrantView(self.event, opts, self.author_id), ephemeral=True)

    @discord.ui.button(label="✏️ Replace Registrant", style=discord.ButtonStyle.primary, row=0)
    async def replace_btn(self, interaction, button):
        if interaction.user.id != self.author_id: return
        regs = self.event.get("registrations", [])
        if not regs:
            return await interaction.response.send_message("❌ No registrations.", ephemeral=True)
        await interaction.response.send_modal(ReplaceRegistrantModal(self.event, self.author_id))

    @discord.ui.button(label="📋 View All", style=discord.ButtonStyle.secondary, row=1)
    async def view_btn(self, interaction, button):
        if interaction.user.id != self.author_id: return
        embed, _ = build_registrations_embed(self.event, 1, self.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=1)
    async def refresh_btn(self, interaction, button):
        if interaction.user.id != self.author_id: return
        regs = self.event.get("registrations", [])
        embed = discord.Embed(title=f"👥 Registrations — {self.event['name']}",
            description=f"**{len(regs)}** registered", color=ROYAL_PURPLE)
        apply_branding(embed, thumbnail=True)
        await interaction.response.edit_message(embed=embed, view=self)


class AddRegistrantModal(Modal, title="➕ Add Registrant"):
    name_input = TextInput(label="Team/Player name", placeholder="e.g. Team Alpha or PlayerX",
        required=True, max_length=80)
    def __init__(self, event, author_id):
        super().__init__(); self.event = event; self.author_id = author_id

    async def on_submit(self, interaction):
        name = self.name_input.value.strip()
        # Check duplicates
        existing = [get_reg_name(r) for r in self.event.get("registrations", [])]
        if name in existing:
            return await interaction.response.send_message(
                f"❌ **{name}** is already registered.", ephemeral=True)
        rm = self.event.get("registration_mode", "solo")
        if rm == "solo":
            self.event["registrations"].append({
                "player_id": None, "player_name": name,
                "registered_at": datetime.utcnow().isoformat(), "added_by_mod": True
            })
        else:
            self.event["registrations"].append({
                "team_name": name, "leader_id": None, "members": [],
                "registered_at": datetime.utcnow().isoformat(), "added_by_mod": True
            })
        save_data(squad_data)
        embed = discord.Embed(title="✅ Registrant Added",
            description=f"**{name}** added to **{self.event['name']}**.", color=ROYAL_GREEN)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(interaction.guild, "➕ Mod Added Registrant",
            f"{interaction.user.mention} manually added **{name}** to **{self.event['name']}**")


class ReplaceRegistrantModal(Modal, title="✏️ Replace Registrant"):
    old_name = TextInput(label="Current name (exact)", required=True, max_length=80)
    new_name = TextInput(label="Replacement name",     required=True, max_length=80)
    def __init__(self, event, author_id):
        super().__init__(); self.event = event; self.author_id = author_id

    async def on_submit(self, interaction):
        old = self.old_name.value.strip()
        new = self.new_name.value.strip()
        replaced = False
        for reg in self.event.get("registrations", []):
            if get_reg_name(reg) == old:
                if reg.get("team_name"):   reg["team_name"] = new
                elif reg.get("player_name"): reg["player_name"] = new
                replaced = True
                break
        if not replaced:
            return await interaction.response.send_message(
                f"❌ **{old}** not found in registrations.", ephemeral=True)
        # Also update in bracket_data if tournament has started
        bd = self.event.get("bracket_data")
        if bd:
            import json
            bd_str = json.dumps(bd).replace(f'"{old}"', f'"{new}"')
            self.event["bracket_data"] = json.loads(bd_str)
        save_data(squad_data)
        embed = discord.Embed(title="✅ Registrant Replaced",
            description=f"**{old}** → **{new}** in **{self.event['name']}**.", color=ROYAL_GREEN)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(interaction.guild, "✏️ Registrant Replaced",
            f"{interaction.user.mention} replaced **{old}** with **{new}** in **{self.event['name']}**")


# ── Mod Tools: Force Advance & Override ──────────────────────────────

class ForceAdvanceView(View):
    """Manually advance tournament if auto-progression fails."""
    def __init__(self, event, author_id):
        super().__init__(timeout=120)
        self.event = event; self.author_id = author_id

    @discord.ui.button(label="⚡ Force Next Round", style=discord.ButtonStyle.danger, row=0)
    async def force_btn(self, interaction, button):
        if interaction.user.id != self.author_id: return
        bd = self.event.get("bracket_data")
        if not bd:
            return await interaction.response.send_message("❌ No bracket.", ephemeral=True)
        cur = bd.get("current_round", 0)
        rounds = bd.get("rounds", [])
        if cur + 1 < len(rounds):
            bd["current_round"] = cur + 1
            save_data(squad_data)
            embed = discord.Embed(title="⚡ Force Advanced",
                description=f"Advanced to **Round {cur + 2}** manually.", color=ROYAL_GOLD)
            apply_branding(embed, thumbnail=True)
            await interaction.response.edit_message(embed=embed, view=None)
            await log_action(interaction.guild, "⚡ Force Advanced",
                f"{interaction.user.mention} force-advanced **{self.event['name']}** to round {cur+2}")
        else:
            await interaction.response.send_message("❌ No further rounds to advance to.", ephemeral=True)

    @discord.ui.button(label="🏆 Declare Winner", style=discord.ButtonStyle.success, row=0)
    async def declare_btn(self, interaction, button):
        if interaction.user.id != self.author_id: return
        await interaction.response.send_modal(DeclareWinnerModal(self.event, self.author_id))


class DeclareWinnerModal(Modal, title="🏆 Declare Tournament Winner"):
    winner_name = TextInput(label="Winner name (exact registration name)",
        placeholder="e.g. Team Alpha", required=True, max_length=80)
    def __init__(self, event, author_id):
        super().__init__(); self.event = event; self.author_id = author_id

    async def on_submit(self, interaction):
        winner = self.winner_name.value.strip()
        self.event["status"]  = "completed"
        self.event["champion"] = winner
        bd = self.event.get("bracket_data")
        if bd:
            bd["champion"] = winner
        save_data(squad_data)
        embed = discord.Embed(title="🏆 Winner Declared",
            description=f"**{winner}** declared champion of **{self.event['name']}**.",
            color=ROYAL_GOLD)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        champ_embed = build_champion_embed(self.event, winner)
        await announce_major(interaction.guild, champ_embed)
        await log_action(interaction.guild, "🏆 Winner Declared",
            f"{interaction.user.mention} declared **{winner}** as winner of **{self.event['name']}**")


# ── Updated EventManagerView ──────────────────────────────────────────

class EventManagerViewV2(View):
    """Full event management dashboard — replaces EventManagerView."""
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Create", emoji="➕", style=discord.ButtonStyle.success, row=0)
    async def create_btn(self, interaction, button):
        await interaction.response.send_modal(CreateEventModal())

    @discord.ui.button(label="Edit", emoji="✏️", style=discord.ButtonStyle.primary, row=0)
    async def edit_btn(self, interaction, button):
        evs = get_all_events()
        if not evs: return await interaction.response.send_message("❌ No events.", ephemeral=True)
        embed = discord.Embed(title="✏️ Edit Event", description="Select:", color=ROYAL_GOLD)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectViewV2(evs, "edit", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="Delete", emoji="🗑️", style=discord.ButtonStyle.danger, row=0)
    async def delete_btn(self, interaction, button):
        evs = get_all_events()
        if not evs: return await interaction.response.send_message("❌ No events.", ephemeral=True)
        embed = discord.Embed(title="🗑️ Delete Event", description="Select:", color=ROYAL_RED)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectViewV2(evs, "delete", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="📝 Record Match", style=discord.ButtonStyle.danger, emoji="⚔️", row=1)
    async def record_match_btn(self, interaction, button):
        """Record a result within an active tournament."""
        evs = [e for e in get_all_events() if e["status"] in ("live", "open")
               and (e.get("bracket_data") or e.get("type") == "fun")]
        if not evs:
            return await interaction.response.send_message(
                "❌ No active events. Start an event first.", ephemeral=True)
        embed = discord.Embed(title="⚔️ Record Match Result", description="Select event:", color=ROYAL_RED)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectView(evs, "record_match", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="👥 Registrations", emoji="📋", style=discord.ButtonStyle.secondary, row=1)
    async def regs_btn(self, interaction, button):
        evs = get_all_events()
        if not evs: return await interaction.response.send_message("❌ No events.", ephemeral=True)
        embed = discord.Embed(title="📋 Manage Registrations", description="Select event:", color=ROYAL_PURPLE)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectViewV2(evs, "regs", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="▶️ Start", style=discord.ButtonStyle.success, row=2)
    async def start_btn(self, interaction, button):
        evs = [e for e in get_all_events() if e["status"] == "open"]
        if not evs: return await interaction.response.send_message("❌ No open events.", ephemeral=True)
        embed = discord.Embed(title="▶️ Start Event", description="Select:", color=ROYAL_GREEN)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectViewV2(evs, "start", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="⏹️ Close", style=discord.ButtonStyle.danger, row=2)
    async def close_btn(self, interaction, button):
        evs = [e for e in get_all_events() if e["status"] in ("live","open")]
        if not evs: return await interaction.response.send_message("❌ No active events.", ephemeral=True)
        embed = discord.Embed(title="⏹️ Close Event", description="Select:", color=ROYAL_RED)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectViewV2(evs, "close", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="🎲 Randomize", style=discord.ButtonStyle.primary, row=2)
    async def random_btn(self, interaction, button):
        evs = get_all_events()
        if not evs: return await interaction.response.send_message("❌ No events.", ephemeral=True)
        embed = discord.Embed(title="🎲 Randomize", description="Select event:", color=ROYAL_PURPLE)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectViewV2(evs, "randomize", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="📅 Schedule", style=discord.ButtonStyle.secondary, row=2)
    async def schedule_btn(self, interaction, button):
        evs = [e for e in get_all_events() if e.get("bracket_data")]
        if not evs:
            return await interaction.response.send_message("❌ No events with brackets.", ephemeral=True)
        embed = discord.Embed(title="📅 Schedule Matches", description="Select event:", color=ROYAL_GOLD)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectViewV2(evs, "schedule", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="⚡ Force Tools", style=discord.ButtonStyle.secondary, row=3)
    async def force_btn(self, interaction, button):
        evs = [e for e in get_all_events() if e.get("bracket_data")]
        if not evs: return await interaction.response.send_message("❌ No events.", ephemeral=True)
        embed = discord.Embed(title="⚡ Force Tools", description="Select event:", color=ROYAL_GOLD)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectView(evs, "force", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=3)
    async def refresh_btn(self, interaction, button):
        await interaction.response.edit_message(embed=build_event_manager_embed(), view=EventManagerViewV2())


# ── Updated EventActionSelectView to handle new actions ──────────────

class EventActionSelectViewV2(View):
    """Handles all event manager actions including new ones."""
    def __init__(self, events, action, author_id):
        super().__init__(timeout=180)
        self.action = action; self.author_id = author_id
        opts = [discord.SelectOption(
            label=ev["name"][:100], value=ev["id"], emoji="🎪",
            description=f"{ev['type'].title()} · {ev['status']} · {len(ev.get('registrations',[]))} reg'd")
            for ev in events[:25]]
        sel = Select(placeholder="🎪 Select an event...", options=opts)
        sel.callback = self._selected
        self.add_item(sel)

    async def _selected(self, interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Not your session.", ephemeral=True)
        eid   = interaction.data["values"][0]
        event = get_event_by_id(eid)
        if not event:
            return await interaction.response.send_message("❌ Event not found.", ephemeral=True)

        if self.action == "record_match":
            # Social events use their own manager
            if event.get("type") == "fun":
                embed = build_social_dashboard_embed(event)
                view  = SocialEventManagerView(event, interaction.user.id)
                return await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            pending = TournamentEngine.pending_matches(event)
            if not pending:
                return await interaction.response.send_message(
                    "❌ No pending matches. All matches may be complete, or bracket not generated yet.",
                    ephemeral=True)
            embed = discord.Embed(
                title=f"⚔️ Record Result — {event['name']}",
                description=f"**{len(pending)}** match(es) pending. Select one to record:",
                color=ROYAL_RED
            )
            # Add context about current stage
            stage = TournamentEngine.current_stage_name(event)
            embed.add_field(name="📍 Current Stage", value=stage, inline=True)
            embed.add_field(name="⏳ Pending", value=str(len(pending)), inline=True)
            apply_branding(embed, thumbnail=True)
            # Add round labels to matches for display
            for m in pending:
                if not m.get("round_display") and not m.get("round_label"):
                    m["round_display"] = stage
            await interaction.response.send_message(embed=embed,
                view=EventMatchRecordView(event, pending, interaction.user.id), ephemeral=True)

        elif self.action == "regs":
            embed, _ = build_registrations_embed(event, 1, interaction.guild)
            await interaction.response.send_message(embed=embed,
                view=ManageRegistrationsView(event, interaction.user.id, interaction.guild),
                ephemeral=True)

        elif self.action == "force":
            pending = TournamentEngine.pending_matches(event)
            stage   = TournamentEngine.current_stage_name(event)
            champ   = TournamentEngine.champion(event)
            embed = discord.Embed(
                title=f"⚡ Force Tools — {event['name']}",
                description=(
                    f"Stage: **{stage}**\n"
                    f"Pending matches: **{len(pending)}**\n"
                    + (f"Champion: **{champ}**" if champ else "*Tournament in progress*")
                ),
                color=ROYAL_GOLD
            )
            apply_branding(embed, thumbnail=True)
            await interaction.response.send_message(embed=embed,
                view=ForceAdvanceView(event, interaction.user.id), ephemeral=True)

        elif self.action == "start":
            event["status"] = "live"; save_data(squad_data)
            embed = discord.Embed(title="▶️ Event Live!",
                description=f"**{event['name']}** is now **LIVE**.", color=ROYAL_GREEN)
            apply_branding(embed, thumbnail=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            pub = discord.Embed(title="⚔️ THE ARENA IS OPEN!",
                description=(
                    f"**{event['name']}** is now **LIVE**!\n\n"
                    f"⚔️ *{event.get('format','?')} · {event.get('description','')}*\n\n"
                    f"*May the best sovereign prevail!*"
                ),
                color=ROYAL_GOLD)
            await announce_major(interaction.guild, pub)
            await log_action(interaction.guild, "▶️ Event Started",
                f"{interaction.user.mention} started **{event['name']}**")

        elif self.action == "close":
            event["status"] = "completed"; save_data(squad_data)
            champ = TournamentEngine.champion(event)
            embed = discord.Embed(title="⏹️ Event Closed!",
                description=f"**{event['name']}** is now closed." + (f"\n👑 Champion: **{champ}**" if champ else ""),
                color=ROYAL_RED)
            apply_branding(embed, thumbnail=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            pub = discord.Embed(title="🏁 EVENT CONCLUDED!",
                description=f"**{event['name']}** has concluded!\n\n" +
                    (f"👑 **Champion: {champ}**\n" if champ else "") +
                    "*Glory and honour to all who competed!*",
                color=ROYAL_PURPLE)
            await announce_major(interaction.guild, pub)
            await log_action(interaction.guild, "⏹️ Event Closed",
                f"{interaction.user.mention} closed **{event['name']}**")

        elif self.action == "edit":
            await interaction.response.send_modal(EditEventModal(event))

        elif self.action == "delete":
            embed = discord.Embed(title=f"🗑️ Delete '{event['name']}'?",
                description=f"Deletes event and **{len(event.get('registrations',[]))}** registrations.",
                color=ROYAL_RED)
            apply_branding(embed, thumbnail=True)
            await interaction.response.send_message(embed=embed,
                view=ConfirmDeleteEventView(event), ephemeral=True)

        elif self.action == "randomize":
            embed = discord.Embed(title=f"🎲 Randomize — {event['name']}",
                description=(
                    "**Row 0 — Simple Draws** (no bracket)\n"
                    "🎲 Random Draw · 👥 Random Teams · 🎯 Pick One · 👥 Gather Group\n\n"
                    "**Row 1 — Bracket Systems**\n"
                    "🏆 Single Elim · ⚔️ Double Elim · 🔄 Round Robin\n\n"
                    "**Row 2 — Groups**\n"
                    "🎲 Random Groups · 🎯 Groups→Bracket · 🗑️ Clear"
                ),
                color=ROYAL_PURPLE)
            apply_branding(embed, thumbnail=True)
            await interaction.response.send_message(embed=embed,
                view=RandomizeView(event, interaction.user.id), ephemeral=True)

        elif self.action == "schedule":
            unscheduled = get_unscheduled_matches(event)
            if not unscheduled:
                return await interaction.response.send_message(
                    "✅ All matches scheduled, or no bracket yet.", ephemeral=True)
            embed = discord.Embed(title=f"📅 Schedule — {event['name']}",
                description=f"**{len(unscheduled)}** unscheduled matches:", color=ROYAL_GOLD)
            apply_branding(embed, thumbnail=True)
            await interaction.response.send_message(embed=embed,
                view=ScheduleMatchSelectView(event, unscheduled, interaction.user.id), ephemeral=True)


# ── Updated public EventDetailView ───────────────────────────────────

class EventDetailViewV2(View):
    """Enhanced detail view with live bracket access."""
    def __init__(self, event, user_id):
        super().__init__(timeout=180)
        self.event   = event
        self.user_id = user_id
        already  = is_registered(event, user_id)
        is_open  = event["status"] in ("open", "registration")
        self.register_btn.disabled = already or not is_open
        if already:
            self.register_btn.label = "✅ Registered"
            self.register_btn.style = discord.ButtonStyle.success
        elif not is_open:
            self.register_btn.label = f"🔒 {event['status'].upper()}"
        self.cancel_btn.disabled   = not already
        self.bracket_btn.disabled  = not event.get("bracket_data")
        self.schedule_btn.disabled = not event.get("schedule")
        self.standings_btn.disabled = event.get("bracket_data", {}).get("system") not in ("round_robin","groups","group_bracket")

    @discord.ui.button(label="📝 Register",            style=discord.ButtonStyle.success, row=0)
    async def register_btn(self, interaction, button):
        await handle_registration(interaction, self.event)

    @discord.ui.button(label="❌ Cancel Registration", style=discord.ButtonStyle.danger,  row=0)
    async def cancel_btn(self, interaction, button):
        await handle_cancel_registration(interaction, self.event)

    @discord.ui.button(label="👥 Registrations",       style=discord.ButtonStyle.secondary, row=1)
    async def regs_btn(self, interaction, button):
        embed, _ = build_registrations_embed(self.event, 1, interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🏆 Live Bracket",        style=discord.ButtonStyle.primary,   row=1)
    async def bracket_btn(self, interaction, button):
        embed = build_live_bracket_embed(self.event)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📅 Schedule",            style=discord.ButtonStyle.secondary, row=1)
    async def schedule_btn(self, interaction, button):
        embed, total = build_schedule_embed(self.event)
        view = SchedulePageView(self.event, 1, interaction.user.id) if total > 1 else None
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="📊 Standings",           style=discord.ButtonStyle.secondary, row=1)
    async def standings_btn(self, interaction, button):
        embed = build_standings_embed(self.event)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# =====================================================================
#              SOCIAL EVENT ENGINE — Creative Esports Companion
# =====================================================================

# =====================================================================
#                SOCIAL EVENT ENGINE — Creative Esports Companion
# =====================================================================
#
#  Social events are NOT tournaments. They're experiences:
#  Hide & Seek, FFA, community games, themed events, special modes.
#
#  This engine provides:
#   • Points-based leaderboard (not elimination)
#   • Round-by-round scoring with fun recaps
#   • Creative random moments (Spotlight, Chaos, Sudden Death)
#   • MVP & award system
#   • Event Moments log for highlights
#   • Crowd engagement features
#   • Cinematic social-flavored announcements
# =====================================================================

import json as _json

# ── Social event constants ────────────────────────────────────────────

# ── Mobile Legends: Bang Bang — Social Event Constants ───────────────

SCORING_SYSTEMS = {
    "wins":      ("🏆", "Match Wins",    "3 pts per win, 1 per draw, 0 per loss"),
    "kills":     ("⚔️", "Kill Count",    "Points = kills submitted for the round"),
    "kda":       ("💀", "KDA Score",     "Points based on (K+A)/D ratio submitted"),
    "mvp_stars": ("⭐", "MVP Stars",     "MLBB MVP stars earned (1–3 per match)"),
    "damage":    ("💥", "Damage Dealt",  "Total hero damage submitted as score"),
    "rank":      ("🏅", "Placement",     "1st=5pts 2nd=3pts 3rd=2pts 4th=1pt 5th+=0"),
    "custom":    ("💎", "Custom Points", "Mod assigns points manually per result"),
}

SOCIAL_FLAVORS = {
    "hide_seek":      "🙈 Hide & Seek",
    "protect_layla":  "🛡️ Protect Layla",
    "one_v_one":      "🗡️ 1v1",
    "kill_race":      "⚔️ Kill Race",
    "brawl":          "🥊 Brawl Mode",
    "all_random":     "🎲 All Random",
    "hero_lock":      "🦸 Hero Lock",
    "magic_chess":    "♟️ Magic Chess",
    "kda_war":        "💀 KDA War",
    "draft_pick":     "📋 Draft Pick 5v5",
    "custom":         "⚙️ Custom Mode",
}

MLBB_EVENT_FORMATS = {
    "hide_seek": (
        "1 Natalia (Hider) vs 3 Seekers in a custom room. "
        "Seekers wait 1 min in base. Natalia hides and must stay still. "
        "3 min time limit. Seekers win by finding Natalia + emoting. "
        "Natalia wins if not found. "
        "Rules: No skills, no attacks, no invisibility, no jungle. "
        "Only Sprint/Arrival allowed. "
        "Twist: the winner becomes Natalia next round."
    ),
    "protect_layla": (
        "3v3 custom match. One team has Layla and must protect her from dying. "
        "The other team must kill Layla to win. "
        "If Layla is killed → attackers win. If Layla survives → defenders win. "
        "Rules set by mod each round."
    ),
    "one_v_one": (
        "1v1 in MLBB custom room. No lane restriction. "
        "First to the agreed kill count wins the round. "
        "Heroes chosen freely unless mod declares a hero lock."
    ),
    "kill_race": (
        "All players in the same custom match. "
        "Whoever reaches the agreed kill target first wins that round. "
        "Submit your kill count to the mod at the end."
    ),
    "brawl": (
        "Brawl mode with random heroes. "
        "Win = 3pts, Loss = 0pts. "
        "Track wins across rounds to determine the overall winner."
    ),
    "all_random": (
        "All Random mode — heroes assigned randomly each round. "
        "Best record (most wins or best KDA) across all rounds wins."
    ),
    "hero_lock": (
        "Everyone must play the same hero — mod announces the hero each round. "
        "Best performance (KDA, kills, or wins) decides the round winner."
    ),
    "magic_chess": (
        "Magic Chess custom lobby. Placement scoring: "
        "1st = 5pts · 2nd = 3pts · 3rd = 2pts · 4th = 1pt · 5th+ = 0pts."
    ),
    "kda_war": (
        "Play a full classic or ranked match. "
        "Submit your final KDA ratio to the mod. "
        "Best KDA wins the round."
    ),
    "draft_pick": (
        "Full 5v5 draft pick match between registered teams. "
        "Win = 3pts · Loss = 0pts. Brackets handled by mod."
    ),
    "custom": "Mod-defined format. Rules announced per round.",
}

HIGHLIGHT_EMOJIS = ["🔥", "💥", "⚡", "🌟", "👑", "🎯", "💎", "🏆", "⚔️", "🌀"]

ROUND_HYPE_LINES = [
    "The Land of Dawn trembles — who will dominate this round?",
    "Heroes clash and kingdoms fall — may the best player rise!",
    "The battlefield is set — prove your worth in the Land of Dawn!",
    "No recalls, no mercy — only dominance survives!",
    "The crowd in the arena roars — fighters, to your lanes!",
    "Fortune favours the bold. Crush your enemies and take the throne!",
    "The royal court watches — make every kill count!",
    "Turrets fall, heroes die — the next champion is about to emerge!",
    "Push the lord, take the base — glory goes to the decisive!",
    "Every gold, every kill, every teamfight — it all matters NOW!",
]

RESULT_HYPE_LINES = [
    "What a performance in the Land of Dawn!",
    "The crowd goes absolutely wild!",
    "A legendary showing from our fighters tonight!",
    "History is being written in the chronicles of the Dominion!",
    "The Oracle could not have predicted this — extraordinary!",
    "Pure mechanical skill on display — the enemy nexus never stood a chance!",
    "The late-game carry was REAL tonight!",
    "That KDA doesn't lie — someone showed up to perform!",
]


# ── SocialEventEngine ─────────────────────────────────────────────────

class SocialEventEngine:
    """
    Engine for social/fun events.
    Manages rounds, points, leaderboard, moments, and progression.
    """

    @staticmethod
    def init_social_data(event):
        """Ensure event has all social-specific fields."""
        event.setdefault("social_data", {
            "rounds": [],
            "leaderboard": {},
            "moments": [],          # logged highlights
            "scoring_system": "points",
            "points_per_win":  3,
            "points_per_draw": 1,
            "points_per_loss": 0,
            "mvp": None,
            "flavor": "custom",
            "round_counter": 0,
        })
        return event["social_data"]

    @staticmethod
    def get_social_data(event) -> dict:
        return SocialEventEngine.init_social_data(event)

    @staticmethod
    def create_round(event, round_name=None, participants=None) -> dict:
        sd = SocialEventEngine.get_social_data(event)
        sd["round_counter"] = sd.get("round_counter", 0) + 1
        rn = round_name or f"Round {sd['round_counter']}"
        rnd = {
            "round_id":   f"sr_{sd['round_counter']}",
            "round_name": rn,
            "status":     "pending",
            "participants": participants or [get_reg_name(r) for r in event.get("registrations", [])],
            "results":    [],
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
        }
        sd["rounds"].append(rnd)
        return rnd

    @staticmethod
    def get_active_round(event) -> dict | None:
        sd = SocialEventEngine.get_social_data(event)
        for rnd in reversed(sd.get("rounds", [])):
            if rnd["status"] in ("pending", "live"):
                return rnd
        return None

    @staticmethod
    def get_last_completed_round(event) -> dict | None:
        sd = SocialEventEngine.get_social_data(event)
        for rnd in reversed(sd.get("rounds", [])):
            if rnd["status"] == "completed":
                return rnd
        return None

    @staticmethod
    def record_round_results(event, round_id, results: list, recorded_by=None) -> dict:
        """
        results = [{"participant": "Name", "points": 5, "result": "1st/win/loss", "note": "..."}]
        Returns: {"round": rnd, "leaderboard": {...}, "mvp_candidate": str|None}
        """
        sd  = SocialEventEngine.get_social_data(event)
        rnd = next((r for r in sd["rounds"] if r["round_id"] == round_id), None)
        if not rnd:
            return {"error": "Round not found"}

        scoring = sd.get("scoring_system", "points")
        pw = sd.get("points_per_win", 3)
        pd = sd.get("points_per_draw", 1)
        pl = sd.get("points_per_loss", 0)

        rnd["results"]      = results
        rnd["status"]       = "completed"
        rnd["completed_at"] = datetime.utcnow().isoformat()
        if recorded_by:
            rnd["recorded_by"] = str(recorded_by)

        # Update leaderboard
        lb = sd.setdefault("leaderboard", {})
        for entry in results:
            name   = entry.get("participant", "?")
            pts    = entry.get("points", 0)
            result = entry.get("result", "").lower()

            # Auto-calc points if using win/loss system
            if scoring == "win_loss":
                if "win" in result or result in ("1st", "1", "first"):
                    pts = pw
                elif "draw" in result or result == "tie":
                    pts = pd
                else:
                    pts = pl
            elif scoring == "rank":
                rank_map = {"1st":5, "1":5, "first":5, "2nd":3, "2":3, "second":3,
                            "3rd":1, "3":1, "third":1}
                pts = rank_map.get(result, 0)

            if name not in lb:
                lb[name] = {"total_points": 0, "rounds_played": 0,
                            "wins": 0, "best_result": None, "round_scores": []}
            lb[name]["total_points"]  += pts
            lb[name]["rounds_played"] += 1
            lb[name]["round_scores"].append(pts)
            if result in ("1st", "1", "first", "win"):
                lb[name]["wins"] = lb[name].get("wins", 0) + 1
            if lb[name]["best_result"] is None or pts > lb[name]["best_result"]:
                lb[name]["best_result"] = pts

        # Store round in event match_results for unified history
        event.setdefault("match_results", []).append({
            "match_id":   round_id,
            "type":       "social_round",
            "round_name": rnd["round_name"],
            "results":    results,
            "recorded_at": rnd["completed_at"],
        })

        # Determine MVP candidate (highest points this round)
        if results:
            top = max(results, key=lambda x: x.get("points", 0))
            mvp_candidate = top["participant"]
        else:
            mvp_candidate = None

        return {
            "round":         rnd,
            "leaderboard":   lb,
            "mvp_candidate": mvp_candidate,
        }

    @staticmethod
    def get_sorted_leaderboard(event) -> list:
        sd = SocialEventEngine.get_social_data(event)
        lb = sd.get("leaderboard", {})
        return sorted(
            [{"name": k, **v} for k, v in lb.items()],
            key=lambda x: (-x["total_points"], -x.get("wins", 0))
        )

    @staticmethod
    def crown_mvp(event, mvp_name=None):
        """Crown MVP — either specified or auto (highest points)."""
        sd = SocialEventEngine.get_social_data(event)
        if not mvp_name:
            lb_sorted = SocialEventEngine.get_sorted_leaderboard(event)
            if lb_sorted:
                mvp_name = lb_sorted[0]["name"]
        sd["mvp"] = mvp_name
        event["champion"] = mvp_name
        return mvp_name

    @staticmethod
    def log_moment(event, description, emoji=None):
        """Log a special highlight moment."""
        sd = SocialEventEngine.get_social_data(event)
        if not emoji:
            emoji = random.choice(HIGHLIGHT_EMOJIS)
        sd.setdefault("moments", []).append({
            "emoji":       emoji,
            "description": description,
            "timestamp":   datetime.utcnow().isoformat(),
        })

    @staticmethod
    def random_spotlight(event) -> str | None:
        """Randomly select one participant to spotlight."""
        regs = event.get("registrations", [])
        if not regs:
            return None
        return random.choice([get_reg_name(r) for r in regs])

    @staticmethod
    def sudden_death_pair(event):
        """Pick the top 2 on leaderboard for a sudden death round."""
        lb = SocialEventEngine.get_sorted_leaderboard(event)
        if len(lb) < 2:
            return None, None
        return lb[0]["name"], lb[1]["name"]

    @staticmethod
    def chaos_shuffle(event) -> list:
        """Randomly reshuffle all participants and return new pairs."""
        regs = [get_reg_name(r) for r in event.get("registrations", [])]
        random.shuffle(regs)
        pairs = []
        for i in range(0, len(regs) - 1, 2):
            pairs.append((regs[i], regs[i+1]))
        if len(regs) % 2 != 0:
            pairs.append((regs[-1], "BYE"))
        return pairs

    @staticmethod
    def lucky_draw(event) -> str | None:
        """Random lucky participant — no logic, pure chaos."""
        regs = event.get("registrations", [])
        if not regs:
            return None
        return random.choice([get_reg_name(r) for r in regs])


# ── Social Announcement Embeds ────────────────────────────────────────

def build_social_round_start_embed(event, rnd) -> discord.Embed:
    """Energetic round start announcement — mode-aware for MLBB."""
    hype   = random.choice(ROUND_HYPE_LINES)
    sd     = SocialEventEngine.get_social_data(event)
    flavor = sd.get("flavor", "custom")
    fl_label = SOCIAL_FLAVORS.get(flavor, "🎪 Event")
    parts    = rnd.get("participants", [])

    embed = discord.Embed(
        title=f"🎪 {rnd['round_name'].upper()} — BEGIN!",
        description=(
            f"## {event['name']}  ·  {fl_label}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"*{hype}*"
        ),
        color=ROYAL_RED,
        timestamp=datetime.utcnow()
    )

    # ── Mode-specific rules block ─────────────────────────────────────
    if flavor == "hide_seek":
        embed.add_field(
            name="🙈 Hide & Seek Rules",
            value=(
                "🦸 **Hider:** Natalia — hide and **stay still**\n"
                "👁️ **Seekers:** 3 players — wait 1 min in base\n"
                "⏱️ **Time Limit:** 3 minutes\n"
                "🏆 **Seekers win:** Find Natalia + emote\n"
                "🏆 **Natalia wins:** Not found in time\n"
                "❌ No skills · No attacks · No invisibility\n"
                "❌ No jungle · Only Sprint/Arrival allowed\n"
                "🔄 **Twist:** Winner becomes Natalia next round"
            ),
            inline=False
        )
        # Assign roles if participants listed
        if len(parts) >= 4:
            hider   = parts[0]
            seekers = parts[1:4]
            embed.add_field(name="🦸 Hider (Natalia)", value=f"**{hider}**",                         inline=True)
            embed.add_field(name="👁️ Seekers",          value="\n".join(f"• {s}" for s in seekers), inline=True)
        elif parts:
            embed.add_field(name="👥 Participants",
                value="\n".join(f"• {p}" for p in parts[:10]), inline=False)

    elif flavor == "protect_layla":
        embed.add_field(
            name="🛡️ Protect Layla Rules",
            value=(
                "👑 **Defenders (3):** Protect Layla at all costs\n"
                "⚔️ **Attackers (3):** Kill Layla to win\n"
                "🏆 **Attackers win:** Layla dies\n"
                "🏆 **Defenders win:** Layla survives the time limit\n"
                "📋 *Mod announces time limit and Layla player*"
            ),
            inline=False
        )
        if len(parts) >= 2:
            half = len(parts) // 2
            defenders = parts[:half]
            attackers = parts[half:]
            embed.add_field(name="🛡️ Defenders",
                value="\n".join(f"• {p}" for p in defenders), inline=True)
            embed.add_field(name="⚔️ Attackers",
                value="\n".join(f"• {p}" for p in attackers), inline=True)

    elif flavor == "one_v_one":
        embed.add_field(
            name="🗡️ 1v1 Rules",
            value=(
                "⚔️ Custom room 1v1 in Mobile Legends\n"
                "🏆 First to the agreed kill count wins\n"
                "🦸 Heroes chosen freely\n"
                "📋 *Mod confirms kill target before match starts*"
            ),
            inline=False
        )
        if len(parts) >= 2:
            for i in range(0, min(len(parts), 20), 2):
                p1 = parts[i]
                p2 = parts[i+1] if i+1 < len(parts) else "BYE"
                embed.add_field(name=f"⚔️ Match {i//2+1}",
                    value=f"**{p1}** vs **{p2}**", inline=True)

    elif flavor == "kill_race":
        embed.add_field(
            name="⚔️ Kill Race Rules",
            value=(
                "💀 All players in the same custom match\n"
                "🏆 First to the agreed kill target wins\n"
                "📋 Submit your final kill count to the mod"
            ),
            inline=False
        )
        if parts:
            embed.add_field(name=f"👥 Fighters ({len(parts)})",
                value="\n".join(f"⚔️ **{p}**" for p in parts[:10])
                + ("..." if len(parts) > 10 else ""), inline=False)

    else:
        # Generic participants list for other modes
        if parts:
            fmt_txt = MLBB_EVENT_FORMATS.get(flavor, "")
            if fmt_txt:
                embed.add_field(name="📋 Format", value=fmt_txt[:512], inline=False)
            lines = [f"⚔️ **{p}**" for p in parts[:20]]
            embed.add_field(
                name=f"👥 Participants ({len(parts)})",
                value="\n".join(lines) + ("..." if len(parts) > 20 else ""),
                inline=False
            )

    # Leaderboard teaser
    lb = SocialEventEngine.get_sorted_leaderboard(event)
    if lb:
        leader = lb[0]
        embed.add_field(
            name="👑 Current Leader",
            value=f"**{leader['name']}** — {leader['total_points']} pts",
            inline=True
        )

    embed.set_footer(text=f"⚜️ {event['name']} | Majestic Dominion")
    apply_branding(embed, thumbnail=True)
    return embed


def build_social_round_recap_embed(event, rnd, result_info) -> discord.Embed:
    """Cinematic round result recap."""
    hype = random.choice(RESULT_HYPE_LINES)
    results = rnd.get("results", [])
    mvp_c   = result_info.get("mvp_candidate")
    lb      = SocialEventEngine.get_sorted_leaderboard(event)

    # Find the round winner (highest points)
    top_result = max(results, key=lambda x: x.get("points", 0)) if results else None

    sd_r = SocialEventEngine.get_social_data(event)
    sc   = sd_r.get("scoring_system","custom")
    sc_icon = SCORING_SYSTEMS.get(sc,("💎","",""))[0]
    flav = SOCIAL_FLAVORS.get(sd_r.get("flavor","custom"), "🎪")
    embed = discord.Embed(
        title=f"🏁 {rnd['round_name'].upper()} — COMPLETE!",
        description=(
            f"## {event['name']}  ·  {flav}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"*{hype}*"
        ),
        color=ROYAL_PURPLE,
        timestamp=datetime.utcnow()
    )

    # Round results
    if results:
        sorted_results = sorted(results, key=lambda x: -x.get("points", 0))
        medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 50
        lines  = []
        for i, r in enumerate(sorted_results[:15]):
            note = f" · *{r['note']}*" if r.get("note") else ""
            score_val = r.get('result', str(r.get('points',0)))
            lines.append(f"{medals[i]} **{r['participant']}** — {sc_icon} {score_val}{note}")
        embed.add_field(
            name=f"📊 Round Results",
            value="\n".join(lines)[:1024],
            inline=False
        )

    # Round star
    if top_result:
        embed.add_field(
            name="⭐ Round Star",
            value=f"**{top_result['participant']}** — {top_result.get('points',0)} pts",
            inline=True
        )

    # Overall standings top 3
    if lb:
        top3 = lb[:3]
        m    = ["🥇","🥈","🥉"]
        stand = "\n".join(f"{m[i]} **{s['name']}** — {s['total_points']} pts total" for i,s in enumerate(top3))
        embed.add_field(name="🏆 Overall Top 3", value=stand, inline=True)

    # Total rounds played
    sd = SocialEventEngine.get_social_data(event)
    total_rounds = len([r for r in sd.get("rounds",[]) if r["status"]=="completed"])
    embed.add_field(name="📈 Rounds Complete", value=str(total_rounds), inline=True)

    embed.set_footer(text=f"⚜️ {event['name']} | Use /events → 📊 Leaderboard to follow along!")
    apply_branding(embed, thumbnail=True)
    return embed


def build_social_leaderboard_embed(event) -> discord.Embed:
    """Live social event leaderboard."""
    lb    = SocialEventEngine.get_sorted_leaderboard(event)
    sd    = SocialEventEngine.get_social_data(event)
    total = len([r for r in sd.get("rounds",[]) if r["status"]=="completed"])
    mvp   = sd.get("mvp")

    sc_key  = sd.get("scoring_system","custom")
    sc_info = SCORING_SYSTEMS.get(sc_key, ("💎","Points",""))
    fl_key  = sd.get("flavor","custom")
    fl_name = SOCIAL_FLAVORS.get(fl_key, "⚙️ Custom")
    embed = discord.Embed(
        title=f"📊 Live Leaderboard — {event['name']}",
        description=(
            f"{fl_name} · {sc_info[0]} **{sc_info[1]}** scoring\n"
            f"After **{total}** round(s) · **{len(lb)}** participants on the board"
        ),
        color=ROYAL_GOLD,
        timestamp=datetime.utcnow()
    )

    if not lb:
        embed.description = "*No results recorded yet. Check back after the first round!*"
    else:
        medals = ["🥇","🥈","🥉"] + ["🏅"]*50
        lines  = []
        for i, s in enumerate(lb[:20]):
            rp  = s.get("rounds_played",0)
            avg = round(s["total_points"]/rp, 1) if rp else 0
            mvp_badge = " 👑" if s["name"] == mvp else ""
            lines.append(
                f"{medals[i]} **{s['name']}**{mvp_badge} — "
                f"**{s['total_points']} pts** · {rp} rounds · avg {avg}"
            )
        embed.description = "\n".join(lines)[:2048]

    # Show moments if any
    moments = sd.get("moments", [])[-4:]
    if moments:
        mlines = [f"{m['emoji']} *{m['description']}*" for m in moments]
        embed.add_field(name="✨ Event Highlights", value="\n".join(mlines)[:1024], inline=False)

    embed.set_footer(text=f"⚜️ Majestic Dominion | {event['name']}")
    apply_branding(embed, thumbnail=True)
    return embed


def build_social_mvp_embed(event, mvp_name) -> discord.Embed:
    """Grand MVP / winner announcement for social events."""
    lb     = SocialEventEngine.get_sorted_leaderboard(event)
    mvp_s  = next((s for s in lb if s["name"] == mvp_name), {})
    total_pts = mvp_s.get("total_points", "?")
    wins      = mvp_s.get("wins", 0)
    rounds    = mvp_s.get("rounds_played", 0)

    embed = discord.Embed(
        title="🌟 MOST VALUABLE PLAYER!",
        description=(
            f"## ⭐ {mvp_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*The Crown recognizes an exceptional performance.*\n\n"
            f"🏆 **{event['name']}** — Event MVP\n\n"
            f"💎 **{total_pts}** total points · "
            f"🏅 **{wins}** round win(s) · "
            f"⚔️ **{rounds}** rounds competed\n\n"
            f"*Glory to the most dominant competitor in the Dominion!*"
        ),
        color=ROYAL_GOLD,
        timestamp=datetime.utcnow()
    )

    # Top 3 podium
    if lb:
        podium = []
        medals = ["🥇","🥈","🥉"]
        for i, s in enumerate(lb[:3]):
            podium.append(f"{medals[i]} **{s['name']}** — {s['total_points']} pts")
        embed.add_field(name="🏆 Final Podium", value="\n".join(podium), inline=False)

    # Event moments
    sd = SocialEventEngine.get_social_data(event)
    moments = sd.get("moments", [])
    if moments:
        mlines = [f"{m['emoji']} *{m['description']}*" for m in moments[-5:]]
        embed.add_field(name="✨ Event Highlights", value="\n".join(mlines)[:1024], inline=False)

    embed.set_footer(text=f"⚜️ Majestic Dominion | {event['name']} — Concluded")
    apply_branding(embed, thumbnail=False, author=True)
    return embed


def build_social_spotlight_embed(event, name) -> discord.Embed:
    """Random spotlight announcement."""
    hype_lines = [
        f"**{name}** steps into the spotlight — the Land of Dawn watches!",
        f"The Oracle points to **{name}** — prove your worth!",
        f"**{name}** is called to the arena — don't disappoint the crown!",
        f"All eyes on **{name}** — the crowd holds its breath!",
        f"**{name}** — your moment has come in the Land of Dawn!",
        f"**{name}** is chosen — glory or humiliation awaits!",
    ]
    embed = discord.Embed(
        title="🎯 RANDOM SPOTLIGHT!",
        description=(
            f"## ⭐ {name}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*{random.choice(hype_lines)}*"
        ),
        color=ROYAL_RED,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=f"⚜️ {event['name']} | Majestic Dominion")
    apply_branding(embed, thumbnail=True)
    return embed


def build_social_sudden_death_embed(event, p1, p2) -> discord.Embed:
    sd = SocialEventEngine.get_social_data(event)
    flavor = sd.get("flavor", "custom")
    mode_hint = {
        "hide_seek":     "One hides as Natalia, one seeks — loser drops on the leaderboard!",
        "protect_layla": "1 defends Layla, 1 attacks — sudden death rules apply!",
        "one_v_one":     "First kill wins — no second chances in sudden death!",
        "kill_race":     "First to 1 kill wins — pure reaction speed!",
    }.get(flavor, "One match decides it all — may the best player win!")

    embed = discord.Embed(
        title="⚡ SUDDEN DEATH!",
        description=(
            f"## {p1}  ⚡  {p2}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*The top two warriors clash — only one survives!*\n\n"
            f"📋 {mode_hint}\n\n"
            f"*No mercy. No excuses. This is Mobile Legends.*"
        ),
        color=ROYAL_RED,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=f"⚜️ {event['name']} | Majestic Dominion")
    apply_branding(embed, thumbnail=True)
    return embed


def build_social_chaos_embed(event, pairs) -> discord.Embed:
    embed = discord.Embed(
        title="🌀 CHAOS ROUND — RESHUFFLED!",
        description=(
            f"## {event['name']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*The Oracle has spoken — all pairings reshuffled!*\n\n"
            f"*Nothing is safe. Everything is possible. Pure chaos begins NOW!*"
        ),
        color=0x9B59B6,
        timestamp=datetime.utcnow()
    )
    if pairs:
        lines = []
        for p1, p2 in pairs[:15]:
            if p2 == "BYE":
                lines.append(f"🚪 **{p1}** — BYE")
            else:
                lines.append(f"⚡ **{p1}** vs **{p2}**")
        embed.add_field(name="🎲 New Pairings", value="\n".join(lines)[:1024], inline=False)
    embed.set_footer(text=f"⚜️ {event['name']} | Majestic Dominion")
    apply_branding(embed, thumbnail=True)
    return embed


def build_social_moment_embed(event, emoji, description) -> discord.Embed:
    embed = discord.Embed(
        title=f"{emoji} EVENT HIGHLIGHT!",
        description=f"## {event['name']}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n*{description}*",
        color=ROYAL_GOLD,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=f"⚜️ {event['name']} | Majestic Dominion")
    apply_branding(embed, thumbnail=True)
    return embed


# ── Social Event Manager Views (Mod Tools) ────────────────────────────

class SocialEventManagerView(View):
    """Full social event control panel for mods."""
    def __init__(self, event, author_id):
        super().__init__(timeout=300)
        self.event     = event
        self.author_id = author_id
        sd = SocialEventEngine.get_social_data(event)
        active = SocialEventEngine.get_active_round(event)
        self.start_round_btn.disabled   = active is not None  # can't start new if one is active
        self.record_round_btn.disabled  = active is None       # can't record if no active round
        self.end_round_btn.disabled     = active is None
        self.sudden_death_btn.disabled  = len(SocialEventEngine.get_sorted_leaderboard(event)) < 2
        self.crown_mvp_btn.disabled     = not sd.get("leaderboard")

    def _check(self, interaction):
        return interaction.user.id == self.author_id

    @discord.ui.button(label="▶️ Start New Round", style=discord.ButtonStyle.success, row=0)
    async def start_round_btn(self, interaction, button):
        if not self._check(interaction): return
        await interaction.response.send_modal(StartSocialRoundModal(self.event, self.author_id))

    @discord.ui.button(label="📝 Record Round", style=discord.ButtonStyle.danger, row=0)
    async def record_round_btn(self, interaction, button):
        if not self._check(interaction): return
        active = SocialEventEngine.get_active_round(self.event)
        if not active:
            return await interaction.response.send_message("❌ No active round.", ephemeral=True)
        await interaction.response.send_modal(
            RecordSocialRoundModal(self.event, active, self.author_id))

    @discord.ui.button(label="⏹️ Close Round", style=discord.ButtonStyle.secondary, row=0)
    async def end_round_btn(self, interaction, button):
        if not self._check(interaction): return
        active = SocialEventEngine.get_active_round(self.event)
        if not active:
            return await interaction.response.send_message("❌ No active round.", ephemeral=True)
        active["status"] = "completed"
        active["completed_at"] = datetime.utcnow().isoformat()
        save_data(squad_data)
        embed = discord.Embed(title="⏹️ Round Closed",
            description=f"**{active['round_name']}** closed without results.", color=ROYAL_RED)
        apply_branding(embed, thumbnail=True)
        await interaction.response.edit_message(embed=embed, view=SocialEventManagerView(self.event, self.author_id))

    @discord.ui.button(label="🎯 Random Spotlight", style=discord.ButtonStyle.primary, row=1)
    async def spotlight_btn(self, interaction, button):
        if not self._check(interaction): return
        name = SocialEventEngine.random_spotlight(self.event)
        if not name:
            return await interaction.response.send_message("❌ No registrations.", ephemeral=True)
        SocialEventEngine.log_moment(self.event, f"{name} was put in the spotlight!", "🎯")
        save_data(squad_data)
        embed = build_social_spotlight_embed(self.event, name)
        await interaction.response.edit_message(embed=embed, view=self)
        await announce_event(interaction.guild, build_social_spotlight_embed(self.event, name))
        await log_action(interaction.guild, "🎯 Spotlight",
            f"{interaction.user.mention} spotlighted **{name}** in **{self.event['name']}**")

    @discord.ui.button(label="⚡ Sudden Death", style=discord.ButtonStyle.danger, row=1)
    async def sudden_death_btn(self, interaction, button):
        if not self._check(interaction): return
        p1, p2 = SocialEventEngine.sudden_death_pair(self.event)
        if not p1:
            return await interaction.response.send_message("❌ Need at least 2 on leaderboard.", ephemeral=True)
        SocialEventEngine.log_moment(self.event, f"Sudden Death: {p1} vs {p2}!", "⚡")
        save_data(squad_data)
        embed = build_social_sudden_death_embed(self.event, p1, p2)
        await interaction.response.edit_message(embed=embed, view=self)
        await announce_event(interaction.guild, build_social_sudden_death_embed(self.event, p1, p2))
        await log_action(interaction.guild, "⚡ Sudden Death",
            f"{interaction.user.mention} called sudden death between **{p1}** vs **{p2}** in **{self.event['name']}**")

    @discord.ui.button(label="🌀 Chaos Reshuffle", style=discord.ButtonStyle.primary, row=1)
    async def chaos_btn(self, interaction, button):
        if not self._check(interaction): return
        pairs = SocialEventEngine.chaos_shuffle(self.event)
        if not pairs:
            return await interaction.response.send_message("❌ No registrations to shuffle.", ephemeral=True)
        SocialEventEngine.log_moment(self.event, "All pairings reshuffled — pure chaos!", "🌀")
        save_data(squad_data)
        embed = build_social_chaos_embed(self.event, pairs)
        await interaction.response.edit_message(embed=embed, view=self)
        await announce_event(interaction.guild, build_social_chaos_embed(self.event, pairs))
        await log_action(interaction.guild, "🌀 Chaos Shuffle",
            f"{interaction.user.mention} chaos-reshuffled **{self.event['name']}**")

    @discord.ui.button(label="🎰 Lucky Draw", style=discord.ButtonStyle.secondary, row=2)
    async def lucky_btn(self, interaction, button):
        if not self._check(interaction): return
        name = SocialEventEngine.lucky_draw(self.event)
        if not name:
            return await interaction.response.send_message("❌ No registrations.", ephemeral=True)
        # Give +1 bonus point
        sd = SocialEventEngine.get_social_data(self.event)
        lb = sd.setdefault("leaderboard", {})
        lb.setdefault(name, {"total_points":0,"rounds_played":0,"wins":0,"round_scores":[]})
        lb[name]["total_points"] += 1
        SocialEventEngine.log_moment(self.event, f"{name} won the Lucky Draw — +1 bonus point! 🎰", "🎰")
        save_data(squad_data)
        embed = discord.Embed(
            title="🎰 LUCKY DRAW!",
            description=f"## 🍀 {name}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"*Fortune smiles on the bold!*\n\n"
                        f"**{name}** wins a **+1 bonus point** from the Lucky Draw!\n\n"
                        f"*The Crown rewards those blessed by fate.*",
            color=ROYAL_GOLD, timestamp=datetime.utcnow()
        )
        apply_branding(embed, thumbnail=True)
        await interaction.response.edit_message(embed=embed, view=self)
        await announce_event(interaction.guild, embed)
        await log_action(interaction.guild, "🎰 Lucky Draw",
            f"{interaction.user.mention} ran lucky draw — **{name}** +1 pt in **{self.event['name']}**")

    @discord.ui.button(label="✨ Log Moment", style=discord.ButtonStyle.secondary, row=2)
    async def moment_btn(self, interaction, button):
        if not self._check(interaction): return
        await interaction.response.send_modal(LogMomentModal(self.event, self.author_id))

    @discord.ui.button(label="👑 Crown MVP", style=discord.ButtonStyle.success, row=2)
    async def crown_mvp_btn(self, interaction, button):
        if not self._check(interaction): return
        await interaction.response.send_modal(CrownMVPModal(self.event, self.author_id))

    @discord.ui.button(label="⚙️ Settings", style=discord.ButtonStyle.secondary, row=3)
    async def settings_btn(self, interaction, button):
        if not self._check(interaction): return
        await interaction.response.send_modal(SocialSettingsModal(self.event, self.author_id))

    @discord.ui.button(label="📊 Leaderboard", style=discord.ButtonStyle.secondary, row=3)
    async def lb_btn(self, interaction, button):
        if not self._check(interaction): return
        embed = build_social_leaderboard_embed(self.event)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=3)
    async def refresh_btn(self, interaction, button):
        if not self._check(interaction): return
        await interaction.response.edit_message(
            embed=build_social_dashboard_embed(self.event),
            view=SocialEventManagerView(self.event, self.author_id)
        )


def build_social_dashboard_embed(event) -> discord.Embed:
    """Mod dashboard for social events."""
    sd     = SocialEventEngine.get_social_data(event)
    active = SocialEventEngine.get_active_round(event)
    lb     = SocialEventEngine.get_sorted_leaderboard(event)
    done_rounds = len([r for r in sd.get("rounds",[]) if r["status"]=="completed"])
    flavor = SOCIAL_FLAVORS.get(sd.get("flavor","custom"), "🎪")
    scoring = SCORING_SYSTEMS.get(sd.get("scoring_system","points"), ("💎","Points",""))[1]

    fmt_hint = MLBB_EVENT_FORMATS.get(sd.get("flavor","custom"), "")
    embed = discord.Embed(
        title=f"🎪 MLBB Event Control — {event['name']}",
        description=(
            f"{flavor} · **{scoring}** scoring · "
            f"**{len(event.get('registrations',[]))}** participants\n"
            f"**{done_rounds}** round(s) complete · "
            f"{'⚔️ **Round Active**' if active else '⏳ *No active round*'}"
            + (f"\n📋 *{fmt_hint}*" if fmt_hint else "")
        ),
        color=ROYAL_PURPLE,
        timestamp=datetime.utcnow()
    )

    if active:
        embed.add_field(
            name=f"⚔️ Active: {active['round_name']}",
            value=f"**{len(active.get('participants',[]))}** participants · {active['status']}",
            inline=False
        )

    if lb:
        top3 = lb[:3]
        m    = ["🥇","🥈","🥉"]
        stand = "\n".join(f"{m[i]} **{s['name']}** — {s['total_points']} pts" for i,s in enumerate(top3))
        embed.add_field(name="📊 Top 3", value=stand, inline=True)

    moments = sd.get("moments",[])[-3:]
    if moments:
        mlines = [f"{m['emoji']} *{m['description'][:50]}*" for m in moments]
        embed.add_field(name="✨ Recent Highlights", value="\n".join(mlines), inline=True)

    embed.set_footer(text="⚜️ Majestic Dominion | Social Event Control Panel")
    apply_branding(embed, thumbnail=True)
    return embed


# ── Modals for Social Event Management ───────────────────────────────

class StartSocialRoundModal(Modal, title="▶️ Start New Round"):
    round_name = TextInput(label="Round Name",
        placeholder="e.g. Round 1, Elimination Round, Finals...",
        required=True, max_length=50)
    custom_participants = TextInput(
        label="Participants (one per line, or leave blank for all)",
        placeholder="Leave blank to include all registrants",
        style=discord.TextStyle.paragraph, required=False, max_length=500)
    def __init__(self, event, author_id):
        super().__init__(); self.event = event; self.author_id = author_id

    async def on_submit(self, interaction):
        parts = None
        if self.custom_participants.value.strip():
            parts = [p.strip() for p in self.custom_participants.value.strip().split("\n") if p.strip()]
        rnd = SocialEventEngine.create_round(self.event, self.round_name.value.strip(), parts)
        rnd["status"] = "live"
        save_data(squad_data)
        embed = build_social_round_start_embed(self.event, rnd)
        await interaction.response.edit_message(
            embed=build_social_dashboard_embed(self.event),
            view=SocialEventManagerView(self.event, self.author_id)
        )
        await announce_event(interaction.guild, embed)
        await log_action(interaction.guild, "▶️ Round Started",
            f"{interaction.user.mention} started **{rnd['round_name']}** in **{self.event['name']}**")


class RecordSocialRoundModal(Modal, title="📝 Record Match Results"):
    results_raw = TextInput(
        label="Results — IGN: value  (one per line)",
        placeholder=(
            "Kills mode:   PlayerA: 18\nPlayerB: 12\n"
            "Wins mode:    PlayerA: win\nPlayerB: loss\n"
            "KDA mode:     PlayerA: 8.5\nPlayerB: 3.2\n"
            "MVP Stars:    PlayerA: 3\nPlayerB: 2"
        ),
        style=discord.TextStyle.paragraph,
        required=True, max_length=2000
    )
    def __init__(self, event, rnd, author_id):
        super().__init__(); self.event = event; self.rnd = rnd; self.author_id = author_id

    async def on_submit(self, interaction):
        sd      = SocialEventEngine.get_social_data(self.event)
        scoring = sd.get("scoring_system", "custom")
        pw = sd.get("points_per_win", 3)
        pd_pts = sd.get("points_per_draw", 1)
        pl = sd.get("points_per_loss", 0)
        results = []

        for line in self.results_raw.value.strip().split("\n"):
            line = line.strip()
            if not line or ":" not in line:
                continue
            name, val = line.split(":", 1)
            name = name.strip(); val = val.strip()

            # ── MLBB-aware result parsing ──────────────────────────────
            val_lower = val.lower()

            if scoring == "wins":
                # win/loss/draw text
                if val_lower in ("win","w","1st","victory"):
                    pts = pw; result_str = "Win"
                elif val_lower in ("draw","tie"):
                    pts = pd_pts; result_str = "Draw"
                elif val_lower in ("loss","lose","l","defeat"):
                    pts = pl; result_str = "Loss"
                else:
                    try: pts = int(val); result_str = f"{pts} wins"
                    except: pts = 0; result_str = val

            elif scoring == "kills":
                # raw kill count becomes the score
                try: pts = int(val); result_str = f"{pts} kills"
                except: pts = 0; result_str = val

            elif scoring == "kda":
                # float KDA ratio
                try:
                    kda = float(val)
                    pts = round(kda * 2)   # KDA 5.0 → 10pts, 2.5 → 5pts etc.
                    result_str = f"KDA {kda}"
                except: pts = 0; result_str = val

            elif scoring == "mvp_stars":
                # MLBB MVP stars: 1, 2, or 3 per match
                try:
                    stars = max(0, min(3, int(val)))
                    pts   = stars
                    result_str = f"{'⭐' * stars}"
                except: pts = 0; result_str = val

            elif scoring == "damage":
                # raw damage number, scaled down for leaderboard
                try:
                    dmg = int(val.replace(",","").replace(".",""))
                    pts = dmg // 1000   # 50000 damage → 50pts
                    result_str = f"{dmg:,} dmg"
                except: pts = 0; result_str = val

            elif scoring == "rank":
                # placement 1st-8th
                rank_pts = {"1":5,"1st":5,"first":5,
                            "2":3,"2nd":3,"second":3,
                            "3":2,"3rd":2,"third":2,
                            "4":1,"4th":1,"fourth":1}
                pts = rank_pts.get(val_lower, 0)
                result_str = f"#{val}"

            else:
                # custom: just take the number
                try: pts = int(val); result_str = f"{pts} pts"
                except: pts = 0; result_str = val

            results.append({"participant": name, "points": pts,
                            "result": result_str, "note": ""})

        if not results:
            return await interaction.response.send_message(
                "❌ No valid results parsed.\n"
                "Format: `IGN: value` one per line.\n"
                "Examples: `PlayerA: win` · `PlayerA: 18` · `PlayerA: 8.5`",
                ephemeral=True)

        result_info = SocialEventEngine.record_round_results(
            self.event, self.rnd["round_id"], results, interaction.user.id)
        save_data(squad_data)

        recap = build_social_round_recap_embed(self.event, self.rnd, result_info)
        await interaction.response.edit_message(
            embed=build_social_dashboard_embed(self.event),
            view=SocialEventManagerView(self.event, self.author_id)
        )
        await announce_event(interaction.guild, recap)
        await log_action(interaction.guild, "📝 Round Recorded",
            f"{interaction.user.mention} recorded **{self.rnd['round_name']}** "
            f"({len(results)} results) in **{self.event['name']}**")


class LogMomentModal(Modal, title="✨ Log Event Highlight"):
    emoji_input = TextInput(label="Emoji (optional)", placeholder="🔥 💥 ⚡ etc.",
        required=False, max_length=5)
    description = TextInput(label="What happened?",
        placeholder="PlayerX pulled off an insane play!",
        style=discord.TextStyle.paragraph, required=True, max_length=200)
    def __init__(self, event, author_id):
        super().__init__(); self.event = event; self.author_id = author_id

    async def on_submit(self, interaction):
        emoji = self.emoji_input.value.strip() or random.choice(HIGHLIGHT_EMOJIS)
        desc  = self.description.value.strip()
        SocialEventEngine.log_moment(self.event, desc, emoji)
        save_data(squad_data)
        moment_embed = build_social_moment_embed(self.event, emoji, desc)
        await interaction.response.edit_message(
            embed=build_social_dashboard_embed(self.event),
            view=SocialEventManagerView(self.event, self.author_id)
        )
        await announce_event(interaction.guild, moment_embed)
        await log_action(interaction.guild, "✨ Moment Logged",
            f"{interaction.user.mention} logged highlight in **{self.event['name']}**: *{desc[:80]}*")


class CrownMVPModal(Modal, title="👑 Crown Event MVP"):
    mvp_name = TextInput(
        label="MVP Name (leave blank for auto — highest pts)",
        placeholder="Leave blank to auto-crown top leaderboard player",
        required=False, max_length=80
    )
    def __init__(self, event, author_id):
        super().__init__(); self.event = event; self.author_id = author_id

    async def on_submit(self, interaction):
        name = self.mvp_name.value.strip() or None
        mvp  = SocialEventEngine.crown_mvp(self.event, name)
        if not mvp:
            return await interaction.response.send_message(
                "❌ Could not determine MVP. Record some round results first.", ephemeral=True)
        self.event["status"]   = "completed"
        self.event["champion"] = mvp
        save_data(squad_data)
        mvp_embed = build_social_mvp_embed(self.event, mvp)
        await interaction.response.edit_message(
            embed=build_social_dashboard_embed(self.event),
            view=SocialEventManagerView(self.event, self.author_id)
        )
        await announce_major(interaction.guild, mvp_embed)
        await log_action(interaction.guild, "👑 MVP Crowned",
            f"{interaction.user.mention} crowned **{mvp}** as MVP of **{self.event['name']}**")


class SocialSettingsModal(Modal, title="⚙️ MLBB Event Settings"):
    scoring = TextInput(
        label="Scoring  (wins / kills / kda / mvp_stars / damage / rank / custom)",
        placeholder="wins",
        required=True, max_length=12)
    pts_win  = TextInput(label="Points per Win  (wins mode only)",   default="3", required=True, max_length=3)
    pts_draw = TextInput(label="Points per Draw (wins mode only)",   default="1", required=True, max_length=3)
    pts_loss = TextInput(label="Points per Loss (wins mode only)",   default="0", required=True, max_length=3)
    flavor   = TextInput(
        label="Game Mode  (hide_seek / protect_layla / one_v_one / kill_race / brawl / all_random / hero_lock / magic_chess / kda_war / draft_pick / custom)",
        placeholder="hide_seek",
        required=False, max_length=15)
    def __init__(self, event, author_id):
        super().__init__(); self.event = event; self.author_id = author_id

    async def on_submit(self, interaction):
        sd = SocialEventEngine.get_social_data(self.event)
        sc = self.scoring.value.strip().lower()
        if sc not in SCORING_SYSTEMS:
            valid = " / ".join(SCORING_SYSTEMS.keys())
            return await interaction.response.send_message(
                f"❌ Valid scoring systems: `{valid}`", ephemeral=True)
        try:
            pw = int(self.pts_win.value)
            pd_v = int(self.pts_draw.value)
            pl = int(self.pts_loss.value)
        except:
            return await interaction.response.send_message("❌ Points must be whole numbers.", ephemeral=True)
        sd["scoring_system"]  = sc
        sd["points_per_win"]  = pw
        sd["points_per_draw"] = pd_v
        sd["points_per_loss"] = pl
        fl = self.flavor.value.strip().lower() if self.flavor.value else "custom"
        if fl in SOCIAL_FLAVORS:
            sd["flavor"] = fl
        save_data(squad_data)
        sys_info  = SCORING_SYSTEMS[sc]
        flav_name = SOCIAL_FLAVORS.get(fl, "⚙️ Custom")
        fmt_desc  = MLBB_EVENT_FORMATS.get(fl, "")
        embed = discord.Embed(
            title="⚙️ MLBB Event Settings Updated",
            description=(
                f"🎮 **Mode:** {flav_name}\n"
                f"{sys_info[0]} **Scoring:** {sys_info[1]}\n"
                f"*{sys_info[2]}*"
                + (f"\n\n📋 *{fmt_desc}*" if fmt_desc else "")
                + (f"\n\n**Win:** {pw}pts · **Draw:** {pd_v}pts · **Loss:** {pl}pts" if sc == "wins" else "")
            ),
            color=ROYAL_GREEN)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ── Public Social Event View ──────────────────────────────────────────

class SocialEventDetailView(View):
    """Public view for social events — leaderboard, rounds, highlights."""
    def __init__(self, event, user_id):
        super().__init__(timeout=180)
        self.event   = event
        self.user_id = user_id
        already = is_registered(event, user_id)
        is_open = event["status"] in ("open", "registration")
        self.register_btn.disabled = already or not is_open
        if already:
            self.register_btn.label = "✅ Registered"
            self.register_btn.style = discord.ButtonStyle.success
        elif not is_open:
            self.register_btn.label = f"🔒 {event['status'].upper()}"
        self.cancel_btn.disabled = not already
        sd = SocialEventEngine.get_social_data(event)
        self.leaderboard_btn.disabled = not sd.get("leaderboard")
        self.rounds_btn.disabled      = not sd.get("rounds")

    @discord.ui.button(label="📝 Register",            style=discord.ButtonStyle.success, row=0)
    async def register_btn(self, interaction, button):
        await handle_registration(interaction, self.event)

    @discord.ui.button(label="❌ Cancel Registration", style=discord.ButtonStyle.danger,   row=0)
    async def cancel_btn(self, interaction, button):
        await handle_cancel_registration(interaction, self.event)

    @discord.ui.button(label="📊 Live Leaderboard",    style=discord.ButtonStyle.primary,  row=1)
    async def leaderboard_btn(self, interaction, button):
        embed = build_social_leaderboard_embed(self.event)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📜 Round History",       style=discord.ButtonStyle.secondary, row=1)
    async def rounds_btn(self, interaction, button):
        sd = SocialEventEngine.get_social_data(self.event)
        rounds = [r for r in sd.get("rounds",[]) if r["status"] == "completed"]
        if not rounds:
            return await interaction.response.send_message("*No rounds completed yet.*", ephemeral=True)
        embed = discord.Embed(
            title=f"📜 Round History — {self.event['name']}",
            color=ROYAL_PURPLE,
            timestamp=datetime.utcnow()
        )
        for rnd in rounds[-8:]:
            results = sorted(rnd.get("results",[]), key=lambda x: -x.get("points",0))
            if results:
                top = results[0]
                lines = [f"🥇 **{top['participant']}** — {top.get('points',0)} pts"]
                for r in results[1:4]:
                    lines.append(f"• {r['participant']} — {r.get('points',0)} pts")
            else:
                lines = ["*No results*"]
            embed.add_field(name=f"⚔️ {rnd['round_name']}", value="\n".join(lines)[:512], inline=True)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="👥 Registrations",       style=discord.ButtonStyle.secondary, row=1)
    async def regs_btn(self, interaction, button):
        embed, _ = build_registrations_embed(self.event, 1, interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# =====================================================================
#                         EVENTS SYSTEM  (Complete)
# =====================================================================

# ── Constants ─────────────────────────────────────────────────────────
REGISTRATION_MODES = {
    "solo":       ("👤", "Solo",       "Each player registers individually"),
    "small_team": ("👥", "Small Team", "Team leader registers with teammates"),
    "squad_5v5":  ("👑", "Squad 5v5", "Leaders only — uses existing squads"),
}

TOURNAMENT_SYSTEMS = {
    "single_elim":   ("🏆", "Single Elimination"),
    "double_elim":   ("⚔️", "Double Elimination"),
    "round_robin":   ("🔄", "Round Robin"),
    "group_bracket": ("🎯", "Groups → Bracket"),
}

# ── Data helpers ───────────────────────────────────────────────────────

def get_all_events():
    if "events" not in squad_data:
        squad_data["events"] = []
    # Ensure each event has match_results log
    for ev in squad_data["events"]:
        ev.setdefault("match_results", [])
        ev.setdefault("champion", None)
        ev.setdefault("settings", {"bo_format": "bo1", "auto_advance": True})
        bd = ev.get("bracket_data")
        if bd:
            bd.setdefault("current_round", 0)
    return squad_data["events"]

def get_event_by_id(eid):
    for e in get_all_events():
        if e["id"] == eid:
            return e
    return None

def get_reg_name(reg):
    return (reg.get("team_name") or reg.get("player_name") or
            f"<@{reg.get('player_id','?')}>")

def is_registered(event, user_id):
    uid = str(user_id)
    for reg in event.get("registrations", []):
        if reg.get("player_id") == uid:
            return True
        if reg.get("leader_id") == uid:
            return True
        if uid in reg.get("members", []):
            return True
    return False

def find_registration(event, user_id):
    uid = str(user_id)
    for i, reg in enumerate(event.get("registrations", [])):
        if (reg.get("player_id") == uid or reg.get("leader_id") == uid
                or uid in reg.get("members", [])):
            return i, reg
    return None, None

# ── Tournament generators ──────────────────────────────────────────────

def _pad_to_power2(names):
    size = 1
    while size < len(names): size *= 2
    return names + ["BYE"] * (size - len(names))

def generate_single_elim(regs, shuffle=True):
    names = [get_reg_name(r) for r in regs]
    if shuffle: random.shuffle(names)
    names = _pad_to_power2(names)
    rounds, mid = [], [1]
    current = names
    while len(current) > 1:
        matches = []
        for i in range(0, len(current), 2):
            matches.append({"match_id": f"se_{mid[0]}", "team1": current[i],
                            "team2": current[i+1], "bracket": "winners"})
            mid[0] += 1
        rounds.append(matches)
        current = ["TBD"] * len(matches)
    return {"system": "single_elim", "rounds": rounds}

def generate_double_elim(regs, shuffle=True):
    names = [get_reg_name(r) for r in regs]
    if shuffle: random.shuffle(names)
    names = _pad_to_power2(names)
    mid = [1]

    def _make_round(teams, prefix):
        ms = []
        for i in range(0, len(teams), 2):
            ms.append({"match_id": f"{prefix}_{mid[0]}", "team1": teams[i],
                       "team2": teams[i+1], "bracket": prefix})
            mid[0] += 1
        return ms

    w_rounds = []
    current = names[:]
    while len(current) > 1:
        w_rounds.append(_make_round(current, "wb"))
        current = ["TBD"] * (len(current) // 2)

    # Losers bracket structure (placeholder TBD until matches play out)
    l_rounds = []
    lb_size = len(names) // 2
    phase = 0
    while lb_size >= 2:
        # Drop-in round (from WB losers)
        lb_size_cur = lb_size // (2 ** (phase // 2))
        if lb_size_cur < 1: break
        ms = [{"match_id": f"lb_{mid[0]+i}", "team1": "TBD", "team2": "TBD",
               "bracket": "losers"} for i in range(lb_size_cur // 2)]
        mid[0] += len(ms)
        if ms: l_rounds.append(ms)
        phase += 1
        if phase > 2 * len(w_rounds): break

    gf = {"match_id": f"gf_{mid[0]}", "team1": "WB Finalist", "team2": "LB Champion",
          "bracket": "grand_final"}
    return {"system": "double_elim", "winners": w_rounds, "losers": l_rounds,
            "grand_final": gf}

def generate_round_robin_matches(names, group_label=None, mid_start=1):
    matches, mid = [], mid_start
    prefix = f"g{group_label}_" if group_label else "rr_"
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            matches.append({"match_id": f"{prefix}{mid}", "team1": names[i],
                            "team2": names[j], "group": group_label})
            mid += 1
    return matches, mid

def generate_round_robin(regs, shuffle=True):
    names = [get_reg_name(r) for r in regs]
    if shuffle: random.shuffle(names)
    matches, _ = generate_round_robin_matches(names)
    return {"system": "round_robin", "matches": matches}

def generate_groups(regs, num_groups=4, shuffle=True):
    names = [get_reg_name(r) for r in regs]
    if shuffle: random.shuffle(names)
    num_groups = max(2, min(num_groups, len(names)))
    letters = "ABCDEFGHIJKLMNOP"
    groups = {letters[i]: [] for i in range(num_groups)}
    for i, name in enumerate(names):
        groups[letters[i % num_groups]].append(name)
    all_matches, mid = [], 1
    for gname, gteams in groups.items():
        ms, mid = generate_round_robin_matches(gteams, group_label=gname, mid_start=mid)
        all_matches.extend(ms)
    return {"system": "groups", "groups": groups, "matches": all_matches,
            "bracket": None, "bracket_stage": "groups"}

def generate_group_bracket(regs, num_groups=4, shuffle=True):
    data = generate_groups(regs, num_groups, shuffle)
    data["system"] = "group_bracket"
    return data

def advance_groups_to_bracket(bracket_data, advances_per_group=2):
    """Take top N from each group (by insertion order) and generate a bracket."""
    groups = bracket_data.get("groups", {})
    qualifiers = []
    for gname, gteams in sorted(groups.items()):
        qualifiers.extend(gteams[:advances_per_group])
    se = generate_single_elim([{"player_name": q} for q in qualifiers], shuffle=False)
    bracket_data["bracket"] = se
    bracket_data["bracket_stage"] = "bracket"
    return bracket_data

# ── Schedule helpers ────────────────────────────────────────────────────

def get_all_bracket_matches(event):
    """Return every match from bracket_data as a flat list with display info."""
    bd = event.get("bracket_data")
    if not bd: return []
    system = bd.get("system", "")
    matches = []

    if system == "single_elim":
        for ri, rnd in enumerate(bd.get("rounds", [])):
            for m in rnd:
                m2 = dict(m); m2["round_display"] = f"Round {ri+1}"; matches.append(m2)

    elif system == "double_elim":
        for ri, rnd in enumerate(bd.get("winners", [])):
            for m in rnd:
                m2 = dict(m); m2["round_display"] = f"WB Round {ri+1}"; matches.append(m2)
        for ri, rnd in enumerate(bd.get("losers", [])):
            for m in rnd:
                m2 = dict(m); m2["round_display"] = f"LB Round {ri+1}"; matches.append(m2)
        gf = bd.get("grand_final")
        if gf:
            m2 = dict(gf); m2["round_display"] = "Grand Final"; matches.append(m2)

    elif system in ("round_robin", "groups", "group_bracket"):
        for m in bd.get("matches", []):
            m2 = dict(m)
            m2["round_display"] = f"Group {m.get('group','?')}" if m.get("group") else "Match"
            matches.append(m2)
        bracket = bd.get("bracket")
        if bracket:
            for ri, rnd in enumerate(bracket.get("rounds", [])):
                for m in rnd:
                    m2 = dict(m); m2["round_display"] = f"Bracket R{ri+1}"; matches.append(m2)

    elif system in ("random_draw", "random_teams"):
        for i, m in enumerate(bd.get("matches", [])):
            m2 = dict(m)
            m2["round_display"] = f"Match {i+1}"
            matches.append(m2)

    # random_pick and gather_group have no schedulable matches
    elif system in ("random_pick", "gather_group"):
        pass

    return matches


def generate_random_draw(regs, shuffle=True):
    """Randomly pair all registrations — no bracket, just who plays who."""
    names = [get_reg_name(r) for r in regs]
    if shuffle: random.shuffle(names)
    matches = []
    for i, mid in enumerate(range(0, len(names) - 1, 2), start=1):
        matches.append({
            "match_id": f"rd_{i}",
            "team1": names[mid],
            "team2": names[mid + 1]
        })
    if len(names) % 2 != 0:
        matches.append({
            "match_id": f"rd_{len(matches)+1}",
            "team1": names[-1],
            "team2": "BYE"
        })
    return {"system": "random_draw", "matches": matches}


def generate_random_teams_from_solo(regs, team_size=2, shuffle=True):
    """Form random teams from solo registrants, then pair the teams."""
    names = [get_reg_name(r) for r in regs]
    if shuffle: random.shuffle(names)
    # Split into teams
    teams = []
    for i in range(0, len(names), team_size):
        chunk = names[i:i + team_size]
        teams.append(chunk)
    # Name the teams
    team_labels = [f"Team {i+1} ({' & '.join(t)})" for i, t in enumerate(teams)]
    # Pair teams up for matches
    matches = []
    for i, mid_i in enumerate(range(0, len(team_labels) - 1, 2), start=1):
        matches.append({
            "match_id": f"rt_{i}",
            "team1": team_labels[mid_i],
            "team2": team_labels[mid_i + 1]
        })
    if len(team_labels) % 2 != 0:
        matches.append({
            "match_id": f"rt_{len(matches)+1}",
            "team1": team_labels[-1],
            "team2": "BYE"
        })
    return {
        "system": "random_teams",
        "teams": [{"label": label, "members": members}
                  for label, members in zip(team_labels, teams)],
        "matches": matches
    }


def generate_random_pick(regs, shuffle=True):
    """Randomly select ONE player or team from all registrations (lottery)."""
    entries = [get_reg_name(r) for r in regs]
    if shuffle: random.shuffle(entries)
    winner = random.choice(entries)
    others = [e for e in entries if e != winner]
    return {
        "system": "random_pick",
        "winner": winner,
        "all_entries": entries,
        "others": others,
    }


def generate_gather_group(regs, size, shuffle=True):
    """Randomly pick exactly `size` participants and group them together."""
    all_names = [get_reg_name(r) for r in regs]
    if shuffle: random.shuffle(all_names)
    selected  = all_names[:size]
    remaining = all_names[size:]
    return {
        "system": "gather_group",
        "size": size,
        "selected": selected,
        "remaining": remaining,
    }

def get_unscheduled_matches(event):
    scheduled_ids = {s["match_id"] for s in event.get("schedule", [])}
    return [m for m in get_all_bracket_matches(event)
            if m["match_id"] not in scheduled_ids
            and "TBD" not in [m.get("team1",""), m.get("team2","")]
            and m.get("team2") != "BYE"   # BYE matches auto-advance, no scheduling needed
            and m.get("team1") != "BYE"]

# ── Embed builders ─────────────────────────────────────────────────────

def build_event_list_embed(events, page, total_pages):
    status_icons = {"open": "🟢", "ongoing": "⚔️", "closed": "🔴"}
    type_icons   = {"tournament": "🏆", "fun": "🎉", "social": "🎉"}
    mode_icons   = {"solo": "👤", "small_team": "👥", "squad_5v5": "👑"}
    embed = discord.Embed(title="🎪 Events — Majestic Dominion",
        description="*Register for events and compete for the Crown's glory!*",
        color=ROYAL_GOLD)
    if not events:
        embed.description = "*No upcoming events right now. Stay tuned!*"
    for ev in events:
        si = status_icons.get(ev["status"], "⚪")
        ti = type_icons.get(ev["type"], "🎪")
        mi = mode_icons.get(ev.get("registration_mode", "solo"), "")
        fmt = ev.get("format", "?")
        rc = len(ev.get("registrations", []))
        mx_str = f"/{ev['max_entries']}" if ev.get("max_entries") else ""
        desc = ev.get("description","")[:80] + ("..." if len(ev.get("description","")) > 80 else "")
        pp = f" | 💰 {ev['prize_pool']}" if ev.get("prize_pool") else ""
        val = (f"{ti} **{ev['type'].title()}** | {mi} **{fmt}**{pp}\n"
               f"📅 {ev['date']}\n"
               f"👥 {rc}{mx_str} registered | {si} **{ev['status'].upper()}**\n"
               f"*{desc}*")
        embed.add_field(name=f"🎪 {ev['name']}", value=val, inline=False)
    embed.set_footer(text=f"⚜️ Majestic Dominion | Page {page}/{total_pages}")
    apply_branding(embed, thumbnail=True)
    return embed

def build_event_detail_embed(event, guild=None):
    status_colors = {"open": ROYAL_GREEN, "ongoing": ROYAL_PURPLE, "closed": 0x555555}
    status_labels = {"open": "🟢 OPEN — Registration Active", "ongoing": "⚔️ ONGOING", "closed": "🔴 CLOSED"}
    type_labels   = {"tournament": "🏆 Tournament", "fun": "🎉 Social Event", "social": "🎉 Social Event"}
    # For social events, pull flavor from social_data
    if event.get("type") == "fun":
        sd = event.get("social_data", {})
        flavor_key = sd.get("flavor", "custom")
        flavor_label = SOCIAL_FLAVORS.get(flavor_key, "⚙️ Custom")
        scoring_key  = sd.get("scoring_system", "points")
        scoring_label = SCORING_SYSTEMS.get(scoring_key, ("💎","Points",""))[1]
    mode_labels   = {"solo": "👤 Solo", "small_team": "👥 Small Team", "squad_5v5": "👑 Squad 5v5"}
    reg_count = len(event.get("registrations", []))
    mx_str = f" / {event['max_entries']} max" if event.get("max_entries") else ""
    system = event.get("tournament_system")   # None = no bracket system
    sys_label = TOURNAMENT_SYSTEMS.get(system, ("",""))[1] if system else "—"
    embed = discord.Embed(
        title=f"🎪 {event['name']}",
        description=event.get("description",""),
        color=status_colors.get(event["status"], ROYAL_GOLD))
    if event.get("event_image"):
        embed.set_image(url=event["event_image"])
    embed.add_field(name="📋 Type",    value=type_labels.get(event["type"], event["type"].title()), inline=True)
    embed.add_field(name="⚔️ Format",  value=event.get("format","?"),                               inline=True)
    embed.add_field(name="📊 Status",  value=status_labels.get(event["status"], event["status"]),   inline=True)
    embed.add_field(name="📅 Date",    value=event["date"],                                          inline=True)
    embed.add_field(name="👥 Registered", value=f"{reg_count}{mx_str}",                             inline=True)
    embed.add_field(name="📝 Registration", value=mode_labels.get(event.get("registration_mode","solo"), "?"), inline=True)
    if event["type"] == "tournament":
        rand_parts = []
        if event.get("randomize_groups"):   rand_parts.append("Groups")
        if event.get("randomize_brackets"): rand_parts.append("Bracket")
        embed.add_field(name="🏆 System",  value=sys_label, inline=True)
        embed.add_field(name="🎲 Randomize", value=" & ".join(rand_parts) or "Off", inline=True)
    if event.get("prize_pool"):
        embed.add_field(name="💰 Prize Pool", value=event["prize_pool"], inline=False)
    if event.get("rules"):
        embed.add_field(name="📜 Rules", value=event["rules"][:1024], inline=False)
    rm = event.get("registration_mode", "solo")
    if rm == "squad_5v5":
        embed.add_field(name="⚠️ Registration",
            value="*This is a **Squad 5v5** event — only **Kingdom Leaders** may register their squad.*",
            inline=False)
    elif rm == "small_team":
        ts = event.get("team_size", 2)
        embed.add_field(name="ℹ️ Registration",
            value=f"*Team of **{ts}** — leader registers and adds **{ts-1}** teammate(s).*",
            inline=False)
    embed.set_footer(text=f"⚜️ Event ID: {event['id']} | Majestic Dominion")
    apply_branding(embed, thumbnail=True)
    return embed

def build_registrations_embed(event, page, guild):
    regs = event.get("registrations", [])
    per_page = 8
    total_pages = max(1, (len(regs) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    chunk = regs[(page-1)*per_page : page*per_page]
    embed = discord.Embed(title=f"📋 Registrations — {event['name']}",
        description=f"**{len(regs)}** registered" + (f" / {event['max_entries']} max" if event.get("max_entries") else ""),
        color=ROYAL_PURPLE)
    if not regs:
        embed.description = "*No registrations yet.*"
        apply_branding(embed, thumbnail=True)
        return embed, 1
    rm = event.get("registration_mode","solo")
    for i, reg in enumerate(chunk, start=(page-1)*per_page+1):
        if rm == "solo":
            pid = reg.get("player_id")
            m = guild.get_member(int(pid)) if pid and guild else None
            name = m.mention if m else reg.get("player_name", pid)
            embed.add_field(name=f"#{i}", value=f"{name}\n📅 {reg.get('registered_at','')[:10]}", inline=True)
        else:
            lid = reg.get("leader_id")
            lm = guild.get_member(int(lid)) if lid and guild else None
            leader_name = lm.display_name if lm else reg.get("team_name", str(lid))
            members = reg.get("members", [])
            m_names = []
            for mid in members:
                mm = guild.get_member(int(mid)) if guild else None
                m_names.append(mm.display_name if mm else f"<@{mid}>")
            val = (f"👑 {leader_name}" +
                   (f"\n{', '.join(m_names)}" if m_names else "") +
                   f"\n📅 {reg.get('registered_at','')[:10]}")
            val = val[:1024]
            tname = reg.get("team_name", f"Team {i}")
            embed.add_field(name=f"#{i} — {tname}", value=val, inline=False)
    embed.set_footer(text=f"⚜️ Page {page}/{total_pages} | Majestic Dominion")
    apply_branding(embed, thumbnail=True)
    return embed, total_pages

def build_event_manager_embed():
    events = get_all_events()
    open_ev = sum(1 for e in events if e["status"] == "open")
    ongoing  = sum(1 for e in events if e["status"] == "ongoing")
    closed   = sum(1 for e in events if e["status"] == "closed")
    embed = discord.Embed(title="🎪 Event Manager",
        description=f"**{open_ev}** open · **{ongoing}** ongoing · **{closed}** closed",
        color=ROYAL_GOLD)
    for ev in (events[-8:] if events else []):
        si = {"open":"🟢","ongoing":"⚔️","closed":"🔴"}.get(ev["status"],"⚪")
        rc = len(ev.get("registrations",[]))
        fmt = ev.get("format","?")
        bd_icon = "🏆" if ev.get("bracket_data") else ""
        embed.add_field(name=f"{si} {ev['name']} {bd_icon}",
            value=f"{ev['type'].title()} | {fmt} | 👥 {rc} | 📅 {ev['date']}", inline=False)
    if not events:
        embed.add_field(name="📭 No Events", value="Create your first event!", inline=False)
    embed.set_footer(text="⚜️ Majestic Dominion | Event Manager")
    apply_branding(embed, thumbnail=True)
    return embed

def build_bracket_embed(event):
    bd = event.get("bracket_data")
    if not bd:
        embed = discord.Embed(title="🏆 No Bracket Generated",
            description="Use the Randomize function to generate a bracket.", color=ROYAL_RED)
        apply_branding(embed, thumbnail=True)
        return embed
    system = bd.get("system","?")
    sys_labels = {
        "single_elim":   "Single Elimination",
        "double_elim":   "Double Elimination",
        "round_robin":   "Round Robin",
        "groups":        "Group Stage",
        "group_bracket": "Group Stage → Bracket",
        "random_draw":   "Random Draw",
        "random_teams":  "Random Teams",
        "random_pick":   "Random Pick",
        "gather_group":  "Random Group",
    }
    draw_desc = {
        "random_draw":  "*Random draw — who plays who. No bracket structure.*",
        "random_teams": "*Random teams formed from registrants. Pairings shown below.*",
        "random_pick":  "*One participant randomly selected from all registrations.*",
        "gather_group": "*A random group of participants selected from registrations.*",
    }
    embed = discord.Embed(
        title=f"{'🎲' if system in ('random_draw','random_teams','random_pick','gather_group') else '🏆'} {sys_labels.get(system,'Draw')} — {event['name']}",
        description=draw_desc.get(system, "*Generated bracket — may the best sovereign prevail!*"),
        color=ROYAL_GOLD)

    if system == "single_elim":
        round_names = ["Grand Final","Semi-Finals","Quarter-Finals",
                       "Round of 16","Round of 32","Round of 64","Round of 128"]
        rounds = bd.get("rounds",[])
        total  = len(rounds)
        per_field = 15  # max matches per embed field (keeps chars well under 1024)
        for ri, rnd in enumerate(rounds):
            rn_idx = total - 1 - ri
            rn = round_names[rn_idx] if rn_idx < len(round_names) else f"Round {ri+1}"
            lines = [f"`{m['match_id']}` **{m['team1']}** vs **{m['team2']}**" for m in rnd]
            # Split into sub-fields if round has many matches
            for ci in range(0, len(lines), per_field):
                chunk = "\n".join(lines[ci:ci+per_field])
                part_label = f" ({ci//per_field + 1})" if len(lines) > per_field else ""
                embed.add_field(name=f"⚔️ {rn}{part_label}", value=chunk, inline=False)
                if len(embed.fields) >= 24: break
            if len(embed.fields) >= 24: break

    elif system == "double_elim":
        per_field = 15
        for ri, rnd in enumerate(bd.get("winners",[])):
            lines = [f"`{m['match_id']}` {m['team1']} vs {m['team2']}" for m in rnd]
            for ci in range(0, len(lines), per_field):
                chunk = "\n".join(lines[ci:ci+per_field])
                part_label = f" ({ci//per_field + 1})" if len(lines) > per_field else ""
                embed.add_field(name=f"🏆 WB Round {ri+1}{part_label}", value=chunk, inline=False)
                if len(embed.fields) >= 22: break
            if len(embed.fields) >= 22: break
        for ri, rnd in enumerate(bd.get("losers",[])):
            lines = [f"`{m['match_id']}` {m['team1']} vs {m['team2']}" for m in rnd]
            for ci in range(0, len(lines), per_field):
                chunk = "\n".join(lines[ci:ci+per_field])
                part_label = f" ({ci//per_field + 1})" if len(lines) > per_field else ""
                embed.add_field(name=f"💀 LB Round {ri+1}{part_label}", value=chunk, inline=False)
                if len(embed.fields) >= 24: break
            if len(embed.fields) >= 24: break
        gf = bd.get("grand_final")
        if gf:
            embed.add_field(name="🎯 Grand Final",
                value=f"`{gf['match_id']}` **{gf['team1']}** vs **{gf['team2']}**", inline=False)

    elif system in ("round_robin",):
        matches = bd.get("matches",[])
        lines = [f"`{m['match_id']}` **{m['team1']}** vs **{m['team2']}**" for m in matches]
        # split into chunks of 10
        for ci in range(0, len(lines), 10):
            chunk = "\n".join(lines[ci:ci+10])[:1024]
            embed.add_field(name=f"⚔️ Matches {ci+1}–{min(ci+10,len(lines))}", value=chunk, inline=False)
            if len(embed.fields) >= 20: break

    elif system in ("groups","group_bracket"):
        groups = bd.get("groups",{})
        for gname, gteams in sorted(groups.items()):
            embed.add_field(name=f"🛡️ Group {gname}",
                value="\n".join(f"• {t}" for t in gteams)[:1024], inline=True)
            if len(embed.fields) >= 20: break
        bracket = bd.get("bracket")
        if bracket:
            embed.add_field(name="━━━━ Knockout Stage ━━━━", value="*Group stage complete — bracket below*", inline=False)
            rounds = bracket.get("rounds",[])
            for ri, rnd in enumerate(rounds):
                lines = [f"`{m['match_id']}` {m['team1']} vs {m['team2']}" for m in rnd]
                embed.add_field(name=f"⚔️ Bracket R{ri+1}", value="\n".join(lines)[:1024], inline=False)

    elif system == "random_draw":
        matches = bd.get("matches", [])
        real = [m for m in matches if m.get("team2") != "BYE"]
        byes = [m for m in matches if m.get("team2") == "BYE"]
        lines = [f"`{m['match_id']}` ⚔️ **{m['team1']}** vs **{m['team2']}**" for m in real]
        for ci in range(0, len(lines), 10):
            chunk = "\n".join(lines[ci:ci+10])[:1024]
            embed.add_field(name=f"🎲 Matches {ci+1}–{min(ci+10,len(lines))}", value=chunk, inline=False)
            if len(embed.fields) >= 20: break
        if byes:
            embed.add_field(name="🚪 BYE", value="\n".join(m["team1"] for m in byes), inline=False)

    elif system == "random_teams":
        teams = bd.get("teams", [])
        team_lines = [f"🛡️ **{t['label'].split('(')[0].strip()}** — {' · '.join(t['members'])}" for t in teams]
        for ci in range(0, len(team_lines), 5):
            chunk = "\n".join(team_lines[ci:ci+5])[:1024]
            embed.add_field(name=f"👥 Teams {ci+1}–{min(ci+5,len(team_lines))}", value=chunk, inline=False)
            if len(embed.fields) >= 10: break
        matches = bd.get("matches", [])
        if matches:
            real = [m for m in matches if m.get("team2") != "BYE"]
            lines = [f"`{m['match_id']}` {m['team1'].split('(')[0].strip()} vs {m['team2'].split('(')[0].strip()}" for m in real]
            embed.add_field(name="━━━━ Match Pairings ━━━━",
                value="\n".join(lines)[:1024] or "—", inline=False)

    elif system == "random_pick":
        winner = bd.get("winner", "?")
        others = bd.get("others", [])
        embed.add_field(name="🎉 Selected!", value=f"### **{winner}**", inline=False)
        if others:
            embed.add_field(name=f"📋 All Entries ({len(bd.get('all_entries',[]))} total)",
                value="\n".join(f"• {e}" for e in others[:20])[:1024]
                      + (f"\n*...and {len(others)-20} more*" if len(others) > 20 else ""),
                inline=False)

    elif system == "gather_group":
        selected  = bd.get("selected", [])
        remaining = bd.get("remaining", [])
        size      = bd.get("size", len(selected))
        embed.add_field(
            name=f"👥 Selected Group ({size} participants)",
            value="\n".join(f"• **{m}**" for m in selected)[:1024] or "—",
            inline=False)
        if remaining:
            embed.add_field(
                name=f"📋 Not Selected ({len(remaining)})",
                value="\n".join(f"• {m}" for m in remaining[:20])[:1024]
                      + (f"\n*...and {len(remaining)-20} more*" if len(remaining) > 20 else ""),
                inline=False)

    embed.set_footer(text=f"⚜️ Event ID: {event['id']} | Use /events to register")
    apply_branding(embed, thumbnail=True)
    return embed

def build_schedule_embed(event, page=1):
    schedule = event.get("schedule",[])
    per_page = 8
    total_pages = max(1, (len(schedule)+per_page-1)//per_page)
    page = max(1, min(page, total_pages))
    chunk = schedule[(page-1)*per_page : page*per_page]
    embed = discord.Embed(title=f"📅 Match Schedule — {event['name']}",
        description=f"**{len(schedule)}** matches scheduled",
        color=ROYAL_PURPLE)
    if not schedule:
        embed.description = "*No matches scheduled yet. Generate bracket then use Schedule Matches.*"
    for s in chunk:
        embed.add_field(
            name=f"⚔️ {s['team1']} vs {s['team2']}",
            value=f"📅 **{s.get('date','TBD')}**\n🏷️ {s.get('round_display','')}\n`{s['match_id']}`",
            inline=False)
    embed.set_footer(text=f"⚜️ Page {page}/{total_pages} | Majestic Dominion")
    apply_branding(embed, thumbnail=True)
    return embed, total_pages

# ── Public /events views ───────────────────────────────────────────────

class EventsListView(View):
    def __init__(self, all_events, page=0, author_id=None):
        super().__init__(timeout=180)
        visible = [e for e in all_events if e["status"] != "closed"] or all_events
        self.all_events = visible
        self.page = page
        self.author_id = author_id
        self.per_page = 4
        self.total_pages = max(1, (len(self.all_events)+self.per_page-1)//self.per_page)
        self._refresh()

    def _page_events(self):
        s = self.page * self.per_page
        return self.all_events[s:s+self.per_page]

    def _refresh(self):
        for item in list(self.children):
            if isinstance(item, Select):
                self.remove_item(item)
        self.prev_btn.disabled = self.page <= 0
        self.next_btn.disabled = self.page >= self.total_pages-1
        evs = self._page_events()
        if evs:
            opts = [discord.SelectOption(label=ev["name"][:100], value=ev["id"], emoji="🎪",
                description=f"{ev['type'].title()} · {ev['status'].upper()} · {ev['date'][:30]}")
                for ev in evs]
            sel = Select(placeholder="🎪 Select an event to view details...", options=opts, row=0)
            sel.callback = self._on_select
            self.add_item(sel)

    async def _on_select(self, interaction):
        eid = interaction.data["values"][0]
        event = get_event_by_id(eid)
        if not event:
            return await interaction.response.send_message("❌ Event not found.", ephemeral=True)
        embed = build_event_detail_embed(event, interaction.guild)
        if event.get("type") == "fun":
            view = SocialEventDetailView(event, interaction.user.id)
        else:
            view = EventDetailViewV2(event, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary, row=1)
    async def prev_btn(self, interaction, button):
        self.page = max(0, self.page-1); self._refresh()
        await interaction.response.edit_message(
            embed=build_event_list_embed(self._page_events(), self.page+1, self.total_pages), view=self)

    @discord.ui.button(label="▶ Next", style=discord.ButtonStyle.secondary, row=1)
    async def next_btn(self, interaction, button):
        self.page = min(self.total_pages-1, self.page+1); self._refresh()
        await interaction.response.edit_message(
            embed=build_event_list_embed(self._page_events(), self.page+1, self.total_pages), view=self)


class EventDetailView(View):
    def __init__(self, event, user_id):
        super().__init__(timeout=180)
        self.event = event
        self.user_id = user_id
        already = is_registered(event, user_id)
        is_open = event["status"] == "open"
        self.register_btn.disabled = already or not is_open
        if already:
            self.register_btn.label = "✅ Registered"
            self.register_btn.style = discord.ButtonStyle.success
        elif not is_open:
            self.register_btn.label = f"🔒 {event['status'].upper()}"
        # Show cancel only if registered
        self.cancel_btn.disabled = not already

        # Show bracket/schedule buttons if data exists
        self.bracket_btn.disabled = not event.get("bracket_data")
        self.schedule_btn.disabled = not event.get("schedule")

    @discord.ui.button(label="📝 Register", style=discord.ButtonStyle.success, row=0)
    async def register_btn(self, interaction, button):
        await handle_registration(interaction, self.event)

    @discord.ui.button(label="❌ Cancel Registration", style=discord.ButtonStyle.danger, row=0)
    async def cancel_btn(self, interaction, button):
        await handle_cancel_registration(interaction, self.event)

    @discord.ui.button(label="🏆 Bracket / Groups", style=discord.ButtonStyle.secondary, row=1)
    async def bracket_btn(self, interaction, button):
        embed = build_bracket_embed(self.event)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📅 Schedule", style=discord.ButtonStyle.secondary, row=1)
    async def schedule_btn(self, interaction, button):
        embed, _ = build_schedule_embed(self.event)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="👥 Registrations", style=discord.ButtonStyle.secondary, row=1)
    async def regs_btn(self, interaction, button):
        embed, _ = build_registrations_embed(self.event, 1, interaction.guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ── Registration handlers ──────────────────────────────────────────────

async def handle_registration(interaction, event):
    if event["status"] != "open":
        return await interaction.response.send_message("❌ Event is not open for registration.", ephemeral=True)
    if is_registered(event, interaction.user.id):
        return await interaction.response.send_message("❌ Already registered.", ephemeral=True)
    if event.get("max_entries") and len(event.get("registrations",[])) >= event["max_entries"]:
        return await interaction.response.send_message("❌ Event is full.", ephemeral=True)

    rm = event.get("registration_mode","solo")
    if rm == "solo":
        await interaction.response.send_modal(SoloRegisterModal(event))
    elif rm == "small_team":
        await interaction.response.send_modal(SmallTeamRegisterModal(event))
    elif rm == "squad_5v5":
        await handle_squad_5v5_registration(interaction, event)
    else:
        await interaction.response.send_message("❌ Unknown registration mode.", ephemeral=True)

async def handle_cancel_registration(interaction, event):
    idx, reg = find_registration(event, interaction.user.id)
    if idx is None:
        return await interaction.response.send_message("❌ You are not registered.", ephemeral=True)
    # For team/squad — only leader can cancel
    rm = event.get("registration_mode","solo")
    if rm != "solo" and reg.get("leader_id") != str(interaction.user.id):
        return await interaction.response.send_message(
            "❌ Only the **team leader** who registered can cancel.", ephemeral=True)
    event["registrations"].pop(idx)
    save_data(squad_data)
    embed = discord.Embed(title="✅ Registration Cancelled",
        description=f"You have been removed from **{event['name']}**.",
        color=ROYAL_RED)
    apply_branding(embed, thumbnail=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_action(interaction.guild, "❌ Registration Cancelled",
        f"{interaction.user.mention} cancelled registration for **{event['name']}**")


class SoloRegisterModal(Modal, title="📝 Confirm Solo Registration"):
    confirm = TextInput(label='Type "CONFIRM" to register', placeholder="CONFIRM", required=True, max_length=10)
    def __init__(self, event):
        super().__init__(); self.event = event

    async def on_submit(self, interaction):
        if self.confirm.value.strip().upper() != "CONFIRM":
            return await interaction.response.send_message("❌ Cancelled.", ephemeral=True)
        if is_registered(self.event, interaction.user.id):
            return await interaction.response.send_message("❌ Already registered.", ephemeral=True)
        self.event["registrations"].append({
            "player_id": str(interaction.user.id),
            "player_name": interaction.user.display_name,
            "registered_at": datetime.utcnow().isoformat()
        })
        save_data(squad_data)
        embed = discord.Embed(title="✅ You're Registered!",
            description=f"You have joined **{self.event['name']}**!\n📅 {self.event['date']}",
            color=ROYAL_GREEN)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(interaction.guild, "📝 Solo Registered",
            f"{interaction.user.mention} registered for **{self.event['name']}**")


class SmallTeamRegisterModal(Modal, title="📝 Team Registration"):
    team_name  = TextInput(label="Team Name", required=True, max_length=50)
    members_raw = TextInput(label="Teammates (user IDs, comma-separated)",
        placeholder="123456789, 987654321 — or leave blank",
        style=discord.TextStyle.paragraph, required=False, max_length=500)

    def __init__(self, event):
        super().__init__()
        self.event = event
        ts = event.get("team_size", 2)
        self.members_raw.label = f"Teammates — need {ts - 1} more (user IDs or @mentions)"

    async def on_submit(self, interaction):
        ts = self.event.get("team_size", 2)
        tname = self.team_name.value.strip()
        member_ids = [str(interaction.user.id)]
        raw = self.members_raw.value.strip() if self.members_raw.value else ""
        if raw:
            for part in raw.replace(",", " ").split():
                p = part.strip().strip("<@!>").strip()
                if p.isdigit() and p not in member_ids:
                    member_ids.append(p)
        for mid in member_ids:
            if is_registered(self.event, mid):
                m = interaction.guild.get_member(int(mid))
                return await interaction.response.send_message(
                    f"❌ **{m.display_name if m else mid}** is already registered.", ephemeral=True)
        self.event["registrations"].append({
            "team_name": tname, "leader_id": str(interaction.user.id),
            "members": member_ids[1:], "registered_at": datetime.utcnow().isoformat()
        })
        save_data(squad_data)
        filled = len(member_ids)
        desc = f"**{tname}** joined **{self.event['name']}**!\n📅 {self.event['date']}\n👥 {filled}/{ts} members"
        if filled < ts:
            desc += f"\n⚠️ *Your team needs {ts - filled} more player(s). A mod can update your roster.*"
        embed = discord.Embed(title="✅ Team Registered!", description=desc, color=ROYAL_GREEN)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(interaction.guild, "📝 Team Registered",
            f"{interaction.user.mention} registered team **{tname}** for **{self.event['name']}**")


async def handle_squad_5v5_registration(interaction, event):
    uid = str(interaction.user.id)
    if not is_leader(interaction.user):
        return await interaction.response.send_message(
            "❌ Only **Kingdom Leaders** can register for 5v5 events.", ephemeral=True)
    sr, tag = get_member_squad(interaction.user, interaction.guild)
    if not sr:
        return await interaction.response.send_message("❌ You must be in a kingdom.", ephemeral=True)
    embed = discord.Embed(title="👑 5v5 Kingdom Registration",
        description=f"Register **{tag} {sr.name}** for **{event['name']}**?\nYour **main roster** will be used automatically.",
        color=ROYAL_GOLD)
    apply_branding(embed, thumbnail=True)
    await interaction.response.send_message(embed=embed,
        view=SquadRegisterConfirmView(event, sr.name, tag, interaction.user.id), ephemeral=True)


class SquadRegisterConfirmView(View):
    def __init__(self, event, sq_name, tag, author_id):
        super().__init__(timeout=60)
        self.event = event; self.sq_name = sq_name
        self.tag = tag; self.author_id = author_id

    @discord.ui.button(label="✅ Confirm Registration", style=discord.ButtonStyle.success)
    async def confirm(self, interaction, button):
        if interaction.user.id != self.author_id: return
        for reg in self.event.get("registrations",[]):
            if reg.get("team_name") == self.sq_name:
                return await interaction.response.edit_message(
                    content=f"❌ **{self.sq_name}** is already registered.", embed=None, view=None)
        sq_info = squad_data["squads"].get(self.sq_name, {})
        mains = [str(m) for m in sq_info.get("main_roster", [])]
        leader_id = str(interaction.user.id)
        self.event["registrations"].append({
            "team_name": self.sq_name, "leader_id": leader_id,
            "members": [m for m in mains if m != leader_id],
            "squad_ref": self.sq_name, "registered_at": datetime.utcnow().isoformat()
        })
        save_data(squad_data)
        embed = discord.Embed(title="✅ Kingdom Registered!",
            description=f"{self.tag} **{self.sq_name}** entered **{self.event['name']}**!\n📅 {self.event['date']}",
            color=ROYAL_GREEN)
        apply_branding(embed, thumbnail=True)
        await interaction.response.edit_message(embed=embed, view=None)
        pub = discord.Embed(title="⚔️ A KINGDOM ENTERS THE ARENA!",
            description=f"{self.tag} **{self.sq_name}** registered for **{self.event['name']}**!\n*The battlefield grows more crowded...*",
            color=ROYAL_GOLD)
        await announce_event(interaction.guild, pub)
        await log_action(interaction.guild, "📝 5v5 Registered",
            f"{interaction.user.mention} registered {self.tag} **{self.sq_name}** for **{self.event['name']}**")

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        if interaction.user.id != self.author_id: return
        await interaction.response.edit_message(content="❌ Cancelled.", embed=None, view=None)


# ── Mod Event Manager views ────────────────────────────────────────────

class EventManagerView(View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Create", emoji="➕", style=discord.ButtonStyle.success, row=0)
    async def create_btn(self, interaction, button):
        await interaction.response.send_modal(CreateEventModal())

    @discord.ui.button(label="Edit", emoji="✏️", style=discord.ButtonStyle.primary, row=0)
    async def edit_btn(self, interaction, button):
        evs = get_all_events()
        if not evs:
            return await interaction.response.send_message("❌ No events to edit.", ephemeral=True)
        embed = discord.Embed(title="✏️ Edit Event", description="Select:", color=ROYAL_GOLD)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectViewV2(evs, "edit", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="Delete", emoji="🗑️", style=discord.ButtonStyle.danger, row=0)
    async def delete_btn(self, interaction, button):
        evs = get_all_events()
        if not evs:
            return await interaction.response.send_message("❌ No events.", ephemeral=True)
        embed = discord.Embed(title="🗑️ Delete Event", description="Select:", color=ROYAL_RED)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectViewV2(evs, "delete", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="Registrations", emoji="📋", style=discord.ButtonStyle.secondary, row=1)
    async def regs_btn(self, interaction, button):
        evs = get_all_events()
        if not evs:
            return await interaction.response.send_message("❌ No events.", ephemeral=True)
        embed = discord.Embed(title="📋 Registrations", description="Select:", color=ROYAL_PURPLE)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectViewV2(evs, "regs", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="Start", emoji="▶️", style=discord.ButtonStyle.success, row=1)
    async def start_btn(self, interaction, button):
        evs = [e for e in get_all_events() if e["status"] == "open"]
        if not evs:
            return await interaction.response.send_message("❌ No open events.", ephemeral=True)
        embed = discord.Embed(title="▶️ Start Event", description="Select:", color=ROYAL_GREEN)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectViewV2(evs, "start", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="Close", emoji="⏹️", style=discord.ButtonStyle.danger, row=1)
    async def close_btn(self, interaction, button):
        evs = [e for e in get_all_events() if e["status"] == "ongoing"]
        if not evs:
            return await interaction.response.send_message("❌ No ongoing events.", ephemeral=True)
        embed = discord.Embed(title="⏹️ Close Event", description="Select:", color=ROYAL_RED)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectViewV2(evs, "close", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="Randomize", emoji="🎲", style=discord.ButtonStyle.primary, row=2)
    async def random_btn(self, interaction, button):
        evs = get_all_events()
        if not evs:
            return await interaction.response.send_message("❌ No events.", ephemeral=True)
        embed = discord.Embed(title="🎲 Randomize", description="Select event:", color=ROYAL_PURPLE)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectViewV2(evs, "randomize", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="Schedule Matches", emoji="📅", style=discord.ButtonStyle.secondary, row=2)
    async def schedule_btn(self, interaction, button):
        evs = [e for e in get_all_events() if e.get("bracket_data")]
        if not evs:
            return await interaction.response.send_message(
                "❌ No events with generated brackets. Randomize first.", ephemeral=True)
        embed = discord.Embed(title="📅 Schedule Matches", description="Select event:", color=ROYAL_GOLD)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=EventActionSelectViewV2(evs, "schedule", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=2)
    async def refresh_btn(self, interaction, button):
        await interaction.response.edit_message(embed=build_event_manager_embed(), view=EventManagerView())


class EventActionSelectView(View):
    def __init__(self, events, action, author_id):
        super().__init__(timeout=180)
        self.action = action; self.author_id = author_id
        opts = [discord.SelectOption(label=ev["name"][:100], value=ev["id"], emoji="🎪",
            description=f"{ev['type'].title()} · {ev['status']} · {len(ev.get('registrations',[]))} reg'd")
            for ev in events[:25]]
        sel = Select(placeholder="🎪 Select an event...", options=opts)
        sel.callback = self._selected
        self.add_item(sel)

    async def _selected(self, interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Not your session.", ephemeral=True)
        eid = interaction.data["values"][0]
        event = get_event_by_id(eid)
        if not event:
            return await interaction.response.send_message("❌ Event not found.", ephemeral=True)

        if self.action == "edit":
            await interaction.response.send_modal(EditEventModal(event))

        elif self.action == "delete":
            embed = discord.Embed(title=f"🗑️ Delete '{event['name']}'?",
                description=f"Permanently deletes the event and **{len(event.get('registrations',[]))}** registrations.",
                color=ROYAL_RED)
            apply_branding(embed, thumbnail=True)
            await interaction.response.send_message(embed=embed,
                view=ConfirmDeleteEventView(event), ephemeral=True)

        elif self.action == "regs":
            embed, total = build_registrations_embed(event, 1, interaction.guild)
            await interaction.response.send_message(embed=embed,
                view=RegistrationsPageView(event, 1, interaction.user.id, interaction.guild), ephemeral=True)

        elif self.action == "start":
            event["status"] = "ongoing"; save_data(squad_data)
            embed = discord.Embed(title="▶️ Event Started!",
                description=f"**{event['name']}** is now **ONGOING**.", color=ROYAL_GREEN)
            apply_branding(embed, thumbnail=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            pub = discord.Embed(title="⚔️ THE ARENA IS OPEN!",
                description=f"**{event['name']}** has officially begun!\n\n*{event.get('description','')}*\n\n⚔️ Let the battle commence!",
                color=ROYAL_GOLD)
            await announce_major(interaction.guild, pub)
            await log_action(interaction.guild, "▶️ Event Started", f"{interaction.user.mention} started **{event['name']}**")

        elif self.action == "close":
            event["status"] = "closed"; save_data(squad_data)
            embed = discord.Embed(title="⏹️ Event Closed!",
                description=f"**{event['name']}** is now **CLOSED**.", color=ROYAL_RED)
            apply_branding(embed, thumbnail=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            pub = discord.Embed(title="🏁 EVENT CONCLUDED!",
                description=f"**{event['name']}** has concluded!\n\n*Glory and honour to all who competed!*",
                color=ROYAL_PURPLE)
            await announce_major(interaction.guild, pub)
            await log_action(interaction.guild, "⏹️ Event Closed", f"{interaction.user.mention} closed **{event['name']}**")

        elif self.action == "randomize":
            embed = discord.Embed(title=f"🎲 Randomize — {event['name']}",
                description="Choose what to generate:", color=ROYAL_PURPLE)
            apply_branding(embed, thumbnail=True)
            await interaction.response.send_message(embed=embed,
                view=RandomizeView(event, interaction.user.id), ephemeral=True)

        elif self.action == "schedule":
            unscheduled = get_unscheduled_matches(event)
            if not unscheduled:
                return await interaction.response.send_message(
                    "✅ All matches are already scheduled (or no matches generated yet).", ephemeral=True)
            embed = discord.Embed(title=f"📅 Schedule Matches — {event['name']}",
                description=f"**{len(unscheduled)}** unscheduled matches. Select one to schedule:",
                color=ROYAL_GOLD)
            apply_branding(embed, thumbnail=True)
            await interaction.response.send_message(embed=embed,
                view=ScheduleMatchSelectView(event, unscheduled, interaction.user.id), ephemeral=True)


class ConfirmDeleteEventView(View):
    def __init__(self, event):
        super().__init__(timeout=60); self.event = event

    @discord.ui.button(label="✅ Confirm Delete", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, button):
        squad_data["events"] = [e for e in get_all_events() if e["id"] != self.event["id"]]
        save_data(squad_data)
        embed = discord.Embed(title="🗑️ Event Deleted", description=f"**{self.event['name']}** removed.", color=ROYAL_RED)
        apply_branding(embed, thumbnail=True)
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(interaction.guild, "🗑️ Event Deleted", f"{interaction.user.mention} deleted **{self.event['name']}**")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(content="❌ Cancelled.", embed=None, view=None)


class RegistrationsPageView(View):
    def __init__(self, event, page, author_id, guild):
        super().__init__(timeout=180)
        self.event = event; self.page = page
        self.author_id = author_id; self.guild = guild
        _, self.total_pages = build_registrations_embed(event, page, guild)
        self.prev_btn.disabled = page <= 1
        self.next_btn.disabled = page >= self.total_pages

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary, row=0)
    async def prev_btn(self, interaction, button):
        if interaction.user.id != self.author_id: return
        self.page = max(1, self.page-1)
        self.prev_btn.disabled = self.page <= 1
        self.next_btn.disabled = self.page >= self.total_pages
        embed, _ = build_registrations_embed(self.event, self.page, self.guild)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="▶ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_btn(self, interaction, button):
        if interaction.user.id != self.author_id: return
        self.page = min(self.total_pages, self.page+1)
        self.prev_btn.disabled = self.page <= 1
        self.next_btn.disabled = self.page >= self.total_pages
        embed, _ = build_registrations_embed(self.event, self.page, self.guild)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🗑️ Remove Registrant", style=discord.ButtonStyle.danger, row=1)
    async def remove_btn(self, interaction, button):
        if interaction.user.id != self.author_id: return
        regs = self.event.get("registrations", [])
        if not regs:
            return await interaction.response.send_message("❌ No registrations.", ephemeral=True)
        opts = []
        for i, reg in enumerate(regs[:25]):
            name = get_reg_name(reg)
            opts.append(discord.SelectOption(label=name[:100], value=str(i),
                description=f"Registered {reg.get('registered_at','')[:10]}"))
        embed = discord.Embed(title="🗑️ Remove Registrant", description="Select who to remove:", color=ROYAL_RED)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=RemoveRegistrantView(self.event, opts, interaction.user.id), ephemeral=True)


class RemoveRegistrantView(View):
    def __init__(self, event, opts, author_id):
        super().__init__(timeout=120)
        self.event = event; self.author_id = author_id
        sel = Select(placeholder="Select registrant to remove...", options=opts)
        sel.callback = self._selected
        self.add_item(sel)

    async def _selected(self, interaction):
        if interaction.user.id != self.author_id: return
        idx = int(interaction.data["values"][0])
        if idx >= len(self.event["registrations"]):
            return await interaction.response.edit_message(content="❌ Invalid selection.", embed=None, view=None)
        removed = self.event["registrations"].pop(idx)
        save_data(squad_data)
        name = get_reg_name(removed)
        embed = discord.Embed(title="✅ Registrant Removed",
            description=f"**{name}** removed from **{self.event['name']}**.", color=ROYAL_RED)
        apply_branding(embed, thumbnail=True)
        await interaction.response.edit_message(embed=embed, view=None)
        await log_action(interaction.guild, "🗑️ Registrant Removed",
            f"{interaction.user.mention} removed **{name}** from **{self.event['name']}**")


# ── Randomize view ─────────────────────────────────────────────────────

class RandomizeView(View):
    """
    Row 0: Simple Draws  — just "who plays who", no structure
    Row 1: Full Brackets — tournament structure (Single/Double Elim, Round Robin)
    Row 2: Groups & management
    """
    def __init__(self, event, author_id):
        super().__init__(timeout=180)
        self.event = event
        self.author_id = author_id

    def _ok(self, i): return i.user.id == self.author_id

    async def _gen(self, interaction, bd, label):
        self.event["bracket_data"] = bd
        self.event["schedule"] = []
        save_data(squad_data)
        embed = build_bracket_embed(self.event)
        await interaction.response.edit_message(embed=embed, view=None)
        await announce_major(interaction.guild, build_bracket_embed(self.event))
        await log_action(interaction.guild, f"🎲 {label}",
            f"{interaction.user.mention} generated **{label}** for **{self.event['name']}**")

    # ── Row 0: Simple Draws (no bracket structure) ──────────────────────
    @discord.ui.button(label="🎲 Random Draw", style=discord.ButtonStyle.success, row=0,
        custom_id="rdraw")
    async def draw_btn(self, interaction, button):
        """Pair everyone randomly — simple list, no bracket."""
        if not self._ok(interaction): return
        regs = self.event.get("registrations", [])
        if len(regs) < 2:
            return await interaction.response.send_message("❌ Need at least 2 registrations.", ephemeral=True)
        await self._gen(interaction, generate_random_draw(regs), "Random Draw")

    @discord.ui.button(label="👥 Random Teams (from Solo)", style=discord.ButtonStyle.success, row=0,
        custom_id="rteams")
    async def teams_btn(self, interaction, button):
        """Group solo registrants into random teams, then pair them."""
        if not self._ok(interaction): return
        if self.event.get("registration_mode") != "solo":
            return await interaction.response.send_message(
                "❌ Only available for **Solo** registration events.", ephemeral=True)
        if len(self.event.get("registrations", [])) < 2:
            return await interaction.response.send_message("❌ Need at least 2 registrations.", ephemeral=True)
        await interaction.response.send_modal(RandomTeamSizeModal(self.event, self.author_id))

    @discord.ui.button(label="🎯 Pick One (Lottery)", style=discord.ButtonStyle.success, row=0,
        custom_id="rpick")
    async def pick_btn(self, interaction, button):
        """Randomly select ONE player or team — lottery style."""
        if not self._ok(interaction): return
        regs = self.event.get("registrations", [])
        if len(regs) < 1:
            return await interaction.response.send_message("❌ No registrations yet.", ephemeral=True)
        await self._gen(interaction, generate_random_pick(regs), "Random Pick")

    @discord.ui.button(label="👥 Gather Group (N players)", style=discord.ButtonStyle.success, row=0,
        custom_id="rgather")
    async def gather_btn(self, interaction, button):
        """Randomly pick N participants and group them together."""
        if not self._ok(interaction): return
        if len(self.event.get("registrations", [])) < 2:
            return await interaction.response.send_message("❌ Need at least 2 registrations.", ephemeral=True)
        await interaction.response.send_modal(GatherGroupModal(self.event, self.author_id))

    # ── Row 1: Bracket Systems ──────────────────────────────────────────
    @discord.ui.button(label="🏆 Single Elimination", style=discord.ButtonStyle.primary, row=1,
        custom_id="selim")
    async def se_btn(self, interaction, button):
        if not self._ok(interaction): return
        regs = self.event.get("registrations", [])
        if len(regs) < 2:
            return await interaction.response.send_message("❌ Need at least 2.", ephemeral=True)
        await self._gen(interaction, generate_single_elim(regs), "Single Elimination")

    @discord.ui.button(label="⚔️ Double Elimination", style=discord.ButtonStyle.primary, row=1,
        custom_id="delim")
    async def de_btn(self, interaction, button):
        if not self._ok(interaction): return
        regs = self.event.get("registrations", [])
        if len(regs) < 2:
            return await interaction.response.send_message("❌ Need at least 2.", ephemeral=True)
        await self._gen(interaction, generate_double_elim(regs), "Double Elimination")

    @discord.ui.button(label="🔄 Round Robin", style=discord.ButtonStyle.secondary, row=1,
        custom_id="rrobin")
    async def rr_btn(self, interaction, button):
        if not self._ok(interaction): return
        regs = self.event.get("registrations", [])
        if len(regs) < 2:
            return await interaction.response.send_message("❌ Need at least 2.", ephemeral=True)
        await self._gen(interaction, generate_round_robin(regs), "Round Robin")

    # ── Row 2: Groups & Management ──────────────────────────────────────
    @discord.ui.button(label="🎲 Random Groups", style=discord.ButtonStyle.primary, row=2,
        custom_id="rgroups")
    async def groups_btn(self, interaction, button):
        if not self._ok(interaction): return
        if len(self.event.get("registrations", [])) < 4:
            return await interaction.response.send_message("❌ Need at least 4 registrations.", ephemeral=True)
        await interaction.response.send_modal(GroupCountModal(self.event, self.author_id))

    @discord.ui.button(label="🎯 Groups → Bracket", style=discord.ButtonStyle.success, row=2,
        custom_id="gadvance")
    async def advance_btn(self, interaction, button):
        if not self._ok(interaction): return
        bd = self.event.get("bracket_data")
        if not bd or bd.get("system") not in ("groups", "group_bracket"):
            return await interaction.response.send_message("❌ No group stage found.", ephemeral=True)
        advance_groups_to_bracket(bd, bd.get("advances_per_group", 2))
        await self._gen(interaction, bd, "Groups → Bracket")

    @discord.ui.button(label="🗑️ Clear & Redo", style=discord.ButtonStyle.danger, row=2,
        custom_id="gclear")
    async def clear_btn(self, interaction, button):
        if not self._ok(interaction): return
        self.event["bracket_data"] = None
        self.event["schedule"] = []
        save_data(squad_data)
        desc = ("**Choose a draw type above:**\n\n"
                "**Row 1 — Simple Draws** (no bracket)\n"
                "🎲 **Random Draw** — pair everyone up randomly\n"
                "👥 **Random Teams** — form teams from solo players then pair them\n\n"
                "**Row 2 — Bracket Systems** (structured tournament)\n"
                "🏆 Single Elim · ⚔️ Double Elim · 🔄 Round Robin\n\n"
                "**Row 3 — Groups**\n"
                "🎲 Random Groups · 🎯 Groups→Bracket")
        embed = discord.Embed(title=f"🎲 Randomize — {self.event['name']}",
            description=desc, color=ROYAL_PURPLE)
        apply_branding(embed, thumbnail=True)
        await interaction.response.edit_message(embed=embed, view=self)
        await log_action(interaction.guild, "🗑️ Draw Cleared",
            f"{interaction.user.mention} cleared draw for **{self.event['name']}**")


class RandomTeamSizeModal(Modal, title="👥 Random Teams — Team Size"):
    team_size = TextInput(label="Players per team",
        placeholder="e.g., 2  →  2v2 teams,  3  →  3v3 teams",
        required=True, max_length=2)
    def __init__(self, event, author_id):
        super().__init__(); self.event = event; self.author_id = author_id

    async def on_submit(self, interaction):
        try:
            ts = int(self.team_size.value.strip())
            if ts < 2: raise ValueError
        except:
            return await interaction.response.send_message("❌ Enter a valid team size ≥ 2.", ephemeral=True)
        regs = self.event.get("registrations", [])
        if len(regs) < ts:
            return await interaction.response.send_message(
                f"❌ Not enough registrations ({len(regs)}) for teams of {ts}.", ephemeral=True)
        bd = generate_random_teams_from_solo(regs, team_size=ts)
        self.event["bracket_data"] = bd
        self.event["schedule"] = []
        save_data(squad_data)
        embed = build_bracket_embed(self.event)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await announce_major(interaction.guild, build_bracket_embed(self.event))
        await log_action(interaction.guild, "👥 Random Teams",
            f"{interaction.user.mention} formed **{len(bd['teams'])} teams** (size {ts}) for **{self.event['name']}**")


class GatherGroupModal(Modal, title="👥 Gather Random Group"):
    group_size = TextInput(
        label="How many participants to pick?",
        placeholder="e.g., 3  (picks 3 random players from all registrants)",
        required=True, max_length=3)
    def __init__(self, event, author_id):
        super().__init__(); self.event = event; self.author_id = author_id

    async def on_submit(self, interaction):
        try:
            n = int(self.group_size.value.strip())
            if n < 1: raise ValueError
        except:
            return await interaction.response.send_message(
                "❌ Enter a valid number (1 or more).", ephemeral=True)
        regs = self.event.get("registrations", [])
        if n > len(regs):
            return await interaction.response.send_message(
                f"❌ Only **{len(regs)}** registered — can't pick {n}.", ephemeral=True)
        bd = generate_gather_group(regs, size=n)
        self.event["bracket_data"] = bd
        self.event["schedule"] = []
        save_data(squad_data)
        # Confirmation embed
        conf = discord.Embed(
            title=f"👥 Random Group of {n} — {self.event['name']}",
            description="\n".join(f"• **{m}**" for m in bd["selected"]),
            color=ROYAL_GOLD)
        conf.set_footer(text=f"⚜️ Randomly selected from {len(regs)} registrants")
        apply_branding(conf, thumbnail=True)
        await interaction.response.send_message(embed=conf, ephemeral=True)
        # Public announcement in war-results
        pub = discord.Embed(
            title=f"🎲 RANDOM GROUP SELECTED — {self.event['name']}",
            description=(
                f"**{n} participant(s)** were randomly selected:\n\n"
                + "\n".join(f"⚔️ **{m}**" for m in bd["selected"])
                + (f"\n\n*({len(bd['remaining'])} others were not selected this draw)*" if bd["remaining"] else "")
            ),
            color=ROYAL_GOLD)
        pub.set_footer(text=f"⚜️ Majestic Dominion | {self.event['name']}")
        apply_branding(pub, thumbnail=False, author=True)
        await announce_event(interaction.guild, pub)
        await log_action(interaction.guild, "👥 Group Gathered",
            f"{interaction.user.mention} randomly picked **{n}** participants for **{self.event['name']}**")


class GroupCountModal(Modal, title="🎲 Random Groups"):
    num_groups = TextInput(label="Number of Groups", placeholder="e.g., 4", required=True, max_length=2)
    advances   = TextInput(label="Teams advancing per group (Groups→Bracket)", placeholder="e.g., 2", required=False, max_length=1)
    def __init__(self, event, author_id):
        super().__init__(); self.event = event; self.author_id = author_id

    async def on_submit(self, interaction):
        try:
            n = int(self.num_groups.value.strip())
            if n < 2: raise ValueError
        except:
            return await interaction.response.send_message("❌ Enter a valid number ≥ 2.", ephemeral=True)
        adv = 2
        if self.advances.value.strip():
            try: adv = max(1, int(self.advances.value.strip()))
            except: pass
        regs = self.event.get("registrations", [])
        if len(regs) < n:
            return await interaction.response.send_message(
                f"❌ Not enough registrations ({len(regs)}) for {n} groups.", ephemeral=True)
        ts = self.event.get("tournament_system", "")
        bd = generate_group_bracket(regs, num_groups=n) if ts == "group_bracket" else generate_groups(regs, num_groups=n)
        bd["advances_per_group"] = adv
        self.event["bracket_data"] = bd
        self.event["schedule"] = []
        save_data(squad_data)
        embed = build_bracket_embed(self.event)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await announce_major(interaction.guild, build_bracket_embed(self.event))
        await log_action(interaction.guild, "🎲 Groups Generated",
            f"{interaction.user.mention} generated **{n} groups** for **{self.event['name']}**")


# ── Schedule match views ───────────────────────────────────────────────

class ScheduleMatchSelectView(View):
    def __init__(self, event, unscheduled, author_id):
        super().__init__(timeout=180)
        self.event = event; self.author_id = author_id; self.unscheduled = unscheduled
        opts = []
        for m in unscheduled[:25]:
            label = f"{m['team1'][:30]} vs {m['team2'][:30]}"
            desc = f"{m.get('round_display','')} | {m['match_id']}"
            opts.append(discord.SelectOption(label=label[:100], value=m["match_id"],
                description=desc[:100], emoji="⚔️"))
        sel = Select(placeholder="⚔️ Select match to schedule...", options=opts)
        sel.callback = self._selected
        self.add_item(sel)

    async def _selected(self, interaction):
        if interaction.user.id != self.author_id: return
        mid = interaction.data["values"][0]
        match = next((m for m in self.unscheduled if m["match_id"] == mid), None)
        if not match:
            return await interaction.response.send_message("❌ Match not found.", ephemeral=True)
        await interaction.response.send_modal(ScheduleMatchModal(self.event, match, interaction.user.id))


class ScheduleMatchModal(Modal, title="📅 Schedule Match"):
    match_date = TextInput(label="Date & Time", placeholder="e.g., May 20, 8:00 PM EST", required=True, max_length=100)
    notes = TextInput(label="Notes (optional)", required=False, max_length=200)
    def __init__(self, event, match, author_id):
        super().__init__(); self.event = event; self.match = match; self.author_id = author_id

    async def on_submit(self, interaction):
        date_str = self.match_date.value.strip()
        note_str = self.notes.value.strip() if self.notes.value else ""
        entry = {
            "match_id": self.match["match_id"],
            "team1": self.match["team1"], "team2": self.match["team2"],
            "date": date_str, "notes": note_str,
            "round_display": self.match.get("round_display",""),
            "group": self.match.get("group"),
            "scheduled_by": str(interaction.user.id),
            "scheduled_at": datetime.utcnow().isoformat()
        }
        if "schedule" not in self.event:
            self.event["schedule"] = []
        # Remove any existing schedule for this match_id
        self.event["schedule"] = [s for s in self.event["schedule"] if s["match_id"] != self.match["match_id"]]
        self.event["schedule"].append(entry)
        save_data(squad_data)
        embed = discord.Embed(title="📅 Match Scheduled!",
            description=(f"⚔️ **{self.match['team1']}** vs **{self.match['team2']}**\n"
                         f"📅 **{date_str}**\n"
                         f"🏷️ {self.match.get('round_display','')}"
                         + (f"\n📋 {note_str}" if note_str else "")),
            color=ROYAL_GREEN)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        pub = discord.Embed(title="📅 MATCH SCHEDULED!",
            description=(f"**{self.match['team1']}** vs **{self.match['team2']}**\n\n"
                         f"📅 **{date_str}**\n"
                         f"🏷️ *{self.match.get('round_display','')} — {self.event['name']}*"),
            color=ROYAL_GOLD)
        pub.set_footer(text=f"⚜️ Majestic Dominion | {self.event['name']}")
        await announce_event(interaction.guild, pub)
        await log_action(interaction.guild, "📅 Match Scheduled",
            f"{interaction.user.mention} scheduled `{self.match['match_id']}`: {self.match['team1']} vs {self.match['team2']} — {date_str}")


# ── Schedule page view ─────────────────────────────────────────────────

class SchedulePageView(View):
    def __init__(self, event, page, author_id):
        super().__init__(timeout=180)
        self.event = event; self.page = page; self.author_id = author_id
        _, self.total_pages = build_schedule_embed(event, page)
        self.prev_btn.disabled = page <= 1
        self.next_btn.disabled = page >= self.total_pages

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction, button):
        if interaction.user.id != self.author_id: return
        self.page = max(1, self.page-1)
        self.prev_btn.disabled = self.page <= 1
        self.next_btn.disabled = self.page >= self.total_pages
        embed, _ = build_schedule_embed(self.event, self.page)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="▶ Next", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction, button):
        if interaction.user.id != self.author_id: return
        self.page = min(self.total_pages, self.page+1)
        self.prev_btn.disabled = self.page <= 1
        self.next_btn.disabled = self.page >= self.total_pages
        embed, _ = build_schedule_embed(self.event, self.page)
        await interaction.response.edit_message(embed=embed, view=self)


# ── Create Event ───────────────────────────────────────────────────────

class CreateEventModal(Modal, title="🎪 New Event — Basic Info"):
    ev_name = TextInput(label="Event Name",               placeholder="e.g., Season 3 Championship",     required=True,  max_length=100)
    ev_desc = TextInput(label="Description",               placeholder="Short overview of the event",      required=True,  max_length=500, style=discord.TextStyle.paragraph)
    ev_date = TextInput(label="Date & Time",               placeholder="e.g., May 20, 2026 at 18:00 UTC", required=True,  max_length=100)
    ev_max  = TextInput(label="Max Entries  (0 = unlimited)", placeholder="e.g., 16",                     required=False, max_length=5)

    async def on_submit(self, interaction):
        max_val = None
        if self.ev_max.value.strip() not in ("", "0"):
            try: max_val = int(self.ev_max.value.strip())
            except: pass
        partial = {
            "name":        self.ev_name.value.strip(),
            "description": self.ev_desc.value.strip(),
            "date":        self.ev_date.value.strip(),
            "format":      "",          # set in settings view
            "max_entries": max_val,
        }
        embed = discord.Embed(title=f"🎪 Configuring: {partial['name']}",
            description=("**Step 1 — Set the event type:**\n"
                         "• 🏆 Tournament → choose a **fixed format** (1v1, 2v2, 5v5…)\n"
                         "• 🎉 Social Event → type **any free format** (1v2, 3v2, FFA, Hide & Seek…)"),
            color=ROYAL_GOLD)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed,
            view=CreateEventSettingsView(partial, interaction.user.id), ephemeral=True)


class CreateEventSettingsView(View):
    """
    Row 0: Type buttons  (🏆 Tournament | 🎉 Social Event)
    Row 1: Registration mode select
    Row 2: Bracket system select
    Row 3: Format select  (fixed list for tournaments, free-text for social)
    Row 4: 💰 Prize | 📜 Rules | 🖼️ Image | ✅ Create | ❌ Cancel
    """
    TOURNAMENT_FORMATS = ["1v1", "2v2", "3v3", "4v4", "5v5", "6v6", "7v7"]

    def __init__(self, partial, author_id):
        super().__init__(timeout=300)
        self.partial           = partial
        self.author_id         = author_id
        self.ev_type           = "tournament"
        self.reg_mode          = "squad_5v5"
        self.team_size         = 5
        self.tournament_system = "single_elim"
        self.prize_pool        = ""
        self.event_image       = ""
        self.rules             = ""
        if not self.partial.get("format"):
            self.partial["format"] = "5v5"

    def _reg_label(self):
        if self.reg_mode == "solo":      return "👤 Solo"
        if self.reg_mode == "squad_5v5": return "👑 Squad 5v5 (Leaders Only)"
        return f"👥 Small Team ({self.team_size}v{self.team_size})"

    def _sys_label(self):
        if not self.tournament_system: return "None (no bracket)"
        return TOURNAMENT_SYSTEMS.get(self.tournament_system, ("", ""))[1]

    def _embed(self):
        fmt  = self.partial.get("format") or "—"
        type_label = "Tournament" if self.ev_type == "tournament" else "Social Event"
        embed = discord.Embed(title=f"🎪 {self.partial['name']}", color=ROYAL_GOLD)
        embed.add_field(name="📋 Type",           value=f"**{type_label}**",       inline=True)
        embed.add_field(name="⚔️ Format",         value=f"**{fmt}**",              inline=True)
        embed.add_field(name="📝 Registration",   value=self._reg_label(),         inline=True)
        embed.add_field(name="🏆 Bracket System", value=self._sys_label(),         inline=True)
        embed.add_field(name="📅 Date",           value=self.partial["date"],       inline=True)
        if self.partial.get("max_entries"):
            embed.add_field(name="🔢 Max",        value=str(self.partial["max_entries"]), inline=True)
        if self.prize_pool:
            embed.add_field(name="💰 Prize",      value=self.prize_pool,           inline=True)
        if self.event_image:
            embed.add_field(name="🖼️ Image",      value="✅ Set",                   inline=True)
            embed.set_image(url=self.event_image)
        if self.rules:
            embed.add_field(name="📜 Rules",
                value=self.rules[:200] + ("..." if len(self.rules) > 200 else ""), inline=False)
        embed.add_field(name="📖 Description", value=self.partial["description"][:200], inline=False)
        embed.set_footer(text="⚜️ Configure then click ✅ Create")
        apply_branding(embed, thumbnail=True)
        return embed

    # Row 0 ── Event type
    @discord.ui.button(label="🏆 Tournament", style=discord.ButtonStyle.primary, row=0)
    async def t_tournament(self, i, b):
        if i.user.id != self.author_id: return
        self.ev_type = "tournament"
        if self.partial.get("format") not in self.TOURNAMENT_FORMATS:
            self.partial["format"] = "5v5"
        if not self.tournament_system:
            self.tournament_system = "single_elim"
        await i.response.edit_message(embed=self._embed(), view=self)

    @discord.ui.button(label="🎉 Social Event", style=discord.ButtonStyle.primary, row=0)
    async def t_fun(self, i, b):
        if i.user.id != self.author_id: return
        self.ev_type = "fun"
        if self.partial.get("format") in self.TOURNAMENT_FORMATS:
            self.partial["format"] = ""
        self.tournament_system = None
        await i.response.edit_message(embed=self._embed(), view=self)

    # Row 1 ── Registration mode
    @discord.ui.select(placeholder="📝 Registration mode...", row=1, options=[
        discord.SelectOption(label="👤 Solo",                     value="solo",
            description="Each player registers individually"),
        discord.SelectOption(label="👥 Small Team — 2v2",         value="small_team_2",
            description="2 players per team"),
        discord.SelectOption(label="👥 Small Team — 3v3",         value="small_team_3",
            description="3 players per team"),
        discord.SelectOption(label="👥 Small Team — 4v4",         value="small_team_4",
            description="4 players per team"),
        discord.SelectOption(label="👑 Squad 5v5 (Leaders Only)", value="squad_5v5",
            description="Uses existing squad system"),
    ])
    async def reg_mode_select(self, interaction, select):
        if interaction.user.id != self.author_id: return
        val = select.values[0]
        if val.startswith("small_team_"):
            self.reg_mode  = "small_team"
            self.team_size = int(val.split("_")[-1])
            if self.ev_type == "tournament":
                self.partial["format"] = f"{self.team_size}v{self.team_size}"
        else:
            self.reg_mode = val
            if val == "squad_5v5" and self.ev_type == "tournament":
                self.partial["format"] = "5v5"
        await interaction.response.edit_message(embed=self._embed(), view=self)

    # Row 2 ── Bracket system
    @discord.ui.select(placeholder="🏆 Bracket system (optional)...", row=2, options=[
        discord.SelectOption(label="None (no bracket)",           value="none",
            description="Social/fun event without a bracket"),
        discord.SelectOption(label="🏆 Single Elimination",       value="single_elim",
            description="Classic — one loss and out"),
        discord.SelectOption(label="⚔️ Double Elimination",       value="double_elim",
            description="Two losses to be eliminated"),
        discord.SelectOption(label="🔄 Round Robin",              value="round_robin",
            description="Everyone plays everyone"),
        discord.SelectOption(label="🎯 Group Stage → Bracket",    value="group_bracket",
            description="Groups first, then knockout"),
    ])
    async def sys_select(self, interaction, select):
        if interaction.user.id != self.author_id: return
        val = select.values[0]
        self.tournament_system = None if val == "none" else val
        await interaction.response.edit_message(embed=self._embed(), view=self)

    # Row 3 ── Format select
    @discord.ui.select(placeholder="⚔️ Select event format...", row=3, options=[
        discord.SelectOption(label="1v1",  value="1v1",  emoji="⚔️"),
        discord.SelectOption(label="2v2",  value="2v2",  emoji="👥"),
        discord.SelectOption(label="3v3",  value="3v3",  emoji="🔱"),
        discord.SelectOption(label="4v4",  value="4v4",  emoji="🏰"),
        discord.SelectOption(label="5v5",  value="5v5",  emoji="👑",
            description="Required for Squad 5v5 events"),
        discord.SelectOption(label="6v6",  value="6v6",  emoji="🛡️"),
        discord.SelectOption(label="7v7",  value="7v7",  emoji="⚜️"),
        discord.SelectOption(label="✏️ Custom / Free format (Social events only)", value="free",
            description="Type any format — e.g. 1v2, FFA, Hide & Seek"),
    ])
    async def format_select(self, interaction, select):
        if interaction.user.id != self.author_id: return
        val = select.values[0]
        if val == "free":
            if self.ev_type == "tournament":
                return await interaction.response.send_message(
                    "❌ Tournaments require a **fixed format** (1v1 – 7v7). "
                    "Switch to 🎉 **Social Event** to use a custom format.", ephemeral=True)
            return await interaction.response.send_modal(FreeFormatModal(self))
        self.partial["format"] = val
        await interaction.response.edit_message(embed=self._embed(), view=self)

    # Row 4 ── Extras + confirm
    @discord.ui.button(label="💰 Prize",  style=discord.ButtonStyle.secondary, row=4)
    async def prize_btn(self, i, b):
        if i.user.id != self.author_id: return
        await i.response.send_modal(AddPrizePoolModal(self))

    @discord.ui.button(label="📜 Rules",  style=discord.ButtonStyle.secondary, row=4)
    async def rules_btn(self, i, b):
        if i.user.id != self.author_id: return
        await i.response.send_modal(AddRulesModal(self))

    @discord.ui.button(label="🖼️ Image",  style=discord.ButtonStyle.secondary, row=4)
    async def image_btn(self, i, b):
        if i.user.id != self.author_id: return
        await i.response.send_modal(AddImageModal(self))

    @discord.ui.button(label="✅ Create", style=discord.ButtonStyle.success, row=4)
    async def create_confirm(self, interaction, button):
        if interaction.user.id != self.author_id: return
        if not self.partial.get("format"):
            return await interaction.response.send_message(
                "❌ Please select a **Format** first (Row 3).", ephemeral=True)
        event_id = str(uuid.uuid4())[:8]
        event = {
            "id": event_id, "name": self.partial["name"],
            "type": self.ev_type, "registration_mode": self.reg_mode,
            "team_size": (self.team_size if self.reg_mode == "small_team"
                          else 5 if self.reg_mode == "squad_5v5" else 1),
            "format":      self.partial["format"],
            "max_entries": self.partial.get("max_entries"),
            "date":        self.partial["date"],
            "description": self.partial["description"],
            "rules":       self.rules,
            "prize_pool":  self.prize_pool,
            "event_image": self.event_image,
            "status":      "open",
            "tournament_system": self.tournament_system,
            "randomize_groups": False, "randomize_brackets": False,
            "registrations": [], "bracket_data": None, "schedule": [],
            "created_by": str(interaction.user.id),
            "created_at": datetime.utcnow().isoformat()
        }
        if "events" not in squad_data: squad_data["events"] = []
        squad_data["events"].append(event)
        save_data(squad_data)
        embed = discord.Embed(title="✅ Event Created!",
            description=f"**{event['name']}** is live!\n`ID: {event_id}`", color=ROYAL_GREEN)
        apply_branding(embed, thumbnail=True)
        await interaction.response.edit_message(embed=embed, view=None)
        await announce_new_event(interaction.guild, event)
        await log_action(interaction.guild, "🎪 Event Created",
            f"{interaction.user.mention} created **{event['name']}** ({event['type']}, {event['format']})")

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger, row=4)
    async def cancel_btn(self, interaction, button):
        if interaction.user.id != self.author_id: return
        await interaction.response.edit_message(content="❌ Event creation cancelled.", embed=None, view=None)


class FreeFormatModal(Modal, title="⚔️ Custom Format"):
    """Free-text format for social events."""
    fmt = TextInput(label="Format (any — e.g. 1v2, FFA, Hide & Seek…)",
        placeholder="Type any format freely", required=True, max_length=30)
    def __init__(self, parent):
        super().__init__(); self.parent = parent
    async def on_submit(self, interaction):
        self.parent.partial["format"] = self.fmt.value.strip()
        await interaction.response.edit_message(embed=self.parent._embed(), view=self.parent)


async def announce_new_event(guild, event):
    """
    Announcements channel → @MAJESTIC ping + clean summary (name, description, format, reg, date, max, prize, how to register, check war-results).
    War-results channel   → full details embed, NO ping.
    """
    ann_ch = discord.utils.get(guild.text_channels, name=NEWS_CHANNEL_NAME)
    war_ch = discord.utils.get(guild.text_channels, name=ANNOUNCE_CHANNEL_NAME)

    majestic_role = discord.utils.get(guild.roles, name=MAJESTIC_ROLE_NAME)
    mention       = majestic_role.mention if majestic_role else f"@{MAJESTIC_ROLE_NAME}"

    ts       = event.get("team_size", 2)
    rm_labels = {
        "solo":       "👤 Solo",
        "small_team": f"👥 Small Team ({ts}v{ts})",
        "squad_5v5":  "👑 Squad 5v5 (Leaders Only)",
    }
    rm_label   = rm_labels.get(event.get("registration_mode", "solo"), "?")
    type_icon  = {"tournament": "🏆", "fun": "🎉", "social": "🎉"}.get(event["type"], "🎪")
    type_label = "Tournament" if event["type"] == "tournament" else "Social Event"
    sys_label  = TOURNAMENT_SYSTEMS.get(event.get("tournament_system", ""), ("", ""))[1]

    # ── Announcements channel: @MAJESTIC ping + clean summary ─────────
    if ann_ch:
        ann_embed = discord.Embed(
            title=f"🎪 {event['name']}",
            description=event.get("description", ""),
            color=ROYAL_GOLD,
            timestamp=datetime.utcnow()
        )
        ann_embed.add_field(name="⚔️ Format",       value=event.get("format", "?"), inline=True)
        ann_embed.add_field(name="📝 Registration",  value=rm_label,                 inline=True)
        ann_embed.add_field(name="📅 Date",          value=event["date"],             inline=True)
        if event.get("max_entries"):
            ann_embed.add_field(name="🔢 Max Entries", value=str(event["max_entries"]), inline=True)
        if event.get("prize_pool"):
            ann_embed.add_field(name="💰 Prize Pool",  value=event["prize_pool"],       inline=True)
        ann_embed.add_field(
            name="📝 How to Register",
            value=f"Type `/events` → select **{event['name']}** → click **📝 Register**",
            inline=False
        )
        ann_embed.add_field(
            name="📺 Full Details & Updates",
            value=f"Bracket, schedule and all game updates in **{ANNOUNCE_CHANNEL_NAME}**",
            inline=False
        )
        ann_embed.set_footer(text=f"⚜️ Majestic Dominion | Event ID: {event['id']}")
        apply_branding(ann_embed, thumbnail=False, author=True)
        try:
            if event.get("event_image"):
                ann_embed.set_image(url=event["event_image"])
                await ann_ch.send(content=f"📢 {mention}", embed=ann_embed)
            elif os.path.exists(LOGO_DARK):
                af = discord.File(LOGO_DARK, filename="banner.png")
                ann_embed.set_image(url="attachment://banner.png")
                await ann_ch.send(content=f"📢 {mention}", embed=ann_embed, file=af)
            else:
                await ann_ch.send(content=f"📢 {mention}", embed=ann_embed)
        except Exception as e:
            print(f"⚠️ Announcement channel error: {e}")

    # ── War-results channel: full details, NO ping ────────────────────
    if war_ch:
        war_embed = discord.Embed(
            title=f"🎪 NEW EVENT — {event['name']}",
            description=event.get("description", ""),
            color=ROYAL_GOLD,
            timestamp=datetime.utcnow()
        )
        if event.get("event_image"):
            war_embed.set_image(url=event["event_image"])
        war_embed.add_field(name="📋 Type",       value=f"{type_icon} {type_label}", inline=True)
        war_embed.add_field(name="⚔️ Format",     value=event.get("format", "?"),    inline=True)
        war_embed.add_field(name="📅 Date",        value=event["date"],               inline=True)
        war_embed.add_field(name="📝 Registration", value=rm_label,                   inline=True)
        if event.get("max_entries"):
            war_embed.add_field(name="🔢 Max",    value=str(event["max_entries"]),    inline=True)
        if event.get("prize_pool"):
            war_embed.add_field(name="💰 Prize",   value=event["prize_pool"],         inline=True)
        if sys_label:
            war_embed.add_field(name="🏆 Bracket", value=sys_label,                  inline=True)
        if event.get("rules"):
            war_embed.add_field(name="📜 Rules",   value=event["rules"][:1024],       inline=False)
        war_embed.add_field(
            name="📝 Register",
            value=f"Type `/events` → select **{event['name']}** → **📝 Register**",
            inline=False
        )
        war_embed.set_footer(text=f"⚜️ Majestic Dominion | Event ID: {event['id']}")
        apply_branding(war_embed, thumbnail=False, author=True)
        try:
            if not event.get("event_image") and os.path.exists(LOGO_DARK):
                wf = discord.File(LOGO_DARK, filename="banner.png")
                war_embed.set_image(url="attachment://banner.png")
                await war_ch.send(embed=war_embed, file=wf)
            else:
                await war_ch.send(embed=war_embed)
        except Exception as e:
            print(f"⚠️ War-results event error: {e}")


class AddPrizePoolModal(Modal, title="💰 Add Prize Pool"):
    prize = TextInput(label="Prize Pool Description", placeholder="e.g., 50$ / Game credits / Custom reward",
        required=True, max_length=200)
    def __init__(self, parent):
        super().__init__(); self.parent = parent
    async def on_submit(self, interaction):
        self.parent.prize_pool = self.prize.value.strip()
        await interaction.response.edit_message(embed=self.parent._embed(), view=self.parent)

class AddImageModal(Modal, title="🖼️ Add Event Image"):
    url = TextInput(label="Image URL", placeholder="https://i.imgur.com/example.png", required=True, max_length=500)
    def __init__(self, parent):
        super().__init__(); self.parent = parent
    async def on_submit(self, interaction):
        self.parent.event_image = self.url.value.strip()
        await interaction.response.edit_message(embed=self.parent._embed(), view=self.parent)

class AddRulesModal(Modal, title="📜 Add Event Rules"):
    rules = TextInput(label="Rules & Special Conditions",
        placeholder="Enter event rules, special format, etc.",
        style=discord.TextStyle.paragraph, required=False, max_length=1000)
    def __init__(self, parent):
        super().__init__(); self.parent = parent
    async def on_submit(self, interaction):
        self.parent.rules = self.rules.value.strip()
        await interaction.response.edit_message(embed=self.parent._embed(), view=self.parent)


class EditEventModal(Modal, title="✏️ Edit Event"):
    def __init__(self, event):
        super().__init__(); self.event = event
        self.ev_name   = TextInput(label="Event Name",       default=event["name"],                required=True,  max_length=100)
        self.ev_desc   = TextInput(label="Description",       default=event.get("description",""),  required=True,  max_length=500, style=discord.TextStyle.paragraph)
        self.ev_date   = TextInput(label="Date & Time",       default=event.get("date",""),         required=True,  max_length=100)
        self.ev_prize  = TextInput(label="Prize Pool",        default=event.get("prize_pool",""),   required=False, max_length=200)
        self.ev_status = TextInput(label="Status (open/ongoing/closed)", default=event.get("status","open"), required=True, max_length=10)
        self.add_item(self.ev_name); self.add_item(self.ev_desc); self.add_item(self.ev_date)
        self.add_item(self.ev_prize); self.add_item(self.ev_status)

    async def on_submit(self, interaction):
        status = self.ev_status.value.strip().lower()
        if status not in ("open","ongoing","closed"):
            return await interaction.response.send_message("❌ Status must be: open, ongoing, or closed", ephemeral=True)
        self.event.update({
            "name": self.ev_name.value.strip(), "description": self.ev_desc.value.strip(),
            "date": self.ev_date.value.strip(), "prize_pool": self.ev_prize.value.strip(),
            "status": status,
        })
        save_data(squad_data)
        embed = discord.Embed(title="✅ Event Updated!",
            description=f"**{self.event['name']}** has been updated.", color=ROYAL_GREEN)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(interaction.guild, "✏️ Event Edited", f"{interaction.user.mention} edited **{self.event['name']}**")


# ── /events slash command ──────────────────────────────────────────────

@bot.tree.command(name="events", description="🎪 Browse and register for upcoming Majestic events")
async def events_command(interaction: discord.Interaction):
    all_events = get_all_events()
    visible = [e for e in all_events if e["status"] != "closed"] or all_events
    if not visible:
        embed = discord.Embed(title="🎪 Majestic Arena — No Events Yet",
            description="*The arena is quiet... for now.*\n\n⚔️ Check back soon — the Crown will announce the next battle!",
            color=ROYAL_GOLD)
        apply_branding(embed, thumbnail=True)
        await interaction.response.send_message(embed=embed)
        return

    per_page = 4
    total_pages = max(1, (len(visible)+per_page-1)//per_page)
    first_chunk = visible[:per_page]
    status_icons = {"open":"🟢","ongoing":"⚔️","closed":"🔴"}
    type_icons   = {"tournament":"🏆","fun":"🎉","social":"🎉"}
    mode_icons   = {"solo":"👤","small_team":"👥","squad_5v5":"👑"}

    embed = discord.Embed(title="🎪 Majestic Arena — Events",
        description=f"*The Crown's arena is open!*\n**{len(visible)}** event(s) available",
        color=ROYAL_GOLD)
    apply_branding(embed, thumbnail=True)
    for ev in first_chunk:
        si  = status_icons.get(ev["status"],"⚪")
        ti  = type_icons.get(ev["type"],"🎪")
        mi  = mode_icons.get(ev.get("registration_mode","solo"),"")
        fmt = ev.get("format","?")
        rc  = len(ev.get("registrations",[]))
        mx  = f"/{ev['max_entries']}" if ev.get("max_entries") else ""
        pp  = f" | 💰 {ev['prize_pool']}" if ev.get("prize_pool") else ""
        desc = ev.get("description","")[:80]+("..." if len(ev.get("description",""))>80 else "")
        embed.add_field(name=f"{ti} {ev['name']}",
            value=f"{si} **{ev['status'].upper()}** | {mi} {fmt}{pp}\n📅 {ev['date']}\n👥 {rc}{mx} registered\n*{desc}*",
            inline=False)
    embed.set_footer(text=f"⚜️ Page 1/{total_pages} | Select an event below")
    view = EventsListView(visible, page=0, author_id=interaction.user.id)  # detail uses EventDetailViewV2
    await interaction.response.send_message(embed=embed, view=view)
    await log_action(interaction.guild, "🎪 /events", f"{interaction.user.mention} opened the **Events Board**")


# -------------------- EVENTS --------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    safety_sync.start()
    if not weekly_digest_task.is_running():
        weekly_digest_task.start()
    if not daily_pulse_task.is_running():
        daily_pulse_task.start()
    if not bot_commands_cleanup_task.is_running():
        bot_commands_cleanup_task.start()

    # Set bot avatar to Majestic Dominion logo (once)
    if os.path.exists(LOGO_DARK):
        try:
            if not squad_data.get("_avatar_set_dark"):
                with open(LOGO_DARK, "rb") as f:
                    await bot.user.edit(avatar=f.read())
                squad_data["_avatar_set_dark"] = True
                save_data(squad_data)
                print("👑 Bot avatar set to Majestic Dominion dark logo!")
        except Exception as e:
            print(f"⚠️ Could not set avatar: {e}")

    print(f"✅ Logged in as {bot.user}")
    print(f"⚜️ Majestic Dominion Bot is online! The Crown watches over all.")
    for guild in bot.guilds:
        await cache_transparent_logo(guild)
        await setup_bot_commands_channel(guild)
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
