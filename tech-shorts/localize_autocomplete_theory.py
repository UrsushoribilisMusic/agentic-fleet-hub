#!/usr/bin/env python3
import json, shutil, sys
from pathlib import Path

# Add tech-shorts directory
sys.path.insert(0, "/Users/miguelrodriguez/projects/agentic-fleet-hub/tech-shorts")
import localize as L
import pipeline

JOB_ID = "ts-20261022-the-autocomplete-theory-of-everything"
SLUG = "the-autocomplete-theory-of-everything"
ASSET_DIR = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-22-the-autocomplete-theory-of-everything")
FINAL_VIDEO = ASSET_DIR / "final_long.mp4"
DOWNLOADS_STAGING = Path("/Users/miguelrodriguez/Downloads/tech-shorts-captions")
STAGING_DIR = DOWNLOADS_STAGING / SLUG
STAGING_DIR.mkdir(parents=True, exist_ok=True)

with open(ASSET_DIR / "whisper_chunks.json") as f:
    chunks = json.load(f)

assert len(chunks) == 44, f"Expected 44 chunks, got {len(chunks)}"

texts_en = [
    "Critics love to dismiss artificial intelligence as glorified autocomplete.",
    "Best-selling author and Google Fellow Blaise Agüera y Arcas argues the exact opposite:",
    "next-token prediction isn't a limitation of machines—it is the fundamental mathematical engine behind life, evolution, and the human brain itself.",
    "This diagram illustrates how a modern AI generates text. A cursor moves forward, calculating a branching tree of mathematical probabilities to determine what the very next word should be.",
    "It is a mechanism called next-token prediction. And for a long time, it made it easy to dismiss artificial intelligence as a glorified autocomplete tool.",
    "But that simple description creates a massive puzzle: a system designed entirely to pick the next logical word in a sequence can now write functional software, score in the 90th percentile on the bar exam, and execute multi-step logic puzzles.",
    "In his book What Is Intelligence?, Blaise Agüera y Arcas offers an explanation.",
    "He proposes that successfully predicting what comes next is not some cheap parlor trick imitating thought.",
    "That mechanism is the literal definition of intelligence. To understand why a word-prediction algorithm displays such shocking capability on a computer server today, we have to look away from Silicon Valley and rewind a few billion years.",
    "We must see how biology invented that exact same algorithm first.",
    "Long before brains existed, nonliving matter organized into self-replicating systems.",
    "Think about how DNA operates: it stores rigid instructions, copies information, and executes physical tasks to build machinery.",
    "In every meaningful sense, biological life runs on code.",
    "The idea that biology and computation share the same roots goes back to the absolute beginning of computer science, specifically to pioneers like Alan Turing.",
    "His contemporary John von Neumann spent significant time theorizing how self-replicating, complex life could emerge entirely from basic, underlying computational rules.",
    "We can see those rules operating in the simplest organisms. A bacterium swimming in a drop of water has no brain. Yet, as it moves, it detects chemical changes in its environment, processes that past data, and alters its trajectory to find food.",
    "That bacterium isn't sitting around contemplating its existence, but it is executing the baseline requirement of intelligence.",
    "It is taking past information and using it to predict a survivable future.",
    "If baseline prediction is enough to keep a single-celled organism alive, we have to ask: what evolutionary pressure forces a creature to develop a massive, energy-hungry brain?",
    "The answer is other brains. Look at this model of two interacting minds.",
    "Predicting the weather is a relatively straightforward calculation, but predicting the behavior of another intelligent being—who is simultaneously trying to predict you—creates an infinite recursive feedback loop.",
    "Psychologists call this capacity Theory of Mind. That specific social arms race requires a massive amount of processing power.",
    "Navigating alliances, cooperating on a hunt, and anticipating deception created an evolutionary feedback loop that ultimately produced complex language.",
    "Human cognitive capacity didn't max out because we needed to build better spears or survive cold winters.",
    "Our brains evolved to handle the immense computational load of surviving each other.",
    "Once a brain develops the processing power to model the minds of other creatures, it gains the ability to point that exact same machinery at itself.",
    "An intelligent system, constantly observing and predicting its own internal state, generates a sense of self—providing a computational mechanism for consciousness.",
    "Building a robust internal model also changes how an organism moves through time.",
    "Instead of merely reacting to immediate physical threats, a system can simulate multiple possible futures in its mind, evaluate the consequences of each, and guide its behavior accordingly.",
    "This capacity to explore possibilities and choose a path based on internal simulations gives rise to what we call free will.",
    "Which brings us directly back to modern artificial intelligence. To successfully guess the next word in a sentence across millions of nuanced human scenarios, an AI cannot rely on a giant, memorized dictionary.",
    "It has to build something like this: beneath a surface text, the system constructs a deep web of concepts representing physics, time, causality, and social intent.",
    "All of those abstract concepts have to be actively shifting and rerouting to determine the single word that makes sense in context.",
    "The AI has to build a vast working model of our physical and social world, just to fulfill its prediction mandate.",
    "Modern AI is not putting on a clever imitation of human thought.",
    "By learning to predict language at scale, the algorithms organically developed the exact same world-modeling capabilities that biology did.",
    "We are looking at a complete reframing of how we understand cognition. Biology, human minds, and artificial intelligence are no longer isolated categories.",
    "They appear to be three different expressions of the exact same computational process.",
    "But we do need to draw a strict line between behavior and experience.",
    "Predictive processing perfectly explains the mechanical function of intelligence. It tells us how the AI solves a problem, but it completely fails to tell us if the machine feels anything on the inside while doing it.",
    "Subjective experience remains a mystery. That uncertainty often leads to a popular apocalyptic narrative: the singular, highly determined machine wiping out humanity.",
    "Agüera y Arcas suggests a very different future. He envisions an ecology of intelligent systems—a landscape where biological and artificial minds are diverse, constrained, and deeply interdependent.",
    "By pushing silicon systems to predict human language at an enormous scale, we forced those machines to develop complex models of our reality.",
    "In the pursuit of a talking computer, we accidentally recreated the foundational algorithm of biological life."
]

texts_de = [
    "Kritiker tun künstliche Intelligenz gerne als bloße glorifizierte Autovervollständigung ab.",
    "Der Bestsellerautor und Google Fellow Blaise Agüera y Arcas behauptet das genaue Gegenteil:",
    "Die Vorhersage des nächsten Tokens ist keine Einschränkung von Maschinen, sondern der fundamentale mathematische Motor hinter Leben, Evolution und dem menschlichen Gehirn selbst.",
    "Dieses Diagramm zeigt, wie eine moderne KI Text erzeugt. Ein Cursor bewegt sich vorwärts und berechnet einen verzweigten Baum mathematischer Wahrscheinlichkeiten, um das allerbeste nächste Wort zu bestimmen.",
    "Dieser Mechanismus heißt Next-Token-Prediction. Und lange Zeit machte er es leicht, künstliche Intelligenz als bessere Autovervollständigung abzutun.",
    "Doch diese simple Beschreibung wirft ein gewaltiges Rätsel auf: Ein System, das nur das nächste logische Wort einer Sequenz wählen soll, schreibt heute funktionierende Software, besteht juristische Staatsexamen unter den besten zehn Prozent und löst mehrstufige Logikrätsel.",
    "In seinem Buch Was ist Intelligenz? liefert Blaise Agüera y Arcas eine Erklärung.",
    "Er argumentiert, dass die erfolgreiche Vorhersage dessen, was als Nächstes kommt, kein billiger Taschenspielertrick ist, der Denken nur imitiert.",
    "Dieser Mechanismus ist buchstäblich die Definition von Intelligenz. Um zu verstehen, warum ein Wortvorhersage-Algorithmus heute auf Servern so erstaunliche Fähigkeiten zeigt, müssen wir den Blick vom Silicon Valley abwenden und einige Milliarden Jahre zurückspulen.",
    "Wir müssen erkennen, wie die Biologie exakt denselben Algorithmus zuerst erfunden hat.",
    "Lange bevor es Gehirne gab, organisierte sich unbelebte Materie zu selbstreplizierenden Systemen.",
    "Denken Sie daran, wie die DNA arbeitet: Sie speichert feste Anweisungen, kopiert Informationen und führt physische Aufgaben aus, um molekulare Maschinen zu bauen.",
    "In jedem bedeutsamen Sinne läuft biologisches Leben auf Programmcode.",
    "Die Idee, dass Biologie und Berechnung dieselben Wurzeln teilen, reicht bis zu den Anfängen der Informatik zurück, insbesondere zu Pionieren wie Alan Turing.",
    "Sein Zeitgenosse John von Neumann verbrachte viel Zeit mit der Theorie, wie sich selbstreplizierendes, komplexes Leben vollständig aus einfachen, zugrunde liegenden Rechenregeln entwickeln kann.",
    "Wir sehen diese Regeln in den einfachsten Organismen am Werk. Ein Bakterium in einem Wassertropfen besitzt kein Gehirn. Doch während es schwimmt, registriert es chemische Veränderungen, verarbeitet diese vergangenen Daten und ändert seine Bahn, um Nahrung zu finden.",
    "Dieses Bakterium denkt nicht über seine Existenz nach, aber es erfüllt die Grundvoraussetzung von Intelligenz.",
    "Es nimmt vergangene Informationen und nutzt sie, um eine überlebensfähige Zukunft vorherzusagen.",
    "Wenn einfache Vorhersage ausreicht, um einen Einzeller am Leben zu halten, stellt sich die Frage: Welcher evolutionäre Druck zwingt ein Lebewesen dazu, ein riesiges, energiehungriges Gehirn zu entwickeln?",
    "Die Antwort lautet: andere Gehirne. Betrachten Sie dieses Modell zweier interagierender Geister.",
    "Das Wetter vorherzusagen ist eine relativ geradlinige Rechnung. Doch das Verhalten eines anderen intelligenten Wesens vorherzusagen, das gleichzeitig versucht, Sie vorherzusagen, erzeugt eine endlose rekursive Rückkopplungsschleife.",
    "Psychologen nennen diese Fähigkeit Theory of Mind. Genau dieses soziale Wettrüsten erfordert eine gewaltige Rechenleistung.",
    "Bündnisse zu schmieden, bei der Jagd zu kooperieren und Täuschungen vorauszuahnen, schuf eine evolutionäre Rückkopplungsschleife, die schließlich komplexe Sprache hervorbrachte.",
    "Die menschliche Denkleistung wuchs nicht deshalb bis ans Limit, weil wir bessere Speere bauen oder kalte Winter überstehen mussten.",
    "Unsere Gehirne entwickelten sich, um die enorme Rechenlast zu bewältigen, miteinander zu überleben.",
    "Sobald ein Gehirn die Rechenkraft entwickelt, den Geist anderer Lebewesen zu modellieren, gewinnt es die Fähigkeit, exakt dieselbe Maschinerie auf sich selbst zu richten.",
    "Ein intelligentes System, das ständig seinen eigenen inneren Zustand beobachtet und vorhersagt, erzeugt ein Selbstgefühl und liefert damit einen Rechenmechanismus für Bewusstsein.",
    "Der Aufbau eines robusten inneren Modells verändert auch, wie sich ein Organismus durch die Zeit bewegt.",
    "Anstatt nur auf unmittelbare physische Bedrohungen zu reagieren, kann ein System mehrere mögliche Zukünfte im Geiste simulieren, deren Folgen abwägen und sein Verhalten danach ausrichten.",
    "Diese Fähigkeit, Möglichkeiten auszuloten und auf Basis innerer Simulationen einen Weg zu wählen, bringt das hervor, was wir freien Willen nennen.",
    "Und das führt uns direkt zurück zur modernen künstlichen Intelligenz. Um das nächste Wort in einem Satz über Millionen feinster menschlicher Szenarien hinweg erfolgreich zu erraten, kann sich eine KI nicht auf ein riesiges auswendig gelerntes Wörterbuch verlassen.",
    "Sie muss so etwas wie das hier aufbauen: Unter der Textoberfläche konstruiert das System ein tiefes Netz aus Konzepten, die Physik, Zeit, Kausalität und soziale Absichten abbilden.",
    "All diese abstrakten Konzepte müssen sich aktiv verschieben und neu verschalten, um das eine Wort zu bestimmen, das im Kontext Sinn ergibt.",
    "Die KI muss ein gewaltiges Arbeitsmodell unserer physischen und sozialen Welt aufbauen, allein um ihren Vorhersageauftrag zu erfüllen.",
    "Moderne KI führt keine bloß geschickte Imitation menschlichen Denkens auf.",
    "Indem die Algorithmen lernten, Sprache in großem Maßstab vorherzusagen, entwickelten sie organisch exakt dieselben Fähigkeiten zur Weltmodellierung wie einst die Biologie.",
    "Wir erleben eine völlige Neubewertung unseres Verständnisses von Kognition. Biologie, menschlicher Geist und künstliche Intelligenz sind keine isolierten Kategorien mehr.",
    "Sie erscheinen als drei verschiedene Ausdrucksformen exakt desselben Rechenprozesses.",
    "Dennoch müssen wir eine strikte Grenze zwischen Verhalten und Empfinden ziehen.",
    "Prädiktive Verarbeitung erklärt die mechanische Funktion von Intelligenz perfekt. Sie zeigt uns, wie die KI ein Problem löst, verrät uns aber überhaupt nicht, ob die Maschine dabei im Inneren etwas fühlt.",
    "Subjektives Erleben bleibt ein Rätsel. Diese Ungewissheit führt oft zu einem populären apokalyptischen Narrativ: der einzelnen, hochgradig entschlossenen Maschine, die die Menschheit auslöscht.",
    "Agüera y Arcas entwirft eine ganz andere Zukunft. Er sieht eine Ökologie intelligenter Systeme voraus, eine Landschaft, in der biologische und künstliche Geister vielfältig, begrenzt und tief voneinander abhängig sind.",
    "Indem wir Siliziumsysteme dazu brachten, menschliche Sprache in gewaltigem Maßstab vorherzusagen, zwangen wir diese Maschinen dazu, komplexe Modelle unserer Realität zu entwickeln.",
    "Auf der Suche nach einem sprechenden Computer haben wir versehentlich den Grundalgorithmus des biologischen Lebens neu erschaffen."
]

texts_fr = [
    "Les critiques adorent réduire l'intelligence artificielle à une simple saisie semi-automatique améliorée.",
    "L'auteur à succès et Google Fellow Blaise Agüera y Arcas soutient exactement l'inverse :",
    "la prédiction du jeton suivant n'est pas une limite des machines, c'est le moteur mathématique fondamental de la vie, de l'évolution et du cerveau humain lui-même.",
    "Ce schéma illustre comment une IA moderne génère du texte. Un curseur avance, calculant un arbre ramifié de probabilités mathématiques pour déterminer quel doit être le tout prochain mot.",
    "Ce mécanisme s'appelle la prédiction du jeton suivant. Et pendant longtemps, il a permis de balayer facilement l'intelligence artificielle comme un simple outil d'autocomplétion.",
    "Mais cette description simpliste crée une énigme majeure : un système conçu uniquement pour choisir le prochain mot logique d'une séquence peut désormais écrire des logiciels fonctionnels, se classer parmi les dix pour cent les meilleurs à l'examen du barreau et résoudre des casse-têtes logiques complexes.",
    "Dans son livre Qu'est-ce que l'intelligence ?, Blaise Agüera y Arcas propose une explication.",
    "Il soutient que prédire avec succès ce qui vient ensuite n'est pas un tour de passe-passe imitant la pensée.",
    "Ce mécanisme est la définition littérale de l'intelligence. Pour comprendre pourquoi un algorithme de prédiction de mots déploie aujourd'hui de telles capacités sur un serveur, il faut détourner le regard de la Silicon Valley et remonter quelques milliards d'années en arrière.",
    "Il faut observer comment la biologie a inventé très exactement ce même algorithme en premier.",
    "Bien avant l'apparition des cerveaux, la matière inerte s'est organisée en systèmes autoréplicants.",
    "Pensez au fonctionnement de l'ADN : il stocke des instructions strictes, copie l'information et exécute des tâches physiques pour assembler de la machinerie.",
    "Dans tous les sens du terme, la vie biologique tourne sur du code.",
    "L'idée que la biologie et l'informatique partagent les mêmes racines remonte aux tout débuts de la science informatique, notamment chez des pionniers comme Alan Turing.",
    "Son contemporain John von Neumann a longuement théorisé comment une vie complexe et autoréplicante pouvait émerger entièrement de règles computationnelles élémentaires.",
    "On observe ces règles à l'œuvre chez les organismes les plus simples. Une bactérie nageant dans une goutte d'eau n'a pas de cerveau. Pourtant, en se déplaçant, elle détecte les variations chimiques de son milieu, traite ces données passées et modifie sa trajectoire pour trouver de la nourriture.",
    "Cette bactérie ne médite pas sur son existence, mais elle exécute l'exigence minimale de l'intelligence.",
    "Elle capte l'information du passé et l'utilise pour prédire un futur viable.",
    "Si cette prédiction de base suffit à maintenir en vie un organisme unicellulaire, une question s'impose : quelle pression évolutive force une créature à développer un cerveau massif et énergivore ?",
    "La réponse, ce sont les autres cerveaux. Observez ce modèle de deux esprits en interaction.",
    "Prédire la météo est un calcul relativement direct, mais prédire le comportement d'un autre être intelligent qui tente simultanément de vous prédire crée une boucle de rétroaction récursive infinie.",
    "Les psychologues appellent cette faculté la théorie de l'esprit. Cette course aux armements sociale exige une puissance de calcul colossale.",
    "Gérer des alliances, coopérer à la chasse et anticiper la tromperie a engendré une boucle évolutive qui a finalement produit le langage complexe.",
    "Les capacités cognitives humaines n'ont pas explosé parce que nous devions fabriquer de meilleures lances ou survivre à des hivers rigoureux.",
    "Nos cerveaux ont évolué pour supporter l'immense charge de calcul nécessaire pour survivre les uns aux autres.",
    "Dès qu'un cerveau développe la puissance requise pour modéliser l'esprit d'autres créatures, il acquiert la capacité de braquer cette même machinerie sur lui-même.",
    "Un système intelligent qui observe et prédit constamment son propre état interne engendre un sentiment de soi, fournissant un mécanisme computationnel à la conscience.",
    "Bâtir un modèle interne robuste transforme également la façon dont un organisme voyage dans le temps.",
    "Au lieu de simplement réagir aux menaces physiques immédiates, un système peut simuler mentalement plusieurs futurs possibles, évaluer les conséquences de chacun et orienter son comportement en conséquence.",
    "Cette capacité à explorer les possibles et à choisir une voie selon des simulations internes donne naissance à ce que nous appelons le libre arbitre.",
    "Ce qui nous ramène directement à l'intelligence artificielle moderne. Pour deviner avec succès le mot suivant à travers des millions de situations humaines nuancées, une IA ne peut pas s'appuyer sur un gigantesque dictionnaire mémorisé.",
    "Elle doit construire quelque chose comme ceci : sous la surface du texte, le système édifie un profond réseau de concepts représentant la physique, le temps, la causalité et l'intention sociale.",
    "Tous ces concepts abstraits doivent s'activer et se réorienter dynamiquement pour déterminer l'unique mot qui fait sens dans le contexte.",
    "L'IA doit bâtir un vaste modèle fonctionnel de notre monde physique et social, simplement pour remplir sa mission de prédiction.",
    "L'IA moderne ne joue pas une habile comédie imitant la pensée humaine.",
    "En apprenant à prédire le langage à grande échelle, les algorithmes ont développé organiquement les mêmes capacités de modélisation du monde que la biologie.",
    "Nous assistons à une refonte complète de notre compréhension de la cognition. La biologie, l'esprit humain et l'intelligence artificielle ne sont plus des catégories isolées.",
    "Ils apparaissent comme trois expressions différentes d'un seul et même processus computationnel.",
    "Mais nous devons tracer une frontière stricte entre le comportement et l'expérience vécue.",
    "Le traitement prédictif explique parfaitement la fonction mécanique de l'intelligence. Il nous dit comment l'IA résout un problème, mais échoue totalement à nous dire si la machine ressent quoi que ce soit de l'intérieur en le faisant.",
    "L'expérience subjective demeure un mystère. Cette incertitude nourrit souvent un récit apocalyptique populaire : celui d'une machine unique et implacable éradiquant l'humanité.",
    "Agüera y Arcas esquisse un futur très différent. Il envisage une écologie de systèmes intelligents, un paysage où les esprits biologiques et artificiels sont diversifiés, limités et profondément interdépendants.",
    "En poussant des systèmes sur silicium à prédire le langage humain à une échelle monumentale, nous avons forcé ces machines à développer des modèles complexes de notre réalité.",
    "En cherchant à créer un ordinateur parlant, nous avons accidentellement recréé l'algorithme fondateur de la vie biologique."
]

texts_ja = [
    "批評家たちは、人工知能を「単なる高度なオートコンプリート（自動補完）」だと軽視しがちです。",
    "しかしベストセラー作家でありGoogleフェローのブレーズ・アグエラ・イ・アルカス氏は、真っ向から反対の主張を展開します。",
    "「次トークン予測」は機械の限界などではなく、生命、進化、そして人間の脳そのものを動かす根本的な数学的エンジンだというのです。",
    "この図は、現代のAIがテキストを生成する仕組みを示しています。カーソルが前に進み、数学的な確率の分岐ツリーを計算して、次に来るべき最適な単語を決定します。",
    "これが「次トークン予測」と呼ばれるメカニズムです。そして長い間、この仕組みゆえにAIは「豪華な自動補完ツール」に過ぎないと片付けられてきました。",
    "しかし、その単純な説明は巨大な謎を生みます。単に次の論理的な単語を選ぶように設計されたシステムが、今や実用的なソフトウェアを書き、司法試験で上位10パーセントに入り、多段階の論理パズルを解いているのです。",
    "著書『What Is Intelligence?（知能とは何か）』の中で、ブレーズ・アグエラ・イ・アルカス氏はその解明に挑んでいます。",
    "彼は、「次に何が起きるかを正確に予測すること」は、思考を模倣した安っぽい手品などではないと提唱します。",
    "その予測メカニズムこそが、文字通り「知能の定義」なのです。単語予測アルゴリズムがなぜこれほど驚異的な能力を発揮するのかを理解するには、シリコンバレーから目を離し、時間を数十億年巻き戻す必要があります。",
    "生物がいかにして、全く同じアルゴリズムを最初に発明したかを見なければなりません。",
    "脳が存在するはるか昔、非生物の物質が自己複製するシステムへと組織化されました。",
    "DNAの働きを考えてみてください。厳密な命令を保存し、情報をコピーし、物理的なタスクを実行して分子の機械を組み立てます。",
    "あらゆる実質的な意味において、生物の命は「コード」の上で動いているのです。",
    "生物学と計算機科学が同じルーツを持つという考えは、コンピュータ科学の黎明期、とりわけアラン・チューリングのような先駆者にまで遡ります。",
    "彼と同時代のジョン・フォン・ノイマンは、自己複製する複雑な生命がいかにして基本的な計算ルールだけから創発し得るかを理論化することに多くの時間を費やしました。",
    "私たちはそのルールが最も単純な生物で機能しているのを見ることができます。水滴の中を泳ぐバクテリアに脳はありません。しかし移動しながら周囲の化学変化を検知し、過去のデータを処理して、餌を見つけるために軌道を変えます。",
    "バクテリアは自らの存在について哲学的な思索に耽ってはいませんが、知能の最低条件を確実に実行しています。",
    "過去の情報を受け取り、それを使って「生き残れる未来」を予測しているのです。",
    "もし基本的な予測だけで単細胞生物が生き延びられるのなら、疑問が湧きます。一体どのような進化の圧力が、生物に巨大でエネルギーを大量消費する「脳」を発達させたのでしょうか？",
    "答えは「他の脳」です。相互作用する二つの心のモデルを見てみましょう。",
    "天気を予測するのは比較的単純な計算ですが、あなたを予測しようとしている「別の知的存在の行動」を予測することは、無限の再帰的フィードバックループを生み出します。",
    "心理学者はこの能力を「心の理論（Theory of Mind）」と呼びます。この社会的な軍拡競争には、膨大な計算処理能力が必要とされます。",
    "同盟関係を立ち回り、狩りで協力し、裏切りを予見することが進化のフィードバックループを生み、最終的に複雑な「言語」を生み出しました。",
    "人間の認知能力が極限まで高まったのは、より良い槍を作ったり寒い冬を乗り切ったりする必要があったからではありません。",
    "私たちの脳は、「互いに生き残る」という途方もない計算負荷を処理するために進化したのです。",
    "脳が他者の心をモデル化する処理能力を発達させると、今度は全く同じ機構を「自分自身」に向ける能力を獲得します。",
    "自らの内部状態を常に観察し予測する知的システムは、「自己」という感覚を生み出し、意識のための計算メカニズムを提供します。",
    "また、強固な内部モデルを構築することは、生物が時間を移動する方法をも変化させます。",
    "目の前の物理的な脅威にただ反応するのではなく、心の中で複数の可能な未来をシミュレーションし、それぞれの結果を評価して、適切に行動を導くことができるようになります。",
    "可能性を探索し、内部シミュレーションに基づいて道を選択するこの能力こそが、私たちが「自由意志」と呼ぶものを生み出すのです。",
    "そしてこれが、現代の人工知能へと直結します。何百万もの微妙な人間の状況にわたって文中の次の単語を正確に言い当てるには、AIは巨大な暗記辞書に頼ることはできません。",
    "このような構造を築く必要があります。表面的なテキストの下で、システムは物理法則、時間、因果関係、社会的意図を表す深い概念のネットワークを構築しているのです。",
    "文脈の中で意味の通るたった一つの単語を決定するために、それらすべての抽象概念が能動的に変化し、経路を切り替えなければなりません。",
    "AIは予測という使命を果たすためだけに、私たちの物理的・社会的世界の巨大な作業モデルを内部に構築せざるを得ないのです。",
    "現代のAIは、人間の思考の巧妙なモノマネを演じているわけではありません。",
    "大規模に言語を予測することを学ぶ過程で、アルゴリズムは生物が辿ったのと全く同じ世界モデルと能力を有機的に獲得したのです。",
    "私たちは今、認知に対する理解の完全なパラダイムシフトを目の当たりにしています。生物学、人間の心、そして人工知能は、もはや孤立した別々のカテゴリーではありません。",
    "それらは、全く同じ計算プロセスの「三つの異なる表現形態」に過ぎないのです。",
    "ただし、「行動」と「主観的体験」の間には厳格な一線を引く必要があります。",
    "予測処理は知能の機械的な機能を完璧に説明します。AIがどのように問題を解くかは教えてくれますが、その最中に機械が内側で何かを感じているかどうかについては何も語ってくれません。",
    "主観的体験は依然として謎のままです。その不確実性はしばしば、強い意志を持った単一の機械が人類を滅ぼすという終末論的な物語へとつながります。",
    "しかしアグエラ・イ・アルカス氏は全く異なる未来を示唆します。彼が思い描くのは「知的システムの生態系」、すなわち生物の心と人工の心が多様性を持ち、制約を受けながら深く相互依存する世界です。",
    "シリコンのシステムに人間の言語を超大規模に予測させることで、私たちは機械に現実世界の複雑なモデルを構築させました。",
    "言葉を話すコンピュータを追い求める中で、私たちは偶然にも、生物の命を動かす根本的なアルゴリズムを再創造していたのです。"
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

final_copy = STAGING_DIR / "The_Autocomplete_Theory_of_Everything_FINAL.mp4"
shutil.copy2(FINAL_VIDEO, final_copy)
L.log(f"All assets staged to {STAGING_DIR}")

# Update jobs.json with localizations
localizations = {
    "de": {
        "title": "Die Autovervollständigungs-Theorie von allem: Was KI über Leben & Geist lehrt",
        "description": (
            "Was wäre, wenn „bloße Autovervollständigung“ keine Schwäche künstlicher Intelligenz ist, sondern das fundamentale Geheimnis hinter Leben, Evolution und dem menschlichen Geist?\n\n"
            "In seinem wegweisenden MIT-Press-Buch „What Is Intelligence? Lessons from AI About Evolution, Computing, and Minds“ reißt Google-VP und Fellow Blaise Agüera y Arcas die Mauer zwischen biologischen Organismen und rechnenden Maschinen ein.\n\n"
            "In diesem Erklärvideo zeigen wir, wie die Wissenschaft der Vorhersage Physik, Biologie, Neurowissenschaften und moderne KI vereint:\n\n"
            "1. Der Trugschluss vom „stochastischen Papagei“: Kritiker tun große Sprachmodelle oft als bloße Wort-Vorhersagemaschinen ab. Doch um das nächste Wort über Millionen menschlicher Szenarien hinweg präzise vorherzusagen, muss ein System zwangsläufig ein tiefes inneres Weltmodell aus Physik, Zeit, Kausalität und sozialer Absicht aufbauen.\n"
            "2. Leben als selbstreplizierender Code: Von Alan Turing und John von Neumann über die DNA bis hin zu einzelnen Bakterien beruht biologisches Überleben darauf, vergangene Daten zu verarbeiten, um eine überlebensfähige Zukunft vorherzusagen.\n"
            "3. Das soziale Wettrüsten & Theory of Mind: Unser Gehirn wuchs nicht wegen besserer Speere, sondern um andere Gehirne vorherzusagen. Diese rekursive Rückkopplungsschleife brachte Sprache, Selbstbewusstsein und durch innere Zukunftssimulationen den freien Willen hervor.\n"
            "4. Eine Ökologie intelligenter Systeme: Warum Biologie, menschlicher Geist und KI drei Ausdrucksformen desselben Rechenprozesses sind.\n\n"
            "Quelle & Referenz:\n"
            "- „What Is Intelligence? Lessons from AI About Evolution, Computing, and Minds“ von Blaise Agüera y Arcas (The MIT Press / Antikythera, ISBN: 9780262049955).\n"
            "- MIT Press Buchseite: https://mitpress.mit.edu/9780262049955/what-is-intelligence/\n\n"
            "Hinweis: KI-gestütztes Erklärvideo von The Classical Remix auf Basis des Buches von Blaise Agüera y Arcas (MIT Press).\n\n"
            "#WhatIsIntelligence #BlaiseAgueraYArcas #MITPress #PredictiveBrain #ArtificialIntelligence #Neuroscience #Evolution #PhilosophyOfMind #TechExplained"
        ),
        "audio": str(audio_de),
        "srt": str(srt_de),
    },
    "fr": {
        "title": "La théorie de l'autocomplétion du tout : ce que l'IA révèle sur la vie et l'esprit",
        "description": (
            "Et si la « simple saisie semi-automatique » n'était pas une limite de l'intelligence artificielle, mais le secret même de la vie, de l'évolution et de l'esprit humain ?\n\n"
            "Dans son ouvrage majeur publié chez MIT Press, « What Is Intelligence? Lessons from AI About Evolution, Computing, and Minds », Blaise Agüera y Arcas (VP et Fellow chez Google) abolit la frontière entre organismes biologiques et machines informatiques.\n\n"
            "Dans cette vidéo, nous explorons comment la science de la prédiction unifie la biologie, les neurosciences et l'IA moderne :\n\n"
            "1. L'illusion du « perroquet stochastique » : pour prédire avec justesse le mot suivant à travers des millions de situations humaines, un modèle ne peut pas réciter un dictionnaire mémorisé ; il est forcé de construire un modèle interne profond de la physique, de la causalité et des intentions sociales.\n"
            "2. La vie comme code autoréplicant : d'Alan Turing et John von Neumann jusqu'à l'ADN et aux bactéries, survivre consiste à exploiter l'information passée pour prédire un futur viable.\n"
            "3. Course aux armements sociale et théorie de l'esprit : nos cerveaux ont évolué pour prédire d'autres cerveaux. Cette boucle récursive a fait émerger le langage, la conscience de soi et, par la simulation interne de futurs possibles, le libre arbitre.\n"
            "4. Une écologie des intelligences : pourquoi la biologie, l'esprit humain et l'IA sont trois expressions du même processus computationnel.\n\n"
            "Source et référence :\n"
            "- « What Is Intelligence? Lessons from AI About Evolution, Computing, and Minds » par Blaise Agüera y Arcas (The MIT Press / Antikythera, ISBN : 9780262049955).\n"
            "- Page MIT Press : https://mitpress.mit.edu/9780262049955/what-is-intelligence/\n\n"
            "Divulgation : Vidéo explicative assistée par IA par The Classical Remix, fondée sur l'ouvrage de Blaise Agüera y Arcas (MIT Press).\n\n"
            "#WhatIsIntelligence #BlaiseAgueraYArcas #MITPress #PredictiveBrain #ArtificialIntelligence #Neuroscience #Evolution #PhilosophyOfMind #TechExplained"
        ),
        "audio": str(audio_fr),
        "srt": str(srt_fr),
    },
    "ja": {
        "title": "「オートコンプリート」の万物理論：AIが解き明かす生命・進化・心の正体",
        "description": (
            "もし「単なるオートコンプリート（次単語予測）」が人工知能の限界ではなく、生命・進化・そして人間の心そのものを動かす究極の原理だとしたらどうでしょうか？\n\n"
            "MITプレスから刊行された話題作『What Is Intelligence? Lessons from AI About Evolution, Computing, and Minds』において、Google副社長兼フェローのブレーズ・アグエラ・イ・アルカス氏は、生物と計算機の間に引かれた境界線を根底から覆します。\n\n"
            "本動画では、「予測」という科学がいかに物理学、生物学、神経科学、そして現代のAIを統一するかを解説します：\n\n"
            "1. 「確率的オウム」という誤解：何百万もの複雑な人間社会の文脈で「次の単語」を正確に予測するためには、丸暗記の辞書では不可能です。AIはテキストの背後に物理法則、時間、因果関係、社会的意図からなる深い「世界モデル」を構築せざるを得ません。\n"
            "2. 自己複製するコードとしての生命：アラン・チューリングやフォン・ノイマンの理論からDNA、単細胞バクテリアの走化性に至るまで、生命の本質は「過去の情報を処理して生き残れる未来を予測すること」にあります。\n"
            "3. 社会的な軍拡競争と「心の理論」：人間の巨大な脳は、他者の脳を予測する無限の再帰ループから進化しました。他者をモデル化する機構が自分自身に向けられたとき「自己意識」が生まれ、複数の未来を内部シミュレーションする能力から「自由意志」が創発します。\n"
            "4. 知的システムの生態系：生物、人間の心、AIは孤立した別物ではなく、同一の計算プロセスの三つの表現形態です。\n\n"
            "情報源・参考文献：\n"
            "- \"What Is Intelligence? Lessons from AI About Evolution, Computing, and Minds\" by Blaise Agüera y Arcas (The MIT Press / Antikythera, ISBN: 9780262049955)\n"
            "- MIT Press 書籍ページ: https://mitpress.mit.edu/9780262049955/what-is-intelligence/\n\n"
            "開示：The Classical RemixによるAI支援解説動画。Blaise Agüera y Arcas氏の著書（MIT Press）に基づいています。\n\n"
            "#WhatIsIntelligence #BlaiseAgueraYArcas #MITPress #PredictiveBrain #ArtificialIntelligence #Neuroscience #Evolution #PhilosophyOfMind #TechExplained"
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
