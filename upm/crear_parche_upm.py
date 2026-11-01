"""Crea el parche de UPM con solo las diferencias, sin copiar archivos del mod ni del juego.

Uso: python -I crear_parche_upm.py <UPM_sin_tocar> <UPM_corregido> <juego_base_corregido> <parche.txt>
Formato, con rutas relativas a la carpeta del juego:
  B ruta sha256: archivo del juego base corregido que debe existir.
  F ruta sha256_original sha256_corregido: archivo del mod que cambia, seguido de sus lineas E.
  N ruta fuente sha256_fuente sha256_final: archivo nuevo creado desde otro, seguido de sus lineas E. La fuente es - si no hay.
  D ruta sha256: archivo que sale del mod.
  E posicion bytes_borrados base64_nuevo.
"""
import base64
import collections
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'juego-base'))
from crear_parche import apply, edits, sha  # noqa: E402

MOD = 'mod/UPM'
BASE_CORREGIDA = 'common/defines.lua'


def listar(root):
    res = {}
    for dp, _, fn in os.walk(root):
        for name in fn:
            p = os.path.join(dp, name)
            res[os.path.relpath(p, root).replace('\\', '/')] = p
    return res


def leer(p):
    with open(p, 'rb') as f:
        return f.read()


def bloque(cabecera, a, b, rel, lines, puesto):
    ed = edits(a, b)
    assert apply(a, ed) == b, rel
    lines.append(cabecera)
    for at, n, new in ed:
        lines.append(f'E\t{at}\t{n}\t{base64.b64encode(new).decode()}')
    puesto[rel] = (sum(len(e[2]) for e in ed), len(b))


def fuente_de(rel, base_root, quitados):
    """Busca desde que archivo crear uno nuevo: el del juego base o el que el mod cambio de carpeta."""
    p = os.path.join(base_root, rel)
    if os.path.exists(p):
        return rel, p
    nombre = rel.rsplit('/', 1)[-1]
    for q, qp in quitados.items():
        if q.rsplit('/', 1)[-1] == nombre:
            return f'{MOD}/{q}', qp
    return None, None


def main():
    old_root, new_root, base_root, out = sys.argv[1:5]
    viejo, nuevo = listar(old_root), listar(new_root)
    quitados = {k: viejo[k] for k in viejo if k not in nuevo}
    lines = [f'B\t{BASE_CORREGIDA}\t{sha(leer(os.path.join(base_root, BASE_CORREGIDA)))}']
    puesto = {}
    for rel in sorted(set(viejo) & set(nuevo)):
        a, b = leer(viejo[rel]), leer(nuevo[rel])
        if a != b:
            bloque(f'F\t{MOD}/{rel}\t{sha(a)}\t{sha(b)}', a, b, rel, lines, puesto)
    for rel in sorted(set(nuevo) - set(viejo)):
        b = leer(nuevo[rel])
        fuente, p = fuente_de(rel, base_root, quitados)
        a = leer(p) if p else b''
        huella = sha(a) if p else '-'
        bloque(f'N\t{MOD}/{rel}\t{fuente or "-"}\t{huella}\t{sha(b)}', a, b, rel, lines, puesto)
    for rel in sorted(quitados):
        lines.append(f'D\t{MOD}/{rel}\t{sha(leer(quitados[rel]))}')
    with open(out, 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')

    c = collections.Counter(x[0] for x in lines)
    print('lineas', dict(c), 'parche KB', os.path.getsize(out) // 1024)
    print('bytes puestos', sum(v[0] for v in puesto.values()), 'de', sum(v[1] for v in puesto.values()))
    casi = sorted(((v[0] / v[1], v[0], k) for k, v in puesto.items() if v[1] and v[0] > v[1] / 2), reverse=True)
    print('archivos con mas de la mitad puesta:', len(casi), 'bytes', sum(x[1] for x in casi))
    for r, n, k in casi[:30]:
        print(f'  {r:.0%} {n} {k}')


if __name__ == '__main__':
    main()
