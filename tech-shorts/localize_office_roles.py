#!/usr/bin/env python3
import json, shutil, sys
from pathlib import Path

# Add tech-shorts directory
sys.path.insert(0, "/Users/miguelrodriguez/projects/agentic-fleet-hub/tech-shorts")
from run_batch_localize import write_srt, ffdur, log, DOWNLOADS_STAGING
import localize as L

ASSET_DIR = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-18-ai-transforms-office-roles")
FINAL_VIDEO = ASSET_DIR / "final_long.mp4"
SLUG = "ai-transforms-office-roles"
STAGING_DIR = DOWNLOADS_STAGING / SLUG
STAGING_DIR.mkdir(parents=True, exist_ok=True)

with open(ASSET_DIR / "whisper_chunks.json") as f:
    chunks = json.load(f)

texts_en = [c["text"] for c in chunks]

texts_de = [
    "Was geschieht mit Ihrer Arbeit, wenn KI-Kollegen die Menschen im Verhältnis sechs zu eins überflügeln?",
    "Bei Anthropic leisten interaktive Agenten mittlerweile den Großteil der Arbeitsstunden und verwandeln das moderne Büro vom Ausführen einzelner Aufgaben in das Dirigieren von Maschinen. Willkommen in der Zukunft der Arbeit.",
    "Willkommen in der Zukunft der Arbeit. Willkommen zum heutigen Erklärvideo. Heute tauchen wir direkt in den tatsächlichen Büroalltag ein, der vollständig durch künstliche Intelligenz transformiert wurde.",
    "Wir hören zahllose Theorien über die Zukunft der Arbeit, nicht wahr? Doch heute stützen wir uns auf handfeste Daten.",
    "Als Fallstudie dient uns ein umfassender interner Bericht von Anthropic aus dem Jahr zweitausendsechsundzwanzig, um zu analysieren, wie tiefgreifende KI-Integration Arbeitsnachfrage und menschliches Verhalten radikal umgestaltet.",
    "Legen wir direkt los. Zu Beginn werfen wir einen Blick auf eine absolut verblüffende Zahl.",
    "Bis zum August zweitausendsechsundzwanzig übertrafen die Arbeitsstunden interaktiver KI-Agenten bei Anthropic jene der menschlichen Mitarbeiter um das Sechsfache.",
    "Denken Sie kurz darüber nach: Wir sprechen hier nicht von einem kleinen Werkzeug, das man gelegentlich nutzt, um eine Tabelle zu formatieren.",
    "Die menschlichen Mitarbeiter bilden im Grunde nur noch eine hauchdünne Schicht an der Spitze eines rasant wachsenden Heers digitaler Arbeitskräfte, während die KI den überwältigenden Großteil der aktiven Arbeit im Unternehmen verrichtet.",
    "Und wegen dieses extremen Verhältnisses verändert sich das tägliche Arbeitserlebnis von Grund auf.",
    "Ein sichtlich geforderter Entwickler beschrieb diesen Wandel treffend: Die Arbeit gleiche einer parallelen Belegschaft, bei der man ständig eine Armee von KI-Assistenten leitet, buchstäblich einem Heer von Claudes gegenübersteht, von denen jeder nach Aufmerksamkeit verlangt.",
    "Man erledigt nicht mehr bloß eine isolierte Einzelaufgabe. Plötzlich dirigiert, prüft und koordiniert man eine ganze Flotte digitaler Mitarbeiter.",
    "Die entscheidende Frage unseres heutigen Videos lautet daher: Was geschieht mit Ihrem Beruf, wenn die KI-Kollegen Sie um sechs zu eins überragen?",
    "Wenn der handwerkliche Umsetzungsteil Ihrer Arbeit plötzlich vollständig automatisiert ist, was bleibt dann für Sie zu tun?",
    "Betrachten wir die unmittelbaren Folgewirkungen dieses gigantischen Umbruchs. Erster Abschnitt: Die Produktivitätsexplosion und der Turbo für den Output.",
    "Sehen wir, wie daraus ein unternehmensweiter Produktivitätsboom erwächst. Das Faszinierende: Es betrifft nicht nur Softwareentwickler, deren Code-Commit-Geschwindigkeit sich immerhin verfünffacht hat.",
    "Dieser Schub erfasst jede Abteilung: Vertriebsmitarbeiter lagern Standard-E-Mails komplett aus und gewinnen dreißig Prozent mehr persönliche Gesprächszeit mit Kunden.",
    "Und Personalvermittler? Sie verkürzen die tagelange Kandidatensuche auf wenige Stunden. Die Arbeitsleistung schießt schlicht überall durch die Decke.",
    "Zweiter Abschnitt: Der menschliche Engpass. Wer bremst hier wen aus? Genau hier nimmt die Entwicklung eine hochinteressante Wendung.",
    "Die KI hat alle blitzschnell gemacht, aber sie schuf ein völlig unerwartetes Problem: Wir Menschen sind es nun, die die KI ausbremsen.",
    "Das enorme Volumen der von diesen Agenten erzeugten Inhalte ist so gewaltig, dass allein das aufmerksame Lesen zu einem Vollzeitjob wird.",
    "Rein nach Textmenge müsste selbst ein Mitarbeiter ohne technischen Hintergrund bis zu fünfzig Prozent seiner gesamten Arbeitswoche investieren, nur um die Ergebnisse seiner Agenten zu sichten.",
    "Die Mitarbeiter werden ununterbrochen von Texten, Programmcode und Entscheidungsfragen auf ihren Bildschirmen überschwemmt.",
    "Ich finde die Schilderung eines Mitarbeiters großartig, der diese Realität mit Babysitten verglich: Die Agenten verhielten sich ein wenig wie Kleinkinder.",
    "Ein Agent hat vielleicht einen kritischen Fehler entdeckt, was einem Schnitt in den Finger gleicht, während ein anderer bloß ein Saftpäckchen geöffnet haben will, weil ein kleiner Formatierungsfehler vorliegt.",
    "Der Haken dabei ist: Die KI trägt Ihnen beide Anliegen mit exakt derselben dringlichen Panik vor.",
    "Jeder Agent fordert gleichermaßen Ihre Aufmerksamkeit ein, und der Mensch muss verzweifelt versuchen, dieses Durcheinander zu priorisieren.",
    "Das Ergebnis dieses menschlichen Flaschenhalses ist verblüffend: Bei interaktiven Sitzungen verbringt ein KI-Agent erstaunliche achtzig Prozent seiner Zeit untätig mit dem Warten darauf, dass der Mensch Anweisungen erteilt, Fehler korrigiert oder Arbeiten freigibt.",
    "Nur zwanzig Prozent der Zeit arbeitet die KI aktiv. Die Maschine ist unfassbar schnell, dreht aber meistens digital Däumchen und wartet darauf, dass das langsamere menschliche Gehirn nachkommt und grünes Licht gibt.",
    "Dritter Abschnitt: Der Aufstieg der Meta-Arbeit. Vom Ausführen zum Verwalten. Um diesen erdrückenden Engpass zu überwinden, reicht es nicht, einfach härter zu arbeiten.",
    "Man muss in die Ära der sogenannten Meta-Arbeit eintreten: Statt selbst Code zu schreiben oder E-Mails zu verfassen, löst man sich ganz von der einzelnen Aufgabe.",
    "Man baut Dashboards, verfasst ständige Anweisungen und gestaltet Pipelines. Im Grunde betreibt man Suchmaschinenoptimierung für die eigene KI und schafft Rahmenwerke, damit Agenten autonom Lösungen finden, ohne alle fünf Minuten anzuklopfen.",
    "Um das Ausmaß zu verdeutlichen: Die Zahl schriftlicher Daueranweisungen für Agenten bei Anthropic explodierte von wenigen Hundert im Juli zweitausendfünfundzwanzig auf über achttausendfünfhundert nur ein Jahr später.",
    "Die Mitarbeiter verwenden einen Großteil ihrer Zeit darauf, ihr eigenes Expertenwissen zu kodifizieren und ihre alltäglichen Aufgaben bewusst wegzuautomatisieren.",
    "Vierter Abschnitt: Wandel der Einstellungsprioritäten. Wer bekommt jetzt noch den Job? Wenn sich die Arbeit so drastisch vom Ausführen zur Führung einer Flotte wandelt, wen stellt man dann überhaupt noch ein?",
    "Die Daten zeichnen ein ernüchterndes Bild für Einsteigerpositionen: Der Anteil von Nachwuchskräften bei technischen Neueinstellungen brach drastisch ein, von siebenundzwanzig Prozent auf nur noch neun Prozent.",
    "Weil die KI die grundlegende Umsetzung nahtlos übernimmt, bricht der Bedarf an menschlicher Routinearbeit rapide ein.",
    "Der Wandel des Anforderungsprofils ist glasklar: Früher honorierten Unternehmen eng umrissene Fachkompetenz und reine Ausführungsfähigkeiten.",
    "Heute rücken Personalverantwortliche bewusst davon ab und suchen Bewerber mit hoher Autonomie, starkem Urteilsvermögen und der Fähigkeit, diese KI-Werkzeuge strategisch zu steuern.",
    "Wie eine Führungskraft betonte, sind KI-Modelle in ihren Fähigkeiten ungleichmäßig: Man braucht vielseitige Mitarbeiter, die eingreifen, die KI lenken und urteilen, wenn die Maschine steckenbleibt.",
    "Fünfter Abschnitt: Der Weg nach vorn. Anpassung an das KI-Büro. Blicken wir auf die makroökonomischen Folgen und darauf, wie Unternehmen und Beschäftigte diesen Wandel meistern können.",
    "Der Ansatz von Anthropic bietet einen klaren Leitfaden: Erstens müssen Frühwarnsysteme aufgebaut werden, um bedrohte Rollen frühzeitig zu erkennen.",
    "Zweitens: Wenn Tätigkeiten automatisiert werden, sollten Mitarbeiter vorrangig intern auf anspruchsvollere Aufgaben umgeschult werden, statt Entlassungen auszusprechen.",
    "Und drittens, ganz entscheidend: Es muss sichergestellt werden, dass die Mitarbeiter am finanziellen Erfolg dieses Produktivitätsbooms teilhaben.",
    "Der Bericht zieht eine treffende Parallele zu den Gewerkschaftsabkommen nach dem Zweiten Weltkrieg: Wer will, dass Mitarbeiter ihr Wissen für Maschinen bereitstellen, muss ihre Interessen mit dem Unternehmenserfolg verknüpfen.",
    "Niemand tut das umsonst. Und das führt uns zu einer ermutigenden Erkenntnis.",
    "Die wichtigste Erkenntnis lautet: Während KI-Agenten die reine Ausführung übernehmen, bleiben menschliches Vertrauen, Verantwortlichkeit und persönliche Koordination das unverzichtbare Herzstück des Büros.",
    "In einem KI-intensiven Umfeld müssen Entscheidungen offen getroffen werden: Man braucht weiterhin Meetings, Strategiediskussionen und dokumentierten Kontext, damit die Flotte das richtige Ziel ansteuert.",
    "Reine Routinearbeit tritt in den Hintergrund, wodurch echte menschliche Qualitäten wie Urteilsvermögen und persönliche Beziehungen zum wertvollsten Gut im Unternehmen werden.",
    "Das moderne Büro verwandelt sich grundlegend von einem Ort des reinen Tuns in einen Ort des Dirigierens.",
    "Während auch Ihr eigener Arbeitsplatz diesem Wendepunkt entgegengeht, möchten wir Ihnen eine entscheidende Frage mitgeben:",
    "Wenn die künstliche Intelligenz die operative Arbeit schneller erledigt als Sie jemals zuvor, sind Sie dann bereit, die Maschine zu führen?",
    "Vielen Dank, dass Sie bei diesem Erklärvideo dabei waren. Wir hoffen, dieser Leitfaden hilft Ihnen bei der Orientierung in der nahen Zukunft der Arbeit."
]

texts_fr = [
    "Qu'advient-il de votre travail quand les collègues IA surpassent les humains à six contre un ?",
    "Chez Anthropic, les agents interactifs enregistrent désormais la grande majorité des heures de travail, transformant le bureau moderne de l'exécution de tâches vers l'orchestration de machines. Bienvenue dans le futur du travail.",
    "Bienvenue dans le futur du travail. Bienvenue dans cette vidéo explicative. Aujourd'hui, nous plongeons dans la réalité quotidienne d'un bureau entièrement transformé par l'intelligence artificielle.",
    "On entend énormément de théories sur l'avenir du travail, n'est-ce pas ? Mais aujourd'hui, nous disposons de données concrètes.",
    "Nous prenons pour étude de cas un rapport interne complet d'Anthropic d'octobre deux mille vingt-six, afin d'explorer comment l'IA restructure le travail, la demande et les comportements humains.",
    "Entrons directement dans le vif du sujet avec un chiffre proprement vertigineux.",
    "Dès le mois d'août deux mille vingt-six, chez Anthropic, les heures effectuées par les agents IA interactifs dépassaient celles des employés humains à six contre un.",
    "Songez-y un instant : il ne s'agit pas d'un simple utilitaire utilisé pour formater une feuille de calcul.",
    "Les humains sont devenus une très fine couche superposée à un contingent de travailleurs numériques en pleine expansion, l'IA assurant la vaste majorité des heures actives de toute l'entreprise.",
    "En raison de cette proportion inédite, l'expérience même du travail se trouve radicalement bouleversée.",
    "Un ingénieur quelque peu submergé a parfaitement décrit ce paysage : le travail est devenu une force parallèle où l'on supervise en permanence une armée d'assistants IA, faisant face à une légion de Claudes réclamant tous de l'attention.",
    "On ne réalise plus une tâche isolée : on orchestre, examine et répond soudain à toute une flotte d'assistants numériques.",
    "La question fondamentale que nous voulons explorer aujourd'hui est la suivante : qu'advient-il de votre poste quand vos collègues IA vous surpassent à six contre un ?",
    "Lorsque la part d'exécution concrète de votre travail est subitement automatisée, que vous reste-t-il exactement à faire ?",
    "Examinons les répercussions directes de cette transition majeure. Première partie : l'explosion de productivité qui décuple les résultats.",
    "Voyons comment s'articule ce boom de productivité à l'échelle de l'entreprise. Ce qui est captivant, c'est que cela ne concerne pas seulement les développeurs, dont la vitesse de livraison de code a été multipliée par cinq.",
    "Cette explosion traverse chaque département : les commerciaux délèguent totalement les courriels de routine, gagnant trente pour cent de temps d'échange direct avec leurs clients.",
    "Les recruteurs ? Ils réduisent une recherche de candidats d'une semaine à quelques heures. Les résultats montent en flèche dans tous les domaines.",
    "Deuxième partie : le goulet d'étranglement humain. Qui ralentit qui ? C'est ici que l'histoire prend un tournant particulièrement saisissant.",
    "L'IA a rendu tout le monde d'une rapidité fulgurante, mais a créé un problème inattendu : ce sont désormais les humains qui ralentissent l'IA.",
    "Le volume de contenu produit par ces agents est si massif que le simple fait de tout lire devient en soi un travail à plein temps.",
    "Au seul vu du volume de texte, même un employé non technique devrait consacrer jusqu'à cinquante pour cent de sa semaine rien qu'à lire le travail de ses agents.",
    "Les salariés se retrouvent submergés d'un flot continu de textes, de code et d'arbitrages surgissant sur leurs écrans.",
    "L'illustration donnée par un employé résume parfaitement cette réalité via la métaphore de la garde d'enfants : les agents se comportent un peu comme des tout-petits.",
    "Un agent signale un bug critique, l'équivalent d'un doigt coupé, tandis qu'un autre a juste besoin qu'on lui ouvre sa brique de jus pour un léger souci de mise en page.",
    "Le problème, c'est que l'IA vous présente ces deux questions avec exactement le même degré d'urgence affolé.",
    "Chaque agent exige votre attention avec la même intensité, laissant l'humain trier dans l'urgence tout ce flux continu.",
    "Le résultat de ce goulet d'étranglement est frappant : dans les sessions interactives, un agent IA passe près de quatre-vingts pour cent de son temps à attendre passivement qu'un humain lui donne des consignes, corrige une erreur ou valide son travail.",
    "L'IA ne travaille activement que vingt pour cent du temps. La machine est ultra-rapide, mais passe le plus clair de son temps à attendre que le cerveau humain, plus lent, prenne le relais et donne son feu vert.",
    "Troisième partie : l'avènement du méta-travail. De l'exécution au pilotage. Pour résoudre ce goulet d'étranglement, travailler plus dur ne suffit pas.",
    "Il faut entrer dans l'ère du méta-travail : plutôt que d'écrire du code ou de rédiger des courriels soi-même, on s'abstrait totalement de la tâche directe.",
    "On construit des tableaux de bord, on rédige des protocoles permanents, on conçoit des pipelines. C'est presque du référencement pour sa propre IA, créant des repères pour que les agents trouvent les réponses seuls, sans sollicitation continue.",
    "Pour mesurer l'ampleur du phénomène : le nombre de consignes permanentes écrites pour les agents chez Anthropic a bondi de quelques centaines en juillet deux mille vingt-cinq à plus de huit mille cinq cents un an après.",
    "Les équipes consacrent une large part de leur temps à formaliser leur expertise, automatisant délibérément leurs tâches quotidiennes.",
    "Quatrième partie : l'évolution des priorités de recrutement. Qui est embauché aujourd'hui ? Si le travail consiste désormais à superviser des agents plutôt qu'à exécuter, quels profils recherche-t-on ?",
    "Les données révèlent une réalité frappante pour les débutants : la part des embauches de profils techniques juniors a chuté de manière spectaculaire, passant de vingt-sept pour cent à seulement neuf pour cent.",
    "L'IA prenant directement en charge l'exécution de base, la demande pour le travail d'entrée de gamme recule à toute vitesse.",
    "L'évolution des attentes est limpide : autrefois, les entreprises privilégiaient une expertise pointue et une rigueur d'exécution pure.",
    "Désormais, les recruteurs privilégient l'autonomie, un jugement humain solide et la capacité créative à orchestrer ces outils d'IA.",
    "Comme le souligne un manager, les capacités des modèles sont inégales : il faut des employés polyvalents, capables d'intervenir et de trancher quand la machine bute.",
    "Cinquième partie : la voie à suivre. S'adapter au bureau sous IA. Élargissons la perspective pour voir comment entreprises et salariés peuvent négocier cette transition majeure.",
    "L'approche d'Anthropic propose une feuille de route claire : d'abord, concevoir des systèmes d'alerte précoce pour identifier les métiers directement exposés.",
    "Deuxièmement : à mesure que les tâches sont automatisées, redéployer en priorité les équipes en interne vers des rôles à plus forte valeur ajoutée.",
    "Et troisièmement, point capital : veiller à ce que les salariés soient directement associés financièrement aux gains de productivité.",
    "Le rapport établit un parallèle remarquable avec les accords sociaux d'après-guerre : pour que les équipes transmettent volontiers leur savoir aux machines, leurs intérêts doivent converger avec la réussite de l'entreprise.",
    "Personne ne le fera gratuitement, après tout. Ce qui nous amène à un constat très encourageant.",
    "L'enseignement clé est le suivant : si les agents IA prennent en charge l'exécution brute, la confiance humaine, la responsabilité et la coordination directe demeurent le socle indispensable.",
    "Dans un environnement dominé par l'IA, les décisions doivent se prendre au grand jour : il faut débattre de la stratégie et expliciter le contexte pour orienter la flotte d'agents vers les bons objectifs.",
    "Les corvées administratives s'effacent, faisant des qualités purement humaines comme le discernement et le lien relationnel les atouts les plus précieux de l'organisation.",
    "Le bureau moderne passe d'un lieu où l'on exécute à un espace où l'on orchestre.",
    "À l'approche inévitable de ce tournant dans votre propre entreprise, nous vous laissons avec une interrogation clé :",
    "Quand l'IA accomplit le travail opérationnel plus vite que vous ne l'avez jamais fait, êtes-vous prêt à diriger la machine ?",
    "Merci d'avoir suivi cette vidéo, et nous espérons que cette analyse vous apporte un cadre clair pour aborder l'avenir très proche du travail."
]

texts_ja = [
    "AIの同僚が人間を6対1の比率で上回ったとき、私たちの仕事には何が起きるのでしょうか？",
    "Anthropicでは現在、対話型エージェントが実働時間の大半を占め、オフィスの役割は作業の実行から機械の統括へと転換しています。仕事の未来へようこそ。",
    "仕事の未来へようこそ。本日の解説動画へようこそ。本日は、AIによって完全に変貌を遂げたオフィスの日常の現実に迫ります。",
    "仕事の未来については多くの理論が語られていますが、本日提示するのは確かな実証データです。",
    "Anthropicが2026年にまとめた包括的な社内報告書をケーススタディとして、高度なAI導入がいかに労働、需要、そして人間の行動を激変させるかを探ります。",
    "早速本題に入りましょう。まず、極めて衝撃的な統計データから始めます。",
    "2026年8月時点で、Anthropicにおける対話型AIエージェントの稼働時間は、人間の従業員の労働時間を6対1の比率で上回りました。",
    "少し考えてみてください。たまに表計算ソフトを整えるために使うような、些細なツールの話ではありません。",
    "人間は実質的に、急激に拡大するデジタル労働者集団の上に位置するごく薄い層となり、社内の実働時間の大半をAIが記録しているのです。",
    "そしてこの極端な比率によって、日々の勤務体験そのものが根本から激変しています。",
    "ある圧倒されたエンジニアはその変化を的確に表現しました。「仕事は事実上パラレルな労働力となり、常にAIアシスタントの軍団を管理し、各自が注意を求めてくるClaudesの軍勢と対峙するようなものだ」と。",
    "もはや個別の孤立したタスクをこなすだけではありません。突如として、デジタル労働者の艦隊全体を統括し、査読し、応答する役割になるのです。",
    "私たちが本日掘り下げたい核心の問いはこれです。AIの同僚が6対1で人間を圧倒した時、あなたの仕事はどうなるのか？",
    "仕事の具体的な実行部分が突然完全に自動化されたら、人間に残される仕事とは何でしょうか？",
    "この巨大な変化がもたらす直接的な波及効果を見てみましょう。第1章：生産性の爆発的向上、アウトプットの加速。",
    "全社的な生産性の急上昇がどのように形成されたかを見てみましょう。興味深いのは、単にソフトウェアエンジニアのコーディング速度が上がっただけではないという点です。事実、コミット速度は5倍に跳ね上がっていますが。",
    "この爆発的成長は全事業部門に及んでいます。営業担当者は定型メールの処理を委ねることで、顧客との対面対話の時間を30パーセント増やしました。",
    "採用担当者は？1週間かかっていた候補者ソーシングをわずか数時間に短縮しています。あらゆる部門で成果物が急増しているのです。",
    "第2章：人間のボトルネック。誰が誰の足を引っ張っているのか？ここで話は極めて興味深い展開を迎えます。",
    "AIはすべての人を圧倒的に高速化しましたが、完全に予想外の問題を生み出しました。今やAIの作業を遅らせているのは人間の方なのです。",
    "エージェントが生成するアウトプットの絶対量が膨大すぎるため、すべてに目を通すこと自体が実質的なフルタイムの仕事になってしまうのです。",
    "テキスト量だけでも、非技術職の従業員ですら労働週の最大50パーセントを、エージェントが作成した内容を読むだけで費やすことになります。",
    "画面上を飛び交う膨大なテキスト、コード、意思決定の要求に、人間は常に圧倒されています。",
    "ある社員がこの現実をベビーシッターに例えて説明した例は秀逸です。エージェントは幼児のようなものだと。",
    "あるエージェントは深刻なバグを発見し（指を切って出血した状態）、別のエージェントは単なる書式修正のために（ジュースのパックを開けてほしいと）せがんできます。",
    "厄介なのは、AIがこの両方の問題を全く同じ緊迫したトーンで突きつけてくることです。",
    "すべてのエージェントが等しく注意を要求してくるため、人間は必死になって優先順位のトリアージに追われることになります。",
    "この人間のボトルネックがもたらす結果は衝撃的です。対話型セッションにおいて、AIエージェントの時間のなんと80パーセントは、人間が指示を出し、誤りを直し、承認するのを無駄に待つアイドル時間なのです。",
    "AIが能動的に働いているのはわずか20パーセントの時間だけです。機械は極めて高速なのに、デジタルの親指を弄びながら、相対的に遅い人間の脳が追いついてゴーサインを出すのを待っているのです。",
    "第3章：メタワークの台頭。実行者から管理者へ。この圧倒的な人間のボトルネックを解消するためには、単にもっとハードに働くだけでは不可能です。",
    "メタワークと呼ばれる領域へ移行する必要があります。特定のコードを書いたりメールを作成したりする代わりに、タスクそのものを抽象化するのです。",
    "ダッシュボードを構築し、常時運用マニュアルを書き、パイプラインを設計します。5分おきに肩を叩かれることなくエージェントが自律的に正解を見つけられるよう、自社AI向けにフレームワークを整えるのです。",
    "この規模感を把握するために言うと、Anthropicにおけるエージェント向け常設指示書の数は、2025年7月の数百件からわずか1年で8500件以上へと急増しました。",
    "社員たちは自分自身の専門知を体系化することに膨大な時間を費やし、日常の定常業務を進んで意図的に自動化しています。",
    "第4章：変化する採用基準。今求められる人材とは？日々の業務がタスクの実行からAI軍団の管理へと激変する中、企業は一体どのような人材を求めているのでしょうか？",
    "データは初任職にとって厳しく冷静な現実を示しています。ジュニア技術職の採用割合は、27パーセントからわずか9パーセントへと劇的に減少しました。",
    "基礎レベルの実装作業をAIがシームレスに引き受けるため、基本的な実行作業を行う人間の需要は急速に縮小しています。",
    "雇用主が求めるものの変化は極めて明瞭です。かつて企業は狭い専門知識と純粋な実行力を高く評価していました。",
    "しかし現在、採用担当者はそうした特性から離れ、高い自律性、的確な人間的判断力、そしてAIツールを巧みに操る創造的な管理能力を持つ候補者を優先しています。",
    "あるマネージャーが指摘した通り、AIモデルの能力にはムラがあります。だからこそ、領域を横断して適応し、機械が行き詰まった時に介入して高度な判断を下せる人間が必要なのです。",
    "第5章：今後の道筋。AIオフィスへの適応。雇用の未来に関するマクロな視点に立ち、企業と労働者がこのパラダイムシフトをいかに乗り越えるべきかを見てみましょう。",
    "Anthropicのアプローチは明快なロードマップを提示しています。第1に、変革のリスクに直面している職種を追跡する早期警戒システムを構築すること。",
    "第2に、それらの役割が自動化された際、単に解雇するのではなく、より高次の新しい業務へ柔軟に社内再配置することを優先すること。",
    "第3に、これが極めて重要ですが、急速な生産性向上の成果を社員に経済的に還元し、共有することです。",
    "この報告書は第2次世界大戦後の労使協定との見事な類似性を指摘しています。労働者に知識を進んで機械へ移植させ、変化に適応させるには、会社の成功と社員の利益を一致させる必要があります。",
    "無償でそれを行う人はいません。そしてここから、極めて勇気づけられる事実に気づかされます。",
    "最終的な結論として、AIエージェントがタスクの単純な実行を引き受ける一方で、人間の信頼関係、責任感、対面での協調こそが近代オフィスの不可欠な中核であり続けるということです。",
    "AI集約型の職場では、意思決定を公明正大に行う必要があります。エージェント艦隊が目指すべきゴールを正しく理解できるよう、会議を開き、戦略を議論し、背景を文書化しなければなりません。",
    "単調な事務作業が消失することで、判断力や人間同士の絆といった人間固有のスキルが、組織内で最も価値ある資産として残るのです。",
    "現代のオフィスは、作業を実行する場所から全体を指揮・統括する場所へと根本的に変化しています。",
    "皆さんの職場も不可避的にこの転換点に近づく中、最後に深く考えるべき重要な問いを投げかけたいと思います。",
    "AIが現場レベルの実務作業を私たちよりも圧倒的に速くこなせるようになった時、あなたはその機械を統括する準備ができていますか？",
    "ご視聴ありがとうございました。この分析が、間近に迫る仕事の未来を見通す明快な道しるべとなれば幸いです。"
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

final_copy = STAGING_DIR / "AI_Transforms_Office_Roles_FINAL.mp4"
shutil.copy2(FINAL_VIDEO, final_copy)
log(f"All assets staged to {STAGING_DIR}")
