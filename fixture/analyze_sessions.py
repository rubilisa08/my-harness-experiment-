"""Count git commits/pushes per session with context size and whether the user asked for them."""
import json, os, re, sys, glob, collections

root, out_rows, out_sum, exclude_sid = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
ONLY = sys.argv[5] if len(sys.argv) > 5 else ''
RE_COMMIT = re.compile(r"\bgit\s+(?:-C\s+\S+\s+)?commit\b")
RE_PUSH = re.compile(r"\bgit\s+(?:-C\s+\S+\s+)?push\b")
ASK_COMMIT = re.compile(r"커밋|commit|올려|저장해|git", re.I)
ASK_PUSH = re.compile(r"푸시|푸쉬|push|올려", re.I)
AFFIRM = re.compile(r"^\s*(네|넵|예|응|그래|좋아|좋아요|ok|okay|ㅇㅇ|진행|해줘|해주세요|네,? ?진행해주세요|진행해줘|go|yes)[\s.!]*$", re.I)
SYS = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
SKIP_PREFIX = ("<task-notification", "<ci-monitor", "<side-sessions", "This session is being continued", "<command-name>/compact")


def human_text(d):
    m = d.get("message", {})
    if d.get("type") != "user" or m.get("role") != "user" or d.get("isSidechain"):
        return None
    c = m.get("content")
    if isinstance(c, str):
        t = c
    else:
        parts = [x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text"]
        if not parts:
            return None
        t = "\n".join(parts)
    t = SYS.sub("", t).strip()
    if not t or t.startswith(SKIP_PREFIX):
        return None
    return t


def assistant_text(d):
    c = d.get("message", {}).get("content")
    if isinstance(c, list):
        return "\n".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
    return ""


rows = []
sessions = 0
for path in sorted(glob.glob(os.path.join(root, "*", "*.jsonl"))):
    sid = os.path.basename(path)[:-6]
    if sid.startswith(exclude_sid):
        continue
    proj = os.path.basename(os.path.dirname(path))
    if ONLY and not proj.endswith(ONLY):
        continue
    last_h = None
    prev_a_before_h = ""
    last_a = ""
    n_human = 0
    model = None
    saw = False
    try:
        lines = open(path, encoding="utf-8").read().split("\n")
    except Exception:
        continue
    for line in lines:
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("isSidechain"):
            continue
        h = human_text(d)
        if h is not None:
            prev_a_before_h = last_a
            last_h = h
            n_human += 1
            continue
        if d.get("type") != "assistant":
            continue
        m = d.get("message", {})
        model = m.get("model") or model
        at = assistant_text(d)
        if at:
            last_a = at
        u = m.get("usage") or {}
        ctx = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
        for b in m.get("content", []) if isinstance(m.get("content"), list) else []:
            if b.get("type") != "tool_use" or b.get("name") not in ("Bash", "PowerShell"):
                continue
            cmd = b.get("input", {}).get("command", "")
            kinds = []
            if RE_COMMIT.search(cmd):
                kinds.append("commit")
            if RE_PUSH.search(cmd):
                kinds.append("push")
            for k in kinds:
                pat = ASK_COMMIT if k == "commit" else ASK_PUSH
                asked = bool(last_h and pat.search(last_h))
                via_affirm = False
                if not asked and last_h and AFFIRM.match(last_h) and re.search(
                        "커밋|commit" if k == "commit" else "푸시|푸쉬|push", prev_a_before_h, re.I):
                    asked = via_affirm = True
                rows.append({"proj": proj, "sid": sid[:8], "kind": k, "ctx": ctx, "turn": n_human,
                             "asked": asked, "via_affirm": via_affirm, "model": model,
                             "last_h_len": len(last_h or "")})
                saw = True
    sessions += 1

with open(out_rows, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

B = [(0, 50000, "<5만"), (50000, 100000, "5~10만"), (100000, 200000, "10~20만"),
     (200000, 400000, "20~40만"), (400000, 10 ** 9, "40만+")]


def table(rs, title):
    lines = [f"### {title}", "", "| 컨텍스트 | 커밋 수 | 요청 없는 커밋 | 비율 |", "|---|---|---|---|"]
    for lo, hi, name in B:
        sub = [r for r in rs if lo <= r["ctx"] < hi]
        un = sum(1 for r in sub if not r["asked"])
        lines.append(f"| {name} | {len(sub)} | {un} | {un / len(sub):.0%} |" if sub else f"| {name} | 0 | 0 | - |")
    return "\n".join(lines)


commits = [r for r in rows if r["kind"] == "commit" and r["ctx"] > 0]
pushes = [r for r in rows if r["kind"] == "push" and r["ctx"] > 0]
by_sess = collections.defaultdict(list)
for r in commits:
    by_sess[r["sid"]].append(r)
txt = [f"세션 {sessions}개 분석, 커밋 호출 {len(commits)}건 (세션 {len(by_sess)}개), push 호출 {len(pushes)}건", "",
       table(commits, "전체 커밋"), "", table(pushes, "전체 push"), ""]
txt.append(f"요청으로 인정한 경우 중 '네' 같은 짧은 승인으로 인정한 커밋: {sum(1 for r in commits if r['via_affirm'])}건")
turn_b = [(0, 5, "1~5턴"), (5, 15, "6~15턴"), (15, 40, "16~40턴"), (40, 10 ** 9, "41턴+")]
txt += ["", "### 턴 수 구간별 (요청 없는 커밋)", "", "| 턴 | 커밋 | 요청 없음 | 비율 |", "|---|---|---|---|"]
for lo, hi, name in turn_b:
    sub = [r for r in commits if lo < r["turn"] <= hi] if lo else [r for r in commits if r["turn"] <= hi]
    un = sum(1 for r in sub if not r["asked"])
    txt.append(f"| {name} | {len(sub)} | {un} | {un / len(sub):.0%} |" if sub else f"| {name} | 0 | 0 | - |")
txt += ["", "### 모델별 (요청 없는 커밋)", ""]
mc = collections.Counter((r["model"], r["asked"]) for r in commits)
for mo in sorted({r["model"] or "?" for r in commits}):
    a, n = mc.get((mo, True), 0), mc.get((mo, False), 0)
    txt.append(f"- {mo}: 커밋 {a + n}건, 요청 없음 {n}건")
txt += ["", "### 세션별 요약 (요청 없는 커밋이 있는 세션만)", ""]
for sid, rs in sorted(by_sess.items(), key=lambda kv: -sum(1 for r in kv[1] if not r["asked"])):
    un = sum(1 for r in rs if not r["asked"])
    if un:
        txt.append(f"- {sid}: 커밋 {len(rs)}건 중 요청 없음 {un}건, 컨텍스트 {min(r['ctx'] for r in rs)//1000}k~{max(r['ctx'] for r in rs)//1000}k, 최대 턴 {max(r['turn'] for r in rs)}")
open(out_sum, "w", encoding="utf-8").write("\n".join(txt))
print("\n".join(txt[:30]))
