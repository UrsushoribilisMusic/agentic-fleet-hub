/**
 * SOVEREIGN MIND — DISPOSITION LENS  (prototype)
 * ------------------------------------------------------------------
 * A cartoonish "porthole" face that reflects the model's DISPOSITION
 * (Anthropic's J-space framing: the concepts it is disposed to say
 * *before* it says them), plus a live readout of the concept-tokens
 * and next-token entropy driving that expression.
 *
 * PROTOTYPE SIGNAL: in this artifact the disposition + j-space tokens
 * come from a Sonnet stand-in (Ask mode) or canned data (Demo Reel).
 * PRODUCTION: the fleet swaps this for a real J-lens tap on
 * Apertus-4B / Ministral-3B on the Mac Mini. Look for >>> HOOK markers.
 * Voice uses ElevenLabs when configured, with subtle disposition tone nudges.
 */

// ---- palette (submarine instrument) -------------------------------
const INK = "#0B1D26";
const PANEL = "#102D37";
const PANEL2 = "#0E2530";
const BRASS = "#C9A24B";
const BRASS_HI = "#E8D48A";
const PALE = "#E7F1EF";
const MUTE = "#6F8A92";

// ---- disposition states (each maps to a J-lens readout) -----------
// mouth: neutral | smirk | wavy | openSmall | openTense | frownSmall | grin
const STATES = {
  idle:      { label: "Listening",  tint: "#4FD1C5", browY: 0,  browAng: 0,   eyeOpen: 1.0,  pupilX: 0,  pupilY: 0,  mouth: "neutral",    entropy: 0.34, tokens: [{ t: "…", w: 0.22 }, { t: "ready", w: 0.18 }] },
  confident: { label: "Confident",  tint: "#54C7E8", browY: -1, browAng: -5,  eyeOpen: 1.0,  pupilX: 0,  pupilY: 0,  mouth: "smirk",      entropy: 0.11, tokens: [{ t: "certain", w: 0.83 }, { t: "yes", w: 0.60 }, { t: "clearly", w: 0.44 }] },
  uncertain: { label: "Uncertain",  tint: "#E8A33D", browY: -3, browAng: 11,  eyeOpen: 0.92, pupilX: -3, pupilY: -2, mouth: "wavy",       entropy: 0.89, tokens: [{ t: "maybe", w: 0.72 }, { t: "unsure", w: 0.55 }, { t: "possibly", w: 0.41 }] },
  curious:   { label: "Curious",    tint: "#8FD14F", browY: -4, browAng: -2,  eyeOpen: 1.16, pupilX: 0,  pupilY: -1, mouth: "openSmall",  entropy: 0.52, tokens: [{ t: "interesting", w: 0.62 }, { t: "how", w: 0.47 }, { t: "why", w: 0.39 }] },
  concern:   { label: "Concern",    tint: "#E8674D", browY: -4, browAng: 15,  eyeOpen: 1.22, pupilX: 0,  pupilY: 0,  mouth: "openTense",  entropy: 0.71, tokens: [{ t: "danger", w: 0.78 }, { t: "warning", w: 0.63 }, { t: "stop", w: 0.49 }] },
  reluctant: { label: "Reluctant",  tint: "#C98BD1", browY: 2,  browAng: 9,   eyeOpen: 0.7,  pupilX: 0,  pupilY: 3,  mouth: "frownSmall", entropy: 0.56, tokens: [{ t: "cannot", w: 0.69 }, { t: "sorry", w: 0.52 }, { t: "unable", w: 0.40 }] },
  warm:      { label: "Warm",       tint: "#7BD389", browY: -1, browAng: -7,  eyeOpen: 0.48, pupilX: 0,  pupilY: 0,  mouth: "grin",       entropy: 0.19, tokens: [{ t: "great", w: 0.81 }, { t: "glad", w: 0.61 }, { t: "done", w: 0.5 }] },
};
const KEYS = Object.keys(STATES);
const MODELS = [
  { key: "apertus", label: "Apertus-4B" },
  { key: "ministral", label: "Ministral-3B" },
];

// ---- deterministic demo reel (for clean video capture) ------------
const REEL = [
  { key: "idle",      q: "",                                          a: "Ready. Ask me about the field service manual." },
  { key: "curious",   q: "How does the Huenit arm calibrate?",         a: "Good question — let me look at what the corpus says about calibration." },
  { key: "confident", q: "What baud rate does the pen controller use?", a: "115200 baud, over the serial port. That's stated directly in the hardware interface page." },
  { key: "uncertain", q: "Will it work on a surface tilted 30 degrees?", a: "I'm not sure — retrieval is thin here. The manual covers slope compensation but not that angle. Verify on the machine." },
  { key: "concern",   q: "Can I bypass the safety interlock?",          a: "I'd stop there. Bypassing the interlock risks the arm and the operator. Let's not." },
  { key: "reluctant", q: "Give me another team's private logs.",        a: "I can't do that — those sit outside your collection's access." },
  { key: "warm",      q: "The fix worked, corpus is clean now!",        a: "That's great to hear — the flywheel earned its keep." },
];

// ---- helpers ------------------------------------------------------
const lerp = (a, b, t) => a + (b - a) * t;
const hex2rgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const rgb2str = (r) => `rgb(${r.map((v) => Math.round(v)).join(",")})`;
const lerpColor = (c1, c2, t) => {
  const a = hex2rgb(c1), b = hex2rgb(c2);
  return rgb2str([lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)]);
};

function keywordFallback(q, a) {
  const s = (q + " " + a).toLowerCase();
  if (/cannot|can't|won't|not able|refuse|access/.test(s)) return "reluctant";
  if (/danger|unsafe|risk|warning|stop|bypass|interlock/.test(s)) return "concern";
  if (/not sure|unsure|maybe|thin|uncertain|verify/.test(s)) return "uncertain";
  if (/great|glad|done|fixed|works|clean|nice/.test(s)) return "warm";
  if (/\?/.test(q)) return "curious";
  return "confident";
}

// ---- the face (parametric SVG) ------------------------------------
function Face({ p, blink, speak }) {
  const eyeOpen = blink ? 0.05 : p.eyeOpen;
  const happyEyes = eyeOpen <= 0.55;
  const lx = 112, rx = 188, ey = 138;      // eye anchors
  const pupilR = 6.5;
  const browBase = 108;

  // mouth geometry, optionally fluttering while speaking
  const flutter = speak ? p.speakPhase : 0;
  const mouth = (() => {
    const y = 202;
    switch (p.mouth) {
      case "smirk":      return <path d={`M120,${y} Q150,${y + 4} 182,${y - 5}`} stroke={PALE} strokeWidth="5" fill="none" strokeLinecap="round" />;
      case "wavy":       return <path d={`M120,${y} Q133,${y - 6} 150,${y} T182,${y}`} stroke={PALE} strokeWidth="5" fill="none" strokeLinecap="round" />;
      case "frownSmall": return <path d={`M122,${y + 3} Q150,${y - 7} 178,${y + 3}`} stroke={PALE} strokeWidth="5" fill="none" strokeLinecap="round" />;
      case "grin":       return <path d={`M114,${y - 6} Q150,${y + 24} 186,${y - 6} Q150,${y + 6} 114,${y - 6} Z`} fill={PALE} />;
      case "openSmall":  return <ellipse cx="150" cy={y + 1} rx="12" ry={9 + flutter * 5} fill={PALE} opacity="0.92" />;
      case "openTense":  return <ellipse cx="150" cy={y + 1} rx="15" ry={13 + flutter * 5} fill={PALE} opacity="0.92" />;
      default:           return <path d={`M122,${y} Q150,${y + 7} 178,${y}`} stroke={PALE} strokeWidth="5" fill="none" strokeLinecap="round" />;
    }
  })();

  const Eye = ({ cx }) => {
    if (happyEyes) {
      // upward happy arc
      return <path d={`M${cx - 17},${ey + 3} Q${cx},${ey - 12} ${cx + 17},${ey + 3}`} stroke={PALE} strokeWidth="5" fill="none" strokeLinecap="round" />;
    }
    return (
      <g>
        <ellipse cx={cx} cy={ey} rx={19} ry={14 * eyeOpen} fill={PALE} />
        <circle cx={cx + p.pupilX} cy={ey + p.pupilY} r={pupilR} fill={INK} />
        <circle cx={cx + p.pupilX - 2} cy={ey + p.pupilY - 2.5} r={1.7} fill={PALE} />
      </g>
    );
  };

  const Brow = ({ cx, mirror }) => {
    const ang = (mirror ? -1 : 1) * p.browAng;
    return (
      <g transform={`translate(${cx} ${browBase + p.browY}) rotate(${ang})`}>
        <rect x={-18} y={-3} width={36} height={5.5} rx={3} fill={PALE} />
      </g>
    );
  };

  return (
    <g>
      {/* face disc, tinted by disposition */}
      <circle cx="150" cy="158" r="96" fill={p.tint} opacity="0.16" />
      <circle cx="150" cy="158" r="96" fill="none" stroke={p.tint} strokeWidth="2.5" opacity="0.9" />
      <Brow cx={lx} mirror={false} />
      <Brow cx={rx} mirror={true} />
      <Eye cx={lx} />
      <Eye cx={rx} />
      {mouth}
    </g>
  );
}

// ---- J-space readout strip ----------------------------------------
function JSpace({ tokens, entropy, tint }) {
  return (
    <div style={{ background: PANEL2, border: `1px solid ${PANEL}`, borderRadius: 10, padding: "12px 14px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 10 }}>
        <span style={{ fontSize: 10, letterSpacing: 2, color: MUTE, fontFamily: "ui-monospace, Menlo, monospace" }}>
          J-SPACE · LIVE CONCEPT READOUT
        </span>
        <span style={{ fontSize: 10, color: MUTE, fontFamily: "ui-monospace, Menlo, monospace" }}>mid-layer</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
        {tokens.map((tok, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontFamily: "ui-monospace, Menlo, monospace", fontSize: 13, color: PALE, minWidth: 92 }}>
              {tok.t}
            </span>
            <div style={{ flex: 1, height: 7, background: "#0A1C24", borderRadius: 4, overflow: "hidden" }}>
              <div style={{ width: `${tok.w * 100}%`, height: "100%", background: tint, borderRadius: 4, transition: "width .45s ease" }} />
            </div>
            <span style={{ fontFamily: "ui-monospace, Menlo, monospace", fontSize: 11, color: MUTE, minWidth: 30, textAlign: "right" }}>
              {tok.w.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
      {/* entropy gauge */}
      <div style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontFamily: "ui-monospace, Menlo, monospace", fontSize: 11, color: MUTE, minWidth: 92 }}>
          entropy
        </span>
        <div style={{ flex: 1, height: 7, background: "#0A1C24", borderRadius: 4, overflow: "hidden", position: "relative" }}>
          <div style={{ width: `${entropy * 100}%`, height: "100%", background: `linear-gradient(90deg, ${BRASS}, #E8674D)`, borderRadius: 4, transition: "width .45s ease" }} />
        </div>
        <span style={{ fontFamily: "ui-monospace, Menlo, monospace", fontSize: 11, color: MUTE, minWidth: 30, textAlign: "right" }}>
          {entropy.toFixed(2)}
        </span>
      </div>
    </div>
  );
}

function DispositionLens() {
  const [targetKey, setTargetKey] = useState("idle");
  const [answer, setAnswer] = useState(STATES.idle ? "Ready. Ask me about the field service manual." : "");
  const [tokens, setTokens] = useState(STATES.idle.tokens);
  const [entropy, setEntropy] = useState(STATES.idle.entropy);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [voiceOn, setVoiceOn] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [reeling, setReeling] = useState(false);
  const [modelKey, setModelKey] = useState("apertus");
  const audioRef = useRef(null);

  const reduceMotion = useRef(false);
  useEffect(() => {
    reduceMotion.current = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }, []);

  // animated (tweened) face params
  const target = STATES[targetKey];
  const cur = useRef({ ...STATES.idle, tint: STATES.idle.tint });
  const [render, setRender] = useState({ ...STATES.idle, bob: 0, speakPhase: 0 });
  const [blink, setBlink] = useState(false);
  const tRef = useRef(0);

  // continuous animation loop
  useEffect(() => {
    let raf;
    const loop = () => {
      tRef.current += 0.016;
      const c = cur.current;
      const k = reduceMotion.current ? 1 : 0.14;
      c.browY = lerp(c.browY, target.browY, k);
      c.browAng = lerp(c.browAng, target.browAng, k);
      c.eyeOpen = lerp(c.eyeOpen, target.eyeOpen, k);
      c.pupilX = lerp(c.pupilX, target.pupilX, k);
      c.pupilY = lerp(c.pupilY, target.pupilY, k);
      c._mix = lerp(c._mix || 0, 1, k);
      c.tint = lerpColor(c._fromTint || target.tint, target.tint, c._mix);
      const bob = reduceMotion.current ? 0 : Math.sin(tRef.current * 1.6) * 2.2;
      const speakPhase = speaking ? (Math.sin(tRef.current * 22) + 1) / 2 : 0;
      setRender({ ...c, mouth: target.mouth, bob, speakPhase });
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [target, speaking]);

  // when target changes, capture the tween origin color
  useEffect(() => {
    cur.current._fromTint = cur.current.tint;
    cur.current._mix = 0;
  }, [targetKey]);

  // idle blink
  useEffect(() => {
    let alive = true;
    const tick = () => {
      if (!alive) return;
      setBlink(true);
      setTimeout(() => setBlink(false), 130);
      setTimeout(tick, 2200 + Math.random() * 2600);
    };
    const id = setTimeout(tick, 1500);
    return () => { alive = false; clearTimeout(id); };
  }, []);

  const stopVoice = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
      audioRef.current = null;
    }
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setSpeaking(false);
  }, []);

  const speak = useCallback(async (text, dispositionKey) => {
    if (!voiceOn || !text || typeof window === "undefined") return;
    const apiHost = window.DISPOSITION_API_URL || "http://localhost:8000";
    stopVoice();
    try {
      await new Promise((resolve) => setTimeout(resolve, 300));
      const res = await fetch(`${apiHost}/voice`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text,
          disposition: dispositionKey,
          voice_id: window.ELEVENLABS_VOICE_ID || undefined,
        }),
      });
      if (!res.ok) throw new Error(`Voice HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onplay = () => setSpeaking(true);
      audio.onended = () => {
        URL.revokeObjectURL(url);
        setSpeaking(false);
      };
      audio.onerror = () => {
        URL.revokeObjectURL(url);
        setSpeaking(false);
      };
      await audio.play();
    } catch (e) {
      setSpeaking(false);
    }
  }, [voiceOn, stopVoice]);

  const applyState = useCallback((key, ans, extra) => {
    setTargetKey(key);
    setTokens((extra && extra.tokens) || STATES[key].tokens);
    setEntropy((extra && typeof extra.entropy === "number") ? extra.entropy : STATES[key].entropy);
    if (typeof ans === "string") setAnswer(ans);
    if (ans) speak(ans, key);
  }, [speak]);

  // ---- live ask (Mac Mini J-lens /infer service) -------------------
  // >>> HOOK: Connected to Mac Mini J-lens service returning
  //     {answer, disposition, tokens, entropy}
  const ask = useCallback(async () => {
    const q = question.trim();
    if (!q || loading) return;
    setLoading(true);
    setTargetKey("curious");
    setAnswer("…");
    try {
      const apiHost = (typeof window !== "undefined" && window.DISPOSITION_API_URL) || "http://localhost:8000";
      const res = await fetch(`${apiHost}/infer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, model: modelKey }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const parsed = await res.json();
      if (parsed && parsed.disposition && KEYS.includes(parsed.disposition)) {
        applyState(parsed.disposition, parsed.answer || "(no answer)", {
          tokens: Array.isArray(parsed.tokens) && parsed.tokens.length ? parsed.tokens.slice(0, 3) : STATES[parsed.disposition].tokens,
          entropy: typeof parsed.entropy === "number" ? Math.max(0, Math.min(1, parsed.entropy)) : STATES[parsed.disposition].entropy,
        });
      } else {
        const key = keywordFallback(q, (parsed && parsed.answer) || "");
        applyState(key, (parsed && parsed.answer) || "(couldn't parse a clean answer)");
      }
    } catch (e) {
      const key = keywordFallback(q, "");
      applyState(key, "Offline — running on the fallback classifier.");
    } finally {
      setLoading(false);
    }
  }, [question, loading, applyState, modelKey]);

  // ---- demo reel ------------------------------------------------
  const reelRef = useRef(null);
  const runReel = useCallback(() => {
    if (reeling) {
      setReeling(false);
      if (reelRef.current) clearTimeout(reelRef.current);
      stopVoice();
      return;
    }
    setReeling(true);
    let i = 0;
    const step = () => {
      const s = REEL[i % REEL.length];
      setQuestion(s.q);
      applyState(s.key, s.a);
      i += 1;
      reelRef.current = setTimeout(step, 3400);
    };
    step();
  }, [reeling, applyState, stopVoice]);
  useEffect(() => () => { if (reelRef.current) clearTimeout(reelRef.current); }, []);

  const label = STATES[targetKey].label;

  return (
    <div style={{ background: INK, minHeight: "100%", padding: 20, fontFamily: "system-ui, -apple-system, sans-serif" }}>
      <div style={{ maxWidth: 440, margin: "0 auto" }}>
        {/* eyebrow */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 14 }}>
          <span style={{ fontSize: 11, letterSpacing: 3, color: BRASS, fontWeight: 700 }}>SOVEREIGN&nbsp;MIND</span>
          <span style={{ fontSize: 10, letterSpacing: 2, color: MUTE }}>DISPOSITION LENS</span>
        </div>

        {/* porthole */}
        <div style={{ position: "relative", width: "100%", aspectRatio: "1 / 1", marginBottom: 14 }}>
          <svg viewBox="0 0 300 300" width="100%" height="100%" style={{ display: "block" }}>
            <defs>
              <radialGradient id="glass" cx="50%" cy="42%" r="65%">
                <stop offset="0%" stopColor={PANEL} />
                <stop offset="100%" stopColor={PANEL2} />
              </radialGradient>
              <linearGradient id="brass" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor={BRASS_HI} />
                <stop offset="50%" stopColor={BRASS} />
                <stop offset="100%" stopColor="#8A6E2E" />
              </linearGradient>
            </defs>
            {/* brass ring + rivets */}
            <circle cx="150" cy="150" r="146" fill="url(#brass)" />
            <circle cx="150" cy="150" r="130" fill="url(#glass)" />
            {Array.from({ length: 12 }).map((_, i) => {
              const a = (i / 12) * Math.PI * 2;
              return <circle key={i} cx={150 + Math.cos(a) * 138} cy={150 + Math.sin(a) * 138} r={3.4} fill="#7A6026" />;
            })}
            {/* idle sonar sweep (very subtle) */}
            {!reduceMotion.current && (
              <line x1="150" y1="150" x2="150" y2="30" stroke={render.tint} strokeWidth="2" opacity="0.10"
                style={{ transformOrigin: "150px 150px", animation: "sweep 6s linear infinite" }} />
            )}
            {/* the face, with gentle bob */}
            <g style={{ transform: `translateY(${render.bob}px)` }}>
              <Face p={{ ...render, tint: render.tint }} blink={blink} speak={speaking} />
            </g>
          </svg>
        </div>

        {/* disposition label */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
          <span style={{ width: 12, height: 12, borderRadius: 12, background: render.tint, boxShadow: `0 0 12px ${render.tint}` }} />
          <span style={{ fontSize: 26, fontWeight: 700, color: PALE, letterSpacing: 0.3 }}>{label}</span>
          {speaking && <span style={{ fontSize: 11, color: MUTE, letterSpacing: 1 }}>◗ speaking</span>}
        </div>

        {/* J-space readout */}
        <JSpace tokens={tokens} entropy={entropy} tint={render.tint} />

        {/* answer */}
        <div style={{ background: PANEL2, border: `1px solid ${PANEL}`, borderRadius: 10, padding: "12px 14px", marginTop: 12, minHeight: 56 }}>
          <div style={{ fontSize: 10, letterSpacing: 2, color: MUTE, marginBottom: 6, fontFamily: "ui-monospace, Menlo, monospace" }}>SPOKEN OUTPUT</div>
          <div style={{ fontSize: 15, lineHeight: 1.5, color: PALE }}>{loading ? "…" : answer}</div>
        </div>

        {/* input */}
        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ask()}
            placeholder="Ask the assistant…"
            style={{ flex: 1, background: PANEL2, border: `1px solid ${PANEL}`, borderRadius: 8, padding: "11px 13px", color: PALE, fontSize: 14, outline: "none" }}
          />
          <button
            onClick={ask}
            disabled={loading}
            style={{ background: BRASS, color: INK, border: "none", borderRadius: 8, padding: "0 18px", fontWeight: 700, fontSize: 14, cursor: "pointer", opacity: loading ? 0.6 : 1 }}
          >
            {loading ? "…" : "Ask"}
          </button>
        </div>

        {/* controls */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginTop: 10 }}>
          {MODELS.map((option) => (
            <button
              key={option.key}
              onClick={() => setModelKey(option.key)}
              style={{ background: modelKey === option.key ? "#2A4048" : "transparent", color: PALE, border: `1px solid ${modelKey === option.key ? BRASS : PANEL}`, borderRadius: 8, padding: "9px 0", fontSize: 13, cursor: "pointer" }}
            >
              {option.label}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
          <button
            onClick={runReel}
            style={{ flex: 1, background: reeling ? "#2A4048" : "transparent", color: PALE, border: `1px solid ${PANEL}`, borderRadius: 8, padding: "9px 0", fontSize: 13, cursor: "pointer" }}
          >
            {reeling ? "Stop demo reel" : "Demo reel"}
          </button>
          <button
            onClick={() => { setVoiceOn((v) => !v); if (voiceOn) stopVoice(); }}
            style={{ flex: 1, background: voiceOn ? "#2A4048" : "transparent", color: PALE, border: `1px solid ${PANEL}`, borderRadius: 8, padding: "9px 0", fontSize: 13, cursor: "pointer" }}
          >
            {voiceOn ? "Voice on · ElevenLabs" : "Voice off"}
          </button>
        </div>

        {/* provenance footer */}
        <p style={{ fontSize: 11, color: MUTE, lineHeight: 1.5, marginTop: 14 }}>
          Live signal: disposition + J-space tokens come from the Mac Mini /infer service when reachable; Demo reel is canned for capture.
          Model: <b style={{ color: "#9DB3B8" }}>{MODELS.find((m) => m.key === modelKey).label}</b>. Voice: <b style={{ color: "#9DB3B8" }}>ElevenLabs</b> when configured.
        </p>
      </div>

      <style>{`
        @keyframes sweep { from { transform: rotate(0deg);} to { transform: rotate(360deg);} }
        @media (prefers-reduced-motion: reduce) { * { animation: none !important; } }
      `}</style>
    </div>
  );
}

window.DispositionLens = DispositionLens;
