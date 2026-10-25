#!/usr/bin/env python3
"""Upload Compilations C1 and C2 as private to YouTube, push localizations/captions,
update compilations.json, and re-run gen_insights.py (COMPILATION_PLAYBOOK.md §3.5-3.6).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path("/Users/miguelrodriguez/projects/agentic-fleet-hub/tech-shorts")
MUSIC_VIDEO_TOOL = Path("/Users/miguelrodriguez/projects/music-video-tool")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(MUSIC_VIDEO_TOOL))

import pipeline as P
from googleapiclient.http import MediaFileUpload
from youtube_uploader import (
    channel_token_path,
    get_authenticated_service,
    upload_video,
)

C1_DIR = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-24-compilation-c1-ai-will-do-the-work-vol-2")
C2_DIR = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-25-compilation-c2-the-attack-surface-in-your-house")

C1_TITLE = "If AI Does the Work, Who Gets Paid Next? (Full Compilation · Vol. 2)"
C1_DESC = """Every screen in the building is still glowing, and the work is still getting done — only the chairs are empty. Across six research deep dives (~36 minutes), we follow the economic data on what happens when exponential AI models collide with a linear labor market: productivity bottlenecks, Anthropic's 2026–2030 wage-divergence scenarios, how language models learn the grammar of career moves, the $10.3T off-balance-sheet debt Catch-22, the Jevons Paradox of automation, and the White-Collar Bypass erasing entry-level jobs.

Chapters:
00:00 Intro — If AI Does the Work, Who Gets Paid Next?
00:20 1. The AI Bottleneck: Exponential Models, Linear World
08:39 2. How AI Reshapes Jobs, Growth & Unemployment (Anthropic 2026–2030)
12:59 3. The Grammar of Work: How LLMs Learn Career Moves
19:48 4. The Catch-22 of the AI Economy
24:53 5. Will AI Create Jobs or Destroy Them? The Jevons Paradox
30:47 6. The White-Collar Bypass: How AI Is Erasing Entry-Level Jobs

Original Deep Dives Included in This Compilation:
1. The AI Bottleneck: Exponential Models, Linear World — https://youtu.be/7UPyRA9cBtE
2. How AI Reshapes Jobs, Growth & Unemployment: Anthropic's 2026–2030 Economic Scenarios — https://youtu.be/lChiYc1A4B8
3. The Grammar of Work: How LLMs Learn Career Moves — https://youtu.be/Vritr444eKs
4. Can the AI Boom Continue Without Leading to a Massive Increase in Inequality? — https://youtu.be/jxi-GUpdhYI
5. The Jevons Paradox and the Future of AI Employment — https://youtu.be/Miw8TeG3RFI
6. The White-Collar Bypass: How AI Is Erasing Entry-Level Jobs — https://youtu.be/JFhLTSY7Pxw

#AIEconomy #FutureOfWork #Automation #Anthropic #JevonsParadox #TechCompilation"""

C1_LOCS = {
    "de": {
        "title": "Wenn KI die Arbeit macht, wer wird dann bezahlt? (Komplette Kompilation · Teil 2)",
        "description": "In sechs tiefgehenden Untersuchungen (~36 Minuten) folgen wir den Wirtschaftsdaten zur Frage, was passiert, wenn exponentielle KI-Modelle auf einen linearen Arbeitsmarkt treffen.\n\nKapitel:\n00:00 Intro — Wenn KI die Arbeit macht, wer wird dann bezahlt?\n00:20 1. Der KI-Engpass: Exponentielle Modelle, lineare Welt\n08:39 2. Wie KI Jobs, Wachstum & Arbeitslosigkeit verändert (Anthropic 2026–2030)\n12:59 3. Die Grammatik der Arbeit: Wie Sprachmodelle Karrierewege lernen\n19:48 4. Die Zwickmühle der KI-Ökonomie\n24:53 5. Schafft KI Jobs oder vernichtet sie diese? Das Jevons-Paradoxon\n30:47 6. Der White-Collar-Bypass: Wie KI Einstiegsjobs auslöscht",
        "srt": str(C1_DIR / "ai-will-do-the-work-vol-2_de.srt"),
    },
    "fr": {
        "title": "Si l'IA fait le travail, qui est payé ensuite ? (Compilation complète · Vol. 2)",
        "description": "À travers six enquêtes approfondies (~36 minutes), nous suivons les données économiques sur ce qui se passe lorsque des modèles d'IA exponentiels se heurtent à un marché du travail linéaire.\n\nChapitres :\n00:00 Intro — Si l'IA fait le travail, qui est payé ensuite ?\n00:20 1. Le goulet d'étranglement de l'IA : modèles exponentiels, monde linéaire\n08:39 2. Comment l'IA remodèle l'emploi et la croissance (Anthropic 2026–2030)\n12:59 3. La grammaire du travail : comment les LLM apprennent les trajectoires de carrière\n19:48 4. Le dilemme de l'économie de l'IA\n24:53 5. L'IA va-t-elle créer ou détruire des emplois ? Le paradoxe de Jevons\n30:47 6. Le contournement des cols blancs : comment l'IA efface les emplois débutants",
        "srt": str(C1_DIR / "ai-will-do-the-work-vol-2_fr.srt"),
    },
    "ja": {
        "title": "AIが仕事をするなら、次に報酬を得るのは誰か？（完全総集編・Vol. 2）",
        "description": "6つの調査レポート（約36分）を通じて、指数関数的なAIモデルが線形な労働市場と衝突するときに何が起きるのかを経済データで追います。\n\nチャプター:\n00:00 イントロ — AIが仕事をするなら、次に報酬を得るのは誰か？\n00:20 1. AIのボトルネック：指数関数的なモデルと線形な世界\n08:39 2. AIが雇用・成長・失業をどう変えるか（Anthropic 2026–2030）\n12:59 3. 仕事の文法：大規模言語モデルはどうキャリアを学習するか\n19:48 4. AI経済のジレンマ\n24:53 5. AIは雇用を生むのか奪うのか？ジェヴォンズのパラドックス\n30:47 6. ホワイトカラー・バイパス：新卒・初級職を消すAI",
        "srt": str(C1_DIR / "ai-will-do-the-work-vol-2_ja.srt"),
    },
    "en": {
        "title": C1_TITLE,
        "description": C1_DESC,
        "srt": str(C1_DIR / "ai-will-do-the-work-vol-2_en.srt"),
    },
}

C2_TITLE = "What Is Running on Your Living Room Network? The Attack Surface in Your House"
C2_DESC = """At 3 a.m., every screen in your house is dark — but the network never sleeps. Across seven cybersecurity and AI threat investigations (~38 minutes), we trace how the offensive frontier moved from nation-state labs into everyday infrastructure: Japan AISI's live hacking evaluation of US vs. Chinese models, stolen API keys fueling the criminal supply chain, a two-student automated zero-day factory, the IoT convenience paradox, self-replicating AI worms targeting smart TVs, household shadow datacenters, and why AI agents need zero-trust authority.

Chapters:
00:00 Intro — What Is Running on Your Living Room Network?
00:20 1. Japan Tested US vs Chinese AI on Real Hacking
05:05 2. Secure Your API Keys: Stolen Keys as the AI Underworld's Free Weapon
09:53 3. Two Students Built an AI Zero-Day Factory
13:32 4. The Convenience Paradox: Why the Internet of Things is Melting
18:46 5. The Convergence Point: When AI Worms Self-Replicate on Smart TVs
23:54 6. The Shadow Datacenter: Why AI Worms Are Targeting Your Smart TV
29:54 7. Models as Insider Risks: Why AI Agents Need Zero-Trust Authority

Original Deep Dives Included in This Compilation:
1. Can AI Build Autonomous Cyber Exploits? Japan AISI Tested US vs Chinese Frontier Models on Real Hacking — https://youtu.be/ECuneH0hPcg
2. Secure Your API Keys: How Stolen Keys Became the AI Underworld's Free Weapon — https://youtu.be/KbxsK1LlVSw
3. Two Students Built an AI Zero-Day Factory: Inside China's Automated Cyber Espionage Pipeline — https://youtu.be/n0J3a4-1rmY
4. The Convenience Paradox: Why the Internet of Things is Melting — https://youtu.be/D-LV9YJN2ZM
5. The Convergence Point: When AI Worms Self-Replicate on Smart TVs — https://youtu.be/GLLa6t_MQuA
6. The Shadow Datacenter: Why AI Worms Are Targeting Your Smart TV — https://youtu.be/lZ_LLtp8Ulo
7. Models as Insider Risks: Why AI Agents Need Zero-Trust Authority — https://youtu.be/cRgmoG-XqkQ

#AISecurity #Cybersecurity #SmartHome #ZeroTrust #AIThreats #TechCompilation"""

C2_LOCS = {
    "de": {
        "title": "Was läuft in Ihrem Heimnetzwerk? Die Angriffsfläche in Ihrem Haus (Kompilation)",
        "description": "Um drei Uhr morgens ist jeder Bildschirm in Ihrem Haus dunkel — aber das Netzwerk schläft nie. In sieben Untersuchungen (~38 Minuten) zeigen wir, wie sich die Cyber-Angriffsfront von Geheimdienstlaboren bis ins eigene Wohnzimmer verschoben hat.\n\nKapitel:\n00:00 Intro — Was läuft in Ihrem Heimnetzwerk?\n00:20 1. Japan testete US- gegen chinesische KI bei echtem Hacking\n05:05 2. Sichern Sie Ihre API-Schlüssel: Gestohlene Keys als Waffe\n09:53 3. Zwei Studenten bauten eine KI-Zero-Day-Fabrik\n13:32 4. Das Komfort-Paradoxon: Warum das Internet der Dinge schmilzt\n18:46 5. Der Konvergenzpunkt: Wenn KI-Würmer sich auf Smart-TVs selbst replizieren\n23:54 6. Das Schatten-Rechenzentrum: Warum KI-Würmer Ihren Smart-TV ins Visier nehmen\n29:54 7. Modelle als Insider-Risiko: Warum KI-Agenten Zero-Trust brauchen",
        "srt": str(C2_DIR / "the-attack-surface-in-your-house_de.srt"),
    },
    "fr": {
        "title": "Que tourne-t-il sur votre réseau domestique ? La surface d'attaque chez vous",
        "description": "À trois heures du matin, chaque écran de votre maison est éteint — mais le réseau ne dort jamais. À travers sept enquêtes (~38 minutes), nous retraçons comment le front offensif s'est déplacé jusque dans votre salon.\n\nChapitres :\n00:00 Intro — Que tourne-t-il sur votre réseau domestique ?\n00:20 1. Le Japon a testé les IA américaines et chinoises sur du vrai piratage\n05:05 2. Sécurisez vos clés API : l'arme gratuite de la cybercriminalité\n09:53 3. Deux étudiants ont bâti une usine d'exploits zero-day par IA\n13:32 4. Le paradoxe du confort : pourquoi l'Internet des objets fond\n18:46 5. Le point de convergence : quand des vers d'IA se répliquent sur les Smart TV\n23:54 6. Le datacenter fantôme : pourquoi les vers d'IA ciblent votre téléviseur\n29:54 7. Les modèles comme menaces internes : pourquoi les agents IA ont besoin du Zero-Trust",
        "srt": str(C2_DIR / "the-attack-surface-in-your-house_fr.srt"),
    },
    "ja": {
        "title": "自宅のネットワークで何が動いているのか？家の中に潜むAI攻撃対象領域（完全総集編）",
        "description": "午前3時、家の中のすべての画面は暗くなっていますが、ネットワークは決して眠りません。7つの調査（約38分）を通じて、サイバー攻撃の最前線がいかにして家庭のスマートテレビやIoT機器へと入り込んだのかを追跡します。\n\nチャプター:\n00:00 イントロ — 自宅のネットワークで何が動いているのか？\n00:20 1. 日本のAISIが米国製・中国製AIの実戦ハッキング能力を検証\n05:05 2. APIキーを守れ：盗まれたキーがAI犯罪の無料兵器になる仕組み\n09:53 3. 大学生2人が構築したAIゼロデイ工場\n13:32 4. 利便性のパラドックス：なぜIoTは崩壊しつつあるのか\n18:46 5. 収束点：AIワームがスマートテレビ上で自己増殖するとき\n23:54 6. 影のデータセンター：なぜAIワームはスマートテレビを狙うのか\n29:54 7. インサイダー脅威としてのAIモデル：なぜゼロトラスト権限が必要なのか",
        "srt": str(C2_DIR / "the-attack-surface-in-your-house_ja.srt"),
    },
    "en": {
        "title": C2_TITLE,
        "description": C2_DESC,
        "srt": str(C2_DIR / "the-attack-surface-in-your-house_en.srt"),
    },
}


def make_thumb(intro_mp4: Path, out_jpg: Path) -> Path:
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", "15", "-i", str(intro_mp4), "-frames:v", "1", "-q:v", "2", str(out_jpg)
    ], check=True)
    return out_jpg


def upload_one(label: str, comp_dir: Path, title: str, desc: str, tags: list[str], locs: dict) -> str:
    video_path = comp_dir / "final_comp.mp4"
    thumb_path = make_thumb(comp_dir / "intro.mp4", comp_dir / "thumbnail.jpg")
    print(f"[{label}] Uploading {video_path} as private...", flush=True)
    res = upload_video(
        video_path=str(video_path),
        title=title,
        description=desc,
        privacy_status="private",
        tags=tags,
        category_id="28",
        channel="main",
    )
    url = res.get("url", "")
    vid = res.get("video_id") or res.get("id") or P.youtube_video_id(url)
    print(f"[{label}] Uploaded -> {url} (id={vid})", flush=True)

    svc = get_authenticated_service(token_path=channel_token_path("main"))
    try:
        svc.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(thumb_path))).execute()
        print(f"[{label}] Custom thumbnail set.", flush=True)
    except Exception as e:
        print(f"[{label}] Thumbnail warning: {e}", flush=True)

    P.push_localizations(svc, vid, {"youtube": {"localizations": locs}})
    return vid


if __name__ == "__main__":
    which = sys.argv[1:] or ["C1", "C2"]
    results = {}
    if "C1" in which:
        results["C1"] = upload_one(
            "C1", C1_DIR, C1_TITLE, C1_DESC,
            ["AI economy", "future of work", "AI jobs", "Anthropic", "Jevons paradox", "automation", "white collar jobs"],
            C1_LOCS,
        )
    if "C2" in which:
        results["C2"] = upload_one(
            "C2", C2_DIR, C2_TITLE, C2_DESC,
            ["AI cybersecurity", "smart TV hacking", "API key security", "IoT security", "zero trust AI", "AI worms"],
            C2_LOCS,
        )
    print("UPLOAD_RESULTS_JSON:" + json.dumps(results), flush=True)
