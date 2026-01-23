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
    "Autobots": "AB",
    "ENNEAD": "EN",
    "Ethereal": "ÆTH",
    "NR Esports.": "NR",
}


# -------- EXPLICIT GUEST ROLE MAPPING --------
GUEST_ROLES = {
    "Ethereal": "Ethereal_guest",
    "ENNEAD": "Ennead_guest",
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
    "Excalibur": "Excalibur_guest",
    "Blood Moon": "Blood.Moon_guest",
    "NR Esports.": "NR.Esports_guest",
    "TEENYI BAMBUSEL": "TeenyI.Bambusel_guest",
    "Red Raptors": "Red.Raptors_guest",
    "SRG": "SRG_guest",
    "Kit buu": "Kit.buu_guest",
    "NONKAR": "Nonkar_guest",
    "Exeed": "Exeed_guest",
    "Brilliant": "Brilliant_guest",
    "asgard warriors": "Asguard.Warriors_guest",
    "Manschaft": "Manschaft_guest",
}


ALL_TAGS = list(SQUADS.values())


# -------------------- LOGGING HELPER --------------------

LOG_CHANNEL_NAME = "bot-logs"

async def log_action(guild: discord.Guild, title: str, description: str):
    # Hard stop if guild is missing
    if guild is None:
        return

    # Find channel by name
    channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)

    # If channel not found, try by ID (optional fallback)
    if channel is None:
        print("[LOGGING] bot-logs channel not found")
        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blurple()
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
    await log_action(
        guild,
        "🤖 Bot Ready",
        f"Bot logged in as **{bot.user}** and completed initial nickname sync."
    )


# -------------------- MEMBER COMMANDS --------------------
@bot.tree.command(name="help")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Squad Bot Help",
        description="All commands are visible to everyone.\n"
                    "Some commands require the **LEADER** role.",
        color=0x2F3136
    )

    embed.add_field(
        name="👥 Member Commands",
        value=(
            "• `/my_squad_info`\n"
            "• `/all_squads_info`\n"
            "• `/leave_squad`"
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ Leader Commands",
        value=(
            "• `/add_member @user`\n"
            "• `/remove_member @user`\n"
            "• `/promote_leader @user`\n"
            "• `/give_guest @user`\n"
            "• `/remove_guest @user`\n"
            "• `/squad_info`"
        ),
        inline=False
    )

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
    await log_action(
        interaction.guild,
        "🚪 Squad Left",
        f"{interaction.user.mention} left **{role.name}**"
    )


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
    await log_action(
        interaction.guild,
        "ℹ️ Squad Info Viewed",
        f"{interaction.user.mention} viewed their squad info."
    )
@bot.tree.command(name="all_squads_info")
async def all_squads_info(interaction: discord.Interaction):
    embeds = []
    embed = discord.Embed(title="🛡️ All Squads", color=0x2F3136)

    field_count = 0

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

        field_count += 1

        if field_count == 25:
            embeds.append(embed)
            embed = discord.Embed(color=0x2F3136)
            field_count = 0

    if field_count > 0:
        embeds.append(embed)

    await interaction.response.send_message(embeds=embeds, ephemeral=True)
    await log_action(
        interaction.guild,
        "📋 All Squads Viewed",
        f"{interaction.user.mention} viewed all squads info."
    )

# -------------------- LEADER COMMANDS --------------------
@bot.tree.command(name="give_guest")
async def give_guest(interaction: discord.Interaction, member: discord.Member):
    if not is_leader(interaction.user):
        await interaction.response.send_message("❌ Leader only.", ephemeral=True)
        return

    squad_role, _ = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message("❌ You are not assigned to a squad.", ephemeral=True)
        return

    guest_role_name = GUEST_ROLES.get(squad_role.name)
    if not guest_role_name:
        await interaction.response.send_message("❌ Guest role not configured.", ephemeral=True)
        return

    guest_role = discord.utils.get(interaction.guild.roles, name=guest_role_name)
    if not guest_role:
        await interaction.response.send_message("❌ Guest role not found on server.", ephemeral=True)
        return

    for r in member.roles:
        if r.name.endswith("_guest"):
            await member.remove_roles(r)

    await member.add_roles(guest_role)

    await interaction.response.send_message(
        f"🎟️ {member.mention} is now a **guest of {squad_role.name}**.",
        ephemeral=True
    )
    await log_action(
        interaction.guild,
        "🎟️ Guest Assigned",
        f"{interaction.user.mention} assigned guest role to {member.mention} (**{squad_role.name}**)"
    )

@bot.tree.command(name="remove_guest", description="Remove a guest from your squad (Leader only)")
async def remove_guest(interaction: discord.Interaction, member: discord.Member):

    # Leader check
    if not is_leader(interaction.user):
        await interaction.response.send_message(
            "❌ Only squad leaders can use this command.",
            ephemeral=True
        )
        return

    # Get leader squad
    squad_role, _ = get_member_squad(interaction.user, interaction.guild)
    if not squad_role:
        await interaction.response.send_message(
            "❌ You are not assigned to a squad.",
            ephemeral=True
        )
        return

    # Get correct guest role for THIS squad
    guest_role_name = GUEST_ROLES.get(squad_role.name)
    if not guest_role_name:
        await interaction.response.send_message(
            "❌ Your squad does not have a guest role configured.",
            ephemeral=True
        )
        return

    guest_role = discord.utils.get(interaction.guild.roles, name=guest_role_name)
    if not guest_role or guest_role not in member.roles:
        await interaction.response.send_message(
            "❌ This member is not a guest of your squad.",
            ephemeral=True
        )
        return

    # Remove guest role
    await member.remove_roles(guest_role)
    await asyncio.sleep(0.4)  # rate-limit safety

    await interaction.response.send_message(
        f"🧹 Guest role **{guest_role.name}** removed from {member.mention}.",
        ephemeral=True
    )
    await log_action(
        interaction.guild,
        "🧹 Guest Removed",
        f"{interaction.user.mention} removed guest role from {member.mention} (**{squad_role.name}**)"
    )



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
    await log_action(
        interaction.guild,
        "➖ Member Removed",
        f"{interaction.user.mention} removed {member.mention} from **{leader_role.name}**"
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
    await log_action(
        interaction.guild,
        "➕ Member Added",
        f"{interaction.user.mention} added {member.mention} to **{squad_role.name}**"
    )

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
    await log_action(
        interaction.guild,
        "⭐ Leader Promoted",
        f"{interaction.user.mention} promoted {member.mention} to **LEADER**"
    )


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
    await log_action(
        interaction.guild,
        "🛡️ Squad Info Viewed",
        f"{interaction.user.mention} viewed squad info for **{role.name}**"
    )

# -------------------- INSTANT ROLE SYNC --------------------
@bot.event
async def on_member_update(before, after):
    role, tag = get_member_squad(after, after.guild)
    await bot.wait_until_ready()
    await safe_nick_update(after, role, tag)

# -------------------- SAFETY SYNC --------------------
@tasks.loop(minutes=2)
async def safety_sync():
    for guild in bot.guilds:
        for member in guild.members:
            role, tag = get_member_squad(member, guild)
            await safe_nick_update(member, role, tag)
# -------------------- RUN --------------------
bot.run(os.getenv("DISCORD_TOKEN"))
