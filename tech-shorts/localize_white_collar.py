#!/usr/bin/env python3
import json, shutil, sys
from pathlib import Path

# Add tech-shorts directory
sys.path.insert(0, "/Users/miguelrodriguez/projects/agentic-fleet-hub/tech-shorts")
from run_batch_localize import assemble_dub, write_srt, ffdur, log, DOWNLOADS_STAGING, VOICE_DE, VOICE_FR

ASSET_DIR = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-12-the-white-collar-bypass")
FINAL_VIDEO = ASSET_DIR / "final_long.mp4"
SLUG = "the-white-collar-bypass"
STAGING_DIR = DOWNLOADS_STAGING / SLUG
STAGING_DIR.mkdir(parents=True, exist_ok=True)

with open(ASSET_DIR / "whisper_chunks.json") as f:
    chunks = json.load(f)

texts_en = [c["text"] for c in chunks]

texts_de = [
    "Seit über einem Jahrzehnt waren ausgelagerte Callcenter in Entwicklungsländern das verlässlichste Ticket in die Mittelschicht. Doch seit dem Aufstieg generativer künstlicher Intelligenz verschwindet diese gesamte Einstiegsleiter. Willkommen zum White-Collar-Bypass.",
    "Wer in Nordamerika oder Europa lebt, hat meist ein ganz bestimmtes, frustrierendes Bild von Callcentern: Man hängt in der Warteschleife, erträgt schreckliche Dudelmusik und versucht, eine Erstattung für einen verspäteten Flug zu bekommen. Doch auf den Philippinen, in Indien oder Kolumbien ist eine Stelle in solch einem Zentrum oft ein lebensverändernder Wendepunkt. Seit über zehn Jahren fungieren diese Jobs als verlässliches Sprungbrett in die",
    "formelle Arbeitswelt, besonders für junge Menschen und Frauen. Die Tätigkeit bietet ein geregeltes Gehalt, gute Krankenversicherung und einen eigenen Schreibtisch, ein greifbarer Weg in die aufstrebende Mittelschicht von Schwellenländern. Genau dieser Weg versperrt sich nun. Nach Jahren stetigen Wachstums ist die weltweite Zahl der Beschäftigten in Callcentern seit acht aufeinanderfolgenden Quartalen rückläufig. Diese Grafik zeichnet den Verlauf nach.",
    "Man erkennt ein Jahrzehnt stabiler Zuwächse bis zum Dezember zweitausenddreiundzwanzig. Dort erreicht die Beschäftigung ihren Höchststand und stürzt anschließend steil ab, um fünf Komma drei Prozent ins Minus. Wenn eine Branche Stellen abbaut, vermuten Ökonomen üblicherweise eine Verlagerung in noch billigere Niedriglohnländer, um Kosten zu sparen. Doch die weltweite Heatmap belegt: Der Einbruch begann in wohlhabenden Märkten wie den USA und Europa und hat sich dann",
    "in rasender Geschwindigkeit nach unten fortgepflanzt, sodass Lateinamerika und Südostasien zeitgleich von negativem Beschäftigungswachstum erfasst wurden. Die Unternehmen verlagern diesen Support nicht mehr in günstigere Länder. Das traditionelle Modell des Auslagerns von Einsteiger-Kundendiensten ist vollständig zum Stillstand gekommen. Man könnte einwenden, dies sei lediglich eine normale Konjunkturkorrektur nach dem Einstellungsboom der Pandemie und angesichts gestiegener Zinsen. Wäre das der Fall, sähen wir",
    "einen ähnlichen Einstellungsstopp bei allen Bürojobs dieser Schwellenländer. Doch das Gegenteil trifft zu: Der restliche Büroarbeitsmarkt boomt. Dieses Balkendiagramm vergleicht die jüngsten Beschäftigungstrends über Branchen hinweg: Während Callcenter schrumpfen, legte Customer Success um sieben Komma zwei Prozent zu und Software sowie Data stiegen um acht Komma neun Prozent. Diese Technologieberufe bieten erhebliche Gehaltssprünge und sind hochprofitabel. Eine Softwarerolle",
    "bringt mehr als das Doppelte des Gehalts eines gewöhnlichen Callcenter-Mitarbeiters. Die Bürowirtschaft dieser Länder floriert in vollen Zügen. Das Wirtschaftssystem ist intakt, doch die unterste Sprosse der Aufstiegsleiter ist verschwunden. Um die Ursache zu verstehen, müssen wir auf den genauen Zeitpunkt blicken, an dem sich die Callcenter-Daten vom Rest der Bürowelt entkoppelt haben: Dieser Bruch geschah im November zweitausendzweiundzwanzig. Zuvor spiegelten die Callcenter-Einstellungen exakt das Wachstum anderer administrativer",
    "und technischer Berufe wider. In genau diesem Monat stellte OpenAI ChatGPT der Öffentlichkeit vor. In den Monaten danach drifteten die Verläufe völlig auseinander: Die Belegschaften in Callcentern brachen ein, während alle anderen Angestelltenberufe ihren Aufstieg fortsetzten. Die Arbeit in diesen Zentren basiert vor allem auf standardisierten, streng vorgegebenen Abläufen in hoher Stückzahl. Genau dieses Profil macht sie zum perfekten Ziel für die Automatisierung durch große Sprachmodelle. Führende Dienstleister",
    "treiben diese Effizienzgewinne aggressiv voran und prognostizieren, dass autonome KI-Agenten ihre Supportkosten um bis zu fünfzig Prozent senken können. Sie ersetzen diese Stellen bewusst durch künstliche Intelligenz und steuern die Branche in eine rasche, gezielte Veralterung. Doch was passiert mit den betroffenen Menschen? In einer wachsenden Technologiewirtschaft könnte man erwarten, dass sie in expandierende, gut bezahlte Rollen aufsteigen. Doch ein Blick",
    "auf das Flussdiagramm der freigesetzten Arbeitskräfte zeichnet ein düsteres Bild: Nur zehn Komma acht Prozent gelingt der schmale Pfad nach oben in echte Technologierollen. Fast die Hälfte wird nach unten in schlechter bezahlte Tätigkeiten im Einzelhandel, Vertrieb oder einfache Bürojobs abgedrängt. Während die Spitzen der digitalen Wirtschaft boomen, bleiben Einstiegskräfte von diesen Wohlstandsgewinnen völlig abgeschnitten. Die Internationale Arbeitsorganisation in Genf hat",
    "dieses wachsende globale Risiko erkannt und ihm einen eigenen Namen gegeben: den White-Collar-Bypass. Das Konzept beschreibt das Szenario, in dem Entwicklungsländern genau jene Einstiegsjobs verloren gehen, über die wohlhabende Nationen einst ihre eigene breite Mittelschicht aufbauen konnten. Dass Technologie Berufe ersetzt, ist nicht neu: Im zwanzigsten Jahrhundert fanden Hunderttausende junger Frauen ihre erste bezahlte Arbeit außerhalb des Hauses an gewaltigen manuellen",
    "Telefonvermittlungen. Als die automatische Vermittlung dieses Berufsbild vollständig auflöste, passte sich die Wirtschaft an und die Arbeitskräfte wechselten in neu entstehende Rollen. Die drängende Frage unserer Ära lautet, ob die heutige Erwerbsbevölkerung dazu ebenfalls in der Lage ist. Wenn künstliche Intelligenz diesen niederschwelligen Einstiegspunkt tilgt, wird es für die nächste Generation in Schwellenländern extrem schwer, in der digitalen Wirtschaft Fuß zu fassen. Das Schrumpfen der Callcenter",
    "vernichtet nicht nur eine gewaltige Quelle unmittelbarer Beschäftigung: Noch beunruhigender ist, dass es dauerhaft jene Leiter einzieht, über die Millionen Menschen der Armut entkommen sind."
]

texts_fr = [
    "Depuis plus de dix ans, les centres d'appels délocalisés constituaient le tremplin le plus sûr vers la classe moyenne dans les pays en développement. Mais avec l'essor de l'intelligence artificielle générative, tout ce premier échelon s'efface. Bienvenue dans le grand contournement des cols blancs.",
    "Si vous vivez en Amérique du Nord ou en Europe, les centres d'appels vous évoquent sans doute une attente interminable, une musique d'ascenseur exaspérante et la lutte pour vous faire rembourser un vol retardé. Mais aux Philippines, en Inde ou en Colombie, décrocher un poste dans l'un de ces centres transforme souvent une vie. Depuis plus d'une décennie, ces emplois ont été la porte d'entrée la plus solide vers",
    "le monde de l'entreprise formel, surtout pour les jeunes et les femmes arrivant sur le marché du travail. Ce travail apporte un salaire régulier, une bonne couverture santé et un bureau dédié : une trajectoire directe vers la classe moyenne montante des nations en développement. Aujourd'hui, cette voie se referme. Après des années d'expansion continue, les effectifs mondiaux des centres d'appels chutent depuis huit trimestres consécutifs. Ce graphique en illustre la trajectoire.",
    "On observe une décennie de croissance régulière jusqu'en décembre deux mille vingt-trois, où l'emploi atteint son apogée avant de chuter brutalement, s'enfonçant de cinq virgule trois pour cent dans le rouge. Habituellement, lorsqu'un secteur détruit des emplois, les économistes supposent que les entreprises délocalisent simplement ces postes vers des pays à plus bas coûts. Mais cette carte thermique mondiale montre que la contraction a débuté dans les pays riches comme les États-Unis et l'Europe, puis",
    "s'est rapidement répercutée, plongeant l'Amérique latine et l'Asie du Sud-Est dans une baisse d'emplois simultanée. Les entreprises ne transfèrent plus ces postes vers des marchés moins chers : le modèle historique d'externalisation du support client est totalement à l'arrêt. On pourrait penser à une simple correction économique après la vague d'embauches de la pandémie et la hausse des taux d'intérêt. Si c'était le cas, nous verrions",
    "un gel similaire des embauches sur l'ensemble des postes de bureau dans ces pays. Au contraire, le marché des cols blancs y est en plein essor. Ce graphique à barres compare l'évolution récente des effectifs par secteur : les centres d'appels reculent, mais les postes de Customer Success progressent de sept virgule deux pour cent, et le logiciel et les données grimpent de huit virgule neuf pour cent. Des emplois technologiques particulièrement lucratifs. Un poste dans le logiciel",
    "paie plus du double d'un agent de centre d'appels de base. L'économie tertiaire de ces pays est florissante. Le système est bien portant, mais le premier barreau de l'échelle a disparu. Pour comprendre, il faut observer précisément le moment où les données des centres d'appels ont décroché du reste de l'économie de bureau : cette rupture survient en novembre deux mille vingt-deux. Jusqu'à cette date, les embauches en centre d'appels suivaient fidèlement la courbe des autres postes administratifs",
    "et techniques. C'est précisément ce mois-là qu'OpenAI a lancé ChatGPT auprès du grand public. Dès les mois suivants, les trajectoires divergent totalement : les effectifs des centres d'appels s'effondrent, tandis que les autres métiers de bureau continuent de progresser. Le travail dans ces centres repose sur un volume élevé d'échanges strictement encadrés par des scripts. Ce profil en fait la cible idéale pour l'automatisation par les grands modèles de langage. Les grands opérateurs",
    "poursuivent activement ces gains d'efficacité, prévoyant que des agents IA autonomes pourraient réduire les coûts de support client jusqu'à cinquante pour cent. Les leaders du secteur remplacent délibérément ces postes par de l'intelligence artificielle, organisant une obsolescence rapide et programmée. Qu'advient-il des salariés qui perdent leur emploi ? Dans une économie technologique florissante, on pourrait espérer qu'ils évoluent vers ces fonctions en plein essor. Pourtant,",
    "le schéma des flux de travailleurs déplacés révèle une réalité sombre : seuls dix virgule huit pour cent franchissent ce passage étroit vers les métiers de la tech. Près de la moitié bascule vers le bas, dans le commerce de détail moins rémunéré, la vente ou de la simple saisie administrative. Les niveaux supérieurs de l'économie numérique prospèrent, mais les débutants se retrouvent totalement exclus de ces gains. L'Organisation internationale du Travail à Genève a identifié",
    "ce risque mondial croissant sous un nom précis : le contournement des cols blancs. Ce concept décrit un scénario où les nations en développement perdent précisément les emplois de base qui ont autrefois permis aux pays riches de bâtir leur classe moyenne. La technologie a déjà fait disparaître des métiers : au vingtième siècle, des centaines de milliers de jeunes femmes ont trouvé leur premier emploi rémunéré en opérant des centraux téléphoniques",
    "manuels. Lorsque la commutation automatique a éliminé cette profession, l'économie s'est adaptée et les employés ont basculé vers de nouveaux rôles. La question cruciale pour notre époque est de savoir si les travailleurs d'aujourd'hui peuvent en faire autant. Si l'intelligence artificielle supprime cette porte d'entrée si accessible, la prochaine génération aura bien du mal à prendre pied dans l'économie numérique. Le déclin des centres d'appels",
    "détruit un réservoir massif d'emplois immédiats. Plus alarmant encore, il retire définitivement l'échelle qui a permis à des millions d'individus de s'extraire de la pauvreté."
]

texts_ja = [
    "過去10年以上にわたり、業務委託のコールセンターは新興国の人々が中間層へと這い上がる最も確実な登竜門でした。しかし生成AIの登場により、その最初のはしごが今、完全に消え去ろうとしています。「ホワイトカラー・バイパス」の世界へようこそ。",
    "北米や欧州にお住まいの方なら、コールセンターと聞けば保留音にイライラさせられ、飛行機の払い戻しを求めて格闘する姿を思い浮かべるでしょう。しかしフィリピンやインド、コロンビアでは、こうしたセンターへの就職は人生を一変させる出来事です。10年以上にわたり、これらの職は",
    "正規の企業社会への極めて確実な入り口として機能してきました。若者や働く女性にとっては特に重要です。安定した給与、充実した健康保険、専用のデスクを提供し、新興国の成長する中間層への直接的な道となってきました。現在、その道が閉ざされつつあります。長年の安定成長を経て、世界のコールセンターの人員は8四半期連続で減少しました。このグラフはその軌跡を示しています。",
    "2023年12月まで10年間に及ぶ安定成長が続き、そこで雇用がピークに達したあと急落し、マイナス5.3パーセントへと転じたことがわかります。通常、特定分野で雇用が減ると、企業がコスト削減のためにさらに低賃金の国へ移転させたと経済学者は考えます。しかし世界分布図を見ると、縮小はまずアメリカや欧州などの高所得国で始まり、",
    "急速に波及して、中南米や東南アジアでも全く同じ時期に雇用のマイナス成長が広がったのです。企業はもはやサポート業務を低賃金市場に移転していません。エントリーレベルの顧客窓口をオフショア化する伝統的なモデルは完全に停止しました。パンデミック期の採用バブルや高金利による通常の後退ではないかと思うかもしれません。もしそうなら、",
    "これら新興国におけるオフィスワーク全体で同様の採用抑制が起きるはずです。しかし実際には、広義のホワイトカラー市場は沸き立っています。この棒グラフは各セクターの近年の雇用変化を比較したものです。コールセンターが縮小する一方で、カスタマーサクセスは7.2パーセント成長し、ソフトウェアとデータ分野は8.9パーセント上昇しました。これらテック職は非常に高給です。ソフトウェア職の給与は",
    "一般のコールセンター窓口担当者の2倍以上です。これらの国々のオフィス経済は絶好調です。システム自体は健全なのに、はしごの最初の一段だけが消滅したのです。何が起きたのかを探るには、コールセンターの数値がオフィス経済全体から乖離した時期を見極める必要があります。その分岐点は2022年11月です。この月より前は、コールセンターの採用は他の事務職や",
    "技術職の伸びと完全に一致していました。まさにその月、OpenAIがChatGPTを一般公開したのです。リリース直後の数か月で、両者の軌道は完全に分岐しました。コールセンターの人員は急減し、他のホワイトカラー職は上昇を続けたのです。これらサポート窓口の業務は、定型化されたスクリプト通りの大量の対話が中心です。その特徴こそが、大規模言語モデルによる自動化の格好の標的となりました。大手運用企業は",
    "積極的な効率化を進めており、自律型AIエージェントが顧客サポートコストを最大50パーセント削減できると予測しています。大手事業者はこれらの職を意図的にAIへと置き換え、業界を計画的な急速の陳腐化へと導いています。では職を失った人々はどうなるのでしょうか？活況を呈するテック経済において、彼らが拡大中の高給な職へステップアップすると期待するかもしれません。しかし",
    "職を追われた労働者のフロー図を見ると、現実は厳しいものです。テック職への狭き門を上れたのはわずか10.8パーセントに過ぎません。図が下方に広がる通り、半数近くがより低賃金の小売業、販売、一般的な雑務へと転落しています。デジタル経済の上層部は潤っていますが、エントリーレベルの労働者はその果実から完全に締め出されています。ジュネーブの国際労働機関ILOはこの",
    "深刻化する世界規模のリスクを認識し、「ホワイトカラー・バイパス」と名付けました。これは、かつて先進国が豊かな中間層を形成する土台となった初任職の受け皿を、新興国が失ってしまう現象を指します。技術が職業を代替した例は過去にもありました。20世紀には、何十万人もの若い女性が巨大な手動の電話交換台を操作することで、",
    "家庭外で初めての有給雇用を得ました。自動交換機によってその手動の職業が消えた際、経済は適応し、労働者は他の新しい職業へと移行しました。現代における切実な問いは、今日の労働力に同じことができるのかという点です。もし人工知能がこの極めて身近な参入障壁を消し去れば、新興国の次世代はデジタル経済に足がかりを築くことが難しくなります。コールセンターの",
    "縮小は、直接的な雇用の巨大な受け皿を奪うだけではありません。より深刻なのは、何百万人もの人々を貧困から救い上げてきた「上昇のはしご」を永遠に引き上げてしまうことなのです。"
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

# Dubbing
audio_de = ASSET_DIR / f"{SLUG}_audio_de.m4a"
audio_fr = ASSET_DIR / f"{SLUG}_audio_fr.m4a"

log("Assembling German dub...")
assemble_dub(chunks, texts_de, VOICE_DE, dur, audio_de, ASSET_DIR / "tmp_de")

log("Assembling French dub...")
assemble_dub(chunks, texts_fr, VOICE_FR, dur, audio_fr, ASSET_DIR / "tmp_fr")

# Copy to staging directory
log("Staging files to Downloads...")
for p in [srt_en, srt_de, srt_fr, srt_ja, audio_de, audio_fr]:
    shutil.copy2(p, STAGING_DIR / p.name)

hook_vo = ASSET_DIR / f"{SLUG}_hook_vo.mp3"
if hook_vo.exists():
    shutil.copy2(hook_vo, STAGING_DIR / hook_vo.name)

final_copy = STAGING_DIR / "The_White-Collar_Bypass_FINAL.mp4"
shutil.copy2(FINAL_VIDEO, final_copy)
log(f"All assets staged to {STAGING_DIR}")
