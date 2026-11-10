"""Corrige directamente los archivos del juego base. Cada archivo original se guarda antes en la copia de seguridad.

Uso: python -I base_fix.py <carpeta_del_juego> <carpeta_copia_de_seguridad> <registro.txt>
"""
import collections
import glob
import os
import re
import shutil
import sys

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
SHORT = {
    # Nombres cortados con " ..." en sus botones
    'point_defense_system': 'Defensa en puntos', 'point_defense_system_desc': 'Defensa en puntos',
    'deep_defense_system': 'Defensa en profundidad', 'military_staff_system': 'Sistema de estado mayor',
    'army_decision_making': 'Toma de decisiones militar', 'army_risk_management': 'Supervisión de riesgos',
    'army_nco_training': 'Formación de suboficiales', 'bank_inspection_board': 'Inspección bancaria',
    'ad_hoc_money_bill_printing': 'Papel moneda específico', 'private_bank_money_bill_printing': 'Papel moneda banca privada',
    'central_bank_money_bill_printing': 'Papel moneda Banco Central', 'modern_central_bank_system': 'Banco Central moderno',
    'market_determined_exchange_rates': 'Tipos de cambio de mercado', 'early_classical_theory_and_critique': 'Primeras teorías clásicas',
    'classicism_n_early_romanticism': 'Clasicismo y romanticismo', 'mass_culture_n_the_avant_garde': 'Cultura de masas y vanguardia',
    'high_n_low_pressure_steam_engines': 'Vapor a alta y baja presión', 'electrical_power_generation': 'Generación eléctrica',
    'blue_and_brown_water_schools': 'Aguas azules y marrones', 'oil_driven_ships': 'Barcos de petróleo',
    'alphabetic_flag_signaling': 'Alfabeto de banderas', 'naval_risk_management': 'Riesgos navales',
    'naval_nco_training': 'Suboficiales navales',
    'gerrymandering': 'Distritos amañados', 'trinket_wage': 'Salarios testimoniales', 'low_schools': 'Escuela básica',
    'no_admin_reform': 'Sin reforma administrativa', 'no_finance_reform': 'Sin reforma financiera', 'yes_finance_reform': 'Reforma financiera',
    'no_education_reform': 'Sin reforma educativa', 'no_pre_indust': 'Costumbres antiguas', 'yes_pre_indust': 'Industrialización',
    'no_industrial_construction': 'Sin obra industrial', 'no_foreign_training': 'Formación local', 'yes_foreign_training': 'Formación extranjera',
    'no_foreign_officers': 'Oficiales locales', 'yes_foreign_officers': 'Oficiales extranjeros',
    'no_foreign_naval_officers': 'Mandos navales locales', 'yes_foreign_naval_officers': 'Mandos navales extranjeros',
    'yes_foreign_navies': 'Flota importada', 'MILITARY_UNIT_EXPERIENCE': 'Experiencia inicial',
    'yes_slavery_l': 'Esclavismo', 'TRADE_EXPORTED': 'Export.',
    # La cifra de la barra superior es lo ganado ayer, no el balance previsto: el texto lo deja claro.
    'TOPBAR_FUNDS': 'Ayer ganamos $YESTERDAY$¤ (la cifra entre paréntesis es solo la de ayer y varía mucho: el balance real está en Presupuesto, «Balance diario previsto»). Nuestra reserva monetaria actual es de §Y$CASH$§W¤.',
    'DIPLOMACY_THEY_BETTER_OPINION': 'No podemos dirigir esta acción contra §Y$TARGET$§W, ya que §Y$RECIPIENT$§W tiene una opinión §Y$OPINION$§W de ellos.\\n',
    'DIPLOMACY_THEY_BETTER_OPINION2': 'Necesitan tener al menos la misma opinión de nosotros para poder influirles. Su opinión actual de nosotros es §Y$OPINION$§W.',
    'EVTDESC3004': "Ante una opinión pública poco favorable a nuevas reformas sociales, algunos ciudadanos de uno de nuestros estados han decidido ocuparse por su cuenta de los más desfavorecidos y han fundado una 'Sociedad de Amigos'. La sociedad se dedica a diversas tareas de asistencia: alimentos para los ancianos, empleo y educación religiosa para los pobres, y además gestiona una casa de trabajo cooperativa con esos fines.",
    'EVTDESC4408': "...y me parece una auténtica farsa que, mientras nuestro pueblo trabaja bajo el yugo de la pobreza, la insalubridad y la degradación moral, nuestro parlamento insista en gastar millones y millones en pólvora y cañones. Nuestra nación debe ir a la guerra, caballeros: una guerra contra los males que aquejan a nuestra sociedad.'\\n\\nUno de los miembros de nuestro gabinete se ha dirigido al parlamento con un largo discurso que expone la política antimilitarista del gobierno. ¿Cómo deberíamos aprovechar esto?",
    # Variables mal escritas o frases que decian otra cosa que el texto ingles.
    'CB_JUSTIFY_NO_LONGER_VALID_LOG': 'Nuestro proceso de justificación de la guerra contra $TARGET$ ya no es válido.',
    'WAR_OTHER_ACCEPT_LOG': '$AGRESSOR$ ha declarado la guerra a $DEFENDER$.',
    'WAR_THEY_ACCEPT_LOG': 'Hemos declarado la guerra a $DEFENDER$.',
    'INVESTED_IN_US_1': '¡$ICOUNTRY$ ha invertido en nosotros!',
    'INVESTED_IN_US_BUILD': '$INAME$ construida en $ILOCATION$ por $IAMOUNT$¤',
    'INVESTED_IN_US_LOG': '§Y$ICOUNTRY$§! ha invertido en nosotros: $INVESTED_IN_US_MESSAGE$',
    'GUNBOAT_ALREADY_ACTIVE': 'Ya les amenaza $COUNTRY$.',
    'GAIN_CB': 'Gana casus belli de tipo $TYPE$ sobre §Y$WHO$§W.\\n',
    'REV_GAIN_CB': '§Y$ACTIVE$§W gana un casus belli de tipo $TYPE$ sobre §Y$PASSIVE$§W.\\n',
    'COLONY_FAIL_5': '$OTHER$, llevado por la codicia, ha reclamado la región.',
    'ATTACKTHEM_MAP': 'Comenzó ataque',
    'TRIGMOD_BTN1': 'Aceptar',
    'TRIGMOD_BTN2': 'Aceptar',
    'IDEOLOGY_IS_EQUAL_TO_TRIGGER': 'El partido gobernante es §Y$NAME$§W.\\n',
    'IDEOLOGY_IS_NOT_TRIGGER': 'El partido gobernante NO es §Y$NAME$§W.\\n',
    'TOPBAR_DIPLOPOINTS': 'Tenemos un total de §Y$CURR$§W puntos diplomáticos.',
    'war_we_lose_medium_title': '¡FIRMADA UNA PAZ VERGONZOSA!',
}
# Cambios dentro de textos largos.
PARTS = {
    'TOPBAR_POPULATION': [('ha cambiado en $CURR$ en la últimos', 'ha cambiado en $CHANGE$ en los últimos')],
    'AI_LOVES_US_DESC1_MEDIUM': [('$TAG_0_0_$', '$TAG_0_0$')],
    'AI_LOVES_US_DESC3_SHORT': [('$TAG_0_0J$', '$TAG_0_0$'), ('continuan', 'continúan'), ('facilmente', 'fácilmente')],
}
# Filas rotas en el juego: un ';' dentro del texto ingles descuadra todas las columnas.
FULL = {
    'post_napoleonic_army_doctrine_desc': (
        'After the Napoleonic Wars armies grew into massed formations of citizen soldiers, organized in divisions and corps.',
        'La Revolución Francesa y las Guerras Napoleónicas que la siguieron revolucionaron la estrategia militar. Con la llegada de armas ligeras baratas y del ciudadano soldado reclutado, los ejércitos crecieron con rapidez. Esto obligó a dividir el ejército primero en divisiones y más tarde en cuerpos, y las rígidas formaciones de piqueros y mosqueteros dieron paso a la infantería ligera en línea de tiradores.'),
    'machine_gun_armament_desc': (
        'From the hand-cranked Gatling gun of 1861 to the recoil-operated Maxim gun of 1885, automatic fire changed warfare.',
        'La ametralladora Gatling, patentada en 1861 por Richard Jordan Gatling, fue la primera en ofrecer fuego controlado y secuencial con carga automática. La primera ametralladora de funcionamiento autónomo la inventó Sir Hiram Maxim en 1885: usaba la fuerza de retroceso del disparo anterior para recargar, lo que permitía una cadencia mucho mayor que los diseños anteriores.'),
    'form_yugoslavia_title': ('Form Yugoslavia', 'Formar Yugoslavia'),
    'form_yugoslavia_desc': ('The South Slavs should be united in a single state.', 'Los eslavos del sur deberían unirse en un solo Estado.'),
}
SPANISH = 5  # columna del espanol en los .csv
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
        # Texto copiado de una hoja de calculo: el juego muestra las comillas de CSV y corta en los ';'.
        if es.startswith(b'"') and len(c) > mode:
            es += b',' + c.pop(SPANISH + 1)
        if es.startswith(b'"') and es.endswith(b'"') and len(es) > 1:
            es = es[1:-1]
        es = es.replace(b'""', b'"').replace(b'$STR_0_0$', b'$STRING_0_0$')
        es = re.sub(rb'(?<=\S)(?<!\\n) {2,}(?=\S)', b' ', es)
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
