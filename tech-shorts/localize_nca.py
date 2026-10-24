#!/usr/bin/env python3
import json, shutil, sys
from pathlib import Path

sys.path.insert(0, "/Users/miguelrodriguez/projects/agentic-fleet-hub/tech-shorts")
import localize as L
import pipeline

JOB_ID = "ts-20261024-reasoning-with-neural-cellular-automata-nca"
SLUG = "reasoning-with-neural-cellular-automata-nca"
ASSET_DIR = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-24-reasoning-with-neural-cellular-automata-nca")
FINAL_VIDEO = ASSET_DIR / "final_long.mp4"
DOWNLOADS_STAGING = Path("/Users/miguelrodriguez/Downloads/tech-shorts-captions")
STAGING_DIR = DOWNLOADS_STAGING / SLUG
STAGING_DIR.mkdir(parents=True, exist_ok=True)

with open(ASSET_DIR / "whisper_chunks.json") as f:
    chunks = json.load(f)

assert len(chunks) == 16, f"Expected 16 chunks, got {len(chunks)}"

texts_en = [
    "Can complex multi-step reasoning emerge purely from tiny cells that only talk to their immediate neighbors?",
    "Researchers from Google's Paradigms of Intelligence team and Mila just proved that Neural Cellular Automata can solve giant mazes, extreme Sudoku, and ARC-AGI without global attention—turning reasoning into a living, self-healing spatial wave. Modern artificial intelligence runs on an architecture built around a concept called global attention.",
    "In systems like large language models, every single piece of data in the network constantly monitors and communicates with every other piece of data to solve a problem. That constant all-to-all communication requires a massive amount of computing power. As these models scale up to handle harder tasks, that centralized data movement becomes a severe bottleneck, draining vast amounts of energy to keep every part of the system synchronized.",
    "Take a look at this maze overlaid with a single central node. To find the exit, a traditional AI architecture uses global attention to ingest the entire board simultaneously, calculating every wall and open corridor in one synchronized, energy-intensive sweep. Biology solves spatial problems completely differently. A slime mold navigating the forest floor doesn't have a centralized brain mapping out the entire terrain.",
    "It finds food from the bottom up, using tiny, localized interactions that require very little energy. Pushing past the current physical and energy limits of computing requires looking past that centralized, top-down structure. We have to figure out if complex logic can be executed using localized, decentralized interactions. What you are watching here is a decentralized alternative called a Neural Cellular Automaton, or NCA.",
    "Instead of a single giant processor, the system is made up of a grid of thousands of highly compact, independent AI cells, waking up and communicating like a swarm. There is no master brain directing this swarm. And as you can see in this diagram, no single cell can see the overall maze. Each unit is entirely blind to the big picture; it only possesses the ability to observe the immediate eight neighbors physically touching it. That creates a serious mechanical puzzle.",
    "These cells possess no global map, no shared memory, and no long-range communication. They are completely disconnected from the exit, yet somehow they have to coordinate to navigate the entire board. To see how they manage it, we must drop down to the maze's absolute starting point and look at the behavior of a single isolated cell. Every cell operates on a strict two-step loop. Step one is perception:",
    "as the arrows here indicate, the cell gathers data exclusively from the three-by-three grid of neighbors surrounding it, reading their current state. Step two is the update: based entirely on that local input, the cell applies a shared rule and alters its own internal state, changing its color and shape to become a wall, an empty space, or an active path. Importantly, these cells don't tick forward together on a synchronized global clock. They fire",
    "asynchronously, updating their states randomly and independently. This creates an unpredictable, organic rippling effect across the grid. Relying strictly on that tiny, localized perceive-and-update loop removes the need for a central processor. The vast computational work of navigating the maze is distributed entirely across the physical space of the problem itself.",
    "When you pull back and watch thousands of these microscopic loops execute at the same time, the math translates into a physical phenomenon. The cells generate a wave of exploration. Because they only understand their immediate surroundings, they don't pick a single route; they explore multiple branching paths in parallel, spilling down corridors like water seeking a drain.",
    "But because they are blind to the exit, a majority of these expanding branches will inevitably crash into dead ends. Watch the leading edge of this path hit a wall. The cells trapped at the end realize they have nowhere left to expand, and they initiate a localized pruning wave. The trapped cells turn their path states off, and then broadcast that failure backward to the neighbor directly behind them.",
    "Cell by cell, they shut down the doomed corridor, retracting the path all the way back to the last viable intersection. As the system runs, all the incorrect branches organically prune themselves and collapse. Eventually, the grid reaches a consensus, leaving a single glowing line that represents the optimal route from start to finish. The network didn't calculate a mathematical answer in a void.",
    "By flooding the space and then pruning the failures locally, it generated a visible, spatial chain of thought entirely through decentralized logic. Because this chain of thought relies entirely on that local three-by-three perception window, the actual physical dimensions of the maze do not matter to the individual cells. You can see that principle at work in this substrate scaling test. On the left is a tiny",
    "nine-by-nine grid. Researchers trained the cells on this simple environment for just three minutes. On the right, they dropped those exact same cells into a colossal two-hundred-and-one by two-hundred-and-one labyrinth. The cells executed the exact same local wave-and-prune rules they learned on the tiny board, and flawlessly solved the massive maze without requiring a single weight update or any additional learning.",
    "By decoupling the logic from a global overview, the architecture effortlessly expands to fit whatever hardware or space it is dropped into. It scales by simply tiling more cells, completely bypassing the massive data bottlenecks of centralized models. Watch what happens when a digital blast blows a hole directly through the center of an already completed path.",
    "The dormant cells sitting quietly on the edges of that new void suddenly detect a change in their local neighborhood. They wake up, reactivate their perceive-and-update loops, and automatically calculate a glowing detour bridge directly around the damage. If you punch a hole in the data flow of a centralized, globally synchronized AI, the system crashes."
]

texts_de = [
    "Kann komplexes mehrstufiges Denken allein aus winzigen Zellen entstehen, die nur mit ihren unmittelbaren Nachbarn sprechen?",
    "Forscher des Google-Teams Paradigms of Intelligence und des Mila-Instituts haben soeben bewiesen, dass Neuronale Zelluläre Automaten riesige Labyrinthe, extremes Sudoku und ARC-AGI ganz ohne globale Aufmerksamkeit lösen können. Damit verwandeln sie logisches Schließen in eine lebendige, sich selbst heilende räumliche Welle. Moderne KI basiert sonst auf globaler Aufmerksamkeit.",
    "In Systemen wie großen Sprachmodellen überwacht und kommuniziert jedes einzelne Datenelement permanent mit jedem anderen Element im Netzwerk, um ein Problem zu lösen. Diese ständige Alles-mit-Allem-Kommunikation verschlingt enorme Rechenleistung. Wenn solche Modelle für schwierigere Aufgaben wachsen, wird dieser zentrale Datentransport zum massiven Flaschenhals, der Unmengen an Energie verbraucht, um das Gesamtsystem synchron zu halten.",
    "Betrachten Sie dieses Labyrinth mit einem einzigen zentralen Knoten. Um den Ausgang zu finden, erfasst eine klassische KI-Architektur über globale Aufmerksamkeit das gesamte Spielfeld gleichzeitig und berechnet jede Wand und jeden Gang in einem einzigen synchronisierten, energieintensiven Durchlauf. Die Biologie löst räumliche Probleme völlig anders: Ein Schleimpilz auf dem Waldboden besitzt kein zentrales Gehirn, das das gesamte Gelände kartiert.",
    "Er findet Nahrung von unten nach oben, durch winzige lokale Wechselwirkungen, die kaum Energie benötigen. Um die heutigen physikalischen und energetischen Grenzen des Rechnens zu überwinden, müssen wir über diese zentralisierte Top-Down-Struktur hinausblicken. Wir müssen herausfinden, ob komplexe Logik durch lokale, dezentrale Interaktionen ausgeführt werden kann. Was Sie hier sehen, ist eine solche Alternative: ein Neuronaler Zellulärer Automat, kurz NCA.",
    "Statt eines einzigen Riesenprozessors besteht das System aus einem Gitter tausender kompakter, unabhängiger KI-Zellen, die wie ein Schwarm erwachen und kommunizieren. Es gibt kein Zentralgehirn, das diesen Schwarm steuert. Und wie dieses Diagramm zeigt, sieht keine einzelne Zelle das gesamte Labyrinth. Jede Einheit ist blind für das große Ganze und nimmt nur die acht unmittelbaren Nachbarn wahr, die sie direkt berühren. Das erzeugt ein spannendes mechanisches Rätsel.",
    "Diese Zellen besitzen keine globale Karte, keinen gemeinsamen Speicher und keine Fernkommunikation. Sie haben keinerlei Verbindung zum Ausgang und müssen sich dennoch koordinieren, um durch das gesamte Feld zu navigieren. Um zu verstehen, wie ihnen das gelingt, zoomen wir an den Startpunkt des Labyrinths und betrachten das Verhalten einer einzelnen isolierten Zelle. Jede Zelle arbeitet in einer strikten Zweischritt-Schleife. Schritt eins ist die Wahrnehmung:",
    "Wie die Pfeile zeigen, sammelt die Zelle Daten ausschließlich aus dem drei-mal-drei-Nachbarschaftsgitter um sie herum und liest deren aktuellen Zustand. Schritt zwei ist die Aktualisierung: Allein auf Basis dieses lokalen Eingangs wendet die Zelle eine gemeinsame Regel an und ändert ihren inneren Zustand, ihre Farbe und Form zu einer Wand, einem freien Feld oder einem aktiven Pfad. Entscheidend ist: Diese Zellen ticken nicht im Gleichschritt einer globalen Uhr. Sie feuern",
    "asynchron und aktualisieren ihre Zustände zufällig und unabhängig voneinander. Das erzeugt einen organischen Welleneffekt über das gesamte Gitter. Da sich das System strikt auf diese winzige lokale Wahrnehmungs- und Aktualisierungsschleife verlässt, entfällt jeder Zentralprozessor. Die gesamte Rechenarbeit der Wegfindung verteilt sich direkt über den physischen Raum des Problems selbst.",
    "Wenn man herauszoomt und tausende dieser mikroskopischen Schleifen gleichzeitig beobachtet, wird Mathematik zu einem physikalischen Phänomen. Die Zellen erzeugen eine Erkundungswelle. Da sie nur ihre unmittelbare Umgebung kennen, wählen sie nicht bloß eine einzige Route, sondern erkunden viele verzweigte Pfade parallel und strömen durch die Gänge wie Wasser auf dem Weg zum Abfluss.",
    "Weil sie jedoch blind für den Ausgang sind, prallt ein Großteil dieser wachsenden Verzweigungen unweigerlich in Sackgassen. Beobachten Sie, wie die Spitze dieses Pfades auf eine Mauer trifft. Die am Ende gefangenen Zellen merken, dass sie sich nicht weiter ausdehnen können, und lösen eine lokale Rückbauwelle aus. Sie schalten ihren Pfadzustand ab und melden diesen Fehlschlag rückwärts an den Nachbarn direkt hinter ihnen.",
    "Zelle für Zelle legen sie den aussichtslosen Gang still und ziehen den Pfad bis zur letzten funktionierenden Kreuzung zurück. Während das System läuft, stutzen sich alle falschen Abzweigungen organisch selbst zurück und fallen in sich zusammen. Schließlich erreicht das Gitter einen Konsens und hinterlässt eine einzige leuchtende Linie: die optimale Route vom Start bis zum Ziel. Das Netzwerk hat keine abstrakte Formel im luftleeren Raum gelöst.",
    "Indem es den Raum flutete und Sackgassen lokal zurückschnitt, erzeugte es eine sichtbare, räumliche Gedankenkette allein durch dezentrale Logik. Weil diese Gedankenkette ausschließlich auf dem lokalen drei-mal-drei-Sichtfenster beruht, spielt die tatsächliche Größe des Labyrinths für die einzelne Zelle überhaupt keine Rolle. Genau dieses Prinzip zeigt dieser Skalierungstest: Links sehen Sie ein winziges",
    "neun-mal-neun-Gitter. Die Forscher trainierten die Zellen in dieser einfachen Umgebung nur drei Minuten lang. Rechts setzten sie exakt dieselben Zellen in ein gewaltiges zweihunderteins-mal-zweihunderteins-Labyrinth. Die Zellen führten genau dieselben lokalen Wellen- und Rückbauregeln aus, die sie auf dem kleinen Feld gelernt hatten, und lösten das riesige Labyrinth fehlerfrei, ohne ein einziges Gewichts-Update oder zusätzliches Lernen.",
    "Durch die Entkopplung der Logik von einer globalen Übersicht wächst die Architektur mühelos mit jeder Hardware und jedem Raum mit. Sie skaliert einfach durch das Anfügen weiterer Zellen und umgeht so die gewaltigen Datenengpässe zentralisierter Modelle. Beobachten Sie nun, was passiert, wenn eine digitale Explosion ein Loch mitten in einen bereits fertigen Lösungspfad reißt.",
    "Die ruhenden Zellen am Rand dieser neuen Lücke registrieren sofort die Veränderung in ihrer direkten Nachbarschaft. Sie wachen auf, reaktivieren ihre Wahrnehmungs- und Aktualisierungsschleifen und berechnen automatisch eine leuchtende Umleitungsbrücke direkt um den Schaden herum. Reißt man hingegen ein Loch in den Datenfluss einer zentralisierten, global synchronisierten KI, stürzt das gesamte System ab."
]

texts_fr = [
    "Un raisonnement complexe en plusieurs étapes peut-il émerger uniquement de minuscules cellules qui ne parlent qu'à leurs voisines immédiates ?",
    "Des chercheurs de l'équipe Paradigms of Intelligence de Google et de Mila viennent de prouver que les automates cellulaires neuronaux peuvent résoudre d'immenses labyrinthes, des Sudokus extrêmes et le test ARC-AGI sans aucune attention globale, transformant le raisonnement en une onde spatiale vivante et autoréparatrice. L'IA moderne repose habituellement sur une architecture centrée sur l'attention globale.",
    "Dans les grands modèles de langage, chaque élément de donnée du réseau surveille et communique en permanence avec tous les autres éléments pour résoudre un problème. Cette communication constante de tous vers tous exige une puissance de calcul colossale. À mesure que ces modèles grandissent, ce mouvement centralisé des données devient un goulet d'étranglement critique, engloutissant d'immenses quantités d'énergie pour maintenir la synchronisation.",
    "Observez ce labyrinthe surplombé d'un unique nœud central. Pour trouver la sortie, une architecture d'IA traditionnelle utilise l'attention globale afin d'ingérer tout le plateau simultanément, calculant chaque mur et chaque couloir en un seul balayage synchronisé et énergivore. La biologie résout les problèmes spatiaux tout autrement : un blob explorant le sol d'une forêt n'a pas de cerveau centralisé cartographiant tout le terrain.",
    "Il trouve sa nourriture de bas en haut, grâce à de minuscules interactions locales qui consomment très peu d'énergie. Dépasser les limites physiques et énergétiques actuelles de l'informatique impose de regarder au-delà de cette structure centralisée descendante. Nous devons savoir si une logique complexe peut s'exécuter via des interactions locales et décentralisées. Ce que vous voyez ici est cette alternative : un automate cellulaire neuronal, ou NCA.",
    "Au lieu d'un unique processeur géant, le système se compose d'une grille de milliers de cellules d'IA compactes et indépendantes, qui s'éveillent et communiquent comme un essaim. Aucun cerveau maître ne dirige cet essaim. Et comme le montre ce schéma, aucune cellule ne voit le labyrinthe dans son ensemble. Chaque unité est totalement aveugle à la vue d'ensemble et ne peut observer que ses huit voisines immédiates qui la touchent. Cela pose une fascinante énigme mécanique.",
    "Ces cellules n'ont ni carte globale, ni mémoire partagée, ni communication à longue distance. Elles sont totalement coupées de la sortie, et doivent pourtant se coordonner pour traverser tout le plateau. Pour comprendre comment elles y parviennent, descendons au point de départ du labyrinthe et observons le comportement d'une seule cellule isolée. Chaque cellule fonctionne selon une boucle stricte en deux étapes. La première étape est la perception :",
    "comme l'indiquent ces flèches, la cellule recueille des données exclusivement auprès de la grille trois par trois de ses voisines immédiates, en lisant leur état actuel. La seconde étape est la mise à jour : uniquement à partir de cette entrée locale, la cellule applique une règle partagée et modifie son propre état interne, changeant de couleur et de forme pour devenir un mur, un espace vide ou un chemin actif. Point essentiel : ces cellules ne suivent pas une horloge globale synchronisée. Elles s'activent",
    "de manière asynchrone, mettant à jour leurs états de façon aléatoire et indépendante. Cela crée un effet d'ondulation organique à travers la grille. S'appuyer strictement sur cette minuscule boucle locale de perception et de mise à jour supprime le besoin d'un processeur central. L'immense travail de calcul pour naviguer dans le labyrinthe est entièrement distribué à travers l'espace physique du problème lui-même.",
    "Lorsqu'on prend du recul et qu'on observe des milliers de ces boucles microscopiques s'exécuter en même temps, les mathématiques se traduisent en un phénomène physique. Les cellules génèrent une onde d'exploration. Comme elles ne comprennent que leur voisinage immédiat, elles ne choisissent pas une route unique : elles explorent plusieurs branches en parallèle, se répandant dans les couloirs comme de l'eau cherchant un conduit.",
    "Mais comme elles sont aveugles à la sortie, la majorité de ces branches finiront inévitablement dans des impasses. Regardez l'extrémité de ce chemin heurter un mur. Les cellules piégées au bout réalisent qu'elles ne peuvent plus avancer et déclenchent une onde locale d'élagage. Elles désactivent leur état de chemin, puis transmettent cet échec à rebours à la voisine située juste derrière elles.",
    "Cellule après cellule, elles ferment le couloir condamné, rétractant le chemin jusqu'à la dernière intersection viable. Au fil de l'exécution, toutes les branches erronées s'élaguent organiquement et s'effondrent. Finalement, la grille parvient à un consensus, ne laissant qu'une unique ligne lumineuse qui représente l'itinéraire optimal du départ à l'arrivée. Le réseau n'a pas calculé une réponse abstraite dans le vide.",
    "En inondant l'espace puis en élaguant localement les échecs, il a engendré une chaîne de pensée spatiale visible, entièrement par logique décentralisée. Parce que cette chaîne de pensée repose uniquement sur cette fenêtre de perception locale de trois par trois, les dimensions physiques réelles du labyrinthe n'ont aucune importance pour chaque cellule. Ce test de mise à l'échelle du substrat l'illustre parfaitement : à gauche se trouve une minuscule",
    "grille de neuf par neuf. Les chercheurs ont entraîné les cellules dans cet environnement simple pendant seulement trois minutes. À droite, ils ont déposé exactement ces mêmes cellules dans un labyrinthe colossal de deux cent un par deux cent un. Les cellules ont exécuté les mêmes règles locales d'onde et d'élagage apprises sur le petit plateau, résolvant sans faille le labyrinthe géant sans la moindre mise à jour des poids ni apprentissage supplémentaire.",
    "En découplant la logique d'une vue globale, l'architecture s'étend sans effort pour s'adapter à n'importe quel matériel ou espace. Elle passe à l'échelle en juxtaposant simplement davantage de cellules, contournant ainsi les goulets d'étranglement des modèles centralisés. Regardez maintenant ce qui se passe lorsqu'une explosion numérique creuse un trou en plein centre d'un chemin déjà résolu.",
    "Les cellules en sommeil au bord de ce nouveau vide détectent soudain un changement dans leur voisinage local. Elles se réveillent, réactivent leurs boucles de perception et de mise à jour, et calculent automatiquement un pont de contournement lumineux tout autour de la zone endommagée. Si vous percez un tel trou dans le flux de données d'une IA centralisée et synchronisée, tout le système plante."
]

texts_ja = [
    "複雑な多段階の推論は、隣接する細胞としか会話できない微小なセルの集まりだけから創発し得るのでしょうか？",
    "Googleの「Paradigms of Intelligence」チームとMilaの研究者たちは、ニューラル・セル・オートマトン（NCA）が大域的アテンション（Global Attention）を一切使わずに巨大迷路や超高難度ナンプレ、ARC-AGIを解けることを実証し、推論を生きた自己修復する「空間的な波」へと変えました。現代のAIは通常、グローバル・アテンションという概念を中心に構築されています。",
    "大規模言語モデルのようなシステムでは、問題を解くためにネットワーク内のすべてのデータ要素が他のすべての要素を常時監視し、通信し合っています。この「全対全」の通信には莫大な計算電力が必要です。モデルがより難しい課題に対応するため巨大化するにつれ、この中央集権的なデータ移動が深刻なボトルネックとなり、システム全体の同期を保つために膨大なエネルギーを消費してしまいます。",
    "単一の中央ノードが重ねられたこちらの迷路をご覧ください。出口を見つけるため、従来のAIアーキテクチャはグローバル・アテンションを使って盤面全体を一度に取り込み、すべての壁と通路を同期された高エネルギーの一括計算で処理します。一方、生物は空間的な問題を全く異なる方法で解いています。森の床を這う粘菌（変形菌）は、地形全体を把握する中央の脳を持っていません。",
    "粘菌はごくわずかなエネルギーしか使わない微小な局所的相互作用によって、ボトムアップで餌を見つけ出します。現在のコンピューティングの物理的・エネルギー的限界を超えるには、中央集権的なトップダウン構造から脱却し、局所的で分散した相互作用によって高度な論理を実行できるかを探る必要があります。今ご覧いただいているのがその分散型アプローチ、「ニューラル・セル・オートマトン（NCA）」です。",
    "単一の巨大プロセッサの代わりに、このシステムは群れのように目覚めて通信する何千ものコンパクトで独立したAIセルのグリッドで構成されています。この群れを指揮する司令塔の脳は存在しません。そしてこの図の通り、どのセルも迷路全体を見ることはできません。各ユニットは全体像に対して完全に盲目であり、物理的に接触している周囲8マスの隣接セルだけを観察する能力しか持っていません。これが興味深い機械的パズルを生みます。",
    "これらのセルは全体地図も、共有メモリも、長距離通信手段も持っていません。出口からは完全に切り離されているにもかかわらず、どうにかして協調し、盤面全体をナビゲートしなければならないのです。その仕組みを見るため、迷路のスタート地点に降り立ち、孤立した1つのセルの振る舞いを観察してみましょう。すべてのセルは厳密な「2段階ループ」で動作します。ステップ1は「知覚（Perception）」です。",
    "矢印が示す通り、セルは周囲3×3マスの隣接セルからのみデータを集め、現在の状態を読み取ります。ステップ2は「更新（Update）」です。その局所的な入力だけに基づき、セルは共有ルールを適用して自らの内部状態を変化させ、壁・空白・あるいは有効な経路へと色や形を変えます。重要なのは、これらのセルが同期された全体クロックで一斉に動くのではないという点です。セルは",
    "非同期（ランダムかつ独立）に発火して状態を更新します。これにより、グリッド全体に予測不能で有機的なさざ波のような効果が生まれます。この微小で局所的な「知覚と更新のループ」だけに頼ることで、中央プロセッサが不要になります。迷路を解く膨大な計算作業は、問題自身の物理的な空間全体に完全に分散されるのです。",
    "視点を引いて何千ものミクロなループが同時実行される様子を見ると、数学が物理現象へと姿を変えます。セルたちは「探索の波」を生み出します。自分のすぐ周囲しか理解できないため、単一のルートを選ぶのではなく、排水口を探す水のように複数の分岐ルートを並列に探索しながら通路へと広がっていきます。",
    "しかし出口が見えないため、広がっていく分岐の大半は必然的に行き止まりへと衝突します。この経路の先端が壁にぶつかる様子を見てください。行き止まりに閉じ込められたセルは、これ以上広がる場所がないことを悟り、局所的な「剪定（プルーニング）の波」を開始します。経路状態をオフにし、すぐ後ろの隣接セルへと「失敗」を逆向きに伝達するのです。",
    "セルからセルへと行き止まりの通路を閉鎖し、最後に分岐した有効な交差点まで経路を引き戻していきます。システムが稼働するにつれ、誤った分岐はすべて有機的に剪定されて消滅します。やがてグリッド全体が合意に達し、スタートからゴールまでの最適ルートを表す一本の輝くラインだけが残ります。ネットワークは虚空の中で数式を計算したのではありません。",
    "空間を満たし、失敗した枝を局所的に刈り取ることで、完全に分散化された論理だけから目に見える「空間的な思考の連鎖（Spatial Chain of Thought）」を生み出したのです。この思考の連鎖は局所的な3×3の知覚ウィンドウのみに依存するため、迷路の物理的な大きさは個々のセルにとって無関係になります。その原理を証明するのがこちらの「空間スケーリング試験」です。左側は小さな",
    "9×9のグリッドです。研究者はこの単純な環境でセルをわずか3分間だけ学習させました。そして右側では、全く同じセルを201×201という巨大な迷路に投入しました。セルたちは小さな盤面で学んだのと同じ局所的な「波と剪定」のルールを実行し、重みの更新も追加学習も一切なしに、巨大迷路を完璧に解き明かしたのです。",
    "大域的な俯瞰から論理を切り離すことで、このアーキテクチャはどんなハードウェアや空間にも自在に拡張できます。単にセルをタイル状に並べるだけでスケールし、中央集権型モデルの巨大なデータボトルネックを完全に回避できるのです。では、すでに完成した経路の真ん中にデジタルの爆発で穴を開けると何が起きるか見てみましょう。",
    "新たな空白の縁で静かに休眠していたセルたちが、局所的な近隣の変化を瞬時に検知します。セルたちは目覚め、知覚と更新のループを再稼働させ、損傷箇所を迂回する輝くバイパス橋を自動的に計算して繋ぎ直します。もし中央集権型の同期AIのデータフローに同じような穴を開ければ、システム全体がクラッシュしてしまうでしょう。"
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

# Dubbing with local Kokoro
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

final_copy = STAGING_DIR / "The_Spatial_Chain_of_Thought_FINAL.mp4"
shutil.copy2(FINAL_VIDEO, final_copy)
L.log(f"All assets staged to {STAGING_DIR}")

localizations = {
    "de": {
        "title": "Die räumliche Gedankenkette: Logisches Denken mit Neuronalen Zellulären Automaten (Google & Mila)",
        "description": (
            "Kann komplexes mehrstufiges Denken allein aus winzigen Zellen entstehen, die nur mit ihren unmittelbaren 3x3-Nachbarn kommunizieren – ganz ohne globale Aufmerksamkeit (Global Attention) und ohne zentralen Taktgeber?\n\n"
            "In „Reasoning with Neural Cellular Automata“ (arXiv:2609.36126) stellen Forscher des Google-Teams Paradigms of Intelligence, der McGill University / Mila und der Universität Genf den Transformer-Konsens infrage, wonach logisches Schließen zwingend eine dichte Alles-mit-Allem-Vernetzung erfordert.\n\n"
            "In diesem Erklärvideo zeigen wir, wie Neuronale Zelluläre Automaten (NCAs) logische Deduktion in einen dezentralen, selbstorganisierenden räumlichen Prozess verwandeln:\n\n"
            "1. Den Flaschenhals globaler Aufmerksamkeit durchbrechen: Klassische Transformer benötigen quadratische Alles-mit-Allem-Kommunikation. NCAs arbeiten auf einem 2D-Gitter, auf dem jede Zelle nur ihre unmittelbare 3x3-Moore-Nachbarschaft wahrnimmt und sich asynchron über ein geteiltes MLP aktualisiert.\n"
            "2. 500-fache räumliche Skalierung ohne Nachtraining: Nach nur 3 Minuten Training auf winzigen 9x9-Labyrinthen erlernen NCAs einen exakten Wellenfront- und Backtracking-Algorithmus, der ohne ein einziges Gewichts-Update auf bis zu 500-mal größere Labyrinthe (201x201) generalisiert.\n"
            "3. Niche-Capped Diversity Pruning & Test-Time Scaling: Durch das Beschneiden redundanter Lösungspfade erreichen NCAs 60,3 % Pass@64 (63,0 % im Ensemble) auf ARC-AGI-1 und steigern die Genauigkeit bei Sudoku-Extreme bei gleichem FLOP-Budget von 25,6 % auf 81,7 % (bis zu 4x geringerer Rechenaufwand).\n"
            "4. Selbstheilung & dezentrale adaptive Rechenleistung: Zellen passen ihre Feuerrate anhand ihrer lokalen Konfidenz selbst an – sie ruhen in bereits gelösten Bereichen und wachen bei lokalen Schäden sofort wieder auf, um eine Umleitung um die beschädigte Stelle zu berechnen.\n\n"
            "Quelle & Referenz:\n"
            "- Etcheverry, M., Miotti, P., Sirbu, A., Schürholt, K., Drozdova, M., Ghosh, A., Agüera y Arcas, B., Manyika, J., Richards, B., & Niklasson, E. (2026). „Reasoning with Neural Cellular Automata.“ arXiv:2609.36126v1.\n"
            "- Paper-URL: https://arxiv.org/html/2609.36126v1\n\n"
            "Hinweis: KI-gestütztes Erklärvideo von The Classical Remix auf Basis veröffentlichter Forschung von Google Paradigms of Intelligence, Mila und der Universität Genf.\n\n"
            "#NeuralCellularAutomata #AIArchitecture #GoogleResearch #ARCAGI #SelfOrganizingAI #SpatialReasoning #MachineLearning #ArtificialLife #TechExplained"
        ),
        "audio": str(audio_de),
        "srt": str(srt_de),
    },
    "fr": {
        "title": "La chaîne de pensée spatiale : raisonner avec des automates cellulaires neuronaux (Google & Mila)",
        "description": (
            "Un raisonnement complexe en plusieurs étapes peut-il émerger uniquement de minuscules cellules qui ne communiquent qu'avec leurs voisines immédiates 3x3, sans aucune attention globale ni horloge centrale ?\n\n"
            "Dans « Reasoning with Neural Cellular Automata » (arXiv:2609.36126), des chercheurs de l'équipe Paradigms of Intelligence de Google, de l'Université McGill / Mila et de l'Université de Genève remettent en question le consensus des Transformers selon lequel le raisonnement exige une connectivité globale de tous vers tous.\n\n"
            "Dans cette vidéo, nous explorons comment les automates cellulaires neuronaux (NCA) transforment la déduction logique en un processus spatial décentralisé et auto-organisé :\n\n"
            "1. Briser le goulet d'étranglement de l'attention globale : Contrairement aux Transformers quadratiques, chaque cellule d'un NCA ne perçoit que son voisinage immédiat 3x3 de Moore et se met à jour de façon asynchrone.\n"
            "2. Mise à l'échelle spatiale 500x sans réentraînement : Entraînés pendant seulement 3 minutes sur de petites grilles 9x9, les NCA apprennent un algorithme exact d'expansion de front d'onde et d'élagage capable de résoudre des labyrinthes 500 fois plus grands (201x201) sans aucune mise à jour des poids.\n"
            "3. Élagage de diversité par niches (Niche-Capped Diversity Pruning) : En éliminant les trajectoires redondantes lors du calcul au moment du test, les NCA atteignent 60,3 % Pass@64 (63,0 % en ensemble) sur ARC-AGI-1 et passent de 25,6 % à 81,7 % sur Sudoku-Extreme à budget FLOP constant (jusqu'à 4x moins de calcul).\n"
            "4. Autoréparation et calcul adaptatif décentralisé : Les cellules modulent leur fréquence d'activation selon leur confiance locale, se mettant en veille sur les zones résolues et se réveillant spontanément pour contourner et réparer un dommage localisé.\n\n"
            "Source et référence :\n"
            "- Etcheverry, M., Miotti, P., Sirbu, A., Schürholt, K., Drozdova, M., Ghosh, A., Agüera y Arcas, B., Manyika, J., Richards, B., & Niklasson, E. (2026). « Reasoning with Neural Cellular Automata. » arXiv:2609.36126v1.\n"
            "- Lien arXiv : https://arxiv.org/html/2609.36126v1\n\n"
            "Divulgation : Vidéo explicative assistée par IA produite par The Classical Remix à partir des travaux publiés par Google Paradigms of Intelligence, Mila et l'Université de Genève.\n\n"
            "#NeuralCellularAutomata #AIArchitecture #GoogleResearch #ARCAGI #SelfOrganizingAI #SpatialReasoning #MachineLearning #ArtificialLife #TechExplained"
        ),
        "audio": str(audio_fr),
        "srt": str(srt_fr),
    },
    "ja": {
        "title": "空間的な思考の連鎖：ニューラル・セル・オートマトンによる分散型推論（Google & Mila）",
        "description": (
            "大域的アテンション（Global Attention）も中央クロックも一切使わず、周囲3×3の隣接セルとしか通信しない微小なセルの集まりから、複雑な多段階推論は創発し得るのでしょうか？\n\n"
            "論文『Reasoning with Neural Cellular Automata』（arXiv:2609.36126）において、Google「Paradigms of Intelligence」チーム、マギル大学／Mila、ジュネーブ大学の研究者たちは、「高度な推論には全対全の密な接続が不可欠である」というTransformer時代の常識を覆しました。\n\n"
            "本動画では、ニューラル・セル・オートマトン（NCA）がいかに論理的推論を自己組織化する空間プロセスへと変えるのかを解説します：\n\n"
            "1. グローバル・アテンションのボトルネック打破：従来のTransformerは全要素間の通信に膨大な電力を消費します。NCAは2Dグリッド上で各セルが周囲3×3（ムーア近傍）のみを知覚し、共有MLPによって非同期に状態を更新します。\n"
            "2. 追加学習なしの500倍ゼロショット空間スケーリング：小さな9×9の迷路でわずか3分間学習しただけで、NCAは波面拡大と剪定（バックトラッキング）のアルゴリズムを獲得し、重みの更新を一切行わずに500倍の巨大迷路（201×201）を完璧に解きます。\n"
            "3. ニッチ制限付き多様性プルーニングとテスト時スケーリング：重複する探索軌道を途中で刈り取ることで、ARC-AGI-1で60.3% Pass@64（アンサンブルで63.0%）を達成し、Sudoku-Extremeでは同一FLOP予算で正解率を25.6%から81.7%へと飛躍させました（最大4倍の計算量削減）。\n"
            "4. 自己修復と分散型アダプティブ計算：解決済みの領域ではセルが休眠して計算資源を節約し、経路が破壊されると周囲のセルが自律的に目覚めて迂回路を再構築します。\n\n"
            "情報源・参考文献：\n"
            "- Etcheverry, M., Miotti, P., Sirbu, A., Schürholt, K., Drozdova, M., Ghosh, A., Agüera y Arcas, B., Manyika, J., Richards, B., & Niklasson, E. (2026). \"Reasoning with Neural Cellular Automata.\" arXiv:2609.36126v1.\n"
            "- 論文URL: https://arxiv.org/html/2609.36126v1\n\n"
            "開示：The Classical RemixによるAI支援解説動画。Google Paradigms of Intelligence、Mila、ジュネーブ大学の公開研究に基づいています。\n\n"
            "#NeuralCellularAutomata #AIArchitecture #GoogleResearch #ARCAGI #SelfOrganizingAI #SpatialReasoning #MachineLearning #ArtificialLife #TechExplained"
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
L.log("Updated jobs.json with EN/DE/FR/JA localizations for NCA.")
