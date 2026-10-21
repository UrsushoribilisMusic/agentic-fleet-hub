#!/usr/bin/env python3
import json, shutil, sys
from pathlib import Path

# Add tech-shorts directory
sys.path.insert(0, "/Users/miguelrodriguez/projects/agentic-fleet-hub/tech-shorts")
import localize as L
import pipeline

JOB_ID = "ts-20261021-squeezing-an-autonomous-agent-into-32gb"
SLUG = "squeezing-an-autonomous-agent-into-32gb"
ASSET_DIR = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-21-squeezing-an-autonomous-agent-into-32gb")
FINAL_VIDEO = ASSET_DIR / "final_long.mp4"
DOWNLOADS_STAGING = Path("/Users/miguelrodriguez/Downloads/tech-shorts-captions")
STAGING_DIR = DOWNLOADS_STAGING / SLUG
STAGING_DIR.mkdir(parents=True, exist_ok=True)

with open(ASSET_DIR / "whisper_chunks.json") as f:
    chunks = json.load(f)

assert len(chunks) == 19, f"Expected 19 chunks, got {len(chunks)}"

texts_en = [
    "Can you squeeze a frontier autonomous agent into just 32 gigabytes of consumer memory?",
    "Meta Superintelligence Labs just released Muse Glimmer 30B, proving that a dense architecture paired with evolutionary quantization and block-diffusion decoding can out-think cloud giants right on your desk. Artificial intelligence is migrating outward, shifting from massive centralized data centers down to the physical silicon on your desk. This creates a strict operational paradox.",
    "Large cloud models possess the deep reasoning required to act as autonomous agents, but they require you to transmit your private data off-site. Open edge models run privately on local hardware, but they routinely fail to execute complex multi-step tasks. Meta engineered the Muse Glimmer 30B model to resolve this exact friction. It is a local model purpose-built for autonomous workflows.",
    "Every design decision in the model's architecture is dictated by a single unyielding physical constraint: it must operate reliably within a strict 32-gigabyte VRAM envelope, the memory ceiling of consumer hardware like an RTX 5090. This chart compares Muse Glimmer against Gemma 4 and Qwen 3.6. The blue line, Muse Glimmer, tracks closest to the outer perimeter.",
    "Notice the extensions on MCPAtlas, OSWorld-Verified, and TerminalBench. These measure sequential tool use and environment navigation, the exact tasks where local models historically break down. Achieving frontier-level autonomous behavior on a single consumer GPU does not happen by accident. It requires dismantling standard training assumptions and co-designing the architecture entirely around memory limits.",
    "To reach 30 billion parameters under 32 gigabytes, the first decision is structural: how to arrange the neural network itself. The current industry consensus relies on Mixture-of-Experts architectures. MoE divides a massive network into smaller specialized subnetworks, activating only a fraction of its parameters at a time to save on inference compute.",
    "Meta engineers explicitly rejected this consensus. They opted for a dense architecture, meaning every parameter is activated for every token generated. The metric driving this decision is tokens per parameter. When your physical memory ceiling is absolute, you have to measure the maximum compute efficiency you can extract from every megabyte stored in VRAM.",
    "This chart plots bits per byte against GPU hours. It compares a dense architecture against 1-to-8 and 1-to-16 sparse MoE configurations. Because Meta applied an immense compute budget, these models were evaluated in a highly over-trained regime. At the target FLOPs utilization, the dense architecture yields a 2 to 2.5 times increase in compute efficiency",
    "over the MoE ladders. A dense parameter layout extracts higher intelligence per square inch of silicon. If hardware memory is finite, maximizing compute efficiency per parameter dictates a dense build. A dense 30-billion parameter model stored in standard 16-bit floating-point format consumes 55.7 gigabytes of memory.",
    "55.7 gigabytes obviously does not fit into a 32-gigabyte GPU. To leave space for input context and vision encoders, the core language weights must be compressed to under 20 gigabytes. Standard post-training quantization usually applies a flat, uniform bit-rate reduction across all network layers. However, aggressive 4-bit quantization damages the delicate chain-of-thought routing required for an agent to backtrack,",
    "plan, and execute multi-step tools. Meta solved this using EvoPress, an evolutionary mixed-precision search algorithm to selectively compress the model. The algorithm treats the model as 418 independent weight units, separating out individual attention slices and feed-forward gates. EvoPress iteratively tests lowering the precision on each unit, measuring the calibration KL divergence.",
    "It maps exactly how much each specific compression degrades the output compared to the original 16-bit baseline. The algorithm settled on a highly specific allocation: 51 units dropped to Q4, 130 to Q5, and 237 remained at Q6. This precise distribution resulted in a final weight size of exactly 19.65 gigabytes.",
    "Evolutionary search allows the architecture to shrink physically while preserving the mathematical integrity of its reasoning structures. Deploying an agent involves long-horizon tasks: a local model might need to sift through documents and run scripts over thousands of consecutive turns. New turns generate context in the KV cache. Unchecked, this working memory rapidly consumes the remaining VRAM and crashes the system.",
    "Meta implemented Grouped-Query Attention to heavily restrict how much memory the attention layers allocate. They used an extreme 16-to-1 ratio, forcing 32 separate query heads to share just two key-value heads per layer, drastically narrowing the data footprint. The architecture also deploys sliding-window attention to discard irrelevant history: a 2,048-token sliding window rolls forward with the sequence; once the context exceeds this limit, older local tokens are dropped,",
    "flatlining the cache's growth. To prevent the model from losing its overarching objective, every fourth layer uses global attention to accumulate and retain long-range positional signals. The remaining memory budget accommodates a frozen 1.8-billion parameter perception encoder, allowing the model to natively process UI screenshots and documents. The 32-gigabyte envelope is fully occupied:",
    "19.65 gigabytes for weights, 1.8 for vision, a DFlash drafter, and a bounded KV cache. Hard-coding these boundaries guarantees that complex multi-day operations will not trigger out-of-memory failures on consumer hardware. The architecture provides a reliable execution environment, but hardware alone is just an empty vessel. Training a 30-billion parameter model on static internet text does not produce an entity capable of sequential tool use or privacy-aware data management.",
    "Muse Glimmer acquires its behaviors through distillation from Meta's massive frontier-class teacher model, Muse Spark. Meta constructed an always-on AI agent harness running simulated digital lives within deterministic Docker containers populated with mock emails, calendars, and command-line interfaces. They deployed AI personas into these closed universes to execute complex tasks,",
    "generating hundreds of thousands of verified reasoning and tool-use trajectories. Muse Glimmer learns through on-policy distillation: by generating its own rollouts within these simulations and receiving token-level corrections from the teacher model, it learns to replicate frontier-level logic. The result is a highly optimized edge model that delivers cloud-level intelligence, running locally and privately on a single off-the-shelf GPU.",
    "Squeezing autonomous AI onto consumer hardware is a packaging problem: it requires physical limits to dictate the architecture, and simulated digital universes to dictate the mind."
]

texts_de = [
    "Lässt sich ein autonomer Spitzen-Agent in nur zweiunddreißig Gigabyte Arbeitsspeicher auf normaler Verbraucher-Hardware quetschen?",
    "Meta Superintelligence Labs hat soeben Muse Glimmer dreißig B veröffentlicht und bewiesen, dass eine dichte Architektur in Kombination mit evolutionärer Quantisierung und Block-Diffusions-Dekodierung selbst Cloud-Giganten direkt auf Ihrem Schreibtisch übertrumpfen kann. Künstliche Intelligenz wandert nach außen, weg von gigantischen Rechenzentren hin zum physischen Silizium vor Ort. Das erzeugt ein striktes operatives Paradoxon.",
    "Große Cloud-Modelle besitzen zwar das tiefe logische Denkvermögen für autonome Agenten, zwingen Sie aber dazu, private Daten nach außen zu senden. Offene Edge-Modelle laufen privat auf lokaler Hardware, scheitern jedoch regelmäßig an komplexen mehrstufigen Aufgaben. Meta hat Muse Glimmer dreißig B entwickelt, um genau diesen Konflikt zu lösen: ein lokales Modell, maßgeschneidert für autonome Arbeitsabläufe.",
    "Jede Designentscheidung dieser Architektur folgt einer einzigen unerbittlichen physischen Grenze: Das Modell muss zuverlässig in ein striktes Videospeicher-Budget von zweiunddreißig Gigabyte passen, die Obergrenze von Grafikkarten wie einer RTX fünfzig-neunzig. Dieses Diagramm vergleicht Muse Glimmer mit Gemma vier und Qwen drei. Die blaue Linie, Muse Glimmer, verläuft am nächsten am äußeren Rand.",
    "Beachten Sie die Ausschläge bei MCP Atlas, OS World Verified und Terminal Bench. Diese messen sequenzielle Werkzeugnutzung und Umgebungsnavigation, genau jene Aufgaben, an denen lokale Modelle bisher scheiterten. Autonomes Verhalten auf Spitzenniveau auf einer einzigen Grafikkarte entsteht nicht zufällig. Es erfordert das Aufbrechen gängiger Trainingsannahmen und ein Architekturdesign rund um Speichergrenzen.",
    "Um dreißig Milliarden Parameter unter zweiunddreißig Gigabyte zu erreichen, ist die erste Entscheidung struktureller Natur: der Aufbau des neuronalen Netzes selbst. Der aktuelle Branchenkonsens setzt auf Mixture-of-Experts-Architekturen. MoE teilt ein riesiges Netz in kleinere Teilnetze auf und aktiviert pro Schritt nur einen Bruchteil der Parameter, um Rechenleistung bei der Inferenz zu sparen.",
    "Die Ingenieure von Meta lehnten diesen Konsens bewusst ab. Sie wählten eine dichte Architektur, bei der jeder einzelne Parameter für jedes erzeugte Token aktiviert wird. Die entscheidende Kennzahl hierfür lautet Tokens pro Parameter. Wenn die physische Speicherobergrenze absolut ist, zählt allein die maximale Recheneffizienz, die sich aus jedem gespeicherten Megabyte im Videospeicher herausholen lässt.",
    "Dieses Diagramm zeigt Bits pro Byte im Verhältnis zu den GPU-Stunden. Es vergleicht eine dichte Architektur mit eins-zu-acht und eins-zu-sechzehn dünn besetzten MoE-Konfigurationen. Da Meta ein enormes Rechenbudget einsetzte, wurden diese Modelle in einem stark übertrainierten Bereich evaluiert. Bei der angestrebten Auslastung liefert die dichte Architektur eine zwei- bis zweieinhalbfach höhere Recheneffizienz",
    "gegenüber den MoE-Varianten. Eine dichte Parameterstruktur holt schlicht mehr Intelligenz aus jedem Quadratzentimeter Silizium. Wenn der Hardwarespeicher endlich ist, diktiert die maximale Effizienz pro Parameter einen dichten Aufbau. Doch ein dichtes Modell mit dreißig Milliarden Parametern im Standard-Sechzehn-Bit-Format belegt fünfundfünfzig Komma sieben Gigabyte Speicher.",
    "Fünfundfünfzig Komma sieben Gigabyte passen offensichtlich nicht in eine Zweiunddreißig-Gigabyte-Grafikkarte. Um Platz für Kontext und Bildverarbeitung zu lassen, müssen die Sprachgewichte auf unter zwanzig Gigabyte komprimiert werden. Herkömmliche Quantisierung reduziert die Bitrate meist gleichmäßig über alle Schichten hinweg. Doch eine pauschale Vier-Bit-Quantisierung zerstört die feinen Denkstrukturen, die ein Agent zum Zurückverfolgen,",
    "Planen und Ausführen mehrstufiger Werkzeuge benötigt. Meta löste dies mit EvoPress, einem evolutionären Suchalgorithmus für gemischte Präzision zur selektiven Komprimierung. Der Algorithmus behandelt das Modell als vierhundertachtzehn unabhängige Gewichtseinheiten und trennt Aufmerksamkeits-Slices und Feed-Forward-Gates auf. EvoPress testet schrittweise geringere Präzisionen je Einheit und misst die KL-Divergenz.",
    "So wird exakt kartiert, wie stark jede einzelne Komprimierung die Ausgabe im Vergleich zur Sechzehn-Bit-Basislinie verschlechtert. Der Algorithmus fand eine hochpräzise Verteilung: einundfünfzig Einheiten sanken auf Q vier, einhundertdreißig auf Q fünf und zweihundertsiebenunddreißig blieben bei Q sechs. Diese exakte Aufteilung ergab eine finale Modellgröße von genau neunzehn Komma sechs fünf Gigabyte.",
    "Die evolutionäre Suche lässt die Architektur physisch schrumpfen, während die mathematische Integrität ihrer logischen Strukturen erhalten bleibt. Der Einsatz eines Agenten erfordert jedoch Langzeitaufgaben: Ein lokales Modell muss Dokumente durchforsten und Skripte über tausende Runden hinweg ausführen. Jede Runde vergrößert den Kontext im KV-Cache. Ungebremst frisst dieser Arbeitsspeicher den restlichen Videospeicher auf und bringt das System zum Absturz.",
    "Meta implementierte Grouped-Query Attention, um den Speicherbedarf der Aufmerksamkeitsschichten drastisch zu begrenzen. Mit einem extremen Verhältnis von sechzehn zu eins teilen sich zweiunddreißig Abfrageköpfe lediglich zwei Schlüssel-Wert-Köpfe pro Schicht, was den Datenfußabdruck massiv reduziert. Zudem verwirft ein gleitendes Aufmerksamkeitsfenster von zweitausendachtundvierzig Tokens irrelevante Historie: Sobald der Kontext dieses Limit überschreitet, werden ältere lokale Tokens verworfen,",
    "wodurch das Wachstum des Caches abgeflacht wird. Damit das Modell sein übergeordnetes Ziel nicht aus den Augen verliert, nutzt jede vierte Schicht globale Aufmerksamkeit, um weitreichende Positionssignale zu bewahren. Das verbleibende Speicherbudget beherbergt einen eingefrorenen Wahrnehmungs-Encoder mit einer Komma acht Milliarden Parametern, der Screenshots und Dokumente nativ verarbeitet. Damit ist der Zweiunddreißig-Gigabyte-Rahmen exakt ausgefüllt:",
    "neunzehn Komma sechs fünf Gigabyte für Gewichte, eins Komma acht für das Sehen, ein D-Flash-Drafter und ein begrenzter KV-Cache. Diese fest einprogrammierten Grenzen garantieren, dass komplexe mehrtägige Operationen auf Verbraucher-Hardware niemals zu Speicherabstürzen führen. Doch die Architektur liefert nur die verlässliche Ausführungsumgebung; Hardware allein ist eine leere Hülle. Ein Training auf statischen Internettexten erzeugt noch keinen Agenten für sichere Werkzeugnutzung.",
    "Muse Glimmer erwirbt seine Fähigkeiten durch Destillation aus Metas gewaltigem Spitzenmodell Muse Spark. Dafür baute Meta eine permanent aktive Agenten-Testumgebung, die simulierte digitale Lebenswelten in deterministischen Docker-Containern mit nachgebildeten E-Mails, Kalendern und Kommandozeilen ausführt. In diese geschlossenen Universen wurden KI-Personas gesetzt, um komplexe Aufgaben zu lösen,",
    "wodurch hunderttausende verifizierte Denk- und Werkzeug-Trajektorien entstanden. Muse Glimmer lernt durch On-Policy-Destillation: Indem es in diesen Simulationen eigene Abläufe generiert und auf Token-Ebene Korrekturen vom Lehrermodell erhält, lernt es, Spitzenlogik exakt zu replizieren. Das Ergebnis ist ein hochoptimiertes Edge-Modell, das Intelligenz auf Cloud-Niveau liefert und dabei lokal und privat auf einer einzigen handelsüblichen Grafikkarte läuft.",
    "Autonome KI auf Verbraucher-Hardware zu bringen ist ein Verpackungsproblem: Physische Grenzen müssen die Architektur diktieren, und simulierte digitale Universen den Geist."
]

texts_fr = [
    "Peut-on faire tenir un agent autonome de pointe dans seulement trente-deux gigaoctets de mémoire grand public ?",
    "Meta Superintelligence Labs vient de dévoiler Muse Glimmer trente B, prouvant qu'une architecture dense associée à une quantification évolutionnaire et un décodage par diffusion de blocs peut surpasser les géants du cloud directement sur votre bureau. L'intelligence artificielle migre vers la périphérie, quittant les immenses centres de données pour le silicium physique de votre machine. Cela crée un paradoxe opérationnel strict.",
    "Les grands modèles cloud possèdent le raisonnement profond requis pour agir en agents autonomes, mais exigent l'envoi de vos données privées à distance. Les modèles locaux tournent en toute confidentialité sur votre matériel, mais échouent régulièrement face à des tâches complexes en plusieurs étapes. Meta a conçu Muse Glimmer trente B pour résoudre exactement cette friction : un modèle local bâti pour les flux autonomes.",
    "Chaque choix architectural est dicté par une contrainte physique inflexible : fonctionner de manière fiable dans une enveloppe stricte de trente-deux gigaoctets de mémoire vidéo, le plafond des cartes grand public comme la RTX cinquante quatre-vingt-dix. Ce graphique compare Muse Glimmer à Gemma quatre et Qwen trois. La courbe bleue, Muse Glimmer, épouse au plus près le périmètre extérieur.",
    "Observez les pointes sur MCP Atlas, OS World Verified et Terminal Bench. Ces tests mesurent l'usage séquentiel d'outils et la navigation système, là où les modèles locaux s'effondrent habituellement. Obtenir un comportement autonome de pointe sur une seule carte graphique grand public ne doit rien au hasard : il faut repenser l'entraînement et concevoir toute l'architecture autour des limites mémoire.",
    "Pour atteindre trente milliards de paramètres sous trente-deux gigaoctets, la première décision est structurelle : comment organiser le réseau neuronal. Le consensus actuel repose sur les architectures à mélange d'experts. Le MoE divise un vaste réseau en sous-réseaux spécialisés, n'activant qu'une fraction des paramètres à chaque étape pour économiser le calcul d'inférence.",
    "Les ingénieurs de Meta ont explicitement rejeté ce consensus. Ils ont opté pour une architecture dense, où chaque paramètre est activé pour chaque jeton généré. La métrique clé derrière ce choix est le nombre de jetons par paramètre. Lorsque le plafond physique de mémoire est absolu, il faut mesurer l'efficacité de calcul maximale extractible de chaque mégaoctet stocké en mémoire vidéo.",
    "Ce graphique trace les bits par octet face aux heures de calcul GPU. Il compare une architecture dense à des configurations MoE éparses d'un sur huit et d'un sur seize. Grâce à un budget de calcul massif, ces modèles ont été évalués en régime fortement surentraîné. À l'utilisation cible, l'architecture dense offre un gain d'efficacité de calcul de deux à deux virgule cinq fois supérieur",
    "aux échelles MoE. Une disposition dense extrait davantage d'intelligence par centimètre carré de silicium. Si la mémoire matérielle est finie, maximiser l'efficacité par paramètre impose une structure dense. Or, un modèle dense de trente milliards de paramètres stocké au format standard seize bits consomme cinquante-cinq virgule sept gigaoctets de mémoire.",
    "Cinquante-cinq virgule sept gigaoctets ne rentrent évidemment pas dans un GPU de trente-deux gigaoctets. Pour laisser de la place au contexte et à l'encodeur visuel, les poids du modèle doivent passer sous les vingt gigaoctets. La quantification classique réduit uniformément la précision sur toutes les couches. Mais une quantification agressive en quatre bits endommage les délicats chemins de raisonnement nécessaires pour revenir en arrière,",
    "planifier et exécuter des outils en série. Meta a résolu ce problème avec EvoPress, un algorithme évolutionnaire de recherche en précision mixte qui compresse sélectivement le modèle. L'algorithme découpe le réseau en quatre cent dix-huit unités indépendantes, séparant les tranches d'attention et les portes feed-forward. EvoPress teste la baisse de précision sur chaque unité en mesurant la divergence KL de calibration.",
    "Il cartographie ainsi exactement la dégradation induite par chaque compression par rapport à la référence en seize bits. L'algorithme a convergé vers une allocation très précise : cinquante et une unités en Q quatre, cent trente en Q cinq et deux cent trente-sept maintenues en Q six. Cette distribution aboutit à une taille finale des poids d'exactement dix-neuf virgule soixante-cinq gigaoctets.",
    "La recherche évolutionnaire permet de réduire physiquement l'architecture tout en préservant l'intégrité mathématique de ses structures de raisonnement. Mais déployer un agent implique des tâches au long cours : fouiller des documents et exécuter des scripts sur des milliers de tours consécutifs. Chaque tour gonfle le cache KV. Sans contrôle, cette mémoire de travail sature rapidement la mémoire vidéo et fait planter le système.",
    "Meta a implémenté une attention à requêtes groupées pour restreindre drastiquement la mémoire allouée. Avec un ratio extrême de seize pour un, trente-deux têtes de requête partagent seulement deux têtes clé-valeur par couche, réduisant massivement l'empreinte. L'architecture déploie aussi une fenêtre glissante de deux mille quarante-huit jetons pour écarter l'historique superflu : au-delà de cette limite, les anciens jetons locaux sont effacés,",
    "stabilisant la croissance du cache. Pour éviter que le modèle ne perde son objectif global, une couche sur quatre utilise une attention globale qui conserve les signaux positionnels à longue portée. Le budget mémoire restant accueille un encodeur de perception figé d'un virgule huit milliard de paramètres, traitant nativement captures d'écran et documents. L'enveloppe de trente-deux gigaoctets est pleinement occupée :",
    "dix-neuf virgule soixante-cinq gigaoctets pour les poids, un virgule huit pour la vision, un décodeur spéculatif D-Flash et un cache KV borné. Graver ces limites dans le marbre garantit que des opérations complexes sur plusieurs jours ne provoqueront jamais de panne mémoire sur du matériel grand public. Mais le matériel seul reste une coquille vide : entraîner un modèle sur du texte statique ne crée pas un agent maîtrisant les outils et la confidentialité.",
    "Muse Glimmer acquiert ses compétences par distillation à partir de Muse Spark, le modèle géant de pointe de Meta. Meta a bâti un environnement d'agents tournant en continu, simulant des vies numériques au sein de conteneurs Docker déterministes peuplés de courriels, agendas et terminaux simulés. Des personas d'IA ont été déployés dans ces univers clos pour accomplir des tâches complexes,",
    "générant des centaines de milliers de trajectoires vérifiées de raisonnement et d'usage d'outils. Muse Glimmer apprend par distillation sur politique : en générant ses propres trajectoires dans ces simulations et en recevant des corrections jeton par jeton du modèle professeur, il reproduit une logique de pointe. Le résultat est un modèle local ultra-optimisé offrant une intelligence digne du cloud sur un simple GPU du commerce.",
    "Concentrer une IA autonome sur du matériel grand public est un défi d'intégration : ce sont les limites physiques qui doivent dicter l'architecture, et des univers numériques simulés qui doivent façonner l'esprit."
]

texts_ja = [
    "最先端の自律型AIエージェントを、わずか32ギガバイトの民生用メモリに収めることは可能でしょうか？",
    "Metaのスーパーインテリジェンス・ラボが発表した「Muse Glimmer 30B」は、高密度（Dense）アーキテクチャに進化型量子化とブロック拡散デコーディングを組み合わせることで、デスク上のローカル環境でもクラウドの巨大モデルを凌駕できることを実証しました。AIは今、巨大な中央集権型データセンターから手元の物理シリコンへと移行しており、そこに重大な運用上のパラドックスが生まれています。",
    "大規模なクラウドモデルは自律エージェントに必要な深い推論力を備えていますが、機密データを外部へ送信する必要があります。一方、オープンなエッジモデルはローカル機器上で安全に動作するものの、複雑なマルチステップのタスクでは頻繁に破綻します。Metaはこのジレンマを解消するため、自律ワークフロー専用に設計されたローカルモデル「Muse Glimmer 30B」を開発しました。",
    "アーキテクチャのあらゆる設計判断は、たった一つの絶対的な物理制約に従っています。それはRTX 5090などの民生用GPUのメモリ上限である「32GB VRAM」の枠内で確実に動作することです。このレーダーチャートはMuse GlimmerをGemma 4およびQwen 3.6と比較したもので、青い線のMuse Glimmerが最も外周近くをトレースしています。",
    "MCPAtlas、OSWorld-Verified、TerminalBenchでの突出したスコアに注目してください。これらは連続的なツール利用や環境操作を測定するもので、従来のローカルモデルが最も苦手としてきた領域です。単一の民生用GPUで最先端の自律動作を実現することは偶然では起こり得ません。標準的な学習の前提を解体し、メモリ制約を中心にアーキテクチャ全体を再設計する必要があるのです。",
    "32GB未満で300億パラメータを実現するための第一の決断は、ニューラルネットワーク自体の構造です。現在の業界の主流はMixture-of-Experts（MoE）アーキテクチャです。MoEは巨大なネットワークを専門化した小規模なサブネットワークに分割し、推論時には一部のパラメータのみを活性化させることで計算コストを節約します。",
    "しかしMetaのエンジニアはこの常識を明確に退け、生成されるすべてのトークンに対して全パラメータを活性化させる「Dense（高密度）アーキテクチャ」を選択しました。この判断の鍵となった指標が「パラメータあたりのトークン数」です。物理メモリの上限が絶対である場合、VRAMに格納された1メガバイトあたりから引き出せる最大の計算効率を測る必要があります。",
    "このグラフはGPU時間に対する1バイトあたりのビット数をプロットし、Dense構造と1対8および1対16のスパースMoE構成を比較しています。Metaは膨大な計算予算を投じ、これらを過学習領域で評価しました。目標とするFLOPs利用率において、DenseアーキテクチャはMoEに対して2倍から2.5倍もの計算効率の向上を達成しています。",
    "シリコンの単位面積あたりでより高い知能を引き出せるのはDense構造なのです。ハードウェアメモリが有限である以上、パラメータあたりの計算効率の最大化はDense設計を必然とします。しかし、300億パラメータのDenseモデルを標準的な16ビット浮動小数点形式で保存すると、55.7GBものメモリを消費してしまいます。",
    "55.7GBは当然ながら32GBのGPUには収まりません。入力コンテキストや視覚エンコーダ用の領域を確保するには、言語モデルの重みを20GB未満に圧縮する必要があります。一般的な学習後量子化では全レイヤーに均一なビット削減を適用しますが、強引な4ビット量子化は、エージェントが軌道修正や",
    "計画立案、マルチステップのツール実行を行うための繊細な思考連鎖（Chain-of-Thought）のルーティングを損なってしまいます。Metaは進化型混合精度探索アルゴリズム「EvoPress」を用いてモデルを選択的に圧縮することでこれを解決しました。この手法ではモデルを418個の独立した重みユニットに分割し、各ユニットの精度低下によるKLダイバージェンスの増加を反復的に測定します。",
    "これにより、16ビットの基準モデルと比較して各圧縮が出力品質をどれだけ劣化させるかを正確にマッピングします。最終的にアルゴリズムは、51ユニットをQ4へ、130ユニットをQ5へ落とし、237ユニットをQ6に維持するという極めて精緻な配分に到達しました。この最適化により、モデルの重みサイズは正確に19.65GBへと収まりました。",
    "進化的探索によって、推論構造の数学的整合性を保ったまま物理サイズを縮小できたのです。さらにエージェントの運用では長期タスクが求められます。何千ターンにもわたり文書を精査しスクリプトを実行し続けると、KVキャッシュのコンテキストが膨れ上がり、放置すれば残りのVRAMを食い潰してシステムがクラッシュしてしまいます。",
    "そこでMetaはGrouped-Query Attention（GQA）を導入し、アテンション層が消費するメモリを厳しく制限しました。32個のクエリヘッドがわずか2個のキー・バリューヘッドを共有する16対1の比率を採用し、データ量を劇的に削減しています。さらに2048トークンのスライディングウィンドウ・アテンションによって古い局所トークンを順次破棄し、",
    "キャッシュの肥大化を平坦化しました。同時に、モデルが全体目標を見失わないよう4層ごとにグローバル・アテンションを配置し、長距離の位置情報を保持させています。残りのメモリ予算には凍結された18億パラメータの視覚エンコーダが収まり、UIのスクリーンショットや文書をネイティブに処理します。こうして32GBの枠は完璧に使い切られます。",
    "重みに19.65GB、視覚に1.8GB、DFlashドラフター、そして上限付きのKVキャッシュ。この境界をハードコードすることで、数日間に及ぶ複雑な自律稼働でも民生用ハードウェアでメモリ不足に陥らないことが保証されます。しかしハードウェアは器に過ぎません。静的なネット上のテキストで300億パラメータを学習させても、ツール操作やプライバシー配慮ができるエージェントにはなりません。",
    "Muse Glimmerは、Metaの最先端巨大教師モデル「Muse Spark」からの蒸留によってその行動様式を獲得します。Metaは模擬メールやカレンダー、CLIを備えた決定論的Dockerコンテナ内で「デジタルな生活空間（ユニバース）」を常時稼働させるAIエージェント環境を構築し、そこにAIペルソナを投入して複雑なタスクを実行させました。",
    "こうして検証済みの推論とツール利用の軌跡が何十万件も生成されました。Muse Glimmerはオンポリシー蒸留によって学習します。シミュレーション内で自らロールアウトを生成し、教師モデルからトークン単位の修正フィードバックを受けることで、最先端モデルの論理を再現できるようになるのです。結果として、市販の単一GPU上でローカルかつプライベートにクラウド級の知能を発揮するエッジモデルが誕生しました。",
    "自律型AIを民生用ハードウェアに詰め込むことはパッケージングの問題です。物理的な制約がアーキテクチャを規定し、シミュレートされたデジタル宇宙が知性を形作るのです。"
]

dur = L.ffdur(FINAL_VIDEO)
L.log(f"Processing {SLUG} (duration: {dur:.2f}s, {len(chunks)} chunks)...")

# Write SRTs
srt_en = ASSET_DIR / f"{SLUG}_en.srt"
srt_de = ASSET_DIR / f"{SLUG}_de.srt"
srt_fr = ASSET_DIR / f"{SLUG}_fr.srt"
srt_ja = ASSET_DIR / f"{SLUG}_ja.srt"

L.write_srt(chunks, texts_en, srt_en)
L.write_srt(chunks, texts_de, srt_de)
L.write_srt(chunks, texts_fr, srt_fr)
L.write_srt(chunks, texts_ja, srt_ja)
L.log("SRTs written for EN, DE, FR, JA")

# Dubbing with local Kokoro (100% offline, free, quota-proof)
audio_de = ASSET_DIR / f"{SLUG}_audio_de.m4a"
audio_fr = ASSET_DIR / f"{SLUG}_audio_fr.m4a"

L.log("Assembling German dub with local Kokoro (cryptomilk/kokoro-german-kerstin)...")
L.assemble(None, chunks, texts_de, "kokoro:de:kerstin", dur, audio_de, ASSET_DIR / "tmp_de_kokoro")

L.log("Assembling French dub with local Kokoro (ff_siwis)...")
L.assemble(None, chunks, texts_fr, "kokoro:fr:ff_siwis", dur, audio_fr, ASSET_DIR / "tmp_fr_kokoro")

# Stage files to Downloads
L.log("Staging files to Downloads...")
for p in [srt_en, srt_de, srt_fr, srt_ja, audio_de, audio_fr]:
    shutil.copy2(p, STAGING_DIR / p.name)

hook_vo = ASSET_DIR / f"{SLUG}_hook_vo.mp3"
if hook_vo.exists():
    shutil.copy2(hook_vo, STAGING_DIR / hook_vo.name)

final_copy = STAGING_DIR / "Squeezing_an_Autonomous_Agent_into_32GB_FINAL.mp4"
shutil.copy2(FINAL_VIDEO, final_copy)
L.log(f"All assets staged to {STAGING_DIR}")

# Update jobs.json with localizations
localizations = {
    "de": {
        "title": "Autonomer KI-Agent in 32 GB: Metas Muse Glimmer 30B Architektur erklärt",
        "description": (
            "Kann ein wirklich autonomer KI-Agent komplett lokal auf einer 32-GB-Verbrauchergrafikkarte ohne Cloud-Anbindung laufen?\n\n"
            "In ihrem technischen Bericht vom Oktober 2026 stellt Meta Superintelligence Labs Muse Glimmer 30B (Apache 2.0) vor: ein multimodales Sprachmodell mit 29,6 Milliarden Parametern, das gezielt für langfristige autonome Aufgaben, sequenzielle Werkzeugnutzung und Fehlerbehebung auf lokaler Hardware entwickelt wurde.\n\n"
            "In dieser Analyse entschlüsseln wir die Systemarchitektur, mit der Spitzen-Intelligenz in ein striktes 32-GB-VRAM-Budget gepackt wird:\n\n"
            "1. Warum Dense unter 32 GB gegen MoE gewinnt: Unter einer festen Speicherobergrenze zeigten Skalierungskurven, dass ein dichter 30B-Transformer (52 Schichten) eine 2- bis 2,5-fach höhere Recheneffizienz erreicht als 1:8- und 1:16-Mixture-of-Experts-Designs (MoE).\n"
            "2. Zähmung des KV-Caches: Langzeit-Agentensitzungen werden vom Wachstum des KV-Caches dominiert. Muse Glimmer nutzt 16:1 Grouped-Query Attention (32 Query- / 2 KV-Köpfe) und ein [Local, Local, Local, Global]-Muster mit einem gleitenden 2048-Token-Fenster für über 128K Kontext.\n"
            "3. Multimodaler Perception Encoder: Ein eingefrorener 1,8B NaViT-Vision-Encoder verarbeitet Screenshots, Dokumente und Diagramme in nativer Auflösung.\n"
            "4. Co-Destillation, Souping & synthetische Persona-Universen: Destilliert aus Metas Spitzenmodell Muse Spark durch Top-256-Logit-Destillation, Checkpoint-Souping, On-Policy-Destillation und Multi-Objective-RL in isolierten Docker-Umgebungen mit Contextual-Integrity-Datenschutztraining.\n"
            "5. Unter 20 GB Modellgewichte & DFlash-Spekulation: Evolutionäre Mixed-Precision-Quantisierung (EvoPress Q4_K/Q5_K/Q6_K mit 19,65 GB) kombiniert mit einem 5-schichtigen DFlash-Block-Diffusions-Drafter.\n\n"
            "Quellen & Referenzen:\n"
            "- \"Muse Glimmer 30B: An On-Device Agentic Model\" (Muse Glimmer Team, Meta Superintelligence Labs, 21. Oktober 2026).\n"
            "- arXiv-Preprint: https://arxiv.org/abs/2610.24628\n"
            "- Modellgewichte (Apache 2.0): https://huggingface.co/meta-models/Muse-Glimmer-30B\n"
            "- Forschungsblog: https://research.meta.ai/blog/introducing-muse-glimmer-open-agentic-model\n\n"
            "Hinweis: KI-gestütztes Erklärvideo von The Classical Remix auf Basis des technischen Berichts der Meta Superintelligence Labs.\n\n"
            "#MuseGlimmer #MetaAI #OnDeviceAI #AutonomousAgents #LLMArchitecture #Quantization #SpeculativeDecoding #LocalAI #TechExplained"
        ),
        "audio": str(audio_de),
        "srt": str(srt_de),
    },
    "fr": {
        "title": "Un agent IA autonome dans 32 Go : l'architecture de Muse Glimmer 30B (Meta)",
        "description": (
            "Un agent IA véritablement autonome peut-il fonctionner entièrement sur un GPU grand public de 32 Go sans dépendre du cloud ?\n\n"
            "Dans son rapport technique d'octobre 2026, Meta Superintelligence Labs présente Muse Glimmer 30B (Apache 2.0), un modèle multimodal de 29,6 milliards de paramètres conçu sur mesure pour les flux agentiques au long cours, l'utilisation séquentielle d'outils et la récupération sur erreur en local.\n\n"
            "Dans cette vidéo, nous décryptons l'architecture système permettant de concentrer une intelligence agentique de pointe dans une enveloppe stricte de 32 Go de VRAM :\n\n"
            "1. Pourquoi le modèle dense bat le MoE sous 32 Go : à plafond mémoire fixe, un transformeur dense de 30B (52 couches) offre une efficacité de calcul 2 à 2,5 fois supérieure aux architectures Mixture-of-Experts (MoE 1:8 et 1:16).\n"
            "2. Maîtriser le goulot d'étranglement du cache KV : Muse Glimmer combine une attention à requêtes groupées 16:1 (32 têtes Query / 2 têtes KV) et un motif répétitif [Local, Local, Local, Global] à fenêtre glissante de 2048 jetons pour supporter plus de 128K de contexte.\n"
            "3. Encodeur de perception multimodal : un encodeur visuel NaViT figé de 1,8 milliard de paramètres traite nativement captures d'écran, documents et graphiques.\n"
            "4. Co-distillation, Souping et univers synthétiques : distillé à partir du modèle professeur Muse Spark via co-distillation des 256 meilleurs logits, fusion de checkpoints (souping), distillation sur politique et RL multi-objectif dans des conteneurs Docker simulant des vies numériques complètes.\n"
            "5. Poids sous 20 Go et décodage spéculatif DFlash : quantification évolutionnaire en précision mixte EvoPress (Q4_K/Q5_K/Q6_K à 19,65 Go) associée à un décodeur par diffusion de blocs DFlash à 5 couches.\n\n"
            "Sources et références :\n"
            "- \"Muse Glimmer 30B: An On-Device Agentic Model\" (Muse Glimmer Team, Meta Superintelligence Labs, 21 octobre 2026).\n"
            "- Prépublication arXiv : https://arxiv.org/abs/2610.24628\n"
            "- Poids du modèle (Apache 2.0) : https://huggingface.co/meta-models/Muse-Glimmer-30B\n"
            "- Blog de recherche : https://research.meta.ai/blog/introducing-muse-glimmer-open-agentic-model\n\n"
            "Divulgation : Vidéo explicative assistée par IA par The Classical Remix, fondée sur le rapport technique de Meta Superintelligence Labs.\n\n"
            "#MuseGlimmer #MetaAI #OnDeviceAI #AutonomousAgents #LLMArchitecture #Quantization #SpeculativeDecoding #LocalAI #TechExplained"
        ),
        "audio": str(audio_fr),
        "srt": str(srt_fr),
    },
    "ja": {
        "title": "32GBに自律型AIエージェントを凝縮：Meta「Muse Glimmer 30B」のシステム設計",
        "description": (
            "真に自律的なAIエージェントは、クラウドに頼らず32GBの民生用GPUだけで完全に動作できるのでしょうか？\n\n"
            "2026年10月の技術レポートにて、Meta Superintelligence Labsは「Muse Glimmer 30B」（Apache 2.0ライセンス）を発表しました。民生用ハードウェア上での長期的な自律タスク、連続的なツール呼び出し、エラー回復のために専用設計された296億パラメータのマルチモーダル言語モデルです。\n\n"
            "本動画では、最先端のエージェント知能を厳格な32GB VRAMの枠内に収めるためのシステムアーキテクチャを徹底解説します：\n\n"
            "1. なぜ32GB制約下でDenseがMoEを凌駕するのか：一定の推論メモリ上限のもとでは、30BのDenseトランスフォーマー（52層）が1:8および1:16のMixture-of-Experts（MoE）設計と比較して2〜2.5倍高い計算効率を達成。\n"
            "2. KVキャッシュの肥大化を抑え込む：16:1のGrouped-Query Attention（32クエリ／2KVヘッド）と、[Local, Local, Local, Global]の2048トークン・スライディングウィンドウ構造により、メモリを溢れさせずに128K以上の長文脈を実現。\n"
            "3. マルチモーダル知覚エンコーダ：凍結された18億パラメータのNaViT型視覚バックボーンにより、高解像度のUIスクリーンショット、文書、グラフをネイティブに処理。\n"
            "4. 共蒸留・Souping・合成ペルソナ宇宙：Metaの最先端モデル「Muse Spark」から上位256ロジットのKL共蒸留、チェックポイント平均化（Souping）、オンポリシー蒸留、さらにDockerコンテナ内の仮想デジタル生活空間を用いた多目的RLによって高度なツール操作と文脈的プライバシー保護（Contextual Integrity）を獲得。\n"
            "5. 20GB未満の重み圧縮とDFlash投機的デコーディング：進化的混合精度量子化「EvoPress」（Q4_K/Q5_K/Q6_Kにより19.65GBへ圧縮、BF16比で75.6%対75.7%の精度維持）と、1回のフォワードパスで16トークンを予測する5層DFlashブロック拡散ドラフター。\n\n"
            "情報源・引用文献：\n"
            "- \"Muse Glimmer 30B: An On-Device Agentic Model\" (Muse Glimmer Team, Meta Superintelligence Labs, 2026年10月21日)\n"
            "- arXivプレプリント: https://arxiv.org/abs/2610.24628\n"
            "- モデル重み (Apache 2.0): https://huggingface.co/meta-models/Muse-Glimmer-30B\n"
            "- 研究ブログ: https://research.meta.ai/blog/introducing-muse-glimmer-open-agentic-model\n\n"
            "開示：The Classical RemixによるAI支援技術解説。Meta Superintelligence Labsの技術レポートに基づいています。\n\n"
            "#MuseGlimmer #MetaAI #OnDeviceAI #AutonomousAgents #LLMArchitecture #Quantization #SpeculativeDecoding #LocalAI #TechExplained"
        ),
        "audio": "",
        "srt": str(srt_ja),
    }
}

data = pipeline.load_jobs()
job = pipeline.find_job(data, JOB_ID)
yt = dict(job.get("youtube", {}))
yt["localizations"] = localizations
yt["captions_en_srt"] = str(srt_en)
pipeline.update_job_field(JOB_ID, youtube=yt)
L.log("Updated jobs.json with EN/DE/FR/JA localizations.")
