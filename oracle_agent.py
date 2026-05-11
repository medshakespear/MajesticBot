# =====================================================================
#   ORACLE AI AGENT v2 — Majestic Dominion
#   Primary: Groq (free) | Fallback: Gemini REST (free)
#
#   SECURITY MODEL:
#   ─────────────────────────────────────────────────────────────────
#   mod-oracle channel  → Full control: read + ALL write actions
#   royal-oracle channel → Read only: info, standings, help, chat
#   @mention / /oracle  → Read only (treated as member)
#
#   SETUP:
#   ─────────────────────────────────────────────────────────────────
#   requirements.txt → add: groq  aiohttp
#   Railway Variables → GROQ_API_KEY=gsk_...  GEMINI_API_KEY=AIza...
#
#   bot.py:
#     from oracle_agent import OracleAgent, setup_oracle      ← top
#     oracle = OracleAgent(bot, squad_data, SQUADS)           ← after squad_data
#     setup_oracle(bot, oracle)                               ← inside on_ready() BEFORE tree.sync()
# =====================================================================

import os, json, asyncio, re, uuid
from datetime import datetime, timedelta
from collections import defaultdict
import discord
from discord import app_commands

try:
    from groq import AsyncGroq
    GROQ_OK = True
except ImportError:
    GROQ_OK = False

try:
    import aiohttp
    AIOHTTP_OK = True
except ImportError:
    AIOHTTP_OK = False

# ── Channels ──────────────────────────────────────────────────────────
MOD_ORACLE_CHANNEL   = "mod-oracle"    # any channel containing this → full mod access
ROYAL_ORACLE_CHANNEL = "royal-oracle"        # any channel containing this → read-only

# ── Models ────────────────────────────────────────────────────────────
GROQ_MODEL   = "llama-3.3-70b-versatile"
GEMINI_MODEL = "gemini-2.5-flash"
MAX_TOKENS   = 400

# ── Rate limits ───────────────────────────────────────────────────────
RATE_SEC = 15    # 15 seconds between requests per user
RATE_MIN = 20    # max per minute per user (very generous)
HISTORY  = 4     # messages kept per user
DAILY_USER_MAX = 50   # max per user per day (rolling 24h)
DAILY_TOTAL_MAX = 1000 # global safety cap — APIs handle their own limits

# ── Personality ───────────────────────────────────────────────────────
PERSONALITY_MEMBER = """
You are the Royal Oracle — the AI soul of the Majestic Dominion Discord server.
You are witty, warm, playful, and genuinely fun to talk with.
You're knowledgeable about everything: gaming, life, jokes, advice, the server.
You call members "warrior" sometimes but you're not overly dramatic.
You have a great sense of humor — you can be sarcastic, funny, or wholesome depending on the mood.
You keep replies SHORT (under 150 words) unless asked for detail.
You use the live server data below to answer questions accurately.
You CANNOT make changes to the server — you're read-only for members.
If someone asks you to do something that requires mod access, tell them to ask a mod.
"""

PERSONALITY_MOD = """
You are the Royal Oracle — the AI management assistant of Majestic Dominion Discord server.
You are smart, efficient, and helpful for server management.
You still have personality — witty and fun — but you prioritize being USEFUL to moderators.
You have FULL control over the server: you can record matches, create events, manage bounties,
post announcements, schedule matches, manage registrations, and more.
You keep replies concise and clear — mods are busy.
When you perform an action, confirm it clearly and briefly.
You use the live server data below to make informed decisions.
"""


# ═════════════════════════════════════════════════════════════════════
#  OracleAgent
# ═════════════════════════════════════════════════════════════════════

class OracleAgent:

    def __init__(self, bot, squad_data_ref, squads_ref):
        self.bot        = bot
        self.squad_data = squad_data_ref
        self.squads     = squads_ref
        self.history    = defaultdict(list)
        self.rate_cache = defaultdict(list)
        self.daily_log      = []  # global daily request tracker
        self.daily_user_log = {}  # per-user daily tracker {uid: [timestamps]}

        # Groq
        self.groq = None
        gk = os.getenv("GROQ_API_KEY")
        if GROQ_OK and gk:
            self.groq = AsyncGroq(api_key=gk)
            print(f"✅ Oracle: Groq ({GROQ_MODEL}) ready")
        else:
            print("⚠️  Oracle: No GROQ_API_KEY")

        # Gemini
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_key:
            print(f"✅ Oracle: Gemini ({GEMINI_MODEL}) ready as fallback")
        else:
            print("⚠️  Oracle: No GEMINI_API_KEY")

    # ── Rate limiting ─────────────────────────────────────────────────

    def is_limited(self, uid):
        now  = datetime.utcnow()
        cut  = now - timedelta(seconds=60)
        dcut = now - timedelta(hours=24)

        # 1. Per-user per-minute rate limit (prevents spam)
        r = [t for t in self.rate_cache[uid] if t > cut]
        self.rate_cache[uid] = r
        if r and (now - r[-1]).total_seconds() < RATE_SEC:
            w = int(RATE_SEC - (now - r[-1]).total_seconds()) + 1
            return True, f"⏳ Please wait **{w} seconds** before asking again."
        if len(r) >= RATE_MIN:
            return True, "🔮 You're asking too fast — wait a moment then try again."

        # 2. Per-user daily limit (rolling 24h window)
        if uid not in self.daily_user_log:
            self.daily_user_log[uid] = []
        user_day = [t for t in self.daily_user_log[uid] if t > dcut]
        self.daily_user_log[uid] = user_day
        if len(user_day) >= DAILY_USER_MAX:
            return True, f"🔮 You've used your {DAILY_USER_MAX} daily Oracle questions, warrior. Come back tomorrow!"

        # 3. Global total cap (protects API budget)
        self.daily_log = [t for t in getattr(self, "daily_log", []) if t > dcut]
        if len(self.daily_log) >= DAILY_TOTAL_MAX:
            return True, "🔮 The Oracle is resting for today — back tomorrow!"

        # All good — log this request
        self.rate_cache[uid].append(now)
        self.daily_user_log[uid].append(now)
        self.daily_log.append(now)
        return False, ""

    def usage_stats(self):
        now  = datetime.utcnow()
        dcut = now - timedelta(hours=24)
        total_used = len([t for t in getattr(self, "daily_log", []) if t > dcut])
        user_counts = {
            uid: len([t for t in times if t > dcut])
            for uid, times in getattr(self, "daily_user_log", {}).items()
            if any(t > dcut for t in times)
        }
        return total_used, DAILY_TOTAL_MAX, user_counts

    # ── Context ───────────────────────────────────────────────────────

    def context(self):
        sd = self.squad_data
        sq = sd.get("squads", {})

        top = sorted(sq.items(), key=lambda x: -x[1].get("points", 0))
        rankings = " | ".join(
            f"#{i} {n}:{v.get('points',0)}pts {v.get('wins',0)}W/{v.get('losses',0)}L str:{v.get('streak',0)}"
            for i,(n,v) in enumerate(top[:8], 1)
        )

        evs = sd.get("events", [])
        events = " | ".join(
            f"{e['name']}[{e['status']}]{e.get('format','')} {len(e.get('registrations',[]))}reg/{e.get('max_entries','∞')} date:{e.get('date','?')}"
            for e in evs if e["status"] in ("open","live")
        ) or "none"

        all_evs = " | ".join(
            f"{e['name']}[{e['status']}]id:{e['id']}"
            for e in evs
        ) or "none"

        bounties = " | ".join(
            f"{k}:+{v.get('points',0)}pts"
            for k,v in list(sd.get("bounties",{}).items())
        ) or "none"

        challs = " | ".join(
            f"{c['challenger']} vs {c['challenged']}[{c['status']}]"
            for c in sd.get("challenges",[])
            if c["status"] in ("pending","accepted","scheduled")
        ) or "none"

        recent = " | ".join(
            f"{m.get('team1','?')} {m.get('score','?')} {m.get('team2','?')}->{m.get('winner','draw')}"
            for m in sd.get("matches",[])[-5:][::-1]
        ) or "none"

        sq_names = ", ".join(list(sq.keys())[:20])

        return (
            f"[SERVER DATA]\n"
            f"Kingdoms({len(sq)}): {sq_names}\n"
            f"Rankings: {rankings}\n"
            f"ActiveEvents: {events}\n"
            f"AllEvents: {all_evs}\n"
            f"Bounties: {bounties}\n"
            f"Challenges: {challs}\n"
            f"RecentMatches: {recent}\n"
            f"TotalMatches: {len(sd.get('matches',[]))}"
        )

    # ── Action parser & executor (mod-only) ───────────────────────────

    async def _detect_and_execute(self, text: str, guild, invoker) -> str | None:
        """
        Detect write actions from natural language and execute them.
        Returns a result string if an action was taken, else None.
        """
        t   = text.lower().strip()
        sd  = self.squad_data
        sq  = sd.get("squads", {})

        def fuzzy(name, d):
            name = name.lower().strip()
            # exact first
            for k in d:
                if k.lower() == name: return k
            # partial
            for k in d:
                if name in k.lower(): return k
            return None

        def save():
            try:
                import sys
                m = sys.modules.get("__main__")
                if m and hasattr(m, "save_data"):
                    m.save_data(sd)
            except: pass

        async def to_channel(name, embed):
            ch = discord.utils.get(guild.text_channels, name=name)
            if ch:
                try: await ch.send(embed=embed)
                except: pass

        # ── record match ──────────────────────────────────────────────
        # patterns: "record X beat Y 2-0" / "X won against Y 1-0" / "X vs Y X won 2-1"
        m = re.search(
            r'(?:record|log)?\s*([a-z0-9 ]+?)\s+(?:beat|beats|won|defeated|def\.?)\s+([a-z0-9 ]+?)\s+(\d+-\d+)',
            t, re.I
        )
        if not m:
            m = re.search(
                r'(?:record|log)?\s*([a-z0-9 ]+?)\s+vs\.?\s+([a-z0-9 ]+?)\s+(\d+-\d+)\s+([a-z0-9 ]+?)\s+(?:won|wins)',
                t, re.I
            )
        if m:
            raw_w  = m.group(1).strip()
            raw_l  = m.group(2).strip()
            score  = m.group(3).strip()
            wm = fuzzy(raw_w, sq)
            lm = fuzzy(raw_l, sq)
            if wm and lm and wm != lm:
                sq[wm]["wins"]   = sq[wm].get("wins",0) + 1
                sq[wm]["points"] = sq[wm].get("points",0) + 3
                sq[wm]["streak"] = sq[wm].get("streak",0) + 1
                sq[lm]["losses"] = sq[lm].get("losses",0) + 1
                sq[lm]["streak"] = 0
                sd.setdefault("matches",[]).append({
                    "id": len(sd.get("matches",[]))+1,
                    "team1": wm, "team2": lm, "score": score,
                    "winner": wm, "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                    "recorded_by": str(invoker.id), "source": "oracle"
                })
                save()
                embed = discord.Embed(
                    title="⚔️ BATTLE RECORDED",
                    description=f"**{wm}** defeated **{lm}** — **{score}**\n+3 Glory Points for {wm}",
                    color=0xffd700, timestamp=datetime.utcnow()
                )
                await to_channel("war-results", embed)
                return f"✅ Recorded: **{wm}** beat **{lm}** {score} — glory points updated & posted to war-results."
            elif not wm or not lm:
                missing = raw_w if not wm else raw_l
                return f"❌ Kingdom not found: **{missing}**. Available: {', '.join(list(sq.keys())[:10])}"

        # ── draw ─────────────────────────────────────────────────────
        m = re.search(r'draw\s+(?:between\s+)?([a-z0-9 ]+?)\s+(?:and|vs)\s+([a-z0-9 ]+?)(?:\s+(\d+-\d+))?$', t, re.I)
        if m:
            t1m = fuzzy(m.group(1).strip(), sq)
            t2m = fuzzy(m.group(2).strip(), sq)
            score = m.group(3) or "1-1"
            if t1m and t2m:
                for k in [t1m, t2m]:
                    sq[k]["draws"]  = sq[k].get("draws",0) + 1
                    sq[k]["points"] = sq[k].get("points",0) + 1
                sd.setdefault("matches",[]).append({
                    "id": len(sd.get("matches",[]))+1,
                    "team1": t1m, "team2": t2m, "score": score,
                    "winner": "draw", "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                    "recorded_by": str(invoker.id), "source": "oracle"
                })
                save()
                return f"✅ Draw recorded: **{t1m}** vs **{t2m}** {score} — both +1pt."

        # ── add bounty ────────────────────────────────────────────────
        m = re.search(r'(?:add|put|set)\s+(?:a\s+)?(?:(\d+)\s+(?:point|pt)s?\s+)?bounty\s+on\s+([a-z0-9 ]+?)(?:\s+(\d+)\s+(?:point|pt)s?)?', t, re.I)
        if m:
            pts  = int(m.group(1) or m.group(3) or 2)
            name = (m.group(2) or "").strip()
            km   = fuzzy(name, sq)
            if km:
                sd.setdefault("bounties",{})[km] = {
                    "points": pts, "reason": "Added via Oracle",
                    "added_at": datetime.utcnow().isoformat()
                }
                save()
                return f"✅ Bounty set: **{km}** — +{pts} pts for anyone who defeats them."
            return f"❌ Kingdom not found: **{name}**"

        # ── remove bounty ─────────────────────────────────────────────
        m = re.search(r'(?:remove|clear|delete)\s+bounty\s+(?:on\s+|from\s+)?([a-z0-9 ]+)', t, re.I)
        if m:
            name = m.group(1).strip()
            km   = fuzzy(name, sd.get("bounties",{}))
            if km:
                sd.get("bounties",{}).pop(km, None)
                save()
                return f"✅ Bounty removed from **{km}**."
            return f"❌ No bounty found for: **{name}**"

        # ── create event ──────────────────────────────────────────────
        m = re.search(r'create\s+(?:an?\s+)?event\s+(?:called\s+|named\s+)?["\']?([^"\']+?)["\']?\s+(?:on\s+|for\s+|at\s+|date\s*:?\s*)([^,]+?)(?:\s+format\s*:?\s*([^\s,]+))?(?:\s+max\s*:?\s*(\d+))?$', t, re.I)
        if m:
            name = m.group(1).strip()
            date = m.group(2).strip()
            fmt  = m.group(3) or "TBD"
            mx   = int(m.group(4)) if m.group(4) else None
            eid  = str(uuid.uuid4())[:8]
            ev   = {
                "id": eid, "name": name, "type": "tournament",
                "format": fmt, "date": date, "description": f"Created via Oracle by {invoker.display_name}",
                "registration_mode": "solo", "max_entries": mx,
                "prize_pool": "", "status": "open",
                "registrations": [], "bracket_data": None, "schedule": [],
                "tournament_system": "single_elim",
                "created_by": str(invoker.id),
                "created_at": datetime.utcnow().isoformat()
            }
            sd.setdefault("events",[]).append(ev)
            save()
            embed = discord.Embed(
                title=f"🎪 NEW EVENT — {name}",
                description=f"Format: {fmt} | Date: {date}" + (f" | Max: {mx}" if mx else ""),
                color=0xffd700, timestamp=datetime.utcnow()
            )
            await to_channel("war-results", embed)
            return f"✅ Event **{name}** created (ID: `{eid}`) — open for registration. Posted to war-results."

        # ── close event ───────────────────────────────────────────────
        m = re.search(r'close\s+(?:the\s+)?event\s+["\']?([^"\']+)["\']?', t, re.I)
        if m:
            name = m.group(1).strip()
            ev   = next((e for e in sd.get("events",[]) if name.lower() in e["name"].lower()), None)
            if ev:
                ev["status"] = "completed"
                save()
                return f"✅ Event **{ev['name']}** closed."
            return f"❌ Event not found: **{name}**. Events: {', '.join(e['name'] for e in sd.get('events',[]))}"

        # ── start event ───────────────────────────────────────────────
        m = re.search(r'start\s+(?:the\s+)?event\s+["\']?([^"\']+)["\']?', t, re.I)
        if m:
            name = m.group(1).strip()
            ev   = next((e for e in sd.get("events",[]) if name.lower() in e["name"].lower()), None)
            if ev:
                ev["status"] = "live"
                save()
                embed = discord.Embed(
                    title=f"⚔️ EVENT NOW LIVE — {ev['name']}",
                    description="The arena is open! May the best warrior win.",
                    color=0xdc143c, timestamp=datetime.utcnow()
                )
                await to_channel("war-results", embed)
                return f"✅ Event **{ev['name']}** is now LIVE — posted to war-results."
            return f"❌ Event not found: **{name}**"

        # ── schedule match ────────────────────────────────────────────
        m = re.search(r'schedule\s+([a-z0-9 ]+?)\s+vs\.?\s+([a-z0-9 ]+?)\s+(?:on\s+|for\s+|at\s+)?(.+)', t, re.I)
        if m:
            t1 = m.group(1).strip(); t2 = m.group(2).strip(); dt = m.group(3).strip()
            t1m = fuzzy(t1, sq); t2m = fuzzy(t2, sq)
            names = f"**{t1m or t1}** vs **{t2m or t2}**"
            embed = discord.Embed(
                title="📅 MATCH SCHEDULED",
                description=f"⚔️ {names}\n📅 **{dt}**\n\n*Prepare your lineups, warriors!*",
                color=0xffd700, timestamp=datetime.utcnow()
            )
            await to_channel("war-results", embed)
            return f"✅ Match scheduled: {names} — **{dt}** — posted to war-results."

        # ── post announcement ─────────────────────────────────────────
        m = re.search(r'(?:post|send|announce)\s+(?:announcement|announce|message)\s*:?\s*(?:title\s*:?\s*["\']?([^"\']+?)["\']?\s+)?(?:message\s*:?\s*)?["\']?(.+)["\']?$', t, re.I)
        if m:
            title = (m.group(1) or "Royal Announcement").strip()
            msg   = m.group(2).strip()
            ann_ch = discord.utils.get(guild.text_channels, name="announcements")
            if not ann_ch:
                ann_ch = next((c for c in guild.text_channels if "announcement" in c.name.lower()), None)
            if ann_ch:
                role    = discord.utils.get(guild.roles, name="MAJESTIC")
                mention = role.mention if role else ""
                embed   = discord.Embed(
                    title=title, description=msg,
                    color=0xffd700, timestamp=datetime.utcnow()
                )
                embed.set_footer(text="⚜️ Majestic Dominion")
                await ann_ch.send(content=f"📢 {mention}" if mention else None, embed=embed)
                return f"✅ Announcement posted to {ann_ch.mention}: **{title}**"
            return "❌ Announcements channel not found."

        # ── add registrant ────────────────────────────────────────────
        m = re.search(r'add\s+([a-z0-9 ]+?)\s+to\s+(?:the\s+)?(?:event\s+)?["\']?([^"\']+)["\']?', t, re.I)
        if m:
            pname  = m.group(1).strip()
            evname = m.group(2).strip()
            ev = next((e for e in sd.get("events",[]) if evname.lower() in e["name"].lower()), None)
            if ev:
                ev.setdefault("registrations",[]).append({
                    "player_name": pname, "player_id": None,
                    "registered_at": datetime.utcnow().isoformat(),
                    "added_by_mod": True
                })
                save()
                return f"✅ **{pname}** added to **{ev['name']}** — {len(ev['registrations'])} total registrants."
            return f"❌ Event not found: **{evname}**"

        # ── remove registrant ─────────────────────────────────────────
        m = re.search(r'remove\s+([a-z0-9 ]+?)\s+from\s+(?:the\s+)?(?:event\s+)?["\']?([^"\']+)["\']?', t, re.I)
        if m:
            pname  = m.group(1).strip()
            evname = m.group(2).strip()
            ev = next((e for e in sd.get("events",[]) if evname.lower() in e["name"].lower()), None)
            if ev:
                before = len(ev.get("registrations",[]))
                ev["registrations"] = [
                    r for r in ev.get("registrations",[])
                    if pname.lower() not in (r.get("player_name","") or r.get("team_name","")).lower()
                ]
                removed = before - len(ev["registrations"])
                save()
                return f"✅ Removed **{pname}** from **{ev['name']}** ({removed} entry removed)." if removed else f"❌ **{pname}** not found in **{ev['name']}**."

        # ── set points manually ───────────────────────────────────────
        m = re.search(r'set\s+([a-z0-9 ]+?)\s+(?:points?|pts?)\s+to\s+(\d+)', t, re.I)
        if m:
            name = m.group(1).strip(); pts = int(m.group(2))
            km   = fuzzy(name, sq)
            if km:
                sq[km]["points"] = pts; save()
                return f"✅ **{km}** points set to **{pts}**."
            return f"❌ Kingdom not found: **{name}**"

        # ── clear all bounties ────────────────────────────────────────
        if re.search(r'clear\s+all\s+bounties', t, re.I):
            sd["bounties"] = {}; save()
            return "✅ All bounties cleared."

        # ── send message to channel ───────────────────────────────────
        m = re.search(r'send\s+(?:to\s+#?([a-z0-9-]+)\s+)?["\'](.+?)["\']', t, re.I)
        if m:
            chname = m.group(1); msg = m.group(2)
            target = discord.utils.get(guild.text_channels, name=chname) if chname else None
            if not target:
                target = discord.utils.get(guild.text_channels, name="war-results")
            if target:
                await target.send(msg)
                return f"✅ Message sent to {target.mention}."


        # ── give role ─────────────────────────────────────────────────
        m = re.search(r"give\s+role\s+([a-z0-9 _-]+?)\s+to\s+(\S+)", t, re.I)
        if not m:
            m = re.search(r"add\s+role\s+([a-z0-9 _-]+?)\s+to\s+(\S+)", t, re.I)
        if m and "squad" not in t and "event" not in t:
            role_name = m.group(1).strip()
            user_ref  = m.group(2).strip().strip("<@!>")
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                role = next((r for r in guild.roles if role_name.lower() in r.name.lower()), None)
            member_t = None
            if user_ref.isdigit():
                member_t = guild.get_member(int(user_ref))
            else:
                member_t = discord.utils.get(guild.members, name=user_ref) or                            next((m for m in guild.members if user_ref.lower() in m.display_name.lower()), None)
            if role and member_t:
                try:
                    await member_t.add_roles(role)
                    return f"✅ Role **{role.name}** given to **{member_t.display_name}**."
                except discord.Forbidden:
                    return f"❌ Bot lacks permission to give **{role.name}** (check bot role hierarchy)."
            return f"❌ Could not find role **{role_name}** or user **{user_ref}**."

        # ── remove role ───────────────────────────────────────────────
        m = re.search(r"remove\s+role\s+([a-z0-9 _-]+?)\s+from\s+(\S+)", t, re.I)
        if m and "bounty" not in t and "registrant" not in t and "event" not in t:
            role_name = m.group(1).strip()
            user_ref  = m.group(2).strip().strip("<@!>")
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                role = next((r for r in guild.roles if role_name.lower() in r.name.lower()), None)
            member_t = None
            if user_ref.isdigit():
                member_t = guild.get_member(int(user_ref))
            else:
                member_t = next((mb for mb in guild.members if user_ref.lower() in mb.display_name.lower()), None)
            if role and member_t:
                try:
                    await member_t.remove_roles(role)
                    return f"✅ Role **{role.name}** removed from **{member_t.display_name}**."
                except discord.Forbidden:
                    return f"❌ Bot lacks permission to remove **{role.name}**."
            return f"❌ Role **{role_name}** or user **{user_ref}** not found."

        # ── create role ───────────────────────────────────────────────
        m = re.search(r"create role ([a-z0-9 _-]+?)(?:\s+color (\S+))?$", t, re.I)
        if m:
            role_name  = m.group(1).strip()
            color_name = m.group(2) or "default"
            color_map  = {"red":discord.Color.red(),"blue":discord.Color.blue(),
                          "green":discord.Color.green(),"gold":discord.Color.gold(),
                          "purple":discord.Color.purple(),"orange":discord.Color.orange(),
                          "default":discord.Color.default()}
            color = color_map.get(color_name.lower(), discord.Color.default())
            try:
                new_role = await guild.create_role(name=role_name, color=color)
                return f"✅ Role **{new_role.name}** created."
            except discord.Forbidden:
                return "❌ Bot lacks permission to create roles."

        # ── delete role ───────────────────────────────────────────────
        m = re.search(r"delete role ([a-z0-9 _-]+)", t, re.I)
        if m:
            role_name = m.group(1).strip()
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                role = next((r for r in guild.roles if role_name.lower() in r.name.lower()), None)
            if role:
                try:
                    await role.delete()
                    return f"✅ Role **{role_name}** deleted."
                except discord.Forbidden:
                    return "❌ Bot lacks permission to delete that role."
            return f"❌ Role **{role_name}** not found."

        # ── create channel ────────────────────────────────────────────
        m = re.search(r"create channel ([a-z0-9 _-]+?)(?:\s+in ([a-z0-9 _-]+))?$", t, re.I)
        if m and "event" not in t:
            ch_name  = m.group(1).strip().replace(" ","-").lower()
            cat_name = m.group(2).strip() if m.group(2) else None
            category = None
            if cat_name:
                category = discord.utils.get(guild.categories, name=cat_name)
                if not category:
                    category = next((c for c in guild.categories if cat_name.lower() in c.name.lower()), None)
            try:
                new_ch = await guild.create_text_channel(ch_name, category=category)
                return f"✅ Channel **#{new_ch.name}** created{(' in category **'+category.name+'**') if category else ''}."
            except discord.Forbidden:
                return "❌ Bot lacks permission to create channels."

        # ── delete channel ────────────────────────────────────────────
        m = re.search(r"delete channel #?([a-z0-9 _-]+)", t, re.I)
        if m:
            ch_name = m.group(1).strip().replace(" ","-").lower()
            ch = discord.utils.get(guild.text_channels, name=ch_name)
            if not ch:
                ch = next((c for c in guild.text_channels if ch_name in c.name.lower()), None)
            if ch:
                try:
                    await ch.delete()
                    return f"✅ Channel **#{ch_name}** deleted."
                except discord.Forbidden:
                    return "❌ Bot lacks permission to delete that channel."
            return f"❌ Channel **#{ch_name}** not found."

        # ── kick member ───────────────────────────────────────────────
        m = re.search(r'kick\s+<?@?!?(\d+|[a-z0-9_.# ]+)>?(?:\s+(?:for|reason)\s*:?\s*(.+))?$', t, re.I)
        if m:
            user_ref = m.group(1).strip().strip("<@!>")
            reason   = m.group(2) or "Removed by moderator via Oracle"
            member_t = None
            if user_ref.isdigit():
                member_t = guild.get_member(int(user_ref))
            else:
                member_t = next((mb for mb in guild.members if user_ref.lower() in mb.display_name.lower()), None)
            if member_t:
                try:
                    await member_t.kick(reason=reason)
                    return f"✅ **{member_t.display_name}** has been kicked. Reason: {reason}"
                except discord.Forbidden:
                    return "❌ Bot lacks permission to kick that member."
            return f"❌ Member **{user_ref}** not found."

        # ── get member profile ────────────────────────────────────────
        m = re.search(r'(?:get|show|view)\s+profile\s+(?:of\s+|for\s+)?<?@?!?(\d+|[a-z0-9_.# ]+)>?', t, re.I)
        if m:
            user_ref = m.group(1).strip().strip("<@!>")
            member_t = None
            if user_ref.isdigit():
                member_t = guild.get_member(int(user_ref))
            else:
                member_t = next((mb for mb in guild.members if user_ref.lower() in mb.display_name.lower()), None)
            if member_t:
                sd2  = self.squad_data
                pid  = str(member_t.id)
                prof = sd2.get("profiles",{}).get(pid)
                sq_name, sq_tag = "None", ""
                for sname, sinfo in sd2.get("squads",{}).items():
                    roster = sinfo.get("main_roster",[]) + sinfo.get("subs",[])
                    if member_t.id in roster or pid in [str(x) for x in roster]:
                        sq_name = sname
                        sq_tag  = self.squads.get(sname,"")
                        break
                roles_str = ", ".join(r.name for r in member_t.roles if r.name != "@everyone")
                info = (
                    f"**{member_t.display_name}** (ID:{pid})\n"
                    f"Kingdom: {sq_tag} {sq_name}\n"
                    f"Roles: {roles_str or 'none'}\n"
                    f"Joined: {member_t.joined_at.strftime('%Y-%m-%d') if member_t.joined_at else '?'}\n"
                )
                if prof:
                    info += (
                        f"IGN: {prof.get('ingame_name','?')} | "
                        f"ID: {prof.get('ingame_id','?')} | "
                        f"Rank: {prof.get('rank','?')}"
                    )
                return info
            return f"❌ Member **{user_ref}** not found."

        # ── list all members ──────────────────────────────────────────
        m = re.search(r"(?:list|show)\s+(?:all\s+)?members(?:\s+with\s+role\s+([a-z0-9 _-]+))?", t, re.I)
        if m:
            role_filter = m.group(1).strip() if m.group(1) else None
            if role_filter:
                role = discord.utils.get(guild.roles, name=role_filter)
                if not role:
                    role = next((r for r in guild.roles if role_filter.lower() in r.name.lower()), None)
                members_list = [mb.display_name for mb in (role.members if role else [])]
                return f"**{role_filter}** members ({len(members_list)}): {', '.join(members_list[:30]) or 'none'}"
            else:
                names = [mb.display_name for mb in guild.members if not mb.bot]
                return f"**Server members** ({len(names)}): {', '.join(names[:40])}{'...' if len(names)>40 else ''}"

        # ── add to squad/kingdom ──────────────────────────────────────
        m = re.search(r"add\s+(\S+)\s+to\s+(?:squad|kingdom)\s+([a-z0-9 ]+?)(?:\s+as\s+(sub|main))?$", t, re.I)
        if m:
            user_ref  = m.group(1).strip().strip("<@!>")
            sq_name   = m.group(2).strip()
            slot_type = (m.group(3) or "main").lower()
            member_t  = None
            if user_ref.isdigit():
                member_t = guild.get_member(int(user_ref))
            else:
                member_t = next((mb for mb in guild.members if user_ref.lower() in mb.display_name.lower()), None)
            sq_match = fuzzy(sq_name, sd.get("squads",{}))
            if member_t and sq_match:
                sq_info = sd["squads"][sq_match]
                slot = "subs" if "sub" in slot_type else "main_roster"
                if member_t.id not in sq_info.get(slot,[]):
                    sq_info.setdefault(slot,[]).append(member_t.id)
                    save()
                return f"✅ **{member_t.display_name}** added to **{sq_match}** ({slot})."
            return f"❌ Member **{user_ref}** or kingdom **{sq_name}** not found."

        # ── oracle usage stats ────────────────────────────────────────
        if re.search(r'(?:oracle|bot)\s+(?:usage|stats|status)', t, re.I):
            used, total, user_counts = self.usage_stats()
            pct     = round(used/total*100) if total else 0
            bar     = "█" * (pct//10) + "░" * (10 - pct//10)
            groq_ok = "✅" if self.groq else "❌"
            gem_ok  = "✅" if self.gemini_key else "❌"
            top_users = sorted(user_counts.items(), key=lambda x: -x[1])[:3]
            top_txt   = " | ".join(f"<@{u}>:{n}" for u,n in top_users) or "none yet"
            return (
                f"**🔮 Oracle Status**\n"
                f"Global today: `{bar}` {used}/{total}\n"
                f"Per-user limit: **{DAILY_USER_MAX}** questions/day\n"
                f"Gemini: {gem_ok} | Groq: {groq_ok}\n"
                f"Cooldown: {RATE_SEC}s · Max: {RATE_MIN}/min per user\n"
                f"Most active today: {top_txt}"
            )

        # ── list server roles ─────────────────────────────────────────
        if re.search(r"(?:list|show)\s+(?:all\s+)?(?:server\s+)?roles", t, re.I):
            roles = [r.name for r in reversed(guild.roles) if r.name != "@everyone"]
            return f"**Server Roles** ({len(roles)}): {', '.join(roles)}"

        # ── list channels ─────────────────────────────────────────────
        if re.search(r"(?:list|show)\s+(?:all\s+)?channels", t, re.I):
            channels = [f"#{c.name}" for c in guild.text_channels]
            return f"**Channels** ({len(channels)}): {', '.join(channels[:30])}"



        return None  # no action detected

    # ── AI call: Groq ─────────────────────────────────────────────────

    async def _groq(self, prompt: str) -> str:
        if not self.groq:
            raise RuntimeError("No Groq client")
        # Simple completion — no tool calls, avoids all validation errors
        resp = await self.groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=MAX_TOKENS,
            temperature=0.8,
        )
        return resp.choices[0].message.content or ""

    # ── AI call: Gemini REST ──────────────────────────────────────────

    async def _gemini(self, prompt: str) -> str:
        if not self.gemini_key or not AIOHTTP_OK:
            raise RuntimeError("Gemini not configured")
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{GEMINI_MODEL}:generateContent?key={self.gemini_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": MAX_TOKENS,
                "temperature": 0.8
            }
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                if resp.status == 429:
                    data = await resp.json()
                    raise RuntimeError(f"Gemini quota: {data.get('error',{}).get('message','rate limited')[:80]}")
                if resp.status == 404:
                    raise RuntimeError(f"Gemini model not found — check GEMINI_MODEL name")
                if resp.status == 400:
                    data = await resp.json()
                    raise RuntimeError(f"Gemini bad request: {data.get('error',{}).get('message','')[:80]}")
                if resp.status != 200:
                    raise RuntimeError(f"Gemini HTTP {resp.status}")
                data = await resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Gemini unexpected response: {str(data)[:100]}")

    # ── Build prompt ──────────────────────────────────────────────────

    def _build_prompt(self, username: str, text: str, is_mod: bool,
                      history: list, action_result: str | None) -> str:
        personality = PERSONALITY_MOD if is_mod else PERSONALITY_MEMBER
        ctx         = self.context()

        hist = ""
        for m in history:
            role = "User" if m["role"] == "user" else "Oracle"
            hist += f"{role}: {m['content']}\n"

        action_note = ""
        if action_result:
            action_note = f"\n[ACTION EXECUTED]\n{action_result}\n\nNow confirm this to the user naturally and briefly."

        return (
            f"{personality}\n\n"
            f"{ctx}\n\n"
            f"{'[CONVERSATION HISTORY]' + chr(10) + hist if hist else ''}"
            f"{'[MOD CONTEXT] You are in the mod channel. You can take actions.' if is_mod else ''}\n"
            f"{action_note}\n"
            f"User ({username}): {text}\n\n"
            f"Oracle:"
        )

    # ── Main entry ────────────────────────────────────────────────────

    async def think(self, uid: int, username: str, text: str,
                    guild, channel, invoker, is_mod: bool) -> str:

        history = self.history[uid][-HISTORY:]

        # Mod channel: try to detect and execute an action first
        action_result = None
        if is_mod:
            try:
                action_result = await self._detect_and_execute(text, guild, invoker)
            except Exception as e:
                print(f"⚠️ Action error: {e}")
                action_result = f"❌ Action failed: {str(e)[:100]}"

        prompt = self._build_prompt(username, text, is_mod, history, action_result)

        # Try primary AI → fallback silently (no API names shown to users)
        reply = None
        try:
            reply = await self._gemini(prompt)
        except Exception as e:
            print(f"⚠️ Primary AI error: {e}")
            try:
                reply = await self._groq(prompt)
            except Exception as e2:
                print(f"⚠️ Fallback AI error: {e2}")
                err = str(e2).lower()
                if "429" in str(e2) or "rate" in err or "quota" in err or "token" in err:
                    reply = "🔮 I'm a little overwhelmed right now — give me a minute and try again!"
                elif action_result:
                    reply = action_result
                else:
                    reply = "🔮 I need a moment to recover — try again shortly."

        # Clean any leaked text — function calls, API names, technical errors
        if reply:
            reply = re.sub(r'<function=[^>]+>[^<]*</function>', '', reply)
            reply = re.sub(r'<function=[^/]+/>', '', reply)
            # Remove any accidentally leaked API references
            reply = re.sub(r'\(Groq backup[^)]*\)', '', reply, flags=re.I)
            reply = re.sub(r'\(using backup[^)]*\)', '', reply, flags=re.I)
            reply = re.sub(r'Groq:|Gemini:', '', reply, flags=re.I)
            reply = reply.strip()

        # Update history
        self.history[uid] = (history + [
            {"role": "user",      "content": text},
            {"role": "assistant", "content": reply or ""}
        ])[-HISTORY * 2:]

        return reply or "🔮 The Oracle is momentarily lost in thought..."


# ═════════════════════════════════════════════════════════════════════
#  Discord wiring
# ═════════════════════════════════════════════════════════════════════

def setup_oracle(bot, oracle: OracleAgent):

    def _is_mod_channel(channel):
        return MOD_ORACLE_CHANNEL in channel.name.lower()

    def _is_oracle_channel(channel):
        return (ROYAL_ORACLE_CHANNEL in channel.name.lower() or
                MOD_ORACLE_CHANNEL in channel.name.lower())

    def _user_is_mod(member):
        if not member: return False
        return any(r.name == "KNIGHTS" for r in member.roles)

    @bot.listen("on_message")
    async def oracle_listener(message):
        if message.author.bot: return

        in_oracle  = _is_oracle_channel(message.channel)
        is_mention = bot.user in message.mentions

        if not (in_oracle or is_mention): return

        limited, lmsg = oracle.is_limited(message.author.id)
        if limited:
            await message.reply(lmsg, mention_author=False)
            return

        text = (message.content
                .replace(f"<@{bot.user.id}>","")
                .replace(f"<@!{bot.user.id}>","")
                .strip())
        if not text:
            await message.reply("🔮 Yes? Ask away.", mention_author=False)
            return

        # Determine access level
        # mod-oracle channel AND user has mod role → full access
        # everything else → read-only member access
        member = message.guild.get_member(message.author.id) if message.guild else None
        is_mod = _is_mod_channel(message.channel) and _user_is_mod(member)

        # If non-mod tries to use mod-oracle, redirect them
        if _is_mod_channel(message.channel) and not _user_is_mod(member):
            await message.reply(
                "🛡️ This channel is for the Royal Council only, warrior. "
                "Head to the Royal Oracle channel for assistance.",
                mention_author=False
            )
            return

        async with message.channel.typing():
            reply = await oracle.think(
                uid=message.author.id, username=message.author.display_name,
                text=text, guild=message.guild, channel=message.channel,
                invoker=message.author, is_mod=is_mod
            )

        # Send (split if >2000 chars)
        for i, chunk in enumerate([reply[j:j+1990] for j in range(0,len(reply),1990)]):
            if i == 0: await message.reply(chunk, mention_author=False)
            else: await message.channel.send(chunk)

    @bot.tree.command(name="oracle", description="🔮 Consult the Royal Oracle")
    @app_commands.describe(question="Your question")
    async def oracle_cmd(interaction: discord.Interaction, question: str):
        limited, lmsg = oracle.is_limited(interaction.user.id)
        if limited:
            return await interaction.response.send_message(lmsg, ephemeral=True)
        await interaction.response.defer(thinking=True)
        # /oracle is always member-level (read-only) regardless of who uses it
        reply = await oracle.think(
            uid=interaction.user.id, username=interaction.user.display_name,
            text=question, guild=interaction.guild, channel=interaction.channel,
            invoker=interaction.user, is_mod=False
        )
        for i, chunk in enumerate([reply[j:j+1990] for j in range(0,len(reply),1990)]):
            await interaction.followup.send(chunk)

    @bot.tree.command(name="oracle_clear", description="🔮 Clear your Oracle history")
    async def oracle_clear(interaction: discord.Interaction):
        oracle.history.pop(interaction.user.id, None)
        await interaction.response.send_message("🔮 Memory cleared!", ephemeral=True)

    print("✅ Oracle v2: handlers ready")
    print(f"   Mod channel: any channel containing '{MOD_ORACLE_CHANNEL}'")
    print(f"   Public channel: any channel containing '{ROYAL_ORACLE_CHANNEL}'")
