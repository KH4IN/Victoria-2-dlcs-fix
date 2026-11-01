# Correcciones del juego base (Victoria 2 v3.04)

Este repositorio **no contiene archivos del juego ni de ningún mod**: son propiedad de sus autores. Solo guarda scripts, herramientas y documentación. El paquete se genera en cada equipo a partir de una copia del juego.

UPM queda fuera de este trabajo: se corregirá aparte, más adelante.

## Cómo se aplica

```bash
python -I paquete/base_fix.py "<juego>" "<juego>/mod/V2_Corregido" "<juego>/mod/V2_Corregido.mod" registro.txt
```

Genera un mod separado, **Victoria 2 Corregido**. No modifica ningún archivo original; si se borra, el juego queda como estaba. No lleva `user_dir` a propósito: comparte configuración, idioma y caché de mapa con el juego base.

## Qué corrige

| Área | Cambio |
|---|---|
| Interfaz | 42 nombres que salían cortados con « ...» en tecnologías, reformas, militar, población y comercio |
| Textos | Errata «Sistesma»; 6 textos sin traducir; título de `form_yugoslavia` |
| Datos | Rumanía y China empezaban 1861 con un partido fuera de fecha; provincia 1396 con dos historias distintas; `HAI_oob.txt` en UTF-8 |
| Economía | Ayuda de la barra superior: aclara que la cifra es la de ayer |
| Rebeldes | `REDUCTION_AFTER_RISEING` de 0 a 2 y `MIL_TO_AUTORISE` de 9 a 9,5 |
| Rendimiento | 25 condiciones reordenadas para evaluar lo barato antes que los bucles `any_*`; misma lógica |

## Causa de las «varias versiones»

El código del menú, como `V2 v3.04 (WNVU)`, es un checksum calculado al arrancar. Según el propio ejecutable incluye `common`, `poptypes`, `events`, `missions`, `units`, `inventions`, `script`, `technologies`, `decisions`, `history/*`, `battleplans`, `map/default.map`, `cache/time` y `v2game.exe`. No incluye `interface`, `gfx`, `localisation` ni `music`.

`cache/time` es una suma de hashes del mapa, idéntica entre equipos, pero se lee **antes** de crear la caché:

| Prueba | Código |
|---|---|
| Primer arranque, sin caché | `VKEW` |
| Siguientes arranques | `WNVU` |
| `time` alterado | `AECE` |
| Mod instalado sin activar | `WNVU` |

Con `Jugar.bat`, partiendo sin caché, el paquete dio `YYWO` a la primera y también con caché.

## Pruebas realizadas

- Sintaxis de todos los archivos del paquete: sin errores.
- Prueba de 4 minutos a velocidad máxima con eventos: sin crash ni entradas en `error.log`.
  - Original: llegó a diciembre de 1836, pico de 1.747 MB.
  - Corregido: llegó a agosto de 1838, pico de 1.718 MB.
- Las fechas **no sirven para comparar velocidad**: cada partida estuvo pausada distinto tiempo por los eventos.

## Sin resolver o sin verificar

- **Mapa en blanco en multijugador:** no reproducido. Parece estar en el ejecutable.
- **Mejora de rendimiento:** no medida de forma fiable.
- **Rebeldes en late game:** el cambio no se ha probado en partidas largas.
- **Multijugador real:** no probado con varios jugadores.
- El presupuesto de la barra superior no se corrige, porque el cálculo está en el ejecutable: solo se aclara.
