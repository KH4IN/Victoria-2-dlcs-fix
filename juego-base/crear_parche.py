"""Crea un parche con solo las diferencias entre los archivos originales y los corregidos, sin copiar archivos del juego.

Uso: python -I crear_parche.py <carpeta_originales> <juego_corregido> <parche.txt>
Formato: una linea F por archivo (ruta, sha256 original, sha256 corregido) y lineas E (posicion, bytes borrados, base64 nuevo).
"""
import base64
import difflib
import hashlib
import os
import sys


def sha(d):
    return hashlib.sha256(d).hexdigest()


def edits(a, b):
    """Cambios minimos: compara por lineas y recorta lo comun de cada bloque."""
    al, bl = a.splitlines(keepends=True), b.splitlines(keepends=True)
    pos = [0]
    for x in al:
        pos.append(pos[-1] + len(x))
    res = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, al, bl, autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        s, e = pos[i1], pos[i2]
        new = b''.join(bl[j1:j2])
        old = a[s:e]
        p = 0
        while p < min(len(old), len(new)) and old[p] == new[p]:
            p += 1
        q = 0
        while q < min(len(old), len(new)) - p and old[-1 - q] == new[-1 - q]:
            q += 1
        res.append((s + p, len(old) - p - q, new[p:len(new) - q]))
    return res


def apply(a, ed):
    o, last = [], 0
    for at, n, new in ed:
        o.append(a[last:at])
        o.append(new)
        last = at + n
    o.append(a[last:])
    return b''.join(o)


def main():
    old_root, new_root, out = sys.argv[1:4]
    lines = []
    kept = total = 0
    for dp, _, fn in os.walk(old_root):
        for name in sorted(fn):
            p = os.path.join(dp, name)
            rel = os.path.relpath(p, old_root)
            with open(p, 'rb') as f:
                a = f.read()
            with open(os.path.join(new_root, rel), 'rb') as f:
                b = f.read()
            ed = edits(a, b)
            assert apply(a, ed) == b, rel
            lines.append(f'F\t{rel}\t{sha(a)}\t{sha(b)}')
            for at, n, new in ed:
                lines.append(f'E\t{at}\t{n}\t{base64.b64encode(new).decode()}')
                kept += n
            total += len(a)
    with open(out, 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    print('archivos', sum(1 for x in lines if x[0] == 'F'), 'cambios', sum(1 for x in lines if x[0] == 'E'), 'tamano parche KB', os.path.getsize(out) // 1024, 'bytes originales', total)


if __name__ == '__main__':
    main()
