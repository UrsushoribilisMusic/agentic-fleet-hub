#!/usr/bin/env python3
"""Stitch full EN/DE/FR/JA .srt captions for Compilation C1."""
import json
import re
import shutil
import subprocess
from pathlib import Path

OUT_DIR = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-24-compilation-c1-ai-will-do-the-work-vol-2")
STAGE_DIR = Path("/Users/miguelrodriguez/Downloads/tech-shorts-captions/ai-will-do-the-work-vol-2")
SLUG = "ai-will-do-the-work-vol-2"


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
    "en": "Every screen in the building is still glowing, and the work is still getting done. Only the chairs are empty. Exponential models have collided with a linear economy, reshaping career ladders, entry-level jobs, and who actually gets paid when machines do the work. Across six investigations, we follow the data on one question: if AI does the work, what happens to yours?",
    "de": "Jeder Bildschirm im Gebäude leuchtet noch, und die Arbeit wird weiterhin erledigt. Nur die Stühle sind leer. Exponentielle Modelle sind mit einer linearen Wirtschaft kollidiert und verändern Karriereleitern, Einstiegsjobs und die Frage, wer eigentlich bezahlt wird, wenn Maschinen die Arbeit erledigen. In sechs Untersuchungen folgen wir den Daten zu einer Frage: Wenn KI die Arbeit macht, was passiert dann mit Ihrer?",
    "fr": "Chaque écran du bâtiment brille encore et le travail continue de se faire. Seules les chaises sont vides. Des modèles exponentiels se sont heurtés à une économie linéaire, remodelant les échelles de carrière, les emplois débutants et la question de savoir qui est réellement payé quand les machines font le travail. À travers six enquêtes, nous suivons les données sur une question : si l'IA fait le travail, qu'advient-il du vôtre ?",
    "ja": "ビルの中のすべての画面が今も輝き、仕事は変わらず進んでいます。ただ椅子だけが空っぽなのです。指数関数的なモデルが線形な経済と衝突し、キャリアの階段や新卒の仕事、そして機械が仕事をする時代に誰が報酬を得るのかを塗り替えています。6つの調査を通じて、AIが仕事をするならあなたの仕事はどうなるのかという問いをデータで追います。",
}

PART2_JA = [
    "過去100年間、現代経済学は一貫した法則に依拠してきました。国の生産性が上がれば、人間の賃金もそれに伴って上昇するというものです。この歴史的チャートが示す通り、数十年にわたりGDPが上昇するにつれ、平均賃金も並行して伸びてきました。",
    "しかしアンソロピック研究所の新たな経済フレームワークは、今から2030年の間に人工知能がこの100年来の結びつきをどう断ち切るかをモデル化しています。極端なシナリオでは、AIが今日の知的労働の半分を担い、GDPを32パーセント拡大させます。業務が自動化されると、その経済的価値は人間の労働から物理的資本へと移転します。",
    "スプレッドシートを分析する価値はオフィスワーカーの給与明細から消え、コードを実行するサーバーラックや計算クラスタへと直接移ります。これが物理的なボトルネックを生みます。ソフトウェアは数秒で複製できても、データセンターや送電網、専用チップの建設には何年もかかるため、2030年までインフラは極めて非弾力的です。",
    "テック業界がAI計算需要の爆発に追いつく速さでインフラを建設できないため、ハードウェアのレンタル費用は急騰します。AI収益のフロー図にその影響が表れています。労働への還元パイプは細り、資本所有者へのパイプが拡大してAIの生産性向上による果実のほぼすべてを吸収します。",
    "このハードウェア不足が人間の労働力から価値を吸い上げ、機械そのものへと流し込みます。ハードウェアの所有者が新たな富の大半を握るため、経済全体のパイが大きく膨らんでも、労働者の取り分は縮小します。そしてその縮小した取り分が根本的に再分配されます。",
    "モデルは残りの人間の労働力を2つの島に分けます。一方はホワイトカラー専門職や管理職、事務職からなる知的労働の島。もう一方は技能職や対人サービス、肉体労働からなる非知的労働の島です。AIは情報処理に特化しているため自動化は知的労働の島を直撃し、オフィスワーカーの需要を急減させます。",
    "追い出された知的労働者は専門分野を離れ、仕事を探して非知的労働の島へと渡らなければなりません。同時にGDP全体の32パーセント急増により、企業や消費者は物理インフラや建設、専門医療により多くの資金を使えるようになります。AIは建物の配線やベッドサイドの看護はできないため、技能職の需要が供給を大きく上回ります。",
    "このチャートはその分岐を可視化しています。2030年までに知的労働者の賃金はAI以前の軌道より11.5パーセント低下すると予測されます。一方、非知的労働の賃金は基準線より34パーセント急上昇します。この力学が現代社会の伝統的な階層を逆転させ、ホワイトカラーの賃金プレミアムを完全に消し去ります。",
    "2030年までに、大学の学位で高給のオフィス職を得るという従来の成功法則は時代遅れになります。代わりにAI経済の賃金上昇は、物理世界を維持する技能職や対人ケア、肉体労働者へと流れます。知的労働者は長期的な賃金停滞に直面します。",
    "そしてキャリア転換に苦しむ中で高い失業率に直面します。世論の予測もこの結果と一致しており、米国の成人の半数が10年末までにこの規模の経済的混乱が到来すると予想しています。この移行は富と階級の恒久的な構造的再編を意味します。",
    "生計を立てる基本的な仕組みが変わる以上、私たちの焦点も変えなければなりません。技術を止める議論をするのではなく、足元の地盤が動く中で労働者を支える大規模な再訓練プログラムと新たな所得支援システムを構築する必要があります。",
]

PART4_DE = [
    "Zwischen 2025 und 2032 soll der physische KI-Ausbau, also Rechenzentren, Stromnetze und Chips, voraussichtlich zehn Komma drei Billionen Dollar kosten.",
    "Mit durchschnittlich drei Komma sechs Prozent des US-BIP pro Jahr stellt dieser Ausbau das Eisenbahnnetz, das Autobahnsystem und die ländliche Elektrifizierung in den Schatten.",
    "Doch die Art, wie Tech-Giganten dafür bezahlen, verändert sich. Sie wenden sich von transparenten Unternehmensanleihen ab und komplexen Finanzierungsstrukturen außerhalb ihrer Bilanzen zu.",
    "Statt klassischer Kredite fließt das Kapital über isolierte, schwer durchschaubare Mechanismen wie Joint Ventures, private Kreditmärkte und Zweckgesellschaften.",
    "Weil dieses historische Schuldvolumen gigantisch und weitgehend unsichtbar ist, hängt sein Überleben von einem einzigen Ergebnis ab.",
    "KI muss für ihre Konzerne dauerhaft enorme Cashflows erwirtschaften, um eine systemische Kreditkrise zu verhindern.",
    "Um Billionen an versteckten Verbindlichkeiten abzubezahlen, müssen KI-Firmen Werkzeuge verkaufen, die die Betriebskosten ihrer Unternehmenskunden drastisch senken.",
    "Historisch gesehen ist der schnellste und zuverlässigste Weg zur Kostensenkung in dieser Größenordnung der Abbau menschlicher Arbeitskraft.",
    "Das erzeugt eine schwere Zwickmühle: Scheitert die KI bei diesen Cashflows, droht eine versteckte Schuldenkrise.",
    "Hat sie Erfolg, droht eine massive Arbeitsmarkt- und Ungleichheitskrise. Um zu verstehen, wie sich diese entfaltet, müssen wir die Mechanik technologischer Verdrängung betrachten.",
    "Was passiert konkret, wenn Maschinen menschliche Arbeit übernehmen? Eine große Wirtschaftsstudie des MIT liefert dafür den Rahmen.",
    "Die Forscher unterscheiden zwei Arten von Technologie: Werkzeuge, die Beschäftigte unterstützen und ihre Löhne steigern, und Werkzeuge, die schlicht automatisieren.",
    "Dieses MIT-Diagramm zeigt, wie Automatisierung wirkt: Rechts dehnt sich die Grenze des Kapitals aus, während Maschinen Routineaufgaben übernehmen.",
    "Die verdrängten Arbeitskräfte verschwinden nicht einfach. Sie konkurrieren um die verbleibenden, nicht automatisierten Stellen.",
    "Das erzeugt einen Welleneffekt, der die Löhne über alle Branchen hinweg nach unten drückt.",
    "Technologischer Fortschritt hebt nicht alle gleichermaßen. Automatisierung bestraft gezielt jene, die auf Routineaufgaben spezialisiert sind.",
    "Wir müssen nicht raten, ob diese Theorie stimmt. Anhand von US-Wirtschaftsdaten von 1980 bis 2016 lässt sich die Wirkung exakt nachverfolgen.",
    "Dieses Diagramm zeigt den prozentualen Rückgang des Arbeitsanteils nach Branchen, aufgeteilt in den Gesamtrückgang in Blau und den automatisierungsbedingten Rückgang in Orange.",
    "Es zeigt, dass fünfzig bis siebzig Prozent der Veränderungen bei der Lohnungleichheit in diesen Jahrzehnten allein durch die Automatisierung von Routineaufgaben entstanden.",
    "Dieses Streudiagramm offenbart die menschlichen Kosten anhand der steil abfallenden Trendlinie.",
    "Für die Bevölkerungsgruppen mit der stärksten Aufgabenverdrängung sanken die realen Stundenlöhne um bis zu fünfzehn Prozent.",
    "Man könnte erwarten, dass eine solche Verdrängung von einem gewaltigen Wirtschaftsboom begleitet wird.",
    "Doch im selben Zeitraum wuchs die Gesamtproduktivität kumuliert um lediglich drei Komma vier Prozent.",
    "Eine Technologie muss nur genug Lohnkosten einsparen, um Renditen für Kapitaleigner zu erwirtschaften.",
    "Sie muss keinen utopischen Produktivitätsboom auslösen, um den Arbeitsmarkt komplett umzukrempeln.",
    "Verbindet man diese vierzigjährige Geschichte der Automatisierung mit den zehn Komma drei Billionen Dollar an außerbilanziellen KI-Schulden, wirkt diese Verschuldung wie ein Brandbeschleuniger.",
    "Die enormen Vorabkosten setzen die KI-Branche unter extremen Druck, sofortige Renditen zu liefern.",
    "Investoren können kein Jahrzehnt warten, bis Beschäftigte langsam lernen, KI zur Ergänzung ihres Arbeitsalltags zu nutzen.",
    "Der Druck zwingt Konzerne förmlich dazu, KI strikt zur sofortigen kostensparenden Automatisierung einzusetzen.",
    "Kann der KI-Boom ohne massive Ungleichheit weitergehen? Die historischen Daten sprechen klar dagegen, sofern sich der Einsatz nicht grundlegend ändert.",
    "Wird KI vorrangig zur Automatisierung genutzt, wird das nächste Jahrzehnt die Lohnpolarisierung der letzten vierzig Jahre wiederholen, beschleunigt durch Billionen an Schattenkapital.",
    "Die unmittelbare politische Forderung aus diesen Daten lautet daher: finanzielle Transparenz.",
    "Wir brauchen klare Sicht auf diese außerbilanziellen Strukturen. Aufsichtsbehörden müssen diese Risiken jetzt in Echtzeit überwachen, statt auf einen Marktabschwung zu warten.",
    "Gleichzeitig muss die Gesellschaft in Echtzeit erfassen, welche menschlichen Aufgaben KI ersetzt, um sich auf die wirtschaftlichen Folgen vorzubereiten.",
    "Das größte Risiko des KI-Booms ist nicht das Scheitern der Technik, sondern ein überwältigender finanzieller Erfolg durch das stille Aushöhlen der Arbeitnehmerschaft.",
]

PART4_FR = [
    "Entre 2025 et 2032, le déploiement physique de l'IA — centres de données, réseaux électriques et puces — devrait coûter dix virgule trois mille milliards de dollars.",
    "Représentant en moyenne trois virgule six pour cent du PIB américain par an, ce chantier dépasse le réseau ferroviaire, les autoroutes et l'électrification rurale.",
    "Mais la façon dont les géants technologiques le financent change : ils délaissent la dette d'entreprise transparente au profit de montages complexes hors bilan.",
    "Au lieu de prêts classiques, les capitaux transitent par des mécanismes opaques : coentreprises, crédit privé et véhicules financiers dédiés.",
    "Parce que ce volume historique de dette est massif et largement caché du public, sa survie repose sur un seul résultat.",
    "L'IA doit générer des flux de trésorerie colossaux et durables pour ses créateurs afin d'éviter une crise systémique du crédit.",
    "Pour rembourser des milliers de milliards d'obligations cachées, les entreprises d'IA doivent vendre des outils qui réduisent drastiquement les coûts de leurs clients.",
    "Historiquement, le moyen le plus rapide et le plus fiable d'améliorer les marges à cette échelle consiste à remplacer le travail humain.",
    "Cela crée un double piège : si l'IA échoue à livrer ces revenus, la société affronte une crise de la dette cachée.",
    "Si elle réussit, nous affrontons une crise majeure du travail et des inégalités. Pour comprendre comment elle se déroulerait, examinons la mécanique du remplacement technologique.",
    "Que se passe-t-il lorsque les machines prennent physiquement le relais du travail humain ? Une grande étude économique du MIT fournit un cadre précis.",
    "Les chercheurs distinguent deux types de technologies : celles qui augmentent les travailleurs et leurs salaires, et celles qui ne font qu'automatiser.",
    "Ce diagramme du MIT illustre l'automatisation : à droite, la frontière du capital s'étend à mesure que les machines reprennent les tâches routinières.",
    "Ces travailleurs déplacés ne disparaissent pas : ils entrent en concurrence pour les emplois restants non automatisés.",
    "Cela crée un effet d'onde qui tire les salaires vers le bas dans tous les secteurs.",
    "Le progrès technologique n'élève pas tous les travailleurs également. L'automatisation pénalise ceux qui sont spécialisés dans les tâches routinières.",
    "Inutile de deviner si cette théorie tient : on peut suivre son impact exact sur les salaires américains entre 1980 et 2016.",
    "Ce graphique détaille le recul de la part du travail par secteur, en comparant le déclin total en bleu et celui lié à l'automatisation en orange.",
    "Il révèle que cinquante à soixante-dix pour cent de la hausse des inégalités salariales sur ces décennies proviennent uniquement de l'automatisation des tâches routinières.",
    "Ce nuage de points révèle le coût humain à travers une courbe fortement descendante.",
    "Pour les groupes subissant le plus fort remplacement des tâches, les salaires horaires réels ont chuté jusqu'à quinze pour cent.",
    "On pourrait s'attendre à ce qu'un tel bouleversement s'accompagne d'un boom économique massif.",
    "Pourtant, sur la même période, la productivité globale n'a progressé que de trois virgule quatre pour cent au total.",
    "Une technologie a seulement besoin d'économiser assez sur les coûts salariaux pour rémunérer les détenteurs de capitaux.",
    "Elle n'a pas besoin de déclencher un boom de productivité utopique pour transformer complètement le marché du travail.",
    "Quand on relie ces quarante ans d'automatisation aux dix virgule trois mille milliards de dette hors bilan finançant l'IA, cette dette cachée agit comme un accélérateur financier.",
    "Les coûts initiaux vertigineux exercent une pression écrasante sur l'industrie de l'IA pour générer des rendements immédiats.",
    "Les investisseurs ne peuvent pas attendre dix ans que les salariés apprennent lentement à utiliser l'IA pour enrichir leurs tâches.",
    "La pression incite fortement les entreprises à déployer l'IA uniquement pour une automatisation immédiate réduisant les coûts.",
    "Le boom de l'IA peut-il continuer sans creuser des inégalités massives ? Les données historiques suggèrent que non, sans changement radical de déploiement.",
    "Si l'IA sert surtout à automatiser, la prochaine décennie reproduira la polarisation salariale des quarante dernières années, accélérée par des milliers de milliards de capitaux cachés.",
    "La recommandation immédiate issue de ces données économiques est une exigence de transparence financière.",
    "Nous avons besoin d'une visibilité claire sur ces structures hors bilan. Les régulateurs doivent surveiller ces expositions en temps réel avant qu'un retournement du marché ne les révèle.",
    "Parallèlement, la société doit suivre précisément quelles tâches humaines l'IA remplace en temps réel pour anticiper l'onde de choc économique.",
    "Le risque ultime du boom de l'IA n'est pas son échec technologique, mais son triomphe financier obtenu en vidant la main-d'œuvre dans l'ombre.",
]

PART4_JA = [
    "2025年から2032年の間に、データセンターや電力網、半導体などAIの物理インフラ建設には10兆3000億ドルがかかると予測されています。",
    "米国のGDPの年平均3.6パーセントに相当するこの投資規模は、鉄道網や高速道路網、農村の電化をも凌駕します。",
    "しかし巨大テック企業の資金調達方法は変化しており、透明性の高い社債からバランスシート外の複雑な金融スキームへと移行しています。",
    "従来の融資ではなく、合弁事業やプライベートクレジット、特別目的事業体といった不透明な仕組みを通じて資金が流れています。",
    "この歴史的規模の負債は巨額かつ大部分が公衆の目から隠されているため、その存続はただ一つの結果にかかっています。",
    "システム全体の信用危機を回避するには、AIが開発企業に持続的で莫大なキャッシュフローを生み出さなければなりません。",
    "隠れた数兆ドルの債務を返済するため、AI企業は法人顧客の運営コストを劇的に削減するツールを販売する必要があります。",
    "歴史的に見て、その規模で企業の利益を最も確実かつ迅速に改善する方法は、人間の労働力を置き換えることです。",
    "これが深刻なジレンマを生みます。もしAIがその収益を生めなければ、社会は隠れ債務危機に直面します。",
    "逆に成功すれば、労働と格差の巨大な危機に直面します。その危機がどう展開するかを理解するには、技術的代替のメカニズムを見る必要があります。",
    "機械が人間の労働を物理的に引き継ぐと何が起きるのか。MITの大規模な経済研究がその枠組みを示しています。",
    "研究者たちは、労働者を補助して生産性と賃金を上げる技術と、単に自動化するだけの技術の2つを区別しています。",
    "このMITの図は自動化の仕組みを示しています。右側では、人間が比較優位を持っていた定型業務を機械が奪うことで資本の境界が拡大しています。",
    "追い出された労働者は消えるわけではありません。残された非自動化職をめぐって競争することになります。",
    "これが波及効果を生み、あらゆる産業で賃金を押し下げます。",
    "技術進歩はすべての労働者を平等に引き上げるわけではありません。自動化は定型業務に特化した人々の市場価値を破壊し、不利益を与えます。",
    "この理論が正しいか推測する必要はありません。1980年から2016年までの米国の賃金データで正確な影響を追跡できます。",
    "このチャートは産業別の労働分配率の低下を示しています。青の全体的な低下と、オレンジの自動化による低下の関係に注目してください。",
    "この数十年間の賃金格差の変化の50から70パーセントが、定型業務の自動化のみによって引き起こされたことがわかります。",
    "この散布図の急激な右肩下がりのトレンドラインは、人間が払った代償を明らかにしています。",
    "業務の代替が最も進んだ層では、実質時給が最大15パーセント下落しました。",
    "これほどの労働者の代替があれば、巨大な経済ブームが伴うと思うかもしれません。",
    "しかし同じ期間に、全体の生産性である全要素生産性は累計でわずか3.4パーセントしか成長しませんでした。",
    "技術は資本所有者にリターンをもたらすだけの人件費さえ削減できればよいのです。",
    "労働市場を完全に塗り替えるのに、ユートピア的な生産性ブームを起こす必要はありません。",
    "この40年間の自動化の歴史を、現在AIを支える10兆3000億ドルの簿外債務と結びつけると、その隠れ債務は金融の加速装置となります。",
    "莫大な初期資本コストは、即座にリターンを生むようAI業界に圧倒的な財務圧力をかけています。",
    "投資家は、労働者が日常業務を補助するためにAIの使い方をゆっくり学ぶのを10年も待つことはできません。",
    "そのプレッシャーが、企業に即効性のあるコスト削減の自動化としてAIを導入させる強い動機となっています。",
    "AIブームは巨大な格差を生まずに続けられるのでしょうか。歴史的データは、導入方法が根本的に変わらない限り不可能であることを強く示唆しています。",
    "もしAIが主に自動化に使われれば、次の10年は過去40年の賃金二極化をそのまま再現し、数兆ドルの隠れ資本によってさらに加速されるでしょう。",
    "この経済データから導かれる当面の政策提言は、金融の透明性の確保です。",
    "簿外構造を可視化し、市場の暴落で隠れ債務が露呈するのを待つのではなく、規制当局が今リアルタイムでリスクを監視する必要があります。",
    "同時に社会は、経済への波及効果に備えるため、AIが人間のどの業務を置き換えているかをリアルタイムで正確に追跡しなければなりません。",
    "AIブームの最大のリスクは技術の失敗ではなく、暗闇の中で労働力を空洞化させることで達成される圧倒的な金融上の成功なのです。",
]

PART5_DE = [
    "Hört man genügend Tech-Podcasts, begegnet man immer wieder exakt derselben Debatte in Endlosschleife.",
    "Die eine Seite behauptet, künstliche Intelligenz werde Millionen Jobs vernichten. Die andere beharrt darauf, sie werde Millionen neue schaffen.",
    "Das Problem ist: Keine Seite kann Ihnen sagen, was konkret mit Ihrem eigenen Gehaltsscheck passiert.",
    "Um zu verstehen, warum alle nur raten, müssen wir ins Jahr 1865 zurückblicken.",
    "Das ist William Stanley Jevons, ein englischer Ökonom, der etwas äußerst Kontraintuitives über Effizienz bemerkte.",
    "Als Dampfmaschinen effizienter wurden, verbrannte Großbritannien nicht weniger Kohle, sondern gewaltig mehr.",
    "Billigere Antriebskraft machte Dampf für Anwendungen wirtschaftlich, an die zuvor niemand gedacht hatte.",
    "Effizienz ließ die Nachfrage nicht schrumpfen, sondern explodieren. Tech-Optimisten übertragen dieses Jevons-Paradoxon auf KI.",
    "Doch einige widersprechen, darunter Bill Gates, der davor warnt, diese Regel auf alles anzuwenden.",
    "Gates verweist auf die Erfindung von Radialreifen: Sie waren viermal haltbarer und effizienter als ihre Vorgänger.",
    "Trotzdem fuhren die Menschen deshalb nicht plötzlich viermal so viel Auto. Manche menschlichen Bedürfnisse haben eine feste Obergrenze.",
    "Die klügsten Köpfe der Tech-Welt geben widersprüchliche Ratschläge, weil sie eine einzige Regel auf tausende völlig verschiedene Berufe anwenden wollen.",
    "Diese Rechnung geht nicht auf. Statt einer Universalregel brauchen Sie eine maßgeschneiderte Karte für Ihren Beruf.",
    "Um die Zukunft eines Jobs vorherzusagen, muss man ihn anhand zweier spezifischer ökonomischer Variablen messen.",
    "Betrachten Sie dieses zweiachsige Koordinatensystem, mit dem wir jeden Beruf einordnen und seinen wirtschaftlichen Wert bestimmen können.",
    "Herauszufinden, wo Ihre tägliche Arbeit in diesem Raum landet, ist der einzige verlässliche Weg zu wissen, ob Sie befördert oder ersetzt werden.",
    "Dieses Diagramm zeigt unsere erste Variable auf der vertikalen Y-Achse: die Nachfrageobergrenze.",
    "Sie misst, ob der menschliche Bedarf nach einer Aufgabe unten gedeckelt ist oder nach oben nahezu unbegrenzt wächst.",
    "Nehmen wir die Steuererklärung als Branche mit niedriger Obergrenze: Selbst wenn KI sie mühelos macht, reicht niemand freiwillig mehr Steuererklärungen ein.",
    "Das Arbeitsvolumen ist dauerhaft gedeckelt, sodass die Beschäftigung in dieser Branche unweigerlich schrumpft.",
    "Vergleichen Sie das mit dem Verfassen von Rechtsklagen, einer Branche mit ferner Obergrenze: Wenn ein Sprachmodell kostenlos Klagen entwirft, ziehen Menschen ständig vor Gericht.",
    "Der Wunsch, Streitigkeiten auszutragen, ist nahezu grenzenlos und treibt die Nachfrage nach dieser Aufgabe weit nach oben.",
    "Ob Ihr Beruf durch Automatisierung wächst oder schrumpft, hängt zuerst davon ab, ob die Nachfrage nach Ihrem Ergebnis eine harte Grenze hat.",
    "Schauen wir nun auf die horizontale X-Achse: Sie steht für die menschliche Kernanforderung.",
    "Sie stellt eine einfache Frage: Kann eine Maschine die Aufgabe links komplett automatisieren, oder wird rechts zwingend ein Mensch benötigt?",
    "Warum das entscheidend ist, zeigt das Beispiel von Geoffrey Hinton, einem Pionier der künstlichen Intelligenz.",
    "2016 machte er eine berühmte Vorhersage über die Medizin: Hochschulen sollten sofort aufhören, Radiologen auszubilden.",
    "Er glaubte, Algorithmen würden die Auswertung medizinischer Bilder innerhalb von fünf Jahren vollständig automatisieren.",
    "Ein Jahrzehnt später erleben Krankenhäuser jedoch einen massiven Mangel an Radiologen.",
    "KI wurde zwar extrem gut beim Lesen von Scans und senkte die Kosten, doch weil Scans billiger wurden, ordneten Ärzte viel mehr davon an.",
    "Hinton übersah den psychologischen Engpass: Wenn Patienten eine lebensverändernde Krebsdiagnose erhalten, wollen sie diese nicht von einem Bot hören.",
    "Sie verlangen die Empathie und Autorität eines menschlichen Arztes. Ersetzt ein Algorithmus Sie komplett, verschwinden die Jobs.",
    "Unterstützt der Algorithmus jedoch einen unverzichtbaren Menschen, fließt die zusätzliche Nachfrage direkt in mehr menschliche Arbeitsplätze.",
    "Kombiniert man Nachfrageobergrenze und menschliche Anforderung, teilt dieses Diagramm die moderne Arbeitswelt in vier Quadranten.",
    "Quadrant eins oben rechts ist der Hauptgewinn: eine ferne Nachfragegrenze gepaart mit zwingender menschlicher Präsenz.",
    "Die Gesamtnachfrage explodiert, der Mensch bleibt unverzichtbar, und Berufe wie Radiologie oder Pflege wachsen rasant.",
    "Quadrant zwei unten links ist die Gefahrenzone: Die Nachfrage ist gedeckelt und die Aufgaben sind leicht automatisierbar.",
    "In Bereichen wie der Steuerberatung schrumpft die Beschäftigung. Quadrant drei oben links ist die Paradox-Zone.",
    "Hier gibt es zwar unbegrenzte Nachfrage, aber leicht automatisierbare Arbeit: Bei digitaler Content-Erstellung explodiert das Volumen, doch die Zahl menschlicher Jobs stagniert.",
    "Quadrant vier unten rechts schließlich ist die Nischenzone: Die Nachfrage ist begrenzt, aber Menschen sind absolut unverzichtbar.",
    "Das sind kleine, stabile, menschenzentrierte Dienstleistungen. Jeder moderne Beruf, auch Ihrer, wird derzeit in eines dieser vier Felder sortiert.",
    "Das Jevons-Paradoxon garantiert nicht Ihre Sicherheit, und künstliche Intelligenz garantiert nicht Ihren Untergang.",
    "KI ist schlicht ein ökonomischer Kraftverstärker. Wir erleben in Echtzeit eine gewaltige wirtschaftliche Neuordnung.",
    "Millionen einzelner Rollen weltweit zerstreuen sich und sammeln sich in diesen vier Ecken neu.",
    "Sie müssen Ihre tägliche Arbeit nüchtern betrachten und herausfinden, wo genau Sie stehen.",
    "Fragen Sie sich: Gibt es eine feste Obergrenze für mein Arbeitsvolumen, und verlangen Menschen wirklich einen Menschen für die Bereitstellung?",
    "Wie die alte Metapher sagt: Manchmal ist man die Windschutzscheibe und manchmal das Insekt.",
    "Bewerten Sie Ihren Quadranten ehrlich. Der sicherste Zug ist es, Ihre Fähigkeiten Richtung Quadrant eins zu steuern, bevor die Sortierung abgeschlossen ist.",
]

PART5_FR = [
    "Écoutez assez de podcasts tech et vous entendrez exactement le même débat tourner en boucle.",
    "Un camp affirme que l'intelligence artificielle va supprimer des millions d'emplois ; l'autre assure qu'elle en créera des millions d'autres.",
    "Le problème, c'est qu'aucun des deux ne peut vous dire ce qu'il adviendra de votre propre fiche de paie.",
    "Pour comprendre pourquoi tout le monde tâtonne, il faut remonter à 1865.",
    "Voici William Stanley Jevons, un économiste anglais qui a remarqué quelque chose de très contre-intuitif sur l'efficacité.",
    "À mesure que les machines à vapeur devenaient plus efficaces, la Grande-Bretagne n'a pas brûlé moins de charbon : elle en a brûlé beaucoup plus.",
    "Une énergie moins chère a rendu la vapeur rentable pour des usages auxquels personne n'avait songé auparavant.",
    "L'efficacité n'a pas réduit la demande, elle l'a libérée. Les optimistes appliquent ce paradoxe de Jevons à l'IA.",
    "Mais certains contestent, comme Bill Gates, qui refuse d'appliquer cette règle à tout.",
    "Gates cite l'invention des pneus radiaux, quatre fois plus durables et efficaces que leurs prédécesseurs.",
    "Pourtant, les gens ne se sont pas mis à conduire quatre fois plus. Certains besoins humains ont un plafond strict.",
    "Les voix les plus brillantes de la tech donnent des conseils contradictoires parce qu'elles appliquent une seule règle économique à des milliers de métiers différents.",
    "Ce calcul ne fonctionne tout simplement pas. Au lieu d'une règle universelle, il vous faut une carte sur mesure pour évaluer votre carrière.",
    "Prédire l'avenir d'un métier exige de le mesurer selon deux variables économiques très précises.",
    "Regardez ce système de coordonnées à deux axes : il permet de situer n'importe quelle profession et sa vraie valeur économique.",
    "Découvrir où se situe votre travail quotidien dans cet espace est le seul moyen fiable de savoir si vous serez promu ou remplacé.",
    "Ce graphique met en évidence notre première variable sur l'axe vertical Y : le plafond de la demande.",
    "Il mesure si le désir humain pour une tâche est plafonné vers le bas ou s'étend à l'infini vers le haut.",
    "Prenez la déclaration fiscale, un secteur à plafond bas : même si une IA la rend sans effort, les citoyens ne déclareront pas plus d'impôts pour le plaisir.",
    "Le volume total de travail est plafonné en permanence, ce qui signifie que l'emploi dans ce secteur va inévitablement reculer.",
    "Comparez cela à la rédaction de plaintes juridiques, un secteur à plafond éloigné : si un modèle rédige un recours efficace gratuitement, les gens iront constamment en justice.",
    "Le désir humain de résoudre des litiges est quasi illimité, poussant la demande pour cette tâche tout en haut.",
    "Que votre métier grandisse ou recule sous l'effet de l'automatisation dépend d'abord de l'existence d'un plafond strict à la demande.",
    "Regardez maintenant l'axe horizontal X : il représente l'exigence humaine fondamentale.",
    "Il pose une question simple : une machine peut-elle tout automatiser à gauche, ou un humain est-il strictement requis à droite ?",
    "Pour comprendre pourquoi c'est crucial, regardez Geoffrey Hinton, pionnier de l'intelligence artificielle.",
    "En 2016, il a fait une prédiction célèbre sur la médecine, affirmant que les facultés devaient cesser de former des radiologues.",
    "Il pensait que les algorithmes automatiseraient parfaitement l'interprétation des scanners médicaux en cinq ans.",
    "Dix ans plus tard, les hôpitaux font face à une pénurie massive de radiologues.",
    "L'IA est devenue excellente pour lire les scanners, ce qui a fait baisser les coûts ; comme ils étaient moins chers, les médecins en ont prescrit beaucoup plus.",
    "Hinton avait manqué le goulet d'étranglement psychologique : face à un diagnostic de cancer, un patient refuse de l'entendre d'un robot.",
    "Il exige l'empathie et l'autorité d'un médecin humain dans la pièce. Si un algorithme vous remplace totalement, les emplois disparaissent.",
    "Mais si cet algorithme augmente un humain indispensable, la demande supplémentaire se transforme directement en emplois humains.",
    "En combinant plafond de demande et exigence humaine, ce graphique divise toute la main-d'œuvre moderne en quatre quadrants.",
    "Le quadrant un, en haut à droite, est le gros lot : un plafond éloigné associé à une exigence humaine stricte.",
    "La demande totale explose, l'humain reste dans la boucle, et des métiers comme la radiologie ou les soins infirmiers croissent rapidement.",
    "Le quadrant deux, en bas à gauche, est la zone de danger : le plafond de demande est proche et les tâches sont très automatisables.",
    "Dans des domaines comme la préparation fiscale, l'emploi global recule. Le quadrant trois, en haut à gauche, est la zone du paradoxe.",
    "Il combine une demande illimitée et un travail très automatisable : dans la création de contenu numérique, le volume explose mais l'emploi humain stagne.",
    "Enfin, le quadrant quatre, en bas à droite, est la zone de niche : le plafond est proche, mais les humains sont absolument indispensables.",
    "Ce sont de petits services centrés sur l'humain et très stables. Chaque profession moderne, y compris la vôtre, est en train d'être classée dans l'une de ces quatre cases.",
    "Le paradoxe de Jevons ne garantit pas votre sécurité, et l'intelligence artificielle ne garantit pas votre perte.",
    "L'IA est simplement un multiplicateur de force économique. Nous assistons en temps réel à un immense tri économique.",
    "Des millions de rôles à travers le monde se dispersent et se regroupent dans ces quatre coins.",
    "Vous devez examiner objectivement votre production quotidienne et déterminer exactement où vous atterrissez.",
    "Demandez-vous : existe-t-il un plafond strict au volume de travail que je produis, et les gens ont-ils vraiment besoin d'un humain pour le recevoir ?",
    "Comme le dit la vieille métaphore de l'automatisation : parfois vous êtes le pare-brise, et parfois vous êtes l'insecte.",
    "Évaluez honnêtement votre quadrant. Le choix le plus sûr consiste à orienter vos compétences vers le quadrant un bien avant la fin du tri.",
]

PART5_JA = [
    "テック系ポッドキャストを十分に聴けば、まったく同じ議論が無限ループしていることに気づくでしょう。",
    "一方は人工知能が何百万もの仕事を奪うと主張し、もう一方は何百万もの新たな仕事を生むと主張します。",
    "問題は、どちらの陣営もあなたの給与明細に何が起きるのかを実際には教えてくれないことです。",
    "なぜ全員が推測で語っているのかを理解するには、1865年まで遡る必要があります。",
    "こちらはイギリスの経済学者ウィリアム・スタンレー・ジェヴォンズです。彼は効率性に関して極めて直感に反する現象に気づきました。",
    "蒸気機関の効率が向上したとき、イギリスは石炭の消費を減らすどころか、以前よりはるかに大量の石炭を燃やしたのです。",
    "動力が安くなったことで、それまで誰も試みなかった用途にまで蒸気を使う採算が取れるようになりました。",
    "効率化は需要を縮小させるのではなく、解き放ったのです。テック楽観主義者はこのジェヴォンズのパラドックスをAIに当てはめます。",
    "しかし異議を唱える人もいます。ビル・ゲイツは、この法則をあらゆるものに適用することに反対しています。",
    "ゲイツはラジアルタイヤの発明を例に挙げます。従来のタイヤより4倍長持ちし、効率も優れたものでした。",
    "しかしその結果として人々が突然4倍多く運転するようになったわけではありません。人間のニーズには明確な上限があるものも存在するのです。",
    "テック界の最も賢明な人々が相反する助言をするのは、数千もの異なる職業にたった一つの経済法則を当てはめようとしているからです。",
    "その計算は成り立ちません。普遍的な法則を探すのではなく、自分のキャリアを評価するための専用の地図が必要です。",
    "仕事の将来を予測するには、2つの明確な経済変数に照らして測定する必要があります。",
    "この2軸の座標系を見てください。あらゆる職業をここにプロットし、その真の経済的価値を見極めることができます。",
    "日々の仕事がこの空間のどこに位置するかを把握することこそ、昇進するか置き換えられるかを知る唯一の確実な方法です。",
    "縦のY軸は1つ目の変数である需要の上限を示しています。",
    "特定の業務に対する人間の需要が低い位置で頭打ちになるか、上に向かって無限に伸びるかを測るものです。",
    "上限が低い業界として税務申告を考えてみましょう。AIアプリで確定申告がどれほど簡単になっても、市民が自発的に申告回数を増やすことはありません。",
    "仕事量の総枠が恒久的に決まっているため、その業界の雇用は必然的に縮小します。",
    "これを上限が遠い法的な訴状作成と比較してみましょう。言語モデルが無料で効果的な訴状を作成できれば、人々は絶えず不満を法廷に持ち込むようになります。",
    "紛争を解決したいという人間の欲求はほぼ無限であり、この業務への需要を最上部へと押し上げます。",
    "自動化によってあなたの職業が拡大するか縮小するかは、まずその成果物への需要に明確な上限があるかどうかにかかっています。",
    "次に横のX軸を見てください。これは人間であることの必須要件を表しています。",
    "投げかける問いは単純です。左側のように機械が完全に自動化できるか、それとも右側のように人間が提供することが不可欠かという点です。",
    "なぜこれが重要なのかを見るために、人工知能のパイオニアであるジェフリー・ヒントンを見てみましょう。",
    "2016年、彼は医療分野について有名な予測をし、医学部は放射線科医の育成を完全にやめるべきだと主張しました。",
    "アルゴリズムが5年以内に医療画像の読影を完全に自動化すると考えたのです。",
    "それから10年後、病院は放射線科医の深刻な不足に直面しています。",
    "実際AIは画像読影に極めて長けるようになりコストを下げましたが、検査が安くなったため医師がはるかに多くの検査を発注するようになりました。",
    "ヒントンは心理的なボトルネックを見落としていました。患者が人生を左右するがんの診断を受けるとき、ボットから聞くことを拒むのです。",
    "患者は同じ部屋にいる人間の医師の共感と権威を求めます。アルゴリズムがあなたを完全に代替するなら仕事は消えます。",
    "しかしアルゴリズムが必要不可欠な人間を補助するなら、増えた需要はそのまま人間の雇用の増加へとつながります。",
    "需要の上限と人間の必須要件を組み合わせると、現代の労働力は4つの象限に分けられます。",
    "右上の第1象限は大当たりの領域です。需要の上限が遠く、かつ人間が厳密に必要とされる領域です。",
    "総需要が爆発的に増え、人間がループの中に残り、放射線科医や看護師のような仕事が急速に伸びます。",
    "左下の第2象限は危険地帯です。需要の上限が近く、業務の自動化も容易な領域です。",
    "税務申告のような分野では雇用全体が縮小します。左上の第3象限はパラドックス地帯です。",
    "需要の上限は遠いものの自動化しやすい仕事で、デジタルコンテンツ制作のように仕事量は爆発しても人間の雇用数は横ばいのままです。",
    "最後に右下の第4象限はニッチ地帯です。需要の上限は近いものの、人間が絶対不可欠な領域です。",
    "小規模で安定した人間中心のサービスがこれにあたります。あなたの仕事を含むすべての現代の職業が、今この4つの箱のどれかに振り分けられています。",
    "ジェヴォンズのパラドックスがあなたの安全を保証するわけでも、人工知能があなたの破滅を保証するわけでもありません。",
    "AIは単なる経済的な力の増幅器です。私たちは今、リアルタイムで進行する巨大な経済的選別を目撃しています。",
    "世界中の何百万もの職務が散らばり、この4つの角へと再集結しています。",
    "自分自身の毎日の成果物を客観的に見つめ、自分がどこに着地するかを正確に見極める必要があります。",
    "自分が作り出す仕事の量に明確な上限があるか、そして人々が本当に人間からそれを受け取ることを求めているかを自問してください。",
    "自動化の古い比喩にある通り、時にはあなたがフロントガラスになり、時には虫になります。",
    "自分の象限を正直に評価してください。最終的な選別が終わる前に、第1象限へとスキルを舵取りすることが最も安全な一手です。",
]


def main() -> None:
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    p4_chunks = json.loads((OUT_DIR / "_part_4_chunks.json").read_text(encoding="utf-8"))
    p5_chunks = json.loads((OUT_DIR / "_part_5_chunks.json").read_text(encoding="utf-8"))

    # Compute exact start offset of each part in final_comp.mp4
    # Sequence: intro (20s), part_1, card_2 (4s), part_2, card_3 (4s), part_3, card_4 (4s), part_4, card_5 (4s), part_5, card_6 (4s), part_6, outro (5s)
    t = ffdur(OUT_DIR / "intro.mp4")
    part_offsets = {}
    part_durs = {}
    for n in range(1, 7):
        if n > 1:
            t += ffdur(OUT_DIR / f"card_{n}.mp4")
        part_offsets[n] = t
        d = ffdur(OUT_DIR / f"part_{n}.mp4")
        part_durs[n] = d
        t += d

    p1_dir = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-11-the-ai-bottleneck-why-exponential-tech-is-trapped-in-a-linear-world")
    p2_dir = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-09-09-anthropic-economic-scenarios")
    p3_dir = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-12-labor-llm-language-based-occupational-representations-with-large-language-models")
    p6_dir = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-12-the-white-collar-bypass")

    for lang in ("en", "de", "fr", "ja"):
        all_blocks = [{
            "start": 0.0,
            "end": 18.93,
            "text": INTRO_TEXT[lang],
        }]

        # Part 1: raw_cinematic (drop block 0 hook VO, shift by 15.76s)
        p1_srt = p1_dir / f"the-ai-bottleneck-why-exponential-tech-is-trapped-in-a-linear-world_{lang}.srt"
        for b in parse_srt(p1_srt)[1:]:
            st = max(0.0, b["start"] - 15.76)
            en = min(part_durs[1], b["end"] - 15.76)
            if en > st + 0.2:
                all_blocks.append({"start": part_offsets[1] + st, "end": part_offsets[1] + en, "text": b["text"]})

        # Part 2: final_long trimmed at 17.67s (drop block 0 hook VO, shift by 17.67s)
        if lang == "ja":
            p2_en = parse_srt(p2_dir / "anthropic-economic-scenarios_en.srt")[1:]
            for b, ja_txt in zip(p2_en, PART2_JA):
                st = max(0.0, b["start"] - 17.67)
                en = min(part_durs[2], b["end"] - 17.67)
                if en > st + 0.2:
                    all_blocks.append({"start": part_offsets[2] + st, "end": part_offsets[2] + en, "text": ja_txt})
        else:
            p2_srt = p2_dir / f"anthropic-economic-scenarios_{lang}.srt"
            for b in parse_srt(p2_srt)[1:]:
                st = max(0.0, b["start"] - 17.67)
                en = min(part_durs[2], b["end"] - 17.67)
                if en > st + 0.2:
                    all_blocks.append({"start": part_offsets[2] + st, "end": part_offsets[2] + en, "text": b["text"]})

        # Part 3: raw_cinematic (drop blocks 0..1 hook VO ending at 15.60s, shift by 15.60s)
        p3_srt = p3_dir / f"labor-llm-language-based-occupational-representations-with-large-language-models_{lang}.srt"
        for b in parse_srt(p3_srt)[2:]:
            st = max(0.0, b["start"] - 15.60)
            en = min(part_durs[3], b["end"] - 15.60)
            if en > st + 0.2:
                all_blocks.append({"start": part_offsets[3] + st, "end": part_offsets[3] + en, "text": b["text"]})

        # Part 4: _part_4_chunks.json (already relative to part_4.mp4!)
        p4_texts = [c["text"] for c in p4_chunks] if lang == "en" else (PART4_DE if lang == "de" else (PART4_FR if lang == "fr" else PART4_JA))
        for c, txt in zip(p4_chunks, p4_texts):
            all_blocks.append({"start": part_offsets[4] + c["start"], "end": part_offsets[4] + min(part_durs[4], c["end"]), "text": txt})

        # Part 5: _part_5_chunks.json (already relative to part_5.mp4!)
        p5_texts = [c["text"] for c in p5_chunks] if lang == "en" else (PART5_DE if lang == "de" else (PART5_FR if lang == "fr" else PART5_JA))
        for c, txt in zip(p5_chunks, p5_texts):
            all_blocks.append({"start": part_offsets[5] + c["start"], "end": part_offsets[5] + min(part_durs[5], c["end"]), "text": txt})

        # Part 6: raw_cinematic (drop block 0 hook VO ending at 18.62s, shift by 18.62s)
        p6_srt = p6_dir / f"the-white-collar-bypass_{lang}.srt"
        for b in parse_srt(p6_srt)[1:]:
            st = max(0.0, b["start"] - 18.62)
            en = min(part_durs[6], b["end"] - 18.62)
            if en > st + 0.2:
                all_blocks.append({"start": part_offsets[6] + st, "end": part_offsets[6] + en, "text": b["text"]})

        lines = []
        for idx, b in enumerate(all_blocks, 1):
            lines.append(f"{idx}\n{fmt_ts(b['start'])} --> {fmt_ts(b['end'])}\n{b['text']}\n")
        out_srt = OUT_DIR / f"{SLUG}_{lang}.srt"
        out_srt.write_text("\n".join(lines), encoding="utf-8")
        shutil.copy2(out_srt, STAGE_DIR / out_srt.name)
        print(f"Wrote {out_srt.name} ({len(all_blocks)} blocks)")


if __name__ == "__main__":
    main()
