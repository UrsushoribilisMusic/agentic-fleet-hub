#!/usr/bin/env python3
import json, shutil, sys
from pathlib import Path

# Add tech-shorts directory
sys.path.insert(0, "/Users/miguelrodriguez/projects/agentic-fleet-hub/tech-shorts")
from run_batch_localize import write_srt, ffdur, log, DOWNLOADS_STAGING
import localize as L

ASSET_DIR = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-18-the-sleep-deficit-why-ai-needs-to-dream")
FINAL_VIDEO = ASSET_DIR / "final_long.mp4"
SLUG = "the-sleep-deficit-why-ai-needs-to-dream"
STAGING_DIR = DOWNLOADS_STAGING / SLUG
STAGING_DIR.mkdir(parents=True, exist_ok=True)

with open(ASSET_DIR / "whisper_chunks.json") as f:
    chunks = json.load(f)

texts_en = [c["text"] for c in chunks]

texts_de = [
    "Warum kann sich die mächtigste KI der Welt nicht an den gestrigen Tag erinnern?",
    "Demis Hassabis argumentiert: Solange Modelle nicht wie das menschliche Gehirn schlafen und träumen lernen,",
    "bleibt künstliche allgemeine Intelligenz mathematisch in dauerhafter Amnesie gefangen.",
    "Stellen Sie sich vor, Sie interagieren mit dem fähigsten Assistenten der Erde.",
    "Er analysiert ein tausendseitiges technisches Handbuch in Sekunden, schreibt komplexen Code und übersetzt tote Sprachen.",
    "Doch sobald der Benutzer die Sitzung schließt, vergisst das System diese Interaktion vollständig.",
    "Wenn sich eine KI an einen Witz von vor einer Stunde erinnert, erzeugt das eine perfekte Illusion von Gedächtnis.",
    "In Wahrheit liest das System das gesamte Chat-Protokoll von oben bis unten im Schnelllauf durch, jedes Mal, wenn Sie Enter drücken.",
    "Ingenieure nennen diesen Raum das Kontextfenster. Tech-Konzerne bewerben ihre wachsenden Kontextfenster intensiv, aber egal wie groß sie werden,",
    "sie fungieren letztlich nur als vorübergehendes Konzeptpapier.",
    "Löscht man den Prompt, wird das Papier weggeworfen. Demis Hassabis, Chef von Google DeepMind, betonte kürzlich, dass heutige Architekturen",
    "wie Transformer zwar enorm leistungsfähig sind, ihnen aber entscheidende Bausteine für echte allgemeine Intelligenz fehlen.",
    "Bestehende Modelle tun sich schwer mit langfristigem logischem Denken und konsistenten Ausgaben.",
    "Vor allem fehlt ihnen jeder Mechanismus für kontinuierliches Lernen und den Aufbau dauerhafter Erinnerungen.",
    "Um eine aktive Intelligenz zu erschaffen, müssen Ingenieure das passive Konzeptpapier-Modell hinter sich lassen.",
    "Sie blicken auf das einzige System im Universum, das dieses Speicherproblem gelöst hat: das menschliche Gehirn.",
    "Jeden Tag wird das menschliche Gehirn von einer chaotischen Flut aus Sinneseindrücken, Gesprächen und neuen Erfahrungen überrollt.",
    "Das biologische Äquivalent des Kontextfensters ist der Hippocampus.",
    "Er fungiert als temporärer Zwischenspeicher, der flüchtige episodische Momente festhält, damit Sie den Alltag bewältigen können.",
    "Dieses Speichern geschieht nicht im Wachzustand. Während des Schlafs vollzieht das Gehirn ein Gedächtnis-Replay.",
    "Träume dienen als gewaltige Datenübertragungsphase. Das Gehirn integriert neues Wissen nahtlos und verlustfrei aus dem Zwischenspeicher",
    "in die Großhirnrinde und sichert es dauerhaft ab.",
    "Biologisch betrachtet funktioniert Schlaf wie ein präziser mechanischer Algorithmus.",
    "Er ist die unverzichtbare Datenverarbeitungsphase, die tägliche Einzelerfahrungen in kontinuierlich wachsende Intelligenz verwandelt.",
    "Das wirft eine offensichtliche technische Frage auf: Warum schreiben wir kein Skript, das die KI schlafen lässt und ihr Konzeptpapier",
    "auf eine dauerhafte Festplatte überträgt? Der Flaschenhals ist rein mathematischer Natur.",
    "Während der Inferenzphase sind die Parameter einer KI, ihre neuronalen Verbindungen, vollständig eingefroren.",
    "Informationen in ein größeres Kontextfenster zu schütten, verändert das neuronale Netz nicht.",
    "Neue Daten prallen ab und verfliegen. Permanentes Wissen erfordert das Abschalten und ein massives Nachtrainieren des gesamten Netzes.",
    "Dieses strukturelle Unvermögen, während der Ausführung adaptiv zu lernen, fesselt die KI an eine permanente Amnesie.",
    "Diese mathematische Hürde zu überwinden, ist das größte verbleibende Hindernis auf dem Weg zur AGI.",
    "Das eigentliche Ziel der KI-Forscher ist kontinuierliches Lernen.",
    "Dies erfordert eine elegante mathematische Lösung, mit der ein Modell direkt aus seiner spezifischen",
    "Umgebung im laufenden Betrieb lernt, ganz ohne Abschalten und Nachtrainieren.",
    "Wird dies gelöst, löst es einen gewaltigen Wandel aus. Passive Chatbots, die ständige Prompts brauchen, weichen aktiven Systemen, die",
    "über die Zeit hinweg tiefen, spezifischen Geschäftskontext für den Nutzer aufbauen.",
    "Wenn die Rechenkosten pro Inferenz sinken, erleben wir eine Explosion der Skalierung.",
    "Entwickler werden Tausende dieser aktiven Agenten im Hintergrund parallel für Suche, logisches Schließen und Bewertungen einsetzen.",
    "Aktuell sind viele Deep-Tech-Produkte bloße Behelfslösungen für die Amnesie der KI, indem sie alten Kontext manuell in den Prompt füttern.",
    "Sobald Basismodelle das Problem eingefrorener Parameter lösen und nativ aus der Umgebung lernen, werden solche Zwischenschichten schlagartig obsolet.",
    "Entwickler müssen für einen Zehn-Jahres-Horizont planen, in dem die AGI mitten in der Produktentwicklung Realität wird.",
    "Die Branche bewegt sich auf ein Ökosystem zu, in dem KI endlich schlafen, sich erinnern",
    "und anpassen lernt und statische Software durch tief integrierte, kumulativ wachsende Intelligenz ersetzt."
]

texts_fr = [
    "Pourquoi l'IA la plus puissante au monde est-elle incapable de se souvenir d'hier ?",
    "Demis Hassabis affirme que tant que les modèles n'apprendront pas à dormir et à rêver comme le cerveau humain,",
    "l'intelligence artificielle générale restera mathématiquement piégée dans une amnésie perpétuelle.",
    "Imaginez interagir avec l'assistant le plus compétent de la planète.",
    "Il peut assimiler un manuel technique de mille pages en quelques secondes, coder et traduire des langues mortes.",
    "Pourtant, dès que l'utilisateur clôt la session, le système oublie intégralement cet échange.",
    "Lorsqu'une IA semble se rappeler une plaisanterie faite une heure plus tôt, cela crée une puissante illusion de mémoire.",
    "En réalité, le système relit à toute vitesse l'intégralité du fil de discussion de haut en bas chaque fois que vous appuyez sur Entrée.",
    "Les ingénieurs appellent cet espace la fenêtre de contexte. Les entreprises vantent l'extension de leurs fenêtres, mais quelle que soit leur taille,",
    "elles fonctionnent strictement comme un bloc-notes temporaire.",
    "Dès que l'on efface l'invite, la feuille est jetée. Demis Hassabis, PDG de Google DeepMind, soulignait récemment que si les architectures actuelles",
    "comme les Transformers sont formidables, il leur manque des piliers vitaux pour atteindre une véritable intelligence générale artificielle.",
    "Les modèles actuels peinent à maintenir un raisonnement sur le long terme et une régularité de production.",
    "Surtout, ils sont totalement dépourvus de mécanismes d'apprentissage continu et de formation de souvenirs durables.",
    "Pour bâtir une intelligence active, les ingénieurs doivent s'affranchir du modèle du bloc-notes passif.",
    "Ils étudient de près le seul système dans l'univers qui a résolu ce défi de rétention d'information : le cerveau humain.",
    "Chaque jour, le cerveau humain est submergé par un flux chaotique de données sensorielles, d'échanges et d'expériences nouvelles.",
    "L'équivalent biologique de la fenêtre de contexte est l'hippocampe.",
    "Il sert de zone tampon temporaire, captant ces fragments épisodiques fugaces pour vous permettre de naviguer les exigences de votre journée.",
    "L'ancrage de ces données ne se fait pas à l'état de veille. Pendant le sommeil, le cerveau opère un rejeu mnésique.",
    "Le rêve agit comme une phase massive de transfert de données. Le cerveau intègre sans perte les nouvelles connaissances de la zone tampon",
    "vers le cortex cérébral, les verrouillant ainsi dans une mémoire permanente.",
    "Sur le plan biologique, le sommeil fonctionne selon un algorithme mécanique très strict.",
    "C'est la phase de traitement indispensable qui convertit l'expérience quotidienne éphémère en une intelligence cumulative sur le long terme.",
    "Cela soulève une question d'ingénierie évidente : pourquoi ne pas coder un script ordonnant à l'IA de dormir et de transférer son bloc-notes",
    "vers un disque dur permanent ? Le verrou est purement mathématique.",
    "Durant la phase d'inférence, les paramètres d'une IA, ses connexions synaptiques de base, sont totalement figés.",
    "Déverser des données dans une fenêtre de contexte élargie ne modifie en rien la structure du modèle.",
    "Les données rebondissent et s'évanouissent. Acquérir un savoir durable exige d'éteindre le réseau et de le réentraîner massivement.",
    "Cette incapacité structurelle à apprendre de manière adaptative pendant l'exécution piège l'IA dans une amnésie constante.",
    "Résoudre cette équation mathématique est l'ultime obstacle sur la route de l'AGI.",
    "La ligne d'arrivée pour la recherche en IA consiste à réussir l'apprentissage continu.",
    "Cela exige une formulation mathématique élégante permettant au modèle d'apprendre au vol au contact direct",
    "de son environnement, en éliminant totalement le besoin de l'interrompre pour le réentraîner.",
    "Cette percée déclenchera une mutation sans précédent. Les chatbots passifs tributaires d'invites continues céderont la place à des systèmes actifs",
    "qui accumuleront au fil du temps un contexte métier approfondi sur les opérations de chaque entreprise.",
    "À mesure que le coût unitaire de calcul à l'inférence chute, nous assisterons à une explosion d'échelle.",
    "Les développeurs déploieront en continu des milliers d'agents actifs en tâche de fond pour paralléliser recherche, raisonnement et évaluation.",
    "Aujourd'hui, de nombreux produits deep tech ne sont que des béquilles logicielles face à l'amnésie de l'IA, réinjectant manuellement le contexte dans l'invite.",
    "Dès que les modèles fondationnels résoudront le problème des paramètres figés et apprendront nativement de leur milieu, ces couches superficielles deviendront obsolètes.",
    "Les développeurs doivent anticiper un horizon de dix ans, où l'AGI surgira en plein milieu du cycle de vie de leur produit.",
    "L'industrie progresse vers un écosystème où l'IA apprendra enfin à dormir, se souvenir",
    "et s'adapter, remplaçant le logiciel statique par une intelligence cumulative profondément intégrée."
]

texts_ja = [
    "なぜ世界で最も強力なAIは、昨日のことすら覚えていられないのでしょうか？",
    "デミス・ハサビス氏は、AIモデルが人間の脳のように眠り、夢を見ることを学ばない限り、",
    "汎用人工知能（AGI）は数学的に永続的な記憶喪失に閉じ込められたままだと指摘します。",
    "地球上で最も有能なアシスタントと対話している場面を想像してください。",
    "千ページもの技術文書を瞬時に読み解き、高度なコードを書き、古代語を翻訳できます。",
    "しかし、ユーザーがセッションを閉じた瞬間、その対話内容は完全に忘れ去られます。",
    "AIが1時間前の冗談を覚えているように見える時、それは強力な記憶の錯覚を生み出しています。",
    "実際には、Enterキーを押すたびに、チャット履歴全体を上から下まで猛烈な速度で読み直しているに過ぎません。",
    "エンジニアはこの作業領域を「コンテキストウィンドウ」と呼びます。テック企業はその拡大を大々的に宣伝しますが、",
    "どれほど巨大になろうとも、本質的には一時的な「下書き用紙」に過ぎません。",
    "プロンプトを消去すれば、下書き用紙は捨てられます。Google DeepMindのCEOデミス・ハサビス氏は最近、",
    "Transformerのような現行のAIアーキテクチャは強力であるものの、真のAGIに至るために不可欠な要素が欠落していると指摘しました。",
    "現行モデルは、長期的な推論や出力の一貫性を保つことに苦戦しています。",
    "何より致命的なのは、継続的学習や長期記憶を形成するメカニズムが完全に欠如している点です。",
    "能動的な知性を構築するには、受け身の下書き用紙モデルを脱却しなければなりません。",
    "研究者たちは、このデータ保持問題を完璧に解決した宇宙唯一のシステム、すなわち人間の脳を注視しています。",
    "人間の脳は日々、感覚データ、会話、新たな体験というカオスな情報の奔流にさらされています。",
    "コンテキストウィンドウの生物学的同等物が「海馬」です。",
    "海馬は一時的な保持領域として機能し、日々の要求を処理するために移ろいやすいエピソード記憶を受け止めます。",
    "このデータの長期保存は、覚醒時には行われません。睡眠中に脳は「メモリー・リプレイ」を実行します。",
    "夢を見ることは、膨大なデータ転送フェーズとして機能します。脳は一時的な保持領域から",
    "大脳皮質へと新たな知識をスムーズかつ可逆的に統合し、恒久的な記憶として定着させるのです。",
    "生物学的に見て、睡眠は厳密な機械的アルゴリズムとして機能しています。",
    "それは、日々の断片的な体験を複利的に積み上がる長期的な知性へと変換する、不可欠なデータ処理フェーズなのです。",
    "ここから明確な技術的疑問が生じます。AIに睡眠を命じ、下書き用紙の記憶を恒久的なハードディスクへ転送する",
    "スクリプトは書けないのでしょうか？ボトルネックは数学的なものです。",
    "推論フェーズにおいて、AIのパラメータ、すなわち中核の神経結合は完全に凍結されています。",
    "拡大されたコンテキストウィンドウにいくら情報を流し込んでも、システム自体は変化しません。",
    "新たなデータは表面で弾かれ、消え去ります。永続的な知識を得るには、システムを停止しネットワーク全体を再学習させるしかありません。",
    "実行中に適応的に学習できないこの構造的限界が、AIを永続的な記憶喪失の状態に閉じ込めているのです。",
    "この数理的課題の解決こそが、AGIへ残された最大のハードルです。",
    "AI研究者にとってのゴールラインは、継続的学習（Continual Learning）の実現です。",
    "これには、モデルが停止や再学習を完全にバイパスし、自身の固有な",
    "環境からリアルタイムで直接学習できるエレガントな数学的解法が必要です。",
    "これが達成されれば、巨大な転換が訪れます。絶え間ない指示を必要とする受け身のチャットボットは姿を消し、",
    "時間の経過とともにユーザーの事業に関する深い文脈を蓄積する自律的システムに置き換わります。",
    "1回の推論コストが低下するにつれ、運用の規模は爆発的に拡大するでしょう。",
    "開発者は、並列検索、推論、評価タスクのために、数千ものアクティブエージェントをバックグラウンドで同時に放ちます。",
    "現在、多くのディープテック製品はAIの記憶喪失を補うための単なるソフトウェアの迂回路であり、古い文脈を手動でプロンプトに戻しているに過ぎません。",
    "基盤モデルがパラメータ凍結の問題を解決し、環境から直接学習するようになれば、そうした浅い機能層は完全に時代遅れになります。",
    "開発者は、製品開発の途中でAGIが到達することを前提とした10年単位の展望を持たねばなりません。",
    "業界は、AIがついに眠り、記憶し、適応することを学ぶエコシステムへと移行しており、",
    "静的なソフトウェアは、深く統合された複利的な知性へと完全に置き換わっていくのです。"
]

dur = ffdur(FINAL_VIDEO)
log(f"Processing {SLUG} (duration: {dur:.2f}s, {len(chunks)} chunks)...")

# Write SRTs
srt_en = ASSET_DIR / f"{SLUG}_en.srt"
srt_de = ASSET_DIR / f"{SLUG}_de.srt"
srt_fr = ASSET_DIR / f"{SLUG}_fr.srt"
srt_ja = ASSET_DIR / f"{SLUG}_ja.srt"

write_srt(chunks, texts_en, srt_en)
write_srt(chunks, texts_de, srt_de)
write_srt(chunks, texts_fr, srt_fr)
write_srt(chunks, texts_ja, srt_ja)
log("SRTs written for EN, DE, FR, JA")

# Dubbing with local Kokoro (100% offline, free, quota-proof)
audio_de = ASSET_DIR / f"{SLUG}_audio_de.m4a"
audio_fr = ASSET_DIR / f"{SLUG}_audio_fr.m4a"

log("Assembling German dub with local Kokoro (cryptomilk/kokoro-german-kerstin)...")
L.assemble(None, chunks, texts_de, "kokoro:de:kerstin", dur, audio_de, ASSET_DIR / "tmp_de_kokoro")

log("Assembling French dub with local Kokoro (ff_siwis)...")
L.assemble(None, chunks, texts_fr, "kokoro:fr:ff_siwis", dur, audio_fr, ASSET_DIR / "tmp_fr_kokoro")

# Copy to staging directory
log("Staging files to Downloads...")
for p in [srt_en, srt_de, srt_fr, srt_ja, audio_de, audio_fr]:
    shutil.copy2(p, STAGING_DIR / p.name)

hook_vo = ASSET_DIR / f"{SLUG}_hook_vo.mp3"
if hook_vo.exists():
    shutil.copy2(hook_vo, STAGING_DIR / hook_vo.name)

final_copy = STAGING_DIR / "The_Sleep_Deficit_Why_AI_Needs_to_Dream_FINAL.mp4"
shutil.copy2(FINAL_VIDEO, final_copy)
log(f"All assets staged to {STAGING_DIR}")
