import comtypes.client
import pandas as pd

# -- Constantes para tipos de material
# MAT_TYPE_STEEL = 1
MAT_TYPE_CONCRETE = 2
# MAT_TYPE_NODESIGN = 3
# MAT_TYPE_ALUMINIUM = 4
# MAT_TYPE_COLDFORMED = 5
MAT_TYPE_REBAR = 6
# MAT_TYPE_TENDON = 7
# MAT_TYPE_MASONRY = 8

# Units Length
UNITS_LENGTH_IN = 1
UNITS_LENGTH_FT = 2
UNITS_LENGTH_MM = 4
UNITS_LENGTH_CM = 5
UNITS_LENGTH_M = 6

# Units Force
UNITS_FORCE_LB = 1
UNITS_FORCE_KIP = 2
UNITS_FORCE_N = 3
UNITS_FORCE_KN = 4
UNITS_FORCE_KGF = 5
UNITS_FORCE_TONF = 6

# Unidades de Temperatura (eTemp)
UNITS_TEMP_F = 1  # Fahrenheit
UNITS_TEMP_C = 2  # Celsius


def establecer_units_etabs(
    sap_model, unidad_fuerza, unidad_longitud, unidad_temperatura
):
    if sap_model is None:
        print("Error: El objeto SapModel proporcionado no es válido.")
        return False

    print(
        f"\nIntentando establecer unidades: Fuerza={unidad_fuerza}, Longitud={unidad_longitud}, Temperatura={unidad_temperatura}"
    )

    try:
        # La función SetPresentUnits devuelve 0 si tiene éxito.
        # Firma: SetPresentUnits(eForce Force, eLength Length, eTemp Temp)
        ret = sap_model.SetPresentUnits_2(
            unidad_fuerza, unidad_longitud, unidad_temperatura
        )

        if ret == 0:
            print("Unidades establecidas exitosamente en ETABS.")
            # Opcional: Verificar las unidades actuales después de establecerlas
            current_units = (
                sap_model.GetPresentUnits_2()
            )  # Devuelve una tupla (fuerza, longitud, temperatura)
            print(current_units)
            print(
                f"Unidades actuales verificadas: Fuerza={current_units[0]}, Longitud={current_units[1]}, Temperatura={current_units[2]}"
            )
            return True
        else:
            print(
                f"Error al establecer las unidades en ETABS. Código de retorno: {ret}"
            )
            print(
                "Verifica que los códigos de unidades sean válidos para tu versión de ETABS."
            )
            return False

    except comtypes.COMError as e:
        print(f"Error de COM interactuando con ETABS al establecer unidades: {e}")
        return False
    except Exception as e:
        print(f"Ocurrió un error inesperado al establecer unidades: {e}")
        import traceback

        traceback.print_exc()
        return False


def obtener_sapmodel_etabs():
    sap_model = None
    ETABSObject = None
    ETABSObject = comtypes.client.GetActiveObject("CSI.ETABS.API.ETABSObject")
    
    try:
        try:
            print("Intentando conectar con una instancia activa de ETABS...")
            ETABSObject = comtypes.client.GetActiveObject("CSI.ETABS.API.ETABSObject")
            print("Conexión exitosa con ETABSObject.")
        except (OSError, comtypes.COMError) as e:
            print("No se pudo encontrar una instancia activa de ETABS.")
            print(f"Error: {e}")
            print("Por favor, asegúrate de que ETABS esté abierto con un modelo.")
            return None

        # Obtener el objecto SapModel
        sap_model = ETABSObject.SapModel
        if sap_model is None:
            print("No se pudo obtener el SapModel.")
            return sap_model

        print("SapModel obtenido exitosamente.")

    except comtypes.COMError as e:
        print(f"Error de COM interactuando con ETABS: {e}")
        # Podrías querer registrar el error completo: import traceback; traceback.print_exc()
        return None
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        # import traceback; traceback.print_exc()
        return None

    return sap_model

def close_connection():
    comtypes.CoUninitialize()


def get_story_by_elevation(stories_data, elevation):
    for story in stories_data:
        if story["elevacion"] == elevation:
            return story["nombre"]

    return None


def get_rect_concrete_sections(sap_model):
    secciones_rect_concreto = []
    prop_frame = sap_model.PropFrame
    prop_material = sap_model.PropMaterial

    if not prop_frame or not prop_material:
        print("Error: No se pudo acceder a las propiedades de secciones o materiales.")
        return secciones_rect_concreto

    # 1. Obtener la lista de todos los nombres de las secciones de frame ret, num_nombres,
    # nombres_secciones = prop_frame.GetNameList()
    num_nombres, nombres_secciones, ret = prop_frame.GetNameList()
    if ret != 0 or num_nombres == 0:
        print(
            "No se encontraron secciones de marco definidas o hubo un error al obtenerlas."
        )
        return secciones_rect_concreto

    print(f"Se encontraron {num_nombres} secciones de marco. Analizando...")

    for nombre_seccion in nombres_secciones:
        try:
            # Intentar obtener las propiedades de la seccion como rectangular
            # GetRectangle(Name, FileName, MatProp, T3, T2, Color, Notes, GUID)
            file_name, mat_prop, t3, t2, color, notes, guid, ret_rect = (
                prop_frame.GetRectangle(nombre_seccion)
            )
            if ret_rect == 0:  # Si es 0, la seccion es rectangular
                # 3. Obtener el tipo de material de la seccion
                # GetMaterial(Name, MatType, Color, Notes, GUID)
                tipo_mat_int, _, _, _, ret_mat_details = prop_material.GetMaterial(
                    mat_prop
                )

                if ret_mat_details == 0:
                    # 4. Verificar si el material es concreto
                    # Alternativamente, se podria usar GetTypeOAPI(Name) que devuelve solo el tipo
                    # tipo_mat_oapi_int, ret_tipo_oapi = prop_material.GetTypeOAPI(mat_prop)
                    # if ret_tipo_oapi == 0 and tipo_mat_oapi_int == MAT_TYPE_CONCRETE

                    if tipo_mat_int == MAT_TYPE_CONCRETE:
                        seccion_info = {
                            "Nombre": nombre_seccion,
                            "Material": mat_prop,
                            "Profundidad (T3)": t3,
                            "Ancho (T2)": t2,
                        }
                        secciones_rect_concreto.append(seccion_info)
                        print(
                            f" Seccion rectangular de concreto encontrada: {nombre_seccion} (Material: {mat_prop}, T3={t3}, T2={t2})"
                        )

        except Exception as e:
            print(f"Excepcion al procesar la seccion: '{nombre_seccion}': {e}")
            # Esto podria suceder si una seccion tiene un nombre en la lista pero
            # no se puede consultar con GetRectangle (secciones importadas extranas o nulas)
            continue

    if not secciones_rect_concreto:
        print("No se encontraron secciones rectangulares de concreto.")
    else:
        print(
            f"\nTotal de secciones rectangulares de concreto encontradas: {len(secciones_rect_concreto)}"
        )

    return secciones_rect_concreto


def get_defined_rebars(sap_model):
    barras_refuerzo_definidas = []
    prop_rebar = sap_model.PropRebar

    if not prop_rebar:
        print("Error: No se pudo acceder a las propiedades de las barras de refuerzo.")
        return barras_refuerzo_definidas

    # 1. Obtener la lista de todos los nombres/designaciones de las barras de refuerzo
    # GetNameList() para PropRebar devuelve (ret, NumberNames, MyNameArray)
    num_nombres, nombres_barras, ret = prop_rebar.GetNameList()

    if ret != 0:
        print(
            f"Error al obtener la lista de nombres de barras de refuerzo. Código: {ret}"
        )
        return barras_refuerzo_definidas

    if num_nombres == 0:
        print("No se encontraron barras de refuerzo definidas en el modelo.")
        return barras_refuerzo_definidas

    print(
        f"Se encontraron {num_nombres} designaciones de barras de refuerzo. Analizando..."
    )

    for nombre_barra in nombres_barras:
        try:
            # 2. Obtener las propiedades de cada barra de refuerzo (área y diámetro)
            # GetRebarProps(Name, Area, Diameter)
            # Las unidades de Area y Diameter serán las unidades base de la base de datos del modelo.
            area_barra, diametro_barra, ret_props = prop_rebar.GetRebarProps(
                nombre_barra
            )

            if ret_props == 0:
                barra_info = {
                    "Nombre": nombre_barra,
                    "Area": area_barra,
                    "Diametro": diametro_barra,
                }
                barras_refuerzo_definidas.append(barra_info)
                print(
                    f"  Barra de refuerzo encontrada: {nombre_barra} (Área: {area_barra:.4f}, Diámetro: {diametro_barra:.4f})"
                )
            else:
                print(
                    f"  Error al obtener propiedades para la barra de refuerzo '{nombre_barra}'. Código: {ret_props}"
                )

        except Exception as e:
            print(f"Excepción al procesar la barra de refuerzo '{nombre_barra}': {e}")
            continue

    if not barras_refuerzo_definidas:
        # Este mensaje podría ser redundante si num_nombres fue 0, pero se mantiene por si hay fallos en GetRebarProps
        print("No se pudieron extraer detalles de las barras de refuerzo definidas.")
    else:
        print(
            f"\nTotal de designaciones de barras de refuerzo procesadas: {len(barras_refuerzo_definidas)}"
        )

    return barras_refuerzo_definidas


def get_column_labels(sap_model):
    if sap_model is None:
        print("Error: El objeto SapModel proporcionado no es válido.")
        return []

    column_labels = []
    print("\nObteniendo lista de todos los elementos frame...")

    try:
        num_names, names_array_tuple, ret = sap_model.FrameObj.GetNameList()
        if ret != 0:
            print(
                f"Error al intentar obtener la lista de frames. Código de error: {ret}"
            )
            return column_labels

        number_of_frames = num_names
        all_frame_names_tuple = names_array_tuple

        if number_of_frames == 0:
            print("No se encontraron objetos de tipo frame en el modelo.")
            return column_labels

        for frame_name in all_frame_names_tuple:
            design_orientation, ret_orientation = (
                sap_model.FrameObj.GetDesignOrientation(frame_name)
            )
            # Check design_orientation value.. 1 = Column, 2 = Beam ,3 = Brace
            if ret_orientation == 0:
                if design_orientation == 1:
                    column_labels.append(frame_name)
            else:
                # Advertir si no se puede obtener el tipo, pero continuar con otros frames
                print(
                    f"Advertencia: No se pudo obtener el tipo para el frame '{frame_name}'. Código: {ret_orientation}"
                )

        if not column_labels:
            print("No se encontraron elementos de tipo columna en el modelo.")
        else:
            print(f"\nSe encontraron {len(column_labels)} columnas en el modelo.")

    except AttributeError:
        print(
            "Error: El objeto SapModel no parece tener el método 'FrameObj' o sus sub-métodos."
        )
        print(
            "Asegúrate de que el modelo esté correctamente cargado e inicializado en ETABS."
        )
    except Exception as e:
        print(f"Ocurrió un error inesperado al obtener labels de columnas: {e}")

    return column_labels


def get_story_lable_col_name(sap_model):
    if sap_model is None:
        print("Error: El objeto SapModel proporcionado no es válido.")
        return [], None

    column_data = []
    number_names, mynames, mylabels, mystories, ret = (
        sap_model.FrameObj.GetLabelNameList()
    )

    # Get Levels
    stories = get_stories_with_elevations(sap_model)
    # print(stories)
    for item in range(number_names):
        design_orientation, ret_orientation = sap_model.FrameObj.GetDesignOrientation(
            mynames[item]
        )
        if ret_orientation == 0:
            if design_orientation == 1:
                shape, ret = sap_model.PropFrame.GetTypeOAPI(
                    get_col_section(sap_model, mynames[item])
                )
                if shape == 8:
                    info = {}
                    info["col_id"] = mynames[item]
                    info["label"] = mylabels[item]
                    info["story"] = mystories[item]
                    info["section"] = get_col_section(sap_model, mynames[item])
                    info["material"] = get_col_material(sap_model, info["section"])
                    info["fc"] = get_fc_concrete(sap_model, info["material"])
                    info["shape"] = get_col_shape(sap_model, info["section"])
                    if info["shape"] == "rectangular":
                        dimensions = get_rectangular_col_dimensions(
                            sap_model, info["section"]
                        )
                        info["t3"] = dimensions[0]
                        info["t2"] = dimensions[1]

                        # Get bxh
                        b = min(info["t3"], info["t2"])
                        h = max(info["t3"], info["t2"])
                        info["depth"] = int(h)
                        info["width"] = int(b)
                        info["bxh"] = f"{int(b)}x{int(h)}"
                    else:
                        info["t3"] = None
                        info["t2"] = None
                        info["depth"] = None
                        info["width"] = None
                        info["bxh"] = None

                    coordinates = get_col_coordinates(sap_model, mynames[item])
                    info["pos_x"] = coordinates[0]
                    info["pos_y"] = coordinates[1]
                    info["z_start"] = coordinates[2]
                    info["z_end"] = coordinates[3]
                    nivel_start = clasificar_punto_por_elevacion(stories, info['z_start'])
                    nivel_end = clasificar_punto_por_elevacion(stories, info['z_end'])
                    info['nivel_start'] = nivel_start
                    info['nivel_end'] = nivel_end
                    # Stories
                    info["story_start"] = get_story_by_elevation(
                        stories, info["z_start"]
                    )
                    info["story_end"] = get_story_by_elevation(stories, info["z_end"])
                    info["start_end_level"] = (
                        f"{nivel_start}@{nivel_end}"
                    )
                    # Rebar Data
                    rebar_data = get_rebar_data(sap_model, info["section"])
                    info["Long. Rebar Mat."] = rebar_data[0]
                    info["Mat. Estribo"] = rebar_data[1]
                    info["Rebar"] = rebar_data[8]
                    info["r2_bars"] = rebar_data[6]
                    info["r3_bars"] = rebar_data[7]
                    info["number_bars"] = None
                    if rebar_data[6]:
                        if rebar_data[7]:
                            info["number_bars"] = (2 * rebar_data[6]) + (
                                2 * (rebar_data[7] - 2)
                            )

                    info["Est. Rebar"] = rebar_data[9]
                    info["estribo_r2"] = rebar_data[11]
                    info["estribo_r3"] = rebar_data[12]
                    info["cover"] = rebar_data[4]
                    info["As"] = f"{info['number_bars']} {info['Rebar']}"

                    column_data.append(info)

    # Create dataframe
    df_columns = pd.DataFrame(column_data)
    print(df_columns.columns)
    df_columns_sorted = df_columns.sort_values(by=["label", "z_start"])

    # Unique sections
    # df_section_selected = df_columns_sorted[["bxh", "As"]]
    df_section_selected = df_columns_sorted[["r2_bars", "r3_bars", "estribo_r2", "estribo_r3"]]
    df_section_unique = df_section_selected.drop_duplicates()

    section_rows = len(df_section_unique)
    detail_values = [f"DC-{i + 1}" for i in range(section_rows)]
    df_section_unique["detail"] = detail_values

    # 1. Create tuple of cols "pos_x" and "pos_y" for each row.
    # This is useful to have an object that can be used to find unique combinations.
    df_columns_sorted["temp_grid"] = df_columns_sorted[["pos_x", "pos_y"]].apply(
        tuple, axis=1
    )

    # 2. Get unique values of these tuples and map to an integer value
    # Use factorize(), which is efficient for this. Returns
    # - an array of integers that represents the categories.
    # - an arrray of unique categories
    # Add 1 in order that identifiers start in 1 not in 0
    df_columns_sorted["GridLine"] = pd.factorize(df_columns_sorted["temp_grid"])[0] + 1
    
    df_gridlines = df_columns_sorted.drop_duplicates(subset=["GridLine", "pos_x","pos_y"])
    gridlines_data = df_gridlines.to_dict(orient="records")
    

    gridlines = df_columns_sorted["GridLine"].unique()

    # 3. (Optional) Delete column temp
    df_columns_sorted = df_columns_sorted.drop(columns=["temp_grid"])

    # 4. Merge with detail for section
    df_merged = pd.merge(
        # df_columns_sorted, df_section_unique, on=["bxh", "As"], how="left"
        df_columns_sorted, df_section_unique, on=["r2_bars", "r3_bars", "estribo_r2", "estribo_r3"], how="left"
    )

    sections = df_merged["detail"].unique()
    # print(sections)
    number_details = len(sections)
    # 5. Sort rows
    df_sorted = df_merged.sort_values(by=["GridLine", "z_start"], ascending=True)
    # Sort dataframe by pos_x, pos_y
    # df_sorted.to_excel("column_output.xlsx")
    cols_data = df_sorted.to_dict(orient="records")  # List of dictionaries

    labels = df_columns_sorted["label"].unique()

    return cols_data, gridlines_data


def get_col_section(sap_model, frame_name):
    section_name, ret_1_sec, ret_sec = sap_model.FrameObj.GetSection(frame_name)
    if ret_sec == 0 and section_name:
        return section_name
    return None


def get_col_shape(sap_model, section):
    # 8 for rectangular ,9 for circle, 28 concrete L
    section_type_oapi, ret_type = sap_model.PropFrame.GetTypeOAPI(section)
    if ret_type == 0:
        if section_type_oapi == 8:
            shape = "rectangular"

        elif section_type_oapi == 9:
            shape = "circular"
        elif section_type_oapi == 28:
            shape = "Concrete L"

        elif section_type_oapi == 35:
            shape = "Concrete Tee"

        return shape
    return None


def get_rectangular_col_dimensions(sap_model, section):
    section_type_oapi, ret_type = sap_model.PropFrame.GetTypeOAPI(section)
    if ret_type == 0:
        if section_type_oapi == 8:
            shape = "rectangular"
            # Get dimensions
            ret = sap_model.PropFrame.GetRectangle(section)
            if ret[7] == 0:
                t3 = round(ret[2], 2)
                t2 = round(ret[3], 2)

            return t3, t2
    return None, None

def get_fy_steel(sap_model, material_name):
    """
    Obtiene la resistencia a la fluencia (Fy) de un material de refuerzo (rebar).

    Args:
        sap_model: El objeto SapModel activo de la API de ETABS.
        material_name (str): El nombre del material de refuerzo.

    Returns:
        float: El valor de Fy, o None si ocurre un error.
    """
    if not material_name:
        return None

    try:
        # La API devuelve una tupla de propiedades del acero. Fy es el primer valor.
        # Firma: GetOSteel_1(Name, Fy, Fu, EFy, EFu, ...)
        props = sap_model.PropMaterial.GetOSteel_1(material_name)
        
        # El último valor de la tupla es el código de retorno (0 si es exitoso)
        if props[-1] == 0:
            fy = props[0]
            return round(fy)
        else:
            return None
    except Exception as e:
        print(f"Error al obtener Fy para el material '{material_name}': {e}")
        return None


def get_col_material(sap_model, col_section):
    material_defined = sap_model.PropFrame.GetMaterial(col_section)[0]
    return material_defined


def get_col_coordinates(sap_model, col_name):
    col_point1, col_point2, ret_points = sap_model.FrameObj.GetPoints(col_name)
    if ret_points == 0:
        col_x_pos = sap_model.PointObj.GetCoordCartesian(col_point1)[0]
        col_y_pos = sap_model.PointObj.GetCoordCartesian(col_point1)[1]
        col_z_start = sap_model.PointObj.GetCoordCartesian(col_point1)[2]
        col_z_end = sap_model.PointObj.GetCoordCartesian(col_point2)[2]
        return (
            round(col_x_pos, 2),
            round(col_y_pos, 2),
            round(col_z_start, 2),
            round(col_z_end, 2),
        )
    return None


def get_fc_concrete(sap_model, material):
    mat_type, color, notes, guid, ret = sap_model.PropMaterial.GetMaterial(material)
    fc = None
    if ret == 0:
        if mat_type == MAT_TYPE_CONCRETE:
            ret = sap_model.PropMaterial.GetOConcrete_1(material)
            fc = round(ret[0])
    return fc


def get_rebar_data(sap_model, section):
    rebar_data_results = sap_model.PropFrame.GetRebarColumn(section)
    # print(rebar_data_results)
    return rebar_data_results


def get_next_story(stories, story):
    for item in range(0, len(stories)):
        if stories[item]["nombre"] == story:
            return stories[item + 1]["nombre"]
    return None


def get_stories_with_elevations(sap_model):
    list_stories_elevations = []
    try:
        if sap_model is None:
            print("No se pudo obtener el SapModel.")
            return list_stories_elevations

        num_stories, names_stories, ret = sap_model.Story.GetNameList()
        if num_stories == 0:
            print("No se encontraron stories en el modelo.")
            return list_stories_elevations

        print(f"Se encontraron {num_stories} niveles en el modelo.")

        for nombre_story in names_stories:
            elevacion = sap_model.Story.GetElevation(nombre_story)

            story_info = {"nombre": nombre_story, "elevacion": elevacion[0]}
            list_stories_elevations.append(story_info)
            # print(f" - Story: {nombre_story}, Elevacion: {elevacion[0]}")

    except Exception as e:
        print(f"Ocurrio un error inesperado: {e}")

    return list_stories_elevations

def clasificar_punto_por_elevacion(lista_niveles, elevacion_punto):
    # -- 1.Manejar la lista vacia
    if not lista_niveles:
        print('Advertencia: La lista de niveles esta vacia')
        return None
    
    # -- 2.Ordenar los niveles por de forma ascendente --
    # Esto es crucial para que la logica funcione correctamente
    nivels_ordenados = sorted(lista_niveles, key=lambda item: item['elevacion'])
    
    # -- 3. Iterar de forma inversa (del nivel mas alto al nivel mas bajo)
    for nivel_actual in reversed(nivels_ordenados):
        # -- 4. Comprobar la condicion
        # Si la elevacion del punto del punto es mayor o igual a la del nivel actual....
        if elevacion_punto >= nivel_actual['elevacion']:
            # ... hemos encontrado el nivel correcto.
            # Como vamos de arriba hacia abajo, este es el primer (y por tanto, el correcto)
            # nivel que cumple la condicion
            return nivel_actual['nombre']
        
    # -- 5. Manejar caso en donde el punto esta por debajo de todos los niveles --
    print(f"INFO: El punto con elevacion {elevacion_punto} esta por debajo del nivel mas bajo.")
    return None


# def get_rectangular_concrete_sections(SapModel):
#     print("--Inicio Metodo get_rectangular_concrete_sections--")
#     """
#     Analiza un modelo de ETABS y extrae las propiedades de todas las secciones
#     de marco de concreto rectangulares con refuerzo de columna definido.

#     Args:
#         SapModel: El objeto SapModel activo de la API de ETABS.

#     Returns:
#         list: Una lista de diccionarios, donde cada diccionario representa una
#               sección única y contiene sus propiedades de diseño.
#               Devuelve una lista vacía si no se encuentran secciones o si
#               ocurre un error.
#     """
    
#     secciones_rectangulares = get_rect_concrete_sections(SapModel)
#     print(secciones_rectangulares)
#     nombres_secciones_rectangulares = [x['Nombre'] for x in secciones_rectangulares]
    
#     # Diccionario para convertir el nombre de la barra a su diámetro en pulgadas
#     # ETABS usualmente maneja estos tamaños internamente
#     BAR_DIAMETERS_IN = {
#         '#2': 0.250, '#3': 0.375, '#4': 0.500, '#5': 0.625, '#6': 0.750,
#         '#7': 0.875, '#8': 1.000, '#9': 1.128, '#10': 1.270,
#         '#11': 1.410, '#14': 1.875, '#18': 2.257
#     }

#     # Acceder a los objetos de la API para propiedades y secciones
#     PropFrame = SapModel.PropFrame
    
#     sections_list = []
#     processed_sections = set() # Para evitar duplicados

#     # 1. Obtener la lista de todos los nombres de secciones de marco definidos
#     try:
#         all_sections_names = PropFrame.GetNameList()
#     except Exception as e:
#         print(f"Error al obtener la lista de secciones: {e}")
#         return []

#     print(f"Analizando {len(all_sections_names)} secciones definidas en el modelo...")

#     # 2. Iterar sobre cada sección
#     for section_name in nombres_secciones_rectangulares:
#         if section_name not in processed_sections:
            

#             try:
#                 # 3. Filtrar: Intentar obtener propiedades de sección rectangular
#                 # Si esto falla, no es una sección rectangular y el 'except' la ignorará.
#                 file_name, mat_prop, t3, t2, _, _, _, _ = PropFrame.GetRectangle(section_name)

#                 # 4. Filtrar: Intentar obtener datos de refuerzo de columna.
#                 # Si falla, no es una sección de columna o no tiene refuerzo definido.
#                 rebar_info = PropFrame.GetRebarColumn(section_name)
                
#                 # Desempacar la información de refuerzo obtenida
#                 mat_long, mat_conf, pattern, confine_type, clear_cover, \
#                 num_bars_3, num_bars_2, rebar_size, stirrup_size, _, _, _, _ = rebar_info

#                 # Solo procesar si el patrón de refuerzo es rectangular
#                 if pattern != 1: # 1 = Patrón Rectangular
#                     continue

#                 # 5. Calcular propiedades requeridas
                
#                 # Obtener el diámetro del estribo para calcular el recubrimiento a la barra long.
#                 stirrup_diameter = BAR_DIAMETERS_IN.get(stirrup_size, 0)
                
#                 # El recubrimiento de la API es hasta el estribo. Se ajusta para que sea
#                 # hasta el borde de la barra longitudinal, que es una métrica común.
#                 cover_to_long_bar = clear_cover + stirrup_diameter

#                 # Asumir el número de ganchos como el número de barras internas
#                 num_crossties_2 = max(0, num_bars_2 - 2)
#                 num_crossties_3 = max(0, num_bars_3 - 2)

#                 # 6. Construir el diccionario con los datos de la sección
#                 section_data = {
#                     "section": section_name,
#                     "h": t3,  # Altura (Depth)
#                     "b": t2,  # Ancho (Width)
#                     "cover": cover_to_long_bar,
#                     "rebar_size": rebar_size,
#                     "num_bars_3": num_bars_3, # Barras en la dirección del ancho 'b'
#                     "num_bars_2": num_bars_2, # Barras en la dirección de la altura 'h'
#                     "stirrup_size": stirrup_size,
#                     "num_crossties_2": num_crossties_2,
#                     "num_crossties_3": num_crossties_3
#                 }

#                 # 7. Añadir el diccionario a la lista de resultados
#                 sections_list.append(section_data)
#                 processed_sections.add(section_name)

#             except Exception:
#                 # Si ocurre cualquier error, significa que la sección no es una
#                 # columna de concreto rectangular con refuerzo definido. Simplemente la ignoramos.
#                 print("Error..")
            
#     print(f"\nSe encontraron y procesaron {len(sections_list)} secciones de columna de concreto rectangulares.")
#     return sections_list

def get_rectangular_concrete_sections(sapModel):
    """
    Extrae las propiedades de las secciones de concreto rectangulares que se 
    UTILIZAN COMO COLUMNAS en el modelo de ETABS.

    Args:
        sapModel: El objeto COM de ETABS.

    Returns:
        list: Una lista de diccionarios, donde cada diccionario representa una
              sección de columna rectangular única.
    """
    print("Iniciando la extracción de secciones de COLUMNAS rectangulares...")

    # --- 1. Identificar todas las secciones que se usan en elementos de columna ---
    column_section_names = set()  # Usar un 'set' para evitar duplicados
    
    # Obtener la lista de todos los elementos frame en el modelo
    num_frames, frame_names, ret = sapModel.FrameObj.GetNameList()
    if ret != 0:
        print("Error al obtener la lista de elementos frame.")
        return []

    print(f"Analizando {num_frames} elementos frame para identificar cuáles son columnas...")
    for frame_name in frame_names:
        # Verificar la orientación de diseño del elemento
        design_orientation, ret_orient = sapModel.FrameObj.GetDesignOrientation(frame_name)
        
        # design_orientation == 1 significa que es una columna
        if ret_orient == 0 and design_orientation == 1:
            # Si es una columna, obtener el nombre de su sección
            section_name, _, ret_sec = sapModel.FrameObj.GetSection(frame_name)
            if ret_sec == 0 and section_name:
                column_section_names.add(section_name)

    if not column_section_names:
        print("No se encontraron secciones asignadas a elementos de tipo columna en el modelo.")
        return []

    print(f"\nSe identificaron {len(column_section_names)} secciones únicas de columna: {list(column_section_names)}")

    # --- 2. Extraer las propiedades para las secciones de columna identificadas ---
    all_sections = []
    print("\nExtrayendo detalles de las secciones de columna...")

    for section_name in sorted(list(column_section_names)): # Iterar sobre la lista única y ordenada
        
        # Obtener dimensiones (esto también nos confirma que es rectangular)
        _, mat_prop_conc, t3, t2, _, _, _, ret_rect = sapModel.PropFrame.GetRectangle(section_name)
        if ret_rect != 0:
            # Si la sección de columna no es rectangular, la omitimos
            print(f"  - Adv: La sección de columna '{section_name}' no es rectangular. Omitiendo.")
            continue

        # Obtener datos de refuerzo (esto nos confirma que tiene refuerzo de columna)
        mat_prop_rebar, _, _, _, cover, _, num_r3, num_r2, rebar_size, tie_size, _, num_2d_tie, num_3d_tie, _, ret_rebar = sapModel.PropFrame.GetRebarColumn(section_name)
        if ret_rebar != 0:
            # Si no tiene refuerzo de columna definido, la omitimos
            print(f"  - Adv: La sección de columna '{section_name}' no tiene refuerzo de columna definido. Omitiendo.")
            continue

        # Obtener propiedades de materiales
        fc_value = get_fc_concrete(sapModel, mat_prop_conc)
        fy_value = get_fy_steel(sapModel, mat_prop_rebar)
        
        section_dict = {
            "section": section_name,
            "b": t2,
            "h": t3,
            "fc": fc_value,
            "fy": fy_value,
            "cover": cover,
            "rebar_size": rebar_size,
            "num_bars_2": num_r2,
            "num_bars_3": num_r3,
            "stirrup_size": tie_size,
            "num_crossties_2": num_2d_tie,
            "num_crossties_3": num_3d_tie
        }
        all_sections.append(section_dict)
        print(f"  + Procesada sección de columna: '{section_name}'")
        
    print("\nProceso finalizado.")
    return all_sections

# def get_rectangular_concrete_sections(sapModel):
#     """
#     Extrae todas las secciones transversales rectangulares de concreto de un modelo de ETABS.

#     Args:
#         sapModel: El objeto COM de ETABS.

#     Returns:
#         list: Una lista de diccionarios, donde cada diccionario representa una
#               sección transversal rectangular de concreto.
#     """
#     print("RECTANGULAR SECTIONS")
#     all_sections = []
#     # Obtener todos los nombres de las secciones de los marcos
#     ret = sapModel.PropFrame.GetNameList()
    
#     frame_section_names = ret[1]
#     # print(frame_section_names)
#     rect_sections = []
#     for section_name in frame_section_names:
        
#         file_name, mat_prop, t3, t2, color, notes, guid, ret_rect = (
#                 sapModel.PropFrame.GetRectangle(section_name)
#             )
#         mat_prop_conc = mat_prop
#         # Obtener las propiedades del refuerzo
#         mat_prop, mat_conf, pattern, conf_type, cover, num_c_bars, num_r3, num_r2, rebar_size, tie_size, tie_spacing, num_2d_tie, num_3d_tie, to_be_designed, ret_rebar= sapModel.PropFrame.GetRebarColumn(section_name)
#         if ret_rebar == 0:
#             print(mat_prop)
#             fc_value = get_fc_concrete(sapModel, mat_prop_conc)
#             fy_value = get_fy_steel(sapModel, mat_prop)
#             section_dict = {
#                 "section": section_name,
#                 "b": t2,  # Convertir a mm
#                 "h": t3,  # Convertir a mm
#                 "fc": fc_value,
#                 "fy": fy_value,
#                 "cover": cover,  # Convertir a mm
#                 "rebar_size": rebar_size,
#                 "num_bars_2": num_r2,
#                 "num_bars_3": num_r3,
#                 "stirrup_size": tie_size,
#                 "num_crossties_2": num_2d_tie,
#                 "num_crossties_3": num_3d_tie
#             }
#             print(section_dict)
#             all_sections.append(section_dict)
                    
#     return all_sections