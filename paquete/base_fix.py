"""Genera el paquete 'Victoria 2 Corregido' a partir del juego base. No modifica ningun archivo del juego.

Uso: python -I base_fix.py <carpeta_del_juego> <carpeta_mod_destino> <archivo_.mod> <registro.txt>
"""
import collections
import glob
import os
import re
import shutil
import sys

game, dst, modfile, logpath = sys.argv[1:5]
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
log = collections.defaultdict(list)


def note(c, m):
    log[c].append(m)


def rb(p):
    with open(p, 'rb') as f:
        return f.read()


def wb(p, d):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(d)


def G(*a):
    return os.path.join(game, *a)


def D(*a):
    return os.path.join(dst, *a)


if os.path.exists(dst):
    shutil.rmtree(dst)
os.makedirs(dst)

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
    'TOPBAR_FUNDS': 'Ayer ganamos $YESTERDAY$¤ (la cifra entre paréntesis es solo la de ayer y varía mucho; el balance real está en Presupuesto, «Balance diario previsto»). Nuestra reserva monetaria actual es de §Y$CASH$§W¤.',
    'DIPLOMACY_THEY_BETTER_OPINION': 'No podemos dirigir esta acción contra §Y$TARGET$§W, ya que §Y$RECIPIENT$§W tiene una opinión §Y$OPINION$§W de ellos.\\n',
    'DIPLOMACY_THEY_BETTER_OPINION2': 'Necesitan tener al menos la misma opinión de nosotros para poder influirles. Su opinión actual de nosotros es §Y$OPINION$§W.',
    'EVTDESC3004': "Ante una opinión pública poco favorable a nuevas reformas sociales, algunos ciudadanos de uno de nuestros estados han decidido ocuparse por su cuenta de los más desfavorecidos y han fundado una 'Sociedad de Amigos'. La sociedad se dedica a diversas tareas de asistencia: alimentos para los ancianos, empleo y educación religiosa para los pobres, y además gestiona una casa de trabajo cooperativa con esos fines.",
    'EVTDESC4408': "...y me parece una auténtica farsa que, mientras nuestro pueblo trabaja bajo el yugo de la pobreza, la insalubridad y la degradación moral, nuestro parlamento insista en gastar millones y millones en pólvora y cañones. Nuestra nación debe ir a la guerra, caballeros: una guerra contra los males que aquejan a nuestra sociedad.'\\n\\nUno de los miembros de nuestro gabinete se ha dirigido al parlamento con un largo discurso que expone la política antimilitarista del gobierno. ¿Cómo deberíamos aprovechar esto?",
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
base = {}
for p in sorted(glob.glob(G('localisation', '*.csv'))):
    for line in rb(p).decode('cp1252', 'replace').splitlines():
        c = line.split(';')
        if c[0] and not c[0].startswith('#'):
            base.setdefault(c[0].lower(), c)
rows = ['CODE;ENGLISH;FRENCH;GERMAN;POLISH;SPANISH;ITALIAN;SWEDISH;CZECH;HUNGARIAN;DUTCH;PORTUGUESE;RUSSIAN;FINNISH;x']
for k, es in SHORT.items():
    c = base.get(k.lower())
    assert c, k
    en = c[1] if c[1].strip() else k
    fr = c[2] if len(c) > 2 else ''
    de = c[3] if len(c) > 3 else ''
    rows.append(f'{c[0]};{en};{fr};{de};;{es};;;;;;;;;x')
    note('textos', f'{c[0]}: {es[:60]}')
for k, (en, es) in FULL.items():
    rows.append(f'{k};{en};;;;{es};;;;;;;;;x')
    note('textos', f'{k}: {es[:60]}')
wb(D('localisation', '00_correcciones.csv'), ('\r\n'.join(rows) + '\r\n').encode('cp1252'))

# ---- Datos ----------------------------------------------------------------------------------
# Dos historias para la misma provincia: se igualan para que no dependa del orden de carga.
wb(D('history', 'provinces', 'indonesia', '1396 - Api.txt'), rb(G('history', 'provinces', 'asia', '1396 - Api.txt')))
note('datos', 'provincia 1396: historia duplicada igualada')
# Partidos gobernantes fuera de fecha al empezar en 1861.
for f, date, party in (('ROM - Romania.txt', '1859.1.1', 'ROM_liberal_2'), ('CHI - China.txt', '1861.1.1', 'CHI_conservative_2')):
    d = rb(G('history', 'countries', f)).rstrip()
    d += f'\r\n\r\n{date} = {{ ruling_party = {party} }}\r\n'.encode('ascii')
    wb(D('history', 'countries', f), d)
    note('datos', f'{f}: {party} desde {date}')
# Nombre de provincia en UTF-8 dentro de un archivo que debe ser ANSI.
d = rb(G('history', 'units', '1861', 'HAI_oob.txt')).decode('utf-8').encode('cp1252')
wb(D('history', 'units', '1861', 'HAI_oob.txt'), d)
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
wb(D('common', 'defines.lua'), t.encode('latin-1'))

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
        wb(D(z, os.path.basename(pth)), d)
        total += len(edits)
        note('condiciones', f'{z}/{os.path.basename(pth)}: {len(edits)}')

with open(modfile, 'wb') as f:
    f.write(b'name = "Victoria 2 Corregido"\r\npath = "mod/V2_Corregido"\r\n')
with open(logpath, 'w', encoding='utf-8') as f:
    for k in sorted(log):
        f.write(f'\n[{k}] {len(log[k])}\n')
        for x in log[k]:
            f.write(f'  {x}\n')
print('condiciones reordenadas', total)
for k in sorted(log):
    print(f'{k}: {len(log[k])}')
n = sum(len(fn) for _, _, fn in os.walk(dst))
print('archivos en el paquete', n)
