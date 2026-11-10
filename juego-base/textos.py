"""Textos corregidos del juego y limpieza de la columna espanola, comunes a base_fix.py y upm_fix.py."""
import re

SPANISH = 5  # columna del espanol en los .csv

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


def limpiar(es, ancha, fila):
    """Quita lo que deja una hoja de calculo: el juego muestra las comillas de CSV y corta en los ';'."""
    if es.startswith(b'"') and ancha:
        es += b',' + fila.pop(SPANISH + 1)
    if es.startswith(b'"') and es.endswith(b'"') and len(es) > 1:
        es = es[1:-1]
    es = es.replace(b'""', b'"').replace(b'$STR_0_0$', b'$STRING_0_0$')
    return re.sub(rb'(?<=\S)(?<!\\n) {2,}(?=\S)', b' ', es)
