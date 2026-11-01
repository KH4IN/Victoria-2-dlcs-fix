"""Corrige directamente los archivos del juego base. Cada archivo original se guarda antes en la copia de seguridad.

Uso: python -I base_fix.py <carpeta_del_juego> <carpeta_copia_de_seguridad> <registro.txt>
"""
import collections
import glob
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textos import FULL, PARTS, SHORT, SPANISH, limpiar  # noqa: E402

game, backup, logpath = sys.argv[1:4]
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
log = collections.defaultdict(list)
changed = []


def note(c, m):
    log[c].append(m)


def rb(p):
    with open(p, 'rb') as f:
        return f.read()


def wb(p, d):
    b = os.path.join(backup, os.path.relpath(p, game))
    if not os.path.exists(b):
        os.makedirs(os.path.dirname(b), exist_ok=True)
        shutil.copy2(p, b)
    with open(p, 'wb') as f:
        f.write(d)
    changed.append(os.path.relpath(p, game))


def G(*a):
    return os.path.join(game, *a)


if re.search(rb'REDUCTION_AFTER_RISEING\s*=\s*2\.0', rb(G('common', 'defines.lua'))):
    sys.exit('Las correcciones ya estan aplicadas en este juego.')

# ---- Textos ---------------------------------------------------------------------------------
short = {k.lower(): es.encode('cp1252') for k, es in SHORT.items()}
full = {k.lower(): (k, en.encode('cp1252'), es.encode('cp1252')) for k, (en, es) in FULL.items()}
parts = {k.lower(): [(a.encode('cp1252'), b.encode('cp1252')) for a, b in v] for k, v in PARTS.items()}
assert not any(b';' in x for x in short.values()) and not any(b';' in x[1] + x[2] for x in full.values())
found = set()
tidy = 0
# Se corrige cada aparicion de la clave en su propia fila, para que no dependa del orden de carga.
for p in sorted(glob.glob(G('localisation', '*.csv'))):
    orig = rb(p)
    lines = orig.split(b'\n')
    widths = collections.Counter(len(x.split(b';')) for x in lines if x.count(b';') > SPANISH)
    mode = widths.most_common(1)[0][0] if widths else 0
    for i, line in enumerate(lines):
        cr = line.endswith(b'\r')
        c = (line[:-1] if cr else line).split(b';')
        if line.startswith(b'#'):
            continue
        k = c[0].decode('latin-1').lower()
        if k in full:
            n, en, es = full[k]
            c = [n.encode(), en, b'', b'', b'', es] + [b''] * 8 + [b'x']
            found.add(k)
        elif k in short:
            c += [b''] * (SPANISH + 1 - len(c))
            c[SPANISH] = short[k]
            found.add(k)
        elif len(c) <= SPANISH:
            continue
        before = c[SPANISH]
        es = c[SPANISH]
        for a, b in parts.get(k, []):
            assert a in es, (k, a)
            es = es.replace(a, b)
            found.add(k)
        es = limpiar(es, len(c) > mode, c)
        if es != before:
            tidy += 1
        c[SPANISH] = es
        lines[i] = b';'.join(c) + (b'\r' if cr else b'')
    d = b'\n'.join(lines)
    if d != orig:
        wb(p, d)
assert set(short) <= found, sorted(set(short) - found)
assert set(parts) <= found, sorted(set(parts) - found)
note('textos', f'{tidy} filas con comillas, variables o espacios arreglados')
new = [f for f in full if f not in found]
if new:
    d = rb(G('localisation', 'text.csv')).rstrip(b'\r\n')
    for k in new:
        n, en, es = full[k]
        d += b'\r\n' + b';'.join([n.encode(), en, b'', b'', b'', es] + [b''] * 8 + [b'x'])
    wb(G('localisation', 'text.csv'), d + b'\r\n')
for k, v in SHORT.items():
    note('textos', f'{k}: {v[:60]}')
for k, v in FULL.items():
    note('textos', f'{k}: {v[1][:60]}')

# ---- Datos ----------------------------------------------------------------------------------
# Dos historias para la misma provincia: se igualan para que no dependa del orden de carga.
wb(G('history', 'provinces', 'indonesia', '1396 - Api.txt'), rb(G('history', 'provinces', 'asia', '1396 - Api.txt')))
note('datos', 'provincia 1396: historia duplicada igualada')
# Partidos gobernantes fuera de fecha al empezar en 1861.
for f, date, party in (('ROM - Romania.txt', '1859.1.1', 'ROM_liberal_2'), ('CHI - China.txt', '1861.1.1', 'CHI_conservative_2')):
    d = rb(G('history', 'countries', f)).rstrip()
    d += f'\r\n\r\n{date} = {{ ruling_party = {party} }}\r\n'.encode('ascii')
    wb(G('history', 'countries', f), d)
    note('datos', f'{f}: {party} desde {date}')
# Nombre de provincia en UTF-8 dentro de un archivo que debe ser ANSI.
d = rb(G('history', 'units', '1861', 'HAI_oob.txt')).decode('utf-8').encode('cp1252')
wb(G('history', 'units', '1861', 'HAI_oob.txt'), d)
note('datos', 'HAI_oob.txt: convertido a ANSI')

# ---- Rebeldes: ajuste minimo --------------------------------------------------------------------
DEFS = [
    # Tras alzarse el pop no perdia militancia y podia repetir revuelta enseguida.
    ('REDUCTION_AFTER_RISEING', '0.0', '2.0'),
    ('MIL_TO_AUTORISE', '9', '9.5'),
]
t = rb(G('common', 'defines.lua')).decode('latin-1')
for k, a, b in DEFS:
    t, n = re.subn(rf'(\b{k}\s*=\s*){re.escape(a)}\b', lambda m: m.group(1) + b, t)
    assert n == 1, k
    note('defines', f'{k}: {a} -> {b}')
wb(G('common', 'defines.lua'), t.encode('latin-1'))

# ---- Condiciones: lo caro al final (misma logica, menos trabajo) ----------------------------------
EXPENSIVE = {x.encode() for x in ('any_owned_province', 'any_country', 'any_neighbor_country', 'any_pop', 'any_state', 'any_core', 'all_core',
                                  'any_greater_power', 'any_substate', 'any_sphere_member', 'any_neighbor_province', 'any_empty_neighbor_province',
                                  'any_vassal', 'any_owned', 'war_countries')}
TK = re.compile(rb'#[^\n]*|"[^"]*"|[{}=]|[^\s{}="#]+')


def spans(data, a, b):
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
            items.append((s, toks[j - 1][1], k, {x[2] for x in toks[i + 3:j]}))
            i = j
        else:
            items.append((s, v[1], k, set()))
            i += 3
    return items


def block_end(data, a):
    d = 1
    for m in TK.finditer(data, a):
        x = m.group(0)
        if x == b'{':
            d += 1
        elif x == b'}':
            d -= 1
            if d == 0:
                return m.start()
    return None


total = 0
for z, key in (('events', rb'\btrigger\s*=\s*\{'), ('decisions', rb'\bpotential\s*=\s*\{')):
    for pth in sorted(glob.glob(G(z, '*.txt'))):
        orig = rb(pth)
        d = orig
        edits = []
        for m in re.finditer(key, d):
            e = block_end(d, m.end())
            if e is None:
                continue
            it = spans(d, m.end(), e)
            if not it or len(it) < 2:
                continue
            flags = [(x[2] in EXPENSIVE) or bool(x[3] & EXPENSIVE) for x in it]
            if not any(flags) or all(flags):
                continue
            order = [x for x, f in zip(it, flags) if not f] + [x for x, f in zip(it, flags) if f]
            if order != it:
                edits.append((it, order))
        if not edits:
            continue
        for it, order in reversed(edits):
            chunks = [d[x[0]:x[1]] for x in order]
            for k in range(len(it) - 1, -1, -1):
                d = d[:it[k][0]] + chunks[k] + d[it[k][1]:]
        a = sorted(m.group(0) for m in TK.finditer(orig) if not m.group(0).startswith(b'#'))
        b = sorted(m.group(0) for m in TK.finditer(d) if not m.group(0).startswith(b'#'))
        assert a == b, pth
        wb(pth, d)
        total += len(edits)
        note('condiciones', f'{z}/{os.path.basename(pth)}: {len(edits)}')

with open(logpath, 'w', encoding='utf-8') as f:
    for k in sorted(log):
        f.write(f'\n[{k}] {len(log[k])}\n')
        for x in log[k]:
            f.write(f'  {x}\n')
print('condiciones reordenadas', total)
for k in sorted(log):
    print(f'{k}: {len(log[k])}')
print('archivos cambiados', len(set(changed)))
for x in sorted(set(changed)):
    print(' ', x)
