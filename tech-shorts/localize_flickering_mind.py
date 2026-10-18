#!/usr/bin/env python3
import json, shutil, sys
from pathlib import Path

# Add tech-shorts directory
sys.path.insert(0, "/Users/miguelrodriguez/projects/agentic-fleet-hub/tech-shorts")
from run_batch_localize import assemble_dub, write_srt, ffdur, log, DOWNLOADS_STAGING, VOICE_DE, VOICE_FR

ASSET_DIR = Path("/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-18-the-flickering-mind")
FINAL_VIDEO = ASSET_DIR / "final_long.mp4"
SLUG = "the-flickering-mind"
STAGING_DIR = DOWNLOADS_STAGING / SLUG
STAGING_DIR.mkdir(parents=True, exist_ok=True)

with open(ASSET_DIR / "whisper_chunks.json") as f:
    chunks = json.load(f)

texts_en = [c["text"] for c in chunks]

texts_de = [
    "Seit Jahrzehnten suchten Neurowissenschaftler nach dem einen Ort im Gehirn, an dem das Bewusstsein sitzt. Doch eine bahnbrechende Studie aus dem Labor von Doris Tsao zeigt nun: Unser Gehirn ist keine unbewegte Kamera. Es flackert fünfzehn Mal pro Sekunde zwischen bewussten und unterdrückten Welten hin und her.",
    "Willkommen zum heutigen Erklärvideo. Heute entschlüsseln wir ein echtes biologisches Rätsel: das menschliche Bewusstsein. Wir bewegen uns täglich nahtlos durch die Welt, sehen Farben, erkennen Gesichter und spüren den Wind. Doch wie erzeugt die feuchte Hardware in unserem Schädel dieses ununterbrochene Gefühl der Realität? Schnallen Sie sich an, denn neueste Durchbrüche belegen: Ihr Geist leistet etwas unglaublich Dynamisches,",
    "und das beruht auf einem geheimen, rasenden Rhythmus, von dem Sie nichts ahnen. Wo im Gehirn wohnt das Bewusstsein also wirklich? Das ist es, was Philosophen das schwierige Problem nennen. Wir wissen genau, wie Licht auf die Netzhaut trifft und wie Signale den Sehnerv entlanglaufen. Doch unser subjektives Bewusstsein einer konkreten, messbaren Biologie zuzuordnen, war eine gewaltige Hürde. Über Generationen nahmen Forscher an,",
    "wenn wir nur an der richtigen Stelle im Gehirn suchen, fänden wir ein unüberhörbares Signal, das quasi ruft: Genau dieses Objekt sehe ich jetzt bewusst! Doch die Realität war ernüchternd: Wie die Forschungsarbeit betont, wurde ein reines Signal bewusster Wahrnehmung nirgendwo im Gehirn gefunden. Denken Sie darüber nach: Als Wissenschaftler die durchschnittliche Hirnaktivität bei der Betrachtung verschiedener Bilder analysierten, standen sie vor einem Rätsel.",
    "Sie stießen lediglich auf schwache, verwaschene und verwirrende Signale, die keineswegs zur lebhaften Wahrnehmung der Probanden passten. Es schien, als flüstere das Gehirn ein wirres Durcheinander, selbst wenn die Person völlig klar auf ein leuchtendes Bild blickte.",
    "Das Flash-Suppression-Experiment: Die Trennung von Reiz und Wahrnehmung. Tauchen wir ein in dieses geniale Experiment, mit dem Forscher trennten, was die Augen sehen, von dem, was der Geist wahrnimmt. Mit hochdichten Neuropixels-Sonden zeichneten sie die Hirnaktivität von Rhesusaffen während dieser raffinierten Aufgabe auf.",
    "Schritt eins: Ein Auge wird vorbereitet, indem man ihm ein Bild zeigt, beispielsweise ein bestimmtes Gesicht. Schritt zwei: Ein oder zwei Sekunden später wird dem anderen Auge blitzartig ein völlig anderes Bild präsentiert. Schritt drei, und das ist das Verrückte: Obwohl beide Bilder physikalisch auf dem Bildschirm präsent sind, blendet das Gehirn das erste Bild komplett aus dem Bewusstsein aus.",
    "Der physikalische Reiz bleibt unverändert, aber die bewusste Wahrnehmung wählt einen klaren Favoriten. Bei der Analyse der neuronalen Daten erkannten die Wissenschaftler Bahnbrechendes: Erinnern Sie sich an die verwaschenen Signale von vorhin? Im Vergleich zur neuen Wirklichkeit verstanden die Forscher, dass die gemittelte Aktivität über mehrere Sekunden bloß eine verwackelte Langzeitbelichtung eines extrem schnellen Ziels war.",
    "Als sie aufhörten, die Daten zu mitteln, und sie stattdessen Millisekunde für Millisekunde analysierten, verschwand das Rauschen vollständig. An seine Stelle traten glasklare, hochpräzise Signale. Das Gehirn war keineswegs verwirrt; es arbeitete schlicht atemberaubend schnell. Das Geheimnis lag also nicht darin, wo das Bewusstsein verortet ist,",
    "sondern wie schnell es umschaltet. Und wie rasant ist dieser Wechsel? Um das reine Bewusstseinssignal aufzuspüren, brauchten die Forscher schlicht eine schnellere Kamera. Und die gefundene Zahl lautet: fünfzehn.",
    "Das Gehirn schaltet buchstäblich rund fünfzehn Mal pro Sekunde zwischen dem bewussten und dem unterdrückten Zustand hin und her. Sie haben richtig gehört: Etwa alle sechzig Millisekunden wechselt die neuronale Aktivität zwischen bewussten und unterdrückten Mikroepochen. Ihr Gehirn verhält sich im Grunde wie ein flackernder Bildschirm. Im einen Augenblick bildet es das ab, was Sie bewusst sehen, und im nächsten Bruchteil einer Sekunde feuert dieselbe",
    "Zellpopulation für das Bild, das Sie vollkommen ignorieren und das Ihrem Bewusstsein entzogen ist. Dieses Flackern spüren wir nicht: Für uns wirkt die Welt völlig stabil. Doch unter der Haube springt das Gehirn unablässig hin und her. Das Unbewusste rekonstruieren und sehen, was das Gehirn verbirgt: Was tut das Gehirn in jenem winzigen Fenster von sechzig Millisekunden, wenn es in den unterdrückten Zustand springt? Nun, Forscher nutzten",
    "einen linearen Dekodierer auf den neuronalen Daten, um diese verborgenen Bilder mathematisch direkt aus dem Gehirn zu rekonstruieren, der visuelle Beweis. Links erkennt man deutlich Zustand eins: das bewusste Gesicht, das der Affe tatsächlich wahrnahm. Doch sehen Sie sich Zustand zwei an.",
    "Das unbewusste Bild ist vollständig gerendert, detailreich und klar vom bewussten Zustand getrennt. Das unterdrückte Bild wird keineswegs verworfen oder zu statischem Rauschen degradiert: Es ist während der unterdrückten Mikroepochen hochaktiv und lebendig im Gehirn vorhanden. Das führt zu einem gewaltigen Paradigmenwechsel, der temporalen Selektion. Das ist der Mechanismus, durch den das",
    "Gehirn bewusste und unterdrückte Repräsentationen über die Zeit trennt, statt sie auf verschiedene Hirnregionen zu verteilen. Die Zeit ist hier die fehlende Dimension.",
    "Exakt dieselben Neuronen kodieren sowohl das bewusste als auch das unterdrückte Gesicht, indem sie sich in rascher Folge abwechseln. Sie teilen sich die biologische Hardware, indem sie die Zeit portionieren.",
    "Warum das alles verändert: Die Bedeutung des zeitlichen Multiplexings. Dieses Konzept des temporalen Multiplexings, dieses unfassbar schnelle Flackern zwischen zwei Realitäten, stellt unser Verständnis der visuellen Verarbeitung völlig auf den Kopf. Erstens: Sowohl bewusste als auch unterdrückte Reize werden im Gehirn vollwertig abgebildet; das Unbewusste ist keine schwache Spur. Zweitens: Einzelne Zellen kodieren beides durch rasantes Umschalten. Drittens:",
    "Der einzige wirkliche Unterschied besteht darin, dass bewusste Zustände eine etwas stärkere Verstärkung in ihrer neuronalen Abstimmung aufweisen. Und schließlich: Der Zugang zum Bewusstsein erfordert zwingend diese temporale Selektion. Ihr Gehirn ist ein genialer Zeitmanager, der dem Bewusstsein in diesen winzigen Fenstern von sechzig Millisekunden Vorrang gewährt. Das hinterlässt einen faszinierenden Gedanken:",
    "Ihr Gehirn nimmt das gesamte Sehfeld auf: Es rendert die Dinge, die Sie bemerken, und ebenso jene, von denen Sie gar nichts wissen, und jongliert beides fünfzehn Mal pro Sekunde hin und her. Wenn Ihr Gehirn also ausnahmslos alles sieht und so viel Energie investiert, warum filtert es aktiv und lässt Sie nur die Hälfte bewusst erleben? Was bewertet Ihr Unbewusstes im Verborgenen? Es ist eine",
    "faszinierende Frage für Ihren Alltag, während Sie sich der flackernden Realität in Ihrem eigenen Kopf völlig unbewusst sind. Danke, dass Sie bei diesem Erklärvideo dabei waren, und hinterfragen Sie stets, was Sie zu sehen glauben."
]

texts_fr = [
    "Pendant des décennies, les neuroscientifiques ont cherché l'endroit précis du cerveau où réside la conscience. Mais une étude révolutionnaire du laboratoire de Doris Tsao vient de révéler que votre cerveau n'est pas une caméra continue. Il scintille entre mondes conscients et supprimés quinze fois par seconde.",
    "Bienvenue dans cette vidéo explicative. Aujourd'hui, nous décryptons un véritable mystère biologique : la conscience humaine. Tout au long de la journée, nous faisons l'expérience fluide du monde, percevant les couleurs, reconnaissant les visages, sentant la brise. Mais comment la matière organique de notre crâne produit-elle cette réalité continue ? Accrochez-vous, car des découvertes récentes montrent que votre esprit accomplit quelque chose d'incroyablement dynamique,",
    "qui repose sur un rythme ultra-rapide dont vous n'avez même pas conscience. Alors, où réside réellement la conscience dans le cerveau ? C'est ce que les philosophes nomment le problème difficile. Nous savons exactement comment la lumière frappe la rétine et comment les signaux parcourent le nerf optique. Mais relier notre expérience consciente subjective à une biologie mesurable restait un obstacle colossal. Les scientifiques ont longtemps supposé",
    "qu'en observant la bonne région cérébrale, ils trouveraient un signal éclatant proclamant : Je vois consciemment cet objet précis en ce moment ! Mais la réalité s'est révélée déconcertante : comme le souligne l'étude source, aucun signal pur de perception consciente n'a jamais été localisé dans le cerveau. Songez-y : en mesurant l'activité cérébrale moyenne de sujets observant diverses images, les chercheurs sont restés perplexes.",
    "Ils ne détectaient que des signaux faibles, confus et brouillés, en décalage total avec la netteté de l'expérience vécue. C'était comme si le cerveau murmurait un message chaotique, alors même que la personne contemplait lucidement une image éclatante.",
    "L'expérience de suppression par flash : dissocier l'entrée visuelle de la perception. Découvrons cette expérience ingénieuse conçue pour séparer ce que les yeux reçoivent de ce que l'esprit perçoit réellement. À l'aide de sondes Neuropixels à haute densité, les chercheurs ont suivi l'activité cérébrale de macaques durant une tâche particulièrement brillante.",
    "Étape une : on prépare un premier œil en lui présentant une image, par exemple un visage. Étape deux : une à deux secondes plus tard, on projette brusquement une image totalement différente à l'autre œil. Étape trois, la plus fascinante : bien que les deux images soient physiquement affichées à l'écran, le cerveau efface complètement la première de la conscience.",
    "Le stimulus visuel ne change pas, mais la perception consciente sélectionne un favori absolu. En analysant les données neuronales durant cette suppression, les chercheurs ont fait une découverte fondamentale. Rappelez-vous les signaux brouillés évoqués plus tôt : ils ont compris que mesurer l'activité moyenne sur plusieurs secondes revenait à prendre une photographie floue à longue exposition",
    "d'une cible en mouvement perpétuel. Dès qu'ils ont cessé de moyenner les signaux pour les examiner milliseconde par milliseconde, le brouillard s'est dissipé. À sa place ont émergé des signaux d'une pureté cristalline. Le cerveau n'était pas confus : il fonctionnait à une vitesse vertigineuse. Le secret ne résidait pas dans le lieu de la conscience,",
    "mais dans la cadence de ses bascules. À quel point est-ce rapide ? Pour isoler ce signal pur, il suffisait d'une caméra plus rapide. Et le chiffre obtenu est : quinze.",
    "Le cerveau oscille littéralement entre l'état conscient et l'état supprimé environ quinze fois par seconde. Vous avez bien entendu : toutes les soixante millisecondes environ, l'activité neuronale alterne entre micro-époques conscientes et supprimées. Votre cerveau fonctionne comme un écran scintillant. Un instant, il représente ce dont vous avez conscience, et une fraction de seconde plus tard, cette même",
    "population neuronale bascule pour encoder l'image que vous ignorez totalement, celle qui est supprimée de votre champ conscient. Vous ne ressentez absolument pas ce scintillement : le monde vous paraît d'une parfaite stabilité. Pourtant, en coulisses, votre cerveau saute sans cesse d'un état à l'autre. Reconstruire l'inconscient, révéler ce que le cerveau dissimule : que fabrique-t-il durant cette infime fenêtre de soixante millisecondes ? Les chercheurs ont employé",
    "un décodeur linéaire sur les signaux neuronaux pour extraire mathématiquement ces images cachées du cerveau et en fournir la preuve visuelle. On distingue nettement l'état un à gauche, soit le visage perçu consciemment par le singe. Mais observez l'état deux.",
    "L'image inconsciente est entièrement reconstituée, d'une grande richesse de détails et nettement séparée de l'état conscient. Cette image supprimée n'est ni abandonnée ni réduite à du bruit : elle est intensément vivante dans le cerveau durant ces micro-époques supprimées. Cela nous conduit à un basculement théorique majeur : la sélection temporelle. C'est le mécanisme par lequel le",
    "cerveau sépare les contenus conscients et supprimés dans le temps, plutôt que de les isoler dans des zones anatomiques distinctes. Le temps est ici la dimension manquante.",
    "Les mêmes neurones encodent tour à tour le visage conscient et le visage supprimé en alternant rapidement. Ils partagent le support biologique en fractionnant le temps.",
    "Pourquoi cela change tout : les implications du multiplexage temporel. Ce concept de multiplexage temporel, ce scintillement ultra-rapide entre deux réalités, révolutionne notre conception de la vision. Premièrement : les stimuli conscients et supprimés sont tous deux intégralement représentés ; l'inconscient n'est pas une trace ténue. Deuxièmement : chaque cellule encode les deux états en basculant à grande vitesse. Troisièmement :",
    "la seule vraie différence réside dans un gain ou une intensité légèrement supérieure de l'accordage neuronal lors des états conscients. Enfin, l'accès à la conscience exige impérativement cette sélection temporelle. Votre cerveau est un maître du temps qui accorde la priorité à la conscience dans ces minuscules créneaux de soixante millisecondes. Ce qui nous laisse avec une réflexion vertigineuse :",
    "Votre cerveau absorbe l'intégralité du champ visuel : il modélise ce que vous remarquez et recrée fidèlement ce dont vous ignorez la présence, jonglant de l'un à l'autre quinze fois par seconde. Si votre cerveau voit absolument tout et dépense une telle énergie, pourquoi filtre-t-il activement pour ne vous laisser vivre consciemment que la moitié ? Qu'évalue votre inconscient dans l'obscurité ? C'est une",
    "question passionnante à méditer au fil de votre journée, parfaitement inconscient de cette réalité vacillante au cœur de votre esprit. Merci d'avoir suivi cette vidéo, et continuez à vous interroger sur ce que vous croyez voir."
]

texts_ja = [
    "何十年もの間、脳科学者たちは意識が宿る脳内のたった一つの場所を探し求めてきました。しかしドリス・ツァオの研究室による画期的な研究は、私たちの脳が決して固定カメラではないことを明らかにしました。脳は1秒間に15回、意識と抑制の世界を行き来しながら明滅しているのです。",
    "エクスプローラーへようこそ。本日は生物学最大の謎、人間の意識を解き明かします。私たちは日々、色を感じ、顔を識別し、風を感じながら、世界を途切れなく体験しています。しかし頭蓋骨の中にある生体組織は、いかにしてこの連続した現実感を生み出しているのでしょうか？最新の科学的躍進は、脳が極めて動的な処理を行っていることを示しています。",
    "そこには、私たちが自覚すらしていない秘密の超高速リズムが関わっています。では、意識は脳のどこに宿るのでしょうか？哲学者たちがハード・プロブレムと呼ぶ難問です。光が網膜に届き、信号が視神経を通る仕組みは完全に解明されています。しかし、主観的な意識体験を測定可能な生物学的基盤と結びつけることは巨大な壁でした。長きにわたり、研究者たちは当然のように考えていました。",
    "脳内の正しい場所を見つけさえすれば、「今まさにこの物体を意識的に知覚している」と叫ぶ明白な信号が見つかるはずだと。しかし直面した現実は全く異なっていました。論文にある通り、意識的知覚の純粋なシグナルは脳のいかなる場所にも存在しなかったのです。被験者が様々な画像を注視しているときの平均脳活動を調べた科学者たちは、完全に当惑しました。",
    "被験者の鮮明な体験とは一致しない、微弱で曖昧かつ混乱した信号しか検出できなかったのです。被験者がくっきりとした明るい画像をはっきりと意識して見つめている時でさえ、脳はまるで混信したメッセージを囁いているかのようでした。",
    "フラッシュ抑制実験：入力と知覚の解離。目に見えている物理的刺激と、心が知覚している体験を切り離すために研究者が用いた巧妙な実験を見てみましょう。彼らは高密度ニューロピクセル電極を使い、マカクザルの脳活動を記録しながら画期的な課題を実施しました。",
    "ステップ1：片方の目に特定の顔などの画像を提示して慣れさせます。ステップ2：1〜2秒後、もう片方の目に全く異なる新しい画像を一瞬でフラッシュ提示します。ステップ3：ここからが驚異的な点です。両方の画像が物理的に画面上に存在しているにもかかわらず、脳は最初の画像を意識から完全に消去してしまうのです。",
    "物理的な入力は変わらないのに、意識的な知覚は一方だけを選択します。この抑制状態の神経データを精査することで、研究者たちは極めて重大な事実に気づきました。先ほど触れた曖昧で微弱な信号を思い出してください。数秒間の平均脳活動を観察することは、高速で動く対象を手ブレの長時間露光で撮影するようなものだったのです。",
    "データの平均化をやめ、ミリ秒単位で時間変化を追跡した瞬間、曖昧な信号は完全に消え去りました。そしてその代わりに、極めて高精度で純粋な信号が現れたのです。脳は決して混信していたのではなく、驚異的な超高速で切り替わっていたのです。秘密は場所ではなく、",
    "その切り替え速度にありました。では一体どれほどの速度なのでしょうか？意識の純粋なシグナルを捉えるために研究者が必要としたのは、よりシャッタースピードの速いカメラでした。そして突き止められた数値は15だったのです。",
    "脳は文字通り、意識状態と抑制状態の間を1秒間に約15回も往復しています。聞き間違いではありません。約60ミリ秒ごとに、神経活動は意識的マイクロエポックと抑制的マイクロエポックを交互に繰り返しているのです。脳は実質的に明滅するスクリーンのように振る舞っています。ある瞬間は意識している画像を表現し、",
    "そのわずか一瞬後には、全く同じ神経集団が、意識から完全に排除された無視している画像を表現するよう反転するのです。私たちはこの明滅を自覚できません。世界は完全に安定して見えますが、内部では脳が激しく跳躍しています。無意識の再構成：脳が隠しているものを見る。では60ミリ秒の窓の中で、脳は何をしているのでしょうか？",
    "研究者たちは神経データに線形デコーダーを適用し、隠された画像を脳から数学的に直接抽出して視覚的証拠を得ました。左側の状態1では、サルが能動的に知覚していた意識的な顔が鮮明に復元されています。しかし右側の状態2をご覧ください。",
    "無意識の画像も細部まで豊かに完全にレンダリングされ、意識状態から完全に分離されているのです。抑制された画像は決して破棄されたりノイズ化されたわけではありません。抑制的マイクロエポックの間、脳内で鮮明に生き生きと活動しているのです。これはパラダイムシフトをもたらします。時間的選択と呼ばれる概念です。",
    "脳が意識的表象と抑制的表象を、異なる脳部位に振り分けるのではなく時間軸上で分離する仕組みです。時間こそが見落とされていた次元でした。",
    "全く同じニューロンが、交互に素早く役割を交代することで、意識された顔と抑制された顔の双方を動的にエンコードしているのです。ハードウェアを共有し、時間をスライスして使っているのです。",
    "なぜこれが全てを変えるのか：時分割多重化（テンポラル・マルチプレクシング）の意義。この現時間での高速な明滅は、視覚処理の理解を根底から覆します。第1に、意識的刺激も抑制的刺激も脳内で豊かに完全再現されており、無意識は単なる薄れた痕跡ではないこと。第2に、単一細胞が急速に交代して両方を表現していること。第3に、",
    "唯一の真の違いは、意識状態の方が神経チューニングのゲイン（強度）がわずかに高いという点だけです。そして意識体験へのアクセスには、この時間的選択が不可欠です。脳は時間を巧みに管理し、この60ミリ秒の窓で意識に優先順位を与えているのです。ここである深遠な疑問が浮かびます。",
    "脳は視野全体を受け取り、気づいた対象だけでなく、存在すら知らない対象まで完全にレンダリングし、毎秒15回も両者をジャグリングしています。脳が全てを見て膨大なエネルギーを消費しているなら、なぜ能動的にフィルターをかけ、半分しか意識させないのでしょうか？無意識は暗闇の中で何を評価しているのか？",
    "自分の頭の中にある明滅する現実に気づくことなく過ごす日常の中で、深く考えさせられる問いです。ご視聴ありがとうございました。自分が見ていると信じているものを、疑い続けてみてください。"
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

import localize as L

# Dubbing
audio_de = ASSET_DIR / f"{SLUG}_audio_de.m4a"
audio_fr = ASSET_DIR / f"{SLUG}_audio_fr.m4a"

if audio_de.exists() and audio_de.stat().st_size > 1000000:
    log(f"German dub already exists ({audio_de.stat().st_size // 1024}KB) — skipping regeneration.")
else:
    log("Assembling German dub...")
    assemble_dub(chunks, texts_de, VOICE_DE, dur, audio_de, ASSET_DIR / "tmp_de")

log("Assembling French dub with local Kokoro (ff_siwis)...")
L.assemble(None, chunks, texts_fr, "kokoro:fr:ff_siwis", dur, audio_fr, ASSET_DIR / "tmp_fr_kokoro")


# Copy to staging directory
log("Staging files to Downloads...")
for p in [srt_en, srt_de, srt_fr, srt_ja, audio_de, audio_fr]:
    shutil.copy2(p, STAGING_DIR / p.name)

hook_vo = ASSET_DIR / f"{SLUG}_hook_vo.mp3"
if hook_vo.exists():
    shutil.copy2(hook_vo, STAGING_DIR / hook_vo.name)

final_copy = STAGING_DIR / "The_Flickering_Mind_FINAL.mp4"
shutil.copy2(FINAL_VIDEO, final_copy)
log(f"All assets staged to {STAGING_DIR}")
