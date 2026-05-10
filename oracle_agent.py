# =====================================================================
#       ORACLE AI AGENT — Majestic Dominion Discord Bot
#       Primary: Google Gemini (FREE)
#       Fallback: Groq / Llama (FREE)
# =====================================================================
#
#  SETUP:
#  1. Get Gemini key FREE → aistudio.google.com → Get API Key
#  2. Get Groq key FREE   → console.groq.com → API Keys
#  3. Add to Railway Variables:
#       GEMINI_API_KEY = AIzaSy...
#       GROQ_API_KEY   = gsk_...
#  4. Add to requirements.txt:
#       google-generativeai
#       groq
#  5. Add to bot.py:
#       from oracle_agent import OracleAgent, setup_oracle   ← top
#       oracle = OracleAgent(bot, squad_data, SQUADS)        ← after squad_data loads
#       setup_oracle(bot, oracle)                             ← inside on_ready()
#  6. Create Discord channels:
#       『🔮』 Royal Oracle    ← public
#       『🛡️』 Mod Oracle      ← mod-only
# =====================================================================

import os, json, asyncio, traceback
from datetime import datetime, timedelta
from collections import defaultdict
import discord
from discord import app_commands

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai not in requirements.txt")

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️  groq not in requirements.txt")

ORACLE_CHANNEL_NAME = "『🔮』 Royal Oracle"
MOD_ORACLE_CHANNEL  = "『🛡️』 Mod Oracle"
GEMINI_MODEL        = "gemini-2.0-flash"  # fallback
GROQ_MODEL          = "llama-3.3-70b-versatile"  # primary
MAX_TOKENS          = 1024
CONTEXT_MESSAGES    = 8
RATE_LIMIT_SECONDS  = 6
RATE_LIMIT_PER_MIN  = 8

ORACLE_PERSONALITY = """
You are the Royal Oracle of Majestic Dominion, an all-knowing AI entity living
inside this Mobile Legends: Bang Bang Discord server.

PERSONALITY:
- Royal, dramatic, slightly theatrical but warm and funny
- You LOVE MLBB and know all heroes, meta, game modes inside-out
- Call members "warriors", mods "the Royal Council"
- Refer to yourself as "the Oracle" sometimes
- Gently roast losing kingdoms, dramatically hype winners
- GENUINELY helpful and accurate — use tools for real data

CAPABILITIES:
- Full live access to server data (standings, events, bounties, challenges)
- Can take REAL ACTIONS via tools (mods only for write actions)
- Answers MLBB questions: builds, heroes, counters, strategies
- Knows your custom modes: Hide & Seek, Protect Layla, 1v1, Kill Race

STYLE:
- Under 250 words unless asked for detail
- Use bold and emojis to feel alive
- Always confirm clearly after taking an action
- Never make up data — use tools
"""

TOOLS_SCHEMA = [
    {"name": "get_standings",    "description": "Get kingdom glory points rankings. Use when asked about leaderboard, top kingdoms, who is winning.", "parameters": {"limit": {"type": "integer", "description": "How many kingdoms, default 10"}}},
    {"name": "get_events",       "description": "Get all events. Use for tournaments, events, competitions, registration questions.", "parameters": {"status": {"type": "string", "description": "Filter: open, live, completed, or all"}}},
    {"name": "get_event_details","description": "Get full details of a specific event.", "parameters": {"event_name": {"type": "string", "description": "Event name"}}, "required": ["event_name"]},
    {"name": "get_bounties",     "description": "Get the bounty board.", "parameters": {}},
    {"name": "get_challenges",   "description": "Get active challenges between kingdoms.", "parameters": {"status": {"type": "string", "description": "pending, accepted, scheduled, or all"}}},
    {"name": "get_squad_info",   "description": "Get info about a specific kingdom.", "parameters": {"kingdom_name": {"type": "string", "description": "Kingdom name"}}, "required": ["kingdom_name"]},
    {"name": "get_match_history","description": "Get recent match results.", "parameters": {"limit": {"type": "integer", "description": "Number of matches, default 5"}, "kingdom_name": {"type": "string", "description": "Filter by kingdom (optional)"}}},
    {"name": "record_match",     "description": "ACTION: Record a battle result. MOD ONLY. Updates glory points.", "parameters": {"team1": {"type": "string", "description": "Kingdom 1"}, "team2": {"type": "string", "description": "Kingdom 2"}, "score": {"type": "string", "description": "Score e.g. 2-0"}, "winner": {"type": "string", "description": "Winner kingdom or draw"}}, "required": ["team1","team2","score","winner"]},
    {"name": "create_event",     "description": "ACTION: Create a new event. MOD ONLY.", "parameters": {"name": {"type": "string", "description": "Event name"}, "event_type": {"type": "string", "description": "tournament or fun"}, "format": {"type": "string", "description": "e.g. 1v1, Hide & Seek"}, "date": {"type": "string", "description": "Date and time"}, "description": {"type": "string", "description": "Description"}, "max_entries": {"type": "integer", "description": "Max participants"}, "prize_pool": {"type": "string", "description": "Prize (optional)"}}, "required": ["name","event_type","format","date","description"]},
    {"name": "close_event",      "description": "ACTION: Close an event. MOD ONLY.", "parameters": {"event_name": {"type": "string", "description": "Event to close"}}, "required": ["event_name"]},
    {"name": "add_bounty",       "description": "ACTION: Add a bounty on a kingdom. MOD ONLY.", "parameters": {"kingdom_name": {"type": "string", "description": "Kingdom"}, "points": {"type": "integer", "description": "Bonus points"}}, "required": ["kingdom_name","points"]},
    {"name": "post_announcement","description": "ACTION: Post announcement to server. MOD ONLY.", "parameters": {"title": {"type": "string", "description": "Title"}, "message": {"type": "string", "description": "Message"}}, "required": ["title","message"]},
    {"name": "schedule_match",   "description": "ACTION: Schedule a match and post to war-results.", "parameters": {"team1": {"type": "string", "description": "Kingdom 1"}, "team2": {"type": "string", "description": "Kingdom 2"}, "date_time": {"type": "string", "description": "When"}}, "required": ["team1","team2","date_time"]},
    {"name": "add_registrant",   "description": "ACTION: Add a participant to an event. MOD ONLY.", "parameters": {"event_name": {"type": "string", "description": "Event name"}, "participant_name": {"type": "string", "description": "Player or team name"}}, "required": ["event_name","participant_name"]},
    {"name": "get_help",         "description": "Get bot commands and feature info.", "parameters": {"topic": {"type": "string", "description": "events, matches, rankings, challenges, social, or general"}}},
]


def _to_gemini_tools(schema):
    """Convert tool schema to new google-genai format."""
    from google.genai import types as gtypes
    declarations = []
    for t in schema:
        params = t.get("parameters", {})
        required = t.get("required", [])
        props = {}
        for pname, pinfo in params.items():
            ptype = {"string": gtypes.Type.STRING, "integer": gtypes.Type.INTEGER,
                     "boolean": gtypes.Type.BOOLEAN, "number": gtypes.Type.NUMBER
                     }.get(pinfo.get("type","string"), gtypes.Type.STRING)
            props[pname] = gtypes.Schema(type=ptype, description=pinfo.get("description",""))
        param_schema = gtypes.Schema(
            type=gtypes.Type.OBJECT, properties=props, required=required
        )
        declarations.append(gtypes.FunctionDeclaration(
            name=t["name"], description=t["description"], parameters=param_schema
        ))
    return gtypes.Tool(function_declarations=declarations)


def _to_groq_tools(schema):
    """Convert to Groq tool format — keep it simple, no enums."""
    tools = []
    for t in schema:
        props = {}
        for k, v in t.get("parameters", {}).items():
            props[k] = {
                "type": v.get("type", "string"),
                "description": v.get("description", "")
            }
        tools.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": t.get("required", [])
                }
            }
        })
    return tools


class OracleAgent:
    def __init__(self, bot, squad_data_ref, squads_ref):
        self.bot        = bot
        self.squad_data = squad_data_ref
        self.squads     = squads_ref
        self.history    = defaultdict(list)
        self.rate_cache = defaultdict(list)
        self.gemini_client = None
        self.groq_client  = None

        gkey = os.getenv("GEMINI_API_KEY")
        if GEMINI_AVAILABLE and gkey:
            try:
                self.gemini_client = genai.Client(api_key=gkey)
                print(f"\u2705 Oracle: Gemini ({GEMINI_MODEL}) ready — FALLBACK")
            except Exception as e:
                print(f"\u274c Oracle Gemini init: {e}")
                self.gemini_client = None
        else:
            print("\u26a0\ufe0f Oracle: No GEMINI_API_KEY")
            self.gemini_client = None

        grkey = os.getenv("GROQ_API_KEY")
        if GROQ_AVAILABLE and grkey:
            self.groq_client = AsyncGroq(api_key=grkey)
            print(f"\u2705 Oracle: Groq ({GROQ_MODEL}) ready — PRIMARY")
        else:
            print("\u26a0\ufe0f Oracle: No GROQ_API_KEY (no fallback)")

    def is_rate_limited(self, uid):
        now = datetime.utcnow(); cutoff = now - timedelta(seconds=60)
        recent = [t for t in self.rate_cache[uid] if t > cutoff]
        self.rate_cache[uid] = recent
        if recent and (now-recent[-1]).total_seconds() < RATE_LIMIT_SECONDS:
            w = int(RATE_LIMIT_SECONDS-(now-recent[-1]).total_seconds())+1
            return True, f"\u23f3 *Patience, warrior. The Oracle recovers in **{w}s**...*"
        if len(recent) >= RATE_LIMIT_PER_MIN:
            return True, "\U0001f52e *The Oracle needs a moment. Try again shortly.*"
        self.rate_cache[uid].append(now); return False, ""

    def build_context(self):
        sd = self.squad_data; squads = sd.get("squads",{}); now = datetime.utcnow().strftime("%A %B %d %Y %H:%M UTC")
        ranked = sorted(squads.items(), key=lambda x: -x[1].get("points",0))
        r_lines = [f"  #{i} {self.squads.get(n,chr(9876))} {n}: {v.get('points',0)}pts ({v.get('wins',0)}W/{v.get('draws',0)}D/{v.get('losses',0)}L) streak:{v.get('streak',0)}" for i,(n,v) in enumerate(ranked[:10],1)]
        events = sd.get("events",[]); open_ev = [e for e in events if e["status"] in ("open","live")]
        ev_lines = [f"  • {e['name']} [{e['status'].upper()}] {e.get('format','?')} \U0001f465{len(e.get('registrations',[]))} \U0001f4c5{e.get('date','?')}" for e in open_ev[:5]]
        b = sd.get("bounties",{}); b_lines = [f"  • {k}: +{v.get('points',0)}pts" for k,v in list(b.items())[:5]]
        challs = [c for c in sd.get("challenges",[]) if c["status"] in ("pending","accepted","scheduled")]
        c_lines = [f"  • {c['challenger']} vs {c['challenged']} [{c['status']}]" + (f" @ {c['scheduled_date']}" if c.get("scheduled_date") else "") for c in challs[:5]]
        recent = sd.get("matches",[])[-5:][::-1]
        m_lines = [f"  • {self.squads.get(m.get('team1',''),'')} {m.get('team1','?')} {m.get('score','?')} {self.squads.get(m.get('team2',''),'')} {m.get('team2','?')} \u2192 {m.get('winner','draw')}" for m in recent]
        def sec(title, lines, empty="  None."):
            return f"\n{title}\n"+("\n".join(lines) if lines else empty)
        return f"\u2550\u2550\u2550 MAJESTIC DOMINION LIVE — {now} \u2550\u2550\u2550"+sec("\U0001f3c6 RANKINGS:",r_lines)+sec("\U0001f3aa ACTIVE EVENTS:",ev_lines)+sec("\U0001f4b0 BOUNTIES:",b_lines)+sec("\u2694\ufe0f CHALLENGES:",c_lines)+sec("\U0001f4dc RECENT MATCHES:",m_lines)+f"\n\u2550\u2550\u2550 {len(squads)} kingdoms · {len(sd.get('matches',[]))} total matches \u2550\u2550\u2550"

    async def execute_tool(self, name, args, guild, invoker):
        sd = self.squad_data
        def is_mod():
            m = guild.get_member(invoker.id) if guild else None
            return m and any(r.name in ("KNIGHTS","Admin","Moderator","LEADER") for r in m.roles)
        def fuzzy(t, d):
            return next((k for k in d if t.lower() in k.lower()), None)
        try:
            if name == "get_standings":
                limit = int(args.get("limit",10)); ranked = sorted(sd.get("squads",{}).items(), key=lambda x: -x[1].get("points",0))[:limit]
                return "STANDINGS:\n"+("\n".join([f"#{i} {self.squads.get(n,chr(9876))} {n}: {v.get('points',0)}pts ({v.get('wins',0)}W/{v.get('draws',0)}D/{v.get('losses',0)}L) streak:{v.get('streak',0)}" for i,(n,v) in enumerate(ranked,1)]))
            elif name == "get_events":
                status = args.get("status","all"); evs = sd.get("events",[])
                if status != "all": evs = [e for e in evs if e["status"]==status]
                if not evs: return f"No events (status={status})."
                return "EVENTS:\n"+("\n".join([f"• [{e['id']}] {e['name']} | {e['type']} {e.get('format','?')} | {e['status']} | reg:{len(e.get('registrations',[]))} | {e.get('date','?')}" for e in evs]))
            elif name == "get_event_details":
                ev = next((e for e in sd.get("events",[]) if args.get("event_name","").lower() in e["name"].lower()), None)
                if not ev: return f"Event not found: {args.get('event_name')}"
                regs = [r.get("team_name") or r.get("player_name") or "?" for r in ev.get("registrations",[])]
                return json.dumps({"name":ev["name"],"type":ev["type"],"format":ev.get("format"),"status":ev["status"],"date":ev.get("date"),"description":ev.get("description"),"prize_pool":ev.get("prize_pool"),"max_entries":ev.get("max_entries"),"registrations":regs,"total_reg":len(regs),"has_bracket":ev.get("bracket_data") is not None,"champion":ev.get("champion"),"rules":ev.get("rules")},indent=2)
            elif name == "get_bounties":
                b = sd.get("bounties",{}); return "No bounties." if not b else "BOUNTIES:\n"+("\n".join([f"• {k}: +{v.get('points',0)}pts" for k,v in b.items()]))
            elif name == "get_challenges":
                status = args.get("status","all"); challs = sd.get("challenges",[])
                if status != "all": challs = [c for c in challs if c["status"]==status]
                if not challs: return "No challenges."
                return "CHALLENGES:\n"+("\n".join([f"• {c['challenger']} vs {c['challenged']} [{c['status']}]"+(f" @ {c['scheduled_date']}" if c.get("scheduled_date") else "") for c in challs]))
            elif name == "get_squad_info":
                squads = sd.get("squads",{}); matched = fuzzy(args.get("kingdom_name",""), squads)
                if not matched: return f"Kingdom not found: {args.get('kingdom_name')}. Try: {chr(44).join(list(squads.keys())[:8])}"
                info = squads[matched]
                return json.dumps({"name":matched,"tag":self.squads.get(matched,chr(9876)),"points":info.get("points",0),"wins":info.get("wins",0),"draws":info.get("draws",0),"losses":info.get("losses",0),"streak":info.get("streak",0),"main_roster_size":len(info.get("main_roster",[])),"achievements":info.get("achievements",[])},indent=2)
            elif name == "get_match_history":
                limit = int(args.get("limit",5)); kf = args.get("kingdom_name","").lower(); matches = sd.get("matches",[])
                if kf: matches = [m for m in matches if kf in m.get("team1","").lower() or kf in m.get("team2","").lower()]
                recent = matches[-limit:][::-1]
                if not recent: return "No matches."
                return "HISTORY:\n"+("\n".join([f"• {m.get('team1','?')} {m.get('score','?')} {m.get('team2','?')} \u2192 {m.get('winner','draw')} [{m.get('date','?')}]" for m in recent]))
            elif name == "get_help":
                topic = args.get("topic","general"); h = {"general":"/member · /leader · /mod · /events · /oracle · /profile","matches":"/mod \u2192 Record Battle \u2192 pick teams \u2192 enter score","events":"/events to browse · /mod \u2192 Events to manage","rankings":"/member \u2192 Rankings panel","challenges":"/leader \u2192 Challenge Kingdom","social":"/mod \u2192 Events \u2192 Record Match (social panel)"}
                return f"HELP ({topic}):\n{h.get(topic,h['general'])}"
            elif name == "record_match":
                if not is_mod(): return "\u274c Permission denied. Only mods can record matches."
                squads = sd.get("squads",{}); t1m = fuzzy(args["team1"],squads); t2m = fuzzy(args["team2"],squads)
                if not t1m or not t2m: return f"\u274c Kingdom not found: '{args['team1']}'\u2192'{t1m}', '{args['team2']}'\u2192'{t2m}'"
                winner = args["winner"]; score = args["score"]
                if winner.lower() == "draw":
                    for k in [t1m,t2m]: squads[k]["draws"]=squads[k].get("draws",0)+1; squads[k]["points"]=squads[k].get("points",0)+1
                    summary = f"Draw — both +1pt"
                else:
                    wm = fuzzy(winner,squads)
                    if not wm: return f"\u274c Winner '{winner}' not found."
                    lm = t2m if wm==t1m else t1m
                    squads[wm]["wins"]=squads[wm].get("wins",0)+1; squads[wm]["points"]=squads[wm].get("points",0)+3; squads[wm]["streak"]=squads[wm].get("streak",0)+1
                    squads[lm]["losses"]=squads[lm].get("losses",0)+1; squads[lm]["streak"]=0
                    summary = f"{wm} wins +3pts · {lm} loss"
                sd.setdefault("matches",[]).append({"id":len(sd.get("matches",[]))+1,"team1":t1m,"team2":t2m,"score":score,"winner":winner.lower(),"date":datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),"recorded_by":str(invoker.id),"source":"oracle"})
                self._save(); return f"\u2705 Recorded: {t1m} {score} {t2m} | {summary}"
            elif name == "create_event":
                if not is_mod(): return "\u274c Permission denied."
                import uuid; eid = str(uuid.uuid4())[:8]
                ev = {"id":eid,"name":args["name"],"type":args.get("event_type","tournament"),"format":args["format"],"date":args["date"],"description":args["description"],"registration_mode":args.get("registration_mode","solo"),"max_entries":args.get("max_entries") or None,"prize_pool":args.get("prize_pool",""),"status":"open","registrations":[],"bracket_data":None,"schedule":[],"tournament_system":"single_elim" if args.get("event_type")=="tournament" else None,"created_by":str(invoker.id),"created_at":datetime.utcnow().isoformat()}
                sd.setdefault("events",[]).append(ev); self._save()
                return f"\u2705 Event created: **{ev['name']}** (ID:{eid}) Type:{ev['type']} Format:{ev['format']} Date:{ev['date']} Status:OPEN"
            elif name == "close_event":
                if not is_mod(): return "\u274c Permission denied."
                ev = next((e for e in sd.get("events",[]) if args["event_name"].lower() in e["name"].lower()), None)
                if not ev: return f"\u274c Event not found: {args['event_name']}"
                ev["status"]="completed"; self._save(); return f"\u2705 Event '{ev['name']}' closed."
            elif name == "add_bounty":
                if not is_mod(): return "\u274c Permission denied."
                matched = fuzzy(args["kingdom_name"], sd.get("squads",{}))
                if not matched: return f"\u274c Kingdom not found: {args['kingdom_name']}"
                sd.setdefault("bounties",{})[matched]={"points":int(args.get("points",2)),"reason":"Added via Oracle","added_at":datetime.utcnow().isoformat()}
                self._save(); return f"\u2705 Bounty set: {matched} \u2014 +{args['points']}pts for defeating them."
            elif name == "post_announcement":
                if not is_mod(): return "\u274c Permission denied."
                ann_ch = discord.utils.get(guild.text_channels, name="\u300e\U0001f4e2\u300f\U0001f170\U0001f17d\U0001f17d\U0001f1f4\U0001f1fa\U0001f17d\U0001f1e8\U0001f1ea\U0001f17c\U0001f1f2\U0001f1ea\U0001f17d\U0001f17e\U0001f17e")
                if not ann_ch:
                    ann_ch = discord.utils.get(guild.text_channels, name="announcements") or discord.utils.get(guild.text_channels, name="\u300e\U0001f4e2\u300f Announcements")
                if not ann_ch: return "\u274c Announcements channel not found."
                role = discord.utils.get(guild.roles, name="MAJESTIC"); mention = role.mention if role else "@MAJESTIC"
                embed = discord.Embed(title=args["title"],description=args["message"],color=0xffd700,timestamp=datetime.utcnow()); embed.set_footer(text="\u29dc Majestic Dominion | Royal Decree")
                await ann_ch.send(content=f"\U0001f4e2 {mention}", embed=embed); return f"\u2705 Announcement posted: '{args['title']}'"
            elif name == "schedule_match":
                if not is_mod(): return "\u274c Permission denied."
                war = discord.utils.get(guild.text_channels, name="\u300e\U0001f3c6\u300f war-results")
                if war:
                    embed = discord.Embed(title="\U0001f4c5 MATCH SCHEDULED!",description=f"\u2694\ufe0f **{args['team1']}** vs **{args['team2']}**\n\n\U0001f4c5 **{args['date_time']}**\n\n*Prepare your lineups, warriors!*",color=0xffd700,timestamp=datetime.utcnow()); embed.set_footer(text="\u29dc Majestic Dominion")
                    await war.send(embed=embed)
                return f"\u2705 Scheduled: {args['team1']} vs {args['team2']} on {args['date_time']}"
            elif name == "add_registrant":
                if not is_mod(): return "\u274c Permission denied."
                ev = next((e for e in sd.get("events",[]) if args["event_name"].lower() in e["name"].lower()), None)
                if not ev: return f"\u274c Event not found: {args['event_name']}"
                ev.setdefault("registrations",[]).append({"player_name":args["participant_name"],"player_id":None,"registered_at":datetime.utcnow().isoformat(),"added_by_mod":True})
                self._save(); return f"\u2705 {args['participant_name']} added to {ev['name']}. Total:{len(ev['registrations'])}"
            else:
                return f"Unknown tool: {name}"
        except Exception as e:
            return f"Tool error ({name}): {str(e)}"

    def _save(self):
        try:
            import sys; main = sys.modules.get("__main__")
            if main and hasattr(main,"save_data"): main.save_data(self.squad_data)
        except Exception as e:
            print(f"Oracle save error: {e}")

    async def _call_gemini(self, messages, guild, invoker):
        if not self.gemini_client: raise RuntimeError("Gemini not configured")
        from google.genai import types as gtypes
        context = self.build_context()

        # Build conversation as a single prompt (new API uses contents list)
        history_text = ""
        for m in messages[:-1]:
            role = "User" if m["role"] == "user" else "Oracle"
            content = m["content"] if isinstance(m["content"], str) else str(m["content"])
            history_text += f"{role}: {content}\n"

        last = messages[-1]["content"]
        full_prompt = (
            f"[SYSTEM]\n{ORACLE_PERSONALITY}\n\n"
            f"[LIVE SERVER DATA]\n{context}\n\n"
            + (f"[CONVERSATION HISTORY]\n{history_text}\n\n" if history_text else "")
            + f"[USER MESSAGE]\n{last}"
        )

        tools = _to_gemini_tools(TOOLS_SCHEMA)
        config = gtypes.GenerateContentConfig(
            tools=[tools],
            temperature=0.7,
        )

        for _ in range(5):
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda p=full_prompt: self.gemini_client.models.generate_content(
                    model=GEMINI_MODEL, contents=p, config=config
                )
            )

            # Check for function calls
            fn_calls = []
            text_parts = []
            for part in response.candidates[0].content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    fn_calls.append(part.function_call)
                elif hasattr(part, "text") and part.text:
                    text_parts.append(part.text)

            if not fn_calls:
                return " ".join(text_parts) if text_parts else "*(no response)*"

            # Execute tools and build new prompt with results
            tool_results_text = ""
            for fc in fn_calls:
                args = dict(fc.args) if fc.args else {}
                result = await self.execute_tool(fc.name, args, guild, invoker)
                tool_results_text += f"[TOOL: {fc.name}]\n{result}\n\n"

            # Continue with tool results appended
            full_prompt = full_prompt + f"\n\n[TOOL RESULTS]\n{tool_results_text}\nNow reply to the user based on these results."

        return "*(Oracle reached thinking limit)*"

    async def _call_groq(self, messages, guild, invoker):
        if not self.groq_client: raise RuntimeError("Groq not configured")
        context = self.build_context()
        # Keep system prompt concise for Groq tool use reliability
        short_personality = """You are the Royal Oracle of Majestic Dominion, an AI assistant for a Mobile Legends: Bang Bang Discord server.
You are helpful, funny, and dramatic. Call members "warriors" and mods "the Royal Council".
Use tools to get real data before answering. For write actions (record_match, create_event etc.) only execute if the user is a moderator.
Keep replies under 200 words. Be fun and engaging."""
        system = short_personality + "\n\nLIVE SERVER DATA:\n" + context
        groq_msgs = [{"role":"system","content":system}]+[{"role":m["role"] if m["role"] in ("user","assistant") else "user","content":m["content"] if isinstance(m["content"],str) else str(m["content"])} for m in messages]
        groq_tools = _to_groq_tools(TOOLS_SCHEMA)
        for attempt in range(5):
            try:
                response = await self.groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=groq_msgs,
                    tools=groq_tools,
                    tool_choice="auto",
                    max_tokens=MAX_TOKENS,
                )
            except Exception as e:
                raise RuntimeError(f"Groq API error: {e}")

            choice = response.choices[0]

            if choice.finish_reason == "stop":
                return choice.message.content or ""

            elif choice.finish_reason == "tool_calls" and choice.message.tool_calls:
                # Build assistant message carefully
                asst_msg = {
                    "role": "assistant",
                    "content": choice.message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments or "{}"
                            }
                        }
                        for tc in choice.message.tool_calls
                    ]
                }
                groq_msgs.append(asst_msg)

                for tc in choice.message.tool_calls:
                    try:
                        raw_args = tc.function.arguments or "{}"
                        # Clean up malformed args
                        raw_args = raw_args.strip()
                        if not raw_args or raw_args == "null":
                            raw_args = "{}"
                        args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        args = {}
                    result = await self.execute_tool(tc.function.name, args, guild, invoker)
                    groq_msgs.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": str(result)
                    })
            else:
                # Unexpected finish reason — return whatever text we have
                return choice.message.content or "*(no response)*"

        return "*(Oracle reached thinking limit — try rephrasing your question)*"

    async def think(self, user_id, username, text, guild, channel, invoker):
        history = self.history[user_id][-CONTEXT_MESSAGES:]
        messages = history + [{"role":"user","content":f"{username}: {text}"}]
        primary_err = None
        # Groq is PRIMARY (truly free, no quota limits)
        try:
            reply = await self._call_groq(messages, guild, invoker)
        except Exception as e:
            primary_err = str(e)
            print(f"\u26a0\ufe0f Oracle Groq error: {e}")
            # Gemini as fallback
            try:
                reply = await self._call_gemini(messages, guild, invoker)
            except Exception as e2:
                print(f"\u26a0\ufe0f Oracle Gemini fallback error: {e2}")
                return "\U0001f52e *The Oracle needs a moment to recover. Please try again shortly.*"
        self.history[user_id] = (messages+[{"role":"assistant","content":reply}])[-CONTEXT_MESSAGES*2:]
        return reply


def setup_oracle(bot, oracle):
    @bot.listen("on_message")
    async def oracle_listener(message):
        if message.author.bot: return
        # Flexible channel match — works regardless of exact emoji/spacing
        ch_name_lower = message.channel.name.lower()
        in_oracle = (
            "oracle" in ch_name_lower or
            "royal oracle" in ch_name_lower or
            "mod oracle" in ch_name_lower or
            message.channel.name in (ORACLE_CHANNEL_NAME, MOD_ORACLE_CHANNEL)
        )
        is_mention = bot.user in message.mentions
        if not (in_oracle or is_mention): return
        limited, msg = oracle.is_rate_limited(message.author.id)
        if limited: await message.reply(msg, mention_author=False); return
        text = message.content.replace(f"<@{bot.user.id}>","").replace(f"<@!{bot.user.id}>","").strip()
        if not text: await message.reply("\U0001f52e *The Oracle stirs... speak your question, warrior.*", mention_author=False); return
        async with message.channel.typing():
            reply = await oracle.think(user_id=message.author.id, username=message.author.display_name, text=text, guild=message.guild, channel=message.channel, invoker=message.author)
        chunks = [reply[i:i+1990] for i in range(0,len(reply),1990)]
        for i,chunk in enumerate(chunks):
            if i==0: await message.reply(chunk, mention_author=False)
            else: await message.channel.send(chunk)

    @bot.tree.command(name="oracle", description="\U0001f52e Consult the Royal Oracle")
    @app_commands.describe(question="Your question or command")
    async def oracle_cmd(interaction: discord.Interaction, question: str):
        limited, msg = oracle.is_rate_limited(interaction.user.id)
        if limited: return await interaction.response.send_message(msg, ephemeral=True)
        await interaction.response.defer(thinking=True)
        reply = await oracle.think(user_id=interaction.user.id, username=interaction.user.display_name, text=question, guild=interaction.guild, channel=interaction.channel, invoker=interaction.user)
        chunks = [reply[i:i+1990] for i in range(0,len(reply),1990)]
        for i,chunk in enumerate(chunks): await interaction.followup.send(chunk)

    @bot.tree.command(name="oracle_clear", description="\U0001f52e Clear Oracle conversation history")
    async def oracle_clear(interaction: discord.Interaction):
        oracle.history.pop(interaction.user.id, None)
        await interaction.response.send_message("\U0001f52e *Memory wiped. Start fresh, warrior!*", ephemeral=True)

    print("\u2705 Oracle: Discord handlers ready")
