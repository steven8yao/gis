# create indoor dataset for Senator Burns Layer 01

import arcpy
import datetime

# set the workspace to the default geodatabase
default_gdb = arcpy.mp.ArcGISProject("CURRENT").defaultGeodatabase

# disable adding outputs to the map
arcpy.env.addOutputsToMap = False

# N0P not included
# CAD_prefixs = ['N0b', 'N01', 'N02', 'N03', 'N04', 'N05', 'N06', 'N07', 'N08', 'N09', 'N10', 'N11', 'Nsb']
CAD_prefixs = ['N01']

# set the coordinate system to WGS_1984_Web_Mercator_Auxiliary_Sphere
coor_system = arcpy.SpatialReference(3857)

def get_current_time():
    return datetime.datetime.now().strftime('%H:%M:%S')

def create_unit():
    for CAD_prefix in CAD_prefixs:
        CAD_polyline = CAD_prefix + 'base-Polyline'

        
        print('***' * 30)
        print(get_current_time(), 'file geodatabase is set to', default_gdb, ', CAD file', CAD_polyline, 'is imported.')

        # define projection

        print(get_current_time(), 'Defining the projection for the CAD line feature class as WGS_1984_Web_Mercator and WGS_1984(Z)')
        arcpy.management.DefineProjection(
            in_dataset=CAD_polyline,
            coor_system=coor_system
        )

        # export selected layers into line featureclass
        print('Exporting necessary CAD layers to line feature class: Lines')
        arcpy.conversion.ExportFeatures(
            in_features=CAD_polyline,
            out_features=rf"{default_gdb}\Lines",
            # where_clause="Layer IN ('A-Door', 'A-Door-Head-New', 'A-Door-Jamb', 'A-Door-Jamb-New', 'A-Door-New', 'A-Glaz', 'A-Glaz-Jamb', 'A-Glaz-Jamb-New', 'A-Glaz-New', 'A-Wall', 'A-Wall-DIRTT', 'A-Wall-New', 'A-Wall-New 2', 'A-Wall-Prht', 'A-Wall-Sys-Glaz', 'L-Site-Patt', 'L-Walk')",
            where_clause="Layer IN ('A-Door', 'A-Door-Head-New', 'A-Door-Jamb', 'A-Door-Jamb-New', 'A-Door-New', 'A-Flor-Ovhd', 'A-Flor-Wdwk-New', 'A-Glaz', 'A-Glaz-Jamb', 'A-Glaz-Jamb-New', 'A-Glaz-New', 'A-Wall', 'A-Wall-DIRTT', 'A-Wall-New', 'A-Wall-New 2', 'A-Wall-Prht', 'A-Wall-Sys-Glaz', 'L-Walk', 'S-Cols')", # need to delete 'A-Roof-Otln' for higher floors 
            
            use_field_alias_as_name="NOT_USE_ALIAS",
            field_mapping=f'Entity "Entity" true true false 16 Text 0 0,First,#,{CAD_polyline},Entity,0,15;Handle "Handle" true true false 16 Text 0 0,First,#,{CAD_polyline},Handle,0,15;Layer "Layer" true true false 255 Text 0 0,First,#,{CAD_polyline},Layer,0,254;LyrFrzn "LyrFrzn" true true false 2 Short 0 0,First,#,{CAD_polyline},LyrFrzn,-1,-1;LyrOn "LyrOn" true true false 2 Short 0 0,First,#,{CAD_polyline},LyrOn,-1,-1;Color "Color" true true false 2 Short 0 0,First,#,{CAD_polyline},Color,-1,-1;Linetype "Linetype" true true false 255 Text 0 0,First,#,{CAD_polyline},Linetype,0,254;Elevation "Elevation" true true false 8 Double 0 0,First,#,{CAD_polyline},Elevation,-1,-1;LineWt "LineWt" true true false 2 Short 0 0,First,#,{CAD_polyline},LineWt,-1,-1;RefName "RefName" true true false 255 Text 0 0,First,#,{CAD_polyline},RefName,0,254;DocUpdate "DocUpdate" true true false 255 Date 0 0,First,#,{CAD_polyline},DocUpdate,-1,-1;DocId "DocId" true true false 8 Double 0 0,First,#,{CAD_polyline},DocId,-1,-1;GlobalWidth "GlobalWidth" true true false 8 Double 0 0,First,#,{CAD_polyline},GlobalWidth,-1,-1;t_ "t_" true true false 255 Text 0 0,First,#,{CAD_polyline},t_,0,254;RMNUMBER "RMNUMBER" true true false 255 Text 0 0,First,#,{CAD_polyline},RMNUMBER,0,254;ROOMNAME "ROOMNAME" true true false 255 Text 0 0,First,#,{CAD_polyline},ROOMNAME,0,254',
            sort_field=None
        )

        # dissolve lines
        
        print(get_current_time(), 'Dissolving line feature class for better results')
        arcpy.management.Dissolve(
            in_features="Lines",
            out_feature_class=rf"{default_gdb}\Lines_Dissolve",
            dissolve_field="Layer",
            statistics_fields=None,
            multi_part="SINGLE_PART",
            #unsplit_lines="UNSPLIT_LINES",
            concatenation_separator=""
        )

        # dissolved lines feature vertices to points
        
        print(get_current_time(), 'Creating point feature class from the dissolved line feature class')
        
        arcpy.management.FeatureVerticesToPoints(
            in_features="Lines_Dissolve",
            out_feature_class=rf"{default_gdb}\Lines_Dissolve_AllPoints",
            point_location="ALL"
        )

        # use Generate Near Table tool to generate nearest lines to all vertices
        
        print(get_current_time(), 'Generating nearest lines to all vertices')
        arcpy.analysis.GenerateNearTable(
            in_features="Lines_Dissolve_AllPoints",
            near_features="Lines_Dissolve",
            out_table=rf"{default_gdb}\Vertice_Nearest_Line_Pairs",
            search_radius="0.2 Meters",
            location="LOCATION",
            angle="ANGLE",
            closest="ALL",
            closest_count=5,
            method="PLANAR",
            distance_unit="Meters"
        )

        # export points with distance to nearest points between 0 and 0.2m, split one point pairs to two rectangular pairs
        print(get_current_time(), 'splitting point pairs to rectangular pairs')
        input_table = rf"{default_gdb}\Vertice_Nearest_Line_Pairs"
        
        # Create a new table to store the split results
        output_table = rf"{default_gdb}\Vertice_Nearest_Line_Pairs_Straight"
        arcpy.management.CreateTable(out_path=rf"{default_gdb}", out_name="Vertice_Nearest_Line_Pairs_Straight")
        
        # Add necessary fields to the new table (same as the input table)
        arcpy.management.AddField(output_table, "FROM_X", "DOUBLE")
        arcpy.management.AddField(output_table, "FROM_Y", "DOUBLE")
        arcpy.management.AddField(output_table, "NEAR_X", "DOUBLE")
        arcpy.management.AddField(output_table, "NEAR_Y", "DOUBLE")
        
        # Open a search cursor to read the input table
        with arcpy.da.SearchCursor(input_table, ['IN_FID', 'NEAR_FID', 'NEAR_DIST', 'NEAR_RANK', 'FROM_X', 'FROM_Y', 'NEAR_X', 'NEAR_Y', 'NEAR_ANGLE']) as search_cursor:
            with arcpy.da.InsertCursor(output_table, ['FROM_X', 'FROM_Y', 'NEAR_X', 'NEAR_Y']) as insert_cursor:
                for row in search_cursor:
                    IN_FID, NEAR_FID, dist, rank, x1, y1, x2, y2, angle = row
                    
                    if dist > 0.001 and dist < 0.2:
                        if angle in (0, 90, 180, -90, -180):
                            insert_cursor.insertRow((x1, y1, x2, y2))
                        else:
                            insert_cursor.insertRow((x1, y1, x2, y1))
                            insert_cursor.insertRow((x2, y1, x2, y2))
        
        # create extra lines from point pairs to repair gaps between CAD lines
        
        print(get_current_time(), 'creating extra lines from point pairs to repair gaps between CAD lines')
        arcpy.management.XYToLine(
            in_table="Vertice_Nearest_Line_Pairs_Straight",
            out_featureclass=rf"{default_gdb}\Lines_Extra",
            startx_field="FROM_X",
            starty_field="FROM_Y",
            endx_field="NEAR_X",
            endy_field="NEAR_Y",
            line_type="PLANAR",
            id_field=None,
            spatial_reference='PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],PARAMETER["Standard_Parallel_1",0.0],PARAMETER["Auxiliary_Sphere_Type",0.0],UNIT["Meter",1.0]],VERTCS["WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PARAMETER["Vertical_Shift",0.0],PARAMETER["Direction",1.0],UNIT["Meter",1.0]];-20037700 -30241100 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision',
            attributes="NO_ATTRIBUTES"
        )

        # merge the extra line to the original selected CAD polylines
        
        print(get_current_time(), 'merging the extra line to the original selected CAD polylines')
        arcpy.management.Merge(
            inputs="Lines;Lines_Extra",
            output=rf"{default_gdb}\Lines_Merge",
            field_mappings='Entity "Entity" true true false 16 Text 0 0,First,#,Lines,Entity,0,15;Handle "Handle" true true false 16 Text 0 0,First,#,Lines,Handle,0,15;Layer "Layer" true true false 255 Text 0 0,First,#,Lines,Layer,0,254;LyrFrzn "LyrFrzn" true true false 2 Short 0 0,First,#,Lines,LyrFrzn,-1,-1;LyrOn "LyrOn" true true false 2 Short 0 0,First,#,Lines,LyrOn,-1,-1;Color "Color" true true false 2 Short 0 0,First,#,Lines,Color,-1,-1;Linetype "Linetype" true true false 255 Text 0 0,First,#,Lines,Linetype,0,254;Elevation "Elevation" true true false 8 Double 0 0,First,#,Lines,Elevation,-1,-1;LineWt "LineWt" true true false 2 Short 0 0,First,#,Lines,LineWt,-1,-1;RefName "RefName" true true false 255 Text 0 0,First,#,Lines,RefName,0,254;DocUpdate "DocUpdate" true true false 8 Date 0 0,First,#,Lines,DocUpdate,-1,-1;DocId "DocId" true true false 8 Double 0 0,First,#,Lines,DocId,-1,-1;GlobalWidth "GlobalWidth" true true false 8 Double 0 0,First,#,Lines,GlobalWidth,-1,-1;t_ "t_" true true false 255 Text 0 0,First,#,Lines,t_,0,254;RMNUMBER "RMNUMBER" true true false 255 Text 0 0,First,#,Lines,RMNUMBER,0,254;ROOMNAME "ROOMNAME" true true false 255 Text 0 0,First,#,Lines,ROOMNAME,0,254;Shape_Length "Shape_Length" false true true 8 Double 0 0,First,#,Lines,Shape_Length,-1,-1,Lines_Extra,Shape_Length,-1,-1;X "X" true true false 8 Double 0 0,First,#,Lines_Extra,X,-1,-1;Y "Y" true true false 8 Double 0 0,First,#,Lines_Extra,Y,-1,-1;X_1 "X" true true false 8 Double 0 0,First,#,Lines_Extra,X_1,-1,-1;Y_1 "Y" true true false 8 Double 0 0,First,#,Lines_Extra,Y_1,-1,-1',
            add_source="NO_SOURCE_INFO"
        )

        # further dissolve merged lines, otherwise "invalid topology" error will occur
        
        print(get_current_time(), 'dissolving merged lines')
        arcpy.management.Dissolve(
            in_features="Lines_Merge",
            out_feature_class=rf"{default_gdb}\{CAD_prefix}_Lines_Merge_Dissolve",
            dissolve_field=None,
            statistics_fields=None,
            multi_part="SINGLE_PART",
            unsplit_lines="UNSPLIT_LINES",
            concatenation_separator=""
        )

        # output polygons from the merged lines
        
        print(get_current_time(), 'outputing polygons from the merged lines')
        arcpy.management.FeatureToPolygon(
            in_features=f"{CAD_prefix}_Lines_Merge_Dissolve",
            out_feature_class=rf"{default_gdb}\Polygons",
            cluster_tolerance=None,
            attributes="ATTRIBUTES",
            label_features=None
        )
        
        # add x-extent, y-extent, and area length ratio to filter out slim polygons, set the x and y-extent thresh to 0.8m, the area length ratio thresh to 0.2
        polygon_fc=rf"{default_gdb}\Polygons"
        arcpy.management.AddField(polygon_fc, 'X_EXTENT', 'DOUBLE')
        arcpy.management.AddField(polygon_fc, 'Y_EXTENT', 'DOUBLE')
        arcpy.management.AddField(polygon_fc, "AREA_LENGTH_RATIO", "FLOAT")
        
        with arcpy.da.UpdateCursor(polygon_fc, ["SHAPE@", "AREA_LENGTH_RATIO", "X_EXTENT", "Y_EXTENT"]) as cursor:
            for row in cursor:
                # Calculate area/length and assign to the 'alr' field
                area = row[0].area  # Area of the polygon
                length = row[0].length  # Perimeter of the polygon
                if length > 0:  # To avoid division by zero
                    row[1] = area / length
                else:
                    row[1] = None  # Handle cases where length is zero
                
                # Get the extent of the polygon
                extent = row[0].extent
                
                # Calculate x_extent (width) and y_extent (height)
                x_extent = extent.width
                y_extent = extent.height
                
                # Update the fields with calculated values
                row[2] = x_extent
                row[3] = y_extent
                cursor.updateRow(row)

        # filter polygons with area larger than 1.8 square meters, for further adjustment, as final units
        print(get_current_time(), 'filtering polygons with area larger than 1.8 square meters into Units')
        arcpy.conversion.ExportFeatures(
            in_features="Polygons",
            out_features=rf"{default_gdb}\{CAD_prefix}_Unfiltered_Units",
            where_clause="Shape_Area > 1.8 And X_EXTENT > 0.8 And Y_EXTENT > 0.8 And AREA_LENGTH_RATIO > 0.2",
            use_field_alias_as_name="NOT_USE_ALIAS",
            field_mapping=r'Shape_Length "Shape_Length" false true true 8 Double 0 0,First,#,C:\GIS\Capstone\SAIT_0918_RectangleExtra\SAIT_0918_RectangleExtra.gdb\Polygons,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0,First,#,C:\GIS\Capstone\SAIT_0918_RectangleExtra\SAIT_0918_RectangleExtra.gdb\Polygons,Shape_Area,-1,-1;X_EXTENT "X_EXTENT" true true false 8 Double 0 0,First,#,C:\GIS\Capstone\SAIT_0918_RectangleExtra\SAIT_0918_RectangleExtra.gdb\Polygons,X_EXTENT,-1,-1;Y_EXTENT "Y_EXTENT" true true false 8 Double 0 0,First,#,C:\GIS\Capstone\SAIT_0918_RectangleExtra\SAIT_0918_RectangleExtra.gdb\Polygons,Y_EXTENT,-1,-1;AREA_LENGTH_RATIO "AREA_LENGTH_RATIO" true true false 4 Float 0 0,First,#,C:\GIS\Capstone\SAIT_0918_RectangleExtra\SAIT_0918_RectangleExtra.gdb\Polygons,AREA_LENGTH_RATIO,-1,-1',
            sort_field=None
        )

        print(get_current_time(), 'creating central point from Unfiltered_Units')
        arcpy.management.FeatureToPoint(
            in_features=rf"{default_gdb}\{CAD_prefix}_Unfiltered_Units",
            out_feature_class=rf"{default_gdb}\{CAD_prefix}_Central_Point"
        )

        print(get_current_time(), 'selecting polygons that contain their own central point')
        arcpy.management.SelectLayerByLocation(
            in_layer=rf"{default_gdb}\{CAD_prefix}_Unfiltered_Units",
            overlap_type="CONTAINS",
            select_features=rf"{default_gdb}\{CAD_prefix}_Central_Point",
            search_distance=None,
            selection_type="NEW_SELECTION"
        )

        
        print(get_current_time(), 'creating feature layer for Unfiltered_Units')
        arcpy.management.MakeFeatureLayer(
            in_features=rf"{default_gdb}\{CAD_prefix}_Unfiltered_Units",
            out_layer="Unfiltered_Units_Layer"
        )

        print(get_current_time(), 'selecting polygons that contain their own central point')
        arcpy.management.SelectLayerByLocation(
            in_layer="Unfiltered_Units_Layer",
            overlap_type="CONTAINS",
            select_features=rf"{default_gdb}\{CAD_prefix}_Central_Point",
            search_distance=None,
            selection_type="NEW_SELECTION"
        )

        print(get_current_time(), 'Selecting polygons with area greater than 20 square meters and AREA_LENGTH_RATIO greather than 0.3')
        arcpy.management.SelectLayerByAttribute(
            in_layer_or_view="Unfiltered_Units_Layer",
            selection_type="ADD_TO_SELECTION",
            where_clause="Shape_Area > 20 And AREA_LENGTH_RATIO > 0.3"
        )

        # enable adding outputs to the map
        arcpy.env.addOutputsToMap = True

        print(get_current_time(), 'exporting final selected units')
        arcpy.conversion.ExportFeatures(
            in_features="Unfiltered_Units_Layer",
            out_features=rf"{default_gdb}\{CAD_prefix}_Units",
            use_field_alias_as_name="NOT_USE_ALIAS",
            field_mapping='Shape_Length "Shape_Length" false true true 8 Double 0 0,First,#,Unfiltered_Units_Layer,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0,First,#,Unfiltered_Units_Layer,Shape_Area,-1,-1;UniqueID "UniqueID" true true false 4 Long 0 0,First,#,Unfiltered_Units_Layer,UniqueID,-1,-1',
            sort_field=None
        )

def main():
    create_unit()
    print('process finished')

main()
# use largest overlap to spatial join room units and annotations (exported)



