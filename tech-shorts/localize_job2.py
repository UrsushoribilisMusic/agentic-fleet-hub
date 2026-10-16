#!/usr/bin/env python3
import json, shutil
from pathlib import Path
from run_batch_localize import assemble_dub, write_srt, ffdur, log, DOWNLOADS_STAGING, VOICE_DE, VOICE_FR

ASSET_DIR = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-14-how-to-be-more-ambitious-a-tutorial-for-humans-with-models")
FINAL_VIDEO = ASSET_DIR / "final_long.mp4"
SLUG = "how-to-be-more-ambitious-a-tutorial-for-humans-with-models"
STAGING_DIR = DOWNLOADS_STAGING / SLUG
STAGING_DIR.mkdir(parents=True, exist_ok=True)

with open(ASSET_DIR / "whisper_chunks.json") as f:
    chunks = json.load(f)

texts_en = [c["text"] for c in chunks]

texts_de = [
    "Jeder im Bereich KI rät dir, ehrgeiziger zu sein. Doch fast niemand erklärt, wie. Wahrer Ehrgeiz bedeutet nicht bloß schnelleres Tippen, sondern das Meistern von Flughöhe, Tiefe und Weite.",
    "Willkommen zum heutigen Erklärvideo. Heute ist der sechzehnte Oktober zweitausendsechsundzwanzig, und wir erleben eine Epoche rasanter KI-Fortschritte. Die Spitzenmodelle machen alle paar Wochen gewaltige Entwicklungssprünge. Doch hier ist die entscheidende Frage: Entwickeln wir unsere eigenen Fähigkeiten schnell genug weiter, um das volle Potenzial zu nutzen?",
    "Heute widmen wir uns einem brillanten Text von Felix Rieseberg. Er ist Engineering Manager bei Anthropic und arbeitet direkt an Claude. Er hat einen echten Meisterkurs darüber verfasst, wie wir unseren Ehrgeiz im Umgang mit KI entfesseln, und genau diesen Leitfaden gehen wir jetzt durch.",
    "Tauchen wir ein: Einerseits erleben wir atemberaubende Durchbrüche von Modellen wie Claude. KI hilft Hobbyastronomen, neue Planeten zu entdecken, generiert makellose Musikvideos aus dem Nichts und läutet eine Ära ein, die Experten Mathematik zwei Punkt null nennen. Doch blicken wir auf den Alltag: Genau hier klafft die sogenannte KI-Ambitionslücke. Die große Mehrheit nutzt diese verblüffenden",
    "Werkzeuge für völlig banale Aufgaben. Wir fragen: Was ist die Hauptstadt von Frankreich? Oder: Kannst du diese E-Mail freundlicher formulieren? Wir besitzen buchstäblich Raketenschiffe und nutzen sie, um kurz zum Tante-Emma-Laden um die Ecke zu rollen.",
    "Hier ist unser Fahrplan, um diese Kluft zu überwinden: Zuerst definieren wir die Ambitionslücke klar. Dann erkunden wir drei Dimensionen, um sie zu schließen: Flughöhe, Tiefe und Weite. Schließlich enthüllen wir die psychologische Barriere, die uns bremst: die Selbstwirksamkeit. Legen wir los!",
    "Abschnitt eins: Die KI-Ambitionslücke – Das Ziel definieren. Um diese Lücke zu schließen, müssen wir klären, wie Ehrgeiz aussieht, wenn man vor einem leeren Prompt-Feld sitzt. Es ist leicht zu sagen: Lass das Modell auf einer höheren Abstraktionsebene arbeiten. Aber das ist vage und wenig hilfreich. Felix Rieseberg definiert wahren KI-Ehrgeiz als das aktive",
    "und bewusste Verschieben der Grenzen dessen, was man dem Modell zutraut. Statt bloß Modewörter einzuwerfen, zerlegt wahrer Ehrgeiz Anfragen in vier Dimensionen: Geschwindigkeit, Flughöhe, Tiefe und Weite. Die Geschwindigkeit überspringen wir heute, denn dieselbe Arbeit in kürzerer Zeit zu erledigen, ist lediglich das absolute Standardbrot",
    "des aktuellen KI-Werts. Code schneller schreiben oder E-Mails generieren erfordert am wenigsten menschliche Kreativität. Unser Fokus liegt heute voll auf den drei Säulen, bei denen die wahre Magie und die transformativen Sprünge stattfinden.",
    "Flughöhe, Tiefe und Weite. Das bringt uns zu Abschnitt zwei: Flughöhe – Das Ziel anheben. Hier geht es darum, die Abstraktionsleiter nach oben zu klettern und das übergeordnete Ergebnis statt der einzelnen Aufgabe in den Blick zu nehmen. Betrachten wir als Fallbeispiel den alltäglichen Quartalsbericht von Acme Inc. Normalerweise würde man die KI bitten, ein paar Zahlen in einer",
    "Folienvorlage zu aktualisieren. Doch heben wir die Flughöhe an: Schritt eins: Gib der KI alle Rohdaten und frage: Was hat sich dieses Quartal geändert, warum und was sollten wir tun? Schritt zwei geht höher: Arbeite die drei dringendsten Entscheidungen heraus und nenne Pro- und Contra-Argumente. Schritt drei ist maximale Flughöhe: Entwirf ein völlig neues System anstelle der Folien, um",
    "Probleme frühzeitig zu erkennen, und lass es parallel laufen. Du hast dich vom Aktualisieren einer Vorlage zur Neuerfindung eines Geschäftsprozesses entwickelt. Was soll als Nächstes geschehen?",
    "Was ist das Ziel hinter dem unmittelbaren Ziel? Rieseberg erzählt dazu eine fantastische Anekdote.",
    "Früher bat er Claude, einzelne Softwareabstürze zu beheben. Schließlich erhöhte er die Flughöhe drastisch: Er bat nicht mehr um Bugfixes, sondern gab dem Modell Systemzugriff auf Windows-, Mac- und Linux-Umgebungen mit der simplen Anweisung: Halte unsere Apps absturzfrei! Bei Flughöhe geht es darum, dauerhafte Arbeitsabläufe zu schaffen, die den Menschen schrittweise entlasten.",
    "Weiter zu Abschnitt drei: Tiefe – Die Experten einbinden. Manchmal möchte man keinen Prozess neu erfinden, sondern eine konkrete Aufgabe makellos ausführen. Vergleichen wir oberflächliche Ausführung mit echter Tiefe: Wenn man die Kundenabwanderung bei Acme untersucht, bedeutet Oberflächlichkeit, einfache Tabellen und grobe Schätzungen zu akzeptieren",
    "und absurderweise die KI ihre eigene Arbeit beurteilen zu lassen. Echte Tiefe sieht völlig anders aus.",
    "Sie verlangt, dass Claude exakt dieselben Werkzeuge nutzt wie die weltweit besten Datenwissenschaftler.",
    "Es bedeutet, Tabellen durch Datenbanken und statistische Modelle zu ersetzen, Simulationen auf Rohdaten durchzuführen und externe Validierungstools hinzuzuziehen. Um diese Tiefe zu erreichen, nutzen Sie fünf Techniken: Erstens: Beste Instrumente einfordern, keine Kompromisse. Zweitens: Extrem ehrgeizige Ziele setzen. Soll eine Website in fünf",
    "Sekunden laden, verlange zweihundert Millisekunden. Drittens: Eigene Annahmen durch Rohdatenanalysen hinterfragen. Viertens: Die KI auffordern, neue Erkenntnisse oder blinde Flecken aufzudecken. Und fünftens, ganz entscheidend: Immer ein externes Werkzeug nutzen, um die Ergebnisse unabhängig zu prüfen.",
    "Als Abkürzung dient diese Prompt-Vorlage von Rieseberg, die man sich merken sollte. Der Kern lautet: Ich möchte eine tiefere Version dieser Aufgabe. Sag mir, was ein Spitzenprofi auf diesem Gebiet tun würde.",
    "Nenne das Rohmaterial, die konkreten Methoden und das externe Werkzeug, das die Richtigkeit beweist. Schreibe dann meinen Prompt um. Das ist der ultimative Hebel für fachliche Tiefe bei jedem Modell. Damit zu Abschnitt vier: Weite – Vielfältige Teams zusammenstellen. Hier entsteht die eigentliche Magie.",
    "Weite bedeutet, Erkenntnisse aus völlig verschiedenen Fachbereichen zu verknüpfen – genau wie in einem Heist-Film, bei dem man Spezialisten rekrutiert. Um herauszufinden, wen man braucht, nutzt Rieseberg einen Trick von Tom Kelley: Ersetze Substantive durch Verben. Wer die Aufgabe als Substantiv sieht – ich brauche Folien –, schränkt sich ein. Als Verb formuliert lautet es: Ich muss vielbeschäftigte Menschen von einer Kausalkette überzeugen,",
    "um unter Unsicherheit in dreißig Minuten zu entscheiden. Plötzlich liegen die nötigen Rollen auf der Hand: Nun stellt man das Team auf. Für die Acme-Präsentation bittet man Claude nicht um allgemeine Texte, sondern stellt ein Team zusammen: einen Analysten für harte Zahlen, einen Journalisten für die Erzählung, einen Motion-Designer für die Optik",
    "und meinen Favoriten: einen Leerverkäufer. Der Leerverkäufer dient als schonungsloses Red Team, das die Folien auf Schwachstellen durchleuchtet, bevor man sie präsentiert. Das ist die Stärke der Weite. Damit zu Abschnitt fünf: Das Geheimnis der Selbstwirksamkeit. Hinter den Methoden steht eine psychologische Hürde:",
    "Warum fällt es uns so schwer, ehrgeizig zu handeln? Die Antwort liegt in der Selbstwirksamkeit, dem Glauben an die eigenen Fähigkeiten. Menschen mit hoher Selbstwirksamkeit erreichen mehr, weil sie enge Grenzen überwinden. Denken wir an Michelangelo, der sich weigerte, die Sixtinische Kapelle zu bemalen, weil er sich bloß als Bildhauer sah, nicht als",
    "Maler. Ähnlich schränken wir unsere KI-Nutzung ein, weil unsere Selbstwirksamkeit mit den Möglichkeiten noch nicht Schritt gehalten hat. Das Großartige ist: Selbstwirksamkeit lässt sich gezielt stärken. Die Geschichte beweist es: Neunzehnhundertneununddreißig löste George Dantzig zwei ungelöste Statistikprobleme, nur weil er zu spät zur Vorlesung kam und sie für",
    "Hausaufgaben hielt. Neunzehnhundertvierundfünfzig brach Roger Bannister die Meile unter vier Minuten und zeigte der Welt, dass es möglich ist. Und im April zweitausendsechsundzwanzig lief Sebastian Sawe in London den ersten Marathon unter zwei Stunden – und weil die mentale Barriere fiel, schaffte es der Zweitplatzierte im selben Rennen ebenfalls. Man stärkt die eigene Selbstwirksamkeit, indem man an das Machbare glaubt oder",
    "anderen beim Erfolg zusieht. Damit zum Fazit: Die größte Begrenzung ist derzeit nicht das KI-Modell, sondern unser Glaube an das Mögliche. Wenn menschliche Fähigkeiten alle paar Wochen Sprünge machen – welches scheinbar unmögliche Vorhaben packst du an, jetzt da dein Ehrgeiz entfesselt ist? Erhöhe deine Flughöhe, nutze tiefes Fachwissen, bilde ein vielseitiges Team und fang an zu bauen! Danke fürs Zuschauen,",
    "und bis zum nächsten Mal!"
]

texts_fr = [
    "Tout le monde dans l'IA vous dit d'être plus ambitieux. Mais presque personne n'explique comment. La vraie ambition n'est pas de taper plus vite, c'est de maîtriser l'altitude, la profondeur et l'étendue.",
    "Bienvenue dans cette vidéo explicative. Nous sommes le seize octobre deux mille vingt-six, et nous vivons une période de progrès fulgurants de l'IA. Les modèles de pointe progressent à pas de géant toutes les quelques semaines. Mais voici la question cruciale : développons-nous nos propres compétences assez vite pour en tirer pleinement parti ?",
    "Aujourd'hui, nous explorons un texte brillant de Felix Rieseberg, responsable ingénierie chez Anthropic travaillant directement sur Claude. Il a conçu une véritable masterclass sur la manière de libérer notre ambition avec l'IA, et nous allons détailler son cadre dès maintenant.",
    "Plongeons au cœur du sujet : d'un côté, nous assistons à des prouesses époustouflantes de modèles comme Claude. L'IA aide des astronomes amateurs à découvrir de nouvelles planètes, crée des clips musicaux parfaits de toutes pièces et ouvre une ère que les experts appellent les mathématiques deux point zéro. Mais regardez le quotidien : c'est ce que nous nommons le fossé d'ambition de l'IA. La plupart d'entre nous utilisent ces outils",
    "pour des tâches parfaitement banales. Nous demandons : Quelle est la capitale de la France ? ou Peux-tu rendre cet e-mail moins agressif ? Nous possédons de véritables fusées et nous les utilisons pour faire trois pas jusqu'à l'épicerie du coin.",
    "Voici notre feuille de route pour combler ce fossé : d'abord définir clairement le manque d'ambition, puis explorer trois dimensions concrètes pour y remédier : l'altitude, la profondeur et l'étendue. Enfin, nous découvrirons le frein psychologique qui nous retient : le sentiment d'auto-efficacité. Allons-y !",
    "Première partie : Le fossé d'ambition de l'IA – Définir la cible. Pour combler cet écart, définissons d'abord ce qu'est l'ambition face à un champ de saisie vide. Il est facile de lancer : faites travailler le modèle à un niveau d'abstraction supérieur. Mais c'est flou et peu utile. Felix Rieseberg définit la véritable ambition comme le fait de repousser activement",
    "et consciemment les limites de ce qu'on croit le modèle capable d'accomplir. Plutôt que de lancer des mots à la mode, la vraie ambition décompose la requête en dimensions précises : vitesse, altitude, profondeur et étendue. Nous laissons la vitesse de côté aujourd'hui, car faire le même travail plus vite constitue la base économique",
    "actuelle de l'IA. Coder plus vite ou rédiger des courriels demande le moins de créativité humaine. Notre attention se porte donc sur les trois piliers où s'opère la véritable magie et les sauts transformateurs.",
    "Altitude, profondeur et étendue. Ce qui nous amène à la section deux : l'altitude, élever l'objectif. Il s'agit de monter sur l'échelle de l'abstraction pour viser le résultat final plutôt que la tâche immédiate. Prenons un exemple concret : la très classique revue trimestrielle de l'entreprise Acme. En temps normal, on demanderait à l'IA d'actualiser des chiffres dans une",
    "présentation. Élevons l'altitude : première étape, donnez toutes vos données brutes à l'IA et demandez : Dites-moi ce qui a changé ce trimestre, pourquoi et ce que nous devons faire. Deuxième étape, plus haute : Déterminez les trois décisions les plus urgentes et donnez les arguments pour et contre. Troisième étape, altitude maximale : Concevez un système bien meilleur qu'un diaporama pour détecter",
    "les problèmes en amont, et testez-le en parallèle. Vous venez de passer de la simple mise à jour d'un modèle à la réinvention d'un processus d'affaires. Que voulez-vous qu'il se passe ensuite ?",
    "Quel est l'objectif au-delà de l'objectif immédiat ? Rieseberg partage ici une anecdote frappante.",
    "Auparavant, il demandait à Claude de corriger les plantages au cas par cas. Puis il a élevé son altitude : au lieu de cibler un bug, il a donné au modèle un accès autonome à Windows, Mac et Linux avec cette simple consigne : Garde nos applications sans aucun plantage. L'altitude consiste à créer des flux durables qui s'affranchissent de l'intervention humaine.",
    "Passons à la section trois : la profondeur, incarner les experts. Parfois, on ne cherche pas à tout réinventer, mais à exécuter une tâche précise à la perfection. Comparons l'exécution superficielle et la vraie profondeur : face au désabonnement client chez Acme, une approche superficielle se contente de tableaux sommaires et d'approximations,",
    "en laissant étrangement l'IA juger son propre travail. L'exécution profonde est tout autre.",
    "Elle exige que Claude emploie exactement les mêmes outils que les meilleurs scientifiques des données.",
    "Cela signifie remplacer les tableaux par des bases de données et des modèles statistiques, exécuter des simulations sur les données brutes et utiliser des outils de validation externes. Cinq techniques permettent d'obtenir cette profondeur : 1. Exiger les meilleurs instruments professionnels. 2. Fixer des objectifs audacieux. Si un site doit charger en cinq",
    "secondes, demandez deux cents millisecondes. 3. Remettre en cause vos hypothèses avec les données brutes. 4. Demander de générer de nouvelles connaissances ou d'identifier les angles morts. Et 5. Point capital : toujours employer un juge externe pour valider rigoureusement le résultat.",
    "Pour y parvenir rapidement, voici le modèle de prompt fourni par Rieseberg. Le principe est de dire à l'IA : Je veux une version plus profonde de cette tâche. Dis-moi ce qu'un grand professionnel ferait.",
    "Nomme les données brutes, les méthodes spécifiques et l'outil extérieur qui prouvera l'exactitude du résultat. Puis réécris mon prompt. C'est l'astuce ultime pour tirer une expertise profonde de tout modèle. Passons à la section quatre : l'étendue, rassembler des équipes diversifiées.",
    "L'étendue consiste à puiser dans plusieurs disciplines distinctes, comme dans un film de braquage où l'on réunit des compétences complémentaires. Pour identifier ces talents, Rieseberg reprend une idée de Tom Kelley : remplacer les noms par des verbes. Penser sa tâche comme un nom – j'ai besoin d'un diaporama – limite la portée. Mais formulée avec des verbes : je dois amener des décideurs à comprendre une chaîne de causalité",
    "et à trancher dans l'incertitude en trente minutes. Dès lors, les compétences requises s'imposent d'elles-mêmes. Pour la présentation chez Acme, au lieu d'un rédacteur générique, formez une équipe : un analyste pour les chiffres, un journaliste pour la narration, un designer d'animation pour le visuel,",
    "et surtout un vendeur à découvert. Celui-ci sert d'équipe adverse impitoyable pour auditer les faiblesses avant toute présentation. C'est la force de l'étendue. Enfin, section cinq : le secret de l'auto-efficacité. Au-delà des techniques, il existe une barrière psychologique fondamentale :",
    "Pourquoi est-il si difficile d'agir avec une telle ambition ? La réponse réside dans le sentiment d'auto-efficacité, c'est-à-dire la croyance en ses propres capacités. Les personnes confiantes accomplissent davantage car elles dépassent les définitions réductrices. Pensez à Michel-Ange, qui refusait de peindre la chapelle Sixtine car il se voyait sculpteur et non",
    "peintre. Nous bridons notre usage de l'IA parce que notre confiance n'a pas encore intégré ces nouvelles capacités. Or, l'auto-efficacité peut se stimuler : en dix-neuf cent trente-neuf, George Dantzig a résolu deux problèmes réputés insolubles simplement parce qu'il est arrivé en retard en cours, croyant qu'il s'agissait de",
    "devoirs ordinaires. En dix-neuf cent cinquante-quatre, Roger Bannister courait le mile en moins de quatre minutes, prouvant que c'était faisable. Et en avril deux mille vingt-six, Sebastian Sawe a couru le premier marathon officiel sous les deux heures à Londres, entraînant son dauphin dans son sillage. On peut développer son auto-efficacité en choisissant de croire que l'impossible est à portée,",
    "ou en observant ceux qui y parviennent. En conclusion : notre principale limite n'est pas le modèle d'IA, mais notre vision du possible. Dans un monde où nos capacités d'action progressent toutes les deux semaines, quel défi réputé impossible relèverez-vous ? Prenez de la hauteur, mobilisez les experts, créez une équipe sur mesure et passez à l'action. Merci de m'avoir suivi,",
    "et à la prochaine !"
]

texts_ja = [
    "AIの世界では誰もが「もっと野心的になれ」と言いますが、その具体的な方法を教えてくれる人はほとんどいません。真の野心とは単にタイピングを速くすることではなく、高度、深度、射程を極めることです。",
    "本日の解説へようこそ。2026年10月16日現在、私たちはAIの驚異的な進化の時代を生きています。最先端モデルは数週間ごとに飛躍的な進化を遂げていますが、肝心なのは、私たち自身がその能力を使いこなすスキルを十分に高められているかという点です。",
    "本日は、AnthropicでClaude開発に携わるエンジニアリングマネージャー、フェリックス・リーセバーグによる素晴らしい論考を紐解きます。AIを活用して野心を解放するための実践的フレームワークを今すぐ見ていきましょう。",
    "驚異的な実績の一方で、Claudeのようなモデルはアマチュア天文家による新惑星発見を支援し、完成度の高いMVを一から生成し、専門家が「数学2.0」と呼ぶ新時代を切り拓いています。しかし日常の利用実態に目を向けると、いわゆる「AI野心ギャップ」が存在します。多くの人々は、この圧倒的な",
    "ツールを、極めて平凡で些細な作業にしか使っていません。「フランスの首都は？」と尋ねたり、「メールの文面を柔らかくして」と頼む程度です。私たちは本物の宇宙ロケットを手にしながら、近所のスーパーへ買い物に行くために使っているようなものです。",
    "このギャップを埋めるロードマップをご紹介します。まず野心ギャップを定義し、それを解消する3つの実践的次元「高度、深度、射程」を探ります。最後に、私たちの足を引っ張る心理的要因「自己効力感」を解き明かします。",
    "第1章：AI野心ギャップの定義。このギャップを埋めるには、空白のプロンプト欄を前にしたときに野心がどう見えるかを定義する必要があります。「より高い抽象度でモデルを動かせ」と言うのは簡単ですが、曖昧で役立ちません。フェリックスは、真のAI野心を次のように定義しています。",
    "モデルが達成できると信じている限界を能動的かつ意識的に押し広げること。単に流行りの言葉を並べるのではなく、要求を「速度・高度・深度・射程」の明確な次元に分解するのです。今回は速度を省略します。普段の作業を短時間でこなすことは、AIの",
    "経済的価値の基本に過ぎず、コードやメールを素早く書くことに人間の創造性はほとんど必要ないからです。本日は、本物の飛躍が起こる3つの柱に焦点を当てます。",
    "高度、深度、そして射程です。第2章：高度、目標を引き上げる。高度とは、抽象度の梯子を登ることです。個別の当面のタスクではなく、究極の成果に焦点を合わせることを意味します。Acme社の四半期事業レビュー（QBR）を例にとりましょう。通常なら、スライドテンプレートの",
    "数値を更新するようAIに頼むかもしれません。しかし高度を上げてみましょう。ステップ1：すべての生データを渡し、「今期何が変化し、なぜ起き、どうすべきか」を尋ねる。ステップ2はさらに上：「下すべき最も緊急な3つの決断と賛否両論の根拠を提示せよ」。ステップ3は最高高度です。「スライド資料よりも優れた、",
    "問題を早期に発見できる仕組みを設計し、並行運用せよ」。テンプレートの更新から、ビジネスプロセス自体の再設計へと進化したのです。その次に何を起こしたいのか？",
    "目先の目標の先にある究極のゴールは何か？ここでリーセバーグは素晴らしい逸話を紹介しています。",
    "彼は以前、個々のアプリのクラッシュが発生するたびに修正を求めていました。しかし劇的に高度を上げました。個別のバグ修正を頼むのをやめ、Windows、Mac、Linux環境への自律アクセス権を与えて「アプリが絶対にクラッシュしない状態を維持せよ」と指示したのです。高度とは、人間を介さない持続的ワークフローを作ることです。",
    "第3章：深度、専門知の動員。次の柱は深度です。プロセス全体を再構築するのではなく、特定のタスクを完璧に遂行させたい場合もあります。一般的な浅い実行と真の深度を比較してみましょう。顧客離脱の課題に対処する場合、浅い実行では単純な表や大雑把な概算を受け入れ、",
    "あろうことかAI自身に自分の仕事を評価させがちです。しかし深い実行は根本から異なります。",
    "一流のデータサイエンティストが使うのと全く同じツールをClaudeに使わせるのです。",
    "表をデータベースや統計モデルに置き換え、当て推量ではなく生データのシミュレーションを実行し、外部検証ツールで正しさを証明させます。この専門家レベルの深度を引き出すには5つの手法が必要です。第1に業界最高峰のツールを要求すること。第2に極端に野心的な目標を設定すること。サイトの表示を5秒から",
    "200ミリ秒に縮めるよう要求する。第3に生データで人間の思い込みを検証させる。第4に新たな知見や死角を発見させる。そして第5に最も重要なこととして、外部ツールを用いて客観的に検証させることです。",
    "これを実現する近道として、フェリックスが提示したプロンプトテンプレートがあります。「このタスクのより深いバージョンを求めます。この分野の一流の専門家なら何をするか教えてください。",
    "使用すべき生の素材、具体的な手法、正しさを証明する外部ツールを挙げ、プロンプトを書き直してください」。これこそ、あらゆるモデルから深い専門性を引き出す極意です。それでは第4章：射程、多様なチームの結成へ進みましょう。",
    "射程とは、全く異なる複数の分野を結びつけることです。映画の冒頭で多様な専門家を集める強盗チームのようなものです。必要な人材を見極めるため、トム・ケリーの技法「名詞を動詞に置き換える」を活用します。「スライド資料が必要」と名詞で考えると射程が狭まりますが、動詞で「多忙な人々に因果関係を信じさせ、",
    "30分で不確実な状況下での意思決定を下させる」と表現すると、必要な才能が明白になります。Acme社の発表であれば、汎用ライターではなく、数字を精査するアナリスト、物語を紡ぐジャーナリスト、視覚を彩るデザイナー、",
    "そして空売り投資家（ショートセラー）を呼び出します。発表前にプレゼンの欠点を容赦なく見つけ出すレッドチームとして機能させるのです。これが射程の威力です。そして第5章：自己効力感の秘密。最後に心理的な障壁に目を向けましょう。",
    "手法を知りながら、なぜ野心的に行動できないのか？その答えは「自己効力感」、すなわち自分の能力に対する確信にあります。高い自己効力感を持つ人は、自分のできる範囲を狭く限定しないため、より多くの成果を上げます。ミケランジェロは自分を彫刻家と見なし、礼拝堂の絵画制作を当初拒みました。",
    "同様に私たちも自己認識が追いつかず、AIの利用を制限しています。しかし自己効力感はハックできます。1939年、ジョージ・ダンツィグは授業に遅刻し、黒板に書かれた2つの未解決統計問題を単なる宿題だと思い込んで解いてしまいました。",
    "解けると信じたからこそ解けたのです。1954年にはロジャー・バニスターが不可能とされた1マイル4分の壁を破り、2026年4月にはセバスチャン・サウェがロンドンで人類初の公認2時間切りマラソンを達成、2位の選手も同レースで2時間を切りました。難題を可能だと信じ、",
    "他者の達成を目撃することで自己効力感は高まります。最大の制約はAIモデルではなく、私たち自身の認識です。人間の可能性が飛躍する今、野心を解き放ち、高度を上げ、専門性を深め、多様なチームを編成して構築を始めましょう。ご視聴ありがとうございました。",
    "それでは、また次回お会いしましょう。"
]

dur = ffdur(FINAL_VIDEO)
log(f"Processing {SLUG} (duration: {dur:.2f}s)...")

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

# Dubbing
audio_de = ASSET_DIR / f"{SLUG}_audio_de.m4a"
audio_fr = ASSET_DIR / f"{SLUG}_audio_fr.m4a"

log("Assembling German dub...")
assemble_dub(chunks, texts_de, VOICE_DE, dur, audio_de, ASSET_DIR / "tmp_de")

log("Assembling French dub...")
assemble_dub(chunks, texts_fr, VOICE_FR, dur, audio_fr, ASSET_DIR / "tmp_fr")

# Copy to staging directory
log("Staging files...")
for p in [srt_en, srt_de, srt_fr, srt_ja, audio_de, audio_fr]:
    shutil.copy2(p, STAGING_DIR / p.name)

hook_vo = ASSET_DIR / f"{SLUG}_hook_vo.mp3"
if hook_vo.exists():
    shutil.copy2(hook_vo, STAGING_DIR / hook_vo.name)

final_copy = STAGING_DIR / "How_to_Be_More_Ambitious_FINAL.mp4"
shutil.copy2(FINAL_VIDEO, final_copy)
log(f"All assets staged to {STAGING_DIR}")
