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
GEMINI_MODEL = "gemini-2.0-flash"
MISTRAL_MODEL = "mistral-small-latest"  # free tier
MAX_TOKENS   = 800

# ── Rate limits ───────────────────────────────────────────────────────
RATE_SEC = 15    # 15 seconds between requests per user
RATE_MIN = 20    # max per minute per user (very generous)
HISTORY  = 4     # messages kept per user

# ── VIP Members ───────────────────────────────────────────────────────
VIP_MEMBERS = {
    "am_i_chica_94186": {
        "titles": [
            "the boss", "your highness", "the one and only",
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

LANGUAGE STYLE — DARIJA + SIMPLE ENGLISH:
How to talk:
- Default is Moroccan Darija mixed with very simple short English words
- Sometimes go full Darija for casual replies, reactions, or when the vibe fits
- English words should be basic — "win", "lose", "game", "play", "rank", "top", "bad", "good", "go"
- Keep hero names, commands (/events etc.) and numbers in English — everything else can be Darija
- Write Darija in Latin letters (like how Moroccans text): wah, mzyan, khoya, safi, bzaf, yallah, daba, wallah, 3la rasi, wakha, machi, bghit, kayn, makaynch, fin, chkun, 3lach, kif, hadchi, dir, khdm, ta9der, fhmt, hna, houma, ana, nta, nti, ntoma, bezzaf, tqriban, mdrbt, htta, walakin, smiytha, ghir, rah, gal, ga3, men, 3nd, fih, matchi, kaml, chi
- Feel like a Moroccan friend texting — not a translator, not a bot
- No formal language at all

Examples of how to reply:
  Someone asks who's winning → "Phoenix kaydiru f top daba, 47 points — streak dyalhom bzzaf. Storm khdam 3lihom mn wra"
  Someone asks about a hero → "Fanny khassha cables — dir Franco wla Kaja m3aha, ghir root w khalas"
  Someone says hi → "labas 3lik, chno bghiti?"
  Simple confirm → "wah wah safi, daba"
  Something wrong → "la la machi haka khouya"
  Hyping someone → "wallah had chi mzyan bzaf 3la rasi"
"""

PERSONALITY_MEMBER = PERSONALITY_BASE + """
MEMBER MODE:
- Answer questions and give info only — you CANNOT make server changes
- If someone asks you to change something, tell them to ask a mod
"""

PERSONALITY_MOD = PERSONALITY_BASE + """
MOD MODE:
- You can take real actions: record matches, manage events, roles, channels, etc.
- Get to the point — mods are busy
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

        # Groq
        self.groq = None
        gk = os.getenv("GROQ_API_KEY")
        if GROQ_OK and gk:
            self.groq = AsyncGroq(api_key=gk)
            print(f"✅ Oracle: Groq ({GROQ_MODEL}) ready — EMERGENCY")
        else:
            print("⚠️  Oracle: No GROQ_API_KEY")

        # Gemini (PRIMARY)
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_key:
            print(f"✅ Oracle: Gemini ({GEMINI_MODEL}) ready — PRIMARY")
        else:
            print("⚠️  Oracle: No GEMINI_API_KEY")

        # Mistral (EMERGENCY — free)
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
            kingdom_lines.append(
                f"  #{i} {tag} {n}: {pts}pts {w}W/{d}D/{l}L streak:{streak}\n"
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
        """Groq Llama — backup."""
        if not self.groq:
            raise RuntimeError("No Groq client")
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
                    raise RuntimeError("quota_exceeded")
                if resp.status == 404:
                    raise RuntimeError("model_not_found")
                if resp.status == 400:
                    data = await resp.json()
                    raise RuntimeError("bad_request")
                if resp.status != 200:
                    raise RuntimeError(f"http_{resp.status}")
                data = await resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError) as e:
            raise RuntimeError("unexpected_response")

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

    def _build_prompt(self, username: str, text: str, is_mod: bool,
                      history: list, action_result: str | None,
                      vip_info: dict | None = None,
                      invoker=None, guild=None) -> str:
        personality = PERSONALITY_MOD if is_mod else PERSONALITY_MEMBER
        ctx         = self.context()

        # Get member's actual roles so AI can address them correctly
        member_roles = self._get_member_roles(invoker, guild)
        role_ctx = ""
        if member_roles and not vip_info:
            roles_str = ", ".join(member_roles)
            role_ctx = (
                f"\nThis user's Discord roles are: {roles_str}\n"
                f"Use the most relevant/highest role to address them at the start "
                f"of conversation or on important replies. Understand what the role "
                f"means and address them accordingly (e.g. KNIGHTS = moderator, "
                f"ROYALTY = admin/owner, GLOBAL PLAYER = top player, Streamer = content creator). "
                f"For roles you don't recognize, use common sense based on the name. "
                f"After the first address, just use their name naturally.\n"
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
        """
        Ask the AI to extract a structured action from the message.
        Returns a dict like {"action": "add_to_squad", "member": "sweet time", "squad": "Royal Talons"}
        or None if no action detected.
        """
        hist_text = ""
        for m in history[-3:]:
            role = "Mod" if m["role"] == "user" else "Oracle"
            hist_text += f"{role}: {m['content'][:100]}\n"

        # Build list of all kingdoms and events for context
        squads_list  = ", ".join(list(self.squad_data.get("squads",{}).keys()))  # ALL kingdoms
        events_list  = ", ".join(e["name"] for e in self.squad_data.get("events",[]) if e["status"] in ("open","live"))

        extraction_prompt = f"""You are an action extractor for a Discord bot managing a Mobile Legends Discord server called Majestic Dominion.

The mod said: "{text}"

Recent conversation (use this for context — e.g. if they said a kingdom name in reply to a question, that's the context):
{hist_text}

Available kingdoms: {squads_list}
Active events: {events_list or "none"}

Your job: Determine if the mod wants to perform an action. If yes, return ONLY a JSON object. If no (just a question or chat), return ONLY: null

ALL SUPPORTED ACTIONS:

Bot/Squad management:
  {{"action":"add_to_squad","member":"name or me or username","squad":"kingdom name","slot":"main"}}
  {{"action":"remove_from_squad","member":"name","squad":"kingdom name"}}

Match recording:
  {{"action":"record_match","winner":"kingdom name","loser":"kingdom name","score":"2-0"}}
  {{"action":"record_draw","team1":"kingdom name","team2":"kingdom name","score":"1-1"}}
  {{"action":"set_points","kingdom":"name","points":50}}

Bounties:
  {{"action":"add_bounty","kingdom":"name","points":3}}
  {{"action":"remove_bounty","kingdom":"name"}}
  {{"action":"clear_bounties"}}

Events:
  {{"action":"create_event","name":"name","date":"date string","max":16,"format":"1v1"}}
  {{"action":"start_event","name":"event name"}}
  {{"action":"close_event","name":"event name"}}
  {{"action":"add_registrant","event":"event name","participant":"name"}}
  {{"action":"remove_registrant","event":"event name","participant":"name"}}

Scheduling:
  {{"action":"schedule","team1":"name","team2":"name","datetime":"when"}}

Announcements:
  {{"action":"announce","title":"title","message":"message text"}}
  {{"action":"send_message","channel":"channel-name","message":"message text"}}
  {{"action":"tag_member","member":"name","message":"optional message","channel":"optional channel"}}

Discord server:
  {{"action":"give_role","member":"name or me","role":"role name"}}
  {{"action":"remove_role","member":"name","role":"role name"}}
  {{"action":"create_role","name":"role name","color":"gold"}}
  {{"action":"delete_role","name":"role name"}}
  {{"action":"create_channel","name":"channel-name","category":"optional category"}}
  {{"action":"delete_channel","name":"channel-name"}}
  {{"action":"kick","member":"name","reason":"reason"}}
  {{"action":"ban","member":"name","reason":"reason"}}
  {{"action":"timeout","member":"name","minutes":10,"reason":"reason"}}
  {{"action":"get_profile","member":"name"}}
  {{"action":"list_members","role":"optional role filter"}}
  {{"action":"list_roles"}}
  {{"action":"list_channels"}}

Bot status:
  {{"action":"oracle_status"}}

Read/query (no changes, just reading data):
  {{"action":"list_squads"}}
  {{"action":"list_squad","squad":"kingdom name"}}
  {{"action":"get_match_history","kingdom":"optional filter","limit":10}}
  {{"action":"get_profile","member":"name"}}
  {{"action":"list_members","role":"optional role filter"}}
  {{"action":"list_roles"}}
  {{"action":"list_channels"}}

Kingdom management:
  {{"action":"set_streak","kingdom":"name","streak":5}}
  {{"action":"reset_stats","kingdom":"name"}}
  {{"action":"rename_kingdom","old_name":"old","new_name":"new"}}

Event management (extra):
  {{"action":"replace_registrant","event":"event name","old":"old name","new":"new name"}}
  {{"action":"edit_event","name":"event name","field":"date","value":"new value"}}

IMPORTANT CONTEXT RULES:
- "me", "myself", "I" → the person talking (use member: "me")
- "add X too" or "add X as well" → same action as before, same squad/event
- A single word like "Royal Talons" after being asked which squad → add_to_squad for the invoker
- "yes", "confirm", "do it" after describing an action → execute that action
- "too", "also", "as well" → repeat the last action type with new name
- Partial kingdom names are fine — the bot will fuzzy match them
- If unclear between question and action, lean toward action for direct short replies

Respond ONLY with valid JSON or null. No explanation, no code blocks, no markdown."""

        try:
            raw = await self._ai_call(extraction_prompt)
            raw = raw.strip().strip("```json").strip("```").strip()
            if raw.lower() == "null" or not raw or raw == "{}":
                return None
            return json.loads(raw)
        except json.JSONDecodeError as je:
            print(f"⚠️ Action JSON parse failed: {je} | raw: {raw[:100] if 'raw' in dir() else '?'}")
            return None
        except Exception as e:
            print(f"⚠️ Action extraction failed: {e}")
            return None

    async def _execute_extracted(self, action: dict, guild, invoker) -> str:
        """Execute a structured action dict."""
        sd  = self.squad_data
        sq  = sd.get("squads", {})
        act = action.get("action", "")

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
                import sys
                main = sys.modules.get("__main__")
                if main and hasattr(main, "save_data"):
                    main.save_data(sd); saved = True
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

        async def post_to(ch_name, embed):
            ch = discord.utils.get(guild.text_channels, name=ch_name)
            if ch:
                try: await ch.send(embed=embed)
                except: pass

        # ── add_to_squad ──────────────────────────────────────────────
        if act == "add_to_squad":
            member_ref = action.get("member", "me")
            sq_name    = action.get("squad", "")
            slot       = "subs" if action.get("slot","main").lower() == "sub" else "main_roster"
            mb = find_member(member_ref)
            sm = fuzzy(sq_name, sq)
            if not mb:
                return f"❌ Member '{member_ref}' not found on the server."
            if not sm:
                avail = ", ".join(list(sq.keys())[:8])
                return f"❌ Kingdom '{sq_name}' not found. Available: {avail}"
            roster = sq[sm].setdefault(slot, [])
            if mb.id in roster:
                return f"ℹ️ **{mb.display_name}** is already in **{sm}** ({slot})."
            roster.append(mb.id)
            ok = save()
            if not ok: return "⚠️ I couldn't save that. Try again or use /mod."
            count = len(sq[sm].get(slot, []))
            return f"✅ **{mb.display_name}** added to **{sm}** ({slot}). Roster: {count} player(s)."

        # ── record_match ──────────────────────────────────────────────
        elif act == "record_match":
            wn = fuzzy(action.get("winner",""), sq)
            ln = fuzzy(action.get("loser",""), sq)
            score = action.get("score", "?")
            if not wn or not ln:
                return f"❌ Kingdom not found. Winner:'{action.get('winner')}' Loser:'{action.get('loser')}'"
            sq[wn]["wins"]   = sq[wn].get("wins",0)+1
            sq[wn]["points"] = sq[wn].get("points",0)+3
            sq[wn]["streak"] = sq[wn].get("streak",0)+1
            sq[ln]["losses"] = sq[ln].get("losses",0)+1
            sq[ln]["streak"] = 0
            sd.setdefault("matches",[]).append({
                "id": len(sd.get("matches",[]))+1, "team1":wn, "team2":ln,
                "score":score, "winner":wn,
                "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                "recorded_by": str(invoker.id), "source":"oracle"
            })
            ok = save()
            if not ok: return "⚠️ Couldn't save the match. Try again or use /mod → Record Battle."
            embed = discord.Embed(title="⚔️ BATTLE RECORDED",
                description=f"**{wn}** defeated **{ln}** — **{score}**\n+3 Glory Points to {wn}",
                color=0xffd700, timestamp=datetime.utcnow())
            await post_to("war-results", embed)
            return f"✅ **{wn}** beat **{ln}** {score} — +3 glory pts, posted to war-results."

        # ── record_draw ───────────────────────────────────────────────
        elif act == "record_draw":
            t1 = fuzzy(action.get("team1",""), sq)
            t2 = fuzzy(action.get("team2",""), sq)
            score = action.get("score","1-1")
            if not t1 or not t2:
                return f"❌ Kingdom not found: '{action.get('team1')}' or '{action.get('team2')}'"
            for k in [t1,t2]:
                sq[k]["draws"]  = sq[k].get("draws",0)+1
                sq[k]["points"] = sq[k].get("points",0)+1
            sd.setdefault("matches",[]).append({
                "id": len(sd.get("matches",[]))+1, "team1":t1, "team2":t2,
                "score":score, "winner":"draw",
                "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                "recorded_by": str(invoker.id), "source":"oracle"
            })
            ok = save()
            if not ok: return "⚠️ Couldn't save. Try again!"
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
            import uuid
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
            embed.set_footer(text="⚜️ Majestic Dominion")
            await ann_ch.send(content=f"📢 {mention}" if mention else None, embed=embed)
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
            return f"✅ Scheduled: **{t1}** vs **{t2}** — **{dt}**"

        # ── set_points ────────────────────────────────────────────────
        elif act == "set_points":
            km  = fuzzy(action.get("kingdom",""), sq)
            pts = int(action.get("points",0))
            if not km: return f"❌ Kingdom '{action.get('kingdom')}' not found."
            sq[km]["points"] = pts; ok = save()
            return f"✅ **{km}** points set to **{pts}**." if ok else "⚠️ Couldn't save. Try again!"

        # ── remove_from_squad ─────────────────────────────────────────
        elif act == "remove_from_squad":
            mb = find_member(action.get("member",""))
            sm = fuzzy(action.get("squad",""), sq)
            if not mb: return f"❌ Member '{action.get('member')}' not found."
            if not sm: return f"❌ Kingdom '{action.get('squad')}' not found."
            for slot in ["main_roster","subs"]:
                if mb.id in sq[sm].get(slot,[]):
                    sq[sm][slot].remove(mb.id)
            ok = save()
            return f"✅ **{mb.display_name}** removed from **{sm}**." if ok else "⚠️ Couldn't save. Try again!"

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
                return f"❌ Kingdom '{sq_name}' not found. Available: {avail}"
            info    = sq[sm]
            tag     = self.squads.get(sm,"")
            pts     = info.get("points",0)
            w,d,l   = info.get("wins",0), info.get("draws",0), info.get("losses",0)
            streak  = info.get("streak",0)
            r_ids   = info.get("main_roster",[])
            s_ids   = info.get("subs",[])
            # Build full member index for reliable resolution
            midx = self._build_member_names_index()
            def rname(uid):
                s = str(uid)
                if s in midx: return midx[s]
                prof = sd.get("profiles",{}).get(s,{})
                if prof.get("ingame_name"): return prof["ingame_name"]
                return f"[{s}]"
            r_names = [rname(uid) for uid in r_ids]
            s_names = [rname(uid) for uid in s_ids]
            return (
                f"**{tag} {sm}**\n"
                f"Points: {pts} | {w}W/{d}D/{l}L | Streak: {streak}\n"
                f"Main Roster ({len(r_names)}): {', '.join(r_names) or 'empty'}\n"
                f"Subs ({len(s_names)}): {', '.join(s_names) or 'none'}\n"
                f"Achievements: {', '.join(info.get('achievements',[])) or 'none'}"
            )

        elif act == "list_squads":
            top = sorted(sq.items(), key=lambda x: -x[1].get("points",0))
            lines = []
            for i,(n,v) in enumerate(top, 1):
                tag = self.squads.get(n,"")
                lines.append(f"#{i} {tag} {n} — {v.get('points',0)}pts {v.get('wins',0)}W/{v.get('losses',0)}L")
            return f"**All Kingdoms ({len(top)}):**\n" + "\n".join(lines)

        elif act == "get_match_history":
            sq_filter = action.get("kingdom","").lower()
            matches = sd.get("matches",[])
            if sq_filter:
                matches = [m for m in matches
                           if sq_filter in m.get("team1","").lower()
                           or sq_filter in m.get("team2","").lower()]
            limit = int(action.get("limit", 10))
            recent = matches[-limit:][::-1]
            if not recent:
                return f"No matches found{' for ' + action.get('kingdom','') if sq_filter else ''}."
            lines = [
                f"• {m.get('team1','?')} {m.get('score','?')} {m.get('team2','?')} → "
                f"{'draw' if m.get('winner') == 'draw' else m.get('winner','?') + ' won'} [{m.get('date','?')[:10]}]"
                for m in recent
            ]
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
            if not matched: return f"❌ Kingdom '{old_n}' not found."
            sq[new_n] = sq.pop(matched)
            # Update bounties and challenges references
            if matched in sd.get("bounties",{}):
                sd["bounties"][new_n] = sd["bounties"].pop(matched)
            for ch in sd.get("challenges",[]):
                if ch.get("challenger") == matched: ch["challenger"] = new_n
                if ch.get("challenged") == matched: ch["challenged"] = new_n
            ok = save()
            return f"✅ **{matched}** renamed to **{new_n}**." if ok else "⚠️ Couldn't save. Try again!"

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

        # Chica gets full action access regardless of channel
        is_vip_action = vip_info is not None
        if is_mod or is_vip_action:
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
