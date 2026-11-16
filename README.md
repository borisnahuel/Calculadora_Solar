# Calculadora Solar ULagos

Aplicación web en Python (Streamlit) para el dimensionamiento preliminar de sistemas fotovoltaicos residenciales en Chile, desarrollada como parte de una tesis de la Universidad de Los Lagos.

**App en línea:** https://app-dimensionamiento-fv.streamlit.app/

## Qué hace

A partir de la ubicación elegida en un mapa y del consumo eléctrico del usuario, la aplicación:

1. Obtiene la irradiación mensual sobre plano horizontal de NASA POWER (parámetro `ALLSKY_SFC_SW_DWN`, serie histórica 1984–2024).
2. Transpone esa irradiación al plano inclinado de los módulos según la inclinación y el azimut elegidos (modelo isotrópico mensual de Liu–Jordan, con la formulación de Klein para el factor geométrico, la correlación de Erbs para la fracción difusa y albedo 0,20).
3. Selecciona el mes de diseño (el de menor recurso solar sobre el plano inclinado).
4. Calcula la potencia fotovoltaica requerida, el número de módulos y la potencia instalada para sistemas On-Grid y Off-Grid, incluyendo el banco de baterías en el caso Off-Grid.
5. Genera un informe descargable con los parámetros, resultados, generación mensual y balance energético.

## Modelo de cálculo

- Energía diaria: `E_diario = E_mes / 30`
- Potencia requerida: `P_FV = E_diario · f_cob / (HSP · η)`
- Número de módulos: `N = ceil(P_FV / P_módulo)`
- Eficiencia global: `η = 0,80` (On-Grid) y `η = 0,75` (Off-Grid)
- Banco de baterías (Off-Grid): `C = E · días de autonomía / (V · DoD)`

Las ecuaciones de transposición están en el bloque inicial de `app_boris_ula.py` (funciones de transposición mensual) y documentadas con sus referencias en la tesis.

## Simplificaciones

Es una herramienta de **dimensionamiento preliminar**, no un simulador horario. En particular:

- La transposición es isotrópica y mensual, con un día representativo por mes.
- La eficiencia global es un valor fijo, sin modelar temperatura de módulo, sombreado ni degradación.
- Los datos climáticos son satelitales y no reemplazan una medición en terreno.

En una comparación con PV\*SOL para un caso en Puerto Montt, la aplicación dimensionó 7 módulos frente a 6 y su rendimiento específico anual difirió en un 7,5 %. Es un único caso y una única ubicación, por lo que esto es evidencia de consistencia y no una validación general.

## Cómo ejecutarla localmente

Requiere Python 3.9 o superior.

```bash
git clone https://github.com/borisnahuel/Calculadora_Solar.git
cd Calculadora_Solar
pip install -r requirements.txt
streamlit run app_boris_ula.py
```

Necesita conexión a internet para consultar NASA POWER y cargar el mapa.

## Estructura del repositorio

| Archivo | Descripción |
|---|---|
| `app_boris_ula.py` | Código de la aplicación |
| `requirements.txt` | Dependencias de Python |
| `LICENSE` | Licencia MIT |

## Cómo citar

Nahuelhueique Velásquez, B. A. (2026). *Calculadora Solar ULagos: dimensionamiento de sistemas fotovoltaicos residenciales en Chile* [Tesis, Universidad de Los Lagos]. Código: https://github.com/borisnahuel/Calculadora_Solar

## Licencia

MIT. Ver el archivo [LICENSE](LICENSE).
