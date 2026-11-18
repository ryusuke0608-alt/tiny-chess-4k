import json, os
from urllib.request import Request, urlopen
V = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 950, "K": 0}
HMG = [
[0,0,0,0,5,10,10,-20,5,-5,-10,0,0,0,0,20,5,5,10,25,10,10,20,30,50,50,50,50,0,0,0,0],
[-50,-40,-30,-30,-40,-20,0,5,-30,5,10,15,-30,0,15,20,-30,5,15,20,-30,0,10,15,-40,-20,0,0,-50,-40,-30,-30],
[-20,-10,-10,-10,-10,5,0,0,-10,10,10,10,-10,0,10,10,-10,5,5,10,-10,0,5,10,-10,0,0,0,-20,-10,-10,-10],
[0,0,0,5,-5,0,0,0,-5,0,0,0,-5,0,0,0,-5,0,0,0,-5,0,0,0,5,10,10,10,0,0,0,0],
[-20,-10,-10,-5,-10,0,5,0,-10,5,5,10,0,0,10,10,0,0,10,10,0,0,5,10,-10,0,0,0,-20,-10,-10,-5],
[20,30,10,0,20,20,0,0,-10,-20,-20,-20,-20,-30,-30,-40,-30,-40,-40,-50,-30,-40,-40,-50,-30,-40,-40,-50,20,30,10,0]
]
HEG = [
[0,0,0,0,-10,5,5,5,-10,5,10,10,-10,5,10,15,0,5,10,15,5,10,15,20,20,25,25,25,0,0,0,0],
[-30,-20,-20,-20,-20,-10,-10,-10,-10,-10,-15,-15,-10,-15,-20,-25,-10,-15,-20,-25,-10,-15,-20,-25,-10,-10,-15,-15,-30,-20,-20,-20]
]
PMG = [[t[r * 4 + min(f, 7 - f)] for r in range(8) for f in range(8)] for t in HMG]
PEG = [[t[r * 4 + min(f, 7 - f)] for r in range(8) for f in range(8)] for t in HEG]
PST = {"P": PMG[0], "N": PMG[1], "B": PMG[2], "R": PMG[3], "Q": PMG[4], "K": PMG[5]}
PSE = {"P": PEG[0], "N": PMG[1], "B": PMG[2], "R": PMG[3], "Q": PMG[4], "K": PEG[1]}
# VMG/VE[piece][square120]: signed value of that piece on that square, from
# the side-to-move point of view (lowercase uses the mirrored square).
FLIP = [(11 - s // 10) * 10 + s % 10 for s in range(120)]
VMG = {}; VE = {}
for _ch in "PNBRQK":
    _t = [0] * 120; _e = [0] * 120
    for _r in range(8):
        for _f in range(8):
            _sq = (9 - _r) * 10 + _f + 1
            _t[_sq] = V[_ch] + PST[_ch][_r * 8 + _f]
            _e[_sq] = V[_ch] + PSE[_ch][_r * 8 + _f]
    VMG[_ch] = _t; VE[_ch] = _e
    VMG[_ch.lower()] = [-VMG[_ch][FLIP[s]] for s in range(120)]
    VE[_ch.lower()] = [-VE[_ch][FLIP[s]] for s in range(120)]
PHW = {"P": 0, "N": 1, "B": 1, "R": 2, "Q": 4, "K": 0}
DIRS = {"P": (), "N": (-19, -21, -8, -12, 8, 12, 19, 21), "B": (-9, -11, 9, 11),
        "R": (-10, -1, 1, 10), "Q": (-9, -11, -10, -1, 1, 9, 10, 11)}
DIRS["K"] = DIRS["Q"]
SWAP = str.maketrans("PNBRQKpnbrqk", "pnbrqkPNBRQK")
def rot(b):
    return "".join(b[i:i + 10] for i in range(110, -1, -10)).translate(SWAP)
ROTC = [((c & 4) >> 2) | ((c & 8) >> 2) | ((c & 1) << 2) | ((c & 2) << 2) for c in range(16)]
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# Position = (b, mg, eg, phase, castling, ep, king_pos, halfmove).
# castling bits: 1/2 = side-to-move west/east rook, 4/8 = foe west/east rook.

def fen(s):
    parts = s.split(); rows = parts[0].split("/")
    b = [" "] * 120
    for ri, row in enumerate(rows):
        f = 0
        for ch in row:
            if ch.isdigit(): f += int(ch)
            else: b[(ri + 2) * 10 + f + 1] = ch; f += 1
    for r in range(2, 10):
        for f in range(1, 9):
            if b[r * 10 + f] == " ": b[r * 10 + f] = "."
    b = "".join(b)
    black = len(parts) > 1 and parts[1] == "b"
    c = parts[2] if len(parts) > 2 else "-"
    ca = (1 if "Q" in c else 0) | (2 if "K" in c else 0) | (4 if "q" in c else 0) | (8 if "k" in c else 0)
    e = parts[3] if len(parts) > 3 else "-"
    ep = -1 if e == "-" else (10 - int(e[1])) * 10 + (ord(e[0]) - 96)
    half = int(parts[4]) if len(parts) > 4 else 0
    mg = eg = ph = 0
    for sq in range(120):
        ch = b[sq]
        if ch in VMG:
            mg += VMG[ch][sq]; eg += VE[ch][sq]; ph += PHW[ch.upper()]
    kp = b.index("K")
    if black:
        b = rot(b)
        mg, eg = -mg, -eg
        ca = ROTC[ca]
        if ep >= 0: ep = FLIP[ep]
        kp = b.index("K")
    return (b, mg, eg, ph, ca, ep, kp, half)

def att(b, sq, upper):
    if upper:
        paw, kni, kg, bis, rok, que = "P", "N", "K", "B", "R", "Q"
        pd = (9, 11)
    else:
        paw, kni, kg, bis, rok, que = "p", "n", "k", "b", "r", "q"
        pd = (-9, -11)
    for d in pd:
        if b[sq + d] == paw: return True
    for dirs, pc2 in ((DIRS["N"], kni), (DIRS["K"], kg)):
        for d in dirs:
            if b[sq + d] == pc2: return True
    for dirs, a, b2 in ((DIRS["B"], bis, que), (DIRS["R"], rok, que)):
        for d in dirs:
            s = sq + d
            while b[s] == ".":
                s += d
            if b[s] == a or b[s] == b2: return True
    return False

def gen(pos, co=False):
    b, mg, eg, ph, ca, ep, kp, half = pos
    moves = []
    ap = moves.append
    for i in range(21, 99):
        pc = b[i]
        if not ("A" <= pc <= "Z"): continue
        if pc == "P":
            for d in (-9, -11):
                j = i + d; t = b[j]
                if ("a" <= t <= "z") or j == ep:
                    if j < 29:
                        for pr in (5, 4, 3, 2): ap(i | (j << 7) | (pr << 14))
                    else: ap(i | (j << 7))
            j = i - 10
            if b[j] == ".":
                if j < 29:
                    for pr in (5, 4, 3, 2): ap(i | (j << 7) | (pr << 14))
                elif not co:
                    ap(i | (j << 7))
                    if i > 80 and b[i - 20] == ".": ap(i | ((i - 20) << 7))
        elif pc == "N" or pc == "K":
            for d in DIRS[pc]:
                j = i + d; t = b[j]
                if t == ".":
                    if not co: ap(i | (j << 7))
                elif "a" <= t <= "z": ap(i | (j << 7))
            if pc == "K" and not co and i == 95:
                for bit, rf, kt, emp, safe in ((2, 98, 97, (96, 97), (95, 96, 97)), (1, 91, 93, (92, 93, 94), (93, 94, 95))):
                    if ca & bit and b[rf] == "R" and all(b[s] == "." for s in emp) \
                            and all(not att(b, s, False) for s in safe):
                        ap(95 | (kt << 7))
        else:
            for d in DIRS[pc]:
                j = i + d
                while b[j] == ".":
                    if not co: ap(i | (j << 7))
                    j += d
                if "a" <= b[j] <= "z": ap(i | (j << 7))
    return moves

def move(pos, m):
    b, mg, eg, ph, ca, ep, kp, half = pos
    i = m & 127; j = (m >> 7) & 127; promo = (m >> 14) & 7
    pc = b[i]; cap = b[j]
    b = list(b)
    b[i] = "."
    nep = -1
    if pc == "P" and j == ep and cap == ".":
        b[j + 10] = "."
        mg -= VMG["p"][j + 10]; eg -= VE["p"][j + 10]
    if pc == "P" and i - j == 20: nep = i - 10
    if cap != ".":
        mg -= VMG[cap][j]; eg -= VE[cap][j]; ph -= PHW[cap.upper()]
    if cap != "." or pc == "P": half = 0
    else: half += 1
    mg += VMG[pc][j] - VMG[pc][i]; eg += VE[pc][j] - VE[pc][i]
    if promo:
        nch = "NBRQ"[promo - 2]
        b[j] = nch
        mg += VMG[nch][j] - VMG["P"][j]; eg += VE[nch][j] - VE["P"][j]
        ph += PHW[nch]
    else:
        b[j] = pc
    if pc == "K":
        if abs(j - i) == 2:
            rf = 98 if j > i else 91; rt = (i + j) // 2
            b[rt] = "R"; b[rf] = "."; mg += VMG["R"][rt] - VMG["R"][rf]; eg += VE["R"][rt] - VE["R"][rf]
        ca &= ~3
    if i == 91 or j == 91: ca &= ~1
    if i == 98 or j == 98: ca &= ~2
    if i == 21 or j == 21: ca &= ~4
    if i == 28 or j == 28: ca &= ~8
    nb = rot("".join(b))
    return (nb, -mg, -eg, ph, ROTC[ca], FLIP[nep] if nep >= 0 else -1, nb.index("K"), half)

def ev(pos):
    b, mg, eg, ph, ca, ep, kp, half = pos
    return (mg * ph + eg * (24 - ph)) // 24

INF = 100000; MATE = 90000
TT = {}
rep = set()
nodes = 0
NCAP = 140000

def order(pos, moves, tm):
    b = pos[0]
    def key(m):
        if m == tm: return 10000000
        i = m & 127; j = (m >> 7) & 127
        s = VMG[b[i]][j] - VMG[b[i]][i]
        cap = b[j]
        if cap != ".": s += -VMG[cap][j] + 500
        if m >> 14: s += 800
        return s
    return sorted(moves, key=key, reverse=True)

def qs(pos, alpha, beta, ply):
    global nodes
    nodes += 1
    stand = ev(pos)
    if nodes >= NCAP: return stand
    if stand >= beta: return beta
    if stand > alpha: alpha = stand
    b = pos[0]
    for m in order(pos, gen(pos, True), 0):
        cap = b[(m >> 7) & 127]
        if cap != "." and stand + V[cap.upper()] + 200 < alpha and not (m >> 14): continue
        child = move(pos, m)
        if att(child[0], child[0].index("k"), True): continue
        sc = -qs(child, -beta, -alpha, ply + 1)
        if sc >= beta: return beta
        if sc > alpha: alpha = sc
    return alpha

def search(pos, depth, alpha, beta, ply, nk):
    global nodes
    if depth <= 0: return qs(pos, alpha, beta, ply)
    nodes += 1
    if nodes >= NCAP: raise TimeoutError
    b = pos[0]
    if ply > 0:
        if pos[7] >= 100: return 0
        if (b, pos[4], pos[5]) in rep: return 0
    a0 = alpha; tm = 0
    ent = TT.get((b, pos[4], pos[5]))
    if ent is not None:
        ed, es, ef, em = ent
        if ed >= depth:
            if ef == 0: return es
            if ef == 1 and es > alpha: alpha = es
            elif ef == 2 and es < beta: beta = es
            if alpha >= beta: return es
        tm = em
    ic = att(b, pos[6], False)
    if ic: depth += 1
    if nk and not ic and depth >= 3 and beta < MATE - 1000:
        if any(c in b for c in "NBRQ"):
            nb = rot(b)
            child = (nb, -pos[1], -pos[2], pos[3], ROTC[pos[4]], -1, nb.index("K"), pos[7])
            sc = -search(child, depth - 3, -beta, -beta + 1, ply + 1, False)
            if sc >= beta: return beta
    best = -INF; bm = 0; legal = 0
    for idx, m in enumerate(order(pos, gen(pos), tm)):
        child = move(pos, m)
        if att(child[0], child[0].index("k"), True): continue
        legal += 1
        cap = b[(m >> 7) & 127]
        if idx == 0:
            sc = -search(child, depth - 1, -beta, -alpha, ply + 1, True)
        else:
            r = 1 if (depth >= 3 and cap == "." and not (m >> 14) and not ic and idx >= 3) else 0
            sc = -search(child, depth - 1 - r, -alpha - 1, -alpha, ply + 1, True)
            if sc > alpha and r: sc = -search(child, depth - 1, -alpha - 1, -alpha, ply + 1, True)
            if sc > alpha and sc < beta: sc = -search(child, depth - 1, -beta, -alpha, ply + 1, True)
        if sc > best:
            best = sc; bm = m
            if sc > alpha:
                alpha = sc
                if alpha >= beta: break
    if legal == 0:
        return -MATE + ply if ic else 0
    flag = 0 if a0 < best < beta else (1 if best >= beta else 2)
    TT[(b, pos[4], pos[5])] = (depth, best, flag, bm)
    return best

def choose(pos, keys):
    global nodes, rep
    if len(TT) > 600000: TT.clear()
    rep = set(keys)
    legal = []
    for m in gen(pos):
        child = move(pos, m)
        if att(child[0], child[0].index("k"), True): continue
        legal.append(m)
    if not legal: return None
    if len(legal) == 1: return legal[0]
    nodes = 0
    chosen = legal[0]
    depth = 1
    while depth <= 64:
        try:
            cur = chosen; cur_sc = -INF
            for m in order(pos, legal, chosen):
                sc = -search(move(pos, m), depth - 1, -INF, INF, 1, True)
                if sc > cur_sc: cur_sc = sc; cur = m
            chosen = cur
        except TimeoutError:
            break
        if nodes >= NCAP: break
        depth += 1
    return chosen

def move_uci(m, rotated):
    i = m & 127; j = (m >> 7) & 127
    if rotated: i = FLIP[i]; j = FLIP[j]
    def n(s): return "abcdefgh"[s % 10 - 1] + str(10 - s // 10)
    s = n(i) + n(j)
    if m >> 14: s += "nbrq"[[2, 3, 4, 5].index(m >> 14)]
    return s
def uci_move(u, rot):
    def sq(x):
        s = (10 - int(x[1])) * 10 + (ord(x[0]) - 96)
        return FLIP[s] if rot else s
    f = sq(u[:2]); t = sq(u[2:4])
    pr = {"n": 2, "b": 3, "r": 4, "q": 5}[u[4]] if len(u) > 4 else 0
    return f | (t << 7) | (pr << 14)

def post(url, path, body):
    req = Request(url + path, data=json.dumps(body).encode(), headers={"content-type": "application/json"})
    with urlopen(req) as res:
        return json.loads(res.read())

def play():
    url = os.environ["MAKEFUN_ENV_URL"]
    while True:
        g = post(url, "/game", {})
        if g.get("status") == "done": return
        pos = fen(g["fen"])
        q = fen(START); keys = [(q[0], q[4], q[5])]; r = False
        for u in g["moves"]:
            q = move(q, uci_move(u, r)); r = not r
            keys.append((q[0], q[4], q[5]))
        m = choose(pos, keys)
        if m is None:
            post(url, "/resign", {"game": g["game"]}); continue
        post(url, "/move", {"game": g["game"], "move": move_uci(m, g["fen"].split()[1] == "b")})

if os.environ.get("MAKEFUN_ENV_URL"):
    play()
