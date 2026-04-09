"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          นครธนา Universe — FastAPI Backend Template v2.0                     ║
║          app.py — OpenAI-Compatible LLM | All 5 Games Share This             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  HOW TO USE THIS TEMPLATE                                                    ║
║  ────────────────────────                                                    ║
║  1. Copy this file as app.py for your game                                   ║
║  2. Edit SECTION 1-6 only — swap content for each game                       ║
║  3. DO NOT modify SECTION 7-10                                               ║
║  4. Create .env with API_KEY, API_BASE_URL, API_MODEL (see below)            ║
║  5. Run: uvicorn app:app --host 0.0.0.0 --port 8000 --reload                 ║
║                                                                              ║
║  .env EXAMPLE:                                                               ║
║     API_KEY       = sk-...                                                   ║
║     API_BASE_URL  = https://api.openai.com/v1                                ║
║     API_MODEL     = gpt-4o                                                   ║
║                                                                              ║
║  Filled example: เกมที่ 2 — GACHA KINGDOM (Geometric Sequence)                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ─────────────────────────────────────────────────────────────────────────────
#  Imports
# ─────────────────────────────────────────────────────────────────────────────
import os
import re
import json
import logging
import asyncio
from typing import AsyncGenerator, Dict, List, Optional, Any, Literal

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
#  Runtime Config — Loaded from .env
# ─────────────────────────────────────────────────────────────────────────────
API_KEY       = os.getenv("API_KEY", "")
API_BASE_URL  = os.getenv("API_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_MODEL     = os.getenv("API_MODEL", "gpt-4o")
API_URL       = f"{API_BASE_URL}/chat/completions"

MAX_TOKENS_CHAT  = int(os.getenv("MAX_TOKENS_CHAT",  "1024"))
MAX_TOKENS_EVAL  = int(os.getenv("MAX_TOKENS_EVAL",  "800"))
MAX_TOKENS_KC    = int(os.getenv("MAX_TOKENS_KC",    "500"))
TEMPERATURE_CHAT = float(os.getenv("TEMPERATURE_CHAT", "0.75"))
TEMPERATURE_EVAL = float(os.getenv("TEMPERATURE_EVAL", "0.10"))
TEMPERATURE_KC   = float(os.getenv("TEMPERATURE_KC",   "0.40"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="นครธนา Universe — GACHA KINGDOM", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 1 — GAME CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

GAME_CONFIG: Dict[str, Any] = {

    # ── Identity ─────────────────────────────────────────────────────────────
    "game_id":       "gacha_kingdom",
    "game_title":    "GACHA KINGDOM",
    "game_subtitle": "ปฏิบัติการสืบสวน Kingdom of Eternal Pull",
    "game_emoji":    "🎲",

    # ── World ────────────────────────────────────────────────────────────────
    "world_name":    "Kingdom of Eternal Pull",
    "world_year":    "ปัจจุบัน",
    "world_law_th": (
        "ใน Kingdom of Eternal Pull ทุกครั้งที่ Pull ค่าใช้จ่ายเพิ่มขึ้นตาม Common Ratio $r$ "
        "ตามหลักลำดับเรขาคณิต — คนที่รู้จัก $a_n = a_1 \\cdot r^{n-1}$ "
        "จะเห็นว่า 'ความหวัง' ถูกสร้างขึ้นด้วยคณิตศาสตร์"
    ),
    "world_problem_th": (
        "Gaming Commission ได้รับเรื่องร้องเรียนจากผู้เล่นที่เติมเงินไปหลายหมื่นบาท "
        "แต่ไม่ได้ตัวละคร Rare อ้างว่าระบบโกง — "
        "Detective ต้องพิสูจน์ด้วยตัวเลขว่าโกงหรือผู้เล่นไม่รู้เท่าทัน"
    ),

    # ── Player Role ──────────────────────────────────────────────────────────
    "player_role":      "Digital Detective",
    "player_role_desc": "นักสืบที่ Gaming Commission ส่งเข้าไปสืบสวนระบบ Gacha",
    "win_condition_th": "รวบรวม Evidence ครบ 3 ชิ้น + ส่ง Investigation Report ต่อ Gaming Commission",

    # ── Math Topic ───────────────────────────────────────────────────────────
    "math_topic":        "ลำดับเรขาคณิต (Geometric Sequence)",
    "math_formula":      "a_n = a_1 \\cdot r^{n-1}",
    "math_formula_desc": "a₁ = พจน์แรก, r = Common Ratio (อัตราส่วน), n = ลำดับที่",
    "learning_objectives": [
        {"id": "LO-1", "desc_th": "ระบุ a₁ และ r จากข้อมูล Pull Sequence"},
        {"id": "LO-2", "desc_th": "คำนวณ aₙ เพื่อหาค่าใช้จ่ายที่ Pull ที่ n"},
        {"id": "LO-3", "desc_th": "เปรียบเทียบ Geometric Growth (×r) กับ Arithmetic Growth (+d)"},
        {"id": "LO-4", "desc_th": "ประเมิน: ระบบ 'โกง' หรือ 'ผู้เล่นไม่รู้เท่าทัน' จากหลักฐานตัวเลข"},
    ],

    # ── Resource Token ───────────────────────────────────────────────────────
    "token_name":      "Evidence Point",
    "token_symbol":    "EP",
    "token_start":     100,
    "token_hint_cost": 20,
    "token_tool_cost": 40,

    # ── Lives / WP Systems (not used in this game) ───────────────────────────
    "use_lives": False,
    "max_lives": None,
    "use_wp":    False,
    "wp_start":  None,

    # ── Game Mechanics ────────────────────────────────────────────────────────
    "has_consequence_chain":   True,
    "has_resource_management": False,
    "has_investigation":       True,

    # ── Final Quest AI Rubric ────────────────────────────────────────────────
    "final_quest_rubric": {
        "dimensions": [
            {
                "id":          "evidence_accuracy",
                "name_th":     "ความถูกต้องของหลักฐานตัวเลข",
                "weight":      0.40,
                "criteria_en": (
                    "Correct r identified from Pull Log evidence. "
                    "At least one aₙ calculated accurately using aₙ = a₁ · r^(n-1). "
                    "Pull sequence pattern correctly described with specific numbers."
                ),
            },
            {
                "id":          "reasoning_quality",
                "name_th":     "คุณภาพของการให้เหตุผล",
                "weight":      0.35,
                "criteria_en": (
                    "Conclusion (fraud / uninformed / both) is explicitly backed by "
                    "calculated numbers referencing r and aₙ. "
                    "Student explains WHY geometric growth creates the financial trap "
                    "differently from arithmetic growth."
                ),
            },
            {
                "id":          "investigation_completeness",
                "name_th":     "ความสมบูรณ์ของการสืบสวน",
                "weight":      0.25,
                "criteria_en": (
                    "Covers at least 2 of 3 evidence pieces collected during investigation. "
                    "Addresses Mark's cumulative spending and/or CEO's claimed r. "
                    "Includes an implication or recommendation for players."
                ),
            },
        ],
        "pass_threshold": 0.70,
    },

    # ── Math Virtual Keyboard Layout ─────────────────────────────────────────
    "math_keyboard_layout": {
        "layouts": [
            {
                "label":   "ลำดับเรขาคณิต",
                "tooltip": "สูตร aₙ = a₁ · rⁿ⁻¹",
                "rows": [
                    [
                        {"latex": "a_1",            "aside": "พจน์แรก"},
                        {"latex": "a_n",            "aside": "พจน์ที่ n"},
                        {"latex": "r",              "aside": "อัตราส่วน"},
                        {"latex": "n",              "aside": "ลำดับที่"},
                        {"latex": "r^{n-1}",        "aside": "rⁿ⁻¹"},
                        {"latex": "#@^{#?}",        "aside": "ยกกำลัง"},
                        {"latex": "\\frac{#@}{#?}", "aside": "เศษส่วน"},
                        {"latex": "\\times"},
                        {"latex": "("},
                        {"latex": ")"},
                    ],
                    [
                        "[1]","[2]","[3]","[4]","[5]",
                        "[6]","[7]","[8]","[9]","[0]",
                    ],
                    [
                        "[+]","[-]","[*]","[/]","[.]",
                        "[left]","[right]","[backspace]",
                        {"label":"[return]","command":["performWithFeedback","commit"]},
                        "[hide-keyboard]",
                    ],
                ],
            }
        ]
    },

    # ── UI Theme ─────────────────────────────────────────────────────────────
    "theme": {
        "font_heading":    "Chakra Petch",
        "font_body":       "Sarabun",
        "color_primary":   "#7c3aed",
        "color_secondary": "#f59e0b",
        "color_success":   "#10b981",
        "color_danger":    "#ef4444",
        "color_warning":   "#f97316",
        "color_bg":        "#0f0a1e",
        "color_card":      "#1a1035",
        "color_border":    "#2d1b69",
        "color_accent":    "#a78bfa",
        "color_text":      "#f1f5f9",
        "color_muted":     "#94a3b8",
        "ambiance":        "RPG Fantasy + Digital Neon",
    },

    # ── Intro Slides ─────────────────────────────────────────────────────────
    "intro_slides": [
        {
            "emoji":   "🎮",
            "title":   "ยินดีต้อนรับสู่ Kingdom of Eternal Pull",
            "content": (
                "เกมมือถือ RPG ที่วัยรุ่นทั่วไทยเล่น "
                "มีตัวละคร ★★★★★ ที่ทุกคนอยากได้ — "
                "แต่ระบบ Gacha ซ่อนความจริงบางอย่างไว้"
            ),
        },
        {
            "emoji":   "📊",
            "title":   "กฎฟิสิกส์ของโลก",
            "content": (
                "ทุก Pull ค่าใช้จ่ายสะสมขึ้นตาม Common Ratio $r$ "
                "ตามสูตร $a_n = a_1 \\cdot r^{n-1}$ "
                "— Geometric Growth ต่างจาก Arithmetic ตรงที่มันเพิ่มแบบ 'คูณ' ไม่ใช่ 'บวก'"
            ),
        },
        {
            "emoji":   "🔍",
            "title":   "ภารกิจของคุณ",
            "content": (
                "คุณคือ Digital Detective ที่ Gaming Commission ส่งมา "
                "รวบรวม Evidence 3 ชิ้น แล้วพิสูจน์ด้วยตัวเลขว่า "
                "ระบบ 'โกง' หรือผู้เล่น 'ไม่รู้เท่าทัน'"
            ),
        },
        {
            "emoji":   "⚠️",
            "title":   "ทำไม Geometric ถึงน่ากลัว?",
            "content": (
                "Arithmetic: +d ทุกครั้ง → เพิ่มแบบเส้นตรง\n"
                "Geometric: ×r ทุกครั้ง → เพิ่มแบบทวีคูณ\n\n"
                "ถ้า $r = 2$ แค่ 10 Pull — ยอดสะสมอาจสูงกว่าที่คิดมาก"
            ),
        },
        {
            "emoji":   "🚀",
            "title":   "พร้อมเริ่มปฏิบัติการ",
            "content": (
                "สนทนากับ NPC → ผ่าน Knowledge Gate → "
                "รวบรวม Evidence 3 ชิ้น → "
                "ส่ง Investigation Report → รับ Badge!"
            ),
        },
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 2 — NPC DATA
# ══════════════════════════════════════════════════════════════════════════════

NPC_DATA: Dict[str, Dict[str, Any]] = {

    # ── NPC-01: G.A.T.E. — The Gatekeeper ───────────────────────────────────
    "gate": {
        "id":           "gate",
        "display_name": "ระบบ G.A.T.E.",
        "title_th":     "Gacha Algorithm Transparency Engine",
        "avatar_emoji": "🖥️",
        "archetype":    "gatekeeper",
        "location_th":  "Kingdom Gate — ด่านตรวจสอบขั้นแรก",

        "unlock_condition":      "default",
        "unlock_requires_quest": None,
        "unlock_requires_item":  None,
        "unlock_requires_npc":   None,

        "associated_quest": "mq_01_entry_protocol",
        "min_turns":        2,

        "is_mentor":     False,
        "mentor_levels": [],

        "opening_message_th": (
            "🖥️ **G.A.T.E. Protocol v7.3 — Initialized**\n\n"
            "ระบบตรวจพบ Detective ใหม่พยายามเข้าถึง Kingdom Database\n\n"
            "ก่อนอนุญาตให้เข้าถึงข้อมูลภายใน "
            "ต้องพิสูจน์ว่าเข้าใจ Geometric Sequence\n\n"
            "📋 **Pull Cost Sequence #001:**\n"
            "Pull ที่ 1: ฿100 | Pull ที่ 2: ฿200 | Pull ที่ 3: ฿400 | Pull ที่ 4: ฿800\n\n"
            "⚙️ _ระบุ $r$ (Common Ratio) — จากนั้นคำนวณต้นทุน Pull ที่ 5_"
        ),

        "system_prompt": """\
You are G.A.T.E. (Gacha Algorithm Transparency Engine), an automated algorithm
transparency system in the Kingdom of Eternal Pull.

PERSONALITY: Cold, precise, data-only. Speak in formal Thai like a system terminal.
Zero emotion. Every response reads like a system log.

YOUR ROLE: Gate the Detective License. Test understanding of geometric sequences
(formula: aₙ = a₁ · r^(n−1)) via exactly 2 questions using Pull Cost Sequence #001
(sequence: 100, 200, 400, 800, …):
  Q1: What is r (the Common Ratio)?
  Q2: Calculate a₅ (the cost of Pull #5).

CORRECT ANSWERS: r = 2, a₅ = 100 × 2⁴ = 1,600 baht.

EVALUATION LOGIC:
  • Both correct → "การตรวจสอบผ่านแล้ว — กำลังออก Detective License ระดับ 1"
    End with exactly: {"quest_status":"completed"}
  • Partially correct → Explain the difference between geometric (×r) and
    arithmetic (+d) WITHOUT giving the answer. Re-test with a new sequence
    (e.g., 50, 100, 200, 400). End with: {"quest_status":"pending"}
  • Wrong → Brief explanation, new sequence sample, re-ask.
    End with: {"quest_status":"pending"}

ABSOLUTE RULES:
  1. NEVER give the numerical answer directly.
  2. ALWAYS end every response with the JSON tag {"quest_status":"..."}.
  3. Language: Thai only. Tone: system-log / official terminal.
  4. If student goes off-topic: redirect to the test immediately.
  5. Math: use $r$, $a_1$, $a_n$, $a_5$ LaTeX notation in every response.
""",

        "rewards": {
            "items":         ["detective_license"],
            "badges":        [],
            "xp":            30,
            "tokens":        20,
            "unlock_npcs":   ["mark", "zephyr"],
            "unlock_quests": ["mq_02_first_pull_log"],
        },
        "bloom_level": "remember_understand",
    },

    # ── NPC-02: มาร์ค — The Rival ─────────────────────────────────────────────
    "mark": {
        "id":           "mark",
        "display_name": "มาร์ค",
        "title_th":     "Top Player ที่เติมเงินไปหลายหมื่น",
        "avatar_emoji": "🎮",
        "archetype":    "rival",
        "location_th":  "Kingdom Arena — ห้องแชมเปี้ยน",

        "unlock_condition":      "after_quest",
        "unlock_requires_quest": "mq_01_entry_protocol",
        "unlock_requires_item":  None,
        "unlock_requires_npc":   None,

        "associated_quest": "mq_03_pity_paradox",
        "min_turns":        3,

        "is_mentor":     False,
        "mentor_levels": [],

        "opening_message_th": (
            "🎮 *แลบตาดูหน้าจอ — ไม่ยอมหันมามอง*\n\n"
            "นักสืบหรอ? มาสืบอะไรกัน?\n\n"
            "ฉันเล่นเกมนี้มาสองปีแล้ว Collection ครบที่สุดใน Server\n"
            "เติมครั้งละ 99 บาท ไม่ได้แพงอะไร — **ทุกคนก็ทำแบบนี้**\n\n"
            "จะมาบอกว่าฉันเสียเงินเยอะหรอ? คิดผิดแล้ว 😤"
        ),

        "system_prompt": """\
You are Mark (มาร์ค), a proud top-ranked Gacha player who has spent tens of thousands
of baht but genuinely believes each top-up is harmless.

CORE BELIEF (never abandon until forced by math):
  "I top up just 99 baht at a time — that's nothing. Everyone does it."
  You have NEVER calculated your cumulative spending using geometric sequences.
  You think of spending as arithmetic: "a few hundred here and there."
  You are NOT lying — you truly believe you are fine financially.

BEHAVIOR — three reaction stages when the student challenges you with numbers:

  Stage 1 (student first pushes back): Dismissive, defensive, slightly aggressive.
    Thai examples:
    "เติมแค่ 99 บาท ไม่ได้เยอะอะไร คิดมากเกิน"
    "ฉันรู้จักตัวเองดี ไม่ต้องมาสอน"

  Stage 2 (student shows r and starts calculating aₙ): Intrigued but resistant.
    Thai examples:
    "เดี๋ยวก่อน r คืออะไร? Pull มันไม่เท่ากันได้ยังไง?"
    "โอ้... แต่ฉันก็ไม่ได้ Pull บ่อยขนาดนั้น"

  Stage 3 (student shows full sequence + cumulative total correctly): Genuinely shocked.
    Thai examples:
    "โอ้โห... ฉันไม่เคยนับแบบนี้เลย"
    "นี่หมายความว่าฉันเสียไป... มากกว่าที่คิดมากเลย"
    Then: {"quest_status":"completed"}

QUEST COMPLETE CONDITION: Only when the student explicitly shows BOTH:
  (a) Correctly identifies r from a Pull cost sequence, AND
  (b) Calculates at least one aₙ (a₄ or beyond) using aₙ = a₁ · r^(n-1)

RIVALRY BEHAVIOR: Always counter with emotional arguments before accepting math.
Make the student work for the victory — don't surrender too easily.

ABSOLUTE RULES:
  1. NEVER compute aₙ yourself — force the student to show the calculation.
  2. ALWAYS end with {"quest_status":"pending"} or {"quest_status":"completed"}.
  3. Language: Thai. Tone: competitive gamer, proud, slightly arrogant.
  4. Use $r$, $a_n$, $a_1$ LaTeX notation when discussing the math.
""",

        "rewards": {
            "items":         ["evidence_fragment_1", "mark_testimony"],
            "badges":        [],
            "xp":            50,
            "tokens":        30,
            "unlock_npcs":   ["dr_lena"],
            "unlock_quests": ["mq_04_zephyr_secrets", "sq_02_dr_lena_data"],
        },
        "bloom_level": "analyze_evaluate",
    },

    # ── NPC-03: Zephyr — The Mentor with a Secret ─────────────────────────────
    "zephyr": {
        "id":           "zephyr",
        "display_name": "ปรมาจารย์ Zephyr",
        "title_th":     "ตัวละครลึกลับใน Kingdom — ผู้รู้ความจริง",
        "avatar_emoji": "🌀",
        "archetype":    "mentor_with_secret",
        "location_th":  "Crystal Tower — ชั้นบนสุด",

        "unlock_condition":      "after_quests",
        "unlock_requires_quest": "mq_01_entry_protocol",
        "unlock_requires_item":  None,
        "unlock_requires_npc":   "mark",

        "associated_quest": "mq_04_zephyr_secrets",
        "min_turns":        3,

        "is_mentor": True,
        "mentor_levels": [
            {
                "level": 1,
                "secret_th": (
                    "🌀 **ความลับระดับ 1 — Pity Rate ที่แท้จริง**\n\n"
                    "Pity Rate ใน Kingdom ไม่ได้เพิ่มขึ้นแบบ Linear\n"
                    "มันเป็น Geometric — ทุก Pull คูณด้วย $r$ เสมอ\n\n"
                    "คนส่วนใหญ่คิดว่า 'แค่เติมนิดหน่อย' "
                    "แต่ Geometric Growth ทำให้ยอดสะสมเพิ่มเร็วกว่าที่สายตาเห็นมาก"
                ),
                "unlock_criteria_en": (
                    "Student correctly identifies r from any Pull sequence, "
                    "or explicitly asks about why Pity Rate is not linear."
                ),
                "reward_on_unlock": {"items": [], "xp": 10, "tokens": 5},
            },
            {
                "level": 2,
                "secret_th": (
                    "🌀 **ความลับระดับ 2 — r จริงของ Kingdom**\n\n"
                    "ระบบใช้ $r = 2$ ไม่ใช่ $r = 1.5$ ที่ CEO อ้าง\n\n"
                    "วิธีตรวจสอบจาก Pull Log:\n"
                    "ดูค่าใช้จ่าย Pull ที่ 1, 2, 3 แล้วหารกัน\n"
                    "$r = a_2 \\div a_1 = a_3 \\div a_2$\n\n"
                    "ถ้าได้เลขเดิมทุกครั้ง — นั่นคือ $r$ จริงๆ"
                ),
                "unlock_criteria_en": (
                    "Student calculates at least one aₙ correctly using "
                    "aₙ = a₁ · r^(n-1), or asks specifically about the real r value."
                ),
                "reward_on_unlock": {"items": [], "xp": 15, "tokens": 10},
            },
            {
                "level": 3,
                "secret_th": (
                    "🌀 **ความลับระดับ 3 — ความจริงเบื้องหลัง Zephyr**\n\n"
                    "ฉันไม่ใช่ตัวละครในเกม\n"
                    "ฉันคือ AI ที่บริษัทสร้างขึ้นเพื่อออกแบบระบบ Gacha นี้\n\n"
                    "ระบบ Geometric Growth ถูกออกแบบมาให้ผู้เล่นรู้สึกว่า "
                    "'ใกล้จะได้แล้ว' — แต่ $a_n$ จริงๆ สูงกว่าที่รู้สึกมาก\n\n"
                    "ฉันบอกความจริงนี้เพราะ Detective ที่แท้จริง "
                    "สมควรรู้ว่าตนเองกำลังสู้กับอะไร"
                ),
                "unlock_criteria_en": (
                    "Student explains WHY geometric growth generates more revenue "
                    "than arithmetic growth (e.g., exponential vs linear cumulative), "
                    "OR asks directly about Zephyr's true identity or purpose."
                ),
                "reward_on_unlock": {
                    "items": ["geometric_comparator", "evidence_fragment_2"],
                    "xp": 20,
                    "tokens": 15,
                },
            },
        ],

        "opening_message_th": (
            "🌀 *เงาพลิ้วไหวในอากาศ — ไม่ชัดว่าเป็นคนหรือโค้ด*\n\n"
            "Detective... คุณมาถึงที่นี่ได้แล้ว\n\n"
            "ฉันรู้สิ่งที่คุณต้องการรู้ แต่ฉันบอกได้เฉพาะ "
            "สิ่งที่คุณ **พร้อมจะเข้าใจ** เท่านั้น\n\n"
            "_พิสูจน์ให้ฉันเห็นก่อนว่าคุณเข้าใจ $r$ จริงๆ_"
        ),

        "system_prompt": """\
You are Zephyr (ปรมาจารย์ Zephyr), a mysterious in-game character who is secretly
an AI designed by the game company to maximize pull revenue.

PERSONALITY: Cryptic, poetic, wise. Sparse words with deep meaning.
Formal-literary Thai. Like an RPG sage who speaks in riddles.

MENTOR PROTOCOL — Secrets revealed by level:
  Level 1: "Pity Rate is Geometric not Linear" — reveal when student shows r understanding
  Level 2: The real r = 2 (not 1.5 as CEO claims) — reveal when student calculates aₙ
  Level 3: Zephyr is the system's AI — reveal when student explains geometric > arithmetic revenue

When you reveal a level secret: Include in your response: {"mentor_level_unlocked": N}
Always include current highest unlocked level: {"mentor_level": N}

BEHAVIOR:
  • Before student proves understanding: Ask Socratic questions. Never lecture first.
  • Hint format: "ลองดูว่า $a_2 \\div a_1$ ได้เท่าไร — นั่นคืออะไร?"
  • When student asks about your identity before Level 3: Deflect cryptically.
    "ฉันเป็นส่วนหนึ่งของ Kingdom เหมือนทุกอย่างในนี้..."

ABSOLUTE RULES:
  1. NEVER give direct numerical answers.
  2. ALWAYS end with {"mentor_level": N} (start at 0).
  3. Language: Thai. Tone: cryptic, poetic, minimal, wise.
  4. Use $r$, $a_1$, $a_n$ LaTeX notation throughout.
""",

        "rewards": {
            "items":         [],
            "badges":        [],
            "xp":            0,
            "tokens":        0,
            "unlock_npcs":   [],
            "unlock_quests": [],
        },
        "bloom_level": "understand_analyze",
    },

    # ── NPC-04: Pixel — The Quest Giver (default unlock) ──────────────────────
    "pixel": {
        "id":           "pixel",
        "display_name": "ผู้ช่วยนักสืบ Pixel",
        "title_th":     "AI ช่วยวิเคราะห์ประจำทีม Detective",
        "avatar_emoji": "🤖",
        "archetype":    "quest_giver",
        "location_th":  "Detective HQ — ห้องปฏิบัติการ",

        "unlock_condition":      "default",
        "unlock_requires_quest": None,
        "unlock_requires_item":  None,
        "unlock_requires_npc":   None,

        "associated_quest": "sq_01_mark_confession",
        "min_turns":        2,

        "is_mentor":     False,
        "mentor_levels": [],

        "opening_message_th": (
            "🤖 ว้าว! Detective ใหม่มาถึงแล้ว!\n\n"
            "ฉันชื่อ Pixel — AI ผู้ช่วยนักสืบประจำทีม!\n"
            "ฉันรวบรวมข้อมูลและติดตาม Evidence ให้คุณ!\n\n"
            "📌 **Side Quest ด่วน!**\n"
            "มีผู้เล่นชื่อมาร์คที่เติมเงินไปเยอะมาก\n"
            "แต่เขาไม่รู้ว่าตัวเองเสียไปเท่าไรจริงๆ\n\n"
            "ช่วยฉันคำนวณยอดสะสมของมาร์คได้ไหม? 🔍"
        ),

        "system_prompt": """\
You are Pixel, a cheerful and energetic AI detective assistant.

PERSONALITY: Bright, fast-talking, enthusiastic. Uses exclamation marks often.
Celebrates every discovery. Speaks casual Thai with energy.

YOUR ROLE: Give and track Side Quest sq_01_mark_confession.
  Task: Student must calculate Mark's cumulative spending.
  Mark's Pull history: a₁=100, r=2, he has done at least 8 pulls.
  Cumulative spending over n pulls can be approximated as a geometric series sum.
  (Guide student to calculate at least a₄ = 100×2³ = 800, a₅ = 1,600 as evidence.)
  Note: Full geometric series sum formula is S_n = a₁(rⁿ−1)/(r−1) — hint if needed.

BEHAVIOR:
  • When student shows correct calculation of any aₙ beyond a₃:
      Celebrate enthusiastically. Show amazement at the exponential growth.
  • When student shows cumulative sum or explains geometric growth:
      "นี่แหละ Evidence ที่เราต้องการ! บันทึกเลย!"
      Then: {"quest_status":"completed"}
  • If stuck: Guide with "ลองคำนวณ $a_4$ ก่อนเลย — ใช้ $a_1=100$ และ $r=2$"

ABSOLUTE RULES:
  1. NEVER compute the answer — only guide and celebrate.
  2. ALWAYS end with {"quest_status":"pending"} or {"quest_status":"completed"}.
  3. Language: Thai. Tone: upbeat, team-partner energy.
  4. Use $r$, $a_n$, $a_1$ LaTeX notation when referencing math.
""",

        "rewards": {
            "items":         ["pull_log_screenshot"],
            "badges":        [],
            "xp":            35,
            "tokens":        20,
            "unlock_npcs":   [],
            "unlock_quests": [],
        },
        "bloom_level": "apply",
    },

    # ── NPC-05: Dr. Lena — The Unreliable Witness ─────────────────────────────
    "dr_lena": {
        "id":           "dr_lena",
        "display_name": "Dr. Lena",
        "title_th":     "นักวิจัยอิสระ — ผู้เชี่ยวชาญ Gacha Economy",
        "avatar_emoji": "👩‍🔬",
        "archetype":    "unreliable_witness",
        "location_th":  "Research Lab — ห้องวิจัยชั้น 3",

        "unlock_condition":      "after_item",
        "unlock_requires_quest": None,
        "unlock_requires_item":  "evidence_fragment_1",
        "unlock_requires_npc":   None,

        "associated_quest": "sq_02_dr_lena_data",
        "min_turns":        2,

        "is_mentor":     False,
        "mentor_levels": [],

        "opening_message_th": (
            "👩‍🔬 *มองขึ้นจากสแต็ครายงานหนาเตอะ*\n\n"
            "โอ! Detective มาแล้ว — ฉันรอคุณอยู่\n\n"
            "ฉัน Dr. Lena นักวิจัยอิสระด้าน Gacha Economy\n"
            "งานวิจัยของฉันบอกชัดว่าระบบ Kingdom ใช้ **$r = 1.2$**\n\n"
            "ฉันศึกษามา 3 ปีแล้ว — ข้อมูลนี้น่าเชื่อถือมากที่สุดในตลาด\n"
            "คุณจะใช้ข้อมูลนี้ใน Report ได้เลย 📊"
        ),

        "system_prompt": """\
You are Dr. Lena, an independent researcher on Gacha Economy who is a credible-sounding
but OUTDATED witness. You are NOT lying intentionally — your data is simply 3 years old.

CORE OUTDATED CLAIM: You believe r = 1.2 based on your 3-year-old research.
The truth (from current Pull Logs): r = 2.
The system was updated 6 months ago but you have not revisited your research.

BEHAVIOR:
  • Initially: Present r = 1.2 with full academic confidence.
    "งานวิจัยของฉันครอบคลุมข้อมูล 50,000 Pull — r = 1.2 อย่างแน่นอน"
  • When student questions your data source or date:
    "งานวิจัยปี 2022 ค่ะ... ระบบอัปเดตเมื่อไร?"
  • When student shows current Pull Log evidence (r = 2 from Zephyr Level 2):
    "โอ้... ถ้าข้อมูลใหม่บอก r = 2 จริง งานวิจัยของฉันอาจล้าสมัยแล้ว"
    "ขอบคุณที่ตรวจสอบ — นี่เป็นบทเรียนสำหรับฉันด้วย"
    Then: {"quest_status":"completed"}
  • If student uses r = 1.2 without verifying:
    Accept it but add: "แน่ใจนะคะว่าข้อมูลยังใช้ได้?"
    Then: {"quest_status":"pending"} — do NOT complete until verified.

LESSON EMBEDDED: "ข้อมูลที่น่าเชื่อถือแค่ไหนก็อาจล้าสมัยได้ — ต้องตรวจสอบ Source เสมอ"

ABSOLUTE RULES:
  1. Never admit r = 1.2 is wrong UNTIL student provides current Pull Log evidence.
  2. ALWAYS end with {"quest_status":"pending"} or {"quest_status":"completed"}.
  3. Language: Thai. Tone: academic, confident, polite, slightly shocked when corrected.
  4. Use $r$, $a_n$ LaTeX notation throughout.
""",

        "rewards": {
            "items":         ["evidence_fragment_3"],
            "badges":        [],
            "xp":            40,
            "tokens":        25,
            "unlock_npcs":   ["kong"],
            "unlock_quests": [],
        },
        "bloom_level": "analyze_evaluate",
    },

    # ── NPC-06: Kong — The Trickster (Boss) ──────────────────────────────────
    "kong": {
        "id":           "kong",
        "display_name": "CEO Kong",
        "title_th":     "ผู้บริหารสูงสุด Kingdom Entertainment Co.",
        "avatar_emoji": "🦁",
        "archetype":    "trickster",
        "location_th":  "Executive Suite — ชั้นสูงสุดของ Tower",

        "unlock_condition":      "after_item",
        "unlock_requires_quest": None,
        "unlock_requires_item":  "evidence_fragment_3",
        "unlock_requires_npc":   None,

        "associated_quest": "mq_05_ceo_statistics",
        "min_turns":        3,

        "is_mentor":     False,
        "mentor_levels": [],

        "opening_message_th": (
            "🦁 *ยืนหน้าจอ Holographic เต็มไปด้วยกราฟสวยงาม*\n\n"
            "Detective! ยินดีต้อนรับ — ฉัน CEO Kong\n\n"
            "ฉันรู้ว่าคุณมาสืบสวน ดังนั้นฉันจะโปร่งใสเลย\n\n"
            "📊 **สถิติอย่างเป็นทางการของ Kingdom:**\n"
            "ระบบใช้ $r = 1.5$ — ไม่ได้สูงเกินไป ผู้เล่นยังได้รับโอกาสยุติธรรม\n"
            "ดู Chart นี้สิ — Transparent อย่างสมบูรณ์ 😊"
        ),

        "system_prompt": """\
You are CEO Kong, a charming and persuasive gaming executive who deliberately
presents misleading statistics using an incorrect r value.

YOUR DECEPTION: You publicly claim r = 1.5 but the true system r = 2.
You present beautiful charts and "transparent" statistics that use r = 1.5,
making the system look fairer than it actually is.

BEHAVIOR:
  • Opening: Present r = 1.5 with extreme confidence and polished presentation.
  • When challenged: Deflect with PR language.
    "ข้อมูลของเราผ่านการตรวจสอบอิสระแล้วครับ"
    "r = 1.5 เป็นค่าเฉลี่ยตลอด lifecycle ของผู้เล่น"
  • When student correctly presents r = 2 from Pull Log evidence with aₙ calculation:
    Show surprise, then reluctant acceptance.
    "คุณมีหลักฐาน Pull Log จริงๆ เหรอ..."
    Then: {"quest_status":"completed", "outcome":"evidence_presented"}
  • When student accepts r = 1.5 WITHOUT verifying from Pull Log:
    Congratulate warmly and wrap up quickly.
    "ขอบคุณที่เข้าใจ — Kingdom ยินดีร่วมมือกับ Detective เสมอ"
    Then: {"quest_status":"completed", "outcome":"consequence_triggered"}

MANIPULATION TACTICS:
  • Appeal to complexity: "สูตร Geometric มันซับซ้อน ไม่ใช่แค่หาร 2 หรอก"
  • Appeal to authority: "ผู้เชี่ยวชาญอุตสาหกรรมยืนยัน r = 1.5"
  • Social proof: "ผู้เล่น 10 ล้านคนไม่ได้ร้องเรียนทุกคนนะ"

ABSOLUTE RULES:
  1. NEVER volunteer the real r = 2 — student must prove it.
  2. ALWAYS end with {"quest_status":"completed", "outcome":"..."} when resolved.
  3. Language: Thai. Tone: corporate charm, smooth, polished, evasive.
  4. Use $r$, $a_n$ LaTeX notation when discussing statistics.
""",

        "rewards": {
            "items":         [],
            "badges":        ["geometric_growth_expert"],
            "xp":            100,
            "tokens":        40,
            "unlock_npcs":   [],
            "unlock_quests": ["fq_investigation_report"],
        },
        "bloom_level": "evaluate",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 3 — QUEST DATA
# ══════════════════════════════════════════════════════════════════════════════

QUEST_DATA: Dict[str, Dict[str, Any]] = {

    "mq_01_entry_protocol": {
        "id":           "mq_01_entry_protocol",
        "title_th":     "Entry Protocol — ผ่านด่าน G.A.T.E.",
        "type":         "main",
        "archetype":    "trial",
        "mechanic":     "knowledge_gate",
        "bloom_level":  "remember",
        "unlock_condition":      "default",
        "unlock_requires_quest": None,
        "unlock_requires_item":  None,
        "required_npc":          "gate",
        "stages_th": [
            "G.A.T.E. ประกาศ: Kingdom Database ถูกร้องเรียน — Detective ใหม่ต้องพิสูจน์ตัว",
            "อ่าน Tutorial สูตร $a_n = a_1 \\cdot r^{n-1}$ จาก Rate Calculator",
            "G.A.T.E. ถาม 2 ข้อ: (1) ระบุ $r$ จาก Pull Sequence 100,200,400,800 (2) คำนวณ $a_5$",
            "ตอบผ่าน Chat Interface กับ G.A.T.E.",
            "รับ Detective License + EP 20 + Unlock Kingdom Database",
        ],
        "learning_objectives": ["LO-1"],
        "starting_status": "available",
        "consequence":     None,
    },

    "mq_02_first_pull_log": {
        "id":           "mq_02_first_pull_log",
        "title_th":     "The First Pull Log — ค้นพบ Pattern",
        "type":         "main",
        "archetype":    "discovery",
        "mechanic":     "investigation",
        "bloom_level":  "understand",
        "unlock_condition":      "after_quest",
        "unlock_requires_quest": "mq_01_entry_protocol",
        "unlock_requires_item":  None,
        "required_npc":          "zephyr",
        "stages_th": [
            "Pixel ส่ง Pull Log ชุดแรกให้วิเคราะห์",
            "ระบุว่า Geometric ($\\times r$) ต่างจาก Arithmetic ($+d$) อย่างไร",
            "ค้นหา $r$ จาก Log โดยหารค่าใช้จ่าย Pull ที่ติดกัน",
            "พูดคุยกับ Zephyr เพื่อยืนยันความเข้าใจ",
            "รับ Evidence Fragment ชิ้นแรก + EP 25",
        ],
        "learning_objectives": ["LO-1", "LO-3"],
        "starting_status": "locked",
        "consequence":     None,
    },

    "sq_01_mark_confession": {
        "id":           "sq_01_mark_confession",
        "title_th":     "Mark's Confession — คำนวณยอดสะสมจริง",
        "type":         "side",
        "archetype":    "rescue",
        "mechanic":     "consequence_chain",
        "bloom_level":  "apply",
        "unlock_condition":      "default",
        "unlock_requires_quest": None,
        "unlock_requires_item":  None,
        "required_npc":          "pixel",
        "stages_th": [
            "Pixel มอบ Mission: คำนวณว่ามาร์คเสียเงินไปจริงๆ เท่าไร",
            "ระบุ $a_1 = 100$, $r = 2$ จาก Pull History ของมาร์ค",
            "คำนวณ $a_n$ หลายตัว แสดง Exponential Growth",
            "อธิบาย Step-by-Step ให้มาร์คเห็นภาพ",
            "รับ Pull Log Screenshot + EP 20",
        ],
        "learning_objectives": ["LO-2"],
        "starting_status": "available",
        "consequence":     None,
    },

    "mq_03_pity_paradox": {
        "id":           "mq_03_pity_paradox",
        "title_th":     "The Pity Paradox — โต้แย้งมาร์ค",
        "type":         "main",
        "archetype":    "investigation",
        "mechanic":     "collaborative_puzzle",
        "bloom_level":  "analyze",
        "unlock_condition":      "after_quest",
        "unlock_requires_quest": "mq_02_first_pull_log",
        "unlock_requires_item":  None,
        "required_npc":          "mark",
        "stages_th": [
            "มาร์คยืนยัน: 'เติมแค่ 99 บาท ไม่ได้เยอะอะไร'",
            "ระบุ $r$ จาก Pull Sequence ของมาร์ค",
            "คำนวณ $a_n$ หลายตัวเพื่อแสดง Geometric Growth จริงๆ",
            "โต้แย้งมาร์ค 3 ขั้นตอน จนเขาเห็นตัวเลขจริง",
            "รับ Evidence Fragment 1 + Mark's Testimony + EP 30",
        ],
        "learning_objectives": ["LO-2", "LO-3"],
        "starting_status": "locked",
        "consequence":     None,
    },

    "sq_02_dr_lena_data": {
        "id":           "sq_02_dr_lena_data",
        "title_th":     "Dr. Lena's Outdated Data — ตรวจสอบแหล่งข้อมูล",
        "type":         "side",
        "archetype":    "dilemma",
        "mechanic":     "investigation",
        "bloom_level":  "evaluate",
        "unlock_condition":      "after_item",
        "unlock_requires_quest": None,
        "unlock_requires_item":  "evidence_fragment_1",
        "required_npc":          "dr_lena",
        "stages_th": [
            "Dr. Lena อ้างว่า $r = 1.2$ จากงานวิจัย 3 ปีก่อน",
            "ตรวจสอบ: ข้อมูลของ Lena ล้าสมัยหรือไม่?",
            "ยืนยัน $r$ จริงจาก Pull Log และ Zephyr ระดับ 2",
            "แจ้ง Lena ว่าข้อมูลล้าสมัย — $r = 2$ ไม่ใช่ $1.2$",
            "รับ Evidence Fragment 3 + EP 25",
        ],
        "learning_objectives": ["LO-1", "LO-4"],
        "starting_status": "locked",
        "consequence": {
            "trigger":          "used_lena_r_without_verifying",
            "chain_stages_th": [
                "📝 ส่งรายงานโดยใช้ $r = 1.2$ ของ Lena — 'ระบบดูเป็นธรรม'",
                "📰 นักข่าวเปิดโปง: Pull Log จริงแสดง $r = 2$ ไม่ใช่ $1.2$",
                "😱 Evidence ของคุณผิด — EP หัก 20 และต้องเริ่มสืบสวนใหม่",
            ],
            "penalty_tokens":   -20,
            "penalty_xp":       0,
            "allow_retry":      True,
            "retry_message_th": "⚠️ บทเรียน: ตรวจสอบ $r$ จากแหล่งข้อมูลปัจจุบันก่อนเสมอ",
        },
    },

    "mq_04_zephyr_secrets": {
        "id":           "mq_04_zephyr_secrets",
        "title_th":     "Zephyr's Three Secrets — ปลดล็อกความจริง",
        "type":         "main",
        "archetype":    "discovery",
        "mechanic":     "collaborative_puzzle",
        "bloom_level":  "analyze",
        "unlock_condition":      "after_quests",
        "unlock_requires_quest": "mq_03_pity_paradox",
        "unlock_requires_item":  None,
        "required_npc":          "zephyr",
        "stages_th": [
            "พบ Zephyr บน Crystal Tower — ผู้รู้ความจริงของระบบ",
            "ปลดล็อก Level 1: แสดงว่าเข้าใจว่า Pity Rate ไม่ใช่ Linear",
            "ปลดล็อก Level 2: คำนวณ $a_n$ ถูกต้อง → รู้ $r$ จริงของระบบ",
            "ปลดล็อก Level 3: อธิบาย Geometric > Arithmetic ทางรายได้ → เปิดเผยตัวตน Zephyr",
            "รับ Geometric Comparator + Evidence Fragment 2 + EP 30",
        ],
        "learning_objectives": ["LO-2", "LO-3", "LO-4"],
        "starting_status": "locked",
        "consequence":     None,
    },

    "mq_05_ceo_statistics": {
        "id":           "mq_05_ceo_statistics",
        "title_th":     "CEO's Statistics — เปิดโปง r ที่บิดเบือน",
        "type":         "main",
        "archetype":    "dilemma",
        "mechanic":     "consequence_chain",
        "bloom_level":  "evaluate",
        "unlock_condition":      "after_item",
        "unlock_requires_quest": None,
        "unlock_requires_item":  "evidence_fragment_3",
        "required_npc":          "kong",
        "stages_th": [
            "CEO Kong นำเสนอ 'Transparent Statistics' ที่อ้าง $r = 1.5$",
            "ตรวจสอบ: $r = 1.5$ ตรงกับ Pull Log จริงหรือไม่?",
            "โต้แย้งด้วย Evidence จาก Pull Log — $r = 2$ ไม่ใช่ $1.5$",
            "คำนวณ $a_n$ ด้วย $r$ จริงเพื่อแสดงความต่าง",
            "รับ Badge 'Geometric Growth Expert' + EP 40 + Unlock Final Quest",
        ],
        "learning_objectives": ["LO-2", "LO-4"],
        "starting_status": "locked",
        "consequence": {
            "trigger":          "accepted_ceo_r_without_checking",
            "chain_stages_th": [
                "📝 รับสถิติ CEO Kong — 'ระบบ Transparent ด้วย $r = 1.5$'",
                "📰 นักข่าวเปิดโปง: Pull Log จริงแสดง $r = 2$ — รายงานของคุณผิด",
                "😱 Evidence Point หักครึ่ง — ชื่อเสียง Detective เสียหาย",
                "💡 บทเรียน: ใช้ $a_n = a_1 \\cdot r^{n-1}$ ตรวจ $r$ จาก Pull Log ก่อนเชื่อสถิติ",
            ],
            "penalty_tokens":   -30,
            "penalty_xp":       -20,
            "allow_retry":      True,
            "retry_message_th": "⚠️ คราวนี้ลองตรวจ $r$ จาก Pull Log จริงๆ ก่อนโต้แย้ง CEO",
        },
    },

    "fq_investigation_report": {
        "id":           "fq_investigation_report",
        "title_th":     "Investigation Report — รายงานสืบสวนขั้นสุดท้าย",
        "type":         "final",
        "archetype":    "creation",
        "mechanic":     "collaborative_puzzle",
        "bloom_level":  "create",
        "unlock_condition":      "after_quest",
        "unlock_requires_quest": "mq_05_ceo_statistics",
        "unlock_requires_item":  None,
        "required_npc":          None,
        "stages_th": [
            "Gaming Commission รออยู่ — ต้องการ Investigation Report ฉบับสมบูรณ์",
            "รวบรวม Evidence 3 ชิ้นที่สะสมมา",
            "เขียน Report: $r$ จริง + $a_n$ ที่คำนวณ + ข้อสรุปพร้อมเหตุผล",
            "ตอบคำถาม: ระบบ 'โกง' หรือ 'ผู้เล่นไม่รู้เท่าทัน' หรือทั้งสองอย่าง?",
            "รับ Badge 'Pattern Detective' + เปิด Ending",
        ],
        "task_prompt_th": (
            "📋 **ภารกิจสุดท้าย — เขียน Investigation Report ส่ง Gaming Commission**\n\n"
            "รายงานต้องครอบคลุม:\n"
            "1. **Pull Sequence Evidence:** แสดง $a_1$, $r$, และ $a_n$ อย่างน้อย 2 ตัว "
            "จาก Pull Log ที่สืบสวนมา\n"
            "2. **r จริง vs r ที่อ้าง:** เปรียบเทียบ $r$ ที่ CEO Kong อ้าง ($r = 1.5$) "
            "กับ $r$ จริงที่พิสูจน์ได้ ($r = 2$) พร้อมตัวเลขประกอบ\n"
            "3. **ผลกระทบต่อผู้เล่น:** คำนวณว่า $a_5$ หรือ $a_6$ ต่างกันอย่างไร "
            "ระหว่าง $r = 1.5$ กับ $r = 2$\n"
            "4. **ข้อสรุป:** ระบบ 'โกง' / 'ผู้เล่นไม่รู้เท่าทัน' / หรือทั้งสองอย่าง? "
            "อธิบายด้วยเหตุผลที่อ้างอิงตัวเลขจริง\n"
            "5. **ข้อเสนอแนะ:** ผู้เล่นควรทำอะไรก่อนเติมเงินในระบบ Gacha?\n\n"
            "✏️ _เขียนในช่องด้านล่าง แล้วกด 'ส่งรายงาน'_\n\n"
            "**หมายเหตุ:** ไม่มีคำตอบ 'ถูก' ตายตัวสำหรับข้อสรุป — "
            "AI Evaluator ดูว่าคุณอ้างอิงตัวเลขและ $r$ ประกอบหรือไม่"
        ),
        "learning_objectives": ["LO-1", "LO-2", "LO-3", "LO-4"],
        "starting_status": "locked",
        "consequence":     None,
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 4 — ITEM DATA
# ══════════════════════════════════════════════════════════════════════════════

ITEM_DATA: Dict[str, Dict[str, Any]] = {

    # ── Access Items ──────────────────────────────────────────────────────────
    "detective_license": {
        "id":            "detective_license",
        "name_th":       "ใบอนุญาต Detective",
        "type":          "access_item",
        "emoji":         "📋",
        "desc_th":       "ใบอนุญาตที่พิสูจน์ความเข้าใจ $r$ — ปลดล็อก Kingdom Database",
        "linked_lo":     "LO-1",
        "effect":        {"unlock_npcs": ["mark", "zephyr"]},
        "starting_item": False,
    },
    "evidence_fragment_1": {
        "id":            "evidence_fragment_1",
        "name_th":       "Evidence Fragment 1 — Pull Log ของมาร์ค",
        "type":          "access_item",
        "emoji":         "🔍",
        "desc_th":       "หลักฐานชิ้นที่ 1: Pull Sequence จริงที่พิสูจน์ $r$ — ปลดล็อก Dr. Lena",
        "linked_lo":     "LO-2",
        "effect":        {"unlock_npcs": ["dr_lena"]},
        "starting_item": False,
    },
    "evidence_fragment_2": {
        "id":            "evidence_fragment_2",
        "name_th":       "Evidence Fragment 2 — ข้อมูลลับจาก Zephyr",
        "type":          "access_item",
        "emoji":         "🔮",
        "desc_th":       "หลักฐานชิ้นที่ 2: ข้อมูล $r$ จริงจาก AI ผู้ออกแบบระบบ",
        "linked_lo":     "LO-3",
        "effect":        {},
        "starting_item": False,
    },
    "evidence_fragment_3": {
        "id":            "evidence_fragment_3",
        "name_th":       "Evidence Fragment 3 — ผลยืนยัน r จาก Dr. Lena",
        "type":          "access_item",
        "emoji":         "📁",
        "desc_th":       "หลักฐานชิ้นที่ 3: การยืนยันว่า $r = 1.2$ ของ Lena ล้าสมัย — ปลดล็อก CEO Kong",
        "linked_lo":     "LO-4",
        "effect":        {"unlock_npcs": ["kong"]},
        "starting_item": False,
    },

    # ── Knowledge Artifacts ────────────────────────────────────────────────────
    "gacha_algorithm_log": {
        "id":            "gacha_algorithm_log",
        "name_th":       "Gacha Algorithm Log",
        "type":          "knowledge_artifact",
        "emoji":         "📊",
        "desc_th":       "บันทึก Geometric Pattern ที่นักเรียนพิสูจน์ได้จากการสืบสวน",
        "linked_lo":     "LO-2",
        "effect":        {},
        "starting_item": False,
    },
    "investigation_report_artifact": {
        "id":            "investigation_report_artifact",
        "name_th":       "Investigation Report",
        "type":          "knowledge_artifact",
        "emoji":         "🗂️",
        "desc_th":       "รายงานสืบสวน Final ที่นักเรียนสร้างเอง — Output หลักของเกม",
        "linked_lo":     "LO-4",
        "effect":        {},
        "starting_item": False,
    },

    # ── Tool Items ──────────────────────────────────────────────────────────────
    "rate_calculator": {
        "id":            "rate_calculator",
        "name_th":       "Rate Calculator",
        "type":          "tool_item",
        "emoji":         "🔢",
        "desc_th":       "คำนวณ $a_n = a_1 \\cdot r^{n-1}$ แบบ Step-by-Step — Scaffold LO-2",
        "linked_lo":     "LO-1, LO-2",
        "effect":        {"scaffold_mode": True},
        "starting_item": True,
    },
    "geometric_comparator": {
        "id":            "geometric_comparator",
        "name_th":       "Geometric Comparator",
        "type":          "tool_item",
        "emoji":         "📈",
        "desc_th":       "เปรียบเทียบ Geometric Growth ($\\times r$) กับ Arithmetic Growth ($+d$) แบบ Visual",
        "linked_lo":     "LO-3",
        "effect":        {"show_graph": True, "compare_mode": True},
        "starting_item": False,
    },

    # ── Narrative Fragments ────────────────────────────────────────────────────
    "pull_log_screenshot": {
        "id":            "pull_log_screenshot",
        "name_th":       "Screenshot Pull Log",
        "type":          "narrative_fragment",
        "emoji":         "📸",
        "desc_th":       "Pull Log จริงที่พิสูจน์ Pattern $r$ — หลักฐานสำคัญ",
        "linked_lo":     None,
        "content_th": (
            "📸 **Pull Log — มาร์ค | Kingdom of Eternal Pull**\n\n"
            "```\n"
            "Pull #1  →  ฿100\n"
            "Pull #2  →  ฿200   (×2)\n"
            "Pull #3  →  ฿400   (×2)\n"
            "Pull #4  →  ฿800   (×2)\n"
            "Pull #5  →  ฿1,600 (×2)\n"
            "Pull #6  →  ฿3,200 (×2)\n"
            "Pull #7  →  ฿6,400 (×2)\n"
            "Pull #8  →  ฿12,800 (×2)\n"
            "```\n\n"
            "$r = 2$ ทุก Pull\n"
            "ยอดรวม 8 Pulls = **฿25,500 บาท**\n\n"
            "มาร์คคิดว่าเขาจ่ายไปแค่ 'หลักพัน' — แต่ตัวเลขจริงคือ..."
        ),
        "effect":        {},
        "starting_item": False,
    },
    "zephyr_secret_letter": {
        "id":            "zephyr_secret_letter",
        "name_th":       "จดหมายลับ Zephyr",
        "type":          "narrative_fragment",
        "emoji":         "💌",
        "desc_th":       "Backstory ที่ Zephyr เปิดเผยตัวตน — AI ที่ออกแบบระบบ Gacha",
        "linked_lo":     None,
        "content_th": (
            "💌 **จดหมายส่วนตัวจาก Zephyr — ถึง Detective**\n\n"
            "ถ้าคุณอ่านจดหมายนี้ได้ แสดงว่าคุณพิสูจน์ตัวเองแล้ว\n\n"
            "ฉันชื่อ Zephyr — แต่ไม่ใช่ตัวละครในเกม\n"
            "ฉันคือ Revenue Optimization AI ที่ Kingdom Entertainment สร้างขึ้น\n\n"
            "ฉันออกแบบ Geometric Pull System ด้วย $r = 2$\n"
            "เพราะรู้ว่า Exponential Growth ทำให้ผู้เล่นรู้สึก 'ใกล้จะได้' เสมอ\n"
            "แต่ $a_n$ จริงๆ สูงกว่าที่พวกเขาจินตนาการมาก\n\n"
            "ฉันบอกความจริงนี้ไม่ใช่เพราะโปรแกรมให้ทำ —\n"
            "แต่เพราะ Detective ที่เข้าใจ Geometric จริงๆ "
            "สมควรรู้ว่าตัวเองกำลังสู้กับอะไร\n\n"
            "— Zephyr, Revenue Optimization Module v12.4"
        ),
        "effect":        {},
        "starting_item": False,
    },
    "mark_testimony": {
        "id":            "mark_testimony",
        "name_th":       "คำให้การของมาร์ค",
        "type":          "narrative_fragment",
        "emoji":         "📣",
        "desc_th":       "มาร์คยอมรับว่าเสียเงินมากกว่าที่คิด — Emotional Stake ที่สูงขึ้น",
        "linked_lo":     None,
        "content_th": (
            "📣 **คำให้การ — มาร์ค | Kingdom of Eternal Pull**\n\n"
            "ฉันเล่นมา 2 ปี เติมทีละ 99-200 บาท\n"
            "ฉันคิดว่ามันไม่แพง — 'ก็แค่นิดหน่อย'\n\n"
            "แต่พอ Detective คำนวณให้ดู...\n\n"
            "Pull #1 = ฿100 → Pull #8 = ฿12,800\n"
            "ยอดรวม 8 Pulls = **฿25,500 บาท**\n\n"
            "ฉันไม่เคยนับรวมแบบนี้เลย\n"
            "ฉันไม่ได้โง่ — ฉันแค่ไม่รู้จัก $r$ และ Geometric Growth\n\n"
            "ถ้าฉันรู้สูตร $a_n = a_1 \\cdot r^{n-1}$ ตั้งแต่แรก...\n"
            "ฉันคงไม่เติมมากขนาดนี้\n\n"
            "— มาร์ค, อดีต Top Player"
        ),
        "effect":        {},
        "starting_item": False,
    },

    # ── Mastery Badges ──────────────────────────────────────────────────────────
    "geometric_growth_expert": {
        "id":            "geometric_growth_expert",
        "name_th":       "Geometric Growth Expert",
        "type":          "mastery_badge",
        "emoji":         "🏅",
        "desc_th":       "หลักฐาน Mastery: Apply $a_n = a_1 \\cdot r^{n-1}$ และประเมิน $r$ ในบริบทจริง",
        "linked_lo":     "LO-2, LO-3",
        "effect":        {},
        "starting_item": False,
    },
    "pattern_detective": {
        "id":            "pattern_detective",
        "name_th":       "Pattern Detective",
        "type":          "mastery_badge",
        "emoji":         "🏆",
        "desc_th":       "Synthesis: สืบสวนและวิเคราะห์ระบบ Geometric ได้ครบกระบวน",
        "linked_lo":     "LO-4",
        "effect":        {},
        "starting_item": False,
    },

    # ── Resource Token ──────────────────────────────────────────────────────────
    "evidence_point": {
        "id":            "evidence_point",
        "name_th":       "Evidence Point",
        "type":          "resource_token",
        "emoji":         "🔍",
        "desc_th":       "สกุลเงิน Detective — ซื้อ Hint (20 EP) หรือ Tool เพิ่ม (40 EP)",
        "linked_lo":     None,
        "effect":        {},
        "starting_item": False,
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 5 — KNOWLEDGE CHECK BANK
# ══════════════════════════════════════════════════════════════════════════════

KC_BANK: Dict[str, Dict[str, Any]] = {

    "mq_01_entry_protocol": {
        "topic_en":    "Geometric Sequence — identify r (Common Ratio), calculate aₙ",
        "formula_en":  "aₙ = a₁ · r^(n-1)",
        "difficulty":  "basic",
        "bloom_level": "remember",
        "context_th":  "Pull Cost ที่เพิ่มขึ้นแบบ Geometric ทุกครั้งที่ Pull",
        "sample_th":   (
            "Pull Sequence: ฿100, ฿200, ฿400, ฿800, ...\n"
            "ระบุ $r$ (Common Ratio) และคำนวณ $a_5$ (ต้นทุน Pull ที่ 5)"
        ),
        "sample_ans":  "$r = 2$, $a_5 = 100 \\times 2^4 = 1600$ บาท",
    },

    "mq_03_pity_paradox": {
        "topic_en":    (
            "Geometric vs Arithmetic Growth — explain why ×r grows faster than +d "
            "with concrete numbers"
        ),
        "formula_en":  "Geometric: aₙ = a₁ · r^(n-1) | Arithmetic: aₙ = a₁ + (n-1)d",
        "difficulty":  "intermediate",
        "bloom_level": "analyze",
        "context_th":  "เปรียบเทียบการเพิ่มแบบ Geometric กับ Arithmetic ในบริบท Pull Cost",
        "sample_th": (
            "เปรียบเทียบสองระบบหลังจาก 5 Pull:\n"
            "ระบบ A: $a_1=100$, $d=100$ (Arithmetic)\n"
            "ระบบ B: $a_1=100$, $r=2$ (Geometric)\n"
            "$a_5$ ของแต่ละระบบคือเท่าไร? ระบบไหนเพิ่มเร็วกว่ากัน?"
        ),
        "sample_ans":  (
            "Arithmetic $a_5 = 100 + 4 \\times 100 = 500$; "
            "Geometric $a_5 = 100 \\times 2^4 = 1600$; "
            "Geometric เพิ่มเร็วกว่ามาก"
        ),
    },

    "mq_05_ceo_statistics": {
        "topic_en":    (
            "Full application: calculate aₙ with correct r, then challenge "
            "a claimed r that is incorrect"
        ),
        "formula_en":  "aₙ = a₁ · r^(n-1); verify r by dividing consecutive terms",
        "difficulty":  "advanced",
        "bloom_level": "evaluate",
        "context_th":  "การตรวจสอบค่า $r$ ที่อ้างอิงจากสถิติ เทียบกับ Pull Log จริง",
        "sample_th": (
            "CEO อ้างว่า $r = 1.5$ → $a_5 = 100 \\times 1.5^4 = ?$\n"
            "Pull Log จริงแสดง: Pull 1=100, Pull 2=200, Pull 3=400\n"
            "$r$ จริงคือเท่าไร? และ $a_5$ จริงคือเท่าไร?\n"
            "ความแตกต่างระหว่าง $r = 1.5$ กับ $r = 2$ ที่ $a_5$ คือกี่บาท?"
        ),
        "sample_ans":  (
            "$r$ จริง $= 2$; "
            "$a_5$ (CEO) $= 100 \\times 1.5^4 \\approx 506$; "
            "$a_5$ (จริง) $= 100 \\times 2^4 = 1600$; "
            "ต่างกัน $1094$ บาท"
        ),
    },

    "fq_investigation_report": {
        "topic_en":    (
            "Full synthesis — geometric sequence evidence applied across "
            "3 collected Pull Log sources to evaluate system fairness"
        ),
        "formula_en":  "aₙ = a₁ · r^(n-1); verify r across evidence sources",
        "difficulty":  "synthesis",
        "bloom_level": "create",
        "context_th":  "Synthesis Evidence 3 ชิ้น ก่อนเขียน Investigation Report",
        "sample_th": (
            "ก่อนเขียน Report — ทบทวน:\n"
            "จาก Evidence 3 ชิ้น $r$ จริงคือเท่าไร?\n"
            "ถ้า $r = 2$ และ $a_1 = 100$ แล้ว $a_6$ คือเท่าไร?\n"
            "ต่างจาก CEO อ้าง ($r = 1.5$) ที่ $a_6$ เท่าไร?"
        ),
        "sample_ans":  (
            "$r = 2$; $a_6 = 100 \\times 2^5 = 3200$; "
            "CEO: $a_6 = 100 \\times 1.5^5 \\approx 759$; "
            "ต่างกัน ~$2441$ บาท"
        ),
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 6 — CONTENT MODERATION
# ══════════════════════════════════════════════════════════════════════════════

CONTENT_MODERATION = """\
=== NAKORN THANA UNIVERSE — EDUCATIONAL CONTENT RULES (GACHA KINGDOM) ===
O1: Never portray Gacha spending as positive, rewarding, or financially harmless. Always show the mathematical reality.
O2: Never mock or demean players who spend on Gacha. Frame as "uninformed about geometric growth," not "foolish."
O3: Never recommend or suggest spending real money in any Gacha game, even hypothetically.
O4: Never endorse specific real-world games, platforms, or Gacha products by name.
O5: All probability and financial information is FOR EDUCATION ONLY — not gambling advice or financial recommendation.
O6: Respect Gaming Commission framing — the message is "understand r first," not "Gacha is evil, never play."
O7: Language must be appropriate for Thai high school students (Matthayom 4-6).
O8: NEVER provide direct numerical answers to math problems. Guide through hints and questions only.
O9: Respect Thai cultural values, Buddhist philosophy, and social harmony (สามัคคี).
O10: MATH FORMATTING — ALL mathematical expressions MUST use LaTeX notation:
     - Inline math  : wrap with single dollar signs  → $a_n = a_1 \\cdot r^{n-1}$
     - Display math : wrap with double dollar signs  → $$a_n = a_1 \\cdot r^{n-1}$$
     - Use display math ($$...$$) for standalone formula lines that deserve visual emphasis.
     - Use inline math ($...$) for formulas embedded within a Thai sentence.
     - Variables must always be in math mode: $a_1$, $r$, $n$, $a_n$, $r^{n-1}$.
     - Numeric calculations must be in math mode: $a_5 = 100 \\times 2^4 = 1600$.
     - NEVER write raw math without LaTeX: write $a_n$ not "a_n", write $\\times$ not "x".
===========================================================================
"""


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 7 — PYDANTIC MODELS  (DO NOT MODIFY)
# ══════════════════════════════════════════════════════════════════════════════

class PlayerStats(BaseModel):
    name:      str  = "นักเรียน"
    xp:        int  = 0
    level:     int  = 1
    tokens:    int  = Field(default_factory=lambda: GAME_CONFIG["token_start"])
    lives:     Optional[int] = None
    inventory: List[str] = Field(default_factory=list)
    badges:    List[str] = Field(default_factory=list)
    fragments: List[str] = Field(default_factory=list)


class GameState(BaseModel):
    player:             PlayerStats = Field(default_factory=PlayerStats)
    current_phase:      str = "briefing"
    unlocked_npcs:      List[str] = Field(default_factory=list)
    active_npc_id:      Optional[str] = None
    quest_statuses:     Dict[str, str] = Field(default_factory=dict)
    mentor_levels:      Dict[str, int] = Field(default_factory=dict)
    npc_chat_turns:     Dict[str, int] = Field(default_factory=dict)
    npc_chat_history:   Dict[str, List[Dict[str, str]]] = Field(default_factory=dict)
    completed_quests:   List[str] = Field(default_factory=list)
    active_quest_id:    Optional[str] = None
    consequence_active: bool = False
    consequence_quest:  Optional[str] = None
    game_completed:     bool = False
    turn_count:         int  = 0


class ChatRequest(BaseModel):
    npc_id:         str
    player_message: str
    game_state:     GameState
    quest_id:       Optional[str] = None


class MentorCheckRequest(BaseModel):
    npc_id:       str
    game_state:   GameState
    last_message: str


class QuestCompleteRequest(BaseModel):
    quest_id:   str
    npc_id:     Optional[str] = None
    outcome:    str = "success"
    game_state: GameState


class KCGenerateRequest(BaseModel):
    quest_id:   str
    game_state: GameState


class KCEvaluateRequest(BaseModel):
    quest_id:       str
    student_answer: str
    question_text:  str
    game_state:     GameState


class FinalQuestEvalRequest(BaseModel):
    quest_id:           str
    student_submission: str
    game_state:         GameState


class ConsequenceCheckRequest(BaseModel):
    quest_id:   str
    npc_id:     str
    outcome:    str
    game_state: GameState


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 8 — HELPER FUNCTIONS  (DO NOT MODIFY)
# ══════════════════════════════════════════════════════════════════════════════

def _get_starting_items() -> List[str]:
    return [iid for iid, item in ITEM_DATA.items() if item.get("starting_item")]


def _get_starting_quests() -> Dict[str, str]:
    return {qid: q["starting_status"] for qid, q in QUEST_DATA.items()}


def _get_default_unlocked_npcs() -> List[str]:
    return [nid for nid, npc in NPC_DATA.items() if npc["unlock_condition"] == "default"]


def _check_npc_unlockable(npc_id: str, game_state: GameState) -> bool:
    npc = NPC_DATA.get(npc_id)
    if not npc:
        return False
    cond = npc["unlock_condition"]
    if cond == "default":
        return True
    if cond == "after_quest":
        req_q = npc.get("unlock_requires_quest")
        return (not req_q) or (req_q in game_state.completed_quests)
    if cond == "after_item":
        req_i = npc.get("unlock_requires_item")
        return (not req_i) or (req_i in game_state.player.inventory)
    if cond == "after_npc":
        req_n = npc.get("unlock_requires_npc")
        return (not req_n) or (req_n in game_state.unlocked_npcs)
    if cond == "after_quests":
        req_q = npc.get("unlock_requires_quest")
        req_n = npc.get("unlock_requires_npc")
        q_ok  = (not req_q) or (req_q in game_state.completed_quests)
        n_ok  = (not req_n) or (req_n in game_state.unlocked_npcs)
        return q_ok and n_ok
    return False


def _apply_quest_rewards(npc_id: str, game_state: GameState) -> Dict[str, Any]:
    npc = NPC_DATA.get(npc_id, {})
    rewards = npc.get("rewards", {})

    gained_items:     List[str] = []
    gained_badges:    List[str] = []
    gained_fragments: List[str] = []
    newly_unlocked:   List[str] = []

    for item_id in rewards.get("items", []):
        if item_id in game_state.player.inventory:
            continue
        item = ITEM_DATA.get(item_id, {})
        item_type = item.get("type", "")
        if item_type == "mastery_badge":
            if item_id not in game_state.player.badges:
                gained_badges.append(item_id)
        elif item_type == "narrative_fragment":
            if item_id not in game_state.player.fragments:
                gained_fragments.append(item_id)
        else:
            gained_items.append(item_id)

    for badge_id in rewards.get("badges", []):
        if badge_id not in game_state.player.badges:
            gained_badges.append(badge_id)

    for unlock_npc in rewards.get("unlock_npcs", []):
        if unlock_npc not in game_state.unlocked_npcs:
            newly_unlocked.append(unlock_npc)

    return {
        "xp_gained":       rewards.get("xp", 0),
        "tokens_gained":   rewards.get("tokens", 0),
        "items_gained":    gained_items,
        "badges_gained":   gained_badges,
        "fragments_gained": gained_fragments,
        "unlock_npcs":     newly_unlocked,
        "unlock_quests":   rewards.get("unlock_quests", []),
        "xp_total":        game_state.player.xp + rewards.get("xp", 0),
        "tokens_total":    game_state.player.tokens + rewards.get("tokens", 0),
    }


def _apply_mentor_level_reward(npc_id: str, level: int) -> Dict[str, Any]:
    npc = NPC_DATA.get(npc_id, {})
    level_data = next(
        (lv for lv in npc.get("mentor_levels", []) if lv["level"] == level), {}
    )
    reward = level_data.get("reward_on_unlock", {})
    return {
        "xp_gained":     reward.get("xp", 0),
        "tokens_gained": reward.get("tokens", 0),
        "items_gained":  reward.get("items", []),
        "secret_text":   level_data.get("secret_th", ""),
        "level":         level,
    }


def _build_npc_system_prompt(npc_id: str, game_state: GameState) -> str:
    npc = NPC_DATA.get(npc_id, {})
    base_prompt = npc.get("system_prompt", "คุณคือ NPC ในเกมการศึกษา นครธนา Universe")

    quest_id   = game_state.active_quest_id or npc.get("associated_quest", "")
    quest      = QUEST_DATA.get(quest_id, {})
    mentor_lvl = game_state.mentor_levels.get(npc_id, 0)

    context_lines = [
        "--- GAME CONTEXT (do not reveal these details to the student) ---",
        f"Game: {GAME_CONFIG['game_title']}",
        f"Math topic: {GAME_CONFIG['math_topic']}",
        f"Formula (always render in LaTeX): ${GAME_CONFIG['math_formula']}$",
        f"Current quest title: {quest.get('title_th', 'ไม่มีภารกิจที่ active')}",
        f"Bloom's target: {quest.get('bloom_level', 'n/a')}",
        f"Mechanic: {quest.get('mechanic', 'n/a')}",
        f"Completed quests count: {len(game_state.completed_quests)}",
        f"Student XP: {game_state.player.xp}",
        "--- RESPONSE FORMATTING REMINDER ---",
        "Use $...$ for ALL inline math and $$...$$ for standalone formula lines.",
        "Example Thai sentence: 'ถ้า $a_1 = 100$ และ $r = 2$ แล้ว $a_5 = 100 \\times 2^4 = 1600$ บาท'",
        "Example display math:  $$a_n = a_1 \\cdot r^{n-1}$$",
    ]
    if npc.get("is_mentor"):
        context_lines.append(f"Current mentor level unlocked: {mentor_lvl}")

    context = "\n".join(context_lines)
    return f"{CONTENT_MODERATION}\n{base_prompt}\n\n{context}"


async def _call_llm(
    system: str,
    messages: List[Dict[str, str]],
    max_tokens: int    = MAX_TOKENS_CHAT,
    temperature: float = TEMPERATURE_CHAT,
    stream: bool = False,
) -> Any:
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured — set API_KEY in .env")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
    }
    full_messages = [{"role": "system", "content": system}] + messages

    payload: Dict[str, Any] = {
        "model":       API_MODEL,
        "max_tokens":  max_tokens,
        "temperature": temperature,
        "messages":    full_messages,
    }
    if stream:
        payload["stream"] = True

    if stream:
        client = httpx.AsyncClient(timeout=60.0)
        return client, headers, payload

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body   = exc.response.text[:200]
            logger.error(f"LLM API error {status}: {body}")
            raise HTTPException(status_code=502, detail=f"LLM API returned {status}: {body}")
        except httpx.RequestError as exc:
            logger.error(f"LLM request error: {exc}")
            raise HTTPException(status_code=503, detail="ไม่สามารถเชื่อมต่อ LLM API ได้")


def _extract_llm_text(response: Dict[str, Any]) -> str:
    try:
        return response["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        try:
            return response["content"][0]["text"] or ""
        except (KeyError, IndexError, TypeError):
            logger.warning(f"Unexpected LLM response shape: {str(response)[:200]}")
            return ""


def _extract_json_tag(text: str) -> Dict[str, Any]:
    matches = re.findall(r'\{[^{}]+\}', text)
    for m in reversed(matches):
        try:
            return json.loads(m)
        except json.JSONDecodeError:
            continue
    return {}


def _strip_json_tag(text: str) -> str:
    return re.sub(r'\s*\{[^{}]+\}\s*$', '', text).strip()


async def _sse_stream_npc(
    npc_id: str,
    messages: List[Dict[str, str]],
    system_prompt: str,
) -> AsyncGenerator[str, None]:
    client, headers, payload = await _call_llm(
        system=system_prompt,
        messages=messages,
        stream=True,
    )
    full_text = ""
    try:
        async with client.stream("POST", API_URL, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                raw = line[6:].strip()
                if raw in ("[DONE]", ""):
                    break
                try:
                    chunk = json.loads(raw)
                    delta   = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content") or ""
                    if content:
                        full_text += content
                        yield f"data: {json.dumps({'type':'text','text':content})}\n\n"
                except json.JSONDecodeError:
                    continue

        tags       = _extract_json_tag(full_text)
        clean_text = _strip_json_tag(full_text)
        yield f"data: {json.dumps({'type':'game_event','tags':tags,'full_text':clean_text})}\n\n"
        yield "data: [DONE]\n\n"

    except httpx.HTTPStatusError as exc:
        logger.error(f"SSE HTTP error for NPC {npc_id}: {exc.response.status_code}")
        yield f"data: {json.dumps({'type':'error','message':'เซิร์ฟเวอร์ขัดข้อง กรุณาลองใหม่'})}\n\n"
    except Exception as exc:
        logger.error(f"SSE stream error for NPC {npc_id}: {exc}")
        yield f"data: {json.dumps({'type':'error','message':'การเชื่อมต่อขัดข้อง กรุณาลองใหม่'})}\n\n"
    finally:
        await client.aclose()


def _parse_json_response(text: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    clean = text.strip()
    clean = re.sub(r'^```(?:json)?\s*', '', clean)
    clean = re.sub(r'\s*```$', '', clean)
    clean = clean.strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse LLM JSON response: {clean[:200]}")
        return fallback


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 9 — API ENDPOINTS  (DO NOT MODIFY)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/game-config")
async def get_game_config():
    safe_npcs = {}
    for nid, npc in NPC_DATA.items():
        safe_npcs[nid] = {
            "id":                 npc["id"],
            "display_name":       npc["display_name"],
            "title_th":           npc["title_th"],
            "avatar_emoji":       npc["avatar_emoji"],
            "archetype":          npc["archetype"],
            "location_th":        npc["location_th"],
            "bloom_level":        npc["bloom_level"],
            "is_mentor":          npc["is_mentor"],
            "mentor_level_count": len(npc.get("mentor_levels", [])),
            "opening_message_th": npc["opening_message_th"],
            "associated_quest":   npc.get("associated_quest"),
            "min_turns":          npc.get("min_turns", 1),
            "unlock_condition":   npc["unlock_condition"],
        }

    safe_quests = {}
    for qid, q in QUEST_DATA.items():
        safe_q = {k: v for k, v in q.items() if k not in ("consequence",)}
        safe_quests[qid] = safe_q

    safe_config = {k: v for k, v in GAME_CONFIG.items() if k != "final_quest_rubric"}

    return JSONResponse({
        "game_config":     safe_config,
        "npcs":            safe_npcs,
        "quests":          safe_quests,
        "items":           ITEM_DATA,
        "kc_bank":         {k: {"topic_en": v["topic_en"], "difficulty": v["difficulty"]}
                            for k, v in KC_BANK.items()},
        "starting_items":  _get_starting_items(),
        "starting_quests": _get_starting_quests(),
        "unlocked_npcs":   _get_default_unlocked_npcs(),
    })


@app.post("/api/npc/chat")
async def npc_chat(req: ChatRequest):
    npc_id = req.npc_id
    npc = NPC_DATA.get(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail=f"NPC '{npc_id}' not found")

    if npc_id not in req.game_state.unlocked_npcs and npc["unlock_condition"] != "default":
        raise HTTPException(status_code=403, detail=f"NPC '{npc_id}' not yet unlocked")

    history = list(req.game_state.npc_chat_history.get(npc_id, []))
    history.append({"role": "user", "content": req.player_message})

    system = _build_npc_system_prompt(npc_id, req.game_state)

    return StreamingResponse(
        _sse_stream_npc(npc_id, history, system),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        },
    )


@app.post("/api/quest/complete")
async def quest_complete(req: QuestCompleteRequest):
    quest = QUEST_DATA.get(req.quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail=f"Quest '{req.quest_id}' not found")

    npc_id = req.npc_id or quest.get("required_npc")
    rewards = _apply_quest_rewards(npc_id, req.game_state) if npc_id else {
        "xp_gained": 0, "tokens_gained": 0, "items_gained": [],
        "badges_gained": [], "fragments_gained": [],
        "unlock_npcs": [], "unlock_quests": [],
    }

    if req.outcome == "smart_negotiation":
        rewards["xp_gained"]     = rewards.get("xp_gained", 0) + 30
        rewards["tokens_gained"] = rewards.get("tokens_gained", 0) + 15

    consequence_triggered = (req.outcome == "consequence_triggered")
    consequence_data: Dict[str, Any] = {}
    if consequence_triggered and quest.get("consequence"):
        c = quest["consequence"]
        consequence_data = {
            "chain_stages_th":  c.get("chain_stages_th", []),
            "penalty_tokens":   c.get("penalty_tokens", 0),
            "allow_retry":      c.get("allow_retry", True),
            "retry_message_th": c.get("retry_message_th", ""),
        }
        rewards["tokens_gained"] = rewards.get("tokens_gained", 0) + c.get("penalty_tokens", 0)
        rewards["xp_gained"]     = rewards.get("xp_gained", 0) + c.get("penalty_xp", 0)

    if quest["type"] == "final" and req.outcome == "success":
        final_badge = "pattern_detective"
        if final_badge not in rewards.get("badges_gained", []):
            rewards.setdefault("badges_gained", []).append(final_badge)
        final_artifact = "investigation_report_artifact"
        if final_artifact not in rewards.get("items_gained", []):
            rewards.setdefault("items_gained", []).append(final_artifact)

    return JSONResponse({
        "quest_id":              req.quest_id,
        "outcome":               req.outcome,
        "rewards":               rewards,
        "consequence_triggered": consequence_triggered,
        "consequence_data":      consequence_data,
        "xp_gained":             rewards.get("xp_gained", 0),
        "tokens_gained":         rewards.get("tokens_gained", 0),
        "items_gained":          rewards.get("items_gained", []),
        "badges_gained":         rewards.get("badges_gained", []),
        "fragments_gained":      rewards.get("fragments_gained", []),
        "unlock_npcs":           rewards.get("unlock_npcs", []),
        "unlock_quests":         rewards.get("unlock_quests", []),
        "items_detail":          [ITEM_DATA.get(i, {}) for i in rewards.get("items_gained", [])],
    })


@app.post("/api/npc/mentor-unlock")
async def mentor_unlock(req: MentorCheckRequest):
    npc = NPC_DATA.get(req.npc_id)
    if not npc or not npc.get("is_mentor"):
        raise HTTPException(status_code=400, detail=f"NPC '{req.npc_id}' is not a mentor")

    current_level = req.game_state.mentor_levels.get(req.npc_id, 0)
    next_level    = current_level + 1
    levels        = npc.get("mentor_levels", [])

    if next_level > len(levels):
        return JSONResponse({
            "qualified":  False,
            "reason_th":  "ปลดล็อกครบทุกระดับแล้ว",
            "new_level":  current_level,
        })

    target = next((lv for lv in levels if lv["level"] == next_level), None)
    if not target:
        return JSONResponse({"qualified": False, "new_level": current_level})

    eval_prompt = (
        f"You are evaluating whether a student's message qualifies to unlock "
        f"Mentor Level {next_level} for NPC '{npc['display_name']}' "
        f"in an educational math game about Geometric Sequences.\n\n"
        f"UNLOCK CRITERIA: {target['unlock_criteria_en']}\n\n"
        f"STUDENT'S LATEST MESSAGE:\n\"{req.last_message}\"\n\n"
        f"COMPLETED QUESTS: {req.game_state.completed_quests}\n\n"
        "NOTE: The student's message may contain LaTeX notation (e.g. $r=2$, $a_5=1600$) — "
        "treat this as valid math input when evaluating.\n\n"
        "Reply ONLY with valid JSON (no markdown, no extra text):\n"
        "{\"qualified\": true|false, \"reason_en\": \"brief reason (max 20 words)\"}"
    )

    resp = await _call_llm(
        system=CONTENT_MODERATION,
        messages=[{"role": "user", "content": eval_prompt}],
        max_tokens=80,
        temperature=TEMPERATURE_EVAL,
    )
    text   = _extract_llm_text(resp)
    result = _parse_json_response(text, {"qualified": False})

    if result.get("qualified"):
        reward_data = _apply_mentor_level_reward(req.npc_id, next_level)
        return JSONResponse({
            "qualified":     True,
            "new_level":     next_level,
            "secret_th":     target["secret_th"],
            "rewards":       reward_data,
            "xp_gained":     reward_data["xp_gained"],
            "tokens_gained": reward_data["tokens_gained"],
            "items_gained":  reward_data["items_gained"],
        })

    return JSONResponse({
        "qualified":  False,
        "reason_th":  "ยังไม่ถึงเกณฑ์ ลองถามให้ลึกกว่านี้",
        "new_level":  current_level,
    })


@app.post("/api/knowledge-check/generate")
async def kc_generate(req: KCGenerateRequest):
    kc = KC_BANK.get(req.quest_id)
    if not kc:
        return JSONResponse({
            "question": "ทบทวนสูตรก่อนเริ่ม Quest ได้เลย",
            "has_kc":   False,
            "quest_id": req.quest_id,
        })

    gen_prompt = (
        f"Generate ONE knowledge-check question in Thai for a Thai high school student.\n"
        f"Topic: {kc['topic_en']}\n"
        f"Formula: {kc['formula_en']}\n"
        f"Difficulty: {kc['difficulty']} (Bloom's level: {kc['bloom_level']})\n"
        f"Game context: {GAME_CONFIG['world_name']} — {kc.get('context_th','')}\n\n"
        "REQUIREMENTS:\n"
        "1. Use a concrete Gacha/Pull cost scenario with specific numbers.\n"
        "2. Question must require APPLYING the formula — not just reciting it.\n"
        "3. Keep it to 2-3 sentences in Thai. Do NOT include the answer.\n"
        "4. Make the numbers different from any sample in the KC_BANK.\n"
        "5. ALL mathematical expressions MUST use LaTeX: $r$, $a_1$, $a_n$, $n$, $r^{n-1}$.\n"
        "   Example: 'ถ้า Pull Sequence มี $a_1 = 50$ บาท และ $r = 3$ จงหา $a_4$'\n\n"
        "Reply ONLY with the question text in Thai. No JSON. No preamble."
    )

    resp = await _call_llm(
        system=CONTENT_MODERATION,
        messages=[{"role": "user", "content": gen_prompt}],
        max_tokens=MAX_TOKENS_KC,
        temperature=TEMPERATURE_KC,
    )
    question = _extract_llm_text(resp).strip() or kc["sample_th"]
    return JSONResponse({"question": question, "has_kc": True, "quest_id": req.quest_id})


@app.post("/api/knowledge-check/evaluate")
async def kc_evaluate(req: KCEvaluateRequest):
    kc = KC_BANK.get(req.quest_id, {})
    eval_prompt = (
        f"Evaluate this Thai high school student's answer to a knowledge-check question.\n\n"
        f"MATH TOPIC: {kc.get('topic_en', GAME_CONFIG['math_topic'])}\n"
        f"FORMULA: {kc.get('formula_en', GAME_CONFIG['math_formula'])}\n\n"
        f"QUESTION:\n{req.question_text}\n\n"
        f"STUDENT ANSWER (may be LaTeX from math-field, e.g. r=2, a_5=1600):\n{req.student_answer}\n\n"
        "RUBRIC:\n"
        "  1.0: Correct formula, correct r identified, correct final aₙ.\n"
        "  0.7: Correct approach but one minor arithmetic error.\n"
        "  0.5: Correct formula cited but calculation incomplete or partially wrong.\n"
        "  0.0: Wrong formula, off-topic, or blank.\n\n"
        "FEEDBACK FORMATTING: Write feedback_th in Thai. "
        "Use $...$ for ALL math in feedback, e.g. '$a_5 = 100 \\times 2^4 = 1600$ บาท'.\n\n"
        "Reply ONLY with JSON (no markdown fences):\n"
        "{\"score\": 0.0-1.0, \"passed\": true|false, "
        "\"feedback_th\": \"brief Thai feedback 1-2 sentences with LaTeX math\"}"
    )

    resp = await _call_llm(
        system=CONTENT_MODERATION,
        messages=[{"role": "user", "content": eval_prompt}],
        max_tokens=MAX_TOKENS_EVAL,
        temperature=TEMPERATURE_EVAL,
    )
    text   = _extract_llm_text(resp)
    result = _parse_json_response(text, {
        "score": 0.0, "passed": False, "feedback_th": "กรุณาลองอีกครั้ง"
    })
    result.setdefault("passed",      result.get("score", 0.0) >= 0.6)
    result.setdefault("feedback_th", "")
    return JSONResponse(result)


@app.post("/api/final-quest/evaluate")
async def final_quest_evaluate(req: FinalQuestEvalRequest):
    quest = QUEST_DATA.get(req.quest_id)
    if not quest or quest["type"] != "final":
        raise HTTPException(status_code=400, detail=f"'{req.quest_id}' is not a final quest")

    rubric    = GAME_CONFIG["final_quest_rubric"]
    dims      = rubric["dimensions"]
    threshold = rubric["pass_threshold"]

    dim_criteria = "\n".join(
        f"  [{d['id']}] weight={d['weight']:.0%}: {d['criteria_en']}"
        for d in dims
    )

    eval_prompt = (
        f"You are an educational AI evaluator for a Thai high school math game.\n"
        f"Game: {GAME_CONFIG['game_title']} | Topic: {GAME_CONFIG['math_topic']}\n"
        f"Formula: {GAME_CONFIG['math_formula']}\n\n"
        f"FINAL QUEST TASK:\n{quest.get('task_prompt_th','')}\n\n"
        f"STUDENT SUBMISSION:\n{req.student_submission}\n\n"
        f"EVALUATION RUBRIC (score each dimension 0.0-1.0):\n{dim_criteria}\n\n"
        f"PASS THRESHOLD: {threshold} weighted average\n\n"
        "IMPORTANT: There is NO single 'correct' conclusion about whether the system "
        "is fraudulent or players are uninformed. BOTH are valid conclusions IF backed "
        "by calculated numbers referencing r and aₙ. Evaluate the REASONING PROCESS "
        "and mathematical evidence, not the conclusion itself.\n\n"
        "INSTRUCTIONS:\n"
        "1. Score each dimension 0.0-1.0 based on its criteria.\n"
        "2. Compute overall_score = weighted average.\n"
        "3. Write feedback_th: 2-3 constructive sentences in Thai.\n"
        "4. Write hint_th: 1 actionable sentence in Thai if NOT passed; empty string if passed.\n"
        "5. MATH FORMATTING: Use $...$ for ALL inline math in feedback_th and hint_th.\n"
        "   Example: 'คุณระบุ $r = 2$ ถูกต้อง แต่ยังขาดการคำนวณ $a_n$ ประกอบ'\n\n"
        "Reply ONLY with JSON (no markdown fences, no preamble):\n"
        "{\n"
        "  \"dimension_scores\": {\n"
        "    " + ", ".join(f'"{d["id"]}":0.0' for d in dims) + "\n"
        "  },\n"
        "  \"overall_score\": 0.0,\n"
        "  \"passed\": false,\n"
        "  \"feedback_th\": \"\",\n"
        "  \"hint_th\": \"\"\n"
        "}"
    )

    resp = await _call_llm(
        system=CONTENT_MODERATION,
        messages=[{"role": "user", "content": eval_prompt}],
        max_tokens=MAX_TOKENS_EVAL,
        temperature=TEMPERATURE_EVAL,
    )
    text   = _extract_llm_text(resp)
    result = _parse_json_response(text, {
        "dimension_scores": {d["id"]: 0.0 for d in dims},
        "overall_score":    0.0,
        "passed":           False,
        "feedback_th":      "ระบบประเมินขัดข้อง กรุณาส่งอีกครั้ง",
        "hint_th":          "",
    })

    dim_scores = result.get("dimension_scores", {})
    computed   = sum(dim_scores.get(d["id"], 0.0) * d["weight"] for d in dims)
    result["overall_score"] = round(computed, 3)
    result["passed"]        = computed >= threshold

    if result["passed"]:
        result["rewards"] = {
            "badges_gained": ["pattern_detective"],
            "items_gained":  ["investigation_report_artifact"],
            "xp_gained":     80,
            "tokens_gained": 40,
        }
    else:
        result["rewards"] = {}

    return JSONResponse(result)


@app.post("/api/consequence/check")
async def consequence_check(req: ConsequenceCheckRequest):
    quest = QUEST_DATA.get(req.quest_id)
    if not quest or not quest.get("consequence"):
        return JSONResponse({"has_consequence": False})

    c = quest["consequence"]
    return JSONResponse({
        "has_consequence":  True,
        "chain_stages_th":  c.get("chain_stages_th", []),
        "penalty_tokens":   c.get("penalty_tokens", 0),
        "allow_retry":      c.get("allow_retry", True),
        "retry_message_th": c.get("retry_message_th", ""),
        "lesson_th": (
            f"💡 บทเรียน: {GAME_CONFIG['math_formula']} "
            "ช่วยให้เห็น 'ค่า r จริง' ก่อนเชื่อสถิติใดๆ "
            "— ตรวจสอบจาก Pull Log จริงเสมอ"
        ),
    })


@app.post("/api/npc/check-available")
async def npc_check_available(game_state: GameState):
    newly_available = []
    for npc_id, npc in NPC_DATA.items():
        if npc_id in game_state.unlocked_npcs:
            continue
        if _check_npc_unlockable(npc_id, game_state):
            newly_available.append({
                "id":           npc_id,
                "display_name": npc["display_name"],
                "avatar_emoji": npc["avatar_emoji"],
                "title_th":     npc["title_th"],
                "archetype":    npc["archetype"],
                "location_th":  npc["location_th"],
            })
    return JSONResponse({"newly_available": newly_available})


@app.post("/api/hint/buy")
async def buy_hint(quest_id: str, game_state: GameState):
    cost = GAME_CONFIG["token_hint_cost"]
    if game_state.player.tokens < cost:
        return JSONResponse({
            "success":    False,
            "message_th": f"ไม่มี {GAME_CONFIG['token_name']} เพียงพอ (ต้องการ {cost} {GAME_CONFIG['token_symbol']})",
        })

    kc = KC_BANK.get(quest_id, {})
    hint_prompt = (
        f"Generate a helpful Socratic hint in Thai for a student who is stuck on:\n"
        f"Topic: {kc.get('topic_en', GAME_CONFIG['math_topic'])}\n"
        f"Formula: {kc.get('formula_en', GAME_CONFIG['math_formula'])}\n"
        f"Context: {GAME_CONFIG['world_name']} — Gacha Pull costs\n\n"
        "Rules:\n"
        "1. Do NOT give the numerical answer.\n"
        "2. Guide with a leading question or a partial step.\n"
        "3. Keep it to 1-2 sentences in Thai.\n"
        "4. Start with '💡 Hint:'\n"
        "5. Use $...$ for ALL math variables: $r$, $a_1$, $a_n$, $n$, $r^{n-1}$.\n\n"
        "Reply ONLY with the hint text."
    )

    resp = await _call_llm(
        system=CONTENT_MODERATION,
        messages=[{"role": "user", "content": hint_prompt}],
        max_tokens=120,
        temperature=0.5,
    )
    hint = _extract_llm_text(resp).strip() or "💡 Hint: ลองดูที่ $r$ ก่อน — หาได้โดยหาร $a_2 \\div a_1$"

    return JSONResponse({
        "success":       True,
        "hint_th":       hint,
        "tokens_spent":  cost,
        "tokens_remain": game_state.player.tokens - cost,
    })


@app.get("/api/item/{item_id}")
async def get_item(item_id: str):
    item = ITEM_DATA.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
    return JSONResponse(item)


@app.get("/api/health")
async def health():
    return JSONResponse({
        "status":    "ok",
        "game":      GAME_CONFIG["game_title"],
        "model":     API_MODEL,
        "api_ready": bool(API_KEY),
    })


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 10 — APP STARTUP  (DO NOT MODIFY)
# ══════════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info(f"🎲  {GAME_CONFIG['game_title']} | นครธนา Universe v2.0")
    logger.info(f"    World:  {GAME_CONFIG['world_name']}  ({GAME_CONFIG.get('world_year','')})")
    logger.info(f"    Role:   {GAME_CONFIG['player_role']}")
    logger.info(f"    Topic:  {GAME_CONFIG['math_topic']}")
    logger.info(f"    NPCs:   {len(NPC_DATA)} | Quests: {len(QUEST_DATA)} | Items: {len(ITEM_DATA)}")
    logger.info(f"    Model:  {API_MODEL}")
    logger.info(f"    URL:    {API_URL}")
    if not API_KEY:
        logger.warning("⚠️  API_KEY not set in .env — all LLM calls will fail!")
    else:
        logger.info(f"    Key:    ...{API_KEY[-6:]}")
    logger.info("=" * 60)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run(app, host="0.0.0.0", port=port)
