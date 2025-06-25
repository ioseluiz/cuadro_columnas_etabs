import ezdxf
from ezdxf.enums import TextEntityAlignment
from .detail import Detail

class Drawing:
    def __init__(self, filename, list_details: list[Detail]):
        self.filename = filename
        self.list_details = list_details


    def create_dxf(self):
        doc = ezdxf.new("R2010", setup=True)
        msp = doc.modelspace()
        
        # Create layers
        doc.layers.add(name="DetailArea", color=7)
        doc.layers.add(name="Text", color=8)
        doc.layers.add(name="Column", color=3)
        doc.layers.add(name="Rebar", color=1)
        
        
        # Text Style
        # doc.styles.new("myStandard", dxfattribs={"font" : "OpenSans-Regular.ttf"})
        doc.styles.new("myStandard", dxfattribs={"font" : "OpenSans-Regular.ttf"})
        
        
        counter = 0
        for detail in self.list_details:
            print(detail.rectangle_area_coord)
            # 1. Draw rectangle area
            msp.add_lwpolyline(detail.rectangle_area_coord, dxfattribs={"layer": "DetailArea"})
            # 2. Draw title of the detail
            # Title
            msp.add_text(detail.name, height=50, dxfattribs={"style": "LiberationSerif", "layer": "Text"}).set_placement(
                detail.title_coor
            )
            msp.add_lwpolyline(((detail.title_coor[0], detail.title_coor[1]-10),(detail.title_coor[0]+200, detail.title_coor[1]-10)),dxfattribs={"layer": "Text"} )
            msp.add_text("ESCALA 1:10", height=30, dxfattribs={"style": "LiberationSerif", "layer": "Text"}).set_placement(
                (detail.title_coor[0], detail.title_coor[1] - 45)
            )
            
            
            # 3. Draw column rectangle
            msp.add_lwpolyline(detail.column.coordinates, dxfattribs={"layer": "Column"})
            
            # Add Dimension lines
            # -- Horizontal
            dim = msp.add_linear_dim(
                base=(detail.column.coordinates[3][0], detail.column.coordinates[3][1] - 180),
                p1=detail.column.coordinates[3],
                p2=detail.column.coordinates[2],
                dimstyle="EZDXF",
                text="b",
                override={
                    "dimtxsty": "LiberationSerif",
                    "dimtxt": 40,
                    "dimclrt": 1,
                    "dimgap": 20,
                }
                
            )
            dim.set_dimline_format(color=1, lineweight=35, extension=5)
            dim.set_extline_format(color=1, lineweight=35, extension=10, offset=30)
            dim.set_tick(size=20)
            
            dim.render()
            
            # -- Vertical
            dim_v = msp.add_aligned_dim(
                p1=detail.column.coordinates[3],
                p2=detail.column.coordinates[0],
                distance=180,
                dimstyle="EZDXF",
                text="h",
                override={
                    "dimtxsty": "LiberationSerif",
                    "dimtxt": 40,
                    "dimclrt": 1,
                    "dimgap": 20,
                }
                
            )
            dim_v.set_dimline_format(color=1, lineweight=35, extension=5)
            dim_v.set_extline_format(color=1, lineweight=35, extension=10, offset=30)
            dim_v.set_tick(size=20)
            
            dim_v.render()
            
           
            

            # 4. Draw rebar circles
            for bar in detail.column.rebars:
                msp.add_circle(
                    center=(bar.coord_x, bar.coord_y),
                    radius=bar.diameter/2,
                    dxfattribs={"layer": "Rebar"}
                )
                # Hatch for rebar
                rebar_hatch = msp.add_hatch()
                rebar_hatch.set_solid_fill(color=1) # Color Red
                edge_path = rebar_hatch.paths.add_edge_path()
                edge_path.add_ellipse(
                    center=(bar.coord_x, bar.coord_y),
                    major_axis=(bar.diameter/2, 0, 0),
                    ratio=1.0
                )

            # 5. Draw Main Ring (Outer Stirrup)
            # - Vertical Legs
            #  -- Left Side
            #  ---Inner Line
            msp.add_lwpolyline(detail.column.vert_left_leg_inner_points, dxfattribs={"layer": "Rebar"})
            # --- outer Line
            msp.add_lwpolyline(detail.column.vert_left_leg_outer_points, dxfattribs={"layer": "Rebar"})
            # -- Right Side
            # --- Inner Line
            msp.add_lwpolyline(detail.column.vert_right_leg_inner_points, dxfattribs={"layer": "Rebar"})
            # -- Outer Line
            msp.add_lwpolyline(detail.column.vert_right_leg_outer_points, dxfattribs={"layer": "Rebar"})

            # - Vertical Legs
            # -- Top Side
            # --- Inner
            msp.add_lwpolyline(detail.column.top_leg_inner_points, dxfattribs={"layer": "Rebar"})
            # --- Outer
            msp.add_lwpolyline(detail.column.top_leg_outer_points, dxfattribs={"layer": "Rebar"})
            # -- Bottom Side
            # --- Inner
            msp.add_lwpolyline(detail.column.bottom_leg_inner_points, dxfattribs={"layer": "Rebar"})
            # --- Outer
            msp.add_lwpolyline(detail.column.bottom_leg_outer_points, dxfattribs={"layer": "Rebar"})

            # Arcs
            # -- Top Right
            # -- outer
            msp.add_arc(
                center=detail.column.arc_tr.center_point,
                radius=detail.column.arc_tr.radius,
                start_angle=detail.column.arc_tr.start_angle,
                end_angle=detail.column.arc_tr.end_angle,
                dxfattribs={"layer": "Rebar"}
            )
            # -- Top Left
            # -- outer
            msp.add_arc(
                center=detail.column.arc_tl.center_point,
                radius=detail.column.arc_tl.radius,
                start_angle=detail.column.arc_tl.start_angle,
                end_angle=detail.column.arc_tl.end_angle,
                dxfattribs={"layer": "Rebar"}
                
            )
            # -- Bottom Left
            # -- outer
            msp.add_arc(
                center=detail.column.arc_bl.center_point,
                radius=detail.column.arc_bl.radius,
                start_angle=detail.column.arc_bl.start_angle,
                end_angle=detail.column.arc_bl.end_angle,
                dxfattribs={"layer": "Rebar"}
                
            )
            
            #  -- Bottom Right
            # -- outer
            msp.add_arc(
                center=detail.column.arc_br.center_point,
                radius=detail.column.arc_br.radius,
                start_angle=detail.column.arc_br.start_angle,
                end_angle=detail.column.arc_br.end_angle,
                dxfattribs={"layer": "Rebar"}
                
            )

            # Corner Hook Arc
            msp.add_arc(
                center=detail.column.hook_arc.center_point,
                radius=detail.column.hook_arc.radius,
                start_angle=detail.column.hook_arc.start_angle,
                end_angle=detail.column.hook_arc.end_angle,
                dxfattribs={"layer": "Rebar"}
            )

            # Corner Hook Polyline
            msp.add_lwpolyline(detail.column.corner_hook_coords_left,dxfattribs={"layer": "Rebar"} )
            msp.add_lwpolyline(detail.column.corner_hook_coords_right, dxfattribs={"layer": "Rebar"})


            # Cross Ties
            ## Vertical
            print('CrossTies Verticales')
            print(detail.column.crossties_vert)
            for tie in detail.column.crossties_vert:
                msp.add_lwpolyline(tie['points_1'], dxfattribs={"layer": "Rebar"})
                msp.add_lwpolyline(tie['points_2'], dxfattribs={"layer": "Rebar"})

            ## Horizontal
            print("CrossTies Horizontal")
            print(detail.column.crossties_horizontal)
            for tie in detail.column.crossties_horizontal:
                msp.add_lwpolyline(tie['points_1'], dxfattribs={"layer": "Rebar"})
                msp.add_lwpolyline(tie['points_2'], dxfattribs={"layer": "Rebar"})

            ## Top Seismic Hooks
            print("Top Seismic Hooks")
            for hook in detail.column.tie_top_arcs:
                msp.add_arc(
                    center=hook.center_point,
                    radius=hook.radius,
                    start_angle=hook.start_angle,
                    end_angle=hook.end_angle,
                    is_counter_clockwise=False,
                    dxfattribs={"layer": "Rebar"}
                )

            for poly in detail.column.tie_top_hook_points:
                msp.add_lwpolyline(poly, dxfattribs={"layer": "Rebar"})
            
            ## Botom Seismic Hooks
            for hook in detail.column.tie_bottom_arcs:
                msp.add_arc(
                    center=hook.center_point,
                    radius=hook.radius,
                    start_angle=hook.start_angle,
                    end_angle=hook.end_angle,
                    is_counter_clockwise=False,
                    dxfattribs={"layer": "Rebar"}
                )
            
            for poly in detail.column.tie_bottom_hook_points:
                msp.add_lwpolyline(poly, dxfattribs={"layer": "Rebar"})

            ## Left Seismic Hooks
            for hook in detail.column.tie_left_arcs:
                msp.add_arc(
                    center=hook.center_point,
                    radius=hook.radius,
                    start_angle=hook.start_angle,
                    end_angle=hook.end_angle,
                    is_counter_clockwise=True,
                    dxfattribs={"layer": "Rebar"}
                )

            for poly in detail.column.tie_left_hook_points:
                msp.add_lwpolyline(poly, dxfattribs={"layer": "Rebar"})

            for hook in detail.column.tie_right_arcs:
                msp.add_arc(
                    center=hook.center_point,
                    radius=hook.radius,
                    start_angle=hook.start_angle,
                    end_angle=hook.end_angle,
                    is_counter_clockwise=True,
                    dxfattribs={"layer": "Rebar"}
                )

            for poly in detail.column.tie_right_hook_points:
                msp.add_lwpolyline(poly, dxfattribs={"layer": "Rebar"})



           
        # Save the dxf file
        doc.saveas(self.filename)
        print(f"Drawing {self.filename} created successfully...")