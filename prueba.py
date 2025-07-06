import comtypes.client
import sys

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

def get_rectangular_concrete_sections(sapModel):
    """
    Extrae todas las secciones transversales rectangulares de concreto de un modelo de ETABS.

    Args:
        sapModel: El objeto COM de ETABS.

    Returns:
        list: Una lista de diccionarios, donde cada diccionario representa una
              sección transversal rectangular de concreto.
    """
    print("RECTANGULAR SECTIONS")
    all_sections = []
    # Obtener todos los nombres de las secciones de los marcos
    ret = sapModel.PropFrame.GetNameList()
    
    frame_section_names = ret[1]
    # print(frame_section_names)
    rect_sections = []
    for section_name in frame_section_names:
        
        file_name, mat_prop, t3, t2, color, notes, guid, ret_rect = (
                sapModel.PropFrame.GetRectangle(section_name)
            )     
        # Obtener las propiedades del refuerzo
        mat_prop, mat_conf, pattern, conf_type, cover, num_c_bars, num_r3, num_r2, rebar_size, tie_size, tie_spacing, num_2d_tie, num_3d_tie, to_be_designed, ret_rebar= sapModel.PropFrame.GetRebarColumn(section_name)
        if ret_rebar == 0:
            section_dict = {
                "section": section_name,
                "b": t2,  # Convertir a mm
                "h": t3,  # Convertir a mm
                "cover": cover,  # Convertir a mm
                "rebar_size": rebar_size,
                "num_bars_2": num_r2,
                "num_bars_3": num_r3,
                "stirrup_size": tie_size,
                "num_crossties_2": num_2d_tie,
                "num_crossties_3": num_3d_tie
            }
            print(section_dict)
            all_sections.append(section_dict)
                    
    return all_sections

def main():
    # Conectarse a ETABS
    
    sapModel = obtener_sapmodel_etabs()

    if sapModel:
        # print("Hola")
        # Extraer las secciones rectangulares de concreto
        rectangular_sections = get_rectangular_concrete_sections(sapModel)
        
        # Imprimir las secciones encontradas
        for section in rectangular_sections:
            print(section)

if __name__ == "__main__":
    main()