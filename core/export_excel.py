from openpyxl import Workbook
from openpyxl.styles.borders import Border, Side
from openpyxl.styles import Alignment

import math
from pathlib import Path
import os
import json


from collections import defaultdict



REBAR_PROPERTIES_MM = [
    {'type': '#3', 'diameter': 9.525},
    {'type': '#4', 'diameter': 12.7},
    {'type': '#5', 'diameter': 15.875},
    {'type': '#6', 'diameter': 19.05},
    {'type': '#7', 'diameter': 22.225},
    {'type': '#8', 'diameter': 25.40},
    {'type': '#9', 'diameter': 28.65},
    {'type': '#10', 'diameter': 32.26},
    {'type': '#11', 'diameter': 35.81},
    {'type': '#14', 'diameter': 43.00},
]

HEADER_BORDER = Border(
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

TOP_BORDER = Border(
    top=Side(style='thin')
)
BOTTOM_BORDER = Border(
    bottom=Side(style='thin')
)

thin_side = Side(border_style="thin", color="000000") # Borde fino negro

DIAGONAL_BORDER = Border(
    top=Side(style='thin'),
    bottom=Side(style='thin'),
    diagonalUp=True,
    diagonalDown=True,
    diagonal=thin_side 
)


MAX_DISTANCIA_LIBRE_A_BARRA_APOYADA_MM = 150 #mm
MAX_DISTANCIA_LIBRE_A_BARRA_APOYADA_PULGADAS = 6.0    # pulgadas


from collections import defaultdict

def agrupar_gridlines_por_contenido(datos):
    """
    Analiza una lista de datos y agrupa los 'GridLines' que son 
    absolutamente idénticos.

    Dos GridLines se consideran idénticos si tienen:
    1. Exactamente la misma cantidad de filas (ocurrencias).
    2. El contenido de todas sus filas es idéntico, sin importar el orden.

    Args:
        datos (list): Una lista de diccionarios con los datos.

    Returns:
        list: Una lista de diccionarios donde cada uno representa un grupo
              de GridLines idénticos.
    """
    # Paso 1: Agrupar todas las filas por su 'GridLine'
    gridlines_agrupados = defaultdict(list)
    for fila in datos:
        gridlines_agrupados[fila["GridLine"]].append(fila)

    # Paso 2: Crear una "firma" de contenido para cada GridLine.
    # Esta firma representa de forma única todo el contenido de un GridLine.
    firmas = {}
    for grid, filas in gridlines_agrupados.items():
        # Convertimos cada fila (diccionario) en una tupla de pares (llave, valor)
        # y las ordenamos para que el orden de las llaves no afecte.
        filas_hasheables = [tuple(sorted(fila.items())) for fila in filas]
        
        # Ordenamos la lista de tuplas para que el orden de las filas no afecte.
        # Finalmente, lo convertimos todo en una gran tupla para que sea "hasheable".
        firma_contenido = tuple(sorted(filas_hasheables))
        firmas[grid] = firma_contenido

    # Paso 3: Agrupar los GridLines que tienen la misma firma de contenido
    grupos_por_firma = defaultdict(list)
    for grid, firma in firmas.items():
        grupos_por_firma[firma].append(grid)

    # Paso 4: Construir el resultado final simplificado
    resultado_final = []
    contador_grupo = 1
    
    # Iteramos sobre los valores del diccionario de grupos (las listas de GridLines)
    for lista_de_grids in grupos_por_firma.values():
        grupo_dict = {
            "grupo": f"Grupo {contador_grupo}",
            "gridlines_iguales": sorted(lista_de_grids)
        }
        resultado_final.append(grupo_dict)
        contador_grupo += 1
        
    return resultado_final


def get_diameter(rebar):
        for bar in REBAR_PROPERTIES_MM:
            if bar['type'] == rebar:
                return bar['diameter']
        return None

def calcular_max_espaciamiento_apoyo_lateral_cols(
        diametro_barra_longitudinal: float,
        unidades: str = "mm"
) -> float | None:
    if unidades.lower() not in ["mm", "pulgadas"]:
        print("Error: Unidades no válidas. Use 'mm' o 'pulgadas'.")
        return None
    
    d_b = diametro_barra_longitudinal
    dos_veces_max_dist_libre: float

    if unidades.lower() == "mm":
        dos_veces_max_dist_libre = 2 * MAX_DISTANCIA_LIBRE_A_BARRA_APOYADA_MM # 300 mm
    else:  # unidades es "pulgadas"
        dos_veces_max_dist_libre = 2 * MAX_DISTANCIA_LIBRE_A_BARRA_APOYADA_PULGADAS # 12 pulgadas
    
    # hx_max = 2 * d_b + (s_libre1_max + s_libre2_max)
    # hx_max = 2 * d_b + 2 * MAX_DISTANCIA_LIBRE_A_BARRA_APOYADA
    hx_max = 2 * d_b + dos_veces_max_dist_libre

    return hx_max


def calcular_numero_patas_estribo_por_direccion(
        dimension_columna_cara: float,
        recubrimiento_a_estribo: float,
        diametro_estribo: float,
        hx_max_apoyo_lateral: float,
        unidades_dimensiones: str = "mm" # Solo para mensajes, hx_max debe estar en als mismas unidades
) -> tuple[int, int , float]:
    
    if hx_max_apoyo_lateral <= 0:
        print("Error: hx_max_apoyo_lateral debe ser un valor positivo.")
        return None
    
    # Distancia centro a centro entre las patas más externas del estribo perimetral
    distancia_efectiva_apoyo = dimension_columna_cara - 2 * recubrimiento_a_estribo - diametro_estribo

    if distancia_efectiva_apoyo <= 0:
        # Dimensiones no permiten ni el estribo perimetral o es extremadamente pequeño
        # Se asume que al menos se requiere un estribo perimetral si la columna existe.
        # Esta función se enfoca en el espaciamiento de patas adicionales.
        # Si la distancia efectiva es cero o negativa, no se pueden colocar patas.
        # Podría interpretarse como que las barras están tan juntas que el perímetro las cubre,
        # o la dimensión es inválida. Para este cálculo, retornamos como si no cupieran.
        print(f"Advertencia: La distancia efectiva para el apoyo ({distancia_efectiva_apoyo:.2f} {unidades_dimensiones}) es cero o negativa.")
        return 2, 0, 0.0 # Asumiendo al menos 2 patas para el estribo perimetral si es posible
    
    num_total_patas: int
    num_patas_internas_adicionales: int
    espaciamiento_real_patas: float

    if distancia_efectiva_apoyo <= hx_max_apoyo_lateral:
        # Las dos patas del estribo perimetral son suficientes para cumplir hx_max.
        # Esto significa que el vano único creado por el estribo perimetral
        # ya es menor o igual al espaciamiento máximo permitido (hx_max).
        num_total_patas = 2
        num_patas_internas_adicionales = 0
        espaciamiento_real_patas = distancia_efectiva_apoyo # Solo hay un vano
    else:
        # Se necesitan patas internas además del estribo perimetral.
        num_vanos = math.ceil(distancia_efectiva_apoyo / hx_max_apoyo_lateral)
        num_total_patas = int(num_vanos + 1)
        num_patas_internas_adicionales = num_total_patas - 2
        espaciamiento_real_patas = distancia_efectiva_apoyo / num_vanos

    # Asegurar un mínimo de 2 patas si la columna tiene alguna dimensión
    if num_total_patas < 2 and distancia_efectiva_apoyo > 0: # Prácticamente ya cubierto por lógica anterior
        num_total_patas = 2
        num_patas_internas_adicionales = 0
        espaciamiento_real_patas = distancia_efectiva_apoyo    
    
    return num_total_patas, num_patas_internas_adicionales, espaciamiento_real_patas




def calcular_espaciamiento_estribos_confinamiento_columnas_aci_318_19(
    menor_dimension_columna: float,
    diametro_barra_longitudinal_mas_pequena: float,
    fy_barra_longitudinal: float,
    hx: float,
    unidades: str = "mm",
    fy_units: str = "MPa"
) -> tuple[float, dict[str, float]] | None:
    
    # --- Validación de Unidades ---
    if unidades.lower() not in ["mm", "pulgadas"]:
        print("Error: Unidades de dimensión no válidas. Use 'mm' o 'pulgadas'.")
        return None
    if fy_units.lower() not in ["mpa", "ksi"]:
        print("Error: Unidades de fy no válidas. Use 'MPa' o 'ksi'.")
        return None
    
    # --- Conversión de Unidades y Definición de Constantes ---
    fy_long_mpa = fy_barra_longitudinal
    if fy_units.lower() == "ksi":
        fy_long_mpa = fy_barra_longitudinal * 6.89476  # ksi a MPa

    lower_bound_c_val: float
    upper_bound_c_val: float
    eq_const_c1: float  # Constante aditiva en la ecuación de s_c
    eq_const_c2: float  # Constante de la que se resta hx en la ecuación de s_c

    if unidades.lower() == "mm":
        lower_bound_c_val = 100.0  # Límite inferior para s_c
        upper_bound_c_val = 150.0  # Límite superior para s_c
        eq_const_c1 = 100.0
        eq_const_c2 = 350.0
    else:  # unidades es "pulgadas"
        lower_bound_c_val = 4.0
        upper_bound_c_val = 6.0
        eq_const_c1 = 4.0
        eq_const_c2 = 14.0

    # --- Cálculo de Criterios según ACI 318-19, Sección 18.7.5.3 ---

    # Criterio (a): Un cuarto de la menor dimensión del miembro
    # s_o <= menor_dimension_columna / 4
    s_a = menor_dimension_columna / 4.0

    # Criterio (b): Múltiplo del diámetro de la barra longitudinal más pequeña
    # s_o <= 6 * d_b (para fy_long < 550 MPa o 80 ksi)
    # s_o <= 5 * d_b (para fy_long >= 550 MPa o 80 ksi)
    # Umbral para Grado 80 (fy >= 550 MPa o >= 80 ksi)
    if fy_long_mpa >= 550.0:
        s_b = 5.0 * diametro_barra_longitudinal_mas_pequena
    else:
        s_b = 6.0 * diametro_barra_longitudinal_mas_pequena

    # Criterio (c): Según Ecuación (18.7.5.3c)
    # El valor de s_o de esta ecuación no será mayor que upper_bound_c_val
    # y no necesita ser menor que lower_bound_c_val.
    
    val_eq_c = eq_const_c1 + (eq_const_c2 - hx) / 3.0
    
    # Aplicar la condición "no necesita ser menor que lower_bound_c_val"
    s_c_temp = max(val_eq_c, lower_bound_c_val)
    
    # Aplicar la condición "no será mayor que upper_bound_c_val"
    s_c = min(s_c_temp, upper_bound_c_val)

    # --- Determinación del espaciamiento final s_o ---
    # s_o es el menor de los tres criterios calculados.
    s_o_final = min(s_a, s_b, s_c)

    criterios_calculados = {
        "s_a (menor_dim/4)": s_a,
        "s_b (mult_diam_long_min)": s_b,
        "s_c (Eq. 18.7.5.3c ajustada)": s_c
    }

    return s_o_final, criterios_calculados


def calcular_lo_aci_318_19(mayor_dimension_section_col: float, luz_col: float, unidades: str = "mm") -> float:

    if unidades.lower() not in ["mm", "pulgadas"]:
        print("Error: Unidades no validas. Use 'mm' o 'pulgadas'.")
        return None
    
    # Criterio 1: La dimension mayor de la seccion de la columna
    criterio_1 = mayor_dimension_section_col

    # Criterio 2: Un sexto de la luz libre de la columna
    criterio_2 = luz_col / 6

    # Criteria 3: 18 pulgadas (convertir si es necesario)
    if unidades.lower() == "mm":
        criterio_3 = 450.0 # 18 pulgadas * 25.4 mm/pulgada
    else:
        criterio_3 = 18.0

    # El mayor de los 3 criterios
    lo_calculada = max(criterio_1, criterio_2, criterio_3)

    return lo_calculada

def get_excel_row(row_data, value):
    for item in row_data:
        if item['level'] == value:
            return item['row']
        
    return None

def get_excel_col(col_data, value):
    for item in col_data:
        if item['gridline'] == value:
            return item['excel_col']
        
    return None

def detectar_bxh_empty(work_sheet, stories_reverse, grid_lines):
    for x in range(0, len(stories_reverse)-1):
        row = 9*x+2
        counter_col = 0
        for col in grid_lines:
            actual_cell = work_sheet.cell(row=row, column=3+counter_col)
            if actual_cell.value is None:
                # Merge Cells Below for the story
                work_sheet.merge_cells(start_row=row, start_column=3+counter_col, end_row=row+8, end_column=3+counter_col)
                work_sheet.cell(row=row, column=3+counter_col).border = DIAGONAL_BORDER
            counter_col += 1



def generate_excel_table(folder_path, stories_data, grid_lines_data, column_records: list[dict]):
    
    # GridLines
    grid_lines = []
    for x in grid_lines_data:
        grid_lines.append(x['ID'])
        

    stories_reverse = []

    for story in stories_data:
        stories_reverse.append(story)
        print(story)

    wb = Workbook()
    ws = wb.active

    # Centrar celdas
    alineacion_centrada = Alignment(horizontal='center')
    for fila in ws.iter_rows(min_row=1, max_col=1, max_row=ws.max_row):
        for celda in fila:
            if celda.value is not None: # Aplicar solo si la celda tiene valor
                celda.alignment = alineacion_centrada
    # Create headers
    ws['A1'] = "NIVEL"
    current_cell = ws['A1']
    current_cell.border = HEADER_BORDER
    current_cell.alignment = Alignment(horizontal='center')
    ws['B1'] = "DESCRIPCION"
    current_cell = ws['B1'] 
    current_cell.border = HEADER_BORDER
    current_cell= Alignment(horizontal='center')

    # ancho de columnas
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 25


    col_rows = []
    for item in range(0, len(stories_reverse)-1):
        col_rows.append(
            {'level':f"{stories_reverse[item+1]['Name']}@{stories_reverse[item]['Name']}",
             'row': 9*item+2 }
        )
        # Top Border
        ws.cell(row=9*item+2, column=1).border = TOP_BORDER
        ws.cell(row=9*item+2, column=2).border = TOP_BORDER
        ws.cell(row=9*item+2, column=1).value = f"{stories_reverse[item+1]['Name']}@{stories_reverse[item]['Name']}"
        ws.cell(row=9*item+2, column=2).value = "b x h"
       
        ws.cell(row=9*item+3, column=2).value = "f'c"
        
        ws.cell(row=9*item+4, column=2).value = "As"
        
        ws.cell(row=9*item+5, column=2).value = "Est. en Lo"
        
        ws.cell(row=9*item+6, column=2).value = "Est. en Resto"
        
        ws.cell(row=9*item+7, column=2).value = "Estribo Externo"
        
        ws.cell(row=9*item+8, column=2).value = "Estribos Interno"
        
        ws.cell(row=9*item+9, column=2).value = "Lo"
       
        ws.cell(row=9*item+10, column=2).value = "Detalle"
        if item == len(stories_reverse)-2:
            ws.cell(row=9*item+10, column=1).border = BOTTOM_BORDER
            ws.cell(row=9*item+10, column=2).border = BOTTOM_BORDER
            counter_col = 0
            for y in grid_lines:
                ws.cell(row=9*item+10, column=3+counter_col).border = BOTTOM_BORDER
                counter_col += 1

    # Columns Data
    gridline_columns = []
    print(col_rows)
    counter_col = 0
    for x in grid_lines:
        print(x)
        ws.cell(row=1, column=3+counter_col).value = f"{x}"
        ws.cell(row=1, column=3+counter_col).border = TOP_BORDER
        for y in range(0, len(stories_reverse)-1):
            ws.cell(row=9*y+2, column=3+counter_col).border = TOP_BORDER
        gridline_columns.append(
            {'gridline': x, 'excel_col': 3+counter_col}
        )
        counter_col += 1


    # check start_level and end_level of columns in each gridlines
    columns_records_reduced = []
    for record in column_records:
        if record['nivel start'] != record['nivel end']:
            #print(record['GridLine'], record['nivel start'], record['nivel end'], record['Sección'],record['bxh'],record['As'],record['fc'],record['Rebar. Est.'],record['Detalle No.'])
            columns_records_reduced.append(record)
            
    # analisis_gridlines_iguales = agrupar_gridlines_por_contenido(columns_records_reduced)
    
   
    # print(json.dumps(analisis_gridlines_iguales, indent=2))
            
            
        
    # Column Dataframe
    for record in columns_records_reduced:
        # print(record)
        excel_column = get_excel_col(gridline_columns, record['GridLine'])
        excel_row = get_excel_row(col_rows, record['start_end_level'])
        print(excel_row, excel_column)
        if excel_row:
            if excel_column:
                    #bxh
                    ws.cell(row=excel_row, column=excel_column).value = record['bxh']
                    #f'c
                    ws.cell(row=excel_row+1, column=excel_column).value = record['fc']
                    # As
                    ws.cell(row=excel_row+2, column=excel_column).value = record['As']
                    # Estribo externos
                    ws.cell(row=excel_row+5, column=excel_column).value = record['Rebar. Est.']
                    # Estribo internos
                    ws.cell(row=excel_row+6, column=excel_column).value = record['Rebar. Est.']
                    # Detalle
                    rebar_diameter = get_diameter(record['Rebar'])/10
                    # Lo
                    h_floor = 10 * (float(record['End Z']) - float(record['Start Z'])) # convert to mm
                    ws.cell(row=excel_row+7, column=excel_column).value = calcular_lo_aci_318_19(max(float(record['depth'])*10, float(record['width'])*10), h_floor, "mm") / 10
                    # Espaciamiento Estribos en Lo
                    ws.cell(row=excel_row+3, column=excel_column).value =calcular_espaciamiento_estribos_confinamiento_columnas_aci_318_19(
                        min(float(record['depth'])*10, float(record['width'])*10),
                        rebar_diameter*10,
                        420, # grado 60
                        300,
                        unidades="mm",
                        fy_units="MPa"
                    )[0]
                    ws.cell(row=excel_row+8, column=excel_column).value = record['Detalle No.']

    # deterctar cells bxh empties
    detectar_bxh_empty(ws, stories_reverse, grid_lines)
                

    full_filename = str(Path(folder_path) / 'cuadro_columnas.xlsx')
    wb.save(full_filename)
    print('ARCHIVO EXCEL CREADO')