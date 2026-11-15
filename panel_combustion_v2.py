"""
Panel de investigación v4.1: "Llama en caída libre" (NASA Space Apps)
Seguridad contra incendios en exploración espacial con datos de combustión
en microgravedad (repositorio PSI de la NASA y documentos oficiales).

Ejecutar:
    pip install streamlit pandas altair
    pip install anthropic          # opcional (extractor y preguntas con IA)
    streamlit run panel_combustion_v4.py
"""

import json
import os
import re
import sys

try:
    import pandas as pd
    import streamlit as st
except ImportError as _e:
    print("\nFalta una librería:", _e)
    print("Instálala con:  python -m pip install streamlit pandas altair anthropic\n")
    sys.exit(1)

try:
    import altair as alt
except ImportError:
    alt = None

# ---------------------------------------------------------------------------
# 1. CONSTANTES DEL RETO
# ---------------------------------------------------------------------------
ENTORNOS = ["Nave espacial", "Estación espacial", "Base lunar",
            "Rover presurizado", "Base marciana"]

O2_TIERRA = 21.0
P_TIERRA_PSI = 14.7
P_TRAJE_PSI = 4.3
O2_LUNA_MIN = 30.0
P_LUNA_MAX_PSI = 10.2
PSI_POR_ATM = 14.696

# ---------------------------------------------------------------------------
# 2. FUENTES
# ---------------------------------------------------------------------------
U = "https://www.nasa.gov/wp-content/uploads/2025/07/"
FUENTES = {
    "PSI": ("PSI Data Repository: Combustion Science",
            "https://psi.nasa.gov/physci/repo/search?q=combustion"),
    "CS": ("NASA Combustion Science",
           "https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/"),
    "BASS": ("Ficha BASS / BASS-II / BASS-M", U + "burning-and-suppression-of-solids-bass.pdf"),
    "FLEX": ("Ficha FLEX / FLEX-2", U + "flame-extinguishment-experiment-flex.pdf"),
    "SAME": ("Ficha SAME / SAME-R", U + "smoke-aerosol-measurement-experiment-same.pdf"),
    "SAFFIRE": ("Ficha Saffire", U + "spacecraft-fire-safety-demonstration-saffire.pdf"),
    "ACME": ("Ficha ACME", U + "advanced-combustion-via-microgravity-experiments-acme.pdf"),
    "GUIA": ("A Researcher's Guide to ISS Combustion Science (NP-2015-10-034-JSC)",
             "https://www.nasa.gov/missions/station/a-researchers-guide-to-combustion-science/"),
    "VIDEO": ("ScienceCasts: The Power of Studying Combustion on the ISS",
              "https://www.youtube.com/watch?v=W1oXykoz9zg"),
    "APOLO1": ("Apollo 1", "https://sma.nasa.gov/sma-disciplines/accllp/apollo-1"),
    "APOLO13": ("Apollo 13", "https://sma.nasa.gov/sma-disciplines/accllp/apollo-13"),
    "MIR": ("25 Years Ago: Fire Aboard Space Station Mir",
            "https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/"),
    "TANQUES": ("Fireman's Air Tanks", "https://spinoff.nasa.gov/node/9582"),
    "DETECTOR": ("Fire Detector (1978)", "https://spinoff.nasa.gov/node/9407"),
    "ROPA": ("New Technology for the Fire Attire - Project FIRES (1982)", "https://spinoff.nasa.gov/node/9918"),
}

# ---------------------------------------------------------------------------
# 3. BASE DE CONOCIMIENTO (Datos completos cruzados con Guía ISS 2015 y fichas)
#    o2 en % molar; p en atm; flujo en cm/s
# ---------------------------------------------------------------------------
CAMPOS = ["id", "nombre", "categoria", "estado", "plataforma", "combustible",
          "forma_muestra", "n_muestras", "o2_min", "o2_max", "p_min", "p_max",
          "flujo_min", "flujo_max", "variables", "sensores", "objetivo",
          "hallazgos", "aplic_espacio", "aplic_tierra", "tags", "fuente"]


def E(**kw):
    base = {c: "No especificado en fuente" for c in CAMPOS}
    for num_col in ("n_muestras", "o2_min", "o2_max", "p_min", "p_max", "flujo_min", "flujo_max"):
        base[num_col] = None
    base["tags"] = set()
    base.update(kw)
    return base


EXPERIMENTOS = [
    E(id="BASS", nombre="Burning and Suppression of Solids",
      categoria="Prevención + Supresión", estado="Archivado (2012-2015)",
      plataforma="MSG (ducto de flujo SPICE modificado)",
      combustible="Sólidos: telas delgadas (SIBAL algodón/fibra de vidrio, Nomex, Ultem), PMMA, fibra de vidrio con cera, velas (parafina, 'Japan wax')",
      forma_muestra="Planas 12 cm x 1-2 cm; esferas PMMA de 1 y 2 cm; velas en tubo cerámico 6 mm x 25 mm",
      n_muestras=41, o2_min=17.0, o2_max=21.0, p_min=1.0, p_max=1.0, flujo_min=0.0, flujo_max=50.0,
      variables="O2: aire ISS (21 %) diluido con N2 hasta 17 % (Guía p. 19); flujo de ventilación 0-30 cm/s (hasta 50 cm/s en ducto); caudal de N2 supresor (0-500 cc/min)",
      sensores="Anemómetro, radiómetro, cámara digital fija y video de alta resolución",
      objetivo="Probar que con ventilación de cabina los materiales arden igual o mejor en microgravedad que en 1 g y guiar estrategias de extinción con N2 (precursor de SoFIE).",
      hallazgos="La prueba terrestre NASA-STD-6001 Test 1 no es conservadora: materiales arden con menos O2 en 0 g (ej. esfera PMMA de 2 cm a 17 % O2 y 12 cm/s, Guía Fig. 11). El chorro local de N2 arrastra aire y puede fortalecer la llama en vez de apagarla (Guía pp. 21-22, 31).",
      aplic_espacio="Redefine los criterios de selección de materiales y protocolos de extinción en naves.",
      aplic_tierra="Valida modelos computacionales de propagación de llama en edificios e incendios forestales.",
      tags={"solidos", "supresion", "prevencion", "flujo_variable", "modelado", "espacial_directo"},
      fuente="BASS"),

    E(id="BASS-II", nombre="Burning and Suppression of Solids II",
      categoria="Prevención (inflamabilidad)", estado="Archivado",
      plataforma="MSG (hardware SPICE modificado, presión ISS 1 atm)",
      combustible="Sólidos: películas y láminas de acrílico (PMMA), tela SIBAL, varillas de acrílico, sección de esfera acrílica",
      forma_muestra="Planas 10 cm x 1-2 cm; varillas; sección de esfera grande",
      n_muestras=100, o2_min=17.0, o2_max=21.0, p_min=1.0, p_max=1.0, flujo_min=0.0, flujo_max=50.0,
      variables="O2 ambiente (17-21 % en MSG con dilución N2); velocidad de ventilación (0-50 cm/s); espesor y geometría del combustible; vitiación con N2 (hasta 500 cc/min)",
      sensores="Anemómetro, radiómetro, video y fotografía digital",
      objetivo="Identificar el peor caso de inflamabilidad en naves y compararlo con la prueba terrestre de combustión ascendente.",
      hallazgos="Se obtuvieron tasas de propagación en combustibles delgados y gruesos y una fórmula de transición entre ambos; se calcularon completitud de combustión, calor liberado y razón de equivalencia global.",
      aplic_espacio="Mejora la selección de materiales seguros y tácticas de combate de incendios en misiones futuras.",
      aplic_tierra="Modelos validados aplicables a incendios forestales y estructurales.",
      tags={"solidos", "prevencion", "o2_variable", "flujo_variable", "modelado", "espacial_directo"},
      fuente="BASS"),

    E(id="BASS-M", nombre="Burning and Suppression of Solids - Milliken",
      categoria="Prevención (retardantes)", estado="Archivado",
      plataforma="MSG (hardware SPICE modificado, presión ISS 1 atm)",
      combustible="Textiles de algodón tratados con retardantes de llama (10 tratados + control)",
      forma_muestra="Tiras textiles planas en portamuestras estándar BASS",
      n_muestras=44, o2_min=17.0, o2_max=21.0, p_min=1.0, p_max=1.0, flujo_min=5.0, flujo_max=50.0,
      variables="Composición química del retardante textil; velocidad de flujo de aire (5-50 cm/s)",
      sensores="Anemómetro, radiómetro, video y fotografía",
      objetivo="Evaluar si los textiles retardantes se autoextinguen en microgravedad frente a su comportamiento en Tierra.",
      hallazgos="Permitió contrastar la eficacia real de tratamientos ignífugos comerciales bajo flujo convectivo forzado en 0 g.",
      aplic_espacio="Actualiza los procedimientos de certificación de vestimenta y telas para tripulación.",
      aplic_tierra="Aporta datos fundamentales a la industria de textiles ignífugos terrestres.",
      tags={"solidos", "prevencion", "flujo_variable", "espacial_directo"},
      fuente="BASS"),

    E(id="Saffire-I/II/III", nombre="Spacecraft Fire Safety Demonstration I-III",
      categoria="Prevención (gran escala)", estado="Archivado",
      plataforma="Vehículo de carga Cygnus tras desacoplarse de la ISS (ignición remota)",
      combustible="Sólidos a gran escala: mezcla algodón-fibra de vidrio (SIBAL), Nomex, acrílico PMMA (ventanas)",
      forma_muestra="Saffire-I/III: muestra grande de 0,4 m x 1,0 m en ducto; Saffire-II: 9 muestras múltiples",
      n_muestras=11, o2_min=21.0, o2_max=21.0, p_min=1.0, p_max=1.0, flujo_min=5.0, flujo_max=30.0,
      variables="Velocidad de flujo en ducto (bajo en Saffire-I vs. alto en Saffire-III); geometría y espesor de muestra",
      sensores="Radiómetros, termopares, sensores de O2/CO2, cámaras de video y presión",
      objetivo="Estudiar el crecimiento de llama a gran escala (imposible dentro de la ISS) y los límites de inflamabilidad reales en naves.",
      hallazgos="Demostró la propagación de incendios a escala real de cabina en microgravedad y validó modelos de crecimiento de fuego en vehículos.",
      aplic_espacio="Define protocolos de emergencia cuando la tripulación no puede evacuar la nave.",
      aplic_tierra="Modelos de propagación de incendios en compartimentos cerrados y túneles.",
      tags={"solidos", "prevencion", "gran_escala", "flujo_variable", "espacial_directo"},
      fuente="SAFFIRE"),

    E(id="Saffire-IV/V/VI", nombre="Spacecraft Fire Safety Demonstration IV-VI",
      categoria="Prevención + Detección (gran escala)", estado="Archivado",
      plataforma="Vehículo de carga Cygnus tras desacoplarse de la ISS",
      combustible="Materiales de Saffire-II; tela SIBAL (75 % algodón / 25 % fibra de vidrio), PMMA",
      forma_muestra="Muestras de gran formato en ducto de flujo instrumentado",
      n_muestras=12, o2_min=21.0, o2_max=30.0, p_min=0.69, p_max=1.0, flujo_min=5.0, flujo_max=30.0,
      variables="Presión reducida (~10.2 psi / 0.69 atm) y O2 enriquecido (hasta ~30 % O2, atmósferas de exploración); detección y limpieza posincendio",
      sensores="Detectores de humo, analizadores de gases (CO, CO2, HF, HCN), radiómetros, termopares y cámaras",
      objetivo="Examinar el crecimiento del fuego, la detección y la limpieza de productos tóxicos en las atmósferas previstas para exploración lunar y marciana.",
      hallazgos="Proporcionó la única validación a gran escala en vuelo espacial bajo condiciones de exploración (baja presión / alto O2) y evaluó sistemas de filtración posincendio.",
      aplic_espacio="Base directa para el diseño de seguridad contra incendios en hábitats lunares y naves Orion/Gateway.",
      aplic_tierra="Sistemas avanzados de filtración y monitoreo de gases tóxicos tras incendios.",
      tags={"solidos", "prevencion", "deteccion", "gran_escala", "o2_variable",
            "presion_variable", "alto_o2", "espacial_directo"},
      fuente="SAFFIRE"),

    E(id="SAME", nombre="Smoke Aerosol Measurement Experiment",
      categoria="Detección", estado="Archivado (2007)",
      plataforma="MSG en la ISS (Expedición 15, aire nominal ISS)",
      combustible="Humo de sobrecalentamiento: Teflon, Kapton, goma de silicona, celulosa y dibutil-ftalato sobre mecha",
      forma_muestra="Muestras calentadas en celda de generación de humo dentro de MSG",
      n_muestras=30, o2_min=21.0, o2_max=21.0, p_min=1.0, p_max=1.0, flujo_min=0.0, flujo_max=15.0,
      variables="Flujo de aire; temperatura de calentamiento; tiempo de envejecimiento del humo",
      sensores="Detectores de ionización (Shuttle) y fotoeléctricos/dispersión de luz (ISS); medidores de distribución de tamaño de partículas",
      objetivo="Medir tamaño y distribución de partículas de humo en 0 g y evaluar los detectores de la ISS y del Shuttle.",
      hallazgos="La masa del aerosol se concentra en partículas >1 micra, pero el humo de Teflon es casi todo <1 micra. Todas las muestras producen partículas submicrónicas mejor detectadas por ionización; el objetivo debe ser detectar productos de precombustión antes del hollín (Guía pp. 26, 35).",
      aplic_espacio="Línea base de firmas de humo en microgravedad para diseñar detectores espaciales de próxima generación.",
      aplic_tierra="Detección temprana de humo en submarinos y ambientes cerrados.",
      tags={"deteccion", "modelado", "espacial_directo"}, fuente="SAME"),

    E(id="SAME-R", nombre="Smoke Aerosol Measurement Experiment - Reflight",
      categoria="Detección", estado="Archivado (2010)",
      plataforma="MSG en la ISS (Expedición 24, aire nominal ISS)",
      combustible="Humo de Teflon, Kapton, algodón, goma de silicona y espuma Pyrell",
      forma_muestra="Muestras termo-degradadas en cámara de aerosol",
      n_muestras=25, o2_min=21.0, o2_max=21.0, p_min=1.0, p_max=1.0, flujo_min=0.0, flujo_max=15.0,
      variables="Temperatura de pirólisis, envejecimiento del humo y comparación directa con instrumentos terrestres",
      sensores="Precipitador térmico (TEM), instrumentos de aerosol, detector comercial, detectores ISS/Shuttle y SMPS en tierra",
      objetivo="Contrastar resultados de vuelo con pruebas en tierra y obtener momentos exactos de distribución de tamaños.",
      hallazgos="Confirmó que las partículas de humo en 0 g tienen distribuciones distintas a 1 g debido a la ausencia de convección y mayor tiempo de aglomeración (Guía p. 35).",
      aplic_espacio="Calibración de nuevos detectores para misiones de larga duración donde fallos eléctricos por sobrecalentamiento son más probables.",
      aplic_tierra="Mejora de sensores ópticos y de ionización industriales.",
      tags={"deteccion", "modelado", "espacial_directo"}, fuente="SAME"),

    E(id="DAFT / DAFT-2", nombre="Dust and Aerosol Measurement Feasibility Test",
      categoria="Detección", estado="Archivado",
      plataforma="ISS (cabina presurizada nominal)",
      combustible="Polvo y aerosoles ambientales de cabina (sin combustión)",
      forma_muestra="Muestreo continuo de aire de cabina de la ISS",
      n_muestras=1, o2_min=21.0, o2_max=21.0, p_min=1.0, p_max=1.0, flujo_min=5.0, flujo_max=20.0,
      variables="Concentración de partículas de fondo según actividad de la tripulación",
      sensores="Monitor P-Trak modificado (componente de SAME)",
      objetivo="Comprobar el funcionamiento del instrumento en 0 g y caracterizar el fondo de polvo de la ISS para evitar falsas alarmas (Guía p. 26).",
      hallazgos="Estableció la línea base de aerosoles de fondo en la ISS, indispensable para fijar umbrales de alarma sin falsos disparos.",
      aplic_espacio="Diseño de algoritmos de rechazo de polvo para detectores de humo orbitales.",
      aplic_tierra="Detectores de humo en minería que discriminan polvo mineral de partículas de combustión.",
      tags={"deteccion"}, fuente="GUIA"),

    E(id="FLEX", nombre="Flame Extinguishment Experiment",
      categoria="Supresión", estado="Archivado",
      plataforma="MDCA dentro del CIR (cámara de 100 L en la ISS)",
      combustible="Gotas de combustibles líquidos puros: metanol y n-heptano",
      forma_muestra="Gotas esféricas de 1 a 5 mm (libres o soportadas en fibra)",
      n_muestras=150, o2_min=10.0, o2_max=50.0, p_min=0.5, p_max=1.0, flujo_min=0.0, flujo_max=3.0,
      variables="O2 (10-50 % molar; Guía indica hasta 40 % en MDCA); presión (0.5-1.0 atm); supresores inertes (N2, CO2, helio, xenón hasta 70 %); flujo convectivo lento (ej. 3 cm/s, Guía Fig. 2)",
      sensores="Cámara de color analógica, radiómetro, cámara UV de baja luz, dos cámaras HiBMs",
      objetivo="Cuantificar la eficacia de supresores inertes y determinar el Índice Límite de Oxígeno (LOI) en microgravedad.",
      hallazgos="El límite de inflamabilidad y el LOI son significativamente menores en 0 g que en 1 g: los estándares terrestres de supresores inertes no ofrecen el mismo margen de seguridad. Se descubrieron llamas frías invisibles que persisten tras apagarse la llama visible (Guía pp. 12-13, 33-34, 36).",
      aplic_espacio="Dimensionamiento de agentes extintores inertes y estrategias de despresurización de cabina.",
      aplic_tierra="Modelos cinéticos base para combustibles de aviación y diésel.",
      tags={"supresion", "liquidos", "o2_variable", "presion_variable", "alto_o2", "modelado", "espacial_directo"},
      fuente="FLEX"),

    E(id="FLEX-2", nombre="Flame Extinguishment Experiment 2",
      categoria="Supresión / Fundamental", estado="Archivado",
      plataforma="MDCA dentro del CIR (ISS)",
      combustible="Gotas de combustibles puros (etanol, heptano), mezclas bicomponente y sustitutos de combustibles reales",
      forma_muestra="Gotas de 1 a 5 mm (2-4 mm típicas); gota aislada o pares de gotas",
      n_muestras=180, o2_min=10.0, o2_max=40.0, p_min=0.5, p_max=2.4, flujo_min=0.0, flujo_max=5.0,
      variables="Composición del combustible y diluyentes; presión (hasta 2.4 atm documentadas en Fig. 3 con 30 % O2); flujo subflotante; interacción gota-gota (30-60 pruebas por grupo)",
      sensores="Cámara color, radiómetro, cámara UV, dos cámaras HiBMs",
      objetivo="Extender la combustión de gotas a flujos convectivos lentos, interacción entre gotas, formación de hollín y combustibles prácticos.",
      hallazgos="Caracterizó la propensión al hollín según el diluyente (ej. etanol en 30 % O2 a 2.4 atm, Guía Fig. 3) y la dinámica de llamas frías en mezclas multicomponente (Guía p. 13).",
      aplic_espacio="Predicción del comportamiento de derrames o fugas de fluidos inflamables en naves.",
      aplic_tierra="Validación de modelos de combustión en pulverizadores, turbinas y motores diésel.",
      tags={"supresion", "liquidos", "o2_variable", "presion_variable", "modelado"},
      fuente="FLEX"),

    E(id="CFI (Llamas frías)", nombre="Cool Flames Investigation (CIR / MDCA)",
      categoria="Fundamental / Seguridad", estado="Archivado",
      plataforma="MDCA dentro del CIR (ISS)",
      combustible="Gotas de alcanos grandes (ej. n-heptano) y combustibles líquidos",
      forma_muestra="Gotas esféricas de 2 a 5 mm en ambiente quiescente",
      n_muestras=50, o2_min=15.0, o2_max=40.0, p_min=0.5, p_max=2.0, flujo_min=0.0, flujo_max=1.0,
      variables="Tamaño de gota, presión, concentración de O2 y diluyentes inertes",
      sensores="Cámaras UV de baja luz, radiómetros, cámaras de alta velocidad HiBMs",
      objetivo="Estudiar la transición de llama caliente a llama fría tras la extinción radiativa y el riesgo de reencendido espontáneo.",
      hallazgos="Las llamas frías sostienen la vaporización de la gota tras apagarse la llama visible, formando una nube de vapor combustible invisible al ojo humano que puede reencenderse espontáneamente mucho después (Guía pp. 33-34, 41-42).",
      aplic_espacio="Alerta crítica: apagar la llama visible en un incendio espacial no garantiza la extinción del peligro.",
      aplic_tierra="Cinética de combustión a baja temperatura clave para motores de alta eficiencia HCCI y RCCI.",
      tags={"liquidos", "fundamental", "prevencion"}, fuente="GUIA"),

    E(id="ACME: BRE", nombre="Burning Rate Emulator",
      categoria="Prevención (inflamabilidad por propiedades)", estado="Archivado",
      plataforma="Hardware ACME en el CIR (cámara de 100 L)",
      combustible="Gaseoso (etileno, metano) en quemador poroso plano que emula papel, plástico y alcohol",
      forma_muestra="Quemador poroso plano de superficie controlada",
      n_muestras=60, o2_min=15.0, o2_max=40.0, p_min=0.2, p_max=1.5, flujo_min=0.0, flujo_max=30.0,
      variables="Flujo de combustible retroalimentado según flujo de calor medido y temperatura de superficie; presión y O2 de cámara",
      sensores="Termopar de superficie, dos transductores de flujo de calor, radiómetros, cámaras color y UV",
      objetivo="Entender ignición y extinción de sólidos/líquidos simulados y evaluar si los métodos actuales de prueba sirven en gravedad baja y parcial (Guía p. 15).",
      hallazgos="Permitió medir tasas de quemado estacionarias simulando materiales condensados sin necesidad de reemplazar muestras sólidas.",
      aplic_espacio="Evaluación rápida de criterios de inflamabilidad para hábitats lunares y marcianos.",
      aplic_tierra="Caracterización fundamental de pirolisis y tasa de liberación de calor de materiales.",
      tags={"gases", "atm_quieta", "prevencion", "modelado", "gravedad_parcial_sim", "espacial_directo"},
      fuente="ACME"),

    E(id="ACME: CLD Flame", nombre="Coflow Laminar Diffusion Flame",
      categoria="Fundamental", estado="Archivado",
      plataforma="Hardware ACME en el CIR (ISS)",
      combustible="Metano y etileno diluidos en N2, con coflujo laminar de aire",
      forma_muestra="Chorro de gas laminar coaxial (llamas despegadas / lifted flames)",
      n_muestras=70, o2_min=15.0, o2_max=40.0, p_min=0.5, p_max=2.0, flujo_min=1.0, flujo_max=50.0,
      variables="Velocidad de inyección de combustible y coflujo; dilución del combustible con N2",
      sensores="Cámaras (color, CH*, OH*), pirometría, extinción láser de hollín, radiómetros",
      objetivo="Extender la capacidad predictiva en los extremos de dilución de combustible: llamas muy diluidas cerca de extinción y llamas puras con mucho hollín (Guía p. 16).",
      hallazgos="Las llamas en microgravedad contienen de 5 a 8 veces más hollín; las llamas muy diluidas son más estables y sus límites de dilución se extienden respecto a 1 g.",
      aplic_espacio="Predicción de producción de humo/hollín y estabilidad de llama en sistemas cerrados.",
      aplic_tierra="Submodelos cinéticos y de hollín para turbinas y quemadores industriales.",
      tags={"gases", "fundamental", "modelado"}, fuente="ACME"),

    E(id="ACME: E-FIELD Flames", nombre="Electric-Field Effects on Laminar Diffusion Flames",
      categoria="Fundamental / Gravedad parcial simulada", estado="Archivado",
      plataforma="Hardware ACME en el CIR (ISS)",
      combustible="Gaseoso (llama de coflujo o chorro laminar simple)",
      forma_muestra="Quemador metálico con malla circular superior a distancia fija",
      n_muestras=50, o2_min=18.0, o2_max=35.0, p_min=0.5, p_max=1.5, flujo_min=0.0, flujo_max=30.0,
      variables="Intensidad de campo eléctrico (hasta ±10 kV entre quemador y malla); dilución del combustible (Guía p. 16)",
      sensores="Medición de corriente iónica a través de la llama, tiempo de respuesta eléctrico, cámaras color y UV",
      objetivo="Investigar cómo el transporte de iones y el viento iónico modifican la forma de la llama, límites de inflamabilidad y hollín (simula fuerzas de cuerpo / gravedad parcial).",
      hallazgos="Demostró el control activo de la geometría de llama, transferencia de calor y reducción de emisiones mediante campos eléctricos en ausencia de flotabilidad.",
      aplic_espacio="Análogo experimental de fuerzas de flotabilidad en gravedad parcial y control activo de llamas.",
      aplic_tierra="Quemadores asistidos eléctricamente de ultra bajas emisiones.",
      tags={"gases", "fundamental", "gravedad_parcial_sim"}, fuente="ACME"),

    E(id="ACME: Flame Design", nombre="Flame Design",
      categoria="Fundamental / Alto O2", estado="Archivado",
      plataforma="Hardware ACME en el CIR (ISS)",
      combustible="Etileno o metano inyectados en atmósfera enriquecida en O2 (o llama inversa O2 en combustible)",
      forma_muestra="Llama de difusión esférica sobre quemador esférico poroso (Guía Fig. 6)",
      n_muestras=60, o2_min=21.0, o2_max=50.0, p_min=0.5, p_max=2.0, flujo_min=0.0, flujo_max=10.0,
      variables="Concentración de combustible y enriquecimiento de O2; fracción de mezcla estequiométrica; dirección de flujo (normal vs. inversa)",
      sensores="Radiómetros, cámaras color, UV de baja luz, cámaras HiBMs, cromatógrafo de gases",
      objetivo="Entender el inicio y control del hollín en llamas esféricas enriquecidas con oxígeno para diseñar llamas robustas y libres de hollín (Guía pp. 16-17).",
      hallazgos="Evaluó si la fracción de mezcla estequiométrica caracteriza los límites de hollín e inflamabilidad en llamas no premezcladas.",
      aplic_espacio="Comprensión de combustión en atmósferas enriquecidas en O2 como bases lunares.",
      aplic_tierra="Diseño de quemadores industriales oxicombustibles más limpios y eficientes.",
      tags={"gases", "fundamental", "o2_variable", "alto_o2"}, fuente="ACME"),

    E(id="ACME: s-Flame", nombre="Structure and Response of Spherical Diffusion Flames",
      categoria="Fundamental", estado="Archivado",
      plataforma="Hardware ACME en el CIR (ISS)",
      combustible="Hidrógeno y metano (sin hollín), etileno y propano diluido (con hollín)",
      forma_muestra="Quemador esférico poroso en cámara CIR de 100 L (Guía Fig. 7)",
      n_muestras=65, o2_min=15.0, o2_max=40.0, p_min=0.5, p_max=2.0, flujo_min=0.0, flujo_max=5.0,
      variables="Diluyentes inertes (argón, nitrógeno, helio) en combustible y cámara; número de Lewis crítico",
      sensores="Radiómetros, fotomultiplicadores, cámaras HiBMs, cromatógrafo de gases",
      objetivo="Identificar límites de extinción radiativa y convectiva (números de Damköhler altos y bajos) e inestabilidades pulsantes en llamas esféricas (Guía pp. 17-18).",
      hallazgos="Confirmó la aparición de inestabilidades pulsantes cerca de la extinción cuando la mezcla supera un número de Lewis crítico.",
      aplic_espacio="Validación de criterios de extinción radiativa en ambientes de cabina sin ventilación.",
      aplic_tierra="Referencia unidimensional exacta para validar códigos CFD de combustión.",
      tags={"gases", "fundamental", "modelado"}, fuente="ACME"),

    E(id="ACME: CFI-G", nombre="Cool Flames Investigation with Gases",
      categoria="Fundamental / Alto O2", estado="Archivado",
      plataforma="Hardware ACME en el CIR (ISS)",
      combustible="Gaseoso (propano / alcanos) en cámara con N2; mezcla O2/N2 desde quemador esférico",
      forma_muestra="Quemador esférico poroso (llama inversa de adentro hacia afuera)",
      n_muestras=45, o2_min=21.0, o2_max=85.0, p_min=0.5, p_max=2.0, flujo_min=0.0, flujo_max=5.0,
      variables="Mezcla O2/N2 con hasta 85 % de O2 desde el quemador; presión y dilución",
      sensores="Cámara UV de baja luz, radiómetros, fotomultiplicadores, cromatógrafo de gases",
      objetivo="Observar llamas frías esféricas gaseosas casi estacionarias; contiene las pruebas con mayor concentración de O2 en microgravedad.",
      hallazgos="Aisló la química de llamas frías en fase gaseosa pura sin efectos de evaporación de gotas.",
      aplic_espacio="Datos límite de reactividad a muy altas concentraciones de oxígeno.",
      aplic_tierra="Cinética de baja temperatura para motores avanzados de encendido por compresión.",
      tags={"gases", "fundamental", "alto_o2", "o2_variable"}, fuente="ACME"),

    E(id="SPICE", nombre="Smoke Point In Co-flow Experiment",
      categoria="Fundamental", estado="Archivado (2009)",
      plataforma="MSG en la ISS (su ducto se reutilizó en SLICE y BASS)",
      combustible="Gaseoso: etileno y propano (chorros laminares de difusión)",
      forma_muestra="Boquilla de chorro de gas en ducto con flujo coaxial de aire",
      n_muestras=40, o2_min=21.0, o2_max=21.0, p_min=1.0, p_max=1.0, flujo_min=5.0, flujo_max=30.0,
      variables="Caudal de combustible (transición de punta cerrada sin humo a punta abierta humeante, Guía Fig. 4) y velocidad de coflujo",
      sensores="Cámaras digitales de color y video, radiómetro, medición de flujo",
      objetivo="Determinar el punto de humo en microgravedad como indicador de propensión a emitir hollín y radiación (Guía pp. 13-14).",
      hallazgos="El inicio de emisión de humo en 0 g ocurre a caudales mucho menores que en 1 g y con partículas primarias de hollín más grandes.",
      aplic_espacio="Predicción de generación de humo denso y hollín en incendios de cabina.",
      aplic_tierra="Predicción sencilla de emisiones de hollín en quemadores y motores.",
      tags={"gases", "fundamental", "flujo_variable"}, fuente="GUIA"),

    E(id="SLICE", nombre="Structure & Liftoff in Combustion Experiment",
      categoria="Fundamental", estado="Archivado (2012)",
      plataforma="MSG en la ISS (hardware SPICE, precursor de ACME CLD Flame)",
      combustible="Gaseoso: metano y etileno diluidos en flujo coaxial de aire",
      forma_muestra="Quemador de chorro laminar en ducto de flujo",
      n_muestras=35, o2_min=21.0, o2_max=21.0, p_min=1.0, p_max=1.0, flujo_min=5.0, flujo_max=35.0,
      variables="Velocidad de coflujo de aire (despegue y estabilización de la base de la llama, Guía Fig. 5) y dilución de combustible",
      sensores="Cámaras calibradas de color, radiómetros y medidores de flujo",
      objetivo="Estudiar la estructura de llamas despegadas (lifted flames) para evitar pérdidas de calor al quemador y validar modelos numéricos (Guía pp. 14-15).",
      hallazgos="Proporcionó perfiles térmicos y de estructura en 0 g que permitieron ajustar submodelos de estabilización de llama.",
      aplic_espacio="Comprensión del despegue y soplado de llamas bajo corrientes de ventilación.",
      aplic_tierra="Diseño de quemadores industriales más eficientes y con menos NOx.",
      tags={"gases", "fundamental", "modelado", "flujo_variable"}, fuente="GUIA"),

    E(id="LSP / TGDF / ELF", nombre="Laminar Soot Processes, Turbulent Gas-jet & Enclosed Laminar Flames",
      categoria="Fundamental", estado="Archivado (STS-83, STS-87, STS-94, STS-107)",
      plataforma="Combustion Module (CM), GAS Can y Middeck Glovebox en Transbordador Espacial",
      combustible="Gaseoso: etileno, propano y metano",
      forma_muestra="Chorro laminar en cámara sellada (LSP), chorro con iris inductor de vórtices (TGDF) y ducto cerrado (ELF)",
      n_muestras=60, o2_min=21.0, o2_max=21.0, p_min=1.0, p_max=1.0, flujo_min=0.0, flujo_max=40.0,
      variables="Número de Reynolds del chorro, inducción de vórtices y confinamiento en ducto (Guía p. 13)",
      sensores="Extinción láser de hollín, termopares, cámaras de video y fotografía",
      objetivo="Caracterizar procesos de hollín, interacción llama-vórtice y estabilidad en chorros gaseosos en 0 g.",
      hallazgos="Demostró diferencias notables en altura de llama y dimensión fractal de aglomerados de hollín respecto a 1 g (Guía p. 32).",
      aplic_espacio="Base histórica para el diseño de los experimentos ACME y MSG en la ISS.",
      aplic_tierra="Validación de modelos de turbulencia y formación de hollín.",
      tags={"gases", "fundamental", "modelado"}, fuente="GUIA"),

    E(id="Mist (STS-107)", nombre="Water Mist Fire Suppression",
      categoria="Supresión", estado="Archivado (2003)",
      plataforma="Combustion Module en el transbordador (STS-107)",
      combustible="Llama gaseosa premezclada (propano/aire) propagándose por un tubo con niebla de agua",
      forma_muestra="Tubo de propagación con generador ultrasónico/boquilla de microgotas",
      n_muestras=30, o2_min=18.0, o2_max=25.0, p_min=1.0, p_max=1.0, flujo_min=0.0, flujo_max=20.0,
      variables="Diámetro de gotas de agua, concentración de agua líquida y relación combustible/O2 (Guía p. 26)",
      sensores="Sensores de presión dinámica, fotodiodos de velocidad de llama y cámaras de alta velocidad",
      objetivo="Cuantificar la capacidad de extinción de la niebla de agua en microgravedad para reemplazar sistemas Halon prohibidos.",
      hallazgos="Condujo directamente al diseño y certificación de los extintores portátiles de niebla de agua no tóxicos enviados a la ISS desde diciembre de 2015 para reemplazar unidades de CO2 (Guía p. 26).",
      aplic_espacio="Extintores portátiles seguros y no tóxicos operativos en la ISS.",
      aplic_tierra="Sistemas limpios de supresión por niebla de agua sustitutos de Halon.",
      tags={"supresion", "gases", "espacial_directo", "modelado"}, fuente="GUIA"),

    E(id="Candle Flames (Mir)", nombre="Candle Flames in Non-Buoyant Atmospheres",
      categoria="Fundamental", estado="Archivado (1996-1997)",
      plataforma="Estación Espacial Mir (en contenedor sellado)",
      combustible="Sólido/líquido fundido: vela de parafina estándar",
      forma_muestra="Vela cilíndrica con mecha en atmósfera quiescente",
      n_muestras=15, o2_min=14.0, o2_max=21.0, p_min=1.0, p_max=1.0, flujo_min=0.0, flujo_max=0.0,
      variables="Agotamiento progresivo de O2 en cámara cerrada sin convección (Guía pp. 10, 30, 33)",
      sensores="Cámaras de alta sensibilidad (exposición prolongada), radiómetros y sensores de O2",
      objetivo="Comprobar si una llama de difusión puede sostenerse únicamente por difusión molecular sin flotabilidad.",
      hallazgos="Refutó el mito clásico: la llama esférica azul ardió más de 45 minutos hasta agotar la cera y sobrevivió a concentraciones de O2 más bajas que en la Tierra, presentando oscilaciones previas a la extinción (Guía pp. 30, 33).",
      aplic_espacio="Demostró que apagar la ventilación no apaga inmediatamente un fuego en microgravedad.",
      aplic_tierra="Validación límite de difusión molecular y pérdida radiativa.",
      tags={"solidos", "fundamental", "atm_quieta", "espacial_directo"}, fuente="GUIA"),

    E(id="SOFBALL", nombre="Structure of Flame Balls at Low Lewis-number",
      categoria="Fundamental", estado="Archivado (STS-83, STS-94, STS-107)",
      plataforma="Combustion Module en Transbordador Espacial (1997 y 2003)",
      combustible="Mezclas gaseosas premezcladas muy pobres (H2, CH4 diluidos en O2/N2/CO2/SF6)",
      forma_muestra="Cámara esférica de gran volumen sin flujo (quiescente)",
      n_muestras=45, o2_min=10.0, o2_max=21.0, p_min=0.5, p_max=1.0, flujo_min=0.0, flujo_max=0.0,
      variables="Número de Lewis efectivo (<1), presión y diluyentes con distinta difusividad térmica (Guía pp. 25, 30)",
      sensores="Cámaras CCD intensificadas, radiómetros y sensores de presión",
      objetivo="Verificar la existencia física de bolas de llama estacionarias cerca del límite pobre de inflamabilidad.",
      hallazgos="Produjo las llamas más débiles jamás registradas (~1 W de potencia térmica), ardiendo de forma estable por más de 40 minutos en 0 g.",
      aplic_espacio="Define los límites absolutos de inflamabilidad de mezclas gaseosas pobres en hábitats.",
      aplic_tierra="Inspiró el quemador comercial de ultra bajas emisiones (Ultraclean Low Swirl Combustion, Guía Fig. 15).",
      tags={"fundamental", "gases", "atm_quieta"}, fuente="GUIA"),

    E(id="SCWO / SCWM", nombre="Super-Critical Water Oxidation & Mixture Experiments",
      categoria="Fundamental / Soporte Vital", estado="Archivado (ZGF 2004 / ISS 2010+)",
      plataforma="Zero Gravity Facility (5.2 s) e inserto HTI-R en la ISS (NASA-CNES)",
      combustible="Metanol en agua supercrítica (10 % peso) con aire; mezclas agua-sal Na2SO4",
      forma_muestra="Reactor de 500 mL (ZGF) y celda de fluido de 0.3 cm³ (ISS)",
      n_muestras=20, o2_min=21.0, o2_max=21.0, p_min=220.0, p_max=250.0, flujo_min=0.0, flujo_max=5.0,
      variables="Temperatura (>374 °C) y presión (>22.1 MPa / ~220 atm) por encima del punto crítico del agua (Guía pp. 27-29, 40)",
      sensores="Termopares axiales (A-D), cámaras ópticas de alta resolución y espectrometría",
      objetivo="Evaluar llamas hidrotermales y oxidación en agua supercrítica para reciclaje de residuos en soporte vital de ciclo cerrado.",
      hallazgos="En 0 g desaparece la mezcla convectiva y aparece estratificación térmica con una zona caliente central; las llamas hidrotermales evitan la incrustación de sales en las paredes del reactor.",
      aplic_espacio="Procesamiento de residuos y recuperación de agua en misiones de larga duración a Marte.",
      aplic_tierra="Destrucción limpia de residuos peligrosos sin emisiones atmosféricas.",
      tags={"liquidos", "fundamental", "modelado"}, fuente="GUIA"),

    E(id="SoFIE", nombre="Solid Fuel Ignition and Extinction",
      categoria="Prevención (sólidos en exploración)", estado="En curso / Operativo (CIR ISS)",
      plataforma="Inserto SoFIE en el CIR de la ISS (5 investigaciones integradas)",
      combustible="Plásticos y materiales de nave: PMMA, Delrin (POM), telas y compuestos sólidos",
      forma_muestra="Esferas, láminas planas y canal estrecho con capacidad de encendido, extinción y reencendido múltiple",
      n_muestras=120, o2_min=10.0, o2_max=40.0, p_min=0.2, p_max=1.5, flujo_min=0.0, flujo_max=30.0,
      variables="Atmósferas de exploración (O2 10-40 %, P 0.2-1.5 atm), flujo forzado bajo (0-30 cm/s), flujo de calor radiante externo y espesor (Guía pp. 19, 22-25)",
      sensores="Radiómetros, cámaras color, UV de baja luz, dos cámaras HiBMs, fotomultiplicadores, cromatógrafo de gases",
      objetivo="Caracterizar ignición, propagación y extinción de sólidos en atmósferas de exploración y calibrar el ensayo terrestre de Canal Estrecho (Narrow Channel).",
      hallazgos="El flujo de calor crítico para ignición en microgravedad puede ser hasta la mitad del valor en 1 g debido a la falta de enfriamiento convectivo natural; las llamas a bajo flujo se propagan contra el viento (upstream) (Guía pp. 18, 24).",
      aplic_espacio="Cubre directamente la atmósfera de la Base Lunar (30 % O2, 0.69 atm) para certificar materiales de Artemisa.",
      aplic_tierra="Validación de pruebas de laboratorio en canal estrecho para seguridad contra incendios.",
      tags={"solidos", "prevencion", "o2_variable", "presion_variable", "flujo_variable", "alto_o2", "modelado", "espacial_directo"},
      fuente="GUIA"),

    E(id="FLARE", nombre="Flammability Limits At Reduced-g Experiment",
      categoria="Prevención (modelado internacional)", estado="En curso (ISS - JAXA/NASA)",
      plataforma="Módulo Kibo de la ISS (colaboración JAXA, NASA, ESA, CNES, DLR)",
      combustible="Materiales poliméricos y textiles de naves espaciales",
      forma_muestra="Muestras planas y cilíndricas en túnel de flujo controlado",
      n_muestras=80, o2_min=12.0, o2_max=35.0, p_min=0.5, p_max=1.0, flujo_min=0.0, flujo_max=30.0,
      variables="Concentración límite de O2 (LOC), velocidad de flujo opuesto/concurrente y presión",
      sensores="Cámaras de alta definición, radiómetros y sensores ambientales",
      objetivo="Correlacionar los límites de inflamabilidad entre 1 g y 0 g para predecir el riesgo espacial desde pruebas en Tierra.",
      hallazgos="Establece factores de corrección cuantitativos entre ensayos terrestres y comportamiento orbital.",
      aplic_espacio="Estándar internacional de seguridad de materiales para estaciones comerciales y Gateway.",
      aplic_tierra="Modelos predictivos de inflamabilidad límite.",
      tags={"solidos", "prevencion", "o2_variable", "flujo_variable", "modelado", "espacial_directo"},
      fuente="CS"),

    E(id="FM2 (futuro)", nombre="Flammability of Materials on the Moon",
      categoria="Gravedad parcial", estado="Planificado (Superficie Lunar 1/6 g)",
      plataforma="Módulo de aterrizaje lunar (1/6 g real)",
      combustible="Materiales sólidos representativos de hábitats lunares",
      forma_muestra="Muestras de ensayo de inflamabilidad a escala reducida",
      n_muestras=10, o2_min=30.0, o2_max=34.0, p_min=0.55, p_max=0.70, flujo_min=0.0, flujo_max=15.0,
      variables="Gravedad lunar real (1/6 g) combinada con atmósfera de exploración (O2 ≥30 %, P ≤10.2 psi)",
      sensores="Cámaras ópticas, radiómetros y sensores de temperatura/O2",
      objetivo="Primer experimento de combustión en otro cuerpo planetario para cerrar la brecha entre 0 g y 1 g.",
      hallazgos="En preparación: validará si el peor caso de inflamabilidad ocurre en 0 g o en gravedad parcial lunar (1/6 g).",
      aplic_espacio="Certificación definitiva de seguridad contra incendios para bases lunares permanentes.",
      aplic_tierra="Validación de modelos de flotabilidad en régimen de baja gravedad.",
      tags={"solidos", "gravedad_parcial", "prevencion", "alto_o2", "espacial_directo"},
      fuente="CS"),

    E(id="LUCI (futuro)", nombre="Lunar Combustion Investigation",
      categoria="Gravedad parcial", estado="Planificado (Programa Artemisa)",
      plataforma="Plataforma lunar / vuelo de gravedad parcial",
      combustible="Sólidos y materiales de cabina",
      forma_muestra="Muestras instrumentadas de propagación de llama",
      n_muestras=12, o2_min=30.0, o2_max=36.0, p_min=0.55, p_max=0.70, flujo_min=0.0, flujo_max=20.0,
      variables="Gravedad lunar (1/6 g), enriquecimiento de oxígeno y flujo de ventilación",
      sensores="Cámaras, termopares y sensores de flujo",
      objetivo="Medir tasas de propagación de llama y extinción en gravedad parcial lunar.",
      hallazgos="En fase de diseño para cubrir el vacío de datos experimentales a 1/6 g.",
      aplic_espacio="Diseño de sistemas de detección y supresión para hábitats lunares y rovers presurizados.",
      aplic_tierra="Modelado físico de convección mixta.",
      tags={"solidos", "gravedad_parcial", "prevencion", "alto_o2", "espacial_directo"},
      fuente="PSI"),
]

# ---------------------------------------------------------------------------
# 3b. INCIDENTES, MITOS, APLICACIONES E INSTALACIONES
# ---------------------------------------------------------------------------
INCIDENTES = [
    {"nombre": "Apolo 1 (1967)",
     "descripcion": "Murieron tres astronautas (Grissom, White y Chaffee) por un incendio súbito en la cabina durante una prueba en plataforma con atmósfera de 100 % oxígeno a presión elevada.",
     "causa": "Combinación letal del triángulo del fuego: atmósfera de oxígeno puro, materiales inflamables en cabina y un arco eléctrico como fuente de ignición.",
     "leccion": "Control estricto de materiales no metálicos, normas rígidas de aislamiento eléctrico y abandono de atmósferas de 100 % O2 a alta presión en tierra (Guía pp. 34-35).",
     "fuente": "GUIA"},
    {"nombre": "Apolo 13 (1970)",
     "descripcion": "Un tanque de oxígeno líquido/supercrítico explotó en el módulo de servicio durante el tránsito hacia la Luna.",
     "causa": "Falla de aislamiento eléctrico interno dentro de un sistema de almacenamiento de oxígeno a alta presión.",
     "leccion": "Las naves tienen opciones de escape limitadas y tolerancia casi nula al daño en sistemas críticos de soporte vital (Guía p. 35).",
     "fuente": "APOLO13"},
    {"nombre": "Estación Mir (24 feb 1997)",
     "descripcion": "Con seis tripulantes a bordo (relevo de tripulación), un generador de oxígeno de combustible sólido (SFOG/Vika, perclorato de litio) estalló en llamas en el módulo Kvant-1: lanzó un chorro de fuego de casi 1 metro (3 pies) con chispas y metal fundido, llenó la estación de humo denso y bloqueó la ruta de evacuación hacia una de las dos naves Soyuz.",
     "causa": "Tras dos años de investigación se concluyó que contaminación con hidrocarburos (muy probablemente un fragmento de guante de látex) dentro del cartucho provocó la combustión descontrolada tras más de 2.500 usos previos sin fallos.",
     "leccion": "Control riguroso de limpieza en fabricación de cartuchos, entrenamiento de combate de incendios en espacios confinados con máscaras de O2 y redundancia disímil en la ISS (tres unidades Elektron rusas + sistema OGS estadounidense) (Artículo Mir).",
     "fuente": "MIR"},
    {"nombre": "Artemis II (alarma de humo)",
     "descripcion": "Activación de alarma de humo en espacio profundo (~130.000 km de la Tierra), recordando que cualquier alerta de incendio lejos de casa exige atención inmediata.",
     "causa": "Detección de partículas en suspensión en el sistema de monitoreo ambiental.",
     "leccion": "La detección temprana con discriminación de polvo y rechazo de falsas alarmas es crítica en misiones más allá de la órbita terrestre baja.",
     "fuente": "PSI"},
]

MITOS = [
    {"mito": "Un fuego estable no puede existir en microgravedad sin convección.",
     "hallazgo": "Falso. Una llama de vela ardió más de 45 minutos en Mir y SOFBALL sostuvo bolas de fuego de ~1 W durante más de 40 minutos (Guía pp. 30, 35).",
     "fuente": "GUIA"},
    {"mito": "Un fuego se autoextingue inmediatamente si se apaga la ventilación.",
     "hallazgo": "Falso. La difusión molecular sostiene llamas débiles por decenas de minutos, y el chorro de un extintor puede arrastrar aire ambiental y avivar el fuego (Guía pp. 30-31).",
     "fuente": "GUIA"},
    {"mito": "La microgravedad es más segura y las pruebas terrestres (NASA-STD-6001 Test 1) son muy conservadoras.",
     "hallazgo": "Falso. BASS y SoFIE demostraron que Test 1 no es conservador: materiales arden con menos O2 en 0 g y requieren hasta la mitad de flujo de calor crítico para encenderse (Guía pp. 18, 22, 31).",
     "fuente": "GUIA"},
    {"mito": "Con ventilación muy baja el riesgo de incendio es mínimo.",
     "hallazgo": "Falso. La inflamabilidad de sólidos alcanza su máximo alrededor de ~10 cm/s, precisamente la velocidad típica de ventilación de las cabinas espaciales (Guía p. 31).",
     "fuente": "GUIA"},
    {"mito": "Aplicar nitrógeno siempre apaga la llama en el espacio.",
     "hallazgo": "Falso. BASS mostró que un chorro local de N2 puede fortalecer la llama al arrastrar oxígeno circundante hacia la zona de reacción (Guía p. 22).",
     "fuente": "GUIA"},
    {"mito": "La llama siempre se propaga a favor del flujo de aire, como en la Tierra.",
     "hallazgo": "Falso. A velocidades bajas en microgravedad, las llamas sobre combustibles delgados se propagan corriente arriba (contra el flujo de aire) (Guía pp. 18, 31).",
     "fuente": "GUIA"},
    {"mito": "Cuando se apaga la llama visible, el peligro ha terminado.",
     "hallazgo": "Falso. Las llamas frías invisibles (descubiertas en FLEX) siguen vaporizando combustible y pueden provocar un reencendido espontáneo minutos después (Guía pp. 33-34, 41-42).",
     "fuente": "GUIA"},
]

APLICACIONES = [
    {"nombre": "Detector de incendio incipiente (Brunswick, 1978)",
     "descripcion": "Sensor desarrollado para el transbordador espacial: muestrea el aire y discrimina partículas de combustión frente a polvo, alertando antes de que aparezcan llama o humo. Enlazado a un procesador central ubica el foco; probado 1 año en perforadora de Peabody Coal (Indiana) por el Depto. de Minas y en aviones militares.",
     "origen": "Transbordador espacial (Space Shuttle Orbiter)", "uso": "Minería, fábricas, centrales eléctricas, aviación",
     "fuente": "DETECTOR"},
    {"nombre": "Project FIRES: traje de bomberos (1982)",
     "descripcion": "Programa conjunto de NASA (gestión técnica Marshall Space Flight Center) y USFA/FEMA con contratista Grumman: traje, casco, botas y guantes ligeros e ignífugos derivados de trajes espaciales y Apolo. Evaluado 9 meses por 14 departamentos de bomberos (incluyendo Alexandria, Virginia).",
     "origen": "Trajes espaciales y programa Apolo", "uso": "Cuerpos de bomberos municipales e industriales",
     "fuente": "ROPA"},
    {"nombre": "Extintores portátiles de niebla de agua",
     "descripcion": "Extintores no tóxicos certificados para vuelo espacial (los dos primeros de nueve llegaron a la ISS en diciembre de 2015) que reemplazan unidades de CO2 y sistemas Halon prohibidos.",
     "origen": "Experimento Mist (STS-107)", "uso": "Aviación, salas limpias y sustitución de Halon",
     "fuente": "GUIA"},
    {"nombre": "Monitor simultáneo de partículas y especies químicas",
     "descripcion": "Sensor híbrido desarrollado en NASA GRC que mide aerosoles y gases de combustión simultáneamente; en pruebas con la FAA superó a los detectores comerciales de aeronaves en rechazo de falsas alarmas.",
     "origen": "Investigación de detección en microgravedad (GRC)", "uso": "Aeronáutica comercial y defensa",
     "fuente": "GUIA"},
    {"nombre": "Quemador de ultra bajas emisiones (Low-Swirl)",
     "descripcion": "Quemador que permanece frío al tacto, derivado del estudio de llamas premezcladas en microgravedad; reduce drásticamente emisiones de NOx en calentadores y calderas.",
     "origen": "Investigación de llamas premezcladas (LBNL/NASA)", "uso": "Calentadores de agua y hornos domésticos/industriales",
     "fuente": "GUIA"},
    {"nombre": "Motores de combustión a baja temperatura (HCCI / RCCI)",
     "descripcion": "La cinética química de las llamas frías descubiertas en FLEX permite modelar motores de encendido por compresión con mayor eficiencia térmica y mínimas emisiones.",
     "origen": "Experimentos FLEX y Cool Flames (ISS)", "uso": "Industria automotriz y transporte pesado",
     "fuente": "GUIA"},
    {"nombre": "Modelos CFD de incendios forestales y estructurales",
     "descripcion": "Los modelos físicos simplificados en 1D validados en BASS, BASS-II y SLICE calibran simuladores complejos de propagación de fuego en edificios y bosques.",
     "origen": "BASS, BASS-II y SLICE", "uso": "Ingeniería de protección contra incendios",
     "fuente": "GUIA"},
    {"nombre": "Detección de humo en submarinos y hábitats cerrados",
     "descripcion": "Las distribuciones granulométricas de aerosol obtenidas en SAME calibran sensores en ambientes herméticos donde el humo envejece sin dispersarse.",
     "origen": "Experimentos SAME / SAME-R", "uso": "Submarinos y laboratorios submarinos",
     "fuente": "SAME"},
]

INSTALACIONES = [
    {"nombre": "MDCA (inserto del CIR)", "masa_kg": 254, "volumen_m3": 0.48, "potencia_kw": 0.73, "datos_gb": 72,
     "en_orbita_2015": "Sí (en CIR)", "soporta": "FLEX, FLEX-2, CFI, FLEX-ICE-GA, FLEX-2J",
     "diagnosticos": "Cámara de color analógica, radiómetro, cámara UV de baja luz, dos cámaras HiBMs",
     "o2_min": 0.0, "o2_max": 40.0, "p_min": 0.0, "p_max": 3.0,
     "nota": "Gotas de 1 a 5 mm (libres o en fibra), 0-3 atm y hasta 40 % O2 en cámara CIR de 100 L (Guía pp. 12, 52)"},
    {"nombre": "ACME (módulo en el CIR)", "masa_kg": 250, "volumen_m3": 0.50, "potencia_kw": 0.75, "datos_gb": 72,
     "en_orbita_2015": "En desarrollo (2016+)", "soporta": "BRE, CLD Flame, E-FIELD, Flame Design, s-Flame, CFI-G",
     "diagnosticos": "Radiómetros, dos cámaras de color, UV baja luz, dos HiBMs, fotomultiplicadores, corriente iónica, cromatógrafo de gases",
     "o2_min": 0.0, "o2_max": 40.0, "p_min": 0.0, "p_max": 3.0,
     "nota": "Opera dentro de la cámara CIR de 100 L (0-3 atm, hasta 40 % O2 cámara y hasta 85 % O2 local en quemador CFI-G) (Guía pp. 14, 44, 52)"},
    {"nombre": "SoFIE (inserto del CIR)", "masa_kg": 250, "volumen_m3": 0.50, "potencia_kw": 0.75, "datos_gb": 72,
     "en_orbita_2015": "En desarrollo (2019+)", "soporta": "Flame Spread, GEL, Narrow Channel, SMuRF, MIST",
     "diagnosticos": "Igual que ACME (radiómetros, cámaras color/UV/HiBMs, fotomultiplicadores, cromatógrafo)",
     "o2_min": 10.0, "o2_max": 40.0, "p_min": 0.2, "p_max": 1.5,
     "nota": "Diseñado específicamente para atmósferas de exploración con presión reducida (0.2-1.5 atm) y O2 elevado (10-40 %) (Guía pp. 19, 52)"},
    {"nombre": "MSG (Microgravity Science Glovebox)", "masa_kg": 40, "volumen_m3": 0.10, "potencia_kw": 0.05,
     "datos_gb": 10, "en_orbita_2015": "Sí (desde julio 2002)", "soporta": "SPICE, SLICE, BASS, BASS-II, BASS-M, SAME, SAME-R",
     "diagnosticos": "Cámara fotográfica digital, cámara de video, flujo de aire, flujo de combustible, radiómetro",
     "o2_min": 17.0, "o2_max": 21.0, "p_min": 1.0, "p_max": 1.0,
     "nota": "Espacio de trabajo de 255 L a presión ISS (1 atm); aire nominal (21 % O2) diluido con N2 hasta 17 % O2 (Guía pp. 19, 44-45, 52)"},
]


def verificar_instalaciones(o2, p_atm):
    filas = []
    for i in INSTALACIONES:
        filas.append({
            "Instalación": i["nombre"],
            "O2": icono(_en_rango(o2, i["o2_min"], i["o2_max"])),
            "Presión": icono(_en_rango(p_atm, i["p_min"], i["p_max"])),
            "Rango O2 (%)": _rango(i["o2_min"], i["o2_max"]),
            "Rango P (atm)": _rango(i["p_min"], i["p_max"]),
            "Soporta": i["soporta"],
        })
    return pd.DataFrame(filas)


def fragmentos(exps):
    f = [(e["id"], resumen_estudio(e)) for e in exps]
    f += [(i["nombre"], f"{i['descripcion']} Causa: {i['causa']} Lección: {i['leccion']}") for i in INCIDENTES]
    f += [(m["mito"], m["hallazgo"]) for m in MITOS]
    f += [(a["nombre"], a["descripcion"]) for a in APLICACIONES]
    return f


def buscar_frag(consulta, frags, k=5):
    q = _tokens(consulta)
    pts = sorted(((len(q & _tokens(t + " " + x)), t, x) for t, x in frags), key=lambda z: z[0], reverse=True)
    return [(t, x) for s, t, x in pts[:k] if s > 0]


# ---------------------------------------------------------------------------
# 3c. DETALLE DE LOS DOCUMENTOS Y ANÁLISIS CRUZADO
# ---------------------------------------------------------------------------
DETALLES_DOCS = {
    "Guía del investigador: Combustion Science en la ISS (NASA, 2015, NP-2015-10-034-JSC)": [
        "En la Tierra una llama (~2.300 K frente a ~300 K ambiente) genera un cambio de densidad de 8 veces en 1 cm, creando un flujo flotante de ~1 m/s que oculta la química; sin gravedad el sistema se vuelve casi unidimensional (pp. 8-10, 31).",
        "Más de 200 investigadores principales han usado torres de caída (2.2 s y 5.2 s ZGF), aviones parabólicos y plataformas orbitales (p. 30).",
        "Refuta tres mitos críticos: (1) que no existe llama estable sin convección, (2) que apagar la ventilación extingue el fuego y (3) que las normas terrestres son conservadoras en el espacio (p. 35).",
        "Describe el CIR (cámara de 100 L, 8 ventanas ópticas, lanzado en STS-126 en nov. 2008) con insertos MDCA, ACME y SoFIE, y la MSG (255 L, 1.000 W, >10.000 h de operación desde julio 2002) (pp. 43-45, 52).",
        "El Telescience Support Center (TSC) cuenta con 33 estaciones de trabajo y >26.000 h de control remoto desde tierra desde 2001 (p. 46).",
        "La restricción más severa en la ISS es el tiempo de tripulación: los experimentos deben ser autónomos y permitir quemar, apagar y reencender la misma muestra (pp. 19, 47).",
        "Detalla iniciativas futuras: Cool Flames en CIR, campaña de inflamabilidad, Túnel de Viento en Microgravedad, Clean-airLab, NanopropLab, CombustionLab y CyberLab (pp. 38, 41-42).",
    ],
    "Incendio a bordo de la estación Mir (NASA, artículo de 23 feb 2022)": [
        "El 24 de febrero de 1997 había seis tripulantes a bordo durante un relevo (Korzun, Kaleri, Linenger, Tsibliyev, Lazutkin y Ewald).",
        "Al activar un generador de oxígeno de combustible sólido (SFOG / Vika / TGK) en el módulo Kvant-1 tras la cena, el cartucho de perclorato de litio estalló lanzando una llama de ~1 metro (3 pies) con chispas y metal fundido.",
        "El fuego bloqueó el acceso a una de las dos cápsulas de escape Soyuz y llenó la estación de humo tóxico. La tripulación usó máscaras de O2 y tres extintores de espuma para contenerlo.",
        "Tras 2 años de investigación, la causa más probable fue contaminación con hidrocarburos (material de guante de látex) introducida accidentalmente en el cartucho.",
        "Motivó cambios en entrenamiento, control en tierra y diseño de la ISS, que hoy combina 3 unidades Elektron rusas, el sistema OGS estadounidense y un SFOG mejorado de respaldo.",
    ],
    "Fire Detector (NASA Spinoff, 1978 - Brunswick Corporation)": [
        "Sensor de alerta temprana desarrollado por Brunswick Corporation Defense Division para el transbordador espacial.",
        "Muestrea aire y discrimina partículas de combustión frente a polvo ambiental, evitando falsas alarmas y detectando incendios incipientes antes de que aparezcan llama o humo.",
        "Instalado en red en una perforadora rotatoria Bucyrus-Erie de Peabody Coal (Lynnville, Indiana) en prueba de 1 año con el Depto. de Minas de EE. UU., además de pruebas en aviones militares.",
    ],
    "Project FIRES: New Technology for the Fire Attire (NASA Spinoff, 1982)": [
        "Programa conjunto NASA / U.S. Fire Administration (FEMA), gestionado por Marshall Space Flight Center con contratista Grumman (Bethpage, NY).",
        "Modernizó el equipo de bomberos (traje, casco, botas y guantes) aplicando materiales ligeros y resistentes al calor desarrollados para trajes espaciales y cápsulas Apolo.",
        "Evaluado durante 9 meses por 14 departamentos de bomberos municipales (entre ellos Alexandria, Virginia) tras 5 años de desarrollo.",
    ],
}

EVENTOS = [
    (1967, "Apolo 1: incendio en prueba en plataforma (100 % O2)", "Incidente", "Guía pp. 34-35"),
    (1970, "Apolo 13: explosión de tanque de oxígeno en tránsito lunar", "Incidente", "Guía pp. 34-35"),
    (1978, "Fire Detector (Brunswick): sensor de incendio incipiente", "Tecnología", "Fire Detector"),
    (1982, "Project FIRES: traje de bomberos con materiales Apolo", "Tecnología", "Project FIRES"),
    (1997, "Incendio en estación Mir (generador SFOG en Kvant-1)", "Incidente", "Artículo Mir"),
    (1997, "LSP y SOFBALL en STS-83/94; TGDF y ELF en STS-87", "Experimento", "Guía pp. 13, 25"),
    (2002, "MSG entra en operación en la ISS (julio 2002)", "Instalación", "Guía p. 44"),
    (2003, "Mist (niebla de agua), LSP y SOFBALL en STS-107", "Experimento", "Guía pp. 13, 25-26"),
    (2004, "Pruebas SCWO en torre de caída ZGF (5.2 s)", "Experimento", "Guía p. 27"),
    (2007, "SAME primera campaña en la MSG (Expedición 15)", "Experimento", "Guía p. 45"),
    (2008, "CIR llega a la ISS en STS-126 (noviembre 2008)", "Instalación", "Guía pp. 43-44"),
    (2009, "SPICE en la MSG (punto de humo en coflujo)", "Experimento", "Guía p. 45"),
    (2010, "SAME-R segunda campaña en MSG y baseline SCWM en ISS", "Experimento", "Guía pp. 29, 45"),
    (2012, "SLICE y BASS inician operaciones en la MSG", "Experimento", "Guía pp. 14, 19"),
    (2015, "Extintores de niebla de agua llegan a la ISS (dic. 2015)", "Tecnología", "Guía p. 26"),
    (2016, "Despliegue de experimentos ACME en el CIR", "Experimento", "Guía p. 14"),
    (2019, "Despliegue de SoFIE en el CIR (atmósferas exploración)", "Experimento", "Guía p. 19"),
]

ANALISIS_INCIDENTES = [
    {"Incidente": "Apolo 1", "Año": 1967, "Sistema": "Cabina de mando (prueba en tierra)",
     "Papel del oxígeno": "Atmósfera de 100 % O2 a alta presión",
     "Ignición": "Chispa / arco eléctrico en cableado", "Escape / respuesta": "Escotilla interna bloqueada por presión",
     "Resultado": "3 astronautas fallecidos", "Fuente": "Guía pp. 34-35"},
    {"Incidente": "Apolo 13", "Año": 1970, "Sistema": "Tanque de oxígeno N.º 2 (Módulo de Servicio)",
     "Papel del oxígeno": "Oxígeno criogénico/supercrítico presurizado",
     "Ignición": "Cortocircuito en calentadores internos del tanque", "Escape / respuesta": "Uso del Módulo Lunar como bote salvavidas",
     "Resultado": "Sin muertes; misión abortada", "Fuente": "Guía pp. 34-35"},
    {"Incidente": "Mir", "Año": 1997, "Sistema": "Generador de O2 sólido SFOG (módulo Kvant-1)",
     "Papel del oxígeno": "Liberación química por perclorato de litio",
     "Ignición": "Contaminación por hidrocarburos (probable guante de látex)", "Escape / respuesta": "Llama cortó acceso a 1 Soyuz; apagado con 3 extintores de espuma",
     "Resultado": "Sin muertes; paneles chamuscados; humo despejado en horas", "Fuente": "Artículo Mir"},
]

ANALISIS_SEGURIDAD = [
    {"Área": "Detección", "Hallazgo": "El humo en 0 g tiene distribución granulométrica distinta a 1 g (Teflon <1 µm); un detector terrestre busca firmas equivocadas (Guía pp. 26, 35).",
     "Implicación": "Calibrar sensores con firmas de aerosol en microgravedad y medir partículas de precombustión."},
    {"Área": "Detección", "Hallazgo": "El monitor simultáneo de partículas y gases superó a detectores de aviación FAA en rechazo de falsas alarmas (Guía p. 35).",
     "Implicación": "Usar detección multisensor (óptica/ionización + gases químicos) en hábitats."},
    {"Área": "Detección", "Hallazgo": "DAFT caracterizó el fondo de polvo de la ISS y Brunswick (1978) discriminó polvo de humo (Guía p. 26; Fire Detector).",
     "Implicación": "Ajustar umbrales dinámicos según el polvo ambiental (crítico en base lunar por regolito)."},
    {"Área": "Supresión", "Hallazgo": "Un chorro local de N2 puede arrastrar O2 y fortalecer la llama en 0 g aun sin ventilación (Guía pp. 22, 31).",
     "Implicación": "Diseñar boquillas difusas o inundación de compartimento en lugar de chorros puntuales."},
    {"Área": "Supresión", "Hallazgo": "Los extintores de niebla de agua (Mist) se certificaron y desplegaron en la ISS en 2015 reemplazando CO2 (Guía p. 26).",
     "Implicación": "Priorizar niebla de agua no tóxica para evitar contaminar el sistema cerrado de soporte vital."},
    {"Área": "Supresión", "Hallazgo": "FLEX mostró que el LOI es menor en 0 g y las llamas frías invisibles pueden reencenderse (Guía pp. 12, 33-34).",
     "Implicación": "Monitorear gases/temperatura post-extinción para prevenir reencendidos por llamas frías."},
    {"Área": "Prevención", "Hallazgo": "La inflamabilidad es máxima a ~10 cm/s (ventilación de cabina) y el calor crítico de ignición cae a la mitad (Guía pp. 24, 31).",
     "Implicación": "Reemplazar la prueba terrestre Test 1 por ensayos en Canal Estrecho (SoFIE) validados en 0 g."},
    {"Área": "Respuesta", "Hallazgo": "En Mir el fuego bloqueó el acceso a una Soyuz y exigió trabajo en equipo con máscaras de O2 (Artículo Mir).",
     "Implicación": "Garantizar rutas de evacuación redundantes y estaciones de respiración distribuidas."},
]

LECCIONES_GUIA = [
    "Minimizar la complejidad: más requisitos aumentan costo y tiempo de desarrollo (p. 47).",
    "Diseñar para operación autónoma: el tiempo de la tripulación es el recurso más escaso en la ISS (p. 47).",
    "Diseñar hardware flexible y reparable en órbita por la tripulación (p. 47).",
    "Priorizar el uso de instalaciones existentes (CIR y MSG) mediante convocatorias NRA en NSPIRES (pp. 47-48).",
    "Apoyar cada vuelo con ensayos previos en torres de caída (2.2 s / 5.2 s) y modelado numérico (pp. 37, 48).",
    "Permitir quemar, extinguir y reencender la misma muestra (como en SoFIE) para ahorrar tiempo de astronautas (p. 19).",
]

ATMOSFERAS = [
    ("Tierra (nivel del mar)", 21.0, 14.7),
    ("ISS (aire nominal, Guía p. 19)", 21.0, 14.7),
    ("Base lunar prevista (Artemisa)", 30.0, 10.2),
    ("Traje espacial (EVA)", 100.0, 4.3),
]


def eventos_df():
    return pd.DataFrame(EVENTOS, columns=["Año", "Evento", "Tipo", "Fuente"])


def tabla_cobertura(exps):
    dominios = {"prevencion": "Prevención", "deteccion": "Detección",
                "supresion": "Supresión", "fundamental": "Fundamental"}
    combustibles = {"solidos": "Sólidos", "liquidos": "Líquidos", "gases": "Gases"}
    filas = []
    for e in exps:
        if str(e["estado"]).startswith(("Planificado", "Propuesta")):
            continue
        for d, dn in dominios.items():
            if d in e["tags"]:
                presentes = [cn for c, cn in combustibles.items() if c in e["tags"]]
                for cn in presentes or ["Humo / aerosoles"]:
                    filas.append({"Dominio": dn, "Combustible": cn, "Estudio": e["id"]})
    cols = ["Sólidos", "Líquidos", "Gases", "Humo / aerosoles"]
    filas_orden = list(dominios.values())
    if not filas:
        return pd.DataFrame(0, index=filas_orden, columns=cols), pd.DataFrame(filas)
    df = pd.DataFrame(filas)
    tabla = df.groupby(["Dominio", "Combustible"]).size().unstack(fill_value=0)
    tabla = tabla.reindex(index=filas_orden, columns=cols, fill_value=0)
    return tabla, df


def huecos_cobertura(tabla):
    res = []
    for d in tabla.index:
        for c in tabla.columns:
            if d == "Detección":
                continue
            if tabla.loc[d, c] == 0 and c != "Humo / aerosoles":
                res.append(f"{d} × {c}")
    return res


def analisis_atmosferas(exps):
    filas = []
    for nombre, o2, psi in ATMOSFERAS:
        p_atm = psi / PSI_POR_ATM
        solo_o2 = [e["id"] for e in exps if _en_rango(o2, e["o2_min"], e["o2_max"]) is True]
        ambos = [e["id"] for e in exps if _en_rango(o2, e["o2_min"], e["o2_max"]) is True
                 and _en_rango(p_atm, e["p_min"], e["p_max"]) is True]
        filas.append({
            "Atmósfera": nombre, "O2 (%)": o2, "Presión (psi)": psi,
            "pO2 (psi)": round(o2 / 100 * psi, 2),
            "O2 frente a la Tierra": f"{(o2 / O2_TIERRA - 1) * 100:+.0f} %",
            "Cubren O2 y presión": ", ".join(ambos) or "Ninguno en vuelo (solo simulación/futuro)",
            "Cubren solo el O2": ", ".join(x for x in solo_o2 if x not in ambos) or "Ninguno adicional",
        })
    return pd.DataFrame(filas)


def resumen_analisis(exps):
    tabla, df = tabla_cobertura(exps)
    lineas = []
    if not df.empty:
        por_dom = df.groupby("Dominio")["Estudio"].nunique().to_dict()
        partes = ", ".join(f"{k}: {v}" for k, v in por_dom.items())
        lineas.append(f"- **Cobertura:** estudios ejecutados o en curso por dominio ({partes}).")
    h = huecos_cobertura(tabla)
    if h:
        lineas.append("- **Combinaciones dominio × combustible sin estudios:** " + ", ".join(h) + ".")
    n = len(ANALISIS_INCIDENTES)
    lineas.append(f"- **Incidentes:** los {n} incidentes históricos analizados (Apolo 1, Apolo 13 y Mir) "
                  "involucraron oxígeno concentrado o generado químicamente.")
    luna = analisis_atmosferas(exps)
    fila = luna[luna["Atmósfera"] == "Base lunar prevista (Artemisa)"].iloc[0]
    lineas.append(f"- **Base lunar (30 % O2, 10,2 psi):** estudios que cubren O2 y presión: "
                  f"{fila['Cubren O2 y presión']}. Su presión parcial de O2 es {fila['pO2 (psi)']} psi.")
    return lineas


# ---------------------------------------------------------------------------
# 4. RELEVANCIA POR ENTORNO
# ---------------------------------------------------------------------------
TODOS = lambda v: dict.fromkeys(ENTORNOS, v)

PESOS = {
    "espacial_directo": TODOS(2),
    "solidos": TODOS(2),
    "deteccion": TODOS(2),
    "supresion": TODOS(2),
    "prevencion": TODOS(1),
    "modelado": TODOS(1),
    "gran_escala": TODOS(1),
    "flujo_variable": TODOS(1),
    "atm_quieta": {"Nave espacial": 0, "Estación espacial": 0, "Base lunar": 1,
                   "Rover presurizado": 1, "Base marciana": 1},
    "o2_variable": {"Nave espacial": 1, "Estación espacial": 0, "Base lunar": 3,
                    "Rover presurizado": 3, "Base marciana": 1},
    "presion_variable": {"Nave espacial": 1, "Estación espacial": 0, "Base lunar": 2,
                         "Rover presurizado": 2, "Base marciana": 1},
    "alto_o2": {"Nave espacial": 0, "Estación espacial": 0, "Base lunar": 2,
                "Rover presurizado": 2, "Base marciana": 0},
    "gravedad_parcial_sim": {"Nave espacial": 0, "Estación espacial": 0, "Base lunar": 1,
                             "Rover presurizado": 1, "Base marciana": 1},
    "gravedad_parcial": {"Nave espacial": 0, "Estación espacial": 0, "Base lunar": 4,
                         "Rover presurizado": 3, "Base marciana": 4},
}


def puntuar(e, entorno):
    total = min(sum(PESOS.get(t, {}).get(entorno, 0) for t in e["tags"]), 10)
    if str(e["estado"]).startswith(("Planificado", "Propuesta")):
        return min(total, 4)
    return total


def tabla_relevancia(exps):
    filas = []
    for e in exps:
        f = {"Experimento": e["id"], "Categoría": e["categoria"], "Estado": e["estado"]}
        f.update({ent: puntuar(e, ent) for ent in ENTORNOS})
        filas.append(f)
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# 5. VERIFICADOR DE CONDICIONES (SIN INTERROGANTES NI GUIONES VACÍOS)
# ---------------------------------------------------------------------------
def _en_rango(valor, lo, hi):
    valor = round(valor, 3)
    if lo is None and hi is None:
        return None
    if lo is not None and valor < lo:
        return False
    if hi is not None and valor > hi:
        return False
    return True


def icono(v):
    return {True: "✅ cubre", False: "❌ fuera", None: "ℹ️ N/A (sin límite)"}[v]


def _rango(lo, hi, unidad=""):
    if lo is None and hi is None:
        return "No aplica"
    if lo == hi:
        return f"{lo} {unidad}".strip()
    lo_s = "0.0" if lo is None else str(lo)
    hi_s = "máx. cámara" if hi is None else str(hi)
    return f"{lo_s} a {hi_s} {unidad}".strip()


def verificar(exps, o2, p_atm, flujo):
    filas = []
    for e in exps:
        filas.append({
            "Experimento": e["id"],
            "O2": icono(_en_rango(o2, e["o2_min"], e["o2_max"])),
            "Presión": icono(_en_rango(p_atm, e["p_min"], e["p_max"])),
            "Flujo": icono(_en_rango(flujo, e["flujo_min"], e["flujo_max"])),
            "Rango O2 doc. (%)": _rango(e["o2_min"], e["o2_max"]),
            "Rango P doc. (atm)": _rango(e["p_min"], e["p_max"]),
            "Rango flujo doc. (cm/s)": _rango(e["flujo_min"], e["flujo_max"]),
        })
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# 6. INFORME DE INVESTIGACIÓN
# ---------------------------------------------------------------------------
def aumento_o2_luna():
    return (O2_LUNA_MIN / O2_TIERRA - 1) * 100


def construir_informe(exps):
    pO2_luna = O2_LUNA_MIN / 100 * P_LUNA_MAX_PSI
    pO2_tierra = O2_TIERRA / 100 * P_TIERRA_PSI
    md = ["# Llama en caída libre: investigación de seguridad contra incendios espaciales\n"]

    md.append("## 1. Objetivo del panel")
    md.append("Integrar los datos experimentales de la *Guía del Investigador de la ISS (NP-2015-10-034-JSC)*, "
              "las fichas técnicas de NASA (BASS, FLEX, SAME, Saffire, ACME, SoFIE) y los informes históricos "
              "(Mir, Fire Detector 1978, Project FIRES 1982) para evaluar riesgos en hábitats de exploración.\n")

    md.append("## 2. Incidentes históricos y lecciones")
    for i in INCIDENTES:
        md.append(f"- **{i['nombre']}:** {i['descripcion']} *Lección:* {i['leccion']}")
    md.append("")

    md.append("## 3. Física de la combustión en microgravedad")
    md.append("En 1 g, una llama (~2.300 K frente a ~300 K del aire ambiente) genera un gradiente de densidad de "
              "8 veces en 1 cm, induciendo un flujo convectivo ascendente de ~1 m/s que domina la llama y causa "
              "parpadeo. En 0 g desaparece la flotabilidad, la difusión molecular gobierna el transporte y "
              "el flujo de ventilación de cabina (~10 cm/s) se convierte en el punto máximo de inflamabilidad (Guía pp. 8-10, 31).\n")

    md.append("## 4. Atmósfera de la Base Lunar vs. Tierra e ISS")
    md.append(f"- **Tierra / ISS nominal:** {O2_TIERRA:.0f} % O2 a {P_TIERRA_PSI} psi (1.0 atm) → pO2 = {pO2_tierra:.2f} psi.\n"
              f"- **Base lunar prevista:** ≥{O2_LUNA_MIN:.0f} % O2 a ≤{P_LUNA_MAX_PSI} psi (0.69 atm) → pO2 ≈ {pO2_luna:.2f} psi "
              f"(aumento de **+{aumento_o2_luna():.0f} %** en concentración molar de O2).\n"
              "- **Estudios que cubren exactamente 30 % O2 y 0.69 atm:** **SoFIE**, **Saffire-IV/V/VI**, **FLEX / FLEX-2**, "
              "**ACME (BRE, CLD Flame, Flame Design, s-Flame)** y los futuros experimentos lunares **FM2** y **LUCI**.\n")

    md.append("## 5. Hallazgos clave por experimento")
    for e in exps:
        if e["hallazgos"]:
            md.append(f"- **{e['id']}:** {e['hallazgos']}")
    md.append("")

    md.append("## 6. Mitos frente a evidencia experimental")
    for m in MITOS:
        md.append(f"- *Creencia:* {m['mito']}  \n  **Evidencia:** {m['hallazgo']}")
    md.append("")

    md.append("## 7. Instalaciones orbitales en la ISS")
    for i in INSTALACIONES:
        md.append(f"- **{i['nombre']}:** soporta {i['soporta']}. {i['nota']}.")
    md.append("")

    md.append("## Fuentes oficiales")
    for t, u in FUENTES.values():
        md.append(f"- [{t}]({u})")
    return "\n".join(md)


# ---------------------------------------------------------------------------
# 7. IA OPCIONAL
# ---------------------------------------------------------------------------
MODELO = "claude-sonnet-4-5"


def _cliente():
    clave = os.environ.get("ANTHROPIC_API_KEY")
    if not clave:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=clave)
    except Exception:
        return None


def preguntar_ia(pregunta, contexto):
    c = _cliente()
    if c is None:
        return ""
    try:
        r = c.messages.create(
            model=MODELO, max_tokens=900,
            system="Eres asistente de seguridad contra incendios en exploración espacial. "
                   "Responde en español usando solo el contexto dado.",
            messages=[{"role": "user", "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}"}])
        return "".join(b.text for b in r.content if b.type == "text")
    except Exception as exc:
        return f"No se pudo consultar la IA: {exc}"


def extraer_con_ia(texto):
    c = _cliente()
    if c is None:
        return None, "Define ANTHROPIC_API_KEY para usar el extractor."
    prompt = (
        "Extrae del texto los campos del experimento y responde SOLO con un objeto JSON "
        "(sin markdown). Claves: id, nombre, categoria, combustible, forma_muestra, n_muestras, "
        "o2_min, o2_max (% molar), p_min, p_max (atm), flujo_min, flujo_max (cm/s), variables, "
        "sensores, objetivo, hallazgos, aplic_espacio, aplic_tierra, plataforma, "
        "tags (lista; usa solo: solidos, liquidos, gases, deteccion, supresion, prevencion, modelado, "
        "o2_variable, presion_variable, flujo_variable, gran_escala, gravedad_parcial, alto_o2). "
        "Si un dato no aparece en el texto, usa null.\n\n"
        f"TEXTO:\n{texto}")
    try:
        r = c.messages.create(model=MODELO, max_tokens=1500,
                              messages=[{"role": "user", "content": prompt}])
        crudo = "".join(b.text for b in r.content if b.type == "text")
        crudo = re.sub(r"```(?:json)?", "", crudo).strip()
        datos = json.loads(crudo)
        reg = E(estado="Agregado por el usuario", fuente="PSI")
        for k in CAMPOS:
            if k in datos and k != "tags" and datos[k] is not None:
                reg[k] = datos[k]
        reg["tags"] = set(datos.get("tags") or [])
        reg["id"] = reg["id"] or "Nuevo estudio"
        return reg, ""
    except Exception as exc:
        return None, f"No se pudo extraer: {exc}"


# ---------------------------------------------------------------------------
# 8. BÚSQUEDA Y TABLA LARGA
# ---------------------------------------------------------------------------
def _tokens(t):
    return set(re.findall(r"[a-záéíóúñ0-9\-]{3,}", str(t).lower()))


def resumen_estudio(e):
    return (f"- {e['id']} ({e['categoria']}): {e['objetivo']} | combustible: {e['combustible']} | "
            f"O2: {_rango(e['o2_min'], e['o2_max'], '%')} | P: {_rango(e['p_min'], e['p_max'], 'atm')} | "
            f"flujo: {_rango(e['flujo_min'], e['flujo_max'], 'cm/s')} | hallazgos: {e['hallazgos']}")


def tabla_larga(exps):
    filas = []
    for e in exps:
        for var, lo, hi, u in [("O2", e["o2_min"], e["o2_max"], "% molar"),
                               ("Presión", e["p_min"], e["p_max"], "atm"),
                               ("Flujo", e["flujo_min"], e["flujo_max"], "cm/s")]:
            if lo is not None or hi is not None:
                filas.append({"estudio": e["id"], "variable": var, "mínimo": lo,
                              "máximo": hi, "unidad": u, "combustible": e["combustible"],
                              "fuente": FUENTES[e["fuente"]][1] if e["fuente"] in FUENTES else None})
        if e["n_muestras"]:
            filas.append({"estudio": e["id"], "variable": "N.º de muestras", "mínimo": e["n_muestras"],
                          "máximo": e["n_muestras"], "unidad": "muestras", "combustible": e["combustible"],
                          "fuente": FUENTES[e["fuente"]][1] if e["fuente"] in FUENTES else None})
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# 9. INTERFAZ PRINCIPAL
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Llama en caída libre", page_icon="🔥", layout="wide")
    st.title("🔥 Llama en caída libre")
    st.caption("Seguridad contra incendios en exploración espacial · Guía del investigador de la ISS (2015), "
               "informes históricos de NASA y datos PSI")

    if "extra" not in st.session_state:
        st.session_state["extra"] = []
    exps = [dict(e) for e in EXPERIMENTOS] + st.session_state["extra"]

    tabs = st.tabs(["Investigación", "Análisis", "Relevancia por entorno", "Verificador de condiciones",
                    "Comparar estudios", "Datos para modelado", "Incidentes y mitos", "Documentos",
                    "Instalaciones", "Aplicaciones en la Tierra", "Extractor IA", "Preguntar"])

    with tabs[0]:
        informe = construir_informe(exps)
        st.markdown(informe)
        st.download_button("Descargar informe (.md)", informe, "investigacion_llama.md")

    with tabs[1]:
        st.subheader("1. Cobertura experimental (dominio × combustible)")
        tabla, df_cob = tabla_cobertura(exps)
        if alt is None:
            st.dataframe(tabla)
        else:
            largo = tabla.reset_index().melt(id_vars="Dominio", var_name="Combustible", value_name="Estudios")
            base = alt.Chart(largo).encode(
                x=alt.X("Combustible:N", sort=list(tabla.columns)),
                y=alt.Y("Dominio:N", sort=list(tabla.index)))
            st.altair_chart(base.mark_rect().encode(color="Estudios:Q") +
                            base.mark_text().encode(text="Estudios:Q"), use_container_width=True)
        h = huecos_cobertura(tabla)
        st.markdown("**Combinaciones sin estudios en vuelo:** " + (", ".join(h) if h else "Todas las combinaciones cubiertas"))
        if not df_cob.empty:
            with st.expander("Ver desglose de estudios por celda"):
                st.dataframe(df_cob.groupby(["Dominio", "Combustible"])["Estudio"]
                             .apply(lambda s: ", ".join(sorted(set(s)))).reset_index(), hide_index=True)

        st.subheader("2. Atmósferas de exploración frente a estudios documentados")
        st.dataframe(analisis_atmosferas(exps), hide_index=True)

        st.subheader("3. Incidentes históricos: análisis comparado")
        df_inc = pd.DataFrame(ANALISIS_INCIDENTES)
        c1, c2, c3 = st.columns(3)
        c1.metric("Incidentes analizados", len(df_inc))
        c2.metric("Con oxígeno involucrado", f"{len(df_inc)} de {len(df_inc)}")
        c3.metric("Con ruta de escape bloqueada", "2 de 3 (Apolo 1 y Mir)")
        st.dataframe(df_inc, hide_index=True)

        st.subheader("4. Línea de tiempo histórica y experimental")
        ev = eventos_df()
        if alt is None:
            st.dataframe(ev, hide_index=True)
        else:
            graf = alt.Chart(ev).mark_circle(size=140).encode(
                x=alt.X("Año:Q", scale=alt.Scale(zero=False), axis=alt.Axis(format="d")),
                y=alt.Y("Tipo:N"), color="Tipo:N", tooltip=["Año", "Evento", "Fuente"])
            st.altair_chart(graf, use_container_width=True)
            with st.expander("Ver tabla cronológica"):
                st.dataframe(ev, hide_index=True)

        st.subheader("5. Hallazgos de seguridad por área")
        areas = ["Todas"] + sorted({r["Área"] for r in ANALISIS_SEGURIDAD})
        area = st.selectbox("Filtrar por área", areas)
        filas_seg = [r for r in ANALISIS_SEGURIDAD if area == "Todas" or r["Área"] == area]
        st.dataframe(pd.DataFrame(filas_seg), hide_index=True)

        st.subheader("6. Lecciones de la Guía ISS para futuros diseños")
        for t in LECCIONES_GUIA:
            st.markdown(f"- {t}")

    with tabs[2]:
        entorno = st.selectbox("Entorno habitable", ENTORNOS, index=2)
        df = tabla_relevancia(exps)[["Experimento", "Categoría", "Estado", entorno]]
        df = df.sort_values(entorno, ascending=False)
        st.bar_chart(df.set_index("Experimento")[entorno])
        st.dataframe(df, hide_index=True)

    with tabs[3]:
        st.subheader("¿Qué estudios e instalaciones cubren las condiciones de tu entorno?")
        c1, c2, c3 = st.columns(3)
        o2 = c1.number_input("O2 (% molar)", 0.0, 100.0, O2_LUNA_MIN, 1.0)
        p_psi = c2.number_input("Presión (psi)", 0.1, 20.0, P_LUNA_MAX_PSI, 0.1)
        flujo = c3.number_input("Flujo de aire (cm/s)", 0.0, 500.0, 10.0, 1.0)
        p_atm = p_psi / PSI_POR_ATM
        st.write(f"Presión = **{p_atm:.2f} atm** · presión parcial de O2 ≈ **{o2 / 100 * p_psi:.2f} psi** "
                 f"(Tierra ≈ {O2_TIERRA / 100 * P_TIERRA_PSI:.2f} psi)")
        st.markdown("**Estudios**")
        st.dataframe(verificar(exps, o2, p_atm, flujo), hide_index=True)
        st.markdown("**Instalaciones** (rango operativo de cámara / diseño)")
        st.dataframe(verificar_instalaciones(o2, p_atm), hide_index=True)

        rng = pd.DataFrame([{"Estudio": e["id"],
                             "min": e["o2_min"] if e["o2_min"] is not None else 0.0,
                             "max": e["o2_max"]} for e in exps if e["o2_max"] is not None])
        if alt is not None and not rng.empty:
            barras = alt.Chart(rng).mark_bar().encode(
                y=alt.Y("Estudio:N", sort="-x"), x=alt.X("min:Q", title="O2 (% molar)"), x2="max:Q")
            regla = alt.Chart(pd.DataFrame({"x": [O2_LUNA_MIN]})).mark_rule(strokeDash=[4, 4]).encode(x="x:Q")
            st.altair_chart(barras + regla, use_container_width=True)
            st.caption("Línea vertical punteada: 30 % de O2 (condición mínima de Base Lunar).")

    with tabs[4]:
        elegidos = st.multiselect("Elige estudios para comparar", [e["id"] for e in exps],
                                  default=["BASS", "SoFIE", "FLEX", "Saffire-IV/V/VI"])
        sel = [e for e in exps if e["id"] in elegidos]
        if sel:
            st.dataframe(pd.DataFrame([{
                "Estudio": e["id"], "Categoría": e["categoria"], "Estado": e["estado"],
                "Plataforma": e["plataforma"], "Combustible": e["combustible"],
                "Muestra": e["forma_muestra"], "O2 (%)": _rango(e["o2_min"], e["o2_max"]),
                "P (atm)": _rango(e["p_min"], e["p_max"]),
                "Flujo (cm/s)": _rango(e["flujo_min"], e["flujo_max"]),
                "Variables": e["variables"], "Sensores": e["sensores"], "Hallazgos": e["hallazgos"],
            } for e in sel]).set_index("Estudio").T)

    with tabs[5]:
        st.subheader("Tabla larga de parámetros para modelos predictivos")
        tl = tabla_larga(exps)
        st.dataframe(tl, hide_index=True)
        st.download_button("Descargar variables (.csv)", tl.to_csv(index=False), "variables_estudios.csv")
        base_df = pd.DataFrame([{**e, "tags": ";".join(sorted(e["tags"]))} for e in exps])
        st.download_button("Descargar base completa (.csv)", base_df.to_csv(index=False), "base_estudios.csv")

    with tabs[6]:
        st.subheader("Incidentes históricos y lecciones aprendidas")
        for i in INCIDENTES:
            with st.expander(i["nombre"], expanded=True):
                st.markdown(f"**Qué pasó:** {i['descripcion']}")
                st.markdown(f"**Causa:** {i['causa']}")
                st.markdown(f"**Lección:** {i['leccion']}")
        st.subheader("Mitos frente a hallazgos")
        st.dataframe(pd.DataFrame([{"Creencia": m["mito"], "Hallazgo": m["hallazgo"]} for m in MITOS]),
                     hide_index=True)

    with tabs[7]:
        st.subheader("Síntesis documental de fuentes")
        for titulo, hechos in DETALLES_DOCS.items():
            with st.expander(titulo, expanded=True):
                for hecho in hechos:
                    st.markdown(f"- {hecho}")

    with tabs[8]:
        st.subheader("Instalaciones orbitales y mini-instalaciones (Apéndice Guía ISS)")
        st.dataframe(pd.DataFrame([{
            "Instalación": i["nombre"], "Masa (kg)": i["masa_kg"], "Volumen (m³)": i["volumen_m3"],
            "Potencia (kW)": i["potencia_kw"], "Datos (GB)": i["datos_gb"],
            "Estado orbital": i["en_orbita_2015"], "Soporta": i["soporta"],
            "Diagnósticos": i["diagnosticos"], "Nota": i["nota"]} for i in INSTALACIONES]),
            hide_index=True)

    with tabs[9]:
        st.subheader("Transferencia tecnológica: del espacio a la Tierra")
        st.dataframe(pd.DataFrame([{
            "Tecnología": a["nombre"], "Origen": a["origen"], "Uso en la Tierra": a["uso"],
            "Descripción": a["descripcion"]} for a in APLICACIONES]), hide_index=True)
        for k in ("DETECTOR", "ROPA", "MIR"):
            st.markdown(f"- [{FUENTES[k][0]}]({FUENTES[k][1]})")

    with tabs[10]:
        st.subheader("Extractor con IA")
        txt = st.text_area("Pega la descripción de un estudio del PSI", height=220)
        if st.button("Extraer y agregar") and txt.strip():
            reg, err = extraer_con_ia(txt)
            if err:
                st.error(err)
            else:
                st.session_state["extra"].append(reg)
                st.success(f"Agregado: {reg['id']}")
                st.json({k: (sorted(v) if isinstance(v, set) else v) for k, v in reg.items() if v is not None})

    with tabs[11]:
        pregunta = st.text_input("Consulta sobre estudios, incidentes o aplicaciones",
                                 placeholder="¿Qué estudios cubren la atmósfera de la base lunar?")
        if pregunta:
            frags = fragmentos(exps)
            for titulo, hechos in DETALLES_DOCS.items():
                frags += [(titulo, h) for h in hechos]
            frags += [(r["Área"], f"{r['Hallazgo']} {r['Implicación']}") for r in ANALISIS_SEGURIDAD]
            hallados = buscar_frag(pregunta, frags)
            ctx = "\n".join(f"- {t}: {x}" for t, x in hallados)
            resp = preguntar_ia(pregunta, ctx or construir_informe(exps))
            if resp:
                st.markdown(resp)
            if hallados:
                st.markdown("**Fragmentos relacionados:**")
                st.markdown(ctx)


if __name__ == "__main__":
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        _corriendo_en_streamlit = get_script_run_ctx() is not None
    except Exception:
        _corriendo_en_streamlit = True
    if _corriendo_en_streamlit:
        main()
    else:
        import subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", os.path.abspath(__file__)])
        