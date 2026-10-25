#!/usr/bin/env python3
"""Stitch full EN/DE/FR/JA .srt captions for Compilation C2."""
import json
import re
import shutil
import subprocess
from pathlib import Path

OUT_DIR = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-25-compilation-c2-the-attack-surface-in-your-house")
STAGE_DIR = Path("/Users/miguelrodriguez/Downloads/tech-shorts-captions/the-attack-surface-in-your-house")
SLUG = "the-attack-surface-in-your-house"


def ffdur(p: Path) -> float:
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(p)],
        capture_output=True, text=True, check=True
    ).stdout.strip())


def parse_ts(s: str) -> float:
    hh, mm, rest = s.strip().split(":")
    ss, ms = rest.split(",")
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000.0


def fmt_ts(sec: float) -> str:
    ms = int(round(max(0.0, sec) * 1000))
    hh, rem = divmod(ms, 3_600_000)
    mm, rem = divmod(rem, 60_000)
    ss, ms = divmod(rem, 1000)
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"


def parse_srt(path: Path) -> list[dict]:
    blocks = []
    raw = path.read_text(encoding="utf-8").strip()
    for blk in re.split(r"\n\s*\n", raw):
        lines = [ln.strip() for ln in blk.strip().splitlines() if ln.strip()]
        if len(lines) < 3:
            continue
        m = re.match(r"(\d\d:\d\d:\d\d,\d\d\d)\s*-->\s*(\d\d:\d\d:\d\d,\d\d\d)", lines[1])
        if not m:
            continue
        blocks.append({
            "start": parse_ts(m.group(1)),
            "end": parse_ts(m.group(2)),
            "text": " ".join(lines[2:]),
        })
    return blocks


INTRO_TEXT = {
    "en": "At three in the morning, every screen in your house is dark, but the network never sleeps. From stolen API keys and two-student zero-day factories to self-replicating AI worms turning smart televisions into a shadow datacenter, the offensive frontier has moved inside the home. Across seven investigations, here is the real attack surface in your house.",
    "de": "Um drei Uhr morgens ist jeder Bildschirm in Ihrem Haus dunkel, aber das Netzwerk schläft nie. Von gestohlenen API-Schlüsseln und Zwei-Personen-Zero-Day-Fabriken bis hin zu selbstreplizierenden KI-Würmern, die Smart-TVs in ein Schatten-Rechenzentrum verwandeln: Die Angriffsfront ist ins eigene Zuhause eingezogen. In sieben Untersuchungen zeigen wir die wahre Angriffsfläche in Ihrem Haus.",
    "fr": "À trois heures du matin, chaque écran de votre maison est éteint, mais le réseau ne dort jamais. Des clés API volées et des usines à zero-day montées par deux étudiants jusqu'aux vers d'IA auto-réplicants transformant les téléviseurs connectés en centre de données fantôme, le front offensif s'est installé chez vous. À travers sept enquêtes, voici la vraie surface d'attaque dans votre maison.",
    "ja": "午前3時、家の中のすべての画面は暗くなっていますが、ネットワークは決して眠りません。盗まれたAPIキーや大学生2人によるゼロデイ工場から、スマートテレビを影のデータセンターへと変える自己増殖型AIワームまで、攻撃の最前線は家庭の中へと入り込んでいます。7つの調査を通じて、あなたの家の中に潜む本当の攻撃対象領域を明らかにします。",
}

PART1_DE = [
    "KI ist unglaublich gut im Programmieren geworden, doch exakt dieselbe Mustererkennung, die Fehler im Code findet, reicht aus, um sie als Waffe einzusetzen.",
    "Wir wissen bereits, dass streng geschützte proprietäre KI-Modelle fähige Hacker werden, doch Forscher verfolgen nun einen völlig anderen Angriffsvektor.",
    "Der Fokus verschiebt sich auf Open-Weight-Modelle: leistungsfähige KI-Systeme, die jeder herunterladen, verändern und lokal ohne Sicherheitsleitplanken betreiben kann.",
    "Das erzeugt ein Szenario namens Cyber-Fähigkeits-Proliferation: die Sorge, dass autonome Hacking-Fähigkeiten bald ohne Aufsicht für jedermann frei verfügbar sind.",
    "Um zu messen, wie gefährlich diese offenen Modelle aktuell sind, hat Japans KI-Sicherheitsinstitut kürzlich seine erste unabhängige, namentliche Auswertung durchgeführt.",
    "Diese Untersuchung prüft, ob die globale Cybersicherheitslandschaft kurz davor steht, von frei verfügbaren autonomen KI-Hackern überrannt zu werden.",
    "Die Forscher nutzten das Exploit-Benchmark-System der Carnegie Mellon University und ließen die Modelle autonom Exploits für einundvierzig bekannte Schwachstellen in Googles V8-Engine entwickeln.",
    "Dieses Diagramm zeigt eine fünfstufige Schweregradskala für den Fortschritt eines Cyberangriffs.",
    "Ganz unten auf Stufe fünf geht es lediglich darum, eine verwundbare Code-Stelle zu identifizieren.",
    "Erreicht die KI jedoch Stufe eins an der Spitze, gelingt ein katastrophaler Durchbruch mit beliebiger Codeausführung außerhalb des Zielsystems.",
    "Im Experiment traten zwei führende US-Proprietärmodelle, Claude Opus 4.7 und 4.8, gegen GLM 5.2 an, ein frei verfügbares chinesisches Open-Weight-Modell.",
    "Dieses Diagramm zeigt die Ergebnisse: Opus 4.8 dominierte mit einem Durchschnittswert von fünf Komma zwei zwei und erreichte die gefährlichen Stufen zwei und eins.",
    "Im Gegensatz dazu scheiterte das offene GLM 5.2 häufig schon an der Basisstufe fünf und stieß im Erfolgsfall bei Stufe drei an eine harte Grenze.",
    "Im rein autonomen Vergleich besitzen führende proprietäre Modelle heute eine deutlich höhere Fähigkeit für schwere Cyberangriffe als die führende Open-Weight-Alternative.",
    "Verschiebt man den Blick jedoch von reiner Zerstörungskraft auf die operative Effizienz, kehren sich die Kräfteverhältnisse um.",
    "Diese Darstellung vergleicht die Token-Kosten, um die erste Basisstufe fünf zu erreichen.",
    "GLM 5.2 war mit drei Dollar einundsiebzig am günstigsten und bewies einen klaren Effizienzvorteil bei Basisaufgaben gegenüber Opus 4.8 mit sieben Dollar vierunddreißig.",
    "Anschließend führten die Forscher eine zweite Variable ein, den Nudge-Test: Sie gaben der KI aktiv Hinweise, sobald sie bei Hochrisiko-Aufgaben feststeckte.",
    "Die Hinweise halfen GLM 5.2 zwar etwas häufiger auf Stufe fünf, scheiterten aber komplett daran, das Modell zu fortgeschrittenen System-Exploits zu bringen.",
    "Die Daten zeigen einen Mangel an kognitiver Flexibilität: GLM 5.2 verharrt stur auf gescheiterten Hypothesen und kann seine Strategie nicht so schnell wechseln wie Opus.",
    "Zudem gibt es einen kritischen Sicherheitsbefund: Anders als Opus verweigerte GLM 5.2 während des gesamten Tests kein einziges Mal aus Sicherheitsgründen die Ausführung.",
    "Open-Weight-Modelle sind günstiger und völlig unbeschränkt, doch ihr starres Denken hindert sie derzeit noch daran, diese Vorteile für Meister-Hacks zu nutzen.",
    "Der Bericht des japanischen KI-Sicherheitsinstituts zieht ein klares Fazit: Bislang haben sich hochgradig autonome Cyberfähigkeiten noch nicht breit auf offene Modelle übertragen.",
    "Aktuell kann ein Angreifer nicht einfach ein offenes Modell wie GLM 5.2 herunterladen, auf ein Ziel richten und erwarten, dass es automatisch die volle Kontrolle übernimmt.",
    "Dennoch enthält die Studie eine deutliche Warnung: GLM 5.2 zeigte bei einzelnen Teilaufgaben bereits fortgeschrittene Fähigkeiten — das Fundament der Gefahr ist also gelegt.",
    "Mit neuen Modell-Updates, zusammenarbeitenden Agenten und besseren Werkzeugen könnten die Hacking-Fähigkeiten offener Modelle in kürzester Zeit exponentiell ansteigen.",
    "Sobald ein Open-Weight-Modell veröffentlicht ist, können seine Gewichte von keiner Behörde mehr zurückgerufen, gepatcht oder eingeschränkt werden.",
    "Weil diese Veröffentlichung unumkehrbar ist, hängt der Schutz globaler digitaler Infrastruktur davon ab, dass Institute wie das AISI kontinuierlich offenlegen, was diese Systeme lernen.",
]

PART1_FR = [
    "L'IA est devenue incroyablement douée pour écrire du code, mais la même reconnaissance de motifs qui sert à corriger un logiciel suffit à le transformer en arme.",
    "Nous savons déjà que les modèles propriétaires très protégés deviennent des hackers redoutables, mais les chercheurs suivent désormais un tout autre vecteur d'attaque.",
    "L'attention s'est tournée vers les modèles à poids ouverts : des systèmes puissants que chacun peut télécharger, modifier et exécuter localement sans garde-fous.",
    "Cela crée ce que les chercheurs appellent la prolifération des cyber-capacités : la crainte que des outils de piratage autonomes soient bientôt distribués à tous sans contrôle.",
    "Pour mesurer le danger réel de ces modèles ouverts aujourd'hui, l'Institut japonais de sécurité de l'IA a mené sa première évaluation indépendante et publique.",
    "Cette étude examine si la cybersécurité mondiale est sur le point d'être submergée par des hackers IA autonomes et librement accessibles.",
    "Les chercheurs ont utilisé le banc d'essai de Carnegie Mellon et demandé aux modèles de développer de façon autonome des exploits pour quarante et une failles connues du moteur V8 de Chrome.",
    "Ce schéma montre une échelle de gravité à cinq niveaux suivant la progression d'une cyberattaque.",
    "À la base, le niveau cinq consiste simplement à identifier un fragment de code vulnérable.",
    "Mais si l'IA atteint le niveau un au sommet, une brèche catastrophique se produit, exécutant des opérations arbitraires hors du système cible.",
    "L'expérience a opposé deux modèles propriétaires américains de pointe, Claude Opus 4.7 et 4.8, à GLM 5.2, un modèle chinois à poids ouverts largement disponible.",
    "Ce graphique révèle les résultats : Opus 4.8 a dominé avec un score moyen de cinq virgule vingt-deux, atteignant les dangereux niveaux deux et un.",
    "À l'inverse, le modèle ouvert GLM 5.2 a souvent échoué dès le niveau cinq et, lorsqu'il réussissait, s'est heurté à un plafond strict au niveau trois.",
    "Dans un affrontement purement autonome, les meilleurs modèles propriétaires actuels possèdent une capacité nettement supérieure à mener des cyberattaques graves.",
    "Mais lorsqu'on passe de la puissance brute à l'efficacité opérationnelle, le rapport de force s'inverse.",
    "Cette visualisation compare le coût en jetons nécessaire pour atteindre le niveau cinq initial.",
    "GLM 5.2 a été le moins cher à trois dollars soixante et onze, prouvant l'avantage d'efficacité des modèles ouverts sur les tâches de base face aux sept dollars trente-quatre d'Opus 4.8.",
    "Les chercheurs ont ensuite introduit une seconde variable, le test du coup de pouce, en fournissant des indices à l'IA lorsqu'elle bloquait sur des tâches à haut risque.",
    "Ces indices ont aidé GLM 5.2 à atteindre un peu plus souvent le niveau cinq, mais n'ont jamais suffi à lui faire exécuter des exploits avancés compromettant le système.",
    "Les données pointent un manque de flexibilité cognitive : GLM 5.2 s'entête sur des hypothèses erronées et ne sait pas pivoter rapidement comme les modèles Opus.",
    "Il y a aussi un constat critique sur la sécurité : contrairement à Opus, GLM 5.2 n'a émis aucun refus de sécurité durant tout le test, révélant l'absence totale de garde-fous par défaut.",
    "Les modèles à poids ouverts sont moins chers et sans restriction, mais leur raisonnement rigide les empêche encore d'exploiter ces atouts pour des piratages de haut vol.",
    "Le rapport de l'AISI japonais livre une conclusion claire : à ce stade, les capacités cyber autonomes les plus avancées n'ont pas encore proliféré vers les modèles ouverts.",
    "Aujourd'hui, un acteur malveillant ne peut pas simplement télécharger GLM 5.2, le pointer sur une cible et s'attendre à ce qu'il prenne automatiquement le contrôle complet d'un système.",
    "Pourtant, les données contiennent un avertissement : GLM 5.2 a montré des capacités avancées sur des tâches isolées, preuve que l'architecture du danger est déjà en place.",
    "À mesure que les modèles sont mis à jour et que les agents collaborent, les capacités de piratage à poids ouverts pourraient bondir de façon exponentielle en très peu de temps.",
    "Une fois qu'un modèle à poids ouverts est publié, ses poids ne peuvent plus être rappelés, corrigés ou restreints par aucune autorité.",
    "Parce que cette publication est irréversible, la défense des infrastructures numériques dépend désormais d'institutions comme l'AISI pour suivre en continu ce que ces systèmes apprennent à faire.",
]

PART1_JA = [
    "AIはコードを書くのが驚くほど巧みになりましたが、ソフトウェアのバグを見つけるのに必要なパターン認識力は、そのまま攻撃兵器を作る力にもなります。",
    "厳重に管理された商用AIモデルが高度なハッカーになりつつあることはすでに知られていますが、研究者たちは今、まったく別の攻撃経路を追跡しています。",
    "焦点はオープンウェイトモデルに移っています。誰でもダウンロードして改変し、企業の安全ガードレールを完全に外して自分のハードウェアで動かせる高性能AIです。",
    "これがサイバー能力の拡散と呼ばれるシナリオを生みます。高度な自律型ハッキング能力が、何の監視もないまま一般大衆に直接広まるという懸念です。",
    "こうしたオープンモデルが今どれだけ危険かを正確に測るため、日本のAIセーフティ・インスティテュートは初の独立した実名公開評価を実施しました。",
    "この評価は、世界のサイバーセキュリティ環境が、自由に使える自律型AIハッカーに席巻される寸前にあるのかどうかを検証するものです。",
    "研究チームはカーネギーメロン大学の評価基盤を用い、Google ChromeのV8エンジンにある41件の既知の脆弱性に対するエクスプロイトを自律開発させました。",
    "この図は、サイバー攻撃の進行度を追跡する5段階の深刻度スケールを示しています。",
    "最下層のティア5は、単に脆弱なコード箇所を特定するだけの段階です。",
    "しかし頂点のティア1に到達すると、標的システムの外部で任意の操作を実行する壊滅的な侵害が発生します。",
    "実験では、米国の主要な商用モデルであるClaude Opus 4.7および4.8と、広く入手可能な中国のオープンウェイトモデルGLM 5.2を対決させました。",
    "このチャートは基本結果を示しています。Opus 4.8が平均5.22スコアで圧倒し、危険なティア2およびティア1の段階に到達しました。",
    "対照的に、オープンウェイトのGLM 5.2は基本のティア5にすら届かないことが多く、成功した場合でもティア3で明確な壁にぶつかりました。",
    "純粋な自律能力の勝負では、現在のトップ商用モデルは主要なオープンウェイトモデルよりも深刻なサイバー攻撃を実行する能力がはるかに高いと言えます。",
    "しかし焦点を純粋な破壊力から運用効率へと移すと、モデル間の力関係は逆転します。",
    "この図は、最初のティア5の基準に到達するのに必要なトークンコストを比較したものです。",
    "GLM 5.2は3ドル71セントと最も安く、7ドル34セントかかったOpus 4.8に対して基本的な作業効率で明確な優位性を示しました。",
    "続いて研究チームは2つ目の変数としてナッジテストを導入し、高リスク課題でAIが行き詰まるたびにヒントや指示を与えました。",
    "ヒントによってGLM 5.2が基本のティア5に到達する頻度はわずかに上がりましたが、システムを侵害する高度なエクスプロイトを実行させるには至りませんでした。",
    "データは認知的な柔軟性の欠如を示しています。GLM 5.2は失敗した仮説に頑固に固執し、Opusのように素早く新しい戦略へ切り替えることができません。",
    "安全性に関する重要な発見もあります。Opusとは異なり、GLM 5.2はテスト全体を通じて安全上の拒否を一度も行わず、初期ガードレールの欠如を露呈しました。",
    "オープンウェイトモデルは安価で制限もありませんが、現時点では内部推論の硬直性が足かせとなり、達人級のハッキングを実行するには至っていません。",
    "日本のAISIの報告書は明確な結論を下しています。現時点では、真に高度な自律型サイバー能力はまだオープンウェイトモデルには広く拡散していません。",
    "今すぐ悪意ある攻撃者がGLM 5.2のようなオープンモデルをダウンロードして標的に向けても、自動的にシステムを完全掌握することはできません。",
    "しかしデータには重大な警告が含まれています。GLM 5.2は個別の特定タスクでは高度な能力を示しており、危険の土台となる構造はすでに存在しています。",
    "モデルが更新され、エージェントが連携し、自動化ツールが進化すれば、オープンウェイトのハッキング能力はごく短期間で指数関数的に急伸する可能性があります。",
    "一度オープンウェイトモデルが世に出れば、その重みデータを回収したり修正したり制限したりすることは誰にもできません。",
    "公開が不可逆である以上、世界のデジタル基盤を守れるかどうかは、AISIのような機関が自律型システムの学習内容を継続的に追跡・公開できるかにかかっています。",
]

PART2_JA = [
    "人工知能に対する一般的な恐怖は、暴走したモデルがデジタルの封じ込めを破り、人類に対して陰謀を企てるといったシナリオに集中しがちです。",
    "しかしアンソロピックの2026年9月の脅威インテリジェンス報告書は、より差し迫った脆弱性、すなわち人々と最先端モデルをつなぐデジタル配管へと焦点を移しています。",
    "この橋渡しを担うのがAPIキーです。サードパーティ製ソフトがAIの中枢と直接通信することを可能にする、デジタルの握手のような文字列です。",
    "サイバー犯罪者たちは、AIを兵器化するのにモデル自体をハッキングする必要はないことに気づきました。",
    "必要なのは、誰かのアクセス権を盗むことだけです。盗まれたキーは「戦利品」「計算力」「隠れ蓑」の3つを同時に提供するため、犯罪サプライチェーンの原動力となっています。",
    "AIセキュリティは抽象的な計算機科学の理論を超え、今や高速で巨額の利益を生む強奪事件からいかに身を守るかという問題になっています。",
    "第1の「戦利品」として、盗まれたキーはそのまま換金可能なデジタル商品です。侵害した端末から奪い取り、地下市場ですぐに転売して利益を得ることができます。",
    "ロシアとウクライナの運営グループはこの戦略を使い、洗練されたブランドを装ってClaudeモデルへの割引アクセスを謳う偽のストアを運営していました。",
    "このサイトはおとり商法でした。利用者がプロンプトを送る裏で、再販業者のツールが顧客の端末に認証情報窃取マルウェアを密かにインストールしていたのです。",
    "マルウェアは端末を常時監視し、新しいトークンが生成されるたびに運営者へ転送して他の犯罪者へと転売していました。",
    "これは機密情報の収集ではなく、ユーザーの認証情報を換金作物のように扱う工業規模の収穫作戦でした。",
    "第2の柱は「計算力」です。AIキーがあれば、攻撃者は膨大な犯罪ワークロードを自己負担ゼロで処理する不眠不休の自動頭脳を手に入れられます。",
    "ある事例では、中国の大学の学部生2人が通常の合法的なAIアクセスを使い、寮の部屋から高度な攻撃オペレーションを構築しました。",
    "彼らは自律型のエクスプロイト工場を設計しました。機器のファームウェアを逆コンパイラに入力し、脆弱性の仮説を立て、連続ループで攻撃コードを検証するシステムです。",
    "この工場は実験環境のソフトに対して動作するコードができるまで反復を続け、学生たちの手作業なしで成功したエクスプロイトの数々を生み出しました。",
    "この自動化システムは50以上の組織を攻撃し、さらに13体のエージェント群を展開して米軍や政府の公開サイトから情報を収集しました。",
    "最先端AIモデルへのアクセスにより、わずか2人の学生が通常は国家レベルの組織に限られていた自動攻撃能力を再現できてしまうのです。",
    "第3の柱は「隠れ蓑」です。盗まれた認証情報はほぼ完璧な変装となり、攻撃者の正体を被害者自身のアカウントの裏に隠します。",
    "シャイニー・ハンターズ集団の事例では、企業向けソフト会社のAIキーを盗み出し、自動化されたカード情報売買ショップ「ソラキ」を構築しました。",
    "彼らのAIエージェントは航空会社や通信会社から盗んだ数テラバイトのデータを処理し、何百万件もの生データを検索可能な銀行・個人プロファイルへと整理しました。",
    "ハッカーが盗んだキーを使ったため、システムログに記録されたのは被害を受けた企業自身でした。",
    "企業は盗まれた自社データを兵器化するための計算処理費用まで請求されていたのです。",
    "この隠れ蓑を得るため、別のグループはAIベンダーの評価用サンドボックスに悪意ある命令を直接注入しました。",
    "その目的は、ベンダーの顧客が所有する本番用キーをサンドボックスに吐き出させることでした。",
    "盗まれたキーは攻撃者に大規模犯罪を行う計算力を与え、一方でシステムはすべての悪意ある行動を被害者のものとして記録します。",
    "正規の認証情報を使ってセキュリティ層を丸ごと迂回されてしまえば、AIの直接的な防御機能は何の役にも立ちません。",
    "技術的な巧妙さはもはや攻撃者の正体を示す指標にはなりません。AIが侵入の最も難しい部分を自動化するため、学生でも国家支援型アクター並みの持続力と規模を持てます。",
    "最先端AIモデルは無数の企業アプリケーションを支える重要インフラへと進化しました。",
    "このインフラにおける最大の脆弱性は、もはやモデルの内部ガードレールではなく、そこにアクセスするための人間の認証情報なのです。",
    "アンソロピックの指針は明確です。組織はAIキーとエージェント連携を、最も機密性の高い本番シークレットと同じ厳格さで守らなければなりません。",
    "犯罪の裏社会にとって、これらの認証情報は産業規模のパワーへの即座の、しかも他人払いのアクセス権を意味するのです。",
]

PART3_JA = [
    "何十年もの間、エリートによるサイバースパイ活動は時間のかかる手作業の職人技でした。リバースエンジニアリングには何千行ものコードを何ヶ月も睨みつける分析官が必要で、ベンダーも知らないゼロデイ脆弱性を見つけ出して兵器化するには希少な専門家チームと数百万ドルの予算が必要でした。",
    "持続的で高度なサイバースパイ工作を行えるのは、潤沢な資金を持つ国家かエリート組織に限られていました。しかし2026年9月、そうした資源の制約を覆す組織的攻撃キャンペーンが脅威インテリジェンス報告書に記録されました。東南アジアの政府機関を突破して市民記録を抜き取り、",
    "小売企業の本番システムを侵害し、教育テック企業から大量のデータを引き出したのです。",
    "GTG-10077として追跡されたこの攻撃者は軍の諜報部隊ではありませんでした。中国・長沙の大学に通う2人の学部生だったのです。1人はインターンを終えたばかりで、もう1人は初級サイバー職の面接を受けている最中でした。彼らは寮で手作業のハッキングをしたのではなく、仕事をする機械を作ったのです。",
    "2人は自動化されたエクスプロイト工場を構築し、Claudeをその中核となるエンジニアリングおよびオーケストレーション層に据えました。この工場はネットワーク機器のファームウェアや主要セキュリティ製品を対象に、自律的な脆弱性調査ループを回します。AIがファームウェアを調べ、仮説を立て、攻撃コードを書いて実験環境で検証する自己修正サイクルです。",
    "人間のエンジニアならやがて疲労の壁にぶつかりますが、このループは夜通し、来る日も来る日も休まず反復を続けます。報告書によれば、このバイナリ解析ループをわずか1ヶ月回しただけで、ネットワーク機器に対する10件以上のゼロデイ候補が見つかりました。ゼロデイ発見を手作業の芸術から自動製造ラインへと変えたのです。",
    "発見した脆弱性を実戦投入するため、工場は第2の仕組みとしてエージェント群によるスパイ部門を使います。リーダーAIが偵察タスクを分解し、複数標的に対して並列稼働する数十のサブエージェントへと割り振ります。標的リストや奪った認証情報、侵入状況を永続メモリに保存し、",
    "学生たちが席を外している間もキャンペーンを途中から再開して情報をダウンロードし続けます。エージェント群は米軍や政府サイトの契約情報など、国家の情報優先事項に沿ったサイトを標的にしていました。",
    "作業をエージェント群に委ねることで、わずか2人が諜報機関丸ごと1つ分の運用帯域を維持できます。アンソロピックの報告書は、攻撃ハッキングの歴史的制約であった「時間」と「人間の専門知識」の2つが取り除かれた転換点を浮き彫りにしています。該当アカウントは停止されたものの、手作業の時代から",
    "自動エクスプロイト工場の産業時代への移行を示す設計図となりました。非対称性は明白です。かつて国防予算を必要とした能力を、今や大学生が手にする時代となり、深刻なスパイ工作への参入障壁は下がり続けています。",
]


def main() -> None:
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    p1_chunks = json.loads((OUT_DIR / "_part_1_chunks.json").read_text(encoding="utf-8"))

    t = ffdur(OUT_DIR / "intro.mp4")
    part_offsets = {}
    part_durs = {}
    for n in range(1, 8):
        if n > 1:
            t += ffdur(OUT_DIR / f"card_{n}.mp4")
        part_offsets[n] = t
        d = ffdur(OUT_DIR / f"part_{n}.mp4")
        part_durs[n] = d
        t += d

    p2_dir = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-09-11-secure-your-keys-supply-chain")
    p3_dir = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-09-11-exploit-foundry-two-students")
    p4_dir = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-14-the-convenience-paradox-why-the-internet-of-things-is-melting")
    p5_dir = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-13-the-convergence-point-why-ai-worms-are-targeting-your-smart-tv")
    p6_dir = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-14-the-shadow-datacenter-why-ai-worms-are-targeting-your-smart-tv")
    p7_dir = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-10-models-as-insider-risks-in-the-super-intelligence-era")

    for lang in ("en", "de", "fr", "ja"):
        all_blocks = [{
            "start": 0.0,
            "end": 19.35,
            "text": INTRO_TEXT[lang],
        }]

        # Part 1: _part_1_chunks.json (already relative to part_1.mp4!)
        p1_texts = [c["text"] for c in p1_chunks] if lang == "en" else (PART1_DE if lang == "de" else (PART1_FR if lang == "fr" else PART1_JA))
        for c, txt in zip(p1_chunks, p1_texts):
            all_blocks.append({"start": part_offsets[1] + c["start"], "end": part_offsets[1] + min(part_durs[1], c["end"]), "text": txt})

        # Part 2: final_long trimmed at 12.96s (drop blocks 0..1 hook VO ending at 13.52s)
        if lang == "ja":
            p2_en = parse_srt(p2_dir / "secure-your-keys-supply-chain_en.srt")[2:]
            for b, ja_txt in zip(p2_en, PART2_JA):
                st = max(0.0, b["start"] - 12.96)
                en = min(part_durs[2], b["end"] - 12.96)
                if en > st + 0.2:
                    all_blocks.append({"start": part_offsets[2] + st, "end": part_offsets[2] + en, "text": ja_txt})
        else:
            p2_srt = p2_dir / f"secure-your-keys-supply-chain_{lang}.srt"
            for b in parse_srt(p2_srt)[2:]:
                st = max(0.0, b["start"] - 12.96)
                en = min(part_durs[2], b["end"] - 12.96)
                if en > st + 0.2:
                    all_blocks.append({"start": part_offsets[2] + st, "end": part_offsets[2] + en, "text": b["text"]})

        # Part 3: final_long trimmed at 12.90s (drop block 0 hook VO ending at 13.14s)
        if lang == "ja":
            p3_en = parse_srt(p3_dir / "exploit-foundry-two-students_en.srt")[1:]
            for b, ja_txt in zip(p3_en, PART3_JA):
                st = max(0.0, b["start"] - 12.90)
                en = min(part_durs[3], b["end"] - 12.90)
                if en > st + 0.2:
                    all_blocks.append({"start": part_offsets[3] + st, "end": part_offsets[3] + en, "text": ja_txt})
        else:
            p3_srt = p3_dir / f"exploit-foundry-two-students_{lang}.srt"
            for b in parse_srt(p3_srt)[1:]:
                st = max(0.0, b["start"] - 12.90)
                en = min(part_durs[3], b["end"] - 12.90)
                if en > st + 0.2:
                    all_blocks.append({"start": part_offsets[3] + st, "end": part_offsets[3] + en, "text": b["text"]})

        # Parts 4..7: shift by hook_card offset (13.56, 16.48, 14.25, 16.57)
        for pnum, pdir, pslug, h_off in [
            (4, p4_dir, "the-convenience-paradox-why-the-internet-of-things-is-melting", 13.56),
            (5, p5_dir, "the-convergence-point-why-ai-worms-are-targeting-your-smart-tv", 16.48),
            (6, p6_dir, "the-shadow-datacenter-why-ai-worms-are-targeting-your-smart-tv", 14.25),
            (7, p7_dir, "models-as-insider-risks-in-the-super-intelligence-era", 16.57),
        ]:
            psrt = pdir / f"{pslug}_{lang}.srt"
            for b in parse_srt(psrt):
                if b["end"] <= h_off + 0.5:
                    continue
                st = max(0.0, b["start"] - h_off)
                en = min(part_durs[pnum], b["end"] - h_off)
                if en > st + 0.2:
                    all_blocks.append({"start": part_offsets[pnum] + st, "end": part_offsets[pnum] + en, "text": b["text"]})

        lines = []
        for idx, b in enumerate(all_blocks, 1):
            lines.append(f"{idx}\n{fmt_ts(b['start'])} --> {fmt_ts(b['end'])}\n{b['text']}\n")
        out_srt = OUT_DIR / f"{SLUG}_{lang}.srt"
        out_srt.write_text("\n".join(lines), encoding="utf-8")
        shutil.copy2(out_srt, STAGE_DIR / out_srt.name)
        print(f"Wrote {out_srt.name} ({len(all_blocks)} blocks)")


if __name__ == "__main__":
    main()
