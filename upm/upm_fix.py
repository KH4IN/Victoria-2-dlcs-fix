"""Corrige UPM directamente en su carpeta. Debe partir de UPM sin tocar, en una copia del juego base ya corregido.

Uso: python -I upm_fix.py <carpeta mod/UPM> <juego_base_corregido> <registro.txt>
"""
import collections
import glob
import os
import re
import shutil
import struct
import sys
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'juego-base'))
from textos import FULL, PARTS, SHORT, SPANISH, limpiar  # noqa: E402

dst, game, logpath = sys.argv[1:4]
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
log = collections.defaultdict(list)


def note(cat, msg):
    log[cat].append(msg)


def rb(p):
    with open(p, 'rb') as f:
        return f.read()


def wb(p, data):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(data)


def L(p):
    return rb(p).decode('latin-1')


def W(p, text):
    wb(p, text.encode('latin-1'))


def D(*a):
    return os.path.join(dst, *a)


def sub_file(p, pattern, repl, cat, flags=0):
    t = L(p)
    t2, n = re.subn(pattern, repl, t, flags=flags)
    if n:
        W(p, t2)
        note(cat, f'{os.path.relpath(p, dst)}: {n}')
    return n


if os.path.exists(os.path.join(dst, 'localisation', 'zz_correcciones.csv')):
    sys.exit('Las correcciones ya estan aplicadas en este UPM.')
with open(os.path.join(game, 'common', 'defines.lua'), 'rb') as f:
    if not re.search(rb'REDUCTION_AFTER_RISEING\s*=\s*2\.0', f.read()):
        sys.exit('Primero hay que corregir el juego base con juego-base/base_fix.py.')

# ---- 0. Limpieza de sobrantes ---------------------------------------------------------------
for rel in ('map.zip', 'settings.txt'):
    p = D(rel)
    if os.path.exists(p):
        os.remove(p)
        note('sobrantes', f'eliminado {rel}')

# ---- 1. Bytes NUL y codificacion ------------------------------------------------------------
inv_names = {}
for p in glob.glob(os.path.join(glob.escape(dst), 'inventions', '*.txt')):
    for k in re.findall(r'^([^\s=#]+)\s*=\s*\{', L(p), re.M):
        inv_names[k] = True
accent_keys = [k for k in inv_names if any(ord(c) > 127 for c in k)]


def to_ascii(c):
    n = unicodedata.normalize('NFKD', c)
    return ''.join(x for x in n if ord(x) < 128) or '?'


for dp, dn, fn in os.walk(dst):
    for name in fn:
        if not name.lower().endswith(('.txt', '.gui', '.gfx', '.sfx')):
            continue
        p = os.path.join(dp, name)
        d = rb(p)
        ch = False
        if b'\0' in d:
            d = d.replace(b'\0', b'')
            ch = True
            note('NUL', os.path.relpath(p, dst))
        if re.search(rb'[\x80-\xff]', d):
            try:
                u = d.decode('utf-8')
            except UnicodeDecodeError:
                u = None
            if u is not None:
                for k in accent_keys:
                    pat = re.escape(k)
                    for c in set(x for x in k if ord(x) > 127):
                        pat = pat.replace(re.escape(c), '�').replace(c, '�')
                    u, nn = re.subn(pat, k, u)
                    if nn:
                        note('claves_acento', f'{os.path.relpath(p, dst)}: {k} x{nn}')
                out = []
                for c in u:
                    try:
                        out.append(c.encode('cp1252'))
                    except UnicodeEncodeError:
                        out.append(b'?' if c == '�' else to_ascii(c).encode('ascii', 'replace'))
                d = b''.join(out)
                ch = True
                note('UTF8_a_ANSI', os.path.relpath(p, dst))
        if ch:
            wb(p, d)

# ---- 2. PuppetStates: llave ausente -----------------------------------------------------------
p = D('history', 'diplomacy', 'PuppetStates.txt')
t = L(p)
pat = r'(\tfirst= DAI \r?\n\tsecond= CHA \r?\n\tstart_date= 1803\.1\.1 \r?\n\tend_date= 1835\.1\.1 \r?\n)(\s*\r?\n)(vassal=)'
t2, n = re.subn(pat, lambda m: m.group(1) + '}' + m.group(2) + m.group(3), t, count=1)
assert n == 1, 'PuppetStates no coincide'
W(p, t2)
assert t2.count('{') == t2.count('}'), 'PuppetStates sigue descuadrado'
note('llaves', 'PuppetStates.txt: anadido } en linea 882')

# ---- 3. Tecnologias con prefijo n_ ------------------------------------------------------------
techs = set()
for p in glob.glob(os.path.join(glob.escape(dst), 'technologies', '*.txt')):
    techs |= set(re.findall(r'^(\w+)\s*=\s*\{', L(p), re.M))
OLD = [k[2:] for k in techs if k.startswith('n_') and k[2:] not in techs]
print('tecnologias renombradas por el mod:', len(OLD))
alt = '|'.join(sorted(OLD, key=len, reverse=True))
rx_key = re.compile(r'(?m)^([^#\r\n]*?)(?<![\w"])(' + alt + r')(\s*=\s*(?:\d|yes|no)\b)')
rx_act = re.compile(r'(activate_technology\s*=\s*"?)(' + alt + r')\b')


def fix_tech(t):
    n = 0
    while True:
        t, a = rx_key.subn(lambda m: m.group(1) + 'n_' + m.group(2) + m.group(3), t)
        n += a
        if not a:
            break
    t, b = rx_act.subn(lambda m: m.group(1) + 'n_' + m.group(2), t)
    return t, n + b


for z in ('history/countries', 'events', 'decisions', 'inventions', 'technologies', 'common', 'poptypes', 'units'):
    for pth in glob.glob(os.path.join(glob.escape(dst), z, '**', '*.txt'), recursive=True):
        t = L(pth)
        t2, n = fix_tech(t)
        if n:
            W(pth, t2)
            note('tecnologias', f'{os.path.relpath(pth, dst)}: {n}')
# Decisiones del juego base que siguen cargandose y usan los nombres antiguos: se copian al mod ya corregidas.
for pth in glob.glob(os.path.join(glob.escape(game), 'decisions', '*.txt')):
    rel = os.path.basename(pth)
    if not os.path.exists(D('decisions', rel)):
        t2, n = fix_tech(L(pth))
        if n:
            W(D('decisions', rel), t2)
            note('tecnologias', f'decisions/{rel} (copiada del base): {n}')

# ---- 4. Religion y culturas en paises ---------------------------------------------------------
HC = D('history', 'countries')
GOV = {'democrcy': 'democracy', 'bougeois_dictatorship': 'bourgeois_dictatorship'}
for pth in glob.glob(os.path.join(glob.escape(HC), '*.txt')):
    t = L(pth)
    o = t
    t = re.sub(r'\bculture\s*=\s*zzz_religion_shamanist\b', 'culture = zzz_religion_shamanism', t)
    t = re.sub(r'\breligion\s*=\s*shamanist\b', 'religion = shamanism', t)
    t = re.sub(r'\breligion\s*=\s*othodox\b', 'religion = orthodox', t)
    t = re.sub(r'\bculture\s*=\s*nanfranen\b', 'culture = nanfaren', t)
    t = re.sub(r'\bculture\s*=\s*east_asian\b', 'culture = han', t)
    t = re.sub(r'\bculture\s*=\s*syriac\b', 'culture = assyrian', t)
    t = re.sub(r'\bprimary_culture\s*=\s*palestinian\b', 'primary_culture = mashriqi', t)
    t = re.sub(r'(?m)^\s*culture\s*=\s*union\s*\r?\n', '', t)
    for a, b in GOV.items():
        t = re.sub(rf'\bgovernment\s*=\s*{a}\b', f'government = {b}', t)
    t = re.sub(r'\bvote_franschise\s*=\s*population_equal_weight\b', 'vote_franschise = universal_voting', t)
    t = re.sub(r'\bupper_house_composition\s*=\s*proportional_representation\b', 'upper_house_composition = population_equal_weight', t)
    if t != o:
        W(pth, t)
        note('paises', os.path.basename(pth))

# OOB inexistentes
oobs = {}
for base in (game, dst):
    for dp, dn, fn in os.walk(os.path.join(base, 'history', 'units')):
        for n in fn:
            oobs[os.path.relpath(os.path.join(dp, n), os.path.join(base, 'history', 'units')).replace('\\', '/').lower()] = 1
for pth in glob.glob(os.path.join(glob.escape(HC), '*.txt')):
    t = L(pth)
    bad = [m for m in re.finditer(r'(?m)^[ \t]*oob\s*=\s*"?([^"\r\n]+?)"?[ \t]*\r?\n', t) if m.group(1).replace('\\', '/').lower() not in oobs]
    for m in reversed(bad):
        t = t[:m.start()] + t[m.end():]
        note('oob', f'{os.path.basename(pth)}: quitado {m.group(1)}')
    if bad:
        W(pth, t)

# Historia sin etiqueta declarada
p = D('history', 'countries', 'CPA - Champasak.txt')
if os.path.exists(p):
    os.remove(p)
    note('sobrantes', 'history/countries/CPA - Champasak.txt: etiqueta no declarada')

# ---- 5. Pops ----------------------------------------------------------------------------------
CULT = {
    'east_kwa': 'ewe', 'pueblo': 'sonoran', 'kuba': 'luba', 'christian_mashriqi': 'mashriqi', 'nilotic': 'dinka',
    'afro_yankee': 'afro_american', 'cree': 'plains_algonquian', 'circassian': 'north_caucasian', 'circassians': 'north_caucasian',
    'dakota': 'siouan', 'tupinamba': 'tupi', 'buryat': 'mongol', 'viernamese': 'vietnamese', 'lendu': 'luba', 'mixtec': 'zapotec',
    'mordovian': 'ugrian', 'chinese': 'yue', 'kalmyk': 'mongol', 'spehardic': 'sephardic', 'fsouth_italian': 'south_italian',
    'jewish': 'ashkenazi', 'tay': 'thai', 'nanfanen': 'nanfaren', 'lulundaba': 'lunda', 'sikh': 'panjabi', 'kalimatan': 'bornean',
    'bashkir': 'tatar', 'ibad_bedouin': 'bedouin', 'aimat': 'hazara', 'pamir': 'tajik', 'druze': 'mashriqi',
}
REL = {'buddhist': 'mahayana', 'taoism': 'mahayana', 'tengri': 'tengri_pagan_reformed', 'gujarati': 'hindu', 'nanfaren': 'mahayana'}
NOFAITH = {'secularism', 'none'}
valid_rel = set()
depth = 0
for m in re.finditer(r'#[^\n]*|\{|\}|([A-Za-z_0-9\-]+)\s*=\s*\{', L(D('common', 'religion.txt'))):
    x = m.group(0)
    if x.startswith('#'):
        continue
    if x == '{':
        depth += 1
    elif x == '}':
        depth -= 1
    else:
        if depth == 1:
            valid_rel.add(m.group(1))
        depth += 1
rx_cul = re.compile(r'\bculture\s*=\s*"?(' + '|'.join(sorted(CULT, key=len, reverse=True)) + r')\b"?')
rx_rel = re.compile(r'\breligion\s*=\s*"?([\w\-]+)"?')
for pth in glob.glob(os.path.join(glob.escape(dst), 'history', 'pops', '*', '*.txt')):
    t = L(pth)
    t2, nc = rx_cul.subn(lambda m: 'culture = ' + CULT[m.group(1)], t)
    # religion mayoritaria de cada provincia y del archivo, para los pops sin religion valida
    file_cnt = collections.Counter(m.group(1) for m in rx_rel.finditer(t2) if m.group(1) in valid_rel)
    file_top = file_cnt.most_common(1)[0][0] if file_cnt else 'catholic'
    out, last = [], 0
    nr = 0
    for mp in re.finditer(r'(?m)^\s*\d+\s*=\s*\{', t2):
        i, d = mp.end(), 1
        while d and i < len(t2):
            c = t2[i]
            d += (c == '{') - (c == '}')
            i += 1
        block = t2[mp.start():i]
        cnt = collections.Counter(m.group(1) for m in rx_rel.finditer(block) if m.group(1) in valid_rel)
        top = cnt.most_common(1)[0][0] if cnt else file_top

        def r(m):
            global nr
            v = m.group(1)
            if v in valid_rel:
                return m.group(0)
            nr += 1
            return 'religion = ' + REL.get(v, top)

        out.append(t2[last:mp.start()])
        out.append(rx_rel.sub(r, block))
        last = i
    out.append(t2[last:])
    t3 = ''.join(out)
    if nc or nr:
        W(pth, t3)
        note('pops', f'{os.path.relpath(pth, dst)}: culturas {nc}, religiones {nr}')

# ---- 6. Partidos ------------------------------------------------------------------------------
BM = re.findall(r'date\s*=\s*([\d.]+)', L(D('common', 'bookmarks.txt')))


def dk(s):
    return tuple(int(x) for x in s.split('.'))


cty = dict(re.findall(r'(?m)^([A-Z0-9]{3})\s*=\s*"([^"]+)"', L(D('common', 'countries.txt'))))


def party_blocks(t):
    for m in re.finditer(r'\bparty\s*=\s*\{', t):
        i, d = m.end(), 1
        while d and i < len(t):
            d += (t[i] == '{') - (t[i] == '}')
            i += 1
        yield m.start(), i


def pget(b, k):
    m = re.search(rf'\b{k}\s*=\s*"?([\w.\-]+)"?', b)
    return m.group(1) if m else None


hist_by_tag = {}
for pth in glob.glob(os.path.join(glob.escape(HC), '*.txt')):
    m = re.match(r'([A-Za-z0-9]{3})(\b|[ .\-])', os.path.basename(pth))
    if m:
        hist_by_tag[m.group(1).upper()] = pth

n_ext = n_ren = n_start = n_end = 0
for tag, rel in cty.items():
    cp = D('common', rel)
    if not os.path.exists(cp):
        cp = os.path.join(game, 'common', rel)
    t = L(cp)
    # 6a. partidos que caducaban justo en 2000: el juego llega a 2250
    t, a = re.subn(r'(\bend_date\s*=\s*)2000\.1\.1\b', r'\g<1>2300.1.1', t)
    n_ext += a
    parties = {}
    for s, e in party_blocks(t):
        b = t[s:e]
        parties[pget(b, 'name')] = (pget(b, 'ideology'), pget(b, 'start_date') or '1.1.1', pget(b, 'end_date') or '9999.1.1')
    hp = hist_by_tag.get(tag)
    if not hp or not parties:
        if a:
            W(D('common', rel), t)
        continue
    h = L(hp)
    # estado por fecha: (fecha, partido) a partir del nivel superior y bloques fechados
    uses = []
    depth = 0
    cur = '1.1.1'
    tokens = re.finditer(r'#[^\n]*|\{|\}|(\d{1,4}\.\d{1,2}\.\d{1,2})\s*=\s*\{|\bruling_party\s*=\s*"?([\w\-]+)"?', h)
    events = []
    stack = []
    for m in tokens:
        x = m.group(0)
        if x.startswith('#'):
            continue
        if x == '{':
            stack.append(None)
        elif x == '}':
            if stack:
                stack.pop()
            cur = next((s for s in reversed(stack) if s), '1.1.1')
        elif m.group(1):
            stack.append(m.group(1))
            cur = m.group(1)
        else:
            events.append((cur, m.group(2), m.start(2), m.end(2)))
    events.sort(key=lambda e: dk(e[0]))
    need_start, need_end = {}, {}
    replace = {}
    for date in BM:
        rp = None
        for ed, nm, sp, ep in events:
            if dk(ed) <= dk(date):
                rp = (ed, nm, sp, ep)
        if rp is None:
            continue
        ed, nm, sp, ep = rp
        nm2 = replace.get((sp, ep), nm)
        act = lambda n: dk(parties[n][1]) <= dk(date) < dk(parties[n][2])
        if nm2 not in parties:
            suffix = re.sub(r'^[A-Z0-9]{3}_', '', nm2)
            ideo = re.sub(r'_\d+$', '', suffix)
            cands = [n for n, v in parties.items() if v[0] == ideo]
            pick = next((n for n in cands if act(n)), None) or (cands[0] if cands else next((n for n in parties if act(n)), next(iter(parties))))
            replace[(sp, ep)] = pick
            note('partido_nombre', f'{tag} {date}: {nm2} -> {pick}')
            nm2 = pick
        if not act(nm2):
            same = [n for n, v in parties.items() if v[0] == parties[nm2][0] and act(n)]
            if same and (sp, ep) not in replace:
                replace[(sp, ep)] = same[0]
                note('partido_fecha', f'{tag} {date}: {nm2} -> {same[0]}')
            elif dk(date) < dk(parties[nm2][1]):
                need_start[nm2] = min(need_start.get(nm2, '9999.1.1'), date, key=dk)
            else:
                need_end[nm2] = max(need_end.get(nm2, '1.1.1'), date, key=dk)
    if replace:
        for (sp, ep), new in sorted(replace.items(), reverse=True):
            h = h[:sp] + new + h[ep:]
        W(hp, h)
        n_ren += len(replace)
    if need_start or need_end:
        blocks = list(party_blocks(t))
        for s, e in reversed(blocks):
            b = t[s:e]
            nm = pget(b, 'name')
            if nm in need_start:
                b = re.sub(r'(\bstart_date\s*=\s*)[\d.]+', lambda m: m.group(1) + need_start[nm], b, count=1)
                n_start += 1
            if nm in need_end:
                y, mo, da = dk(need_end[nm])
                b = re.sub(r'(\bend_date\s*=\s*)[\d.]+', lambda m: f'{m.group(1)}{y + 1}.{mo}.{da}', b, count=1)
                n_end += 1
            t = t[:s] + b + t[e:]
    if a or need_start or need_end:
        W(D('common', rel), t)
note('partidos', f'caducidad 2000 ampliada a 2300 en {n_ext} partidos; ruling_party corregidos {n_ren}; inicio adelantado {n_start}; fin ampliado {n_end}')

# ---- 7. Eventos duplicados -----------------------------------------------------------------------
p = D('events', 'converterEvents.txt')
t = L(p)
blocks = []
for m in re.finditer(r'\b(country_event|province_event)\s*=\s*\{', t):
    i, d = m.end(), 1
    while d and i < len(t):
        d += (t[i] == '{') - (t[i] == '}')
        i += 1
    mid = re.search(r'\bid\s*=\s*(\d+)', t[m.start():i])
    if mid:
        blocks.append((m.start(), i, mid.group(1)))
first = {}
remove = []
for s, e, i in blocks:
    if i in first:
        remove.append((s, e, i))
        same = t[first[i][0]:first[i][1]] == t[s:e]
        note('eventos', f'{i}: {"copia identica eliminada" if same else "segunda definicion con mismo id eliminada; se conserva la primera"}')
    else:
        first[i] = (s, e)
for s, e, i in reversed(remove):
    t = t[:s] + t[e:]
W(p, t)

# ---- 8. Provincias con doble historia -------------------------------------------------------------
for n in ('1396 - Api.txt', '1397 - Sandakan.txt'):
    a = D('history', 'provinces', 'asia', n)
    b = D('history', 'provinces', 'indonesia', n)
    if os.path.exists(a):
        os.makedirs(os.path.dirname(b), exist_ok=True)
        shutil.move(a, b)
        note('provincias', f'{n}: movida a indonesia/ para sustituir la del base')

# ---- 9. Clima de las provincias nuevas ------------------------------------------------------------
defs = {}
for r in L(D('map', 'definition.csv')).splitlines()[1:]:
    c = r.split(';')
    if c[0].isdigit():
        try:
            defs[tuple(int(re.sub(r'\D', '', x)) for x in c[1:4])] = int(c[0])
        except ValueError:
            pass
raw = rb(D('map', 'provinces.bmp'))
off = struct.unpack('<I', raw[10:14])[0]
w, h_ = struct.unpack('<ii', raw[18:26])
st = (w * 3 + 3) & ~3
new = set(range(3249, 3261))
neigh = collections.defaultdict(collections.Counter)
for y in range(h_):
    row = raw[off + y * st: off + y * st + w * 3]
    nxt = raw[off + (y + 1) * st: off + (y + 1) * st + w * 3] if y + 1 < h_ else None
    for x in range(0, (w - 1) * 3, 3):
        a = (row[x + 2], row[x + 1], row[x])
        b = (row[x + 5], row[x + 4], row[x + 3])
        pa, pb = defs.get(a), defs.get(b)
        if pa != pb and pa and pb:
            if pa in new:
                neigh[pa][pb] += 1
            if pb in new:
                neigh[pb][pa] += 1
        if nxt is not None:
            c = (nxt[x + 2], nxt[x + 1], nxt[x])
            pc = defs.get(c)
            if pa != pc and pa and pc:
                if pa in new:
                    neigh[pa][pc] += 1
                if pc in new:
                    neigh[pc][pa] += 1
clim = L(os.path.join(game, 'map', 'climate.txt'))
names = re.findall(r'(?ms)^(\w+)\s*=\s*\r?\n?\{([^{}]*)\}', clim)
pclim = {}
for nm, body in names:
    ids = re.findall(r'\b\d+\b', re.sub(r'#[^\n]*', '', body))
    if '_rgo_' in body:
        continue
    for i in ids:
        pclim[int(i)] = nm
add = collections.defaultdict(list)
for pid in sorted(new):
    n = next((q for q, _ in neigh[pid].most_common() if q in pclim), None)
    if n is None:
        note('clima', f'{pid}: sin vecino con clima')
        continue
    add[pclim[n]].append(pid)
    note('clima', f'{pid}: {pclim[n]} (vecino {n})')
for nm, ids in add.items():
    # segunda aparicion del nombre: la lista de provincias
    ms = [m for m in re.finditer(rf'(?ms)^{nm}\s*=\s*\r?\n?\{{([^{{}}]*)\}}', clim) if '_rgo_' not in m.group(1)]
    m = ms[0]
    ins = m.end(1)
    clim = clim[:ins] + ' ' + ' '.join(map(str, ids)) + ' ' + clim[ins:]
W(D('map', 'climate.txt'), clim)

# ---- 10. Textos danados ---------------------------------------------------------------------------
# text.csv paso por una herramienta en UTF-8: cada letra acentuada se comio el caracter siguiente y dejo un '?'.
# Si ese caracter era un ';' la fila quedo una columna corta y el italiano paso a ocupar la columna espanola.
PARTY = {b'Conservatives': 'Conservadores', b'Liberals': 'Liberales', b'National Liberals': 'Nacional Liberales', b'Socialists': 'Socialistas',
         b'National Socialists': 'Nacional Socialistas', b'Monarchy Leadership': 'Reaccionarios monárquicos', b'Radical Liberals': 'Anarcoliberales',
         b'Communists': 'Comunistas', b'Fascists': 'Fascistas'}
BROKEN = re.compile(rb'[A-Za-z\xc0-\xff]\?[A-Za-z\xc0-\xff]')
base_rows = {}
for pth in sorted(glob.glob(os.path.join(glob.escape(game), 'localisation', '*.csv'))):
    for line in rb(pth).split(b'\n'):
        c = line.rstrip(b'\r').split(b';')
        if c[0] and not c[0].startswith(b'#'):
            base_rows.setdefault(c[0].lower(), c)
short = {k.lower().encode(): v.encode('cp1252') for k, v in SHORT.items()}
full = {k.lower().encode(): (k.encode(), en.encode('cp1252'), es.encode('cp1252')) for k, (en, es) in FULL.items()}
parts = {k.lower().encode(): [(a.encode('cp1252'), b.encode('cp1252')) for a, b in v] for k, v in PARTS.items()}
names = {}
csvs = sorted(glob.glob(os.path.join(glob.escape(dst), 'localisation', '*.csv')))
for pth in csvs:
    d = rb(pth)
    orig = d
    if d.startswith(b'\xef\xbb\xbf'):
        d = d[3:]
    if re.search(rb'[\x80-\xff]', d):
        try:
            u = d.decode('utf-8')
        except UnicodeDecodeError:
            u = None
        if u is not None:
            d = b''.join(c.encode('cp1252') if c.isascii() or c in 'áéíóúüñÁÉÍÓÚÜÑ¿¡«»àèìòùâêîôûäëïöçÀÈÌÒÙÂÊÎÔÛÄËÏÖÇãõÃÕåÅæÆøØß¤§' else to_ascii(c).encode('ascii', 'replace') for c in u)
            note('UTF8_a_ANSI', os.path.relpath(pth, dst))
    if d != orig:
        wb(pth, d)
for pth in csvs:
    for line in rb(pth).split(b'\n'):
        c = line.rstrip(b'\r').split(b';')
        if len(c) > SPANISH and c[SPANISH].strip():
            names.setdefault(c[0].lower(), c[SPANISH])
cnt = collections.Counter()
for pth in csvs:
    orig = rb(pth)
    lines = orig.split(b'\n')
    widths = collections.Counter(x.count(b';') + 1 for x in lines if x.count(b';') > SPANISH)
    mode = widths.most_common(1)[0][0] if widths else 0
    same_as_base = os.path.exists(os.path.join(game, 'localisation', os.path.basename(pth)))
    for i, line in enumerate(lines):
        cr = line.endswith(b'\r')
        c = (line[:-1] if cr else line).split(b';')
        k = c[0].lower()
        if not k or k.startswith(b'#') or k in (b'code', b'key') or len(c) < 2:
            continue
        before = list(c)
        es = c[SPANISH] if len(c) > SPANISH else b''
        if k in base_rows and (BROKEN.search(es) or (same_as_base and len(c) < mode)):
            c = list(base_rows[k])
            cnt['fila repuesta desde el juego base'] += 1
        if k == b'evtdesc601xxx':
            c[SPANISH] = c[SPANISH + 1]
            cnt['columna espanola recolocada'] += 1
        c += [b''] * (SPANISH + 1 - len(c))
        if k in full:
            n, en, es = full[k]
            c = [n, en, b'', b'', b'', es] + [b''] * 8 + [b'x']
        elif k in short:
            c[SPANISH] = short[k]
        for a, b in parts.get(k, []):
            c[SPANISH] = c[SPANISH].replace(a, b)
        if not c[SPANISH].strip():
            en = c[1].strip()
            base_es = base_rows[k][SPANISH].strip() if k in base_rows and len(base_rows[k]) > SPANISH else b''
            alias = names.get(k.split(b'_')[0]) if k.endswith(b'_adj') else None
            c[SPANISH] = base_es or (PARTY[en].encode('cp1252') if en in PARTY else en) or alias or b''
            cnt['espanol vacio rellenado'] += 1
        c[SPANISH] = limpiar(c[SPANISH], c[SPANISH].startswith(b'"') and len(c) > mode and same_as_base, c)
        if c != before:
            lines[i] = b';'.join(c) + (b'\r' if cr else b'')
            cnt['filas cambiadas'] += 1
    d = b'\n'.join(lines)
    if d != orig:
        wb(pth, d)
for k, v in sorted(cnt.items()):
    note('textos', f'{k}: {v}')

# ---- 11. Textos que faltaban ----------------------------------------------------------------------
LOC = [
    ('AGC', 'Angoche', 'Angoche'), ('AGC_ADJ', 'Angochese', 'angochano'), ('DEC', 'Deccan', 'Decán'), ('DEC_ADJ', 'Deccani', 'decaní'),
    ('GYN', 'Guyana', 'Guyana'), ('GYN_ADJ', 'Guyanese', 'guyanés'), ('TOU', 'Touat', 'Tuat'), ('TOU_ADJ', 'Touati', 'tuatí'),
    ('ZOM', 'Zomia', 'Zomia'), ('ZOM_ADJ', 'Zomian', 'zomio'),
    ('mestizo', 'Mestizo', 'Mestizo'), ('chechen', 'Chechen', 'Checheno'), ('pardo_brazilian', 'Pardo Brazilian', 'Pardo brasileño'),
    ('norman', 'Norman', 'Normando'), ('zzz_religion_mormon', 'Mormon', 'Mormón'), ('nyasa', 'Nyasa', 'Nyasa'), ('american', 'American', 'Estadounidense'),
    ('mormon', 'Mormon', 'Mormón'),
    ('EVTNAME250004', 'A New Era', 'Una nueva era'), ('EVTDESC250004', 'Times are changing for our nation.', 'Los tiempos están cambiando para nuestra nación.'),
    ('EVTDESC5500xxx', 'Our nation has reached a new stage of its history.', 'Nuestra nación ha alcanzado una nueva etapa de su historia.'),
    ('austrian_form_south_german_confederation2_title', 'Form the South German Confederation', 'Formar la Confederación Alemana del Sur'),
    ('form_germany_AUS_title', 'Form Germany', 'Formar Alemania'), ('austria_annex_SGF_title', 'Annex the South German Confederation', 'Anexionar la Confederación Alemana del Sur'),
    ('form_india_title', 'Form India', 'Formar la India'), ('form_north_german_confederation2_title', 'Form the North German Confederation', 'Formar la Confederación Alemana del Norte'),
    ('form_south_german_confederation2_title', 'Form the South German Confederation', 'Formar la Confederación Alemana del Sur'),
    ('taiping_and_csa_title', 'Taiping and the Confederacy', 'Los Taiping y la Confederación'),
    ('form_occitania_title', 'Form Occitania', 'Formar Occitania'), ('form_the_suebi_title', 'Form the Suebi Kingdom', 'Formar el Reino Suevo'),
    ('form_visigothia_title', 'Form Visigothia', 'Formar Visigotia'),
]
rows = ['CODE;ENGLISH;FRENCH;GERMAN;POLISH;SPANISH;ITALIAN;SWEDISH;CZECH;HUNGARIAN;DUTCH;PORTUGUESE;RUSSIAN;FINNISH;x']
loaded = set()
for pth in glob.glob(os.path.join(glob.escape(dst), 'localisation', '*.csv')):
    for line in L(pth).splitlines():
        loaded.add(line.split(';')[0].lower())
for k, en, es in LOC:
    if k.lower() not in loaded:
        rows.append(f'{k};{en};;;;{es};;;;;;;;;x')
# Claves del base que se perdieron porque UPM sustituye su archivo por una copia mas antigua.
for pth in csvs:
    bp = os.path.join(game, 'localisation', os.path.basename(pth))
    if os.path.exists(bp):
        for line in rb(bp).decode('cp1252', 'replace').splitlines():
            c = line.split(';')
            if len(c) > SPANISH and c[0] and not c[0].startswith('#') and c[0].lower() not in loaded:
                rows.append(line)
                loaded.add(c[0].lower())
if len(rows) > 1:
    wb(D('localisation', 'zz_correcciones.csv'), ('\r\n'.join(rows) + '\r\n').encode('cp1252', 'replace'))
    note('textos', f'{len(rows) - 1} claves nuevas en zz_correcciones.csv')

# ---- 12. Ajustes de rebeldes y carga de IA ----------------------------------------------------------
DEFS = [
    # Tras alzarse, el pop no bajaba nada de militancia y podia repetir revuelta enseguida.
    ('REDUCTION_AFTER_RISEING', '0.0', '2.0'),
    ('MIL_TO_JOIN_RISING', '8', '8.5'),
    ('MIL_TO_AUTORISE', '9', '9.5'),
    ('MIL_REQUIRE_REFORM', '0.2', '0.15'),
    ('MIL_WAR_EXHAUSTION', '0.005', '0.003'),
    ('REBEL_OCCUPATION_STRENGTH_BONUS', '0.01', '0.005'),
    # UPM multiplico por 5 la asimilacion respecto al base: cada asimilacion parte pops y crea mas unidades que simular.
    ('ASSIMILATION_SCALE', '0.02', '0.008'),
    # Ejercitos y flotas de la IA mas contenidos en late game.
    ('SOLDIER_FRACTION', '0.045', '0.035'),
    ('MAX_FLEETS', '20', '10'),
]
p = D('common', 'defines.lua')
t = L(p)
for k, a, b in DEFS:
    t, n = re.subn(rf'(\b{k}\s*=\s*){re.escape(a)}\b', lambda m: m.group(1) + b, t)
    assert n == 1, k
    note('defines', f'{k}: {a} -> {b}')
W(p, t)

# ---- 13. Condiciones: comprobaciones caras al final (misma logica, menos trabajo) --------------------
EXPENSIVE = {'any_owned_province', 'any_country', 'any_neighbor_country', 'any_pop', 'any_state', 'any_core', 'all_core', 'any_greater_power',
             'any_substate', 'any_sphere_member', 'any_neighbor_province', 'any_empty_neighbor_province', 'any_vassal', 'any_owned', 'war_countries'}
TK = re.compile(rb'#[^\n]*|"[^"]*"|[{}=]|[^\s{}="#]+')


def spans(data, a, b):
    """Elementos k = v de nivel superior entre a y b, o None si hay algo que no sea k = v."""
    toks = [(m.start(), m.end(), m.group(0)) for m in TK.finditer(data, a, b) if not m.group(0).startswith(b'#')]
    items, i = [], 0
    while i < len(toks):
        s, e, k = toks[i]
        if k in (b'{', b'}', b'=') or i + 2 >= len(toks) or toks[i + 1][2] != b'=':
            return None
        v = toks[i + 2]
        if v[2] == b'{':
            d, j = 1, i + 3
            while d and j < len(toks):
                d += (toks[j][2] == b'{') - (toks[j][2] == b'}')
                j += 1
            if d:
                return None
            end = toks[j - 1][1]
            body = {t[2] for t in toks[i + 3:j]}
            items.append((s, end, k, body))
            i = j
        else:
            items.append((s, v[1], k, set()))
            i += 3
    return items


def block_end(data, a):
    d, i = 1, a
    for m in TK.finditer(data, a):
        x = m.group(0)
        if x == b'{':
            d += 1
        elif x == b'}':
            d -= 1
            if d == 0:
                return m.start()
    return None


EXP = {x.encode() for x in EXPENSIVE}
total = 0
for z, key in (('events', rb'\btrigger\s*=\s*\{'), ('decisions', rb'\bpotential\s*=\s*\{')):
    for pth in glob.glob(os.path.join(glob.escape(dst), z, '*.txt')):
        d = rb(pth)
        edits = []
        for m in re.finditer(key, d):
            # solo condiciones de primer nivel de un evento o decision
            e = block_end(d, m.end())
            if e is None:
                continue
            it = spans(d, m.end(), e)
            if not it or len(it) < 2:
                continue
            flags = [(x[2] in EXP) or bool(x[3] & EXP) for x in it]
            if not any(flags) or all(flags):
                continue
            order = [x for x, f in zip(it, flags) if not f] + [x for x, f in zip(it, flags) if f]
            if order == it:
                continue
            edits.append((it, order))
        if not edits:
            continue
        for it, order in reversed(edits):
            chunks = [d[x[0]:x[1]] for x in order]
            for k in range(len(it) - 1, -1, -1):
                d = d[:it[k][0]] + chunks[k] + d[it[k][1]:]
        a = sorted(m.group(0) for m in TK.finditer(rb(pth)) if not m.group(0).startswith(b'#'))
        b = sorted(m.group(0) for m in TK.finditer(d) if not m.group(0).startswith(b'#'))
        assert a == b, pth
        wb(pth, d)
        total += len(edits)
        note('condiciones', f'{os.path.relpath(pth, dst)}: {len(edits)}')
print('condiciones reordenadas', total)

with open(logpath, 'w', encoding='utf-8') as f:
    for k in sorted(log):
        f.write(f'\n[{k}] {len(log[k])}\n')
        for x in log[k]:
            f.write(f'  {x}\n')
for k in sorted(log):
    print(f'{k}: {len(log[k])}')
    for x in log[k][:3]:
        print('   ', x[:110])
