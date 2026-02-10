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
        # Save player data
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
        # Validate teams exist
        if self.team1.value not in SQUADS or self.team2.value not in SQUADS:
            await interaction.response.send_message(
                "❌ One or both team names are invalid. Use exact squad names.",
                ephemeral=True
            )
            return
        
        # Parse result
        try:
            score1, score2 = map(int, self.result.value.split('-'))
        except:
            await interaction.response.send_message(
                "❌ Invalid result format. Use format: X-Y (e.g., 2-0)",
                ephemeral=True
            )
            return
        
        # Update squad data
        team1_data = squad_data["squads"][self.team1.value]
        team2_data = squad_data["squads"][self.team2.value]
        
        if score1 > score2:
            # Team 1 wins
            team1_data["wins"] += 1
            team1_data["points"] += 2
            team2_data["losses"] += 1
            result_text = f"🏆 **{self.team1.value}** defeated **{self.team2.value}**"
        elif score2 > score1:
            # Team 2 wins
            team2_data["wins"] += 1
            team2_data["points"] += 2
            team1_data["losses"] += 1
            result_text = f"🏆 **{self.team2.value}** defeated **{self.team1.value}**"
        else:
            # Draw
            team1_data["draws"] += 1
            team1_data["points"] += 1
            team2_data["draws"] += 1
            team2_data["points"] += 1
            result_text = f"🤝 **{self.team1.value}** drew with **{self.team2.value}**"
        
        # Add to match history
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
        
        # Create result embed
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

# -------------------- VIEWS --------------------
class RoleSelectView(View):
    def __init__(self, user_id: int, squad_name: str):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.squad_name = squad_name
        
        # Create role selection dropdown
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
            await interaction.response.send_message(
                "❌ This is not your setup panel.",
                ephemeral=True
            )
            return
        
        selected_role = interaction.data["values"][0]
        
        # Show modal for player details
        modal = PlayerSetupModal(self.user_id, self.squad_name, selected_role)
        await interaction.response.send_modal(modal)

class SquadMenuView(View):
    def __init__(self, squad_role, squad_name: str, tag: str, is_public: bool = True):
        super().__init__(timeout=None)
        self.squad_role = squad_role
        self.squad_name = squad_name
        self.tag = tag
        self.is_public = is_public
    
    @discord.ui.button(label="Squad Info", style=discord.ButtonStyle.primary, emoji="ℹ️")
    async def squad_info_button(self, interaction: discord.Interaction, button: Button):
        await self.show_squad_info(interaction)
    
    @discord.ui.button(label="Rankings", style=discord.ButtonStyle.secondary, emoji="🏆")
    async def rankings_button(self, interaction: discord.Interaction, button: Button):
        await self.show_rankings(interaction)
    
    @discord.ui.button(label="Setup Profile", style=discord.ButtonStyle.success, emoji="⚙️")
    async def setup_profile_button(self, interaction: discord.Interaction, button: Button):
        # Check if user is in a squad
        role, _ = get_member_squad(interaction.user, interaction.guild)
        if not role:
            await interaction.response.send_message(
                "❌ You must be in a squad to set up your profile.",
                ephemeral=True
            )
            return
        
        squad_name = role.name
        view = RoleSelectView(interaction.user.id, squad_name)
        
        embed = discord.Embed(
            title="⚙️ Player Profile Setup",
            description="Select your role to continue setting up your profile.",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def show_squad_info(self, interaction: discord.Interaction):
        squad_info = squad_data["squads"].get(self.squad_name, {})
        
        embed = discord.Embed(
            title=f"🛡️ {self.squad_name}",
            color=self.squad_role.color if self.squad_role else discord.Color.blue()
        )
        
        # Basic info
        embed.add_field(name="Tag", value=f"`{self.tag}`", inline=True)
        embed.add_field(name="Points", value=f"**{squad_info.get('points', 0)}**", inline=True)
        embed.add_field(name="Members", value=len(self.squad_role.members) if self.squad_role else 0, inline=True)
        
        # Stats
        wins = squad_info.get('wins', 0)
        draws = squad_info.get('draws', 0)
        losses = squad_info.get('losses', 0)
        embed.add_field(
            name="Record",
            value=f"🟢 {wins}W - 🟡 {draws}D - 🔴 {losses}L",
            inline=False
        )
        
        # Championship info
        champ_wins = squad_info.get('championship_wins', 0)
        titles = squad_info.get('titles', [])
        if champ_wins > 0:
            embed.add_field(name="Championships", value=f"🏆 {champ_wins}", inline=True)
        if titles:
            embed.add_field(name="Titles", value=", ".join(titles), inline=False)
        
        # Main Roster
        main_roster = squad_info.get('main_roster', [])
        if main_roster:
            roster_text = ""
            for player_id in main_roster[:5]:
                player_data = squad_data["players"].get(str(player_id), {})
                if player_data:
                    roster_text += f"**{player_data.get('role', 'N/A')}**: {player_data.get('ingame_name', 'Unknown')} (#{player_data.get('ingame_id', 'N/A')}) - {player_data.get('highest_rank', 'N/A')}\n"
            if roster_text:
                embed.add_field(name="⭐ Main Roster", value=roster_text, inline=False)
        
        # Subs
        subs = squad_info.get('subs', [])
        if subs:
            subs_text = ""
            for player_id in subs[:3]:
                player_data = squad_data["players"].get(str(player_id), {})
                if player_data:
                    subs_text += f"**{player_data.get('role', 'N/A')}**: {player_data.get('ingame_name', 'Unknown')}\n"
            if subs_text:
                embed.add_field(name="🔄 Substitutes", value=subs_text, inline=False)
        
        # Leaders
        leaders = get_leaders_for_squad(interaction.guild, self.squad_role) if self.squad_role else []
        if leaders:
            embed.add_field(name="👑 Leaders", value=", ".join(leaders), inline=False)
        
        # Guests
        guest_role_name = GUEST_ROLES.get(self.squad_name)
        if guest_role_name:
            guest_role = discord.utils.get(interaction.guild.roles, name=guest_role_name)
            if guest_role and guest_role.members:
                guests = [m.display_name for m in guest_role.members[:10]]
                embed.add_field(name="🎟️ Guests", value=", ".join(guests), inline=False)
        
        # Logo
        logo_url = squad_info.get('logo_url')
        if logo_url:
            embed.set_thumbnail(url=logo_url)
        
        await interaction.response.send_message(embed=embed, ephemeral=not self.is_public)
    
    async def show_rankings(self, interaction: discord.Interaction):
        rankings = get_squad_ranking()
        
        embed = discord.Embed(
            title="🏆 Squad Rankings",
            description="Rankings based on match performance",
            color=discord.Color.gold()
        )
        
        for i, squad in enumerate(rankings[:15], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            embed.add_field(
                name=f"{medal} {squad['tag']} {squad['name']}",
                value=f"**{squad['points']}** pts | {squad['wins']}W-{squad['draws']}D-{squad['losses']}L",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=not self.is_public)

class SquadBrowserView(View):
    def __init__(self, guild):
        super().__init__(timeout=180)
        self.guild = guild
        
        # Create squad selection dropdown with all squads
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
        
        # Discord has a limit of 25 options per select menu
        select = Select(
            placeholder="🔍 Choose a squad to view...",
            options=options[:25],  # Take first 25
            custom_id="squad_browser_select"
        )
        select.callback = self.squad_selected
        self.add_item(select)
    
    async def squad_selected(self, interaction: discord.Interaction):
        selected_squad = interaction.data["values"][0]
        
        # Get squad role and tag
        squad_role = discord.utils.get(self.guild.roles, name=selected_squad)
        tag = SQUADS.get(selected_squad, "?")
        
        # Create temporary view to show squad info
        temp_view = SquadMenuView(squad_role, selected_squad, tag, is_public=True)
        await temp_view.show_squad_info(interaction)

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

# -------------------- MEMBER COMMANDS --------------------
@bot.tree.command(name="help", description="Show all available bot commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Squad Bot - Command Guide",
        description="Here are all the commands available to you!",
        color=discord.Color.blue()
    )
    
    # Member Commands
    embed.add_field(
        name="👥 Member Commands",
        value=(
            "`/help` - Show this help menu\n"
            "`/squad_menu` - Interactive squad management hub\n"
            "`/browse_squads` - View any squad's information\n"
            "`/my_squad` - Quick view of your squad\n"
            "`/rankings` - View current squad rankings\n"
            "`/leave_squad` - Leave your current squad"
        ),
        inline=False
    )
    
    # Leader Commands
    if is_leader(interaction.user):
        embed.add_field(
            name="👑 Leader Commands",
            value=(
                "`/add_member @user` - Add member to your squad\n"
                "`/remove_member @user` - Remove member from squad\n"
                "`/set_main_roster @user` - Add to main roster (max 5)\n"
                "`/set_sub @user` - Add to substitutes (max 3)\n"
                "`/promote_leader @user` - Promote to leader\n"
                "`/give_guest @user` - Give guest role\n"
                "`/remove_guest @user` - Remove guest role\n"
                "`/set_logo <url>` - Set squad logo"
            ),
            inline=False
        )
    
    # Moderator Commands
    if is_moderator(interaction.user):
        embed.add_field(
            name="🛡️ Moderator Commands",
            value="`/add_match` - Add match results between squads",
            inline=False
        )
    
    embed.set_footer(text="Use /squad_menu for the interactive interface!")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="squad_menu", description="View squad info, rankings, and setup your profile")
async def squad_menu(interaction: discord.Interaction):
    role, tag = get_member_squad(interaction.user, interaction.guild)
    squad_name = role.name if role else "No Squad"
    
    view = SquadMenuView(role, squad_name, tag, is_public=True)
    
    embed = discord.Embed(
        title="🎮 Squad Management",
        description="Use the buttons below to access squad features",
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="my_squad", description="Quick view of your squad")
async def my_squad(interaction: discord.Interaction):
    role, tag = get_member_squad(interaction.user, interaction.guild)
    if not role:
        await interaction.response.send_message("❌ You are not in a squad.", ephemeral=True)
        return
    
    squad_name = role.name
    view = SquadMenuView(role, squad_name, tag, is_public=False)
    await view.show_squad_info(interaction)

@bot.tree.command(name="browse_squads", description="Browse and view any squad's information")
async def browse_squads(interaction: discord.Interaction):
    view = SquadBrowserView(interaction.guild)
    
    embed = discord.Embed(
        title="🔍 Squad Browser",
        description="Select a squad from the dropdown below to view their full information, stats, roster, and more!",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Total squads: {len(SQUADS)}")
    
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="rankings", description="View squad rankings")
async def rankings_command(interaction: discord.Interaction):
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

@bot.tree.command(name="leave_squad", description="Leave your current squad")
async def leave_squad(interaction: discord.Interaction):
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

# -------------------- LEADER COMMANDS --------------------
@bot.tree.command(name="add_member", description="Add a member to your squad (Leader)")
async def add_member(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Leader only.", ephemeral=True)
        return
    
    squad_role, tag = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You are not in a squad.", ephemeral=True)
        return
    
    # Remove from other squads
    for r_name in SQUADS:
        r = discord.utils.get(interaction.guild.roles, name=r_name)
        if r and r in member.roles:
            await member.remove_roles(r)
    
    await member.add_roles(squad_role)
    await safe_nick_update(member, squad_role, tag)
    
    await interaction.response.send_message(f"✅ {member.mention} added to **{squad_role.name}**")
    await log_action(
        interaction.guild,
        "➕ Member Added",
        f"{interaction.user.mention} added {member.mention} to **{squad_role.name}**"
    )

@bot.tree.command(name="remove_member", description="Remove a member from your squad (Leader)")
async def remove_member(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Leader only.", ephemeral=True)
        return
    
    leader_role, _ = get_member_squad(interaction.user, interaction.guild)
    if not leader_role or leader_role not in member.roles:
        await interaction.response.send_message("❌ This member is not in your squad.", ephemeral=True)
        return
    
    await member.remove_roles(leader_role)
    clean = remove_all_tags(member.display_name)
    try:
        await member.edit(nick=clean)
    except:
        pass
    
    await interaction.response.send_message(f"➖ {member.mention} removed from **{leader_role.name}**")
    await log_action(
        interaction.guild,
        "➖ Member Removed",
        f"{interaction.user.mention} removed {member.mention} from **{leader_role.name}**"
    )

@bot.tree.command(name="set_main_roster", description="Set a player as main roster (Leader, max 5)")
async def set_main_roster(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Leader only.", ephemeral=True)
        return
    
    squad_role, _ = get_member_squad(interaction.user, interaction.guild)
    member_role, _ = get_member_squad(member, interaction.guild)
    
    if squad_role != member_role:
        await interaction.response.send_message("❌ Member must be in your squad.", ephemeral=True)
        return
    
    squad_name = squad_role.name
    squad_info = squad_data["squads"][squad_name]
    
    # Check if already in main roster
    if member.id in squad_info["main_roster"]:
        await interaction.response.send_message("⚠️ Already in main roster.", ephemeral=True)
        return
    
    # Check limit
    if len(squad_info["main_roster"]) >= 5:
        await interaction.response.send_message("❌ Main roster is full (max 5).", ephemeral=True)
        return
    
    # Remove from subs if there
    if member.id in squad_info["subs"]:
        squad_info["subs"].remove(member.id)
    
    squad_info["main_roster"].append(member.id)
    save_data(squad_data)
    
    await interaction.response.send_message(f"⭐ {member.mention} added to main roster!")
    await log_action(
        interaction.guild,
        "⭐ Main Roster Updated",
        f"{interaction.user.mention} added {member.mention} to main roster"
    )

@bot.tree.command(name="set_sub", description="Set a player as substitute (Leader, max 3)")
async def set_sub(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Leader only.", ephemeral=True)
        return
    
    squad_role, _ = get_member_squad(interaction.user, interaction.guild)
    member_role, _ = get_member_squad(member, interaction.guild)
    
    if squad_role != member_role:
        await interaction.response.send_message("❌ Member must be in your squad.", ephemeral=True)
        return
    
    squad_name = squad_role.name
    squad_info = squad_data["squads"][squad_name]
    
    # Check if already in subs
    if member.id in squad_info["subs"]:
        await interaction.response.send_message("⚠️ Already a substitute.", ephemeral=True)
        return
    
    # Check limit
    if len(squad_info["subs"]) >= 3:
        await interaction.response.send_message("❌ Substitute roster is full (max 3).", ephemeral=True)
        return
    
    # Remove from main if there
    if member.id in squad_info["main_roster"]:
        squad_info["main_roster"].remove(member.id)
    
    squad_info["subs"].append(member.id)
    save_data(squad_data)
    
    await interaction.response.send_message(f"🔄 {member.mention} added to substitutes!")
    await log_action(
        interaction.guild,
        "🔄 Substitute Added",
        f"{interaction.user.mention} added {member.mention} to substitutes"
    )

@bot.tree.command(name="promote_leader", description="Promote a member to leader (Leader)")
async def promote_leader(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Leader only.", ephemeral=True)
        return
    
    leader_role, _ = get_member_squad(interaction.user, interaction.guild)
    member_role, _ = get_member_squad(member, interaction.guild)
    
    if leader_role != member_role:
        await interaction.response.send_message("❌ Member must be in your squad.", ephemeral=True)
        return
    
    leader_role_obj = discord.utils.get(interaction.guild.roles, name=LEADER_ROLE_NAME)
    await member.add_roles(leader_role_obj)
    
    await interaction.response.send_message(f"⭐ {member.mention} promoted to LEADER!")
    await log_action(
        interaction.guild,
        "⭐ Leader Promoted",
        f"{interaction.user.mention} promoted {member.mention} to LEADER"
    )

@bot.tree.command(name="give_guest", description="Give guest role to a player (Leader)")
async def give_guest(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Leader only.", ephemeral=True)
        return
    
    squad_role, _ = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You are not in a squad.", ephemeral=True)
        return
    
    guest_role_name = GUEST_ROLES.get(squad_role.name)
    if not guest_role_name:
        await interaction.response.send_message("❌ Guest role not configured.", ephemeral=True)
        return
    
    guest_role = discord.utils.get(interaction.guild.roles, name=guest_role_name)
    if not guest_role:
        await interaction.response.send_message("❌ Guest role not found.", ephemeral=True)
        return
    
    # Remove other guest roles
    for r in member.roles:
        if r.name.endswith("_guest"):
            await member.remove_roles(r)
    
    await member.add_roles(guest_role)
    
    await interaction.response.send_message(f"🎟️ {member.mention} is now a guest of **{squad_role.name}**!")
    await log_action(
        interaction.guild,
        "🎟️ Guest Added",
        f"{interaction.user.mention} gave guest role to {member.mention}"
    )

@bot.tree.command(name="remove_guest", description="Remove guest role (Leader)")
async def remove_guest(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Leader only.", ephemeral=True)
        return
    
    squad_role, _ = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You are not in a squad.", ephemeral=True)
        return
    
    guest_role_name = GUEST_ROLES.get(squad_role.name)
    if not guest_role_name:
        await interaction.response.send_message("❌ Guest role not configured.", ephemeral=True)
        return
    
    guest_role = discord.utils.get(interaction.guild.roles, name=guest_role_name)
    if not guest_role or guest_role not in member.roles:
        await interaction.response.send_message("❌ Member is not a guest of your squad.", ephemeral=True)
        return
    
    await member.remove_roles(guest_role)
    await interaction.response.send_message(f"🧹 Guest role removed from {member.mention}")
    await log_action(
        interaction.guild,
        "🧹 Guest Removed",
        f"{interaction.user.mention} removed guest role from {member.mention}"
    )

@bot.tree.command(name="set_logo", description="Set your squad's logo (Leader)")
async def set_logo(interaction: discord.Interaction, logo_url: str):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Leader only.", ephemeral=True)
        return
    
    squad_role, _ = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You are not in a squad.", ephemeral=True)
        return
    
    squad_name = squad_role.name
    squad_data["squads"][squad_name]["logo_url"] = logo_url
    save_data(squad_data)
    
    embed = discord.Embed(
        title="✅ Logo Updated",
        description=f"Logo set for **{squad_name}**",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=logo_url)
    
    await interaction.response.send_message(embed=embed)
    await log_action(
        interaction.guild,
        "🖼️ Logo Updated",
        f"{interaction.user.mention} updated logo for **{squad_name}**"
    )

# -------------------- MODERATOR COMMANDS --------------------
@bot.tree.command(name="add_match", description="Add a match result (Moderator)")
async def add_match(interaction: discord.Interaction):
    if not is_moderator(interaction.user):
        await interaction.response.send_message("❌ Moderator only.", ephemeral=True)
        return
    
    modal = AddMatchModal()
    await interaction.response.send_modal(modal)

# -------------------- RUN --------------------
bot.run(os.getenv("DISCORD_TOKEN"))
