#!/usr/bin/env python3
"""
Coercion Files — Master Forensic Launch Series (Days 1-7).

Wipes old generic scripts and generates 100% High-CPM, High-Retention (>70%),
Forensic Human-Feel Case Study scripts.

Structure:
  Beat 1: In Medias Res Hook (0-3s pattern interrupt with concrete numbers)
  Beat 2: Psychological Exploit Mechanism (3-15s brain trap)
  Beat 3: Forensic Real Case Breakdown (15-38s tangible evidence)
  Beat 4: Tactical Immunity Shield + Loop CTA (38-55s)
"""

import json
from pathlib import Path

OUT = Path(__file__).parent
OUT.mkdir(parents=True, exist_ok=True)

CTA = "Follow Coercion Files for documented case files that protect your mind."

SCRIPTS = [
    {
        "day": 1,
        "pillar": "con_artists",
        "pillar_name": "Con Artists & Scam Psychology",
        "hook_style": "forensic_case",
        "title": "How a 3-Word Text Stole $420,000 | Scam Anatomy",
        "hook": "A 3-word text stole $420,000.",
        "visuals_mood": "intense",
        "search_term": "bank fraud scam",
        "tags": ["social engineering", "wire fraud", "scam psychology", "cyber security",
                 "bank fraud alert", "psychology facts", "con artists", "fraud prevention"],
        "key_points": "• The 3-word trigger causing amygdala hijack\n• How scammers simulate bank security\n• 1 golden rule to protect your account",
        "scenes": [
            {
                "caption": "In 2024, an American surgeon wired $420,000 in under eight minutes. He was not stupid — his brain was hijacked.",
                "visual": "hospital corridor dark night",
                "emotion": "intense"
            },
            {
                "caption": "It started with a fake bank alert: 'Fraud detected. Call now.' Just three words designed to trigger an immediate fear spike.",
                "visual": "smartphone notification screen dark",
                "emotion": "chilling"
            },
            {
                "caption": "When he called, a calm voice impersonated his fraud department, claiming his account was compromised from an overseas IP.",
                "visual": "call center dark silhouette",
                "emotion": "mysterious"
            },
            {
                "caption": "Neuroscientists call this the amygdala hijack: manufactured urgency shuts down analytical risk evaluation in seconds.",
                "visual": "abstract neural brain glow dark",
                "emotion": "dark"
            },
            {
                "caption": "They walked him through moving funds to a 'safe federal vault' — which was an offshore crypto wallet.",
                "visual": "bank transfer loading screen dark",
                "emotion": "intense"
            },
            {
                "caption": "Your defense: banks NEVER ask you to wire money to protect it. Hang up, pause, and call the number on your card. " + CTA,
                "visual": "credit card security chip macro dark",
                "emotion": "revelatory"
            }
        ]
    },
    {
        "day": 2,
        "pillar": "coercive_control",
        "pillar_name": "Coercive Control Awareness",
        "hook_style": "workplace_redflag",
        "title": "Quiet Firing: 3 Signs Your Boss Wants You Out",
        "hook": "Quiet firing: 3 signs you're being pushed out.",
        "visuals_mood": "intense",
        "search_term": "quiet firing signs",
        "tags": ["quiet firing", "workplace psychology", "toxic boss", "career advice",
                 "corporate mind games", "psychology facts", "power dynamics", "constructive dismissal"],
        "key_points": "• The 3 classic signs of quiet firing\n• Why corporations use constructive dismissal\n• How to build an indisputable paper trail",
        "scenes": [
            {
                "caption": "If your boss does these three things in your weekly meetings, you are not being overlooked — you are being quietly managed out.",
                "visual": "modern dark office empty desk",
                "emotion": "intense"
            },
            {
                "caption": "Sign one: information starvation. Key emails, client updates, and strategic meeting invites quietly stop reaching your inbox.",
                "visual": "laptop screen dark notification inbox",
                "emotion": "mysterious"
            },
            {
                "caption": "Sign two: shifting goalposts. Deliverables you executed perfectly are suddenly graded against vague, impossible metrics.",
                "visual": "red pen marking documents desk",
                "emotion": "dark"
            },
            {
                "caption": "Sign three: calendar isolation. Your 1-on-1s get repeatedly canceled, and high-visibility projects are reassigned to peers.",
                "visual": "calendar schedule meeting cancel screen",
                "emotion": "chilling"
            },
            {
                "caption": "Corporate psychologists call this constructive dismissal: they pressure you to quit so they avoid severance and unemployment claims.",
                "visual": "shadowed boardroom table empty",
                "emotion": "intense"
            },
            {
                "caption": "Your defense: document every assignment in writing, forward receipts to a personal drive, and never resign without consulting legal counsel. " + CTA,
                "visual": "document signature fountain pen dark",
                "emotion": "revelatory"
            }
        ]
    },
    {
        "day": 3,
        "pillar": "interrogation",
        "pillar_name": "Interrogation & Lie Detection",
        "hook_style": "interrogation_transcript",
        "title": "The 3-Second Silence FBI Interrogators Use",
        "hook": "FBI interrogators use a 3-second silence.",
        "visuals_mood": "dark",
        "search_term": "interrogation psychology lie detection",
        "tags": ["interrogation", "lie detection", "fbi profiling", "body language",
                 "statement analysis", "psychology facts", "true crime"],
        "key_points": "• Why strategic silence breaks deceptive alibis\n• Statement analysis: direct vs padded answers\n• How to stay immune to pressure questions",
        "scenes": [
            {
                "caption": "FBI behavioral interrogators know that suspects rarely break from aggressive shouting — they break from deliberate, unbroken silence.",
                "visual": "interrogation room mirror dark",
                "emotion": "intense"
            },
            {
                "caption": "When an agent maintains eye contact and stays silent for three full seconds after an answer, social anxiety spikes exponentially.",
                "visual": "close up intense eyes shadow",
                "emotion": "mysterious"
            },
            {
                "caption": "Behavioral scientists call this verbal leakage. The human brain interprets silence as suspicion and feels compelled to fill the void.",
                "visual": "tape recorder audio waveform dark",
                "emotion": "chilling"
            },
            {
                "caption": "Statement analysis proves: innocent people give short, direct answers. Deceptive suspects add unnecessary justifications and alibi padding.",
                "visual": "redacted police report desk",
                "emotion": "dark"
            },
            {
                "caption": "When questioned under pressure: answer in five words or less, and comfortably embrace the silence. Let the other person speak next. " + CTA,
                "visual": "shadowed figure walking dark corridor",
                "emotion": "revelatory"
            }
        ]
    },
    {
        "day": 4,
        "pillar": "con_artists",
        "pillar_name": "Con Artists & Scam Psychology",
        "hook_style": "forensic_case",
        "title": "The $100M Pig-Butchering Scam Decoded",
        "hook": "Inside the $100M pig-butchering scam.",
        "visuals_mood": "chilling",
        "search_term": "pig butchering scam explained",
        "tags": ["pig butchering scam", "crypto scam", "romance fraud", "social engineering",
                 "con artists", "fraud prevention", "financial scams"],
        "key_points": "• The 4 stages of the pig-butchering script\n• Why victims willingly wire money multiple times\n• The fake withdrawal fee trap",
        "scenes": [
            {
                "caption": "Federal fraud investigators call it pig-butchering: an industrial-scale con that stole over $3 billion from Americans last year.",
                "visual": "cyber data financial numbers screen dark",
                "emotion": "intense"
            },
            {
                "caption": "Stage one: the wrong number text. Polite, glamorous, and patient. They build rapport over weeks without mentioning money.",
                "visual": "luxury lifestyle blurred phone screen",
                "emotion": "mysterious"
            },
            {
                "caption": "Stage two: the fattening. They introduce an exclusive trading platform, letting you deposit $1,000 and successfully withdraw $1,200.",
                "visual": "crypto wallet trading graph green",
                "emotion": "dark"
            },
            {
                "caption": "Your brain registers proof and drops its guard. You invest your life savings — and the account suddenly shows $500,000 in fake profit.",
                "visual": "money transfer high numbers screen",
                "emotion": "chilling"
            },
            {
                "caption": "Stage three: the butchering. When you try to withdraw, they demand 20% in upfront 'tax fees'. The money was gone the second you wired it.",
                "visual": "account frozen warning red screen",
                "emotion": "intense"
            },
            {
                "caption": "Rule of thumb: never trade on a platform introduced by an online acquaintance. If you must pay to withdraw, it is 100% a scam. " + CTA,
                "visual": "hand locking dark safe vault",
                "emotion": "revelatory"
            }
        ]
    },
    {
        "day": 5,
        "pillar": "cults",
        "pillar_name": "Cult Psychology Decoded",
        "hook_style": "knowledge_gap",
        "title": "The 3 Questions Cult Leaders Forbid",
        "hook": "Cult leaders forbid these 3 questions.",
        "visuals_mood": "mysterious",
        "search_term": "how cults recruit brainwash",
        "tags": ["cult psychology", "nxivm", "brainwashing", "coercive control",
                 "high control groups", "psychology facts", "mind control"],
        "key_points": "• Why intelligence does not protect against cults\n• The 3 questions that trigger immediate defense\n• The difference between community and control",
        "scenes": [
            {
                "caption": "Doctors, tech executives, and professors join high-control groups every year. They do not join because they are naive — they join while in transition.",
                "visual": "crowd city rain night dark",
                "emotion": "intense"
            },
            {
                "caption": "Recruiters use love bombing to satisfy unfulfilled emotional needs, followed by gradual isolation from skeptical family members.",
                "visual": "hands circle candle ritual dark",
                "emotion": "chilling"
            },
            {
                "caption": "To test if an organization is a high-control group, ask question one: 'What happens if I publicly disagree with the founder?'",
                "visual": "shadowed speaker podium stage",
                "emotion": "mysterious"
            },
            {
                "caption": "Question two: 'Can I speak to ex-members who left in good standing?' Controlling groups will always attack ex-members' character.",
                "visual": "doorway silhouette leaving dark",
                "emotion": "dark"
            },
            {
                "caption": "Question three: 'Are financial records transparent to all members?' Healthy communities welcome questions; cults punish doubt as betrayal.",
                "visual": "financial ledger lock dark",
                "emotion": "chilling"
            },
            {
                "caption": "Healthy communities encourage independent critical thinking. Controlling groups demand absolute obedience. Recognize the difference. " + CTA,
                "visual": "open book illuminated candle light",
                "emotion": "revelatory"
            }
        ]
    },
    {
        "day": 6,
        "pillar": "coercive_control",
        "pillar_name": "Coercive Control Awareness",
        "hook_style": "workplace_redflag",
        "title": "The Salary Negotiation Trap Costing $30,000",
        "hook": "Never say this in a salary negotiation.",
        "visuals_mood": "intense",
        "search_term": "salary negotiation psychology power dynamics",
        "tags": ["salary negotiation", "career power dynamics", "corporate psychology",
                 "anchoring bias", "workplace tactics", "psychology facts"],
        "key_points": "• The 'first number' anchoring trap\n• Why salary ranges always work against you\n• The 1 sentence that forces employer concessions",
        "scenes": [
            {
                "caption": "In corporate hiring, saying this one sentence in your final interview can quietly cost you $30,000 over three years.",
                "visual": "skyscraper boardroom glass table dark",
                "emotion": "intense"
            },
            {
                "caption": "When a recruiter asks: 'What is your current compensation?', answering directly surrenders your entire psychological leverage.",
                "visual": "recruiter interview desk silhouette",
                "emotion": "mysterious"
            },
            {
                "caption": "Behavioral economists call this anchoring bias: the first number spoken sets the ceiling for all subsequent negotiation.",
                "visual": "financial chart anchor drop screen",
                "emotion": "dark"
            },
            {
                "caption": "If you give a range like '$110k to $130k', the employer's brain automatically anchors to the lowest possible figure.",
                "visual": "calculator contract fountain pen dark",
                "emotion": "chilling"
            },
            {
                "caption": "The counter-script: 'I am focused on the value I will bring here. Based on market benchmarks for this role, what is your budgeted range?'",
                "visual": "confident silhouette handshake dark",
                "emotion": "revelatory"
            },
            {
                "caption": "Force them to anchor first, then pause. The first person to speak after a salary offer almost always makes the concession. " + CTA,
                "visual": "city skyline night corporate tower",
                "emotion": "revelatory"
            }
        ]
    },
    {
        "day": 7,
        "pillar": "con_artists",
        "pillar_name": "Con Artists & Scam Psychology",
        "hook_style": "forensic_case",
        "title": "The AI Voice-Clone Scam Draining Bank Accounts",
        "hook": "They cloned her daughter's voice in 3 seconds.",
        "visuals_mood": "chilling",
        "search_term": "ai voice clone scam warning",
        "tags": ["ai voice scam", "deepfake audio", "social engineering", "scam alert",
                 "fraud prevention", "cyber security", "psychology facts"],
        "key_points": "• How 3 seconds of audio clones vocal cadence\n• The manufactured kidnap/accident script\n• The Family Safe Word defense protocol",
        "scenes": [
            {
                "caption": "In 2024, an American mother received a phone call. She heard her daughter sobbing, begging for help after a car accident.",
                "visual": "mother distressed phone call night",
                "emotion": "intense"
            },
            {
                "caption": "A menacing voice demanded an immediate $15,000 wire to avoid arrest. Her daughter was actually sitting safely in class.",
                "visual": "police sirens reflection dark window",
                "emotion": "chilling"
            },
            {
                "caption": "Generative voice cloning needs only three seconds of clean audio scraped from TikTok or Instagram to replicate vocal cadence perfectly.",
                "visual": "ai voice waveform frequency screen dark",
                "emotion": "mysterious"
            },
            {
                "caption": "The scam relies on overwhelming panic: terror shuts down logic, preventing victims from verifying the story before wiring money.",
                "visual": "smartphone trembling hand dark",
                "emotion": "dark"
            },
            {
                "caption": "Establish a private 'Family Safe Word' today. If you ever receive an emergency call demanding money, ask for that exact word.",
                "visual": "padlock security shield glowing dark",
                "emotion": "revelatory"
            },
            {
                "caption": "If they cannot provide it, hang up immediately and contact your family member on their known personal number. " + CTA,
                "visual": "phone disconnect screen dark",
                "emotion": "revelatory"
            }
        ]
    }
]


def build_description(script):
    return (
        f"{script['title']}. {script['hook']}\n"
        f"{script['pillar_name']}: Forensic case breakdown — how high-stakes deception hacks the brain, "
        f"and the exact tactical shields to protect yourself.\n\n"
        f"WHAT YOU'LL LEARN:\n{script['key_points']}\n\n"
        f"For educational and documentary purposes only. Learn to recognize the pattern before it traps you.\n\n"
        f"#psychology #truecrime #scams #{script['pillar']}"
    )


def to_pipeline_script(s):
    return {
        "title": s["title"],
        "hook": s["hook"],
        "scenes": [
            {
                "caption": sc["caption"],
                "caption_roman": sc["caption"],
                "visual": sc.get("visual", "dark city night cinematic"),
                "emotion": sc.get("emotion", s["visuals_mood"])
            }
            for sc in s["scenes"]
        ],
        "tags": s["tags"],
        "description": build_description(s),
        "key_points": s["key_points"],
        "pillar": s["pillar"],
        "pillar_name": s["pillar_name"],
        "hook_style": s["hook_style"],
        "source": "forensic_gold_standard_v2",
    }


def main():
    index = ["# 🛡️ Coercion Files — Master Forensic Launch Series (Days 1-7)",
             "_High-RPM ($14-$32) · 70%+ Retention Architecture · USA Target Audience_", "",
             "| Day | Pillar | Title | Hook (First 2s) | Search Keyword |",
             "|---|---|---|---|---|"]
    for s in SCRIPTS:
        p = to_pipeline_script(s)
        slug = f"day{s['day']:02d}_{s['pillar']}"
        (OUT / f"{slug}.json").write_text(json.dumps(p, indent=2, ensure_ascii=False), encoding="utf-8")
        index.append(f"| {s['day']} | {s['pillar_name']} | {s['title']} | \"{s['hook']}\" | `{s['search_term']}` |")

    index += ["", "## 🎬 7-Day Content Schedule", ""]
    for s in SCRIPTS:
        p = to_pipeline_script(s)
        index.append(f"---\n\n### Day {s['day']}: {s['title']}")
        index.append(f"**Pillar:** {s['pillar_name']}  ")
        index.append(f"**Hook (first 2s):** \"{s['hook']}\"  ")
        index.append("**Target RPM:** $14 - $32 (Finance / Legal / Cyber Tier)  ")
        index.append(f"**Word count:** ~{sum(len(sc['caption'].split()) for sc in s['scenes'])} words\n")
        index.append("**Scenes (Forensic Arc):**\n")
        for i, sc in enumerate(p["scenes"], 1):
            index.append(f"{i}. \"{sc['caption']}\"")
            index.append(f"   _B-Roll Query: `{sc['visual']}` | Emotion: `{sc['emotion']}`_\n")

    (OUT / "LAUNCH_WEEK_SCRIPTS.md").write_text("\n".join(index), encoding="utf-8")
    print(f"✅ Generated {len(SCRIPTS)} forensic launch scripts in {OUT}")
    for s in SCRIPTS:
        print(f"  Day {s['day']}: {s['title']}")


if __name__ == "__main__":
    main()
