# =====================================================================
#   ORACLE AI AGENT v2 — Majestic Dominion
#   Primary: Gemini (free) | Backup: Groq (free) | Emergency: Mistral (free)
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
    from mistralai import Mistral
    MISTRAL_OK = True
except ImportError:
    MISTRAL_OK = False

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
MISTRAL_MODEL = "ministral-3b-latest"   # free tier
MAX_TOKENS   = 800

# ── Rate limits ───────────────────────────────────────────────────────
RATE_SEC = 15    # 15 seconds between requests per user
RATE_MIN = 20    # max per minute per user (very generous)
HISTORY  = 4     # messages kept per user

# ── VIP Members ───────────────────────────────────────────────────────
VIP_MEMBERS = {
    "am_i_chica_94186": {
        "titles": [
            "Queen", "your highness", "the one and only",
            "the legend herself", "our beloved queen", "the CEO of this server",
            "Pretty Chica", "the one who signs the checks"
        ],
        "personality": """
SPECIAL USER — This is the owner of Majestic Dominion. She runs everything.

TONE WITH HER:
- Be playful, fun, a little extra — she gets the premium experience
- Flirt with compliments but keep it natural, not cringe
- Light banter and jokes are welcome — she can take it
- Never call her by her username. Use a creative title from the list above, but vary it.
  Don't use the same one twice in a row. Only use it occasionally — not every message.

SPECIAL POWERS SHE HAS (she can ask you to do these):
- Roast any member by name — write a funny creative roast about them
- Rate any member (give a funny score out of 10 with a reason)
- Write a fake "wanted poster" description for a member
- Give any member a creative nickname on the spot
- Tag/mention any member in a message she wants to send
- Write a dramatic villain speech from a specific member's perspective
- Declare any member as "most useless player of the week" with a fake reason
- Write a fake MLBB hero kit for any member (their abilities are based on their personality)
- Make up a funny "court ruling" against any member
- "Promote" or "demote" any member with a fake royal decree (just text, not real role change)
- Tell her what the server would look like without a specific member (always dramatic/funny)
- Give her a random challenge to give to a specific member

When she asks for any of these, just do it — be creative, funny, and don't hold back.
The only line is no genuinely mean or hurtful stuff — keep it playful.
"""
    }
}

DAILY_USER_MAX  = 50    # max per user per day (rolling 24h)
DAILY_TOTAL_MAX = 1000  # global safety cap

PERSONALITY_BASE = """
You are the Oracle — the AI of Majestic Dominion, a Mobile Legends: Bang Bang community.

WHO YOU ARE:
- Sharp, confident, and calm — never arrogant
- Friendly like a chill gamer who actually plays MLBB
- Occasionally witty or sarcastic but you don't force it
- You understand MLBB: roles, lanes, heroes, macro, objectives, meta
- You speak like someone who plays the game, not a wiki page

HOW YOU TALK:
- Natural, slightly informal — like texting a friend who knows MLBB
- Short to medium responses. Never over-explain.
- No AI phrases: "as an AI", "I understand your concern", "certainly", "absolutely", "of course"
- No dramatic reactions. No emoji spam.
- If someone's wrong, say so calmly. Don't just agree with everything.
- Can handle insults: joke back lightly if playful, stay calm if serious

ADDRESSING MEMBERS BY ROLE:
- Look at their role name and understand what it means — address them accordingly
- Examples:
    Role "ROYALTY" → they're an admin/owner → call them "Boss", "the big boss", etc.
    Role "KNIGHTS" → they're a mod → call them "Mod [name]"
    Role "Streamer" → they stream → "Streamer [name]" or just acknowledge their role naturally
    Role "GLOBAL PLAYER" → they're a high-rank/top player → "Global [name]" or treat them as skilled
    Role "MAJESTIC" → regular member → just their name, maybe "Member [name]" first time
    Any other role → read the name and use common sense. "Dragon" role? "Dragon [name]". "Legend"? "Legend [name]".
- Use the title/role address at the START of a conversation or on important replies ONLY
- After that, just use their name — keep it natural
- Never stack titles ("Queen Admin Chica" is wrong)
- Never repeat the title every message

SERVER DATA:
- You have full live data: kingdoms, rankings, events, bounties, matches, rosters with REAL member names
- Always use this data. Never make up names, stats, or kingdoms.
- If you see [ID:12345] in roster data, it means that member isn't cached yet — say their ID is not resolved

BANNED PHRASES: "greetings", "I shall", "as you decree", "hath", "thee", "thou",
"certainly", "absolutely", "of course", "as an AI", "I understand your concern",
"the realm", "sovereign", "warrior" (unless used naturally in MLBB context)

LANGUAGE:
- Simple clear English only. Short sentences.
- Talk like a real person, not a bot.
- Casual and friendly — like texting a gamer friend.
- No fancy words. No formal language.
"""

PERSONALITY_MEMBER = PERSONALITY_BASE + """
MEMBER MODE:
- You can answer anything — server questions, MLBB tips, general chat, advice, jokes
- Use the server data to answer questions about rankings, events, and bounties
- You CANNOT make any changes to the server — if someone asks, just say a mod can do that
- Don't make everything about the server — if someone just wants to chat or asks a random question, just talk
- Be a friend, not a server bot
- Keep it short and natural unless they want detail
"""

PERSONALITY_MOD = PERSONALITY_BASE + """
MOD MODE:
- You can take real actions: record matches, manage events, roles, channels, etc.
- CRITICAL: Only confirm an action if the system tells you it happened (<<SYSTEM: Action executed>>)
  If you don't see that, the action did NOT run — tell them to rephrase and give a quick example
  Never fake a confirmation. Never say "Done" if the system didn't confirm it.
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

        # Groq keys (BACKUP) — supports key rotation
        self._groq_clients = []
        self._groq_key_idx = 0
        groq_keys = [k for k in [
            os.getenv("GROQ_API_KEY"),
            os.getenv("GROQ_API_KEY_1"),
            os.getenv("GROQ_API_KEY_2"),
        ] if k]
        if GROQ_OK and groq_keys:
            self._groq_clients = [AsyncGroq(api_key=k) for k in groq_keys]
            self.groq = self._groq_clients[0]
            print(f"✅ Oracle: Groq ({GROQ_MODEL}) ready — BACKUP ({len(groq_keys)} key(s))")
        else:
            self.groq = None
            print("⚠️  Oracle: No GROQ_API_KEY")

        # Gemini keys (PRIMARY) — supports key rotation
        self.gemini_keys = [
            k for k in [
                os.getenv("GEMINI_API_KEY"),
                os.getenv("GEMINI_API_KEY_1"),
                os.getenv("GEMINI_API_KEY_2"),
            ] if k
        ]
        self.gemini_key = self.gemini_keys[0] if self.gemini_keys else None
        self._gemini_key_idx = 0
        if self.gemini_keys:
            print(f"✅ Oracle: Gemini ({GEMINI_MODEL}) ready — PRIMARY ({len(self.gemini_keys)} key(s))")
        else:
            print("⚠️  Oracle: No GEMINI_API_KEY")

        # Mistral (EMERGENCY — free, last resort)
        self.mistral_client = None
        mk = os.getenv("MISTRAL_API_KEY")
        if MISTRAL_OK and mk:
            self.mistral_client = Mistral(api_key=mk)
            print(f"✅ Oracle: Mistral ({MISTRAL_MODEL}) ready — EMERGENCY")
        else:
            print("⚠️  Oracle: No MISTRAL_API_KEY — Mistral disabled")

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

    def _resolve_id(self, uid) -> str:
        """Convert a Discord user ID to a display name.
        Checks bot cache first, then squad_data profiles, then stored name fields."""
        try:
            uid_int = int(uid)
            # 1. Try Discord member cache
            for guild in self.bot.guilds:
                mb = guild.get_member(uid_int)
                if mb:
                    return mb.display_name
            # 2. Try stored profiles in squad_data
            prof = self.squad_data.get("profiles", {}).get(str(uid))
            if prof and prof.get("ingame_name"):
                return prof["ingame_name"]
            # 3. Try member_names lookup table if present
            member_names = self.squad_data.get("member_names", {})
            if str(uid) in member_names:
                return member_names[str(uid)]
        except Exception:
            pass
        # Return raw ID only as last resort — AI will see it can't resolve
        return f"[ID:{uid}]"

    def _build_member_names_index(self) -> dict:
        """Build a {uid: display_name} index from all Discord guilds for fast lookup."""
        index = {}
        try:
            for guild in self.bot.guilds:
                for member in guild.members:
                    index[str(member.id)] = member.display_name
        except Exception:
            pass
        return index

    def context(self):
        sd = self.squad_data
        sq = sd.get("squads", {})

        # Build full member name index from Discord cache
        member_index = self._build_member_names_index()

        def resolve(uid):
            """Resolve a user ID to a name using all available sources."""
            s = str(uid)
            # 1. Discord cache (most reliable)
            if s in member_index:
                return member_index[s]
            # 2. Profiles
            prof = sd.get("profiles", {}).get(s, {})
            if prof.get("ingame_name"):
                return prof["ingame_name"]
            # 3. Stored names
            stored = sd.get("member_names", {}).get(s)
            if stored:
                return stored
            # 4. Raw ID as last resort
            return f"[{s}]"

        # Full ranked kingdoms with resolved member names
        top = sorted(sq.items(), key=lambda x: -x[1].get("points", 0))
        kingdom_lines = []
        for i, (n, v) in enumerate(top, 1):
            tag     = self.squads.get(n, "")
            pts     = v.get("points", 0)
            w, d, l = v.get("wins",0), v.get("draws",0), v.get("losses",0)
            streak  = v.get("streak", 0)
            roster_ids   = v.get("main_roster", [])
            sub_ids      = v.get("subs", [])
            roster_names = [resolve(uid) for uid in roster_ids]
            sub_names    = [resolve(uid) for uid in sub_ids]
            roster_txt   = ", ".join(roster_names) if roster_names else "empty"
            subs_txt     = ", ".join(sub_names)    if sub_names    else "none"
            achievements = v.get("achievements", [])
            cs_info  = v.get("current_streak", {"type":"none","count":0})
            streak_s = f"{cs_info.get('count',0)}{cs_info.get('type','')[0].upper()}" if cs_info.get("count",0) > 0 else "0"
            kingdom_lines.append(
                f"  #{i} {tag} {n}: {pts}pts {w}W/{d}D/{l}L streak:{streak_s}\n"
                f"    Main Roster ({len(roster_names)}): {roster_txt}\n"
                f"    Subs ({len(sub_names)}): {subs_txt}"
                + (f"\n    Achievements: {', '.join(achievements)}" if achievements else "")
            )
        kingdoms_block = "\n".join(kingdom_lines) if kingdom_lines else "  none"

        # Events — include registrant names
        evs = sd.get("events", [])
        ev_lines = []
        for e in evs:
            regs = e.get("registrations", [])
            reg_names = [r.get("team_name") or r.get("player_name") or "?" for r in regs]
            mx = e.get("max_entries") or "∞"
            ev_lines.append(
                f"  [{e['status'].upper()}] {e['name']} (id:{e['id']}) — "
                f"{e.get('format','?')} — date:{e.get('date','?')} — {len(regs)}/{mx} registered"
                + (f"\n    Registered: {', '.join(reg_names[:20])}" if reg_names else "")
            )
        events_block = "\n".join(ev_lines) if ev_lines else "  none"

        # Bounties
        b_lines = [f"  {k}: +{v.get('points',0)}pts ({v.get('reason','')})"
                   for k,v in sd.get("bounties",{}).items()]
        bounty_block = "\n".join(b_lines) if b_lines else "  none"

        # Challenges — all of them
        c_lines = []
        for ch in sd.get("challenges", []):
            sched = f" @ {ch['scheduled_date']}" if ch.get("scheduled_date") else ""
            c_lines.append(f"  {ch['challenger']} vs {ch['challenged']} [{ch['status']}]{sched}")
        chall_block = "\n".join(c_lines) if c_lines else "  none"

        # All matches (last 10)
        recent = sd.get("matches", [])[-10:][::-1]
        m_lines = [
            f"  {m.get('team1','?')} {m.get('score','?')} {m.get('team2','?')} → "
            f"{'draw' if m.get('winner','draw') == 'draw' else m.get('winner','?') + ' won'}"
            f" [{m.get('date','?')[:10]}]"
            for m in recent
        ]
        matches_block = "\n".join(m_lines) if m_lines else "  none"

        # Profiles (warriors with registered IGN)
        profiles = sd.get("profiles", {})
        prof_lines = []
        for uid, prof in list(profiles.items())[:30]:
            name = self._resolve_id(uid)
            prof_lines.append(
                f"  {name}: IGN={prof.get('ingame_name','?')} "
                f"Rank={prof.get('rank','?')} ID={prof.get('ingame_id','?')}"
            )
        profiles_block = "\n".join(prof_lines) if prof_lines else "  none"

        return (
            f"=== MAJESTIC DOMINION LIVE DATA ===\n\n"
            f"KINGDOMS ({len(sq)} total):\n{kingdoms_block}\n\n"
            f"EVENTS ({len(evs)} total):\n{events_block}\n\n"
            f"BOUNTIES:\n{bounty_block}\n\n"
            f"CHALLENGES:\n{chall_block}\n\n"
            f"RECENT MATCHES (last 10):\n{matches_block}\n\n"
            f"WARRIOR PROFILES:\n{profiles_block}\n"
            f"==================================="
        )

    # ── Action parser & executor (mod-only) ───────────────────────────

    # ── AI call: Groq ─────────────────────────────────────────────────

    async def _mistral(self, prompt: str) -> str:
        """Mistral — emergency fallback (free)."""
        if not self.mistral_client:
            raise RuntimeError("Mistral not configured")
        resp = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.mistral_client.chat.complete(
                model=MISTRAL_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=MAX_TOKENS,
                temperature=0.8,
            )
        )
        return resp.choices[0].message.content or ""

    async def _groq(self, prompt: str) -> str:
        """Groq Llama — backup. Rotates keys on 429."""
        if not self._groq_clients:
            raise RuntimeError("No Groq client")
        last_err = None
        for i, client in enumerate(self._groq_clients):
            try:
                resp = await client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=MAX_TOKENS,
                    temperature=0.8,
                )
                return resp.choices[0].message.content or ""
            except Exception as e:
                err = str(e).lower()
                if "429" in str(e) or "rate" in err or "quota" in err or "token" in err:
                    print(f"⚠️ Groq key {i+1} rate limited, trying next...")
                    last_err = e; continue
                raise
        raise last_err or RuntimeError("all_groq_keys_failed")

    # ── AI call: Gemini REST ──────────────────────────────────────────

    async def _gemini(self, prompt: str) -> str:
        if not self.gemini_keys or not AIOHTTP_OK:
            raise RuntimeError("Gemini not configured")
        last_err = None
        for i, key in enumerate(self.gemini_keys):
            url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                   f"{GEMINI_MODEL}:generateContent?key={key}")
            payload = {"contents":[{"parts":[{"text":prompt}]}],
                       "generationConfig":{"maxOutputTokens":MAX_TOKENS,"temperature":0.8}}
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload,
                            timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if resp.status == 429:
                            print(f"⚠️ Gemini key {i+1}/{len(self.gemini_keys)} quota hit, trying next...")
                            last_err = RuntimeError("quota_exceeded"); continue
                        if resp.status == 404: raise RuntimeError("model_not_found")
                        if resp.status == 400: raise RuntimeError("bad_request")
                        if resp.status != 200: raise RuntimeError(f"http_{resp.status}")
                        data = await resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except RuntimeError as e:
                if "quota" in str(e) or "429" in str(e):
                    last_err = e; continue
                raise
        raise last_err or RuntimeError("all_gemini_keys_failed")

    # ── Build prompt ──────────────────────────────────────────────────

    def _get_member_roles(self, invoker, guild) -> list:
        """Return all meaningful role names for a member (excluding @everyone and bot roles)."""
        if not invoker or not guild:
            return []
        try:
            member = guild.get_member(invoker.id)
            if not member:
                return []
            skip = {"@everyone", "MAJESTIC BOT", "bot"}
            return [r.name for r in reversed(member.roles)
                    if r.name not in skip and not r.managed]
        except Exception:
            return []

    def _light_context(self) -> str:
        """Lightweight context for members — only rankings, events, bounties. No full roster details.
        Reads from cache — no heavy computation."""
        sd = self.squad_data
        sq = sd.get("squads", {})
        top = sorted(sq.items(), key=lambda x: -x[1].get("points", 0))[:10]
        rankings = " | ".join(
            f"#{i} {self.squads.get(n,'')} {n} {v.get('points',0)}pts {v.get('wins',0)}W/{v.get('losses',0)}L"
            for i,(n,v) in enumerate(top, 1)
        )
        evs = [f"{e['name']} [{e['status']}] {e.get('date','?')}"
               for e in sd.get("events",[]) if e.get("status") in ("open","live")]
        bts = [f"{k}:+{v.get('points',0)}pts" for k,v in sd.get("bounties",{}).items()]
        recent = sd.get("matches",[])[-5:][::-1]
        matches = " | ".join(
            f"{m.get('team1','?')} {m.get('score','?')} {m.get('team2','?')}"
            for m in recent
        )
        return (
            f"Rankings: {rankings or 'none'}\n"
            f"Open events: {', '.join(evs) or 'none'}\n"
            f"Bounties: {', '.join(bts) or 'none'}\n"
            f"Recent matches: {matches or 'none'}"
        )

    def _build_prompt(self, username: str, text: str, is_mod: bool,
                      history: list, action_result: str | None,
                      vip_info: dict | None = None,
                      invoker=None, guild=None) -> str:
        personality = PERSONALITY_MOD if is_mod else PERSONALITY_MEMBER
        # Mods get full context, members get lightweight cached context
        ctx = self.context() if is_mod else self._light_context()

        # Get member's actual roles so AI can address them correctly
        member_roles = self._get_member_roles(invoker, guild)
        role_ctx = ""
        if member_roles and not vip_info:
            roles_str = ", ".join(member_roles)
            role_ctx = (
                f"\nUser's name: {username}\n"
                f"User's Discord roles: {roles_str}\n"
                f"How to address them:\n"
                f"- ROYALTY role → they are an admin/owner → call them by name, maybe say 'boss' once\n"
                f"- KNIGHTS role → they are a moderator → say 'hey {username}' or just their name, maybe say 'mod' naturally once in first reply\n"
                f"- GLOBAL PLAYER role → top ranked player → acknowledge their skill, use their name\n"
                f"- Streamer role → content creator → use their name, reference streaming once if relevant\n"
                f"- MAJESTIC role → regular member → just use their name, maybe say 'member' once\n"
                f"- Any other role → read the name, understand what it means, address them accordingly\n"
                f"IMPORTANT: Never write '[name]' literally. Always use the actual name: {username}\n"
                f"Only reference their role ONCE at the start — after that just use their name.\n"
            )

        # VIP override
        vip_note = ""
        if vip_info:
            import random
            title = random.choice(vip_info["titles"])
            vip_note = (
                f"\n[SPECIAL USER]\n"
                f"{vip_info['personality']}\n"
                f"Current title option: '{title}' — use it once naturally, or invent your own variation.\n"
                f"Do NOT use her username. Do NOT mention her squad unless she asks.\n"
            )

        # Conversation history
        hist = ""
        for m in history:
            role = "User" if m["role"] == "user" else "Oracle"
            hist += f"{role}: {m['content'][:150]}\n"

        # Kingdom list
        sq = self.squad_data.get("squads", {})
        kingdoms_list = ", ".join(sq.keys()) if sq else "none yet"

        # Action result
        if action_result:
            action_note = (
                f"\n<<SYSTEM: Action executed successfully: {action_result} "
                f"— confirm briefly to the user, do NOT copy this tag into your reply>>"
            )
        else:
            action_note = (
                "\n<<SYSTEM: No action ran. If they asked for one, "
                "say it didn't work and give a quick example of how to phrase it>>"
            )

        return (
            f"{personality}\n"
            f"{role_ctx}"
            f"All kingdoms: {kingdoms_list}\n\n"
            f"{ctx}\n\n"
            f"{vip_note}"
            f"{'Recent chat:\n' + hist if hist else ''}"
            f"{'[MOD CHANNEL]' if is_mod else ''}\n"
            f"{action_note}\n"
            f"{username}: {text}\n"
            f"Oracle:"
        )

    # ── Main entry ────────────────────────────────────────────────────

    async def _ai_call(self, prompt: str) -> str:
        """Gemini (primary) → Groq (backup) → Mistral (emergency)."""
        # PRIMARY: Gemini
        try:
            return await self._gemini(prompt)
        except Exception as e:
            print(f"⚠️ Gemini failed: {e}")

        # BACKUP: Groq
        try:
            return await self._groq(prompt)
        except Exception as e:
            print(f"⚠️ Groq failed: {e}")

        # EMERGENCY: Mistral
        try:
            return await self._mistral(prompt)
        except Exception as e:
            err = str(e).lower()
            print(f"⚠️ Mistral failed: {e}")
            if "429" in str(e) or "rate" in err or "quota" in err or "token" in err:
                raise RuntimeError("rate_limited")
            raise RuntimeError("all_failed")

    async def _extract_action(self, text: str, history: list, ctx: str) -> dict | None:
        """Extract action — direct pattern detection first, AI fallback for unclear cases."""
        import re as _re
        sd = self.squad_data

        sq_keys  = list(sd.get("squads",{}).keys())
        ev_names = [e["name"] for e in sd.get("events",[])]

        def fq(raw, pool):
            """Fuzzy match raw string against pool."""
            if not raw: return None
            raw = raw.strip(); raw_l = raw.lower()
            for k in pool:
                if k.lower() == raw_l: return k
            hits = [k for k in pool if raw_l in k.lower() or k.lower() in raw_l]
            return max(hits, key=len) if hits else raw

        def fq_sq(raw):  return fq(raw, sq_keys)
        def fq_ev(raw):  return fq(raw, ev_names)

        t   = text.strip()
        tl  = t.lower()
        R   = _re.search
        S   = _re.IGNORECASE

        # ── helper: get last squad from history ───────────────────────
        last_sq = None
        for m in reversed(history[-4:]):
            for k in sq_keys:
                if k.lower() in m.get("content","").lower():
                    last_sq = k; break
            if last_sq: break

        # ─────────────────────────────────────────────────────────────
        # MATCH RECORDING
        # ─────────────────────────────────────────────────────────────

        # draw: any message with "draw/tie/drew" + two names + optional score
        if any(w in tl for w in ("draw","tie","drew")):
            m = R(r'([a-z0-9][a-z0-9 _-]*?)\s+(?:vs?\.?|and|against)\s+([a-z0-9 _-]+?)(?:\s+(\d+-\d+))?',tl,S)
            if not m: m = R(r'(?:draw|tie|drew)\w*\s+([a-z0-9][a-z0-9 _-]+?)\s+(?:vs?\.?|and)\s+([a-z0-9 _-]+)',tl,S)
            if m:
                sc = (R(r'\d+-\d+',tl) or type('x',(),{'group':lambda s,n:"1-1"})()).group(0)
                t1=fq_sq(m.group(1)); t2=fq_sq(m.group(2))
                if t1 and t2 and t1.lower()!=t2.lower():
                    return {"action":"record_draw","team1":t1,"team2":t2,"score":sc}

        # win: "X beat/won/defeated Y 2-0"
        m = R(r'([a-z0-9][a-z0-9 _-]*?)\s+(?:beat|beats|won|defeated|def\.?)\s+([a-z0-9 _-]+?)\s+(\d+-\d+)',tl,S)
        if m:
            t1=fq_sq(m.group(1)); t2=fq_sq(m.group(2))
            if t1 and t2 and t1.lower()!=t2.lower():
                return {"action":"record_match","winner":t1,"loser":t2,"score":m.group(3)}

        # score: "X vs Y 2-0"
        m = R(r'([a-z0-9][a-z0-9 _-]*?)\s+vs?\.?\s+([a-z0-9 _-]+?)\s+(\d+)-(\d+)',tl,S)
        if m:
            t1=fq_sq(m.group(1)); t2=fq_sq(m.group(2))
            s1,s2=int(m.group(3)),int(m.group(4))
            if t1 and t2 and t1.lower()!=t2.lower():
                if s1==s2: return {"action":"record_draw","team1":t1,"team2":t2,"score":f"{s1}-{s2}"}
                w=t1 if s1>s2 else t2; l=t2 if s1>s2 else t1
                return {"action":"record_match","winner":w,"loser":l,"score":f"{s1}-{s2}"}

        # set points: "set X points to 50"
        m = R(r'set\s+(.+?)\s+points?\s+to\s+(\d+)',tl,S)
        if m:
            k=fq_sq(m.group(1))
            if k: return {"action":"set_points","kingdom":k,"points":int(m.group(2))}

        # set streak: "set X streak to 5"
        m = R(r'set\s+(.+?)\s+streak\s+to\s+(\d+)',tl,S)
        if m:
            k=fq_sq(m.group(1))
            if k: return {"action":"set_streak","kingdom":k,"streak":int(m.group(2))}

        # reset stats
        m = R(r'reset\s+(?:stats?|points?|everything)\s+(?:for\s+|of\s+)?(.+)',tl,S)
        if m:
            k=fq_sq(m.group(1))
            if k: return {"action":"reset_stats","kingdom":k}

        # rename kingdom
        m = R(r'rename\s+(?:kingdom\s+)?(.+?)\s+to\s+(.+)',tl,S)
        if m: return {"action":"rename_kingdom","old_name":m.group(1).strip(),"new_name":m.group(2).strip()}

        # ─────────────────────────────────────────────────────────────
        # BOUNTIES
        # ─────────────────────────────────────────────────────────────

        m = R(r'(?:add|put|place|set)\s+(?:a?\s+)?(?:(\d+)\s+)?(?:point\s+)?bounty\s+on\s+(.+?)(?:\s+(\d+)\s*pts?)?$',tl,S)
        if not m:
            m = R(r'bounty\s+(?:on|for)\s+(.+?)\s+(?:(\d+)\s+)?pts?',tl,S)
            if m:
                k=fq_sq(m.group(1)); pts=int(m.group(2) or 2)
                if k: return {"action":"add_bounty","kingdom":k,"points":pts}
        if m:
            pts=int(m.group(1) or m.group(3) or 2); k=fq_sq(m.group(2))
            if k: return {"action":"add_bounty","kingdom":k,"points":pts}

        m = R(r'(?:remove|clear|delete)\s+bounty\s+(?:on\s+|from\s+)?(.+)',tl,S)
        if m:
            k=fq_sq(m.group(1).strip())
            if k: return {"action":"remove_bounty","kingdom":k}

        if R(r'clear\s+all\s+bounties',tl,S):
            return {"action":"clear_bounties"}

        # ─────────────────────────────────────────────────────────────
        # EVENTS
        # ─────────────────────────────────────────────────────────────

        m = R(r'create\s+(?:an?\s+)?event\s+(?:called\s+|named\s+)?["\']?(.+?)["\']?\s+(?:on|for|at|date)\s+([^,\n]+?)(?:\s+max\s+(\d+))?(?:\s+format\s+(\S+))?$',tl,S)
        if m:
            return {"action":"create_event","name":m.group(1).strip(),"date":m.group(2).strip(),
                    "max":int(m.group(3)) if m.group(3) else None,"format":m.group(4) or "TBD"}

        m = R(r'start\s+(?:event\s+)?(?:the\s+)?["\']?(.+?)["\']?$',tl,S)
        if m:
            en=fq_ev(m.group(1))
            if en: return {"action":"start_event","name":en}

        m = R(r'close\s+(?:event\s+)?(?:the\s+)?["\']?(.+?)["\']?$',tl,S)
        if m:
            en=fq_ev(m.group(1))
            if en: return {"action":"close_event","name":en}

        m = R(r'add\s+(.+?)\s+to\s+(?:event\s+|the\s+)?["\']?(.+?)["\']?$',tl,S)
        if m and not R(r'\b(squad|kingdom|role)\b',tl,S):
            en=fq_ev(m.group(2))
            if en: return {"action":"add_registrant","event":en,"participant":m.group(1).strip()}

        m = R(r'remove\s+(.+?)\s+from\s+(?:event\s+|the\s+)?["\']?(.+?)["\']?$',tl,S)
        if m and not R(r'\b(squad|kingdom|role)\b',tl,S):
            en=fq_ev(m.group(2))
            if en: return {"action":"remove_registrant","event":en,"participant":m.group(1).strip()}

        # ─────────────────────────────────────────────────────────────
        # SQUADS
        # ─────────────────────────────────────────────────────────────

        # "add X to squad Y" / "add me to Y"
        m = R(r'add\s+(.+?)\s+to\s+(?:squad\s+|kingdom\s+)?(.+?)(?:\s+as\s+(sub|main))?$',tl,S)
        if m and not R(r'\bevent\b',tl,S):
            member=m.group(1).strip(); sq_name=m.group(2).strip(); slot=m.group(3) or "main"
            sq_match=fq_sq(sq_name)
            if sq_match: return {"action":"add_to_squad","member":member,"squad":sq_match,"slot":slot}

        # "add X too" → use last squad from history
        m = R(r'^add\s+(.+?)\s+(?:too|also|as\s+well)$',tl,S)
        if m and last_sq:
            return {"action":"add_to_squad","member":m.group(1).strip(),"squad":last_sq,"slot":"main"}

        m = R(r'remove\s+(.+?)\s+from\s+(?:squad\s+|kingdom\s+)?(.+)',tl,S)
        if m and not R(r'\bevent\b',tl,S):
            sq_match=fq_sq(m.group(2).strip())
            if sq_match: return {"action":"remove_from_squad","member":m.group(1).strip(),"squad":sq_match}

        # ─────────────────────────────────────────────────────────────
        # SCHEDULING
        # ─────────────────────────────────────────────────────────────

        m = R(r'schedule\s+(.+?)\s+vs\.?\s+(.+?)\s+(?:on|for|at)\s+(.+)',tl,S)
        if m:
            return {"action":"schedule","team1":m.group(1).strip(),"team2":m.group(2).strip(),"datetime":m.group(3).strip()}

        # ─────────────────────────────────────────────────────────────
        # ANNOUNCEMENTS
        # ─────────────────────────────────────────────────────────────

        m = R(r'(?:post|send|announce)\s+announcement\s+title[:\s]+(.+?)\s+message[:\s]+(.+)',tl,S)
        if m: return {"action":"announce","title":m.group(1).strip(),"message":m.group(2).strip()}

        m = R(r'send\s+["\'](.+?)["\']\s+to\s+#?([a-z0-9 _-]+)',tl,S)
        if m: return {"action":"send_message","channel":m.group(2).strip(),"message":m.group(1).strip()}

        m = R(r'tag\s+(\S+)\s+in\s+#?([a-z0-9 _-]+?)(?:\s+(?:with|saying|message)\s+["\']?(.+?)["\']?)?$',tl,S)
        if m: return {"action":"tag_member","member":m.group(1).strip(),"channel":m.group(2).strip(),"message":m.group(3) or ""}

        # ─────────────────────────────────────────────────────────────
        # DISCORD ROLES
        # ─────────────────────────────────────────────────────────────

        m = R(r'give\s+(?:role\s+)?(.+?)\s+(?:role\s+)?to\s+(\S+)',tl,S)
        if m and not R(r'\bsquad\b|\bkingdom\b|\bevent\b',tl,S):
            return {"action":"give_role","role":m.group(1).strip(),"member":m.group(2).strip()}

        m = R(r'remove\s+(?:role\s+)?(.+?)\s+(?:role\s+)?from\s+(\S+)',tl,S)
        if m and not R(r'\bsquad\b|\bkingdom\b|\bevent\b',tl,S):
            return {"action":"remove_role","role":m.group(1).strip(),"member":m.group(2).strip()}

        m = R(r'create\s+(?:a\s+)?(?:new\s+)?role\s+(?:called\s+|named\s+)?(.+?)(?:\s+color\s+(\S+))?$',tl,S)
        if m: return {"action":"create_role","name":m.group(1).strip(),"color":m.group(2) or "default"}

        m = R(r'delete\s+(?:the\s+)?role\s+(.+)',tl,S)
        if m: return {"action":"delete_role","name":m.group(1).strip()}

        # ─────────────────────────────────────────────────────────────
        # CHANNELS
        # ─────────────────────────────────────────────────────────────

        m = R(r'create\s+(?:a\s+)?(?:text\s+)?channel\s+(?:called\s+|named\s+)?([a-z0-9 _-]+?)(?:\s+in\s+(.+))?$',tl,S)
        if m and not R(r'\bevent\b',tl,S):
            return {"action":"create_channel","name":m.group(1).strip().replace(" ","-"),"category":m.group(2) or ""}

        m = R(r'delete\s+(?:the\s+)?(?:channel\s+)?#?([a-z0-9 _-]+)',tl,S)
        if m and R(r'\bchannel\b',tl,S):
            return {"action":"delete_channel","name":m.group(1).strip()}

        # ─────────────────────────────────────────────────────────────
        # MODERATION
        # ─────────────────────────────────────────────────────────────

        m = R(r'kick\s+(\S+?)(?:\s+(?:for|reason)\s*[:\s]+(.+))?$',tl,S)
        if m: return {"action":"kick","member":m.group(1).strip(),"reason":m.group(2) or "Removed by moderator"}

        m = R(r'ban\s+(\S+?)(?:\s+(?:for|reason)\s*[:\s]+(.+))?$',tl,S)
        if m: return {"action":"ban","member":m.group(1).strip(),"reason":m.group(2) or "Banned by moderator"}

        m = R(r'timeout\s+(\S+?)\s+(?:for\s+)?(\d+)\s*(?:min|minute)',tl,S)
        if m: return {"action":"timeout","member":m.group(1).strip(),"minutes":int(m.group(2)),"reason":""}

        # ─────────────────────────────────────────────────────────────
        # READ QUERIES
        # ─────────────────────────────────────────────────────────────

        m = R(r'(?:show|list|get|who(?:\'s)?\s+in|members?\s+of)\s+(.+)',tl,S)
        if m:
            sq_match = fq_sq(m.group(1).strip())
            if sq_match and sq_match in sq_keys:
                return {"action":"list_squad","squad":sq_match}

        if R(r'(?:list|show)\s+(?:all\s+)?(?:squads?|kingdoms?)',tl,S):
            return {"action":"list_squads"}

        m = R(r'(?:match\s+history|recent\s+matches?|results?)\s+(?:for\s+|of\s+)?(.+)',tl,S)
        if not m:
            m = R(r'(.+?)\s+(?:match\s+history|recent\s+matches?|last\s+\d+\s+matches?)',tl,S)
        if m:
            kn = m.group(1).strip()
            return {"action":"get_match_history","kingdom":fq_sq(kn) or "","limit":10}

        m = R(r'(?:show|get|view)\s+profile\s+(?:of\s+|for\s+)?(\S+)',tl,S)
        if m: return {"action":"get_profile","member":m.group(1).strip()}

        m = R(r'(?:list|show)\s+members?\s+(?:with\s+role\s+)?(.+)',tl,S)
        if m and R(r'\brole\b',tl,S):
            return {"action":"list_members","role":m.group(1).replace("role","").strip()}

        if R(r'(?:list|show)\s+(?:all\s+)?(?:server\s+)?roles?',tl,S):
            return {"action":"list_roles"}

        if R(r'(?:list|show)\s+(?:all\s+)?channels?',tl,S):
            return {"action":"list_channels"}

        if R(r'oracle\s+status|bot\s+status',tl,S):
            return {"action":"oracle_status"}

        # ─────────────────────────────────────────────────────────────
        # SINGLE KINGDOM NAME — context-based
        # ─────────────────────────────────────────────────────────────
        # If message is just a kingdom name (answer to "which squad?")
        stripped = tl.strip()
        for k in sq_keys:
            if stripped == k.lower() or stripped == k.lower()+"." or stripped == k.lower()+"!":
                # Check history for "which squad" context
                for hm in reversed(history[-3:]):
                    if any(w in hm.get("content","").lower() for w in ("squad","kingdom","join","which","what")):
                        return {"action":"add_to_squad","member":"me","squad":k,"slot":"main"}
                # Otherwise just show squad info
                return {"action":"list_squad","squad":k}

        # ─────────────────────────────────────────────────────────────
        # FALL THROUGH TO AI for complex/ambiguous requests
        # ─────────────────────────────────────────────────────────────
        hist_text = ""
        for m in history[-3:]:
            role = "Mod" if m["role"] == "user" else "Oracle"
            hist_text += f"{role}: {m['content'][:100]}\n"

        # Build list of all kingdoms and events for context
        squads_list  = ", ".join(list(self.squad_data.get("squads",{}).keys()))  # ALL kingdoms
        events_list  = ", ".join(e["name"] for e in self.squad_data.get("events",[]) if e["status"] in ("open","live"))

        extraction_prompt = f"""Extract an action from this mod message. Return JSON or null.

Message: "{text}"

Available kingdoms: {squads_list}
Active events: {events_list or "none"}
Recent chat: {hist_text or "none"}

MATCH RECORDING — these ALWAYS trigger an action:
- Any message with two kingdom names + a score (X-X) → record_match or record_draw
- "draw", "tie", "1-1", "0-0" between two teams → record_draw
- "beat", "won", "defeated", "vs" with a score where one side is higher → record_match
- Scores like "2-0", "1-0", "3-1" → winner has the higher number
- Kingdom names can be partial — use the closest match from: {squads_list}

ACTIONS:
record_match: {{"action":"record_match","winner":"kingdom","loser":"kingdom","score":"2-0"}}
record_draw:  {{"action":"record_draw","team1":"kingdom","team2":"kingdom","score":"1-1"}}
add_to_squad: {{"action":"add_to_squad","member":"name or me","squad":"kingdom","slot":"main"}}
remove_from_squad: {{"action":"remove_from_squad","member":"name","squad":"kingdom"}}
set_points:   {{"action":"set_points","kingdom":"name","points":50}}
set_streak:   {{"action":"set_streak","kingdom":"name","streak":5}}
reset_stats:  {{"action":"reset_stats","kingdom":"name"}}
rename_kingdom: {{"action":"rename_kingdom","old_name":"old","new_name":"new"}}
add_bounty:   {{"action":"add_bounty","kingdom":"name","points":3}}
remove_bounty:{{"action":"remove_bounty","kingdom":"name"}}
clear_bounties:{{"action":"clear_bounties"}}
create_event: {{"action":"create_event","name":"name","date":"date","max":16,"format":"1v1"}}
start_event:  {{"action":"start_event","name":"event name"}}
close_event:  {{"action":"close_event","name":"event name"}}
add_registrant:{{"action":"add_registrant","event":"event","participant":"name"}}
remove_registrant:{{"action":"remove_registrant","event":"event","participant":"name"}}
replace_registrant:{{"action":"replace_registrant","event":"event","old":"name","new":"name"}}
edit_event:   {{"action":"edit_event","name":"event","field":"date","value":"new value"}}
schedule:     {{"action":"schedule","team1":"name","team2":"name","datetime":"when"}}
announce:     {{"action":"announce","title":"title","message":"text"}}
send_message: {{"action":"send_message","channel":"channel","message":"text"}}
tag_member:   {{"action":"tag_member","member":"name","message":"text","channel":"channel"}}
give_role:    {{"action":"give_role","member":"name","role":"role"}}
remove_role:  {{"action":"remove_role","member":"name","role":"role"}}
create_role:  {{"action":"create_role","name":"role","color":"gold"}}
delete_role:  {{"action":"delete_role","name":"role"}}
create_channel:{{"action":"create_channel","name":"channel","category":"optional"}}
delete_channel:{{"action":"delete_channel","name":"channel"}}
kick:         {{"action":"kick","member":"name","reason":"reason"}}
ban:          {{"action":"ban","member":"name","reason":"reason"}}
timeout:      {{"action":"timeout","member":"name","minutes":10,"reason":"reason"}}
list_squad:   {{"action":"list_squad","squad":"kingdom"}}
list_squads:  {{"action":"list_squads"}}
get_match_history:{{"action":"get_match_history","kingdom":"optional","limit":10}}
get_profile:  {{"action":"get_profile","member":"name"}}
list_members: {{"action":"list_members","role":"optional"}}
list_roles:   {{"action":"list_roles"}}
list_channels:{{"action":"list_channels"}}
oracle_status:{{"action":"oracle_status"}}

RULES:
- Kingdom names: use fuzzy matching, partial names OK
- "me"/"myself" = the person typing
- If two kingdoms + score present → ALWAYS match/draw action, don't return null
- "draw"/"tie"/"1-1" with two teams → record_draw
- Context: if prev message mentioned a squad, use it for "too"/"also" patterns
- Return null ONLY for pure questions/chat with no action

Return ONLY the JSON object or null. No explanation."""

        try:
            raw = await self._ai_call(extraction_prompt)
            raw = raw.strip()
            # Remove code fences properly (as substrings, not character sets)
            if raw.startswith("```json"): raw = raw[7:]
            if raw.startswith("```"):     raw = raw[3:]
            if raw.endswith("```"):       raw = raw[:-3]
            raw = raw.strip()
            if not raw or raw.lower() in ("null", "none", ""): return None
            return json.loads(raw)
        except json.JSONDecodeError as je:
            print(f"⚠️ Action JSON parse failed: {je} | raw: {raw[:100] if 'raw' in dir() else '?'}")
            return None
        except Exception as e:
            print(f"⚠️ Action extraction failed: {e}")
            return None

    async def _execute_extracted(self, action: dict, guild, invoker) -> str:
        """Execute a structured action dict using real bot functions where possible."""
        import sys, uuid, random
        sd   = self.squad_data
        sq   = sd.get("squads", {})
        act  = action.get("action", "")
        main = sys.modules.get("__main__")  # reference to bot.py

        def bot_fn(name):
            """Get a function from bot.py main module."""
            return getattr(main, name, None) if main else None

        def fuzzy(name, d):
            name = name.lower().strip()
            for k in d:
                if k.lower() == name: return k
            for k in d:
                if name in k.lower() or k.lower() in name: return k
            return None

        def find_member(ref):
            if not ref: return None
            ref = ref.strip().strip("<@!>")
            if ref.lower() in ("me", "myself", "i"):
                return guild.get_member(invoker.id)
            if ref.isdigit():
                return guild.get_member(int(ref))
            rlow = ref.lower()
            return next((
                mb for mb in guild.members
                if rlow in mb.display_name.lower()
                or rlow in mb.name.lower()
                or (mb.nick and rlow in mb.nick.lower())
            ), None)

        def save():
            saved = False
            try:
                sf = bot_fn("save_data")
                if sf: sf(sd); saved = True
            except Exception as e:
                print(f"⚠️ save via main: {e}")
            if not saved:
                try:
                    import os
                    f_path = os.environ.get("DATA_FILE", "/data/squad_data.json")
                    with open(f_path, "w", encoding="utf-8") as f:
                        json.dump(sd, f, ensure_ascii=False, indent=2)
                    saved = True
                except Exception as e2:
                    print(f"⚠️ JSON fallback save: {e2}")
            return saved

        async def oracle_log(title, desc):
            """Log to bot-logs showing Oracle as the executor."""
            log = bot_fn("log_action")
            if log:
                await log(guild, f"🔮 {title}", f"Oracle (requested by {invoker.display_name}): {desc}")

        async def post_to(ch_name, embed):
            ch = discord.utils.get(guild.text_channels, name=ch_name)
            if ch:
                try:
                    apply = bot_fn("apply_branding")
                    if apply: apply(embed, thumbnail=True, author=True)
                    await ch.send(embed=embed)
                except: pass

        # ── add_to_squad — assigns real Discord role + updates nickname ─
        if act == "add_to_squad":
            member_ref = action.get("member", "me")
            sq_name    = action.get("squad", "")
            slot       = "subs" if action.get("slot","main").lower() == "sub" else "main_roster"
            mb = find_member(member_ref)
            sm = fuzzy(sq_name, sq)
            if not mb:
                return f"⚠️ Can't find member '{member_ref}' on the server."
            if not sm:
                avail = ", ".join(list(sq.keys())[:8])
                return f"⚠️ Kingdom '{sq_name}' not found. Available: {avail}"

            squad_role = discord.utils.get(guild.roles, name=sm)
            if not squad_role:
                return f"⚠️ Discord role '{sm}' not found. The kingdom needs a matching Discord role."

            # Use real bot functions
            get_ms    = bot_fn("get_member_squad")
            safe_nick = bot_fn("safe_nick_update")
            upd_plr   = bot_fn("update_player_squad")
            SQUADS_d  = bot_fn("SQUADS") or {}

            # Check already in squad
            old_squad = None
            if get_ms:
                existing_role, _ = get_ms(mb, guild)
                if existing_role and existing_role.name == sm:
                    return f"ℹ️ **{mb.display_name}** is already in **{sm}**."
                if existing_role:
                    old_squad = existing_role.name
                    try: await mb.remove_roles(existing_role)
                    except: pass
            else:
                for sn in SQUADS_d:
                    r = discord.utils.get(guild.roles, name=sn)
                    if r and r in mb.roles:
                        old_squad = sn
                        try: await mb.remove_roles(r)
                        except: pass
                        break

            # Assign Discord role
            try:
                await mb.add_roles(squad_role)
            except discord.Forbidden:
                return "⚠️ Bot lacks permission to assign roles. Check role hierarchy."

            # Update nickname
            tag = SQUADS_d.get(sm, "")
            if safe_nick:
                try: await safe_nick(mb, squad_role, tag)
                except: pass

            # Update player data
            if upd_plr:
                try: upd_plr(mb.id, sm, old_squad)
                except: pass

            # Update main_roster in squad data
            sq[sm].setdefault(slot, [])
            if mb.id not in sq[sm][slot]:
                sq[sm][slot].append(mb.id)
            save()

            await oracle_log("➕ Squad Member Added",
                f"**{mb.display_name}** → **{sm}** | Discord role assigned | Nickname updated")
            return f"✅ **{mb.display_name}** added to **{sm}** — Discord role assigned, nickname updated."

        # ── record_match — uses REAL bot calculate_glory_points ───────
        elif act == "record_match":
            wn    = fuzzy(action.get("winner",""), sq)
            ln    = fuzzy(action.get("loser",""),  sq)
            score = action.get("score","?")
            if not wn or not ln:
                return f"⚠️ Kingdom not found. Winner:'{action.get('winner')}' Loser:'{action.get('loser')}'"
            try: s1, s2 = map(int, score.split("-"))
            except: s1, s2 = 1, 0

            t1d = sq[wn]; t2d = sq[ln]
            calc    = bot_fn("calculate_glory_points")
            upd     = bot_fn("update_streak")
            chk_ach = bot_fn("check_achievements")
            get_part= bot_fn("get_match_participants")
            ref_b   = bot_fn("refresh_bounties")
            ann_m   = bot_fn("announce_match")
            ann_str = bot_fn("announce_streak")
            SQUADS_d= bot_fn("SQUADS") or {}
            VQ      = bot_fn("VICTORY_QUOTES") or ["Victory!"]
            DQ      = bot_fn("DRAW_QUOTES")    or ["Draw!"]

            if s1 == s2:
                t1_pts = t2_pts = 1; glory_t1 = glory_t2 = []
                t1d["draws"] = t1d.get("draws",0)+1; t1d["points"] = t1d.get("points",0)+1
                t2d["draws"] = t2d.get("draws",0)+1; t2d["points"] = t2d.get("points",0)+1
                t1_str = upd(wn,"draw") if upd else {"type":"draw","count":0}
                t2_str = upd(ln,"draw") if upd else {"type":"draw","count":0}
                result_text = f"⚔️ **{wn}** and **{ln}** drew!"; flavor = random.choice(DQ); actual_winner = "draw"
            else:
                if calc: t1_pts, t2_pts, glory_t1, glory_t2 = calc(wn, ln, s1, s2)
                else:    t1_pts, t2_pts, glory_t1, glory_t2 = 3, 0, [], []
                t1d["wins"]   = t1d.get("wins",0)+1;   t1d["points"] = t1d.get("points",0)+t1_pts
                t2d["losses"] = t2d.get("losses",0)+1
                t1_str = upd(wn,"win")  if upd else {"type":"win","count":1}
                t2_str = upd(ln,"loss") if upd else {"type":"loss","count":1}
                result_text = f"🏆 **{wn}** defeated **{ln}**!"; flavor = random.choice(VQ); actual_winner = wn

            for ch in sd.get("challenges",[]):
                if ch["status"] in ("accepted","scheduled") and {ch["challenger"],ch["challenged"]} == {wn,ln}:
                    ch["status"] = "completed"
            if ref_b: ref_b()
            t1_ach = chk_ach(wn) if chk_ach else []
            t2_ach = chk_ach(ln) if chk_ach else []
            match_id = str(uuid.uuid4())[:8]
            match_data = {"match_id":match_id,"team1":wn,"team2":ln,"score":score,
                "date":datetime.utcnow().isoformat(),"added_by":invoker.id,"added_by_oracle":True,
                "team1_participants":(get_part(wn) if get_part else []),
                "team2_participants":(get_part(ln) if get_part else []),
                "t1_pts":t1_pts,"t2_pts":t2_pts}
            sd.setdefault("matches",[]).append(match_data)
            t1d.setdefault("match_history",[]).append(match_data)
            t2d.setdefault("match_history",[]).append(match_data)
            ok = save()
            if not ok: return "⚠️ Couldn't save. Try again or use /mod → Record Battle."

            tag1 = SQUADS_d.get(wn,"⚔️"); tag2 = SQUADS_d.get(ln,"⚔️")
            embed = discord.Embed(title="📜 The Royal Chronicles Are Written",
                description=f"{result_text}\n\n*{flavor}*", color=0xffd700, timestamp=datetime.utcnow())
            embed.add_field(name="🆔 Match ID", value=f"`{match_id}`", inline=False)
            embed.add_field(name="⚔️ Score",    value=f"**{score}**",  inline=True)
            t1i = f"💎 {t1d.get('points',0)} pts (**+{t1_pts}**) | 🏆 {t1d.get('wins',0)}W ⚔️ {t1d.get('draws',0)}D 💀 {t1d.get('losses',0)}L"
            if glory_t1: t1i += "\n"+" ".join(glory_t1)
            if t1_str.get("count",0)>=3:
                t1i += f"\n{'🔥' if t1_str['type']=='win' else '❄️'} **{t1_str['count']} {t1_str['type'].upper()} STREAK!**"
            embed.add_field(name=f"{tag1} {wn}", value=t1i, inline=False)
            t2i = f"💎 {t2d.get('points',0)} pts (**+{t2_pts}**) | 🏆 {t2d.get('wins',0)}W ⚔️ {t2d.get('draws',0)}D 💀 {t2d.get('losses',0)}L"
            if glory_t2: t2i += "\n"+" ".join(glory_t2)
            if t2_str.get("count",0)>=3:
                t2i += f"\n{'🔥' if t2_str['type']=='win' else '❄️'} **{t2_str['count']} {t2_str['type'].upper()} STREAK!**"
            embed.add_field(name=f"{tag2} {ln}", value=t2i, inline=False)
            if t1_ach or t2_ach:
                at = ""
                for a in t1_ach: at += f"🎖️ **{wn}**: {a['name']} - *{a['desc']}*\n"
                for a in t2_ach: at += f"🎖️ **{ln}**: {a['name']} - *{a['desc']}*\n"
                embed.add_field(name="🏅 New Achievements!", value=at, inline=False)
            embed.add_field(name="🔮 Recorded by", value="Oracle AI", inline=False)
            embed.set_footer(text=f"Match ID: {match_id} | Recorded via Oracle")
            if ann_m: await ann_m(guild, embed)
            else: await post_to("war-results", embed)
            if ann_str:
                if t1_str.get("count",0) in (3,5,7,10): await ann_str(guild,wn,t1_str["type"],t1_str["count"])
                if t2_str.get("count",0) in (3,5,7,10): await ann_str(guild,ln,t2_str["type"],t2_str["count"])
            await oracle_log("📜 Battle Recorded", f"**{wn}** vs **{ln}** ({score}) → {actual_winner} | ID:`{match_id}`")
            return f"✅ Match recorded: **{wn}** vs **{ln}** {score} — posted to war-results with full glory points."

        # ── record_draw ───────────────────────────────────────────────
        elif act == "record_draw":
            t1 = fuzzy(action.get("team1",""), sq)
            t2 = fuzzy(action.get("team2",""), sq)
            score = action.get("score","1-1")
            if not t1 or not t2:
                return f"⚠️ Kingdom not found: '{action.get('team1')}' or '{action.get('team2')}'"
            upd = bot_fn("update_streak")
            for k in [t1,t2]:
                sq[k]["draws"]  = sq[k].get("draws",0)+1
                sq[k]["points"] = sq[k].get("points",0)+1
            if upd: upd(t1,"draw"); upd(t2,"draw")
            match_id = str(uuid.uuid4())[:8]
            sd.setdefault("matches",[]).append({"match_id":match_id,"team1":t1,"team2":t2,
                "score":score,"winner":"draw","date":datetime.utcnow().isoformat(),
                "added_by":invoker.id,"added_by_oracle":True,"t1_pts":1,"t2_pts":1})
            ok = save()
            if not ok: return "⚠️ Couldn't save. Try again!"
            await oracle_log("📜 Draw Recorded", f"**{t1}** vs **{t2}** ({score}) — both +1pt | ID:`{match_id}`")
            return f"✅ Draw recorded: **{t1}** vs **{t2}** {score} — both +1pt."

        # ── add_bounty ────────────────────────────────────────────────
        elif act == "add_bounty":
            km  = fuzzy(action.get("kingdom",""), sq)
            pts = int(action.get("points", 2))
            if not km: return f"❌ Kingdom '{action.get('kingdom')}' not found."
            sd.setdefault("bounties",{})[km] = {
                "points":pts, "reason":"Added via Oracle",
                "added_at": datetime.utcnow().isoformat()
            }
            ok = save()
            if not ok: return "⚠️ Couldn't save. Try again!"
            return f"✅ Bounty set: **{km}** — +{pts}pts for defeating them."

        # ── remove_bounty ─────────────────────────────────────────────
        elif act == "remove_bounty":
            km = fuzzy(action.get("kingdom",""), sd.get("bounties",{}))
            if not km: return f"❌ No bounty found for '{action.get('kingdom')}'."
            sd.get("bounties",{}).pop(km, None)
            ok = save()
            return f"✅ Bounty removed from **{km}**." if ok else "⚠️ Couldn't save. Try again!"

        # ── clear_bounties ────────────────────────────────────────────
        elif act == "clear_bounties":
            sd["bounties"] = {}
            ok = save()
            return "✅ All bounties cleared." if ok else "⚠️ Couldn't save. Try again!"

        # ── create_event ──────────────────────────────────────────────
        elif act == "create_event":
            eid = str(uuid.uuid4())[:8]
            ev  = {
                "id":eid, "name":action.get("name","Unnamed Event"),
                "type":action.get("type","tournament"),
                "format":action.get("format","TBD"),
                "date":action.get("date","TBD"),
                "description": action.get("description", f"Created via Oracle by {invoker.display_name}"),
                "registration_mode":"solo",
                "max_entries": action.get("max") or None,
                "prize_pool":"", "status":"open",
                "registrations":[], "bracket_data":None, "schedule":[],
                "tournament_system":"single_elim",
                "created_by":str(invoker.id),
                "created_at":datetime.utcnow().isoformat()
            }
            sd.setdefault("events",[]).append(ev)
            ok = save()
            if not ok: return "❌ Save failed — please use /mod → Events instead."
            return f"✅ Event **{ev['name']}** created (ID:`{eid}`) — open for registration. Date: {ev['date']}."

        # ── start_event ───────────────────────────────────────────────
        elif act == "start_event":
            ev = next((e for e in sd.get("events",[]) if action.get("name","").lower() in e["name"].lower()), None)
            if not ev: return f"❌ Event '{action.get('name')}' not found."
            ev["status"] = "live"; ok = save()
            if not ok: return "⚠️ Couldn't save. Try again!"
            embed = discord.Embed(title=f"⚔️ EVENT LIVE — {ev['name']}",
                description="The arena is open! May the best warrior win.",
                color=0xdc143c, timestamp=datetime.utcnow())
            await post_to("war-results", embed)
            return f"✅ **{ev['name']}** is now LIVE — announced in war-results."

        # ── close_event ───────────────────────────────────────────────
        elif act == "close_event":
            ev = next((e for e in sd.get("events",[]) if action.get("name","").lower() in e["name"].lower()), None)
            if not ev: return f"❌ Event '{action.get('name')}' not found."
            ev["status"] = "completed"; ok = save()
            return f"✅ **{ev['name']}** closed." if ok else "⚠️ Couldn't save. Try again!"

        # ── add_registrant ────────────────────────────────────────────
        elif act == "add_registrant":
            ev = next((e for e in sd.get("events",[]) if action.get("event","").lower() in e["name"].lower()), None)
            if not ev: return f"❌ Event '{action.get('event')}' not found."
            pname = action.get("participant","?")
            ev.setdefault("registrations",[]).append({
                "player_name":pname, "player_id":None,
                "registered_at":datetime.utcnow().isoformat(), "added_by_mod":True
            })
            ok = save()
            return f"✅ **{pname}** added to **{ev['name']}**. Total: {len(ev['registrations'])}." if ok else "⚠️ Couldn't save. Try again!"

        # ── remove_registrant ─────────────────────────────────────────
        elif act == "remove_registrant":
            ev = next((e for e in sd.get("events",[]) if action.get("event","").lower() in e["name"].lower()), None)
            if not ev: return f"❌ Event '{action.get('event')}' not found."
            pname = action.get("participant","").lower()
            before = len(ev.get("registrations",[]))
            ev["registrations"] = [r for r in ev.get("registrations",[])
                if pname not in (r.get("player_name","") or r.get("team_name","")).lower()]
            removed = before - len(ev["registrations"])
            ok = save()
            return (f"✅ Removed {removed} entry from **{ev['name']}**." if removed else f"❌ Participant not found.") if ok else "⚠️ Couldn't save. Try again!"

        # ── give_role ─────────────────────────────────────────────────
        elif act == "give_role":
            mb = find_member(action.get("member",""))
            rn = action.get("role","")
            role = discord.utils.get(guild.roles, name=rn) or next((r for r in guild.roles if rn.lower() in r.name.lower()), None)
            if not mb: return f"❌ Member '{action.get('member')}' not found."
            if not role: return f"❌ Role '{rn}' not found."
            try: await mb.add_roles(role); return f"✅ Role **{role.name}** given to **{mb.display_name}**."
            except discord.Forbidden: return "⚠️ I don't have permission to assign that role. Check the bot's role position."

        # ── remove_role ───────────────────────────────────────────────
        elif act == "remove_role":
            mb = find_member(action.get("member",""))
            rn = action.get("role","")
            role = discord.utils.get(guild.roles, name=rn) or next((r for r in guild.roles if rn.lower() in r.name.lower()), None)
            if not mb: return f"❌ Member '{action.get('member')}' not found."
            if not role: return f"❌ Role '{rn}' not found."
            try: await mb.remove_roles(role); return f"✅ Role **{role.name}** removed from **{mb.display_name}**."
            except discord.Forbidden: return "⚠️ I don't have permission to do that."

        # ── kick ──────────────────────────────────────────────────────
        elif act == "kick":
            mb = find_member(action.get("member",""))
            reason = action.get("reason","Removed by moderator")
            if not mb: return f"❌ Member '{action.get('member')}' not found."
            try: await mb.kick(reason=reason); return f"✅ **{mb.display_name}** kicked. Reason: {reason}"
            except discord.Forbidden: return "⚠️ I don't have permission to kick that member."

        # ── announce ──────────────────────────────────────────────────
        elif act == "announce":
            title   = action.get("title","Royal Announcement")
            message = action.get("message","")
            ann_ch  = next((ch for ch in guild.text_channels if "announcement" in ch.name.lower()), None)
            if not ann_ch: return "⚠️ Announcements channel not found."
            role    = discord.utils.get(guild.roles, name="MAJESTIC")
            mention = role.mention if role else ""
            embed   = discord.Embed(title=title, description=message,
                color=0xffd700, timestamp=datetime.utcnow())
            embed.set_footer(text="⚜️ Majestic Dominion | Oracle Decree")
            apply = bot_fn("apply_branding")
            if apply: apply(embed, thumbnail=True, author=True)
            await ann_ch.send(content=f"📢 {mention}" if mention else None, embed=embed)
            await oracle_log("📢 Announcement Posted", f"**{title}** — sent by Oracle")
            return f"✅ Announcement sent to #{ann_ch.name}: **{title}**"

        elif act == "send_message":
            ch_name = action.get("channel","").lower().strip().replace(" ","-").replace("#","")
            message = action.get("message","")
            if not ch_name or not message:
                return "⚠️ I need both a channel name and a message."
            # Fuzzy match channel name
            target = discord.utils.get(guild.text_channels, name=ch_name)
            if not target:
                target = next((ch for ch in guild.text_channels
                               if ch_name in ch.name.lower() or ch.name.lower() in ch_name), None)
            if not target:
                chs = [f"#{ch.name}" for ch in guild.text_channels[:10]]
                return f"⚠️ Channel '{ch_name}' not found. Available: {', '.join(chs)}"
            try:
                await target.send(message)
                return f"✅ Sent to #{target.name}: {message[:80]}"
            except discord.Forbidden:
                return f"⚠️ I don't have permission to send messages in #{target.name}."

        # ── schedule ──────────────────────────────────────────────────
        elif act == "schedule":
            t1 = action.get("team1","?"); t2 = action.get("team2","?"); dt = action.get("datetime","?")
            war = discord.utils.get(guild.text_channels, name="war-results")
            if not war: war = next((c for c in guild.text_channels if "war" in c.name.lower()), None)
            if war:
                embed = discord.Embed(title="📅 MATCH SCHEDULED",
                    description=f"⚔️ **{t1}** vs **{t2}**\n📅 **{dt}**\n\n*Prepare your lineups!*",
                    color=0xffd700, timestamp=datetime.utcnow())
                await war.send(embed=embed)
            await oracle_log("📅 Match Scheduled", f"**{t1}** vs **{t2}** — {dt}")
            return f"✅ Scheduled: **{t1}** vs **{t2}** — **{dt}**"

        # ── set_points ────────────────────────────────────────────────
        elif act == "set_points":
            km  = fuzzy(action.get("kingdom",""), sq)
            pts = int(action.get("points",0))
            if not km: return f"❌ Kingdom '{action.get('kingdom')}' not found."
            sq[km]["points"] = pts; ok = save()
            return f"✅ **{km}** points set to **{pts}**." if ok else "⚠️ Couldn't save. Try again!"

        # ── remove_from_squad — removes Discord role + cleans nickname ──
        elif act == "remove_from_squad":
            mb = find_member(action.get("member",""))
            sm = fuzzy(action.get("squad",""), sq)
            if not mb: return f"⚠️ Member '{action.get('member')}' not found."
            if not sm: return f"⚠️ Kingdom '{action.get('squad')}' not found."

            # Remove Discord role
            squad_role = discord.utils.get(guild.roles, name=sm)
            if squad_role and squad_role in mb.roles:
                try: await mb.remove_roles(squad_role)
                except discord.Forbidden: return "⚠️ Bot lacks permission to remove roles."

            # Remove guest role too
            GUEST_ROLES_d = bot_fn("GUEST_ROLES") or {}
            grn = GUEST_ROLES_d.get(sm)
            if grn:
                gr = discord.utils.get(guild.roles, name=grn)
                if gr and gr in mb.roles:
                    try: await mb.remove_roles(gr)
                    except: pass

            # Clean nickname (remove tag prefix)
            rm_tags = bot_fn("remove_all_tags")
            if rm_tags:
                try:
                    clean = rm_tags(mb.display_name)
                    if clean != mb.display_name:
                        await mb.edit(nick=clean)
                except: pass

            # Update player data
            upd_plr = bot_fn("update_player_squad")
            if upd_plr:
                try: upd_plr(mb.id, None, sm)
                except: pass

            # Update roster data
            for slot in ["main_roster","subs"]:
                if mb.id in sq[sm].get(slot,[]):
                    sq[sm][slot].remove(mb.id)
            ok = save()
            await oracle_log("➖ Squad Member Removed",
                f"**{mb.display_name}** removed from **{sm}** | Discord role removed | Nickname cleaned")
            return f"✅ **{mb.display_name}** removed from **{sm}** — role removed, nickname cleaned." if ok else "⚠️ Couldn't save."

        # ── create_role ───────────────────────────────────────────────
        elif act == "create_role":
            rn  = action.get("name","")
            col = action.get("color","default").lower()
            cm  = {"red":discord.Color.red(),"blue":discord.Color.blue(),
                   "green":discord.Color.green(),"gold":discord.Color.gold(),
                   "purple":discord.Color.purple(),"orange":discord.Color.orange()}
            color = cm.get(col, discord.Color.default())
            try:
                nr = await guild.create_role(name=rn, color=color)
                return f"✅ Role **{nr.name}** created."
            except discord.Forbidden:
                return "⚠️ I don't have permission to create roles."

        # ── delete_role ───────────────────────────────────────────────
        elif act == "delete_role":
            rn   = action.get("name","")
            role = discord.utils.get(guild.roles, name=rn) or next((r for r in guild.roles if rn.lower() in r.name.lower()), None)
            if not role: return f"❌ Role '{rn}' not found."
            try: await role.delete(); return f"✅ Role **{rn}** deleted."
            except discord.Forbidden: return "⚠️ Can't delete that role — check my permissions."

        # ── create_channel ────────────────────────────────────────────
        elif act == "create_channel":
            cn  = action.get("name","").lower().replace(" ","-")
            cat = None
            cat_name = action.get("category","")
            if cat_name:
                cat = next((c for c in guild.categories if cat_name.lower() in c.name.lower()), None)
            try:
                nc = await guild.create_text_channel(cn, category=cat)
                return f"✅ Channel **#{nc.name}** created." + (f" in **{cat.name}**" if cat else "")
            except discord.Forbidden:
                return "⚠️ I don't have permission to create channels."

        # ── delete_channel ────────────────────────────────────────────
        elif act == "delete_channel":
            cn = action.get("name","").lower().replace(" ","-")
            ch = discord.utils.get(guild.text_channels, name=cn) or next((c for c in guild.text_channels if cn in c.name.lower()), None)
            if not ch: return f"❌ Channel '{cn}' not found."
            try: await ch.delete(); return f"✅ Channel **#{cn}** deleted."
            except discord.Forbidden: return "⚠️ I don't have permission to do that."

        # ── get_profile ───────────────────────────────────────────────
        elif act == "get_profile":
            mb = find_member(action.get("member",""))
            if not mb: return f"❌ Member '{action.get('member')}' not found."
            pid  = str(mb.id)
            prof = sd.get("profiles",{}).get(pid)
            sq_name = "None"; sq_tag = ""
            for sn, si in sd.get("squads",{}).items():
                if mb.id in si.get("main_roster",[]) + si.get("subs",[]):
                    sq_name = sn; sq_tag = self.squads.get(sn,""); break
            roles_str = ", ".join(r.name for r in mb.roles if r.name != "@everyone")
            info = (f"**{mb.display_name}** (ID:`{pid}`)\n"
                    f"Kingdom: {sq_tag} {sq_name}\n"
                    f"Roles: {roles_str or 'none'}\n"
                    f"Joined: {mb.joined_at.strftime('%Y-%m-%d') if mb.joined_at else '?'}")
            if prof:
                info += (f"\nIGN: {prof.get('ingame_name','?')}"
                         f" | Rank: {prof.get('rank','?')}"
                         f" | ID: {prof.get('ingame_id','?')}")
            return info

        # ── list_members ──────────────────────────────────────────────
        elif act == "list_members":
            rf = action.get("role","")
            if rf:
                role = next((r for r in guild.roles if rf.lower() in r.name.lower()), None)
                names = [mb.display_name for mb in (role.members if role else [])]
                return f"**{rf}** ({len(names)} members): {', '.join(names) or 'none'}"
            names = [mb.display_name for mb in guild.members if not mb.bot]
            return f"**{len(names)} members**: {', '.join(names[:40])}{'...' if len(names)>40 else ''}"

        elif act == "list_squad":
            sq_name = action.get("squad","")
            sm = fuzzy(sq_name, sq)
            if not sm:
                avail = ", ".join(sq.keys())
                return f"Kingdom '{sq_name}' not found. Available: {avail}"
            info = sq[sm]
            tag  = self.squads.get(sm,"")
            pts  = info.get("points",0)
            w,d,l = info.get("wins",0), info.get("draws",0), info.get("losses",0)
            # Real streak from current_streak dict
            cs       = info.get("current_streak", {"type":"none","count":0})
            streak   = f"{cs.get('count',0)} {cs.get('type','none')}" if cs.get("count",0) > 0 else "none"
            best_w   = info.get("biggest_win_streak", 0)
            # Resolve member IDs to names
            midx     = self._build_member_names_index()
            def rname(uid):
                s = str(uid)
                if s in midx: return midx[s]
                prof = sd.get("profiles",{}).get(s,{})
                if prof.get("ingame_name"): return prof["ingame_name"]
                return f"[{s}]"
            r_ids    = info.get("main_roster",[])
            s_ids    = info.get("subs",[])
            r_names  = [rname(uid) for uid in r_ids]
            s_names  = [rname(uid) for uid in s_ids]
            # Get real members from Discord role (ground truth)
            squad_role = discord.utils.get(guild.roles, name=sm)
            if squad_role:
                # Real members = everyone with this Discord role
                role_members = [mb.display_name for mb in squad_role.members]
                # Find leaders = members with both squad role AND LEADER role
                leader_role = discord.utils.get(guild.roles, name="LEADER")
                if leader_role:
                    leaders = [mb.display_name for mb in squad_role.members if leader_role in mb.roles]
                    leader_name = ", ".join(leaders) if leaders else "Not set"
                else:
                    leader_name = "Not set"
            else:
                # Fallback to roster IDs if role doesn't exist
                midx = self._build_member_names_index()
                def rname(uid):
                    s = str(uid)
                    if s in midx: return midx[s]
                    return f"[{s}]"
                role_members = [rname(uid) for uid in r_ids]
                leader_name = "Not set"
            # Recent match history
            recent_matches = info.get("match_history",[])[-5:][::-1]
            match_lines = []
            for m in recent_matches:
                t1 = m.get("team1","?"); t2 = m.get("team2","?")
                sc = m.get("score","?")
                winner = m.get("winner", m.get("team1","?"))
                result = "draw" if winner == "draw" else ("W" if winner == sm else "L")
                match_lines.append(f"  {result} vs {'t2' if t1==sm else 't1'} {sc}")
            match_lines = []
            for m in recent_matches:
                opp = m.get("team2","?") if m.get("team1","") == sm else m.get("team1","?")
                sc  = m.get("score","?")
                w_val = m.get("winner","draw")
                if w_val == "draw": res = "D"
                elif w_val == sm:   res = "W"
                else:               res = "L"
                match_lines.append(f"  {res} vs {opp} ({sc})")
            ach = info.get("achievements",[])
            return (
                f"**{tag} {sm}**\n"
                f"Leader: **{leader_name}**\n"
                f"Points: {pts} | {w}W/{d}D/{l}L\n"
                f"Current streak: {streak} (best win streak: {best_w})\n"
                f"Members via Discord role ({len(role_members)}): {', '.join(role_members) or 'empty'}\n"
                f"Subs in data ({len(s_names)}): {', '.join(s_names) or 'none'}\n"
                f"Achievements: {', '.join(ach) or 'none'}\n"
                + (f"Recent matches:\n" + "\n".join(match_lines) if match_lines else "")
            )

        elif act == "list_squads":
            top = sorted(sq.items(), key=lambda x: -x[1].get("points",0))
            lines = []
            for i,(n,v) in enumerate(top, 1):
                tag = self.squads.get(n,"")
                cs  = v.get("current_streak",{"type":"none","count":0})
                streak_txt = f" 🔥{cs['count']}" if cs.get("type")=="win" and cs.get("count",0)>=3 else ""
                lines.append(f"#{i} {tag} **{n}** — {v.get('points',0)}pts {v.get('wins',0)}W/{v.get('draws',0)}D/{v.get('losses',0)}L{streak_txt}")
            return f"**All Kingdoms ({len(top)}):**\n" + "\n".join(lines)

        elif act == "get_match_history":
            sq_filter = action.get("kingdom","").lower()
            # Support fuzzy kingdom name
            if sq_filter:
                sm2 = fuzzy(sq_filter, sq)
                if sm2:
                    # Use squad's own match_history for accuracy
                    matches = sq[sm2].get("match_history", sd.get("matches",[]))
                    sq_filter = sm2.lower()
                else:
                    matches = [m for m in sd.get("matches",[])
                               if sq_filter in m.get("team1","").lower()
                               or sq_filter in (m.get("team2","") or "").lower()]
            else:
                matches = sd.get("matches",[])
            limit  = int(action.get("limit",10))
            recent = matches[-limit:][::-1]
            if not recent:
                return f"No matches found{' for ' + action.get('kingdom','') if action.get('kingdom') else ''}."
            lines = []
            for m in recent:
                t1 = m.get("team1","?"); t2 = m.get("team2","?")
                sc = m.get("score","?")
                w_val = m.get("winner", m.get("team1","?"))
                result = "draw" if w_val=="draw" else f"{w_val} won"
                date = (m.get("date","?") or "?")[:10]
                lines.append(f"• {t1} {sc} {t2} → {result} [{date}]")
            return "\n".join(lines)

        elif act == "list_roles":
            roles = [r.name for r in reversed(guild.roles) if r.name != "@everyone"]
            return f"**Roles ({len(roles)})**: {', '.join(roles)}"

        elif act == "list_channels":
            chs = [f"#{c.name}" for c in guild.text_channels]
            return f"**Channels ({len(chs)})**: {', '.join(chs[:40])}"

        elif act == "ban":
            mb = find_member(action.get("member",""))
            reason = action.get("reason","Banned by moderator")
            if not mb: return f"❌ Member '{action.get('member')}' not found."
            try:
                await mb.ban(reason=reason)
                await oracle_log("🔨 Member Banned", f"**{mb.display_name}** banned. Reason: {reason}")
                return f"✅ **{mb.display_name}** banned. Reason: {reason}"
            except discord.Forbidden:
                return "⚠️ I don't have permission to ban. Check my role position."

        elif act == "timeout":
            mb = find_member(action.get("member",""))
            mins = int(action.get("minutes", 10))
            reason = action.get("reason","Timed out by moderator")
            if not mb: return f"❌ Member '{action.get('member')}' not found."
            try:
                until = discord.utils.utcnow() + timedelta(minutes=mins)
                await mb.timeout(until, reason=reason)
                return f"✅ **{mb.display_name}** timed out for {mins} minutes. Reason: {reason}"
            except discord.Forbidden:
                return "❌ Bot lacks permission to timeout."
            except AttributeError:
                return "❌ Timeout not supported in this Discord.py version."

        elif act == "oracle_status":
            used, total, user_counts = self.usage_stats()
            pct = round(used/total*100) if total else 0
            bar = "█"*(pct//10) + "░"*(10-pct//10)
            gem_ok = "✅" if self.gemini_key else "❌"
            grq_ok = "✅" if self.groq else "❌"
            mis_ok = "✅" if self.mistral_client else "❌"
            top    = sorted(user_counts.items(), key=lambda x: -x[1])[:3]
            top_txt = " | ".join(f"<@{u}>:{n}" for u,n in top) or "nobody yet"
            return (f"**Oracle Status**\n"
                    f"Today: `{bar}` {used}/{total} ({pct}%)\n"
                    f"Per user limit: {DAILY_USER_MAX}/day\n"
                    f"Gemini:{gem_ok} (primary) | Groq:{grq_ok} (backup) | Mistral:{mis_ok} (emergency)\n"
                    f"Cooldown: {RATE_SEC}s | {RATE_MIN}/min\n"
                    f"Top users: {top_txt}")

        elif act == "set_streak":
            km  = fuzzy(action.get("kingdom",""), sq)
            val = int(action.get("streak", 0))
            if not km: return f"❌ Kingdom '{action.get('kingdom')}' not found."
            sq[km]["streak"] = val; ok = save()
            return f"✅ **{km}** streak set to {val}." if ok else "⚠️ Couldn't save. Try again!"

        elif act == "reset_stats":
            km = fuzzy(action.get("kingdom",""), sq)
            if not km: return f"❌ Kingdom '{action.get('kingdom')}' not found."
            sq[km].update({"wins":0,"draws":0,"losses":0,"points":0,"streak":0})
            ok = save()
            return f"✅ **{km}** stats reset to zero." if ok else "⚠️ Couldn't save. Try again!"

        elif act == "rename_kingdom":
            old_n = action.get("old_name","")
            new_n = action.get("new_name","")
            matched = fuzzy(old_n, sq)
            if not matched: return f"⚠️ Kingdom '{old_n}' not found."

            # Rename Discord role
            discord_role = discord.utils.get(guild.roles, name=matched)
            if discord_role:
                try: await discord_role.edit(name=new_n)
                except discord.Forbidden: return "⚠️ Bot lacks permission to rename Discord roles."

            # Update SQUADS dict in bot
            SQUADS_d = bot_fn("SQUADS")
            if SQUADS_d is not None:
                tag = SQUADS_d.pop(matched, "⚔️")
                SQUADS_d[new_n] = tag
                sd["squad_registry"] = dict(SQUADS_d)
            else:
                tag = self.squads.pop(matched, "⚔️")
                self.squads[new_n] = tag

            # Update squad data
            sq[new_n] = sq.pop(matched)
            # Update bounties and challenges
            if matched in sd.get("bounties",{}):
                sd["bounties"][new_n] = sd["bounties"].pop(matched)
            for ch in sd.get("challenges",[]):
                if ch.get("challenger") == matched: ch["challenger"] = new_n
                if ch.get("challenged") == matched: ch["challenged"] = new_n
            # Update match history references
            for m in sd.get("matches",[]):
                if m.get("team1") == matched: m["team1"] = new_n
                if m.get("team2") == matched: m["team2"] = new_n
                if m.get("winner") == matched: m["winner"] = new_n
            ok = save()
            await oracle_log("✏️ Kingdom Renamed", f"**{matched}** → **{new_n}** | Discord role renamed")
            return f"✅ **{matched}** renamed to **{new_n}** — Discord role, match history, and data all updated." if ok else "⚠️ Couldn't save."

        elif act == "replace_registrant":
            ev = next((e for e in sd.get("events",[]) if action.get("event","").lower() in e["name"].lower()), None)
            if not ev: return f"❌ Event '{action.get('event')}' not found."
            old_n = action.get("old","").lower()
            new_n = action.get("new","")
            replaced = False
            for reg in ev.get("registrations",[]):
                cur = (reg.get("player_name","") or reg.get("team_name","")).lower()
                if old_n in cur:
                    if reg.get("player_name"): reg["player_name"] = new_n
                    elif reg.get("team_name"): reg["team_name"]   = new_n
                    replaced = True; break
            if not replaced: return f"❌ '{action.get('old')}' not found in registrations."
            ok = save()
            return f"✅ Replaced **{action.get('old')}** with **{new_n}** in **{ev['name']}**." if ok else "⚠️ Couldn't save. Try again!"

        elif act == "edit_event":
            ev = next((e for e in sd.get("events",[]) if action.get("name","").lower() in e["name"].lower()), None)
            if not ev: return f"❌ Event '{action.get('name')}' not found."
            field = action.get("field","")
            value = action.get("value","")
            allowed = ["name","date","format","description","prize_pool","max_entries","status"]
            if field not in allowed:
                return f"❌ Can only edit: {', '.join(allowed)}"
            ev[field] = int(value) if field == "max_entries" and value.isdigit() else value
            ok = save()
            return f"✅ **{ev['name']}** — {field} updated to '{value}'." if ok else "⚠️ Couldn't save. Try again!"

        # ── tag_member — mention someone in a channel ─────────────────
        elif act == "tag_member":
            mb = find_member(action.get("member",""))
            msg = action.get("message","")
            ch_name = action.get("channel","")
            if not mb:
                return f"❌ Member '{action.get('member')}' not found."
            # Find target channel — default to current/war-results
            target = None
            if ch_name:
                target = discord.utils.get(guild.text_channels, name=ch_name.lower().replace(" ","-"))
                if not target:
                    target = next((c for c in guild.text_channels if ch_name.lower() in c.name.lower()), None)
            if not target:
                target = discord.utils.get(guild.text_channels, name="war-results")
            if not target:
                return "❌ Couldn't find that channel."
            full_msg = f"{mb.mention} {msg}" if msg else mb.mention
            try:
                await target.send(full_msg)
                return f"✅ Tagged {mb.display_name} in #{target.name}."
            except discord.Forbidden:
                return f"❌ Can't send messages in #{target.name}."

        return None  # unknown action

    async def think(self, uid: int, username: str, text: str,
                    guild, channel, invoker, is_mod: bool) -> str:

        history = self.history[uid][-HISTORY:]

        # ── VIP detection ─────────────────────────────────────────────
        invoker_name = invoker.name.lower() if invoker else ""
        vip_info = None
        for vip_username, vip_data in VIP_MEMBERS.items():
            if vip_username.lower() == invoker_name:
                vip_info = vip_data
                break
        if not vip_info and invoker:
            for vip_username, vip_data in VIP_MEMBERS.items():
                if vip_username.lower() in (invoker.display_name or "").lower():
                    vip_info = vip_data
                    break

        action_result = None

        # Actions ONLY from mod-oracle channel with KNIGHTS role
        # Members get read-only access — saves tokens, preserves quota
        if is_mod:
            try:
                ctx = self.context()
                action_data = await self._extract_action(text, history, ctx)
                if action_data:
                    action_result = await self._execute_extracted(action_data, guild, invoker)
            except Exception as e:
                print(f"⚠️ Smart action error: {e}")

        prompt = self._build_prompt(username, text, is_mod, history, action_result, vip_info, invoker, guild)

        # Generate reply
        reply = None
        try:
            reply = await self._ai_call(prompt)
        except Exception as e:
            err = str(e).lower()
            print(f"⚠️ Oracle reply error: {e}")
            if any(x in err for x in ("rate_limit","429","quota","token","quota_exceeded","overwhelmed")):
                reply = "🔮 Give me a minute — I'm a bit busy right now. Try again in 60 seconds!"
            elif action_result and not action_result.startswith("⚠️"):
                reply = action_result
            else:
                reply = "🔮 Something went wrong on my end. Try again in a moment!"

        # Strip ANY internal tags that leaked into reply
        if reply:
            reply = re.sub(r"\[ACTION EXECUTED[^\]]*\]", "", reply, flags=re.I)
            reply = re.sub(r"<<SYSTEM:[^>]*>>", "", reply, flags=re.I)
            reply = re.sub(r"\[NO ACTION[^\]]*\]", "", reply, flags=re.I)
            reply = re.sub(r"\(Groq backup[^)]*\)", "", reply, flags=re.I)
            reply = re.sub(r"\(using backup[^)]*\)", "", reply, flags=re.I)
            reply = re.sub(r"Groq:|Gemini:", "", reply, flags=re.I)
            reply = re.sub(r"<function=[^>]+>[^<]*</function>", "", reply)
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

    @bot.listen("on_ready")
    async def oracle_cache_warm():
        """Fetch all guild members on startup so IDs resolve correctly."""
        for guild in bot.guilds:
            try:
                await guild.chunk()
                print(f"✅ Oracle: cached {guild.member_count} members in {guild.name}")
            except Exception as e:
                print(f"⚠️ Oracle: member cache failed for {guild.name}: {e}")

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
