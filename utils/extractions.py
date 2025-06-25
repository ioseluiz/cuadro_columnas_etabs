# Tolerance for comparing floating-point numbers (e.g., elevations)
COORDINATE_TOLERANCE = 1e-3

def get_all_rebars(sap_model):
    number_rebars, tuple_rebar, ret = sap_model.PropRebar.GetNameList()
    list_rebar_defined = list(tuple_rebar)
    rebar_info = []
    for rebar in list_rebar_defined:
        info_rebar = {}
        rebar_area, rebar_diameter , ret = sap_model.PropRebar.GetRebarProps(rebar)
        info_rebar['rebar'] = rebar
        info_rebar['diameter'] = rebar_diameter
        info_rebar['area'] = rebar_area
        rebar_info.append(info_rebar)
        
    return rebar_info

def get_rebar(rebar_data: list[dict], rebar_area) -> str:
    for rebar in rebar_data:
        if rebar['area'] == rebar_area:
            return rebar['rebar']
        
    return None
    

def get_rebar_data(sap_model , section_name, col_name):
    # Get Rebar data (Longitudinal and Confinement)
    # Note: API for rebar can be complex and depends on how
    # the section is defined (Section Designer vs Parametric)
    # Using GetColRebar for Parametric rectangular/circular
    # column sections
    
    rebar_data_results = sap_model.PropFrame.GetRebarColumn(section_name)
    print(rebar_data_results)
    rebar_area = sap_model.PropFrame.GetRebarColumn_1(section_name)[15]
    print(sap_model.PropFrame.GetRebarBeam(col_name))
    rebars_defined = get_all_rebars(sap_model)
    rebar_type = get_rebar(rebars_defined, rebar_area)
    #Parameters:
    #Name, MatPropLong, MatPropConfine, Pattern, ConfineType, Cover, NumberCBars
    #NumberR3Bars, NumberR2Bars, RebarSize, TieSize, TieSpacingLongit,
    # Number2DirTieBars, Number3DirTieBars, ToBeDesigned
    if rebar_data_results[14] == 0:
        print("Rebar Parametric")
        # Success
        mat_long, mat_conf, pattern, confine_type, cover, number_c_bars, number_r3_bars,number_r2_bars, rebarsize, tiesize,tie_spacing,number_2dir_tie, number_3dir_tie, to_be_designed, _ = rebar_data_results
        # print(f"Material Longitudinal: {mat_long}, Material Confine: {mat_conf}, Cover: {cover}, R3 Bars: {number_r3_bars}, R2 Bars: {number_r2_bars}")
        total_long_bars = number_r3_bars * 2 + (number_r2_bars - 2) * 2
        # print(f"Total Longitudinal Bars: {total_long_bars}")
        return {'mat_rebar_long': mat_long, 'mat_rebar_confine': mat_conf, 'cover': cover, 'number_r2_bars': number_r2_bars, 'number_r3_bars': number_r3_bars, 'number_bars': total_long_bars, 'rebar_type': rebar_type}
    else:
        # If GetRebarColumn fails, it be a Section Designer section or other type
        # For Section Designer, you might need PropFrame.GetSecDesProp
        print(f"Could not get parametric rebar data for {section_name}")
        return None
        
def get_all_materials(sap_model):
    # Etabs material type enumerators
    e_mat_types_enum = {1:'Steel', 2: 'Concrete', 3: 'NoDesign', 4: 'Aluminium', 5:'ColdFormed', 6:'Rebar',
                 7: 'Tendon', 8:'Masonry'}
    
    num_materials, material_list, ret  = sap_model.PropMaterial.GetNameList()
    # Classify each material
    for item in material_list:
        enum_mat = sap_model.PropMaterial.GetMaterial(item)
        print(f"Material Name:{item}, Type: {e_mat_types_enum[enum_mat[0]]}")
    return {'num_materials': num_materials, 'material_list': material_list}

def get_story_data(sap_model):
    stories_data = []
    print(sap_model.Story.GetNameList())
    try:
        num_stories, story_names_tuple, ret = sap_model.Story.GetNameList()
        if ret != 0 or not story_names_tuple:
            print("Error: Could not retrieve story names or no stories found.")
            return []
        
        story_names = list(story_names_tuple) # Convert tuple to list
        for story_name in story_names:
            elevation, ret_elev = sap_model.Story.GetElevation(story_name)
            print(sap_model.Story.GetElevation(story_name))
            if ret_elev == 0:
                stories_data.append({"name": story_name, "elevation": elevation})
            else:
                print(f"Warning: Could not retrieve elevation for story '{story_name}'.")
        
        # Sort stories by elevation in ascending order
        stories_data.sort(key=lambda s: s["elevation"])
        print(f"Successfully retrieved {len(stories_data)} stories.")
        return stories_data  
            
    except Exception as e:
        print(f"An error occured while getting story data: {e}")
        return []
    
def extract_columns_by_level(sap_model, stories_data):
    if not stories_data:
        print("No story data provided to extract columns by level")
        return []
    
    columns_by_level = {story['name']: [] for story in stories_data}
    all_frames_count = 0
    identified_columns_count = 0
    
    try:
        # Get all frame objects name
        num_frames, frame_names_tuple, ret = sap_model.FrameObj.GetNameList()
        if ret !=0:
            print("Error: Could not retrieve frame object names.")
            return {}
        if not frame_names_tuple:
            print("No frame objects found in the model.")
            return columns_by_level # Return empty structure
        
        frame_names = list(frame_names_tuple)
        all_frames_count = len(frame_names)
        print(f"\nProcessing {all_frames_count} from objects to identify columns...")
        
        for frame_name in frame_names:
            is_column = False
            
            
            # Method 1: Check Design Orientation and Section Type
            # Get design orientation: 1 for Column, 2 for Beam, 3 for Brace, 4 for Null, 5 for Other
            design_orientation, ret_orient = sap_model.FrameObj.GetDesignOrientation(frame_name)
            # print(f"design_orientation: {design_orientation}, ret_orient: {ret_orient}")
            
            if ret_orient == 0 and design_orientation == 1: # Vertical Orientation
                # print(frame_name)
                # print(sap_model.FrameObj.GetSection(frame_name))
                section_name, ret_1_sec,ret_sec = sap_model.FrameObj.GetSection(frame_name)
                if ret_sec == 0 and section_name:
                    try:
                        # 8 for rectangular ,9 for circle, 28 concrete L
                        section_type_oapi,ret_type = sap_model.PropFrame.GetTypeOAPI(section_name)
                        if section_type_oapi == 8:
                            is_column = True
                        
                        
                        
                    except AttributeError:
                        print(f"Warning: sap_model.PropFrame.GetTypeOAPI may not be available in this ETABS API for section '{section_name}'.")
                        
                    except Exception as e_type:
                        print(f"Warning: Error checking section type for {section_name}: {e_type}")
                        
            if is_column:
                # print('Columna...')
                identified_columns_count += 1
                # Get the start and endpoints (joints) of the frame object
                # The API returns: Point1Name, Point2Name,ReturnValue
                point1_name, point2_name, ret_points = sap_model.FrameObj.GetPoints(frame_name)
                if ret_points != 0:
                    print(f"Warning: Could not get the points for column '{frame_name}'")
                    continue
                # Get coordinates of the points
                # The API returns: X, Y, Z (in current units), Return Value
                x1, y1, z1, ret_c1 = sap_model.PointObj.GetCoordCartesian(point1_name)
                x2, y2, z2, ret_c2 = sap_model.PointObj.GetCoordCartesian(point2_name)
                
                if ret_c1 == 0 and ret_c2 == 0:
                    z_top = max(z1, z2)
                    z_bottom = min(z1, z2)
                    
                    # Assign column to story level if its top is at the stroy  elevation
                    for story in stories_data:
                        if abs(z_top - story["elevation"]) < COORDINATE_TOLERANCE:
                            columns_by_level[story["name"]].append(frame_name)
                            # print(f"column '{frame_name}' (Z_top: {z_top:.2f}) assigned to story '{story['name]} (Elev:{story['elevation']:.2f})'"")
                            break # Assign to the first matching story from bottom up
                else:
                    print(f"Warning: Could not get coordinates for points of column '{frame_name}'")
                    
        print(f"Processed {all_frames_count} frames. Identified {identified_columns_count} potential columns.")
        return columns_by_level
    
    except Exception as e:
        print(f"An error occurred during column extraction: {e}")
        return {}
    
                    
                
                
            
    
    except Exception as e:
        print(f"An error occurred during column extraction: {e}")