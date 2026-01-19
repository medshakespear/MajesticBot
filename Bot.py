import discord
from discord.ext import commands, tasks
import asyncio
import os

# -------------------- INTENTS --------------------
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------- CONFIG --------------------
LEADER_ROLE_NAME = "LEADER"

SQUADS = {
    "Manschaft": "V",
    "Zero Vision": "ZVS",
    "SAT": "SAT",
    "Exeed": "수",
    "Eclypse": "☯",
    "Axiom eSports": "Axs",
    "NONKAR": "🔱",
    "Excalibur": "ΞX",
    "ROYALS": "立",
    "The void": "VD",
    "SRG": "SRG",
    "Blood Moon": "Blod",
    "Meta breakers": "MS",
    "Kit buu": "KITE",
    "Red Raptors": "RED",
    "TEENYI BAMBUSEL": "TNY",
    "Brilliant": "♖",
    "Force X": "X͠",
    "Impuls": "IP",
    "Agartha": "AG",
    "Emberblaze": "EMBR",
    "broken stars": "ᯓ✰",
    "NOX ZENITH CULT": "NZCT",
    "asgard warriors": "AW",
    "NR Esports.": "NR",
}

ALL_TAGS = list(SQUADS.values())

# -------------------- HELPERS --------------------
def remove_all_tags(name):
    for tag in ALL_TAGS:
        if name.startswith(f"{tag} "):
            return name[len(f"{tag} "):]
    return name

def is_leader(member):
    return any(role.name == LEADER_ROLE_NAME for role in member.roles)

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
        return  # ✅ no API call

    try:
        await member.edit(nick=desired)
        await asyncio.sleep(0.4)  # rate-limit safe
    except:
        pass

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

    print("✅ Initial optimized sync done")

# -------------------- INSTANT ROLE SYNC --------------------
@bot.event
async def on_member_update(before, after):
    role, tag = get_member_squad(after, after.guild)
    await safe_nick_update(after, role, tag)

# -------------------- SAFETY SYNC --------------------
@tasks.loop(minutes=1)
async def safety_sync():
    for guild in bot.guilds:
        for member in guild.members:
            role, tag = get_member_squad(member, guild)
            await safe_nick_update(member, role, tag)

# -------------------- MEMBER COMMANDS --------------------
@bot.tree.command(name="help", description="Show all available bot commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Squad Bot Help",
        description="Below is a list of all available commands.\n"
                    "Some commands are **Leader-only** and will not work if you are not a leader.",
        color=0x2F3136
    )

    # Member commands
    embed.add_field(
        name="👥 Member Commands",
        value=(
            "• `/my_squad_info` — Show your squad info (tag, leaders, member count)\n"
            "• `/all_squads_info` — View all squads, their leaders, and member counts\n"
            "• `/leave_squad` — Leave your current squad"
        ),
        inline=False
    )

    # Leader commands
    embed.add_field(
        name="🛡️ Leader Commands",
        value=(
            "• `/add_member @user` — Add a member to your squad\n"
            "• `/remove_member @user` — Remove a member from your squad\n"
            "• `/promote_leader @user` — Promote a squad member to leader\n"
            "• `/squad_info` — Show full info of your squad (members, tag, color)"
        ),
        inline=False
    )

    embed.set_footer(text="Squad Bot • Leader role required for leader commands")

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="leave_squad")
async def leave_squad(interaction: discord.Interaction):
    role, _ = get_member_squad(interaction.user, interaction.guild)
    if not role:
        await interaction.response.send_message("❌ You are not in a squad.", ephemeral=True)
        return

    await interaction.user.remove_roles(role)
    await safe_nick_update(interaction.user, None, None)
    await interaction.response.send_message("➖ You left your squad.", ephemeral=True)

@bot.tree.command(name="my_squad_info")
async def my_squad_info(interaction: discord.Interaction):
    role, tag = get_member_squad(interaction.user, interaction.guild)
    if not role:
        await interaction.response.send_message("❌ You are not in a squad.", ephemeral=True)
        return

    leaders = get_leaders_for_squad(interaction.guild, role)

    embed = discord.Embed(
        title=f"🛡️ {role.name}",
        color=role.color
    )
    embed.add_field(name="Tag", value=f"`{tag}`")
    embed.add_field(name="Leaders", value=", ".join(leaders) or "None")
    embed.add_field(name="Members", value=len(role.members))

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="all_squads_info")
async def all_squads_info(interaction: discord.Interaction):
    embed = discord.Embed(title="🛡️ All Squads", color=0x2F3136)

    for role_name, tag in SQUADS.items():
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if not role:
            continue

        leaders = get_leaders_for_squad(interaction.guild, role)

        embed.add_field(
            name=f"{role.name} ({tag})",
            value=f"Leaders: {', '.join(leaders) or 'None'}\nMembers: {len(role.members)}",
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)

# -------------------- LEADER COMMANDS --------------------
@bot.tree.command(name="remove_member", description="Remove a member from your squad (leader only)")
async def remove_member(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Only leaders can use this command.", ephemeral=True)
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

    await interaction.response.send_message(
        f"➖ {member.mention} removed from **{leader_role.name}**.",
        ephemeral=True
    )

@bot.tree.command(name="add_member")
async def add_member(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Leader only.", ephemeral=True)
        return

    squad_role, tag = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        return

    for r_name in SQUADS:
        r = discord.utils.get(interaction.guild.roles, name=r_name)
        if r and r in member.roles:
            await member.remove_roles(r)

    await member.add_roles(squad_role)
    await safe_nick_update(member, squad_role, tag)

    await interaction.response.send_message("✅ Member added.", ephemeral=True)

@bot.tree.command(name="promote_leader")
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

    await interaction.response.send_message(f"⭐ {member.mention} promoted to LEADER.", ephemeral=True)

@bot.tree.command(name="squad_info")
async def squad_info(interaction: discord.Interaction):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Leader only.", ephemeral=True)
        return

    role, tag = get_member_squad(interaction.user, interaction.guild)
    leaders = get_leaders_for_squad(interaction.guild, role)

    members = "\n".join(m.display_name for m in role.members) or "No members"

    embed = discord.Embed(
        title=f"🛡️ {role.name} Squad",
        color=role.color
    )
    embed.add_field(name="Tag", value=f"`{tag}`", inline=True)
    embed.add_field(name="Leaders", value=", ".join(leaders), inline=True)
    embed.add_field(name="Members", value=members, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# -------------------- RUN --------------------
bot.run(os.getenv("DISCORD_TOKEN"))