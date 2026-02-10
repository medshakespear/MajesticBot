import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select, Modal, TextInput
import asyncio
import os
import json
from datetime import datetime
from typing import Optional

# -------------------- INTENTS --------------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------- CONFIG --------------------
LEADER_ROLE_NAME = "LEADER"
MODERATOR_ROLE_NAME = "MODERATOR"
DATA_FILE = "squad_data.json"

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
        color=discord.Color.blurple(),
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Squad Bot Logs")
    
    try:
        await channel.send(embed=embed)
    except Exception as e:
        print(f"[LOGGING ERROR] {e}")

# -------------------- HELPERS --------------------
async def wait_for_mention(interaction: discord.Interaction, timeout=30):
    def check(msg: discord.Message):
        return (
            msg.author.id == interaction.user.id
            and msg.channel.id == interaction.channel.id
            and len(msg.mentions) == 1
        )

    try:
        msg = await bot.wait_for("message", check=check, timeout=timeout)
        return msg.mentions[0]
    except asyncio.TimeoutError:
        return None


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

def get_squad_ranking():
    """Get squads sorted by points"""
    rankings = []
    for squad_name, data in squad_data["squads"].items():
        rankings.append({
            "name": squad_name,
            "tag": SQUADS[squad_name],
            "points": data["points"],
            "wins": data["wins"],
            "draws": data["draws"],
            "losses": data["losses"]
        })
    
    return sorted(rankings, key=lambda x: x["points"], reverse=True)

# -------------------- MODALS --------------------
class PlayerSetupModal(Modal, title="Player Profile Setup"):
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
            title="✅ Profile Updated",
            description=f"Your player profile has been set up successfully!",
            color=discord.Color.green()
        )
        embed.add_field(name="IGN", value=self.ingame_name.value, inline=True)
        embed.add_field(name="ID", value=self.ingame_id.value, inline=True)
        embed.add_field(name="Rank", value=self.highest_rank.value, inline=True)
        embed.add_field(name="Role", value=self.player_role, inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(
            interaction.guild,
            "👤 Player Profile Updated",
            f"{interaction.user.mention} updated their player profile"
        )

class AddMatchModal(Modal, title="Add Match Result"):
    team1 = TextInput(
        label="Team 1 Name",
        placeholder="Enter exact squad name",
        required=True
    )
    
    team2 = TextInput(
        label="Team 2 Name",
        placeholder="Enter exact squad name",
        required=True
    )
    
    result = TextInput(
        label="Result (team1_score-team2_score)",
        placeholder="e.g., 2-0, 1-1, 0-2",
        required=True,
        max_length=10
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.team1.value not in SQUADS or self.team2.value not in SQUADS:
            await interaction.response.send_message(
                "❌ One or both team names are invalid. Use exact squad names.",
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
            result_text = f"🏆 **{self.team1.value}** defeated **{self.team2.value}**"
        elif score2 > score1:
            team2_data["wins"] += 1
            team2_data["points"] += 2
            team1_data["losses"] += 1
            result_text = f"🏆 **{self.team2.value}** defeated **{self.team1.value}**"
        else:
            team1_data["draws"] += 1
            team1_data["points"] += 1
            team2_data["draws"] += 1
            team2_data["points"] += 1
            result_text = f"🤝 **{self.team1.value}** drew with **{self.team2.value}**"
        
        match_data = {
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
            title="📊 Match Result Added",
            description=result_text,
            color=discord.Color.gold()
        )
        embed.add_field(name="Score", value=f"**{self.result.value}**", inline=True)
        embed.add_field(
            name=f"{SQUADS[self.team1.value]} {self.team1.value}",
            value=f"Points: {team1_data['points']} | W: {team1_data['wins']} D: {team1_data['draws']} L: {team1_data['losses']}",
            inline=False
        )
        embed.add_field(
            name=f"{SQUADS[self.team2.value]} {self.team2.value}",
            value=f"Points: {team2_data['points']} | W: {team2_data['wins']} D: {team2_data['draws']} L: {team2_data['losses']}",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
        await log_action(
            interaction.guild,
            "📊 Match Result Added",
            f"{interaction.user.mention} added: {self.team1.value} vs {self.team2.value} ({self.result.value})"
        )

class SetLogoModal(Modal, title="Set Squad Logo"):
    logo_url = TextInput(
        label="Logo URL",
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
            title="✅ Logo Updated",
            description=f"Logo set for **{self.squad_name}**",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=self.logo_url.value)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_action(
            interaction.guild,
            "🖼️ Logo Updated",
            f"{interaction.user.mention} updated logo for **{self.squad_name}**"
        )

class ManageRosterModal(Modal):
    member_id = TextInput(
        label="Member ID or @mention",
        placeholder="Right-click user > Copy ID",
        required=True
    )
    
    def __init__(self, squad_name: str, roster_type: str):
        super().__init__(title=f"Add to {'Main Roster' if roster_type == 'main' else 'Substitutes'}")
        self.squad_name = squad_name
        self.roster_type = roster_type
    
    async def on_submit(self, interaction: discord.Interaction):
        member_id_str = self.member_id.value.strip('<@!> ')
        try:
            member_id = int(member_id_str)
            member = interaction.guild.get_member(member_id)
        except:
            await interaction.response.send_message("❌ Invalid member ID.", ephemeral=True)
            return
        
        if not member:
            await interaction.response.send_message("❌ Member not found.", ephemeral=True)
            return
        
        squad_info = squad_data["squads"][self.squad_name]
        
        if self.roster_type == "main":
            if member.id in squad_info["main_roster"]:
                await interaction.response.send_message("⚠️ Already in main roster.", ephemeral=True)
                return
            if len(squad_info["main_roster"]) >= 5:
                await interaction.response.send_message("❌ Main roster full (max 5).", ephemeral=True)
                return
            
            if member.id in squad_info["subs"]:
                squad_info["subs"].remove(member.id)
            squad_info["main_roster"].append(member.id)
            msg = f"⭐ {member.mention} added to main roster!"
        else:
            if member.id in squad_info["subs"]:
                await interaction.response.send_message("⚠️ Already a substitute.", ephemeral=True)
                return
            if len(squad_info["subs"]) >= 3:
                await interaction.response.send_message("❌ Subs full (max 3).", ephemeral=True)
                return
            
            if member.id in squad_info["main_roster"]:
                squad_info["main_roster"].remove(member.id)
            squad_info["subs"].append(member.id)
            msg = f"🔄 {member.mention} added to substitutes!"
        
        save_data(squad_data)
        await interaction.response.send_message(msg, ephemeral=True)

class ManageMemberModal(Modal):
    member_id = TextInput(
        label="Member ID or @mention",
        placeholder="Right-click user > Copy ID",
        required=True
    )
    
    def __init__(self, squad_role, tag: str, action: str):
        super().__init__(title=f"{'Add' if action == 'add' else 'Remove'} Member")
        self.squad_role = squad_role
        self.tag = tag
        self.action = action
    
    async def on_submit(self, interaction: discord.Interaction):
        member_id_str = self.member_id.value.strip('<@!> ')
        try:
            member_id = int(member_id_str)
            member = interaction.guild.get_member(member_id)
        except:
            await interaction.response.send_message("❌ Invalid member ID.", ephemeral=True)
            return
        
        if not member:
            await interaction.response.send_message("❌ Member not found.", ephemeral=True)
            return
        
        if self.action == "add":
            for r_name in SQUADS:
                r = discord.utils.get(interaction.guild.roles, name=r_name)
                if r and r in member.roles:
                    await member.remove_roles(r)
            
            await member.add_roles(self.squad_role)
            await safe_nick_update(member, self.squad_role, self.tag)
            await interaction.response.send_message(f"✅ {member.mention} added to **{self.squad_role.name}**", ephemeral=True)
            await log_action(
                interaction.guild,
                "➕ Member Added",
                f"{interaction.user.mention} added {member.mention} to **{self.squad_role.name}**"
            )
        else:
            if self.squad_role not in member.roles:
                await interaction.response.send_message("❌ Member not in your squad.", ephemeral=True)
                return
            
            await member.remove_roles(self.squad_role)
            clean = remove_all_tags(member.display_name)
            try:
                await member.edit(nick=clean)
            except:
                pass
            await interaction.response.send_message(f"➖ {member.mention} removed from **{self.squad_role.name}**", ephemeral=True)
            await log_action(
                interaction.guild,
                "➖ Member Removed",
                f"{interaction.user.mention} removed {member.mention} from **{self.squad_role.name}**"
            )

class ManageGuestModal(Modal):
    member_id = TextInput(
        label="Member ID or @mention",
        placeholder="Right-click user > Copy ID",
        required=True
    )
    
    def __init__(self, guest_role, action: str):
        super().__init__(title=f"{'Give' if action == 'give' else 'Remove'} Guest Role")
        self.guest_role = guest_role
        self.action = action
    
    async def on_submit(self, interaction: discord.Interaction):
        member_id_str = self.member_id.value.strip('<@!> ')
        try:
            member_id = int(member_id_str)
            member = interaction.guild.get_member(member_id)
        except:
            await interaction.response.send_message("❌ Invalid member ID.", ephemeral=True)
            return
        
        if not member:
            await interaction.response.send_message("❌ Member not found.", ephemeral=True)
            return
        
        if self.action == "give":
            for r in member.roles:
                if r.name.endswith("_guest"):
                    await member.remove_roles(r)
            await member.add_roles(self.guest_role)
            await interaction.response.send_message(f"🎟️ {member.mention} is now a guest!", ephemeral=True)
        else:
            if self.guest_role not in member.roles:
                await interaction.response.send_message("❌ Not a guest.", ephemeral=True)
                return
            await member.remove_roles(self.guest_role)
            await interaction.response.send_message(f"🧹 Guest role removed from {member.mention}", ephemeral=True)

class PromoteLeaderModal(Modal, title="Promote to Leader"):
    member_id = TextInput(
        label="Member ID or @mention",
        placeholder="Right-click user > Copy ID",
        required=True
    )
    
    def __init__(self, squad_role):
        super().__init__()
        self.squad_role = squad_role
    
    async def on_submit(self, interaction: discord.Interaction):
        member_id_str = self.member_id.value.strip('<@!> ')
        try:
            member_id = int(member_id_str)
            member = interaction.guild.get_member(member_id)
        except:
            await interaction.response.send_message("❌ Invalid member ID.", ephemeral=True)
            return
        
        if not member or self.squad_role not in member.roles:
            await interaction.response.send_message("❌ Member not in your squad.", ephemeral=True)
            return
        
        leader_role_obj = discord.utils.get(interaction.guild.roles, name=LEADER_ROLE_NAME)
        await member.add_roles(leader_role_obj)
        await interaction.response.send_message(f"⭐ {member.mention} promoted to LEADER!", ephemeral=True)
        await log_action(
            interaction.guild,
            "⭐ Leader Promoted",
            f"{interaction.user.mention} promoted {member.mention} to LEADER"
        )

# -------------------- VIEWS --------------------
class RoleSelectView(View):
    def __init__(self, user_id: int, squad_name: str):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.squad_name = squad_name
        
        options = [
            discord.SelectOption(label=role, emoji="⚔️" if role == "Jungler" else "🎮")
            for role in ROLES
        ]
        
        select = Select(
            placeholder="Choose your role...",
            options=options,
            custom_id="role_select"
        )
        select.callback = self.role_selected
        self.add_item(select)
    
    async def role_selected(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your setup panel.", ephemeral=True)
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
                    emoji=tag if len(tag) <= 2 else "🛡️",
                    description=f"Tag: {tag}"
                )
            )
        
        select = Select(
            placeholder="🔍 Choose a squad to view...",
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
    """Shared function to display squad information"""
    squad_info = squad_data["squads"].get(squad_name, {})
    
    embed = discord.Embed(
        title=f"🛡️ {squad_name}",
        color=squad_role.color if squad_role else discord.Color.blue()
    )
    
    embed.add_field(name="Tag", value=f"`{tag}`", inline=True)
    embed.add_field(name="Points", value=f"**{squad_info.get('points', 0)}**", inline=True)
    embed.add_field(name="Members", value=len(squad_role.members) if squad_role else 0, inline=True)
    
    wins = squad_info.get('wins', 0)
    draws = squad_info.get('draws', 0)
    losses = squad_info.get('losses', 0)
    embed.add_field(
        name="Record",
        value=f"🟢 {wins}W - 🟡 {draws}D - 🔴 {losses}L",
        inline=False
    )
    
    champ_wins = squad_info.get('championship_wins', 0)
    titles = squad_info.get('titles', [])
    if champ_wins > 0:
        embed.add_field(name="Championships", value=f"🏆 {champ_wins}", inline=True)
    if titles:
        embed.add_field(name="Titles", value=", ".join(titles), inline=False)
    
    main_roster = squad_info.get('main_roster', [])
    if main_roster:
        roster_text = ""
        for player_id in main_roster[:5]:
            player_data = squad_data["players"].get(str(player_id), {})
            if player_data:
                roster_text += f"**{player_data.get('role', 'N/A')}**: {player_data.get('ingame_name', 'Unknown')} (#{player_data.get('ingame_id', 'N/A')}) - {player_data.get('highest_rank', 'N/A')}\n"
        if roster_text:
            embed.add_field(name="⭐ Main Roster", value=roster_text, inline=False)
    
    subs = squad_info.get('subs', [])
    if subs:
        subs_text = ""
        for player_id in subs[:3]:
            player_data = squad_data["players"].get(str(player_id), {})
            if player_data:
                subs_text += f"**{player_data.get('role', 'N/A')}**: {player_data.get('ingame_name', 'Unknown')}\n"
        if subs_text:
            embed.add_field(name="🔄 Substitutes", value=subs_text, inline=False)
    
    leaders = get_leaders_for_squad(interaction.guild, squad_role) if squad_role else []
    if leaders:
        embed.add_field(name="👑 Leaders", value=", ".join(leaders), inline=False)
    
    guest_role_name = GUEST_ROLES.get(squad_name)
    if guest_role_name:
        guest_role = discord.utils.get(interaction.guild.roles, name=guest_role_name)
        if guest_role and guest_role.members:
            guests = [m.display_name for m in guest_role.members[:10]]
            embed.add_field(name="🎟️ Guests", value=", ".join(guests), inline=False)
    
    logo_url = squad_info.get('logo_url')
    if logo_url:
        embed.set_thumbnail(url=logo_url)
    
    await interaction.response.send_message(embed=embed, ephemeral=not public)

class MemberPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Browse Squads", style=discord.ButtonStyle.primary, emoji="🔍", row=0)
    async def browse_squads_button(self, interaction: discord.Interaction, button: Button):
        view = SquadBrowserView(interaction.guild)
        embed = discord.Embed(
            title="🔍 Squad Browser",
            description="Select a squad from the dropdown to view their full information!",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view)
    
    @discord.ui.button(label="Rankings", style=discord.ButtonStyle.secondary, emoji="🏆", row=0)
    async def rankings_button(self, interaction: discord.Interaction, button: Button):
        rankings = get_squad_ranking()
        
        embed = discord.Embed(
            title="🏆 Squad Rankings",
            description="Current standings based on match performance",
            color=discord.Color.gold()
        )
        
        for i, squad in enumerate(rankings[:20], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            embed.add_field(
                name=f"{medal} {squad['tag']} {squad['name']}",
                value=f"**{squad['points']}** points | {squad['wins']}W-{squad['draws']}D-{squad['losses']}L",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @discord.ui.button(label="My Squad", style=discord.ButtonStyle.success, emoji="🛡️", row=1)
    async def my_squad_button(self, interaction: discord.Interaction, button: Button):
        role, tag = get_member_squad(interaction.user, interaction.guild)
        if not role:
            await interaction.response.send_message("❌ You are not in a squad.", ephemeral=True)
            return
        
        await show_squad_info(interaction, role, role.name, tag, public=False)
    
    @discord.ui.button(label="Setup Profile", style=discord.ButtonStyle.success, emoji="⚙️", row=1)
    async def setup_profile_button(self, interaction: discord.Interaction, button: Button):
        role, _ = get_member_squad(interaction.user, interaction.guild)
        if not role:
            await interaction.response.send_message("❌ You must be in a squad to set up your profile.", ephemeral=True)
            return
        
        view = RoleSelectView(interaction.user.id, role.name)
        embed = discord.Embed(
            title="⚙️ Player Profile Setup",
            description="Select your role to continue setting up your profile.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Leave Squad", style=discord.ButtonStyle.danger, emoji="🚪", row=2)
    async def leave_squad_button(self, interaction: discord.Interaction, button: Button):
        role, _ = get_member_squad(interaction.user, interaction.guild)
        if not role:
            await interaction.response.send_message("❌ You are not in a squad.", ephemeral=True)
            return
        
        await interaction.user.remove_roles(role)
        await safe_nick_update(interaction.user, None, None)
        await interaction.response.send_message("➖ You left your squad.", ephemeral=True)
        await log_action(
            interaction.guild,
            "🚪 Squad Left",
            f"{interaction.user.mention} left **{role.name}**"
        )

class LeaderPanelView(View):
    def __init__(self, squad_role, tag: str, squad_name: str, guest_role):
        super().__init__(timeout=None)
        self.squad_role = squad_role
        self.tag = tag
        self.squad_name = squad_name
        self.guest_role = guest_role
    
    @discord.ui.button(label="Add Member", style=discord.ButtonStyle.success, emoji="➕", row=0)
async def add_member_button(self, interaction: discord.Interaction, button: Button):
    await interaction.response.send_message(
        "👑 **Mention the player to ADD to your squad** (`@player`)",
        ephemeral=True
    )

    member = await wait_for_mention(interaction)
    if not member:
        return await interaction.followup.send("⏰ Time expired. Try again.", ephemeral=True)

    # Remove other squad roles
    for r_name in SQUADS:
        r = discord.utils.get(interaction.guild.roles, name=r_name)
        if r and r in member.roles:
            await member.remove_roles(r)

    await member.add_roles(self.squad_role)
    await safe_nick_update(member, self.squad_role, self.tag)

    await interaction.followup.send(
        f"📜 **Royal Order Executed**\n{member.mention} has joined **{self.squad_name}** 👑"
    )
    
    @discord.ui.button(label="Remove Member", style=discord.ButtonStyle.danger, emoji="➖", row=0)
    async def remove_member_button(self, interaction: discord.Interaction, button: Button):
        modal = ManageMemberModal(self.squad_role, self.tag, "remove")
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Set Main Roster", style=discord.ButtonStyle.primary, emoji="⭐", row=1)
    async def set_main_button(self, interaction: discord.Interaction, button: Button):
        modal = ManageRosterModal(self.squad_name, "main")
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Set Substitute", style=discord.ButtonStyle.primary, emoji="🔄", row=1)
    async def set_sub_button(self, interaction: discord.Interaction, button: Button):
        modal = ManageRosterModal(self.squad_name, "sub")
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Promote Leader", style=discord.ButtonStyle.secondary, emoji="👑", row=2)
    async def promote_leader_button(self, interaction: discord.Interaction, button: Button):
        modal = PromoteLeaderModal(self.squad_role)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Give Guest", style=discord.ButtonStyle.secondary, emoji="🎟️", row=2)
    async def give_guest_button(self, interaction: discord.Interaction, button: Button):
        if not self.guest_role:
            await interaction.response.send_message("❌ Guest role not configured.", ephemeral=True)
            return
        modal = ManageGuestModal(self.guest_role, "give")
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Remove Guest", style=discord.ButtonStyle.secondary, emoji="🧹", row=3)
    async def remove_guest_button(self, interaction: discord.Interaction, button: Button):
        if not self.guest_role:
            await interaction.response.send_message("❌ Guest role not configured.", ephemeral=True)
            return
        modal = ManageGuestModal(self.guest_role, "remove")
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Set Logo", style=discord.ButtonStyle.secondary, emoji="🖼️", row=3)
    async def set_logo_button(self, interaction: discord.Interaction, button: Button):
        modal = SetLogoModal(self.squad_name)
        await interaction.response.send_modal(modal)

class ModeratorPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Add Match Result", style=discord.ButtonStyle.primary, emoji="📊", row=0)
    async def add_match_button(self, interaction: discord.Interaction, button: Button):
        modal = AddMatchModal()
        await interaction.response.send_modal(modal)

# -------------------- READY --------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    safety_sync.start()
    print(f"✅ Logged in as {bot.user}")
    
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

# -------------------- MAIN COMMANDS (3 PANELS) --------------------
@bot.tree.command(name="members", description="Member panel - Browse squads, rankings, and manage your profile")
async def members_panel(interaction: discord.Interaction):
    view = MemberPanelView()
    
    embed = discord.Embed(
        title="👥 Member Panel",
        description="Use the buttons below to access member features",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Available Actions",
        value="🔍 Browse all squads\n🏆 View rankings\n🛡️ View your squad\n⚙️ Setup your player profile\n🚪 Leave your squad",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="leader", description="Leader panel - Manage your squad (Leaders only)")
async def leader_panel(interaction: discord.Interaction):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ This command is for squad leaders only.", ephemeral=True)
        return
    
    squad_role, tag = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You are not in a squad.", ephemeral=True)
        return
    
    guest_role_name = GUEST_ROLES.get(squad_role.name)
    guest_role = discord.utils.get(interaction.guild.roles, name=guest_role_name) if guest_role_name else None
    
    view = LeaderPanelView(squad_role, tag, squad_role.name, guest_role)
    
    embed = discord.Embed(
        title=f"👑 Leader Panel - {squad_role.name}",
        description="Manage your squad using the buttons below",
        color=squad_role.color
    )
    embed.add_field(
        name="Available Actions",
        value="➕ Add members\n➖ Remove members\n⭐ Set main roster (max 5)\n🔄 Set substitutes (max 3)\n👑 Promote to leader\n🎟️ Manage guests\n🖼️ Set squad logo",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="moderator", description="Moderator panel - Manage matches and standings (Moderators only)")
async def moderator_panel(interaction: discord.Interaction):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("❌ This command is for moderators only.", ephemeral=True)
        return
    
    view = ModeratorPanelView()
    
    embed = discord.Embed(
        title="🛡️ Moderator Panel",
        description="Manage tournament data using the buttons below",
        color=discord.Color.red()
    )
    embed.add_field(
        name="Available Actions",
        value="📊 Add match results\n(More features coming soon)",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# -------------------- RUN --------------------
bot.run(os.getenv("DISCORD_TOKEN"))
