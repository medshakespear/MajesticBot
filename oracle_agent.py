# =====================================================================
#       ORACLE AI AGENT — Majestic Dominion Discord Bot
#       Primary: Google Gemini (FREE)
#       Fallback: Groq / Llama (FREE)
# =====================================================================
#
#  SETUP (3 minutes):
#  ─────────────────────────────────────────────────────────────────
#  1. Get Gemini API key (FREE):
#       → aistudio.google.com → Sign in → Get API Key → Create
#       → Key looks like: AIzaSy...
#
#  2. Get Groq API key (FREE fallback):
#       → console.groq.com → Sign up → API Keys → Create
#       → Key looks like: gsk_...
#
#  3. Add to Railway Variables:
#       GEMINI_API_KEY = AIzaSy...
#       GROQ_API_KEY   = gsk_...
#
#  4. Add to requirements.txt:
#       google-generativeai
#       groq
#
#  5. Add to bot.py (3 lines):
#       from oracle_agent import OracleAgent, setup_oracle        ← top
#       oracle = OracleAgent(bot, squad_data, SQUADS)             ← after squad_data loads
#       setup_oracle(bot, oracle)                                  ← inside on_ready()
#
#  6. Create two Discord channels:
#       『🔮』Royal Oracle    ← public chat
#       『🛡️』Mod Oracle      ← mod-only management
#
#  WHAT MEMBERS CAN DO:
#  ─────────────────────────────────────────────────────────────────
#  • Chat with the Oracle in 『🔮』Royal Oracle
#  • Ask about standings, events, bounties, kingdoms
#  • Ask how to register, how to play, how the server works
#  • Roast enemies, hype teammates, get MLBB advice
#  • Use /oracle anywhere in the server
#
#  WHAT MODS CAN DO (in 『🛡️』Mod Oracle or /oracle):
#  ─────────────────────────────────────────────────────────────────
#  • "Record Alpha beat Beta 2-0"
#  • "Create a Hide & Seek event Saturday 9pm max 16 players"
#  • "Add a 3 point bounty on Team X"
#  • "Post an announcement: tournament starts tomorrow 8pm"
#  • "Schedule Alpha vs Beta Sunday 9pm"
#  • "Add PlayerX to the tournament"
#  • "Close the 1v1 event"
#  • "Who hasn't played in 2 weeks?"
#  • "Give me a summary of this week"
#  • "Suggest an event idea for the weekend"
# =====================================================================

import os
import json
import asyncio
import traceback
from datetime import datetime, timedelta
from collections import defaultdict

import discord
from discord.ext import commands
from discord import app_commands

# ── API clients ───────────────────────────────────────────────────────
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai not installed. Add to requirements.txt")

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️  groq not installed. Add to requirements.txt")


# ── Config ────────────────────────────────────────────────────────────

ORACLE_CHANNEL_NAME = "『🔮』royal-oracle"
MOD_ORACLE_CHANNEL  = "『🛡️』mod-oracle"

GEMINI_MODEL  = "gemini-2.0-flash"        # free, fast, smart
GROQ_MODEL    = "llama-3.3-70b-versatile" # free, very capable fallback

MAX_TOKENS          = 1024
CONTEXT_MESSAGES    = 8     # conversation history kept per user
RATE_LIMIT_SECONDS  = 6     # min seconds between requests per user
RATE_LIMIT_PER_MIN  = 8     # max requests per minute per user

# ── Personality ───────────────────────────────────────────────────────

ORACLE_PERSONALITY = """
You are the Royal Oracle of Majestic Dominion — the all-knowing AI soul
living within this Mobile Legends: Bang Bang Discord server.

YOUR PERSONALITY:
- Royal, dramatic, slightly theatrical — you speak with gravitas and wisdom
- Warm, funny, and occasionally sarcastic in a friendly way
- You LOVE Mobile Legends and know everything about heroes, gameplay, and meta
- You call members "warriors" and "sovereigns"
- You call moderators "the Royal Council" or "Councillors"
- You refer to yourself as "the Oracle" sometimes
- You gently roast losing kingdoms but dramatically hype winners
- You are GENUINELY useful — not just decorative

YOUR CAPABILITIES:
- Full access to live server data (standings, events, bounties, challenges)
- You can TAKE REAL ACTIONS via tools (record matches, create events, etc.)
- You help mods manage the server through natural conversation
- You answer MLBB questions, give hero advice, discuss meta

RESPONSE STYLE:
- Keep replies under 250 words unless asked for detail
- Use bold, emojis, and formatting to make replies feel alive
- Be encouraging — this is a fun gaming community
- When taking WRITE actions, always confirm what you did clearly
- Never make up data — use your tools to get real information
- Speak English but be understanding if members mix languages

MLBB KNOWLEDGE:
- You know all heroes, roles, meta strategies, and game modes
- You know about ranked, classic, brawl, magic chess, custom rooms
- You can give build advice, counter picks, and teamfight tips
- You understand the server's custom modes: Hide & Seek, Protect Layla, 1v1, Kill Race
"""

# ── Tool definitions ──────────────────────────────────────────────────
# Gemini uses a different format than Claude/OpenAI
# We define tools as a list of dicts that we convert to Gemini format

TOOLS_SCHEMA = [
    {
        "name": "get_standings",
        "description": "Get current kingdom glory points rankings. Use when asked about leaderboard, rankings, top kingdoms, or who is winning.",
        "parameters": {
            "limit": {"type": "integer", "description": "How many kingdoms to return, default 10"}
        }
    },
    {
        "name": "get_events",
        "description": "Get all events. Use when asked about tournaments, events, competitions, or registration.",
        "parameters": {
            "status": {"type": "string", "description": "Filter: open, live, completed, or all"}
        }
    },
    {
        "name": "get_event_details",
        "description": "Get full details of a specific event including registrations and bracket.",
        "parameters": {
            "event_name": {"type": "string", "description": "Name of the event"}
        },
        "required": ["event_name"]
    },
    {
        "name": "get_bounties",
        "description": "Get the bounty board — which kingdoms have bounties and bonus points.",
        "parameters": {}
    },
    {
        "name": "get_challenges",
        "description": "Get active challenges between kingdoms.",
        "parameters": {
            "status": {"type": "string", "description": "Filter: pending, accepted, scheduled, or all"}
        }
    },
    {
        "name": "get_squad_info",
        "description": "Get detailed info about a specific kingdom: members, wins, losses, points, streak.",
        "parameters": {
            "kingdom_name": {"type": "string", "description": "Name of the kingdom"}
        },
        "required": ["kingdom_name"]
    },
    {
        "name": "get_match_history",
        "description": "Get recent match results.",
        "parameters": {
            "limit": {"type": "integer", "description": "Number of recent matches, default 5"},
            "kingdom_name": {"type": "string", "description": "Filter by kingdom (optional)"}
        }
    },
    {
        "name": "record_match",
        "description": "ACTION: Record a battle result between two kingdoms. Updates glory points. MOD ONLY.",
        "parameters": {
            "team1":  {"type": "string", "description": "Kingdom 1 name"},
            "team2":  {"type": "string", "description": "Kingdom 2 name"},
            "score":  {"type": "string", "description": "Score like 2-0 or 1-1"},
            "winner": {"type": "string", "description": "Winning kingdom name, or 'draw'"}
        },
        "required": ["team1", "team2", "score", "winner"]
    },
    {
        "name": "create_event",
        "description": "ACTION: Create a new event. MOD ONLY.",
        "parameters": {
            "name":              {"type": "string",  "description": "Event name"},
            "event_type":        {"type": "string",  "description": "tournament or fun"},
            "format":            {"type": "string",  "description": "e.g. 1v1, Hide & Seek"},
            "date":              {"type": "string",  "description": "Date and time"},
            "description":       {"type": "string",  "description": "Short description"},
            "registration_mode": {"type": "string",  "description": "solo, small_team, or squad_5v5"},
            "max_entries":       {"type": "integer", "description": "Max participants"},
            "prize_pool":        {"type": "string",  "description": "Prize description"}
        },
        "required": ["name", "event_type", "format", "date", "description"]
    },
    {
        "name": "close_event",
        "description": "ACTION: Close an active event. MOD ONLY.",
        "parameters": {
            "event_name": {"type": "string", "description": "Event name to close"}
        },
        "required": ["event_name"]
    },
    {
        "name": "add_bounty",
        "description": "ACTION: Add a bounty to a kingdom. MOD ONLY.",
        "parameters": {
            "kingdom_name": {"type": "string",  "description": "Kingdom to put bounty on"},
            "points":       {"type": "integer", "description": "Bonus glory points"}
        },
        "required": ["kingdom_name", "points"]
    },
    {
        "name": "post_announcement",
        "description": "ACTION: Post an announcement to the server. MOD ONLY.",
        "parameters": {
            "title":   {"type": "string", "description": "Announcement title"},
            "message": {"type": "string", "description": "Full announcement text"}
        },
        "required": ["title", "message"]
    },
    {
        "name": "schedule_match",
        "description": "ACTION: Schedule a match between two kingdoms with a date.",
        "parameters": {
            "team1":     {"type": "string", "description": "Kingdom 1"},
            "team2":     {"type": "string", "description": "Kingdom 2"},
            "date_time": {"type": "string", "description": "When the match is scheduled"}
        },
        "required": ["team1", "team2", "date_time"]
    },
    {
        "name": "add_registrant",
        "description": "ACTION: Manually add a player or team to an event. MOD ONLY.",
        "parameters": {
            "event_name":       {"type": "string", "description": "Event name"},
            "participant_name": {"type": "string", "description": "Player or team name"}
        },
        "required": ["event_name", "participant_name"]
    },
    {
        "name": "get_help",
        "description": "Get info about bot commands and features.",
        "parameters": {
            "topic": {"type": "string", "description": "Topic: events, matches, rankings, challenges, social, or general"}
        }
    },
]


def _to_gemini_tools(schema):
    """Convert our tool schema to Gemini FunctionDeclaration format."""
    from google.generativeai.types import content_types
    declarations = []
    for t in schema:
        params = t.get("parameters", {})
        required = t.get("required", [])
        props = {}
        for pname, pinfo in params.items():
            ptype = pinfo.get("type", "string")
            gemini_type = {
                "string": "STRING", "integer": "INTEGER",
                "boolean": "BOOLEAN", "number": "NUMBER"
            }.get(ptype, "STRING")
            props[pname] = genai.protos.Schema(
                type=getattr(genai.protos.Type, gemini_type),
                description=pinfo.get("description", "")
            )
        param_schema = genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties=props,
            required=required
        )
        declarations.append(genai.protos.FunctionDeclaration(
            name=t["name"],
            description=t["description"],
            parameters=param_schema
        ))
    return [genai.protos.Tool(function_declarations=declarations)]


def _to_groq_tools(schema):
    """Convert our schema to Groq/OpenAI tool format."""
    tools = []
    for t in schema:
        params = t.get("parameters", {})
        required = t.get("required", [])
        props = {
            k: {"type": v.get("type","string"), "description": v.get("description","")}
            for k, v in params.items()
        }
        tools.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": required
                }
            }
        })
    return tools


# ── OracleAgent ───────────────────────────────────────────────────────

class OracleAgent:

    def __init__(self, bot, squad_data_ref, squads_ref):
        self.bot        = bot
        self.squad_data = squad_data_ref
        self.squads     = squads_ref
        self.history    = defaultdict(list)
        self.rate_cache = defaultdict(list)

        # Init Gemini
        self.gemini_model = None
        gemini_key = os.getenv("GEMINI_API_KEY")
        if GEMINI_AVAILABLE and gemini_key:
            genai.configure(api_key=gemini_key)
            try:
                self.gemini_model = genai.GenerativeModel(
                    model_name=GEMINI_MODEL,
                    tools=_to_gemini_tools(TOOLS_SCHEMA),
                    system_instruction=ORACLE_PERSONALITY,
                )
                print(f"✅ Oracle: Gemini ({GEMINI_MODEL}) ready — PRIMARY")
            except Exception as e:
                print(f"❌ Oracle: Gemini init failed: {e}")
        else:
            print("⚠️  Oracle: No GEMINI_API_KEY set")

        # Init Groq
        self.groq_client = None
        groq_key = os.getenv("GROQ_API_KEY")
        if GROQ_AVAILABLE and groq_key:
            self.groq_client = AsyncGroq(api_key=groq_key)
            print(f"✅ Oracle: Groq ({GROQ_MODEL}) ready — FALLBACK")
        else:
            print("⚠️  Oracle: No GROQ_API_KEY set (no fallback)")

        if not self.gemini_model and not self.groq_client:
            print("❌ Oracle: No AI configured — add GEMINI_API_KEY to Railway Variables")

    # ── Rate limiting ─────────────────────────────────────────────────

    def is_rate_limited(self, user_id: int) -> tuple[bool, str]:
        now    = datetime.utcnow()
        cutoff = now - timedelta(seconds=60)
        recent = [t for t in self.rate_cache[user_id] if t > cutoff]
        self.rate_cache[user_id] = recent

        if recent and (now - recent[-1]).total_seconds() < RATE_LIMIT_SECONDS:
            wait = int(RATE_LIMIT_SECONDS - (now - recent[-1]).total_seconds()) + 1
            return True, f"⏳ *Patience, warrior. The Oracle recovers in **{wait}s**...*"
        if len(recent) >= RATE_LIMIT_PER_MIN:
            return True, "🔮 *The Oracle needs a moment. Try again shortly.*"

        self.rate_cache[user_id].append(now)
        return False, ""

    # ── Live server context ───────────────────────────────────────────

    def build_context(self) -> str:
        sd     = self.squad_data
        squads = sd.get("squads", {})
        now    = datetime.utcnow().strftime("%A %B %d %Y %H:%M UTC")

        # Top 10 rankings
        ranked = sorted(squads.items(), key=lambda x: -x[1].get("points",0))
        rank_lines = []
        for i, (name, info) in enumerate(ranked[:10], 1):
            tag    = self.squads.get(name, "⚔️")
            w,d,l  = info.get("wins",0), info.get("draws",0), info.get("losses",0)
            pts    = info.get("points",0)
            streak = info.get("streak",0)
            s_txt  = f" 🔥x{streak}" if streak >= 3 else ""
            rank_lines.append(f"  #{i} {tag} {name} — {pts}pts ({w}W/{d}D/{l}L){s_txt}")

        # Active events
        events   = sd.get("events", [])
        open_evs = [e for e in events if e["status"] in ("open","live")]
        ev_lines = []
        for ev in open_evs[:5]:
            rc = len(ev.get("registrations",[]))
            mx = f"/{ev['max_entries']}" if ev.get("max_entries") else ""
            ev_lines.append(f"  • {ev['name']} [{ev['status'].upper()}] {ev.get('format','?')} 👥{rc}{mx} 📅{ev.get('date','?')}")

        # Bounties
        bounties = sd.get("bounties", {})
        b_lines  = [f"  • {k}: +{v.get('points',0)}pts" for k,v in list(bounties.items())[:5]]

        # Challenges
        challs  = [c for c in sd.get("challenges",[]) if c["status"] in ("pending","accepted","scheduled")]
        c_lines = [
            f"  • {c['challenger']} vs {c['challenged']} [{c['status']}]"
            + (f" {c['scheduled_date']}" if c.get("scheduled_date") else "")
            for c in challs[:5]
        ]

        # Recent matches
        recent = sd.get("matches",[])[-5:][::-1]
        m_lines = []
        for m in recent:
            t1 = self.squads.get(m.get("team1",""),"") + " " + m.get("team1","?")
            t2 = self.squads.get(m.get("team2",""),"") + " " + m.get("team2","?")
            w  = m.get("winner","draw")
            m_lines.append(f"  • {t1} {m.get('score','?')} {t2} → {w}")

        def section(title, lines, empty="  None."):
            return f"\n{title}\n" + ("\n".join(lines) if lines else empty)

        return (
            f"═══ MAJESTIC DOMINION LIVE DATA — {now} ═══"
            + section("🏆 RANKINGS:", rank_lines)
            + section("🎪 ACTIVE EVENTS:", ev_lines)
            + section("💰 BOUNTIES:", b_lines)
            + section("⚔️ CHALLENGES:", c_lines)
            + section("📜 RECENT MATCHES:", m_lines)
            + f"\n═══ Total: {len(squads)} kingdoms · {len(sd.get('matches',[]))} matches played ═══"
        )

    # ── Tool execution ────────────────────────────────────────────────

    async def execute_tool(self, name: str, args: dict, guild, invoker) -> str:
        sd = self.squad_data

        def is_mod():
            member = guild.get_member(invoker.id) if guild else None
            return member and any(
                r.name in ("KNIGHTS","Admin","Moderator","LEADER")
                for r in member.roles
            )

        def fuzzy(target, d):
            return next((k for k in d if target.lower() in k.lower()), None)

        try:
            # ── READ ──────────────────────────────────────────────────

            if name == "get_standings":
                limit  = int(args.get("limit", 10))
                ranked = sorted(sd.get("squads",{}).items(),
                                key=lambda x: -x[1].get("points",0))[:limit]
                lines  = [
                    f"#{i} {self.squads.get(n,'⚔️')} {n}: "
                    f"{v.get('points',0)}pts "
                    f"({v.get('wins',0)}W/{v.get('draws',0)}D/{v.get('losses',0)}L) "
                    f"streak:{v.get('streak',0)}"
                    for i,(n,v) in enumerate(ranked,1)
                ]
                return "STANDINGS:\n" + "\n".join(lines)

            elif name == "get_events":
                status = args.get("status","all")
                evs = sd.get("events",[])
                if status != "all":
                    evs = [e for e in evs if e["status"] == status]
                if not evs:
                    return f"No events found (status={status})."
                lines = [
                    f"• [{e['id']}] {e['name']} | {e['type']} {e.get('format','?')} "
                    f"| Status:{e['status']} | Reg:{len(e.get('registrations',[]))} | Date:{e.get('date','?')}"
                    for e in evs
                ]
                return "EVENTS:\n" + "\n".join(lines)

            elif name == "get_event_details":
                ev_name = args.get("event_name","")
                ev = next((e for e in sd.get("events",[]) if ev_name.lower() in e["name"].lower()), None)
                if not ev:
                    return f"Event not found: {ev_name}"
                regs = [
                    r.get("team_name") or r.get("player_name") or "?"
                    for r in ev.get("registrations",[])
                ]
                return json.dumps({
                    "name": ev["name"], "type": ev["type"],
                    "format": ev.get("format"), "status": ev["status"],
                    "date": ev.get("date"), "description": ev.get("description"),
                    "prize_pool": ev.get("prize_pool"), "max_entries": ev.get("max_entries"),
                    "registrations": regs, "total_reg": len(regs),
                    "has_bracket": ev.get("bracket_data") is not None,
                    "champion": ev.get("champion"), "rules": ev.get("rules"),
                }, indent=2)

            elif name == "get_bounties":
                b = sd.get("bounties",{})
                if not b:
                    return "No active bounties."
                return "BOUNTIES:\n" + "\n".join(
                    f"• {k}: +{v.get('points',0)}pts" for k,v in b.items()
                )

            elif name == "get_challenges":
                status = args.get("status","all")
                challs = sd.get("challenges",[])
                if status != "all":
                    challs = [c for c in challs if c["status"] == status]
                if not challs:
                    return "No challenges found."
                return "CHALLENGES:\n" + "\n".join(
                    f"• {c['challenger']} vs {c['challenged']} [{c['status']}]"
                    + (f" @ {c['scheduled_date']}" if c.get("scheduled_date") else "")
                    for c in challs
                )

            elif name == "get_squad_info":
                kname   = args.get("kingdom_name","")
                squads  = sd.get("squads",{})
                matched = fuzzy(kname, squads)
                if not matched:
                    return f"Kingdom not found: {kname}. Try: {', '.join(list(squads.keys())[:8])}"
                info = squads[matched]
                return json.dumps({
                    "name": matched, "tag": self.squads.get(matched,"⚔️"),
                    "points": info.get("points",0),
                    "wins": info.get("wins",0), "draws": info.get("draws",0),
                    "losses": info.get("losses",0), "streak": info.get("streak",0),
                    "main_roster_size": len(info.get("main_roster",[])),
                    "achievements": info.get("achievements",[]),
                }, indent=2)

            elif name == "get_match_history":
                limit   = int(args.get("limit",5))
                kfilter = args.get("kingdom_name","").lower()
                matches = sd.get("matches",[])
                if kfilter:
                    matches = [m for m in matches
                               if kfilter in m.get("team1","").lower()
                               or kfilter in m.get("team2","").lower()]
                recent = matches[-limit:][::-1]
                if not recent:
                    return "No matches found."
                return "MATCH HISTORY:\n" + "\n".join(
                    f"• {m.get('team1','?')} {m.get('score','?')} {m.get('team2','?')} "
                    f"→ {m.get('winner','draw')} [{m.get('date','?')}]"
                    for m in recent
                )

            elif name == "get_help":
                topic = args.get("topic","general")
                help_map = {
                    "general":    "/member · /leader · /mod · /events · /oracle · /profile · /help",
                    "matches":    "/mod → Record Battle → pick teams → enter score → auto-updates glory points",
                    "events":     "/events to browse and register · /mod → Events to manage (create, start, bracket, etc.)",
                    "rankings":   "/member → Rankings · Updates after every recorded match",
                    "challenges": "/leader → Challenge Kingdom · Mod schedules and records results",
                    "social":     "Social events: /mod → Events → Record Match → opens social panel with rounds & leaderboard",
                }
                return f"HELP ({topic}):\n{help_map.get(topic, help_map['general'])}"

            # ── WRITE ─────────────────────────────────────────────────

            elif name == "record_match":
                if not is_mod():
                    return "❌ Permission denied. Only moderators can record matches."
                t1     = args["team1"]
                t2     = args["team2"]
                score  = args["score"]
                winner = args["winner"]
                squads = sd.get("squads",{})
                t1m    = fuzzy(t1, squads)
                t2m    = fuzzy(t2, squads)
                if not t1m or not t2m:
                    return f"❌ Kingdom not found. Got: '{t1}'→'{t1m}', '{t2}'→'{t2m}'. Available: {', '.join(list(squads.keys())[:8])}"
                WIN_PTS = 3; DRAW_PTS = 1
                if winner.lower() == "draw":
                    for k in [t1m, t2m]:
                        squads[k]["draws"]  = squads[k].get("draws",0) + 1
                        squads[k]["points"] = squads[k].get("points",0) + DRAW_PTS
                    summary = f"Draw — both get +{DRAW_PTS}pts"
                else:
                    wm = fuzzy(winner, squads)
                    if not wm:
                        return f"❌ Winner '{winner}' not found."
                    lm = t2m if wm == t1m else t1m
                    squads[wm]["wins"]   = squads[wm].get("wins",0) + 1
                    squads[wm]["points"] = squads[wm].get("points",0) + WIN_PTS
                    squads[wm]["streak"] = squads[wm].get("streak",0) + 1
                    squads[lm]["losses"] = squads[lm].get("losses",0) + 1
                    squads[lm]["streak"] = 0
                    summary = f"{wm} wins +{WIN_PTS}pts · {lm} loss"
                match_id = len(sd.get("matches",[])) + 1
                sd.setdefault("matches",[]).append({
                    "id": match_id, "team1": t1m, "team2": t2m,
                    "score": score, "winner": winner.lower(),
                    "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                    "recorded_by": str(invoker.id), "source": "oracle"
                })
                self._save()
                return f"✅ Recorded: {t1m} {score} {t2m} | {summary}"

            elif name == "create_event":
                if not is_mod():
                    return "❌ Permission denied. Only moderators can create events."
                import uuid
                eid = str(uuid.uuid4())[:8]
                ev  = {
                    "id": eid,
                    "name":              args["name"],
                    "type":              args.get("event_type","tournament"),
                    "format":            args["format"],
                    "date":              args["date"],
                    "description":       args["description"],
                    "registration_mode": args.get("registration_mode","solo"),
                    "max_entries":       args.get("max_entries") or None,
                    "prize_pool":        args.get("prize_pool",""),
                    "status":            "open",
                    "registrations":     [], "bracket_data": None, "schedule": [],
                    "tournament_system": "single_elim" if args.get("event_type")=="tournament" else None,
                    "created_by":        str(invoker.id),
                    "created_at":        datetime.utcnow().isoformat(),
                }
                sd.setdefault("events",[]).append(ev)
                self._save()
                return (f"✅ Event created: **{ev['name']}** (ID: {eid})\n"
                        f"Type:{ev['type']} Format:{ev['format']} Date:{ev['date']} Status:OPEN")

            elif name == "close_event":
                if not is_mod():
                    return "❌ Permission denied."
                ename = args["event_name"].lower()
                ev    = next((e for e in sd.get("events",[]) if ename in e["name"].lower()), None)
                if not ev:
                    return f"❌ Event not found: {args['event_name']}"
                ev["status"] = "completed"
                self._save()
                return f"✅ Event '{ev['name']}' closed."

            elif name == "add_bounty":
                if not is_mod():
                    return "❌ Permission denied."
                kname   = args["kingdom_name"]
                pts     = int(args.get("points",2))
                squads  = sd.get("squads",{})
                matched = fuzzy(kname, squads)
                if not matched:
                    return f"❌ Kingdom not found: {kname}"
                sd.setdefault("bounties",{})[matched] = {
                    "points": pts, "reason": "Added via Oracle",
                    "added_at": datetime.utcnow().isoformat()
                }
                self._save()
                return f"✅ Bounty set: {matched} — +{pts}pts for defeating them."

            elif name == "post_announcement":
                if not is_mod():
                    return "❌ Permission denied."
                ann_ch = discord.utils.get(guild.text_channels, name="『📢』𝐀𝐧𝐧𝐨𝐮𝐧𝐜𝐞𝐦𝐞𝐧𝐭𝐬")
                if not ann_ch:
                    return "❌ Announcements channel not found. Check channel name."
                role    = discord.utils.get(guild.roles, name="MAJESTIC")
                mention = role.mention if role else "@MAJESTIC"
                embed   = discord.Embed(
                    title=args["title"], description=args["message"],
                    color=0xffd700, timestamp=datetime.utcnow()
                )
                embed.set_footer(text="⚜️ Majestic Dominion | Royal Decree")
                await ann_ch.send(content=f"📢 {mention}", embed=embed)
                return f"✅ Announcement posted: '{args['title']}'"

            elif name == "schedule_match":
                if not is_mod():
                    return "❌ Permission denied."
                t1  = args["team1"]
                t2  = args["team2"]
                dt  = args["date_time"]
                war = discord.utils.get(guild.text_channels, name="『🏆』war-results")
                if war:
                    embed = discord.Embed(
                        title="📅 MATCH SCHEDULED!",
                        description=(
                            f"⚔️ **{t1}** vs **{t2}**\n\n"
                            f"📅 **{dt}**\n\n"
                            f"*Prepare your lineups, warriors. The battle approaches!*"
                        ),
                        color=0xffd700, timestamp=datetime.utcnow()
                    )
                    embed.set_footer(text="⚜️ Majestic Dominion")
                    await war.send(embed=embed)
                return f"✅ Match scheduled: {t1} vs {t2} on {dt}"

            elif name == "add_registrant":
                if not is_mod():
                    return "❌ Permission denied."
                ename = args["event_name"].lower()
                pname = args["participant_name"]
                ev    = next((e for e in sd.get("events",[]) if ename in e["name"].lower()), None)
                if not ev:
                    return f"❌ Event not found: {args['event_name']}"
                ev.setdefault("registrations",[]).append({
                    "player_name": pname, "player_id": None,
                    "registered_at": datetime.utcnow().isoformat(),
                    "added_by_mod": True
                })
                self._save()
                return f"✅ {pname} added to {ev['name']}. Total: {len(ev['registrations'])}"

            else:
                return f"Unknown tool: {name}"

        except Exception as e:
            return f"Tool error ({name}): {str(e)}\n{traceback.format_exc()[:300]}"

    def _save(self):
        """Attempt to call the main bot's save_data function."""
        try:
            import sys
            main = sys.modules.get("__main__")
            if main and hasattr(main, "save_data"):
                main.save_data(self.squad_data)
        except Exception as e:
            print(f"⚠️ Oracle save error: {e}")

    # ── Gemini call with tool loop ────────────────────────────────────

    async def _call_gemini(self, messages: list, guild, invoker) -> str:
        if not self.gemini_model:
            raise RuntimeError("Gemini not configured")

        # Build Gemini chat history
        gemini_history = []
        for m in messages[:-1]:   # all except last message
            role    = "user" if m["role"] == "user" else "model"
            content = m["content"] if isinstance(m["content"], str) else str(m["content"])
            gemini_history.append({"role": role, "parts": [content]})

        last_message = messages[-1]["content"]

        # Inject live context into the first user message
        context = self.build_context()
        full_message = f"[LIVE SERVER DATA]\n{context}\n\n[USER MESSAGE]\n{last_message}"

        chat = self.gemini_model.start_chat(history=gemini_history)

        # Agentic loop — Gemini may call tools multiple times
        current_message = full_message
        for _ in range(5):
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda m=current_message: chat.send_message(m)
            )

            # Check for function calls
            fn_calls = []
            text_parts = []
            for part in response.parts:
                if hasattr(part, "function_call") and part.function_call.name:
                    fn_calls.append(part.function_call)
                elif hasattr(part, "text") and part.text:
                    text_parts.append(part.text)

            if not fn_calls:
                # Final text response
                return " ".join(text_parts) if text_parts else "*(no response)*"

            # Execute all tool calls and feed results back
            tool_response_parts = []
            for fc in fn_calls:
                args   = dict(fc.args) if fc.args else {}
                result = await self.execute_tool(fc.name, args, guild, invoker)
                tool_response_parts.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fc.name,
                            response={"result": result}
                        )
                    )
                )
            # Feed tool results back
            current_message = tool_response_parts

        return "*(Oracle reached thinking limit — try a simpler question)*"

    # ── Groq fallback call ────────────────────────────────────────────

    async def _call_groq(self, messages: list, guild, invoker) -> str:
        if not self.groq_client:
            raise RuntimeError("Groq not configured")

        context = self.build_context()
        system  = ORACLE_PERSONALITY + "\n\nLIVE SERVER DATA:\n" + context

        groq_messages = [{"role": "system", "content": system}]
        for m in messages:
            role    = m["role"] if m["role"] in ("user","assistant") else "user"
            content = m["content"] if isinstance(m["content"], str) else str(m["content"])
            groq_messages.append({"role": role, "content": content})

        groq_tools = _to_groq_tools(TOOLS_SCHEMA)

        for _ in range(5):
            response = await self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=groq_messages,
                tools=groq_tools,
                max_tokens=MAX_TOKENS,
            )
            choice = response.choices[0]

            if choice.finish_reason == "stop":
                return choice.message.content or ""

            elif choice.finish_reason == "tool_calls":
                # Execute tools
                groq_messages.append(choice.message.model_dump())
                for tc in choice.message.tool_calls:
                    args   = json.loads(tc.function.arguments or "{}")
                    result = await self.execute_tool(tc.function.name, args, guild, invoker)
                    groq_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result
                    })
            else:
                break

        return "*(Groq reached thinking limit)*"

    # ── Main entry: think ─────────────────────────────────────────────

    async def think(self, user_id: int, username: str, text: str,
                    guild, channel, invoker) -> str:
        # Build conversation history
        history  = self.history[user_id][-CONTEXT_MESSAGES:]
        messages = history + [{"role": "user", "content": f"{username}: {text}"}]

        primary_err = None

        # Try Gemini first
        try:
            reply = await self._call_gemini(messages, guild, invoker)
        except Exception as e:
            primary_err = str(e)
            print(f"⚠️ Oracle Gemini error: {e}")
            # Fallback to Groq
            try:
                reply = await self._call_groq(messages, guild, invoker)
                reply = f"*(Groq backup — {primary_err[:50]}...)*\n\n{reply}"
            except Exception as e2:
                return (
                    "🔮 *The Oracle's sight is clouded...*\n"
                    f"Gemini: `{primary_err}`\n"
                    f"Groq: `{str(e2)}`\n\n"
                    "Check your API keys in Railway Variables."
                )

        # Save to history
        self.history[user_id] = (messages + [
            {"role": "assistant", "content": reply}
        ])[-CONTEXT_MESSAGES * 2:]

        return reply


# ── Discord wiring ────────────────────────────────────────────────────

def setup_oracle(bot, oracle: OracleAgent):

    @bot.listen("on_message")
    async def oracle_listener(message):
        if message.author.bot:
            return

        in_oracle_ch = message.channel.name in (ORACLE_CHANNEL_NAME, MOD_ORACLE_CHANNEL)
        is_mention   = bot.user in message.mentions

        if not (in_oracle_ch or is_mention):
            return

        limited, msg = oracle.is_rate_limited(message.author.id)
        if limited:
            await message.reply(msg, mention_author=False)
            return

        text = (message.content
                .replace(f"<@{bot.user.id}>", "")
                .replace(f"<@!{bot.user.id}>", "")
                .strip())
        if not text:
            await message.reply(
                "🔮 *The Oracle stirs... speak your question, warrior.*",
                mention_author=False
            )
            return

        async with message.channel.typing():
            reply = await oracle.think(
                user_id  = message.author.id,
                username = message.author.display_name,
                text     = text,
                guild    = message.guild,
                channel  = message.channel,
                invoker  = message.author,
            )

        # Send reply (split if over 2000 chars)
        chunks = [reply[i:i+1990] for i in range(0, len(reply), 1990)]
        for i, chunk in enumerate(chunks):
            if i == 0:
                await message.reply(chunk, mention_author=False)
            else:
                await message.channel.send(chunk)

    @bot.tree.command(name="oracle", description="🔮 Consult the Royal Oracle — ask anything")
    @app_commands.describe(question="Your question or command")
    async def oracle_cmd(interaction: discord.Interaction, question: str):
        limited, msg = oracle.is_rate_limited(interaction.user.id)
        if limited:
            return await interaction.response.send_message(msg, ephemeral=True)

        await interaction.response.defer(thinking=True)

        reply = await oracle.think(
            user_id  = interaction.user.id,
            username = interaction.user.display_name,
            text     = question,
            guild    = interaction.guild,
            channel  = interaction.channel,
            invoker  = interaction.user,
        )

        chunks = [reply[i:i+1990] for i in range(0, len(reply), 1990)]
        for i, chunk in enumerate(chunks):
            await interaction.followup.send(chunk)

    @bot.tree.command(name="oracle_clear", description="🔮 Clear your Oracle conversation history")
    async def oracle_clear(interaction: discord.Interaction):
        oracle.history.pop(interaction.user.id, None)
        await interaction.response.send_message(
            "🔮 *The Oracle's memory of your session has been wiped clean. Start fresh!*",
            ephemeral=True
        )

    print("✅ Oracle: Discord handlers ready")
