"""
Carga las estadisticas/curiosidades estructuradas para los partidos de 32vos.
Se guardan en datos_previos['curiosidades_secciones'] como lista de
{titulo, items} y el renderer JS las muestra con seccion + bullets.

Uso: python manage.py set_curiosidades_32vos
"""
from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.polla.models import Partido


def _seccion(titulo, *items):
    return {"titulo": titulo, "items": list(items)}


# Alias de nombres para tolerar variaciones entre el fixture original
# (cargar_fixture_mundial) y el oficial (actualizar_fixture_oficial).
ALIAS = {
    "Rep. Dem. Congo": ["República Democrática del Congo", "RD del Congo", "DR Congo"],
    "Estados Unidos": ["EE.UU.", "EEUU", "USA"],
    "Bosnia y Herzegovina": ["Bosnia"],
    "Costa de Marfil": ["Costa Marfil"],
}


def _candidatos(nombre):
    """Devuelve la lista de nombres a probar para encontrar el equipo."""
    nombres = [nombre]
    for canon, variantes in ALIAS.items():
        if nombre == canon:
            nombres.extend(variantes)
        elif nombre in variantes:
            nombres.append(canon)
            nombres.extend(v for v in variantes if v != nombre)
    # mantener orden y deduplicar
    seen = set()
    out = []
    for n in nombres:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


STATS = [
    {
        "local": "Canadá", "visita": "Sudáfrica",
        "secciones": [
            _seccion("⚡ Dato Express",
                "Canadá disputa su primera fase eliminatoria en una Copa del Mundo, mientras que Sudáfrica busca igualar su mejor actuación histórica."),
            _seccion("📚 ¿Sabías que...?",
                "Canadá y Sudáfrica nunca se han enfrentado en una Copa del Mundo.",
                "Sudáfrica fue el primer país africano en organizar un Mundial, en 2010."),
            _seccion("🔥 Jugador a seguir",
                "Jonathan David (Canadá). El delantero canadiense es la principal referencia ofensiva de su selección y uno de los máximos goleadores de su generación."),
            _seccion("🏆 Antecedentes históricos",
                "Canadá logró avanzar por primera vez a una fase eliminatoria mundialista en esta edición.",
                "Sudáfrica nunca ha superado la fase de grupos en una Copa del Mundo, aunque estuvo muy cerca en el Mundial que organizó en 2010."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "Las selecciones africanas suelen mejorar su rendimiento en rondas de eliminación directa, donde el aspecto físico y la intensidad adquieren mayor importancia."),
            _seccion("👀 Lo que pocos están considerando",
                "Para Canadá, este partido representa una oportunidad histórica. La presión por seguir haciendo historia puede convertirse tanto en una motivación como en un factor de ansiedad."),
        ],
    },
    {
        "local": "Brasil", "visita": "Japón",
        "secciones": [
            _seccion("⚡ Dato Express",
                "Brasil nunca ha faltado a una Copa del Mundo; Japón nunca ha faltado a un Mundial desde 1998."),
            _seccion("📚 ¿Sabías que...?",
                "Japón es la selección asiática con más clasificaciones consecutivas a octavos de final en la historia reciente.",
                "Brasil continúa siendo la selección con más victorias en la historia de los Mundiales."),
            _seccion("🔥 Jugador a seguir",
                "Vinícius Júnior (Brasil). Su velocidad y capacidad para desequilibrar pueden marcar diferencias en partidos cerrados."),
            _seccion("🏆 Antecedentes históricos",
                "Brasil conquistó cinco Copas del Mundo (1958, 1962, 1970, 1994 y 2002).",
                "Japón sorprendió al mundo en Catar 2022 derrotando a Alemania y España durante la fase de grupos."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "Japón ha demostrado en los últimos Mundiales que sabe competir especialmente bien contra selecciones europeas y sudamericanas de primer nivel."),
            _seccion("👀 Lo que pocos están considerando",
                "Brasil suele monopolizar la posesión, pero Japón es una de las selecciones más peligrosas cuando recupera el balón y contraataca rápidamente."),
        ],
    },
    {
        "local": "Alemania", "visita": "Paraguay",
        "secciones": [
            _seccion("⚡ Dato Express",
                "Alemania ha disputado más semifinales mundialistas que cualquier otra selección."),
            _seccion("📚 ¿Sabías que...?",
                "Paraguay estuvo invicta durante toda la fase de grupos del Mundial 2010.",
                "Alemania solo ha faltado a dos Copas del Mundo desde 1930."),
            _seccion("🔥 Jugador a seguir",
                "Jamal Musiala (Alemania). Considerado el nuevo líder creativo de la selección alemana."),
            _seccion("🏆 Antecedentes históricos",
                "Alemania es tetracampeona del mundo (1954, 1974, 1990 y 2014).",
                "Paraguay alcanzó los cuartos de final en Sudáfrica 2010, la mejor actuación mundialista de su historia."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "Paraguay suele ser una selección extremadamente incómoda para los favoritos gracias a su disciplina táctica y fortaleza defensiva."),
            _seccion("👀 Lo que pocos están considerando",
                "Si Paraguay logra mantener el partido igualado durante muchos minutos, la presión comenzará a trasladarse completamente al lado alemán."),
        ],
    },
    {
        "local": "Países Bajos", "visita": "Marruecos",
        "secciones": [
            _seccion("⚡ Dato Express",
                "Este enfrentamiento reúne a la selección africana más exitosa del último Mundial y a una de las selecciones europeas más constantes de la historia."),
            _seccion("📚 ¿Sabías que...?",
                "Más de la mitad de la plantilla marroquí nació o se formó futbolísticamente en países europeos.",
                "Países Bajos nunca ha ganado la Copa del Mundo pese a disputar tres finales."),
            _seccion("🔥 Jugador a seguir",
                "Achraf Hakimi (Marruecos). Uno de los mejores laterales del mundo y pieza clave tanto en defensa como en ataque."),
            _seccion("🏆 Antecedentes históricos",
                "Países Bajos fue subcampeón mundial en 1974, 1978 y 2010.",
                "Marruecos hizo historia en Catar 2022 al convertirse en la primera selección africana en alcanzar unas semifinales mundialistas."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "Marruecos ha demostrado que puede competir de igual a igual contra cualquier potencia cuando consigue adelantarse o mantener el marcador equilibrado durante buena parte del partido."),
            _seccion("👀 Lo que pocos están considerando",
                "Aunque Países Bajos parte como favorito, Marruecos ya no juega con el factor sorpresa. Su éxito reciente ha cambiado por completo la percepción internacional sobre esta selección, y hoy es un rival al que nadie subestima."),
        ],
    },
    {
        "local": "Francia", "visita": "Suecia",
        "secciones": [
            _seccion("⚡ Dato Express",
                "Francia y Suecia suman tres títulos mundiales entre ambas selecciones, aunque todos pertenecen a Francia."),
            _seccion("📚 ¿Sabías que...?",
                "Suecia organizó el Mundial de 1958, donde alcanzó la única final de su historia.",
                "Francia ha disputado 4 finales mundialistas desde 1998, más que cualquier otra selección en ese período."),
            _seccion("🔥 Jugador a seguir",
                "Kylian Mbappé (Francia). Con apenas unos años de carrera mundialista, ya figura entre los máximos goleadores históricos de las Copas del Mundo."),
            _seccion("🏆 Antecedentes históricos",
                "Francia fue campeona del mundo en 1998 y 2018, además de subcampeona en 2006 y 2022.",
                "Suecia terminó subcampeona en 1958 y obtuvo el tercer lugar en 1994, siendo una de las selecciones europeas con mejor historia mundialista sin haber conquistado el título."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "Suecia ha demostrado históricamente que puede complicar a selecciones favoritas gracias a su juego aéreo y fortaleza física, especialmente en partidos de eliminación directa."),
            _seccion("👀 Lo que pocos están considerando",
                "Francia suele asumir el protagonismo con la posesión, pero Suecia se siente cómoda defendiendo en bloque y aprovechando el balón parado, una de sus mayores fortalezas."),
        ],
    },
    {
        "local": "Costa de Marfil", "visita": "Noruega",
        "secciones": [
            _seccion("⚡ Dato Express",
                "Ambas selecciones regresan a una fase eliminatoria mundialista después de varios años de ausencia."),
            _seccion("📚 ¿Sabías que...?",
                "Noruega nunca ha perdido un partido oficial contra Brasil (2 victorias y 2 empates), un dato único entre las selecciones con varios enfrentamientos.",
                "Costa de Marfil ha producido algunos de los mejores futbolistas africanos del siglo XXI, como Didier Drogba y Yaya Touré."),
            _seccion("🔥 Jugador a seguir",
                "Erling Haaland (Noruega). Uno de los delanteros más temidos del mundo y principal arma ofensiva noruega."),
            _seccion("🏆 Antecedentes históricos",
                "Noruega alcanzó los octavos de final en Francia 1998 tras vencer a Brasil en la fase de grupos.",
                "Costa de Marfil disputó tres Mundiales consecutivos (2006, 2010 y 2014), pero nunca logró superar la fase de grupos."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "Costa de Marfil suele crecer en partidos donde no parte como favorita y cuenta con una de las selecciones físicamente más fuertes del torneo."),
            _seccion("👀 Lo que pocos están considerando",
                "Toda la atención estará puesta en Haaland, pero Costa de Marfil destaca por neutralizar delanteros mediante un juego físico y defensores muy rápidos."),
        ],
    },
    {
        "local": "Estados Unidos", "visita": "Bosnia y Herzegovina",
        "secciones": [
            _seccion("⚡ Dato Express",
                "Estados Unidos busca consolidarse como una de las selecciones emergentes del fútbol mundial, mientras Bosnia intenta alcanzar por primera vez los cuartos de final."),
            _seccion("📚 ¿Sabías que...?",
                "Bosnia y Herzegovina consiguió su primera victoria mundialista en Brasil 2014 al derrotar a Irán.",
                "Estados Unidos alcanzó las semifinales del primer Mundial de la historia, en 1930."),
            _seccion("🔥 Jugador a seguir",
                "Christian Pulisic (Estados Unidos). Capitán, líder y máxima figura del fútbol estadounidense."),
            _seccion("🏆 Antecedentes históricos",
                "Estados Unidos alcanzó los cuartos de final en Corea-Japón 2002, eliminando a México en octavos.",
                "Bosnia disputa apenas su segunda Copa del Mundo, lo que convierte cada fase superada en un nuevo récord nacional."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "Bosnia cuenta con una plantilla acostumbrada al fútbol europeo, por lo que la diferencia de experiencia internacional respecto a Estados Unidos es mucho menor de lo que suele pensarse."),
            _seccion("👀 Lo que pocos están considerando",
                "Estados Unidos tendrá el peso de jugar como anfitrión. En eliminatorias, esa presión puede convertirse en un factor tan importante como la calidad futbolística."),
        ],
    },
    {
        "local": "España", "visita": "Austria",
        "secciones": [
            _seccion("⚡ Dato Express",
                "España y Austria fueron campeonas de Europa antes de lograr consolidarse como protagonistas habituales en los Mundiales."),
            _seccion("📚 ¿Sabías que...?",
                "Austria terminó entre las cuatro mejores selecciones del mundo en dos ocasiones (1934 y 1954).",
                "España necesitó más de 80 años desde su primer Mundial para conquistar finalmente el título en Sudáfrica 2010."),
            _seccion("🔥 Jugador a seguir",
                "Lamine Yamal (España). Una de las mayores promesas del fútbol mundial y pieza clave del ataque español."),
            _seccion("🏆 Antecedentes históricos",
                "España fue campeona del mundo en 2010, desplegando uno de los estilos de juego más dominantes de la historia.",
                "Austria obtuvo el tercer lugar en Suiza 1954, su mejor resultado mundialista."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "Austria ha evolucionado notablemente en los últimos años y suele competir muy bien contra selecciones de primer nivel gracias a su organización táctica y presión alta."),
            _seccion("👀 Lo que pocos están considerando",
                "España suele dominar la posesión del balón, pero Austria se siente cómoda cediendo la iniciativa y atacando con velocidad. Si el partido se rompe en transiciones, el favoritismo español podría reducirse considerablemente."),
        ],
    },
    {
        "local": "Suiza", "visita": "Argelia",
        "secciones": [
            _seccion("⚡ Dato Express",
                "Suiza y Argelia son dos selecciones conocidas por complicar a los favoritos en las Copas del Mundo."),
            _seccion("📚 ¿Sabías que...?",
                "Suiza ostenta uno de los récords defensivos más impresionantes en la historia de los Mundiales: pasó 559 minutos sin recibir un gol entre Alemania 2006 y Sudáfrica 2010.",
                "Argelia fue la primera selección africana en derrotar al vigente campeón del mundo, al vencer a Alemania Occidental en 1982."),
            _seccion("🔥 Jugador a seguir",
                "Granit Xhaka (Suiza). Capitán, líder del mediocampo y uno de los jugadores con más partidos en la historia de la selección suiza."),
            _seccion("🏆 Antecedentes históricos",
                "Suiza alcanzó los cuartos de final en los Mundiales de 1934, 1938 y 1954.",
                "Argelia estuvo a segundos de eliminar a la futura campeona Alemania en los octavos de final del Mundial 2014, cayendo solo en la prórroga."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "Entre ambas selecciones, la mayoría de sus partidos mundialistas se han decidido por un solo gol de diferencia o en tiempo extra."),
            _seccion("👀 Lo que pocos están considerando",
                "Ninguna selección suele asumir demasiados riesgos desde el inicio. Si el marcador permanece igualado durante muchos minutos, el encuentro puede convertirse en un auténtico duelo de paciencia."),
        ],
    },
    {
        "local": "México", "visita": "Ecuador",
        "secciones": [
            _seccion("⚡ Dato Express",
                "México ha disputado más del doble de Copas del Mundo que Ecuador."),
            _seccion("📚 ¿Sabías que...?",
                "Ecuador nunca ha perdido un partido mundialista frente a otra selección sudamericana.",
                "México es el único país que ha organizado dos Copas del Mundo masculinas completas (1970 y 1986) y será el primero en albergar partidos en tres ediciones (1970, 1986 y 2026)."),
            _seccion("🔥 Jugador a seguir",
                "Moisés Caicedo (Ecuador). El mediocampista ecuatoriano domina tanto la recuperación como la salida del balón y es el motor del equipo."),
            _seccion("🏆 Antecedentes históricos",
                "México alcanzó los cuartos de final en los Mundiales de 1970 y 1986, ambos disputados como anfitrión.",
                "Ecuador logró su mejor actuación histórica en Alemania 2006, llegando a los octavos de final."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "Ecuador suele destacar por su intensidad física y presión alta, un estilo que históricamente ha complicado a México."),
            _seccion("👀 Lo que pocos están considerando",
                "Aunque México cuenta con una mayor tradición mundialista, la actual generación ecuatoriana está formada por numerosos jugadores consolidados en las principales ligas europeas."),
        ],
    },
    {
        "local": "Inglaterra", "visita": "Rep. Dem. Congo",
        "secciones": [
            _seccion("⚡ Dato Express",
                "Inglaterra ha disputado más de 70 partidos en Copas del Mundo; la RD del Congo apenas disputa su segunda participación mundialista."),
            _seccion("📚 ¿Sabías que...?",
                "La República Democrática del Congo jugó el Mundial de 1974 bajo el nombre de Zaire.",
                "Inglaterra solo ha ganado una Copa del Mundo, a pesar de ser considerada una de las grandes potencias históricas del fútbol."),
            _seccion("🔥 Jugador a seguir",
                "Jude Bellingham (Inglaterra). El mediocampista inglés es uno de los jugadores más completos y determinantes del fútbol actual."),
            _seccion("🏆 Antecedentes históricos",
                "Inglaterra fue campeona del mundo en 1966 jugando como local.",
                "Zaire (actual RD del Congo) fue la primera selección del África subsahariana en disputar una Copa del Mundo."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "La mayoría de los futbolistas congoleños militan en ligas europeas, lo que reduce considerablemente la diferencia de experiencia internacional respecto a Inglaterra."),
            _seccion("👀 Lo que pocos están considerando",
                "La presión recaerá totalmente sobre Inglaterra. La RD del Congo puede afrontar el partido con libertad y aprovechar cualquier exceso de confianza del favorito."),
        ],
    },
    {
        "local": "Bélgica", "visita": "Senegal",
        "secciones": [
            _seccion("⚡ Dato Express",
                "Bélgica y Senegal poseen dos de las generaciones más talentosas que han tenido sus respectivos países."),
            _seccion("📚 ¿Sabías que...?",
                "Senegal eliminó a Francia, vigente campeona del mundo, en el partido inaugural del Mundial 2002.",
                "Bélgica terminó tercera en Rusia 2018, su mejor actuación histórica en una Copa del Mundo."),
            _seccion("🔥 Jugador a seguir",
                "Jérémy Doku (Bélgica). Su velocidad y capacidad de desborde lo convierten en uno de los futbolistas más desequilibrantes del torneo."),
            _seccion("🏆 Antecedentes históricos",
                "Bélgica alcanzó las semifinales en 1986 y obtuvo el tercer puesto en 2018.",
                "Senegal llegó a los cuartos de final en su debut mundialista (2002), igualando el mejor registro histórico de una selección africana hasta ese momento."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "Las selecciones africanas han demostrado históricamente un gran rendimiento frente a equipos europeos en rondas de eliminación directa."),
            _seccion("👀 Lo que pocos están considerando",
                "Este duelo puede definirse más por la velocidad de las transiciones que por el dominio de la posesión. Ambos equipos cuentan con jugadores capaces de cambiar un partido en pocos segundos."),
        ],
    },
    {
        "local": "Portugal", "visita": "Croacia",
        "secciones": [
            _seccion("⚡ Dato Express",
                "Portugal y Croacia nunca han ganado un Mundial, pero entre ambos han disputado una final y dos terceros puestos."),
            _seccion("📚 ¿Sabías que...?",
                "Croacia alcanzó una final mundialista (2018) con una población inferior a los 4 millones de habitantes.",
                "Portugal ganó la Eurocopa 2016, el primer gran título internacional de su historia."),
            _seccion("🔥 Jugador a seguir",
                "Rafael Leão (Portugal). Velocidad, desequilibrio y capacidad de definir en el uno contra uno lo convierten en el principal referente ofensivo portugués."),
            _seccion("🏆 Antecedentes históricos",
                "Portugal terminó tercero en Inglaterra 1966, liderado por Eusébio.",
                "Croacia fue subcampeona del mundo en 2018 y tercera en 1998, consolidándose como una de las selecciones más competitivas del siglo XXI."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "Croacia ha ganado varias eliminatorias mundialistas en prórroga o penales durante las últimas ediciones, demostrando una enorme fortaleza mental en partidos cerrados."),
            _seccion("👀 Lo que pocos están considerando",
                "Aunque Portugal suele tener más talento ofensivo, Croacia acostumbra a controlar el ritmo del partido desde el mediocampo, especialmente en eliminatorias."),
        ],
    },
    {
        "local": "Australia", "visita": "Egipto",
        "secciones": [
            _seccion("⚡ Dato Express",
                "Australia y Egipto representan a dos confederaciones diferentes, pero ambas se caracterizan por su fortaleza física y disciplina táctica."),
            _seccion("📚 ¿Sabías que...?",
                "Egipto es la selección más laureada de la Copa Africana de Naciones, con 7 títulos.",
                "Australia fue campeona de Asia apenas una década después de cambiar de confederación desde Oceanía."),
            _seccion("🔥 Jugador a seguir",
                "Mohamed Salah (Egipto). Uno de los mejores futbolistas africanos de todos los tiempos y gran referente ofensivo de los \"Faraones\"."),
            _seccion("🏆 Antecedentes históricos",
                "Australia alcanzó los octavos de final en 2006 y 2022, sus mejores actuaciones mundialistas.",
                "Egipto disputó su primer Mundial en 1934, siendo una de las primeras selecciones africanas en participar en el torneo."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "Egipto suele recibir muy pocos goles cuando Mohamed Salah está disponible, ya que el equipo adapta su sistema para aprovechar al máximo sus transiciones ofensivas."),
            _seccion("👀 Lo que pocos están considerando",
                "Australia suele crecer en partidos donde no tiene la posesión del balón. Su fortaleza está en el orden colectivo y el juego aéreo."),
        ],
    },
    {
        "local": "Argentina", "visita": "Cabo Verde",
        "secciones": [
            _seccion("⚡ Dato Express",
                "Argentina suma más títulos mundiales que todas las selecciones africanas juntas."),
            _seccion("📚 ¿Sabías que...?",
                "Cabo Verde es el país con menor población en disputar este Mundial.",
                "Argentina ha alcanzado seis finales mundialistas, una cifra solo superada por Alemania."),
            _seccion("🔥 Jugador a seguir",
                "Julián Álvarez (Argentina). Uno de los delanteros más completos del fútbol actual y referente de la nueva generación argentina."),
            _seccion("🏆 Antecedentes históricos",
                "Argentina conquistó las Copas del Mundo de 1978, 1986 y 2022.",
                "Cabo Verde disputa el primer Mundial de su historia, convirtiéndose en una de las grandes revelaciones del torneo."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "Las selecciones debutantes suelen jugar con menos presión y, en ocasiones, protagonizan las mayores sorpresas de los Mundiales."),
            _seccion("👀 Lo que pocos están considerando",
                "Toda la presión estará del lado argentino. Para Cabo Verde, cualquier resultado positivo supondría uno de los mayores hitos de la historia del fútbol africano."),
        ],
    },
    {
        "local": "Colombia", "visita": "Ghana",
        "secciones": [
            _seccion("⚡ Dato Express",
                "Colombia y Ghana alcanzaron por primera vez los cuartos de final de un Mundial con apenas cuatro años de diferencia (2006 y 2014)."),
            _seccion("📚 ¿Sabías que...?",
                "Ghana estuvo a un penal de convertirse en la primera selección africana semifinalista de una Copa del Mundo en 2010.",
                "Colombia terminó invicta la fase de grupos del Mundial 2014 antes de alcanzar los cuartos de final."),
            _seccion("🔥 Jugador a seguir",
                "Luis Díaz (Colombia). Considerado uno de los extremos más explosivos del fútbol mundial y la principal figura colombiana."),
            _seccion("🏆 Antecedentes históricos",
                "Colombia logró su mejor participación en un Mundial al llegar a los cuartos de final en Brasil 2014.",
                "Ghana alcanzó los cuartos de final en Sudáfrica 2010, igualando el mejor registro histórico de una selección africana en ese momento."),
            _seccion("🎯 El dato que puede romper pronósticos",
                "Ghana suele crecer frente a selecciones sudamericanas gracias a su intensidad física y velocidad por las bandas, lo que históricamente ha generado partidos muy igualados."),
            _seccion("👀 Lo que pocos están considerando",
                "Aunque Colombia parte como favorita para muchos aficionados, Ghana posee una generación con amplia experiencia en las principales ligas europeas. La diferencia entre ambas selecciones puede ser mucho menor de lo que indican la historia y el prestigio de cada una."),
        ],
    },
]


def _buscar_partido(local, visita):
    """Busca el partido probando alias y permitiendo invertir local/visita."""
    locales = _candidatos(local)
    visitas = _candidatos(visita)

    # 1) Local/visita en el orden dado
    q = Q()
    for ln in locales:
        for vn in visitas:
            q |= Q(equipo_local__nombre=ln, equipo_visitante__nombre=vn)
    p = Partido.objects.filter(q).first()
    if p:
        return p, False

    # 2) Invertidos (por si el fixture quedó al revés)
    q = Q()
    for ln in locales:
        for vn in visitas:
            q |= Q(equipo_local__nombre=vn, equipo_visitante__nombre=ln)
    p = Partido.objects.filter(q).first()
    if p:
        return p, True

    return None, False


class Command(BaseCommand):
    help = 'Carga stats estructuradas (secciones) para los 12 partidos de 32vos del .txt'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Solo reporta los matches sin guardar nada.'
        )
        parser.add_argument(
            '--sobrescribir', action='store_true',
            help='Sobrescribe curiosidades_secciones aunque ya existan.'
        )

    def handle(self, *args, **options):
        dry = options['dry_run']
        sobre = options['sobrescribir']

        ok, no_encontrado, ya_existian, saltados_invertidos = 0, 0, 0, 0

        for item in STATS:
            local = item['local']
            visita = item['visita']
            partido, invertido = _buscar_partido(local, visita)

            if not partido:
                self.stdout.write(self.style.WARNING(
                    f'  [x] No encontrado: {local} vs {visita}'
                ))
                no_encontrado += 1
                continue

            etiqueta = f'#{partido.numero} {partido.equipo_local.nombre} vs {partido.equipo_visitante.nombre}'
            if invertido:
                etiqueta += '  [encontrado invertido]'

            datos = partido.datos_previos or {}
            if datos.get('curiosidades_secciones') and not sobre:
                self.stdout.write(self.style.NOTICE(
                    f'  [=] Ya tenia secciones: {etiqueta}  (usa --sobrescribir para forzar)'
                ))
                ya_existian += 1
                continue

            if dry:
                self.stdout.write(self.style.SUCCESS(
                    f'  [dry] OK: {etiqueta} - {len(item["secciones"])} secciones'
                ))
            else:
                datos['curiosidades_secciones'] = item['secciones']
                partido.datos_previos = datos
                partido.save(update_fields=['datos_previos'])
                self.stdout.write(self.style.SUCCESS(
                    f'  [ok] {etiqueta} - {len(item["secciones"])} secciones'
                ))
            ok += 1

        total = len(STATS)
        self.stdout.write('')
        self.stdout.write(f'Resumen: {ok}/{total} cargados · {ya_existian} ya existían · {no_encontrado} no encontrados')
        if no_encontrado:
            self.stdout.write(self.style.WARNING(
                'Para los no encontrados: revisa que los partidos de 32vos estén creados y que '
                'los nombres de equipos coincidan con la DB (mira el bloque ALIAS de este comando).'
            ))
