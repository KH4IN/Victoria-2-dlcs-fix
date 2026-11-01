# Correcciones de Universal Project Mod 2.05

Este repositorio **no contiene archivos del mod ni del juego**. `upm_fix.py` corrige UPM en tu propia copia.

## Cómo se aplica

1. Corrige el juego base con [`juego-base/base_fix.py`](../juego-base/).
2. Haz una copia de la carpeta del juego e instala en ella UPM sin tocar.
3. Ejecuta:

```bash
python -I upm/upm_fix.py "<copia>/mod/UPM" "<copia>" registro.txt
```

Después elige **Universal Project Mod** en el launcher. El código del menú con UPM corregido es `DWUE`. Aplica el script a un UPM sin tocar: si ya está corregido, se niega a repetirlo.

## Parche descargable

La [versión de prueba de UPM](https://github.com/KH4IN/Victoria-2-dlcs-fix/releases/tag/upm-prueba-1) hace lo mismo sin instalar Python, con doble clic. Sale de `crear_parche_upm.py`, que compara UPM sin tocar con UPM corregido:

```bash
python -I upm/crear_parche_upm.py "<UPM_sin_tocar>" "<copia>/mod/UPM" "<copia>" parche.txt
```

| Dato | Valor |
|---|---|
| Archivos | 2.110 cambiados, 8 nuevos y 5 retirados |
| Contenido | 1 MB de diferencias, frente a los 689 MB del mod |
| Archivos casi enteros | 48 de localización, 78 KB en total; solo `zz_correcciones.csv` es nuevo |

Los archivos nuevos se crean a partir de los del juego o del mod, y los 5 retirados se guardan en `_copia_antes_de_corregir_UPM`. Se comprobó sobre `UPM.zip` sin tocar: el resultado es idéntico byte a byte a la copia corregida, y se niega a actuar si falta corregir el juego base o si un archivo no coincide.

## El límite del late game

| Prueba | Resultado |
|---|---|
| Partidos políticos tras 2000, UPM sin corregir | Solo 1 de 1.354 países conservaba partidos activos |
| Partidos políticos tras 2000, UPM corregido | Los 1.364 países existentes los conservan |
| Población mundial multiplicada hasta 10.400 millones | Sin crash, sin cifras negativas y con elecciones |
| Dinero multiplicado por 1.000 | Sin crash ni cifras negativas |
| Número de pops multiplicado hasta unos 97.000 | Sin crash; unos 3,8 KB de memoria por pop |
| Partida guardada adelantada a 2150 | Sigue sin errores en 2151 |
| Partida guardada adelantada a noviembre de 2250 | Llega a la pantalla normal de fin de partida en 2251 |

La causa confirmada es que 9.916 partidos caducaban exactamente el 1 de enero de 2000, aunque UPM llega a 2250. Ahora caducan en 2300.

El límite que no se puede quitar es la memoria: `v2game.exe` es de 32 bits y tiene un tope de 4 GB. UPM usa 2,9 GB en una partida normal, así que el techo estimado está en unos 300.000 pops. Es una extrapolación a partir de 97.000, no una medida. Reducir `ASSIMILATION_SCALE` frena la división de pops, pero no elimina el techo.

## Qué corrige

| Área | Cambio |
|---|---|
| Partidos | 9.868 caducidades de 2000 pasan a 2300 en el script; 140 `ruling_party` corregidos y 1.089 fechas de inicio adelantadas para que ningún país empiece sin partido |
| Textos dañados | `text.csv` pasó por una herramienta en UTF-8: 928 textos con `?` y unas 650 filas descuadradas, que ponían italiano en la columna española. 1.518 filas repuestas desde el juego base |
| Textos vacíos | 915 textos sin español rellenados, incluidos los nombres de 44 países que salían en blanco |
| Codificación | 66 scripts en UTF-8 convertidos a ANSI, 39 archivos con bytes NUL limpiados y 4 `.csv` en UTF-8 convertidos |
| Tecnologías | 23 tecnologías renombradas por el mod seguían citadas con el nombre antiguo en 171 archivos |
| Historia | Llave que faltaba en `PuppetStates.txt`, culturas, religiones y gobiernos inexistentes, 23 OOB que no existían y 6 eventos duplicados |
| Mapa | 12 provincias nuevas sin clima y las provincias 1396 y 1397 con dos historias |
| Sobrantes | `map.zip`, `settings.txt` y la historia de una etiqueta no declarada |
| Rendimiento | 108 condiciones reordenadas para evaluar antes lo barato, con la misma lógica |

## Cambios de jugabilidad

Estos sí alteran la partida. Están en `upm_fix.py`, en la lista `DEFS`, por si se quiere retocar alguno:

| Valor | UPM | Corregido | Motivo |
|---|---|---|---|
| `REDUCTION_AFTER_RISEING` | 0 | 2 | Un pop no podía repetir revuelta sin perder militancia |
| `MIL_TO_JOIN_RISING` | 8 | 8,5 | Menos rebeldes en late game |
| `MIL_TO_AUTORISE` | 9 | 9,5 | Menos rebeldes en late game |
| `MIL_REQUIRE_REFORM` | 0,2 | 0,15 | Menos rebeldes en late game |
| `MIL_WAR_EXHAUSTION` | 0,005 | 0,003 | Menos rebeldes en late game |
| `REBEL_OCCUPATION_STRENGTH_BONUS` | 0,01 | 0,005 | Menos rebeldes en late game |
| `ASSIMILATION_SCALE` | 0,02 | 0,008 | UPM la multiplicó por 5: cada asimilación parte pops y gasta memoria |
| `SOLDIER_FRACTION` | 0,045 | 0,035 | Ejércitos de la IA más contenidos |
| `MAX_FLEETS` | 20 | 10 | Flotas de la IA más contenidas |

## Pruebas realizadas

- Las 11 fechas de inicio, de 1492 a 2000: arrancan y aguantan más de un minuto a velocidad máxima, sin entradas en `error.log`.
- 12 minutos desde 2000: llegó a 2004 sin crash, con un pico de 2.949 MB. Sin corregir llegó a la misma fecha con 2.929 MB.
- Sin corregir había 237 rebeldes y 8.433 regimientos en 2005; corregido, 134 y 6.001 en 2004. Son fechas distintas, así que es una comparación aproximada.

## Sin resolver o sin verificar

- **Partida completa:** no se ha jugado de principio a fin. El late game se ha simulado con partidas de 2000 y partidas guardadas modificadas.
- **Velocidad:** no medida de forma fiable, porque las pausas por eventos distorsionan las pruebas.
- **Multijugador:** no probado.
- Los textos con `?` en otros idiomas no se han reparado si la fila no afectaba al español.
