#!/usr/bin/env python3
"""Localize and upload Tech Story: The 2028 AI Post-Mortem (TS Lombard 'Perkini Report')."""
import json, shutil, sys
from pathlib import Path

sys.path.insert(0, "/Users/miguelrodriguez/projects/agentic-fleet-hub/tech-shorts")
import localize as L
import pipeline

JOB_ID = "ts-20261025-the-perkini-report-the-2028-reality-crisis"
SLUG = "the-perkini-report-the-2028-reality-crisis"
ASSET_DIR = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-25-the-perkini-report-the-2028-reality-crisis")
FINAL_VIDEO = ASSET_DIR / "final_long.mp4"
STAGING_DIR = Path("/Users/miguelrodriguez/Downloads/tech-shorts-captions") / SLUG
STAGING_DIR.mkdir(parents=True, exist_ok=True)

with open(ASSET_DIR / "whisper_chunks.json") as f:
    chunks = json.load(f)

assert len(chunks) == 45, f"Expected 45 chunks, got {len(chunks)}"

texts_en = [c["text"] for c in chunks]

texts_de = [
    "Stellen Sie sich vor, wir schreiben das Jahr 2030 und blicken zurück auf den KI-Börsencrash vom April 2028, als in wenigen Wochen zwanzig Billionen Dollar verpufften.",
    "Im viralen Perkini-Report von TS Lombard zerlegt der Ökonom Dario Perkins die Anatomie einer KI-Blase aus CapEx-Recycling, Herstellerfinanzierung und versteckten Schulden außerhalb der Bilanz – und zeigt, warum ihr Platzen einen Boom in der Realwirtschaft auslösen könnte.",
    "Stellen wir uns vor, es ist 2030 und wir blicken zurück auf den Börsencrash vom April 2028.",
    "Innerhalb weniger Wochen fiel der S&P 500 um fast dreißig Prozent, und zwanzig Billionen Dollar an Finanzvermögen lösten sich in Luft auf.",
    "In den Jahren 2026 und 2027 beharrte das vorherrschende Narrativ darauf, dass künstliche Intelligenz das menschliche Dasein sofort komplett umkrempeln würde.",
    "Um dieses Versprechen zu untermauern, pumpten Tech-Hyperscaler scheinbar grenzenloses Kapital in den Ausbau der Infrastruktur.",
    "Investoren sahen diese Geldflut im Ökosystem und hielten sie für den mathematischen Beweis wirtschaftlicher Tragfähigkeit.",
    "Sie nahmen an, kein Konzern würde so viel ausgeben, wenn die Renditen nicht garantiert wären. Doch sie deuteten die Signale falsch.",
    "Der Markt verwechselte eine konzentrierte Flut von Unternehmenskapital mit einer unumkehrbaren, breiten technologischen Nutzung.",
    "Um zu verstehen, warum diese breite Nutzung ausblieb, müssen wir unter die Oberfläche auf drei strukturelle Konstruktionsfehler blicken.",
    "Erstens: CapEx-Recycling. Dieses Flussdiagramm zeigt den Boom-Kreislauf der Branche: Die Investitionsausgaben eines Hyperscalers wurden schlicht zum Umsatz eines anderen Unternehmens und flossen direkt zurück ins System.",
    "Der zweite Fehler war die Herstellerfinanzierung: Chiphersteller investierten ihr eigenes Kapital direkt in KI-Start-ups, damit genau diese Start-ups im Gegenzug weitere Chips kauften.",
    "Geld floss als Finanzierung hinaus und kam als Bestellung zurück. Der dritte Fehler betraf Zweckgesellschaften, sogenannte SPVs.",
    "Hyperscaler hörten auf, Rechenzentren aus einbehaltenen Gewinnen zu finanzieren. Stattdessen wurden sie über hochverschuldete Zweckgesellschaften gebaut und zurückgemietet, was das Risiko aus den Bilanzen der Tech-Giganten fernhielt.",
    "Nimmt man diese drei Mechanismen zusammen, ergibt sich eine nüchterne mathematische Realität.",
    "Die gesamte Branche balancierte eine Billion Dollar an künftigen Verpflichtungen auf lediglich zweihundert Milliarden Dollar laufendem Umsatz, der zudem stark auf wenige unrentable Start-ups konzentriert war.",
    "Gleichzeitig blieben normale Verbraucher außerhalb der Silicon-Valley-Blase weitgehend gleichgültig.",
    "Sie übernahmen KI-Werkzeuge schlicht nicht in ihren täglichen Arbeitsablauf oder ihre persönliche Organisation.",
    "Diese versteckten Finanzmechanismen blähten die Unternehmensumsätze auf dem Papier erfolgreich auf, ohne jemals eine echte, tragfähige Endkundennachfrage zu erzeugen.",
    "Der psychologische Wendepunkt kam Ende 2027: Ein lange verschobener Börsengang eines großen KI-Entwicklers zwang endlich echte, geprüfte Geschäftszahlen ans Licht der Öffentlichkeit.",
    "Dieses Diagramm zeigt die Diskrepanz, die diese Prüfungen offenlegten: Die Lieblingskennzahl der Branche, der jährlich wiederkehrende Umsatz, entpuppte sich als ungeprüfter Marketingtrick.",
    "Als die echten Zahlen vorlagen, zerplatzte die Illusion und legte eine erschreckend dünne Kundenbasis frei.",
    "Angesichts dieser Realität zogen die Hyperscaler abrupt die Notbremse und kürzten ihre Investitionsprognosen für 2028 um fünfundvierzig Prozent.",
    "Dieser plötzliche Stopp ließ die nachgelagerte Umsatzpipeline kollabieren: Bestellungen für Chips, Server und Stromanlagen halbierten sich sofort.",
    "Die Schockwelle erfasste exportorientierte Volkswirtschaften wie Taiwan und Südkorea.",
    "Fabriken, die ihre Kapazitäten massiv hochgefahren hatten, wurden hart getroffen, als sich Halbleiterengpässe über Nacht in gewaltige Überkapazitäten verwandelten.",
    "Der Zusammenbruch der KI-Branche war das Scheitern ihres Geschäftsmodells: Das gesamte Ökosystem brauchte exponentiell wachsende Investitionsausgaben, nur um zu überleben.",
    "Als die Ausgaben stoppten, gab der Markt die Erzählung auf, KI werde die Welt über Nacht verändern.",
    "Stattdessen begannen Investoren hektisch, Unternehmensbilanzen zu prüfen. Als erste Dominosteine fielen die sogenannten NeoCloud-Anbieter.",
    "Als klamme Kunden versuchten, Verträge neu zu verhandeln, rissen diese Anbieter plötzlich die strengen Kreditauflagen ihrer GPU-besicherten Darlehen und lösten die erste Insolvenzwelle aus.",
    "Diese Karte zeigt den Kollaps der außerbilanziellen Finanzkonstruktionen: Rechenzentrumskredite erlitten massive Abschreibungen, während versteckte Zweckgesellschaften einknickten.",
    "Das löste eine breitere Kreditklemme aus: Fonds mit GPU-besicherten Krediten sahen sich mit massiven Mittelabflüssen konfrontiert, was Banken zu Panikverkäufen und strengeren Kreditlinien zwang.",
    "Ohne permanentes Hyperwachstum zur Deckung der Zinskosten erzwang die im gesamten Ökosystem versteckte Verschuldung flächendeckende Zahlungsausfälle.",
    "Angesichts dieser Vermögensvernichtung sagten Pessimisten einen systemischen Kollaps wie in der Finanzkrise 2008 voraus.",
    "Doch sie lagen völlig falsch. Dieses Diagramm veranschaulicht die Realität des Vermögenseffekts.",
    "Da das Aktienvermögen stark auf das oberste eine Prozent der Haushalte konzentriert war, änderte sein plötzliches Verdampfen das Konsumverhalten des durchschnittlichen Amerikaners kaum.",
    "Das Fundament blieb stabil. Als die US-Notenbank sah, dass der Technologiesektor einbrach, griff sie ein.",
    "Sie ließ ihre früheren Inflationssorgen hinter sich und senkte entschlossen die Zinsen, um die wirtschaftlichen Folgen abzufedern.",
    "Diese niedrigeren Zinsen lösten einen Crowding-In-Effekt aus: Billigere Kredite lenkten Kapital weg vom Tech-Sektor und entfachten einen Boom im Wohnungsbau und bei langlebigen Konsumgütern.",
    "Das Platzen der KI-Börsenmanie finanzierte und katalysierte so unmittelbar eine greifbare, längst überfällige Belebung der Realwirtschaft.",
    "Am Ende überlebte die Technologie selbst: Sie wurde zur günstigen Massenware, wodurch Unternehmen sie endlich nutzen konnten, um die echte menschliche Produktivität zu steigern.",
    "Treten wir kurz aus dem Jahr 2030 heraus: Wenn Sie dieses Video heute sehen, ist dieser Crash kein bloßes Gedankenspiel.",
    "Er ist eine mathematische Gewissheit, sobald der aktuelle Investitionszyklus ins Stocken gerät.",
    "Ihr klügster Zug besteht heute darin, Ihr Portfolio konsequent weg von konzentrierten US-Tech-Aktien zu diversifizieren und Anleihen als Schutz gegen Rückschläge zu nutzen.",
    "Die KI-Blase zu überstehen bedeutet nicht, das wahre Potenzial der Technik zu ignorieren – sondern sich zu weigern, ihr zum Scheitern verurteiltes Finanz-Engineering zu subventionieren.",
]

texts_fr = [
    "Imaginez que nous soyons en 2030 et que nous revenions sur le krach boursier de l'IA d'avril 2028, lorsque vingt mille milliards de dollars se sont évaporés en quelques semaines.",
    "Dans le célèbre rapport Perkini de TS Lombard, l'économiste Dario Perkins dissèque l'anatomie d'une bulle de l'IA bâtie sur le recyclage des investissements, le financement fournisseur et la dette hors bilan — et explique pourquoi son éclatement pourrait relancer l'économie réelle.",
    "Imaginons que nous soyons en 2030 et que nous regardions dans le rétroviseur le krach boursier d'avril 2028.",
    "En quelques semaines à peine, le S&P 500 a chuté de près de trente pour cent, et vingt mille milliards de dollars de richesse financière se sont volatilisés.",
    "En 2026 et 2027, le récit dominant assurait que l'intelligence artificielle allait immédiatement bouleverser toute l'existence humaine.",
    "Pour appuyer cette promesse, les géants du cloud déversaient des capitaux apparemment illimités dans la construction d'infrastructures.",
    "Les investisseurs voyaient cette montagne de liquidités inonder l'écosystème et la prenaient pour une preuve mathématique de viabilité financière.",
    "Ils supposaient qu'aucune entreprise ne dépenserait autant sans rendements garantis. Mais ils ont mal lu les signaux.",
    "Le marché a confondu un afflux concentré de capitaux d'entreprise avec une adoption technologique massive et irréversible.",
    "Pour comprendre pourquoi cette adoption ne s'est jamais matérialisée, il faut examiner trois failles structurelles sous la surface.",
    "Premièrement, le recyclage des investissements : ce schéma montre la boucle du boom, où la dépense en capital d'un hyperscaler devenait simplement le chiffre d'affaires d'une autre entreprise avant de revenir dans le système.",
    "La deuxième faille était le financement fournisseur : les fabricants de puces investissaient leurs propres fonds dans des start-ups d'IA pour que celles-ci leur achètent aussitôt davantage de puces.",
    "L'argent sortait sous forme de financement et revenait sous forme de commandes. La troisième faille reposait sur les véhicules financiers dédiés, ou SPV.",
    "Les hyperscalers ont cessé de financer les centres de données sur leurs bénéfices : ces chantiers étaient portés par des SPV très endettés puis reloués, gardant le risque caché hors des bilans principaux.",
    "Additionnez ces trois mécanismes et vous obtenez une réalité mathématique implacable.",
    "Toute l'industrie faisait tenir mille milliards de dollars d'engagements futurs sur seulement deux cents milliards de revenus actuels, très concentrés chez quelques start-ups déficitaires.",
    "Pendant ce temps, les consommateurs ordinaires hors de la bulle de la Silicon Valley restaient largement indifférents.",
    "Ils n'adoptaient tout simplement pas les outils d'IA dans leur travail quotidien ni dans leur organisation personnelle.",
    "Ces mécanismes financiers cachés ont gonflé artificiellement les revenus sur le papier, faisant tourner le système en vase clos sans jamais créer de demande finale durable.",
    "Le tournant psychologique est survenu fin 2027 : l'introduction en bourse longtemps retardée d'un grand développeur d'IA a enfin forcé la publication de comptes réellement audités.",
    "Ce graphique montre l'écart révélé par ces audits : l'indicateur fétiche du secteur, le revenu annuel récurrent, a été démasqué comme une astuce marketing non auditée.",
    "Lorsque les vrais chiffres sont sortis, l'illusion s'est dissipée, révélant une base de clients étonnamment mince.",
    "Face à cette réalité, les hyperscalers ont brutalement freiné, réduisant de quarante-cinq pour cent leurs prévisions d'investissement pour 2028.",
    "Cet arrêt soudain a écrasé toute la chaîne en aval : les commandes de puces, de serveurs et d'équipements électriques ont été divisées par deux du jour au lendemain.",
    "L'onde de choc s'est propagée aux économies exportatrices comme Taïwan et la Corée du Sud.",
    "Les usines qui avaient accru leur production ont été frappées de plein fouet lorsque la pénurie de semi-conducteurs s'est transformée en surabondance.",
    "L'effondrement du secteur de l'IA fut l'échec de son modèle économique, qui dépendait d'une croissance exponentielle et infinie des dépenses d'investissement pour survivre.",
    "Une fois les dépenses arrêtées, le marché a abandonné le récit d'une IA transformant immédiatement le monde.",
    "Les investisseurs se sont mis à scruter fébrilement les bilans. Les premiers dominos à tomber furent les fournisseurs de NeoCloud.",
    "Alors que des clients à court de trésorerie tentaient de renégocier leurs contrats, ces fournisseurs ont déclenché les clauses strictes de leurs prêts gagés sur des GPU, lançant la première vague de faillites.",
    "Cette carte retrace l'effondrement de l'ingénierie hors bilan : les prêts liés aux centres de données ont subi d'énormes dépréciations tandis que les SPV cachés cédaient.",
    "Cela a déclenché un resserrement général du crédit : les fonds détenant des prêts gagés sur des GPU ont subi des rachats massifs, forçant les banques à réduire leurs lignes de crédit.",
    "Sans hypercroissance continue pour couvrir le coût de l'emprunt, l'effet de levier caché dans tout l'écosystème a provoqué des défauts en chaîne.",
    "Face à cette destruction de richesse, les pessimistes prédisaient un effondrement systémique comparable à la crise financière de 2008.",
    "Mais ils avaient totalement tort. Ce graphique illustre la réalité de l'effet de richesse.",
    "Parce que la richesse boursière était fortement concentrée dans le un pour cent des ménages les plus riches, son évaporation soudaine n'a pas modifié la consommation de l'Américain moyen.",
    "La base économique est restée solide. Voyant le secteur technologique s'effondrer, la Réserve fédérale est intervenue.",
    "Elle a mis de côté ses craintes d'inflation et abaissé fortement ses taux d'intérêt pour contenir le choc économique.",
    "Ces taux plus bas ont déclenché un effet d'entraînement positif : le crédit moins cher a détourné les capitaux de la tech pour alimenter un boom du logement et des biens durables.",
    "L'effondrement de la manie boursière de l'IA a ainsi directement financé et catalysé une relance tangible et attendue de l'économie réelle.",
    "Dans le sillage du krach, la technologie a survécu : devenue banale et bon marché, elle a enfin permis aux entreprises d'accroître la vraie productivité humaine.",
    "Sortons un instant des années 2030 : si vous regardez ceci aujourd'hui, ce krach n'est pas un scénario hypothétique.",
    "C'est une certitude mathématique dès l'instant où le cycle actuel de dépenses d'investissement s'arrêtera.",
    "Votre meilleure stratégie consiste aujourd'hui à diversifier votre portefeuille hors des valeurs technologiques américaines concentrées et à utiliser le marché obligataire pour vous protéger.",
    "Survivre à la bulle de l'IA ne consiste pas à ignorer le potentiel réel de la technologie, mais à refuser de subventionner son ingénierie financière condamnée.",
]

texts_ja = [
    "今は2030年だと想像してください。わずか数週間で20兆ドルが消失した2028年4月のAI市場暴落を振り返っています。",
    "TSロンバードの話題のレポート「パーキニ・レポート」で、エコノミストのダリオ・パーキンスは、設備投資の循環やベンダーファイナンス、簿外債務の上に築かれたAIバブルの解剖図と、その崩壊がなぜ実体経済のブームを引き起こすのかを明らかにしています。",
    "2030年の視点から、2028年4月の市場暴落を振り返ってみましょう。",
    "わずか数週間でS&P500は約30パーセント急落し、20兆ドルもの金融資産が跡形もなく消え去りました。",
    "2026年から2027年当時、世間の支配的な物語は、人工知能が人類の生活を即座に根底から作り変えると主張していました。",
    "その約束を裏付けるかのように、巨大テック企業はインフラ建設に無尽蔵とも思える資本を注ぎ込んでいました。",
    "投資家たちは生態系に流れ込むその巨額の資金を見て、それを収益性の数学的証明だと受け止めました。",
    "リターンが保証されていなければ、これほどの巨額を投じるはずがないと思い込んだのです。しかし彼らはシグナルを読み違えていました。",
    "市場は、一部に集中した企業資本の洪水を、後戻りしない広範な技術普及だと勘違いしていたのです。",
    "なぜその普及が実現しなかったのかを知るには、水面下にあった3つの構造的欠陥を見る必要があります。",
    "第1に設備投資の循環です。このフロー図が示す通り、ハイパースケーラーの設備投資がそのまま他社の売上となり、その資金が再びシステムに戻ってさらなる支出を正当化していました。",
    "第2の欠陥はベンダーファイナンスです。半導体メーカーが自社の資金をAIスタートアップに直接出資し、そのスタートアップがまさにその資金で半導体を買い増していました。",
    "資金は出資として出ていき、注文として戻ってきたのです。第3の欠陥は特別目的事業体、いわゆるSPVです。",
    "ハイパースケーラーは内部留保でデータセンターを建設するのをやめ、多額の負債を抱えたSPVに建設させてリースバックすることで、美しいバランスシートの外側にリスクを隠しました。",
    "これら3つの仕組みを足し合わせると、冷厳な数学的現実が浮かび上がります。",
    "業界全体が、赤字スタートアップ数社に偏ったわずか2000億ドルの現在の売上の上に、1兆ドルもの将来の支出約束を積み上げていたのです。",
    "一方で、シリコンバレーのバブルの外で暮らす一般の消費者はほとんど無関心でした。",
    "日々の業務や個人の生活にAIツールを取り入れてはいなかったのです。",
    "こうした隠れた金融メカニズムは帳簿上の企業収益を膨らませましたが、それを支える本物の持続可能な最終需要を生み出すことはありませんでした。",
    "心理的な転換点は2027年後半に訪れました。大手AI開発企業の延期され続けていた新規株式公開により、ついに監査済みの実数値が白日の下にさらされたのです。",
    "このチャートは監査が暴いた乖離を示しています。業界が愛用した「年間経常収益」という指標は、監査を通らないマーケティング上のトリックだったことが判明しました。",
    "本当の数字が出た瞬間、幻想は切り裂かれ、その下にあった驚くほど薄い顧客基盤が露呈しました。",
    "この現実に直面したハイパースケーラーは投資を急停止し、2028年の設備投資見通しを45パーセント削減しました。",
    "その急停止が下流の収益パイプラインを直撃し、半導体やサーバー、電力設備の注文は即座に半減しました。",
    "衝撃波は台湾や韓国といった輸出主導型の経済圏へと広がりました。",
    "供給拡大のために増産していた工場は大打撃を受け、半導体不足は一夜にして巨大な供給過剰へと変わりました。",
    "AI業界の崩壊はビジネスモデルそのものの破綻でした。生態系全体が生き残るためだけに指数関数的な設備投資の拡大に依存していたのです。",
    "支出が止まると、市場はAIが世界を変えるという物語を捨て去りました。",
    "代わりに企業のバランスシートを必死に精査し始め、最初のドミノとしてネオクラウド事業者が倒れました。",
    "資金難の顧客が契約の再交渉を試みたことで、GPU担保ローンの厳格な財務制限条項に抵触し、最初の破産ラッシュが始まったのです。",
    "このマップは簿外スキームの崩壊を追跡しています。データセンター融資は巨額の評価損を出し、隠れSPVが破綻してデフォルト率が急騰しました。",
    "これが広範な信用収縮を引き起こしました。GPU担保ローンを抱えるファンドに解約が殺到し、銀行はパニックに陥って与信枠を絞り込みました。",
    "借入コストを賄う超高速成長が止まったことで、生態系全体に隠されていた巨大なレバレッジが連鎖的なデフォルトを引き起こしました。",
    "巨額の資産喪失とデフォルトの波を見て、悲観論者たちは2008年のリーマンショック並みのシステム崩壊を予測しました。",
    "しかしその予測は完全に外れました。このチャートは資産効果の現実を示しています。",
    "株式資産は最上位1パーセントの世帯に極度に集中していたため、それが突然消えても平均的な米国の消費者の支出行動は変わらなかったのです。",
    "実体経済の土台は盤石なままでした。テック部門の暴落を見たFRBは即座に介入しました。",
    "インフレへの懸念を捨て、経済への悪影響を食い止めるために大幅な利下げに踏み切ったのです。",
    "金利低下はクラウディング・インと呼ばれる現象を引き起こしました。借入コストの低下が資金をテックから向かわせ、住宅や耐久消費財のブームに火をつけました。",
    "AI株バブルの崩壊が、結果としてメインストリートにおける待望の実体経済の復活を直接資金面から後押ししたのです。",
    "その後の世界で技術そのものは生き残りました。AIは徹底的にコモディティ化して安くなり、企業は労働者を置き換えるのではなく本来の生産性を高めるために使えるようになりました。",
    "ここで2030年から現在に戻りましょう。今この動画を見ているなら、この暴落は単なる仮説のシナリオではありません。",
    "現在の設備投資サイクルが止まった瞬間に訪れる、数学的な必然なのです。",
    "今取るべき行動は、米国の一部のテック株への過度な集中からポートフォリオを分散させ、債券市場を活用して下落リスクに備えることです。",
    "AIバブルを生き残るとは、技術の本当の可能性を無視することではなく、破綻が運命づけられた金融工学への補助金を拒否することなのです。",
]

assert len(texts_de) == 45 and len(texts_fr) == 45 and len(texts_ja) == 45

srt_en = ASSET_DIR / f"{SLUG}_en.srt"
srt_de = ASSET_DIR / f"{SLUG}_de.srt"
srt_fr = ASSET_DIR / f"{SLUG}_fr.srt"
srt_ja = ASSET_DIR / f"{SLUG}_ja.srt"
audio_de = ASSET_DIR / f"{SLUG}_audio_de.m4a"
audio_fr = ASSET_DIR / f"{SLUG}_audio_fr.m4a"

L.write_srt(chunks, texts_en, srt_en)
L.write_srt(chunks, texts_de, srt_de)
L.write_srt(chunks, texts_fr, srt_fr)
L.write_srt(chunks, texts_ja, srt_ja)
L.log("Wrote EN/DE/FR/JA SRT files.")

dur = L.ffdur(FINAL_VIDEO)
L.log(f"Assembling German dub with local Kokoro (kerstin) for {dur:.1f}s...")
L.assemble(None, chunks, texts_de, "kokoro:de:kerstin", dur, audio_de, ASSET_DIR / "tmp_de_kokoro")

L.log(f"Assembling French dub with local Kokoro (ff_siwis) for {dur:.1f}s...")
L.assemble(None, chunks, texts_fr, "kokoro:fr:ff_siwis", dur, audio_fr, ASSET_DIR / "tmp_fr_kokoro")

for p in [srt_en, srt_de, srt_fr, srt_ja, audio_de, audio_fr]:
    shutil.copy2(p, STAGING_DIR / p.name)

hook_vo = ASSET_DIR / f"{SLUG}_hook_vo.mp3"
if hook_vo.exists():
    shutil.copy2(hook_vo, STAGING_DIR / hook_vo.name)

shutil.copy2(FINAL_VIDEO, STAGING_DIR / "The_2028_AI_Post-Mortem_FINAL.mp4")
L.log(f"All assets staged to {STAGING_DIR}")

localizations = {
    "de": {
        "title": "Das KI-Post-Mortem 2028: TS Lombards „Perkini-Report“ über den 20-Billionen-Dollar-Crash",
        "description": (
            "Was passiert, wenn sich die offensichtlichste Finanzblase der modernen Geschichte tatsächlich als Blase entpuppt? "
            "Aus der Perspektive des Jahres 2030 blickt der Makroökonom Dario Perkins (TS Lombard) in seinem viralen „Perkini-Report“ "
            "auf den KI-Börsencrash vom April 2028 zurück.\n\n"
            "In dieser Analyse beleuchten wir die vier Akte des KI-Post-Mortems:\n"
            "1. Die drei Säulen des Finanz-Engineerings: CapEx-Recycling, Herstellerfinanzierung und versteckte Zweckgesellschaften (SPVs).\n"
            "2. Der geprüfte Börsengang Ende 2027, der die ARR-Illusion entlarvte und zu einem 45-%-Investitionsstopp führte.\n"
            "3. Die Pleitewelle bei NeoCloud-Anbietern und GPU-besicherten Privatkrediten.\n"
            "4. Warum der Wall-Street-Crash durch Zinssenkungen der Fed einen Boom in der Realwirtschaft (Main Street) auslöste.\n\n"
            "Quelle: https://hub.tslombard.com/the-perkini-report\n\n"
            "#PerkiniReport #KIBlase #Makroökonomie #TSLombard #Finanzmarkt #Rechenzentren"
        ),
        "audio": str(audio_de),
        "srt": str(srt_de),
    },
    "fr": {
        "title": "L'autopsie du krach de l'IA de 2028 : le « Perkini Report » de TS Lombard sur la chute de 20 000 Md$",
        "description": (
            "Et si la bulle financière la plus évidente de l'histoire moderne s'avérait être… une bulle ? "
            "Écrit depuis 2030 en revenant sur le krach d'avril 2028, le « Perkini Report » de l'économiste Dario Perkins (TS Lombard) "
            "retrace comment un dégonflement boursier de 20 000 milliards de dollars se déroulerait réellement.\n\n"
            "Dans cette vidéo :\n"
            "1. Les trois piliers de l'ingénierie financière : recyclage des CapEx, financement fournisseur et SPV hors bilan.\n"
            "2. Le catalyseur de fin 2027 : des comptes audités d'IPO révélant l'illusion des revenus récurrents (ARR).\n"
            "3. L'onde de choc sur les NeoClouds et les prêts gagés sur des GPU.\n"
            "4. Pourquoi le krach de Wall Street a déclenché une relance de l'économie réelle grâce aux baisses de taux de la Fed.\n\n"
            "Source : https://hub.tslombard.com/the-perkini-report\n\n"
            "#PerkiniReport #BulleIA #Macroéconomie #TSLombard #MarchésFinanciers #DataCenters"
        ),
        "audio": str(audio_fr),
        "srt": str(srt_fr),
    },
    "ja": {
        "title": "2028年AIバブル崩壊の検死報告：20兆ドル消失を予測したTSロンバード「パーキニ・レポート」",
        "description": (
            "もし史上最も明白な金融バブルが、やはりバブルだったとしたら？2030年の視点から2028年4月のAI市場暴落を振り返るTSロンバードのチーフエコノミスト、"
            "ダリオ・パーキンスによる話題の『パーキニ・レポート（The Perkini Report）』を徹底解説します。\n\n"
            "1. 3つの金融工学トリック：設備投資の循環（CapExリサイクル）、半導体メーカーによるベンダーファイナンス、簿外SPV（特別目的事業体）。\n"
            "2. 2027年末のIPO監査ショック：ARR（年間経常収益）の幻想が暴かれ、ハイパースケーラーが設備投資を45%急削減。\n"
            "3. ネオクラウド破綻とGPU担保ローンの連鎖デフォルト。\n"
            "4. なぜウォール街の暴落がFRBの利下げを通じて実体経済（メインストリート）の住宅・生産性ブームを生んだのか。\n\n"
            "出典: https://hub.tslombard.com/the-perkini-report\n\n"
            "#パーキニレポート #AIバブル #マクロ経済 #TSロンバード #データセンター #半導体"
        ),
        "audio": "",
        "srt": str(srt_ja),
    },
}

data = pipeline.load_jobs()
job = pipeline.find_job(data, JOB_ID)
yt = dict(job.get("youtube", {}))
yt["localizations"] = localizations
yt["captions_en_srt"] = str(srt_en)
pipeline.update_job_field(JOB_ID, youtube=yt)
L.log("Updated jobs.json with EN/DE/FR/JA localizations for Perkini Report.")
