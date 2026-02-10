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
DATA_FILE = "squad_data.json"

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
    "Titans": "TTS",
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
    "Titans": "Titans_guest",
    "NONKAR": "Nonkar_guest",
    "Exeed": "Exeed_guest",
    "One More Esports": "One.More.Esports_guest",
    "asgard warriors": "Asguard.Warriors_guest",
    "Manschaft": "Manschaft_guest",
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

# -------------------- DATA MANAGEMENT --------------------
def load_data():
    """Load squad data from JSON file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
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
            "match_history": []
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

def update_player_squad(player_id, new_squad=None):
    """Update player's squad in their profile"""
    player_key = str(player_id)
    if player_key in squad_data["players"]:
        squad_data["players"][player_key]["squad"] = new_squad
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
    """Get comprehensive player statistics"""
    player_key = str(player_id)
    player_data = squad_data["players"].get(player_key)
    
    if not player_data:
        return None
    
    # Count matches the player participated in
    matches_played = 0
    wins = 0
    losses = 0
    draws = 0
    
    squad_name = player_data.get("squad")
    if squad_name and squad_name in squad_data["squads"]:
        squad_info = squad_data["squads"][squad_name]
        matches_played = squad_info["wins"] + squad_info["losses"] + squad_info["draws"]
        wins = squad_info["wins"]
        losses = squad_info["losses"]
        draws = squad_info["draws"]
    
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

# -------------------- MODALS --------------------
class PlayerSetupModal(Modal, title="🎭 Royal Profile Setup"):
    ingame_name = TextInput(
        label="In-Game Name",
        placeholder="Enter your IGN",
        required=True,
        max_length=50
    )
    
    ingame_id = TextInput(
        label="In-Game ID",
        placeholder="Enter your game ID",
        required=True,
        max_length=50
    )
    
    highest_rank = TextInput(
        label="Highest Rank",
        placeholder="e.g., Mythic Glory, Legend, etc.",
        required=True,
        max_length=50
    )
    
    def __init__(self, user_id: int, squad_name: str, role: str):
        super().__init__()
        self.user_id = user_id
        self.squad_name = squad_name
        self.player_role = role
    
    async def on_submit(self, interaction: discord.Interaction):
        player_key = str(self.user_id)
        squad_data["players"][player_key] = {
            "discord_id": self.user_id,
            "ingame_name": self.ingame_name.value,
            "ingame_id": self.ingame_id.value,
            "highest_rank": self.highest_rank.value,
            "role": self.player_role,
            "squad": self.squad_name
        }
        save_data(squad_data)
        
        embed = discord.Embed(
            title="✅ Royal Profile Established",
            description=f"Your warrior profile has been inscribed in the royal archives!",
            color=ROYAL_GOLD
        )
        embed.add_field(name="⚔️ IGN", value=self.ingame_name.value, inline=True)
        embed.add_field(name="🎯 ID", value=self.ingame_id.value, inline=True)
        embed.add_field(name="🏆 Rank", value=self.highest_rank.value, inline=True)
        embed.add_field(name="💼 Role", value=f"{ROLE_EMOJIS.get(self.player_role, '⚔️')} {self.player_role}", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(
            interaction.guild,
            "🎭 Royal Profile Updated",
            f"{interaction.user.mention} updated their warrior profile"
        )

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
        
        team1_data = squad_data["squads"][self.team1.value]
        team2_data = squad_data["squads"][self.team2.value]
        
        if score1 > score2:
            team1_data["wins"] += 1
            team1_data["points"] += 2
            team2_data["losses"] += 1
            result_text = f"🏆 **{self.team1.value}** has conquered **{self.team2.value}** in glorious battle!"
        elif score2 > score1:
            team2_data["wins"] += 1
            team2_data["points"] += 2
            team1_data["losses"] += 1
            result_text = f"🏆 **{self.team2.value}** has conquered **{self.team1.value}** in glorious battle!"
        else:
            team1_data["draws"] += 1
            team1_data["points"] += 1
            team2_data["draws"] += 1
            team2_data["points"] += 1
            result_text = f"⚔️ **{self.team1.value}** and **{self.team2.value}** fought to an honorable stalemate!"
        
        # Generate unique match ID
        match_id = str(uuid.uuid4())[:8]
        
        match_data = {
            "match_id": match_id,
            "team1": self.team1.value,
            "team2": self.team2.value,
            "score": self.result.value,
            "date": datetime.utcnow().isoformat(),
            "added_by": interaction.user.id
        }
        
        squad_data["matches"].append(match_data)
        team1_data["match_history"].append(match_data)
        team2_data["match_history"].append(match_data)
        
        save_data(squad_data)
        
        embed = discord.Embed(
            title="📜 Battle Chronicles Updated",
            description=result_text,
            color=ROYAL_GOLD
        )
        embed.add_field(name="🆔 Match ID", value=f"`{match_id}`", inline=False)
        embed.add_field(name="⚔️ Score", value=f"**{self.result.value}**", inline=True)
        embed.add_field(
            name=f"{SQUADS[self.team1.value]} {self.team1.value}",
            value=f"💎 {team1_data['points']} points | 🏆 {team1_data['wins']}W ⚔️ {team1_data['draws']}D 💀 {team1_data['losses']}L",
            inline=False
        )
        embed.add_field(
            name=f"{SQUADS[self.team2.value]} {self.team2.value}",
            value=f"💎 {team2_data['points']} points | 🏆 {team2_data['wins']}W ⚔️ {team2_data['draws']}D 💀 {team2_data['losses']}L",
            inline=False
        )
        embed.set_footer(text=f"Match ID: {match_id} (save this to delete if needed)")
        
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
        modal = PlayerSetupModal(self.user_id, self.squad_name, selected_role)
        await interaction.response.send_modal(modal)

class SquadBrowserView(View):
    def __init__(self, guild):
        super().__init__(timeout=180)
        self.guild = guild
        
        options = []
        for squad_name, tag in sorted(SQUADS.items()):
            options.append(
                discord.SelectOption(
                    label=squad_name,
                    value=squad_name,
                    emoji="🏰",
                    description=f"Tag: {tag}"
                )
            )
        
        select = Select(
            placeholder="🏰 Choose a kingdom to explore...",
            options=options[:25],
            custom_id="squad_browser_select"
        )
        select.callback = self.squad_selected
        self.add_item(select)
    
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
            if player_data:
                role_emoji = ROLE_EMOJIS.get(player_data.get('role', ''), '⚔️')
                roster_text += f"{role_emoji} **{player_data.get('role', 'N/A')}**: {player_data.get('ingame_name', 'Unknown')} (#{player_data.get('ingame_id', 'N/A')}) - {player_data.get('highest_rank', 'Unranked')}\n"
        if roster_text:
            embed.add_field(name="⭐ Elite Warriors (Main Roster)", value=roster_text, inline=False)
    
    if subs:
        subs_text = ""
        for player_id in subs[:3]:
            player_data = squad_data["players"].get(str(player_id), {})
            if player_data:
                role_emoji = ROLE_EMOJIS.get(player_data.get('role', ''), '⚔️')
                subs_text += f"{role_emoji} **{player_data.get('role', 'N/A')}**: {player_data.get('ingame_name', 'Unknown')} (#{player_data.get('ingame_id', 'N/A')})\n"
        if subs_text:
            embed.add_field(name="🔄 Reserve Warriors (Substitutes)", value=subs_text, inline=False)
    
    # If no roster set, show all squad members
    if not main_roster and not subs and squad_role:
        all_members_text = ""
        for member in squad_role.members[:20]:  # Limit to 20
            player_data = squad_data["players"].get(str(member.id), {})
            if player_data:
                role_emoji = ROLE_EMOJIS.get(player_data.get('role', ''), '⚔️')
                all_members_text += f"{role_emoji} {player_data.get('ingame_name', member.display_name)}\n"
            else:
                all_members_text += f"⚔️ {member.display_name}\n"
        
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
    
    embed.set_footer(text="⚜️ Royal Squad Archives")
    
    await interaction.response.send_message(embed=embed, ephemeral=not public)

async def show_player_profile(interaction, member: discord.Member, public=False):
    """Display comprehensive player profile"""
    player_key = str(member.id)
    player_data = squad_data["players"].get(player_key)
    
    if not player_data:
        await interaction.response.send_message(
            f"❌ {member.mention} has not established their warrior profile yet.",
            ephemeral=True
        )
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
    embed.set_footer(text="⚜️ Glory to the warrior")
    
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
                description="*Commands available to all Royal warriors*",
                color=ROYAL_BLUE
            )
            embed.add_field(
                name="/members",
                value="📖 Open the member panel to browse squads, view rankings, setup your profile, and manage your squad membership\n*Example: `/members`*",
                inline=False
            )
            embed.add_field(
                name="/profile @user (optional)",
                value="🎭 View a warrior's profile publicly. Leave blank to view your own.\n*Example: `/profile` or `/profile @JohnDoe`*",
                inline=False
            )
            embed.add_field(
                name="/help",
                value="📜 Display this help guide\n*Example: `/help`*",
                inline=False
            )
            
        elif category == "leader":
            embed = discord.Embed(
                title="👑 Leader Commands",
                description="*Commands for managing your royal kingdom*",
                color=ROYAL_GOLD
            )
            embed.add_field(
                name="/leader",
                value="📖 Open the leader panel (includes Set Logo button)\n*Example: `/leader`*",
                inline=False
            )
            embed.add_field(
                name="/add_member @user",
                value="➕ Recruit a warrior to your kingdom\n*Example: `/add_member @JohnDoe`*",
                inline=False
            )
            embed.add_field(
                name="/remove_member @user",
                value="➖ Remove a warrior from your kingdom\n*Example: `/remove_member @JohnDoe`*",
                inline=False
            )
            embed.add_field(
                name="/set_main @user",
                value="⭐ Add a warrior to the elite main roster (max 5)\n*Example: `/set_main @JohnDoe`*",
                inline=False
            )
            embed.add_field(
                name="/remove_main @user",
                value="⭐ Remove a warrior from the main roster\n*Example: `/remove_main @JohnDoe`*",
                inline=False
            )
            embed.add_field(
                name="/set_sub @user",
                value="🔄 Add a warrior to the reserve substitutes (max 3)\n*Example: `/set_sub @JohnDoe`*",
                inline=False
            )
            embed.add_field(
                name="/remove_sub @user",
                value="🔄 Remove a warrior from substitutes\n*Example: `/remove_sub @JohnDoe`*",
                inline=False
            )
            embed.add_field(
                name="/promote_leader @user",
                value="👑 Bestow leadership upon a worthy warrior\n*Example: `/promote_leader @JohnDoe`*",
                inline=False
            )
            embed.add_field(
                name="/give_guest @user",
                value="🎭 Grant guest privileges to a visitor\n*Example: `/give_guest @JohnDoe`*",
                inline=False
            )
            embed.add_field(
                name="/remove_guest @user",
                value="🧹 Revoke guest privileges\n*Example: `/remove_guest @JohnDoe`*",
                inline=False
            )
            
        else:  # moderator
            embed = discord.Embed(
                title="🛡️ Moderator Commands",
                description="*Commands for overseeing the realm*",
                color=ROYAL_PURPLE
            )
            embed.add_field(
                name="/moderator",
                value="📖 Open the moderator panel to add match results\n*Example: `/moderator`*",
                inline=False
            )
            embed.add_field(
                name="/add_title squad_name title position",
                value="🏆 Award a title to a kingdom (position: 1st, 2nd, 3rd, etc.)\n*Example: `/add_title ROYALS Champion 1st`*",
                inline=False
            )
            embed.add_field(
                name="/set_squad_logo squad_name logo_url",
                value="🖼️ Set the royal emblem for any kingdom\n*Example: `/set_squad_logo ROYALS https://i.imgur.com/example.png`*",
                inline=False
            )
            embed.add_field(
                name="/delete_match match_id",
                value="🗑️ Delete a match result (get match ID from match recording)\n*Example: `/delete_match a1b2c3d4`*",
                inline=False
            )
            embed.add_field(
                name="/recent_matches limit",
                value="📜 View recent match results with IDs\n*Example: `/recent_matches 10`*",
                inline=False
            )
        
        embed.set_footer(text="⚜️ Royal Command Archives")
        await interaction.response.send_message(embed=embed, ephemeral=True)

class MemberPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Browse Kingdoms", style=discord.ButtonStyle.primary, emoji="🏰", row=0)
    async def browse_squads_button(self, interaction: discord.Interaction, button: Button):
        view = SquadBrowserView(interaction.guild)
        embed = discord.Embed(
            title="🏰 Kingdom Explorer",
            description="⚜️ Select a kingdom from the dropdown to view their Royal house!",
            color=ROYAL_BLUE
        )
        await interaction.response.send_message(embed=embed, view=view)
    
    @discord.ui.button(label="Rankings", style=discord.ButtonStyle.secondary, emoji="🏆", row=0)
    async def rankings_button(self, interaction: discord.Interaction, button: Button):
        rankings = get_squad_ranking()
        
        embed = discord.Embed(
            title="🏆 Royal Leaderboard",
            description="⚜️ *Current standings of the Royal houses*",
            color=ROYAL_GOLD
        )
        
        for squad in rankings[:20]:
            i = squad["rank"]
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"🏅 **{i}.**"
            embed.add_field(
                name=f"{medal} {squad['tag']} {squad['name']}",
                value=f"💎 **{squad['points']}** pts | 🏆 {squad['wins']}W-{squad['draws']}D-{squad['losses']}L | 📊 WR: **{squad['win_rate']:.1f}%**",
                inline=False
            )
        
        embed.set_footer(text="⚜️ Glory to the victorious!")
        await interaction.response.send_message(embed=embed)
    
    @discord.ui.button(label="My Kingdom", style=discord.ButtonStyle.success, emoji="🛡️", row=1)
    async def my_squad_button(self, interaction: discord.Interaction, button: Button):
        role, tag = get_member_squad(interaction.user, interaction.guild)
        if not role:
            await interaction.response.send_message("❌ You are not sworn to any kingdom, Royal warrior.", ephemeral=True)
            return
        
        await show_squad_info(interaction, role, role.name, tag, public=False)
    
    @discord.ui.button(label="My Profile", style=discord.ButtonStyle.success, emoji="🎭", row=1)
    async def my_profile_button(self, interaction: discord.Interaction, button: Button):
        await show_player_profile(interaction, interaction.user, public=True)
    
    @discord.ui.button(label="Setup Profile", style=discord.ButtonStyle.primary, emoji="⚙️", row=2)
    async def setup_profile_button(self, interaction: discord.Interaction, button: Button):
        # CHANGE 1: Allow all members to setup profiles, not just squad members
        role, _ = get_member_squad(interaction.user, interaction.guild)
        squad_name = role.name if role else "Free Agent"
        
        view = RoleSelectView(interaction.user.id, squad_name)
        embed = discord.Embed(
            title="🎭 Warrior Profile Setup",
            description="⚜️ Select your battle position to inscribe your legacy in the royal archives.",
            color=ROYAL_PURPLE
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Leave Kingdom", style=discord.ButtonStyle.danger, emoji="🚪", row=2)
    async def leave_squad_button(self, interaction: discord.Interaction, button: Button):
        role, _ = get_member_squad(interaction.user, interaction.guild)
        if not role:
            await interaction.response.send_message("❌ You are not sworn to any kingdom.", ephemeral=True)
            return
        
        # Update player profile - remove squad affiliation
        update_player_squad(interaction.user.id, None)
        
        await interaction.user.remove_roles(role)
        await safe_nick_update(interaction.user, None, None)
        await interaction.response.send_message(f"🚪 You have departed from **{role.name}**. Farewell, Royal warrior.", ephemeral=True)
        await log_action(
            interaction.guild,
            "🚪 Kingdom Departed",
            f"{interaction.user.mention} has left **{role.name}**"
        )

class LeaderPanelView(View):
    def __init__(self, squad_role, tag: str, squad_name: str, guest_role):
        super().__init__(timeout=None)
        self.squad_role = squad_role
        self.tag = tag
        self.squad_name = squad_name
        self.guest_role = guest_role
    
    @discord.ui.button(label="Set Royal Emblem", style=discord.ButtonStyle.primary, emoji="🖼️", row=0)
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

# -------------------- SLASH COMMANDS --------------------

# MEMBER COMMANDS
@bot.tree.command(name="members", description="👥 Access member panel - Browse kingdoms, rankings, and manage your profile")
async def members_panel(interaction: discord.Interaction):
    view = MemberPanelView()
    
    embed = discord.Embed(
        title="👥 Royal Member Hall",
        description="⚜️ *Welcome to the royal chambers, warrior. Use the buttons below to navigate.*",
        color=ROYAL_BLUE
    )
    embed.add_field(
        name="📜 Available Actions",
        value=(
            "🏰 Browse all kingdoms\n"
            "🏆 View royal leaderboard\n"
            "🛡️ View your kingdom\n"
            "🎭 View your profile publicly\n"
            "⚙️ Setup your warrior profile\n"
            "🚪 Depart from your kingdom"
        ),
        inline=False
    )
    embed.set_footer(text="⚜️ May honor guide your path")
    
    # CHANGE 2: Make member panel visible to everyone
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="profile", description="🎭 View a warrior's profile (leave blank for your own)")
async def profile_command(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    target = member or interaction.user
    await show_player_profile(interaction, target, public=True)

@bot.tree.command(name="help", description="📜 View all available commands and their usage")
async def help_command(interaction: discord.Interaction):
    view = HelpCategoryView()
    
    embed = discord.Embed(
        title="📜 Royal Command Archives",
        description="⚜️ *Select a category below to view available commands*",
        color=ROYAL_PURPLE
    )
    embed.add_field(
        name="👥 Member Commands",
        value="Commands available to all warriors",
        inline=False
    )
    embed.add_field(
        name="👑 Leader Commands",
        value="Commands for managing your kingdom",
        inline=False
    )
    embed.add_field(
        name="🛡️ Moderator Commands",
        value="Commands for tournament overseers",
        inline=False
    )
    embed.set_footer(text="⚜️ Knowledge is power")
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# LEADER COMMANDS
@bot.tree.command(name="leader", description="👑 Open leader panel to manage your kingdom")
async def leader_panel(interaction: discord.Interaction):
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
        description="⚜️ *Govern your kingdom wisely, Royal leader*",
        color=squad_role.color if squad_role.color != discord.Color.default() else ROYAL_GOLD
    )
    embed.add_field(
        name="📜 Available Commands",
        value=(
            "`/add_member @user` - Recruit a warrior\n"
            "`/remove_member @user` - Remove a warrior\n"
            "`/set_main @user` - Add to elite roster\n"
            "`/remove_main @user` - Remove from elite roster\n"
            "`/set_sub @user` - Add to reserves\n"
            "`/remove_sub @user` - Remove from reserves\n"
            "`/promote_leader @user` - Bestow leadership\n"
            "`/give_guest @user` - Grant guest privileges\n"
            "`/remove_guest @user` - Revoke guest privileges\n"
            "🖼️ Use the button below to set your royal emblem"
        ),
        inline=False
    )
    embed.set_footer(text="⚜️ Lead with honor and wisdom")
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="add_member", description="➕ Recruit a warrior to your kingdom")
async def add_member(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Only royal leaders may recruit warriors.", ephemeral=True)
        return
    
    squad_role, tag = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You must be sworn to a kingdom.", ephemeral=True)
        return
    
    # Remove from other squads
    for r_name in SQUADS:
        r = discord.utils.get(interaction.guild.roles, name=r_name)
        if r and r in member.roles:
            await member.remove_roles(r)
    
    await member.add_roles(squad_role)
    await safe_nick_update(member, squad_role, tag)
    
    # Update player profile squad
    update_player_squad(member.id, squad_role.name)
    
    embed = discord.Embed(
        title="✅ Warrior Recruited",
        description=f"⚜️ {member.mention} has sworn allegiance to **{squad_role.name}**!",
        color=ROYAL_GOLD
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_action(
        interaction.guild,
        "➕ Warrior Recruited",
        f"{interaction.user.mention} recruited {member.mention} to **{squad_role.name}**"
    )

@bot.tree.command(name="remove_member", description="➖ Remove a warrior from your kingdom")
async def remove_member(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Only royal leaders may dismiss warriors.", ephemeral=True)
        return
    
    squad_role, tag = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You must be sworn to a kingdom.", ephemeral=True)
        return
    
    if squad_role not in member.roles:
        await interaction.response.send_message("❌ This warrior is not sworn to your kingdom.", ephemeral=True)
        return
    
    # Remove from rosters
    squad_info = squad_data["squads"][squad_role.name]
    if member.id in squad_info.get("main_roster", []):
        squad_info["main_roster"].remove(member.id)
    if member.id in squad_info.get("subs", []):
        squad_info["subs"].remove(member.id)
    save_data(squad_data)
    
    # Update player profile
    update_player_squad(member.id, None)
    
    await member.remove_roles(squad_role)
    clean = remove_all_tags(member.display_name)
    try:
        await member.edit(nick=clean)
    except:
        pass
    
    embed = discord.Embed(
        title="➖ Warrior Dismissed",
        description=f"⚜️ {member.mention} has departed from **{squad_role.name}**.",
        color=ROYAL_PURPLE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_action(
        interaction.guild,
        "➖ Warrior Dismissed",
        f"{interaction.user.mention} removed {member.mention} from **{squad_role.name}**"
    )

@bot.tree.command(name="set_main", description="⭐ Add a warrior to the elite main roster")
async def set_main(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Only royal leaders may designate elite warriors.", ephemeral=True)
        return
    
    squad_role, tag = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You must be sworn to a kingdom.", ephemeral=True)
        return
    
    if squad_role not in member.roles:
        await interaction.response.send_message("❌ This warrior is not sworn to your kingdom.", ephemeral=True)
        return
    
    squad_info = squad_data["squads"][squad_role.name]
    
    if member.id in squad_info["main_roster"]:
        await interaction.response.send_message("⚠️ This warrior is already in the elite roster.", ephemeral=True)
        return
    
    if len(squad_info["main_roster"]) >= 5:
        await interaction.response.send_message("❌ The elite roster is full (maximum 5 warriors).", ephemeral=True)
        return
    
    # Remove from subs if present
    if member.id in squad_info["subs"]:
        squad_info["subs"].remove(member.id)
    
    squad_info["main_roster"].append(member.id)
    save_data(squad_data)
    
    embed = discord.Embed(
        title="⭐ Elite Warrior Designated",
        description=f"⚜️ {member.mention} has been elevated to the elite main roster!",
        color=ROYAL_GOLD
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_action(
        interaction.guild,
        "⭐ Elite Warrior Added",
        f"{interaction.user.mention} added {member.mention} to main roster of **{squad_role.name}**"
    )

@bot.tree.command(name="remove_main", description="⭐ Remove a warrior from the main roster")
async def remove_main(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Only royal leaders may manage the elite roster.", ephemeral=True)
        return
    
    squad_role, tag = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You must be sworn to a kingdom.", ephemeral=True)
        return
    
    squad_info = squad_data["squads"][squad_role.name]
    
    if member.id not in squad_info["main_roster"]:
        await interaction.response.send_message("❌ This warrior is not in the main roster.", ephemeral=True)
        return
    
    squad_info["main_roster"].remove(member.id)
    save_data(squad_data)
    
    embed = discord.Embed(
        title="⭐ Removed from Elite Roster",
        description=f"⚜️ {member.mention} has been removed from the main roster.",
        color=ROYAL_BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_action(
        interaction.guild,
        "⭐ Main Roster Updated",
        f"{interaction.user.mention} removed {member.mention} from main roster of **{squad_role.name}**"
    )

@bot.tree.command(name="set_sub", description="🔄 Add a warrior to the reserve substitutes")
async def set_sub(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Only royal leaders may designate reserve warriors.", ephemeral=True)
        return
    
    squad_role, tag = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You must be sworn to a kingdom.", ephemeral=True)
        return
    
    if squad_role not in member.roles:
        await interaction.response.send_message("❌ This warrior is not sworn to your kingdom.", ephemeral=True)
        return
    
    squad_info = squad_data["squads"][squad_role.name]
    
    if member.id in squad_info["subs"]:
        await interaction.response.send_message("⚠️ This warrior is already in the reserves.", ephemeral=True)
        return
    
    if len(squad_info["subs"]) >= 3:
        await interaction.response.send_message("❌ The reserves are full (maximum 3 warriors).", ephemeral=True)
        return
    
    # Remove from main if present
    if member.id in squad_info["main_roster"]:
        squad_info["main_roster"].remove(member.id)
    
    squad_info["subs"].append(member.id)
    save_data(squad_data)
    
    embed = discord.Embed(
        title="🔄 Reserve Warrior Designated",
        description=f"⚜️ {member.mention} has been assigned to the reserve substitutes!",
        color=ROYAL_BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_action(
        interaction.guild,
        "🔄 Reserve Warrior Added",
        f"{interaction.user.mention} added {member.mention} to substitutes of **{squad_role.name}**"
    )

@bot.tree.command(name="remove_sub", description="🔄 Remove a warrior from the substitutes")
async def remove_sub(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Only royal leaders may manage reserves.", ephemeral=True)
        return
    
    squad_role, tag = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You must be sworn to a kingdom.", ephemeral=True)
        return
    
    squad_info = squad_data["squads"][squad_role.name]
    
    if member.id not in squad_info["subs"]:
        await interaction.response.send_message("❌ This warrior is not in the substitutes.", ephemeral=True)
        return
    
    squad_info["subs"].remove(member.id)
    save_data(squad_data)
    
    embed = discord.Embed(
        title="🔄 Removed from Reserves",
        description=f"⚜️ {member.mention} has been removed from the substitutes.",
        color=ROYAL_BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_action(
        interaction.guild,
        "🔄 Substitutes Updated",
        f"{interaction.user.mention} removed {member.mention} from substitutes of **{squad_role.name}**"
    )

@bot.tree.command(name="promote_leader", description="👑 Bestow leadership upon a worthy warrior")
async def promote_leader(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Only royal leaders may bestow leadership.", ephemeral=True)
        return
    
    squad_role, tag = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You must be sworn to a kingdom.", ephemeral=True)
        return
    
    if squad_role not in member.roles:
        await interaction.response.send_message("❌ This warrior is not sworn to your kingdom.", ephemeral=True)
        return
    
    leader_role_obj = discord.utils.get(interaction.guild.roles, name=LEADER_ROLE_NAME)
    if not leader_role_obj:
        await interaction.response.send_message("❌ The LEADER role does not exist.", ephemeral=True)
        return
    
    await member.add_roles(leader_role_obj)
    
    embed = discord.Embed(
        title="👑 Leadership Bestowed",
        description=f"⚜️ {member.mention} has been crowned as a royal leader of **{squad_role.name}**!",
        color=ROYAL_GOLD
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_action(
        interaction.guild,
        "👑 Leadership Bestowed",
        f"{interaction.user.mention} promoted {member.mention} to LEADER"
    )

@bot.tree.command(name="give_guest", description="🎭 Grant guest privileges to a visitor")
async def give_guest(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Only royal leaders may grant guest privileges.", ephemeral=True)
        return
    
    squad_role, tag = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You must be sworn to a kingdom.", ephemeral=True)
        return
    
    guest_role_name = GUEST_ROLES.get(squad_role.name)
    if not guest_role_name:
        await interaction.response.send_message("❌ Guest role not configured for your kingdom.", ephemeral=True)
        return
    
    guest_role = discord.utils.get(interaction.guild.roles, name=guest_role_name)
    if not guest_role:
        await interaction.response.send_message(f"❌ Guest role `{guest_role_name}` does not exist.", ephemeral=True)
        return
    
    # Remove other guest roles
    for r in member.roles:
        if r.name.endswith("_guest"):
            await member.remove_roles(r)
    
    await member.add_roles(guest_role)
    
    embed = discord.Embed(
        title="🎭 Guest Privileges Granted",
        description=f"⚜️ {member.mention} is now an honored guest of **{squad_role.name}**!",
        color=ROYAL_PURPLE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_action(
        interaction.guild,
        "🎭 Guest Welcomed",
        f"{interaction.user.mention} granted guest privileges to {member.mention}"
    )

@bot.tree.command(name="remove_guest", description="🧹 Revoke guest privileges from a visitor")
async def remove_guest(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Only royal leaders may revoke guest privileges.", ephemeral=True)
        return
    
    squad_role, tag = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You must be sworn to a kingdom.", ephemeral=True)
        return
    
    guest_role_name = GUEST_ROLES.get(squad_role.name)
    if not guest_role_name:
        await interaction.response.send_message("❌ Guest role not configured for your kingdom.", ephemeral=True)
        return
    
    guest_role = discord.utils.get(interaction.guild.roles, name=guest_role_name)
    if not guest_role:
        await interaction.response.send_message(f"❌ Guest role `{guest_role_name}` does not exist.", ephemeral=True)
        return
    
    if guest_role not in member.roles:
        await interaction.response.send_message("❌ This person is not a guest of your kingdom.", ephemeral=True)
        return
    
    await member.remove_roles(guest_role)
    
    embed = discord.Embed(
        title="🧹 Guest Privileges Revoked",
        description=f"⚜️ Guest privileges have been removed from {member.mention}.",
        color=ROYAL_BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_action(
        interaction.guild,
        "🧹 Guest Dismissed",
        f"{interaction.user.mention} removed guest privileges from {member.mention}"
    )

# MODERATOR COMMANDS
@bot.tree.command(name="moderator", description="🛡️ Open moderator panel to oversee the realm")
async def moderator_panel(interaction: discord.Interaction):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("❌ Only royal moderators may access this chamber.", ephemeral=True)
        return
    
    view = ModeratorPanelView()
    
    embed = discord.Embed(
        title="🛡️ Royal Overseer Chamber",
        description="⚜️ *Manage the realm's tournaments and records*",
        color=ROYAL_PURPLE
    )
    embed.add_field(
        name="📜 Available Commands",
        value=(
            "⚔️ Record battle results (use button above)\n"
            "`/add_title squad_name title position` - Award titles\n"
            "`/set_squad_logo squad_name url` - Set kingdom emblems\n"
            "`/delete_match match_id` - Delete a match result\n"
            "`/recent_matches limit` - View recent matches with IDs"
        ),
        inline=False
    )
    embed.set_footer(text="⚜️ Govern with fairness and strength")
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="add_title", description="🏆 Award a championship title to a kingdom")
async def add_title(
    interaction: discord.Interaction,
    squad_name: str,
    title: str,
    position: str
):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("❌ Only royal moderators may award titles.", ephemeral=True)
        return
    
    if squad_name not in SQUADS:
        await interaction.response.send_message(
            f"❌ Kingdom `{squad_name}` not found. Use exact squad name.",
            ephemeral=True
        )
        return
    
    squad_info = squad_data["squads"][squad_name]
    
    # Format the title with position
    full_title = f"{title} ({position} Place)"
    
    # Add title to list
    if "titles" not in squad_info:
        squad_info["titles"] = []
    
    squad_info["titles"].append(full_title)
    
    # Increment championship wins for 1st place
    if position.lower() in ["1st", "first", "1"]:
        squad_info["championship_wins"] = squad_info.get("championship_wins", 0) + 1
    
    save_data(squad_data)
    
    # Determine emoji based on position
    position_emoji = "🥇" if position.lower() in ["1st", "first", "1"] else "🥈" if position.lower() in ["2nd", "second", "2"] else "🥉"
    
    embed = discord.Embed(
        title="🏆 Royal Title Bestowed",
        description=f"{position_emoji} **{squad_name}** has been awarded the title:\n\n**{full_title}**",
        color=ROYAL_GOLD
    )
    
    if position.lower() in ["1st", "first", "1"]:
        embed.add_field(
            name="👑 Championship Glory",
            value=f"Total Championships: **{squad_info['championship_wins']}**",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)
    await log_action(
        interaction.guild,
        "🏆 Title Awarded",
        f"{interaction.user.mention} awarded **{squad_name}** the title: {full_title}"
    )

@bot.tree.command(name="set_squad_logo", description="🖼️ Set the royal emblem for any kingdom")
async def set_squad_logo(
    interaction: discord.Interaction,
    squad_name: str,
    logo_url: str
):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("❌ Only royal moderators may set kingdom emblems.", ephemeral=True)
        return
    
    if squad_name not in SQUADS:
        await interaction.response.send_message(
            f"❌ Kingdom `{squad_name}` not found. Use exact squad name.",
            ephemeral=True
        )
        return
    
    squad_data["squads"][squad_name]["logo_url"] = logo_url
    save_data(squad_data)
    
    embed = discord.Embed(
        title="✅ Royal Emblem Established",
        description=f"The crest of **{squad_name}** has been emblazoned!",
        color=ROYAL_GOLD
    )
    embed.set_thumbnail(url=logo_url)
    
    await interaction.response.send_message(embed=embed)
    await log_action(
        interaction.guild,
        "🖼️ Emblem Set",
        f"{interaction.user.mention} set the royal emblem for **{squad_name}**"
    )

@bot.tree.command(name="delete_match", description="🗑️ Delete a match result by ID")
async def delete_match(interaction: discord.Interaction, match_id: str):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("❌ Only royal moderators may delete matches.", ephemeral=True)
        return
    
    index, match = find_match_by_id(match_id)
    
    if match is None:
        await interaction.response.send_message(f"❌ Match with ID `{match_id}` not found.", ephemeral=True)
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
    team1_data["match_history"] = [m for m in team1_data["match_history"] if m.get("match_id") != match_id]
    team2_data["match_history"] = [m for m in team2_data["match_history"] if m.get("match_id") != match_id]
    
    save_data(squad_data)
    
    embed = discord.Embed(
        title="🗑️ Match Deleted",
        description=f"⚜️ Match between **{team1}** and **{team2}** has been erased from the chronicles.",
        color=ROYAL_RED
    )
    embed.add_field(name="Match ID", value=f"`{match_id}`", inline=True)
    embed.add_field(name="Score", value=score, inline=True)
    embed.set_footer(text="Points and records have been adjusted")
    
    await interaction.response.send_message(embed=embed)
    await log_action(
        interaction.guild,
        "🗑️ Match Deleted",
        f"{interaction.user.mention} deleted match {match_id}: {team1} vs {team2} ({score})"
    )

@bot.tree.command(name="recent_matches", description="📜 View recent match results")
async def recent_matches(interaction: discord.Interaction, limit: int = 10):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("❌ Only royal moderators may view match records.", ephemeral=True)
        return
    
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
    
    embed.set_footer(text="Use /delete_match <match_id> to remove a match")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# -------------------- RUN --------------------
bot.run(os.getenv("DISCORD_TOKEN"))
