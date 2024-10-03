# All inputs: 
# Polyline: Walls, Wall_Extra, Doors, Door_Extra, Lines_Extra
# Polygon: Units (all valid)
# Text: Annotation (Adjusted)

import arcpy
import os
import datetime

################### Global Settings ####################

# N0P not included
# CAD_prefixs = ['N0b', 'N01', 'N02', 'N03', 'N04', 'N05', 'N06', 'N07', 'N08', 'N09', 'N10', 'N11', 'Nsb']
CAD_prefix = 'N01'
building_prefix = CAD_prefix[0] # 'N'

# set the workspace to the default geodatabase
default_gdb = arcpy.env.workspace = os.path.join(arcpy.mp.ArcGISProject("CURRENT").homeFolder, building_prefix+'.gdb')
CAD_output_dir = os.path.join(arcpy.mp.ArcGISProject("CURRENT").homeFolder, 'ExportedCAD') 
indoor_gdb_name = "Indoor.gdb"
indoor_gdb_path = os.path.join(arcpy.mp.ArcGISProject("CURRENT").homeFolder, indoor_gdb_name)

# set the log table location
log_table = rf"{default_gdb}\Process_Log"

# set the coordinate system to WGS_1984_Web_Mercator_Auxiliary_Sphere
coor_system = arcpy.SpatialReference(3857)
z_coor_system = 'PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],PARAMETER["Standard_Parallel_1",0.0],PARAMETER["Auxiliary_Sphere_Type",0.0],UNIT["Meter",1.0]],VERTCS["WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PARAMETER["Vertical_Shift",0.0],PARAMETER["Direction",1.0],UNIT["Meter",1.0]];-20037700 -30241100 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision'

def get_current_time():
    return datetime.datetime.now()

def create_log_table():
    # Check if the log table exists, if not, create it
    if not arcpy.Exists(log_table):
        arcpy.management.CreateTable(out_path=default_gdb, out_name="Process_Log")
        arcpy.management.AddField(log_table, "Timestamp", "TEXT")
        arcpy.management.AddField(log_table, "CADPrefix", "TEXT")
        arcpy.management.AddField(log_table, "Message", "TEXT")

def log_message_to_table(log_table, message, CAD_prefix):
    # Insert the log message into the table
    with arcpy.da.InsertCursor(log_table, ["Timestamp", "CADPrefix", "Message"]) as cursor:
        cursor.insertRow([get_current_time(), CAD_prefix, message])

def create_annotations(CAD_prefix):
    message = 'Duplicate adjusted annotation to two feature classes: room type and room number, and modify fields'
    log_message_to_table(log_table, message, CAD_prefix)
    print(message)
    try:
        arcpy.management.CopyFeatures(
            in_features=rf"{CAD_prefix}\{CAD_prefix}_Annotation",
            out_feature_class=rf"{CAD_prefix}\{CAD_prefix}_Annotation_Type",
            config_keyword="",
            spatial_grid_1=None,
            spatial_grid_2=None,
            spatial_grid_3=None
        )
        arcpy.management.CalculateField(
            in_table=rf"{CAD_prefix}\{CAD_prefix}_Annotation_Type",
            field='Layer',
            expression='"Annotation_Type"',
            expression_type="PYTHON3"
        )
        arcpy.management.CalculateField(
            in_table=rf"{CAD_prefix}\{CAD_prefix}_Annotation_Type",
            field='TxtMemo',
            expression=f"!{'ROOMNAME'}!",
            expression_type="PYTHON3"
        )
        arcpy.management.CalculateField(
            in_table=rf"{CAD_prefix}\{CAD_prefix}_Annotation_Type",
            field='Height',
            expression=f"!{'Height'}! / 1000",
            expression_type="PYTHON3"
        )
        arcpy.management.CalculateField(
            in_table=rf"{CAD_prefix}\{CAD_prefix}_Annotation_Type",
            field='TxtWidth',
            expression=f"!{'TxtWidth'}! / 10",
            expression_type="PYTHON3"
        )
        
        arcpy.management.CopyFeatures(
            in_features=rf"{CAD_prefix}\{CAD_prefix}_Annotation",
            out_feature_class=rf"{CAD_prefix}\{CAD_prefix}_Annotation_Number",
            config_keyword="",
            spatial_grid_1=None,
            spatial_grid_2=None,
            spatial_grid_3=None
        )
        arcpy.management.CalculateField(
            in_table=rf"{CAD_prefix}\{CAD_prefix}_Annotation_Number",
            field='Layer',
            expression='"Annotation_Number"',
            expression_type="PYTHON3"
        )
        arcpy.management.CalculateField(
            in_table=rf"{CAD_prefix}\{CAD_prefix}_Annotation_Number",
            field='TxtMemo',
            expression=f"!{'RMNUMBER'}!",
            expression_type="PYTHON3"
        )
        arcpy.management.CalculateField(
            in_table=rf"{CAD_prefix}\{CAD_prefix}_Annotation_Number",
            field='Height',
            expression=f"!{'Height'}! / 1000",
            expression_type="PYTHON3"
        )
        arcpy.management.CalculateField(
            in_table=rf"{CAD_prefix}\{CAD_prefix}_Annotation_Number",
            field='TxtWidth',
            expression=f"!{'TxtWidth'}! / 10",
            expression_type="PYTHON3"
        )
        
    except Exception as e:
        error_message = f"Error duplicating adjusted annotation to two feature classes for {CAD_prefix}: {str(e)}"
        log_message_to_table(log_table, error_message, CAD_prefix)
        print(error_message)
    
    

# Create Arc files to export to CAD
def create_Arc(CAD_prefix):
    arcpy.env.addOutputsToMap = False
    # Section 1: creating Arc_Level, for Level and facility (only level 1) in Import CAD to Indoor Database
    message = 'Merging Doors and Door_Extra to create Doors_All feature class'
    log_message_to_table(log_table, message, CAD_prefix)
    print(message)
    try:
        arcpy.management.Merge(
            inputs=rf"{CAD_prefix}\{CAD_prefix}_Doors;{CAD_prefix}\{CAD_prefix}_Door_Extra",
            output=rf"{default_gdb}\{CAD_prefix}\{CAD_prefix}_Doors_All",
            add_source="NO_SOURCE_INFO"
        )
    except Exception as e:
        error_message = f"Error creating Doors_All for {CAD_prefix}: {str(e)}"
        log_message_to_table(log_table, error_message, CAD_prefix)
        print(error_message)
    
    message = 'Merging Walls, Wall_Extra, Doors_All, Lines_Extra to create Level feature class'
    log_message_to_table(log_table, message, CAD_prefix)
    print(message)
    try:
        arcpy.management.Merge(
            inputs=rf"{CAD_prefix}\{CAD_prefix}_Walls;{CAD_prefix}\{CAD_prefix}_Wall_Extra;{CAD_prefix}\{CAD_prefix}_Doors_All",  # for those layers don't have lines_extra
            # inputs=rf"{CAD_prefix}\{CAD_prefix}_Walls;{CAD_prefix}\{CAD_prefix}_Wall_Extra;{CAD_prefix}\{CAD_prefix}_Lines_Extra;{CAD_prefix}\{CAD_prefix}_Doors_All",
            output=rf"{default_gdb}\{CAD_prefix}\{CAD_prefix}_Level",
            add_source="NO_SOURCE_INFO"
        )
    except Exception as e:
        error_message = f"Error creating Level for {CAD_prefix}: {str(e)}"
        log_message_to_table(log_table, error_message, CAD_prefix)
        print(error_message)
    
    message='Outputing polygons from the Level lines'
    log_message_to_table(log_table, message, CAD_prefix)
    print(message)
    try:
        arcpy.management.FeatureToPolygon(
            in_features=rf"{CAD_prefix}\{CAD_prefix}_Level",
            out_feature_class=rf"{default_gdb}\{CAD_prefix}\{CAD_prefix}_Level_Polygon",
            cluster_tolerance=None,
            attributes="ATTRIBUTES",
            label_features=None
        )
    except Exception as e:
        error_message = f"Error creating polygons from {CAD_prefix}_Level_Polygon: {str(e)}"
        log_message_to_table(log_table, error_message, CAD_prefix)
        print(error_message)
    
    message='Aggregate all level polygons to a whole polygon'
    log_message_to_table(log_table, message, CAD_prefix)
    print(message)
    try:
        arcpy.cartography.AggregatePolygons(
            in_features=rf"{CAD_prefix}\{CAD_prefix}_Level_Polygon",
            out_feature_class=rf"{CAD_prefix}\{CAD_prefix}_Level_Whole",
            aggregation_distance="0.05 Meters",
            minimum_area="0 SquareMeters",
            minimum_hole_size="0 SquareMeters",
            orthogonality_option="NON_ORTHOGONAL",
            barrier_features=None,
            out_table=None,
            aggregate_field=None
        )
    except Exception as e:
        error_message = f"Error creating polygons from {CAD_prefix}_Level_Polygon: {str(e)}"
        log_message_to_table(log_table, error_message, CAD_prefix)
        print(error_message)
    
    message = 'Creating whole outline of the dissolved level polygon for CAD export'
    log_message_to_table(log_table, message, CAD_prefix)
    print(message)
    try:
        arcpy.management.FeatureToLine(
            in_features=rf"{CAD_prefix}\{CAD_prefix}_Level_Whole",
            out_feature_class=rf"{CAD_prefix}\{CAD_prefix}_Arc_Level",
            cluster_tolerance=None,
            attributes="ATTRIBUTES"
        )
    except Exception as e:
        error_message = f"Error exporting Arc_Units for {CAD_prefix}: {str(e)}"
        log_message_to_table(log_table, error_message, CAD_prefix)
        print(error_message)   

    # Section 2: creating Arc_Units, for Units in Import CAD to Indoor Database
    message = 'Creating lines from valid Units Polygons'
    log_message_to_table(log_table, message, CAD_prefix)
    print(message)
    try:
        
        arcpy.management.PolygonToLine(
            in_features=rf"{CAD_prefix}\{CAD_prefix}_Units",
            out_feature_class=rf"{CAD_prefix}\{CAD_prefix}_Arc_Units",
            neighbor_option="IGNORE_NEIGHBORS"
        )
        
    except Exception as e:
        error_message = f"Error creating lines from valid Units Polygons for {CAD_prefix}: {str(e)}"
        log_message_to_table(log_table, error_message, CAD_prefix)
        print(error_message)  
    
    # Section 3: creating Arc_Walls, for details in Import CAD to Indoor Database
    message = 'Buffering Doors_All to be erased from Units_Line'
    log_message_to_table(log_table, message, CAD_prefix)
    print(message)
    try:
        arcpy.analysis.Buffer(
            in_features=rf"{CAD_prefix}\{CAD_prefix}_Doors_All",
            out_feature_class=rf"{CAD_prefix}\{CAD_prefix}_Doors_Buffer",
            buffer_distance_or_field="0.05 Meters",
            line_side="FULL",
            line_end_type="ROUND",
            dissolve_option="NONE",
            dissolve_field=None,
            method="PLANAR"
        )
    except Exception as e:
        error_message = f"Error buffering Doors_All for {CAD_prefix}: {str(e)}"
        log_message_to_table(log_table, error_message, CAD_prefix)
        print(error_message)   
    
    message = 'Erasing Units_Lines with Doors_Buffer to create Arc_Walls for CAD export'
    log_message_to_table(log_table, message, CAD_prefix)
    print(message)
    try:
        arcpy.analysis.Erase(
            in_features=rf"{CAD_prefix}\{CAD_prefix}_Arc_Units",
            erase_features=rf"{CAD_prefix}\{CAD_prefix}_Doors_Buffer",
            out_feature_class=rf"{CAD_prefix}\{CAD_prefix}_Arc_Walls",
            cluster_tolerance=None
        )
    except Exception as e:
        error_message = f"Error erasing Units_Lines with Doors_Buffer for {CAD_prefix}: {str(e)}"
        log_message_to_table(log_table, error_message, CAD_prefix)
        print(error_message)  
        
def export_CAD(CAD_prefix):
    message = 'Exporting Arc_Level, Arc_Units, Arc_Walls to new CAD file'
    log_message_to_table(log_table, message, CAD_prefix)
    print(message)
    try:
        # Check if the folder exists
        if not os.path.exists(CAD_output_dir):
            os.makedirs(CAD_output_dir)
            print(f"Folder '{CAD_output_dir}' created successfully.")
        else:
            # print(f"Folder '{CAD_output_dir}' already exists.")
            pass
        
        arcpy.conversion.ExportCAD(
            in_features=rf"{CAD_prefix}\{CAD_prefix}_Arc_Level;{CAD_prefix}\{CAD_prefix}_Arc_Units;{CAD_prefix}\{CAD_prefix}_Arc_Walls;{CAD_prefix}\{CAD_prefix}_Annotation_Number;{CAD_prefix}\{CAD_prefix}_Annotation_Type",
            Output_Type="DWG_R2018",
            Output_File=os.path.join(CAD_output_dir, f'{CAD_prefix}.dwg'),
            Ignore_FileNames="Ignore_Filenames_in_Tables",
            Append_To_Existing="Overwrite_Existing_Files",
            Seed_File=None
        )
    except Exception as e:
        error_message = f"Error exporting to new CAD file for {CAD_prefix}: {str(e)}"
        log_message_to_table(log_table, error_message, CAD_prefix)
        print(error_message)

def import_CAD(CAD_prefix):
    message = f'Import Arc_Level, Arc_Units, Arc_Walls of layer {CAD_prefix} from CAD file to Indoor Database'
    log_message_to_table(log_table, message, CAD_prefix)
    print(message)
    try:
        # Check if indoor database exists, if not, create a new one
        if not os.path.exists(indoor_gdb_path):
            arcpy.management.CreateFileGDB(
                out_folder_path=arcpy.mp.ArcGISProject("CURRENT").homeFolder,
                out_name=indoor_gdb_name,
                out_version="CURRENT"
            )
            arcpy.indoors.CreateIndoorsDatabase(
                target_gdb=indoor_gdb_path,
                create_network="CREATE_NETWORK",
                spatial_reference=z_coor_system,
                create_attribute_rules="CREATE_RULES"
                )
            print(f"Indoor Database '{indoor_gdb_path}' created successfully.")
        else:
            # print(f"Folder '{CAD_output_dir}' already exists.")
            pass
        
        if str(int(CAD_prefix[-2:])) == '1': # for the first floor, import facility
            arcpy.indoors.ImportCADToIndoorDataset(
                input_cad_datasets=os.path.join(CAD_output_dir, CAD_prefix+'.dwg' ),
                target_level_features=rf"{indoor_gdb_path}\Indoors\Levels",
                level_name=f"L{str(int(CAD_prefix[-2:]))}",  #L1
                vertical_order=int(CAD_prefix[-2:])-1,
                level_elevation=str(int(CAD_prefix[-2:])-1)*5 + " Meters",
                target_facility_features=rf"{indoor_gdb_path}\Indoors\Facilities",
                facility_name=f"SAIT.{CAD_prefix[0]}",  #SAIT.N
                target_unit_features=rf"{indoor_gdb_path}\Indoors\Units",
                target_detail_features=rf"{indoor_gdb_path}\Indoors\Details",
                allow_layers_from_cad="ALLOW_LAYERS_FROM_CAD",
                input_unit_layers_cad=f"{CAD_prefix}_ARC_UNITS",
                input_unit_feature_layers=None,
                input_level_layers_cad=f"{CAD_prefix}_ARC_LEVEL",
                input_level_feature_layers=None,
                input_door_layers_cad=None,
                input_door_feature_layers=None,
                input_detail_layers_cad=f"{CAD_prefix}_ARC_WALLS",
                input_detail_feature_layers=None,
                input_facility_layers_cad=f"{CAD_prefix}_ARC_LEVEL",
                input_facility_feature_layers=None,
                cad_annotation_mapping="Units USE_TYPE Text ANNOTATION_TYPE # # #;Units NAME Text ANNOTATION_NUMBER # # #",
                door_close_buffer="0.0001 InchesInt",
                input_unit_minimum_width="2 FeetInt",
                input_unit_minimum_area="2 SquareFeet"
            )
            
            # update Facility_ID in Facilities to style like "SAIT.N"
            arcpy.management.CalculateField(
                in_table=rf"{indoor_gdb_path}\Indoors\Facilities",
                field="FACILITY_ID",
                expression=f'"SAIT.{CAD_prefix[0]}"',
                expression_type="PYTHON3",
                code_block="",
                field_type="TEXT",
                enforce_domains="NO_ENFORCE_DOMAINS"
            )
            # arcpy.management.AddField(rf"{indoor_gdb_path}\Indoors\Levels", "NAME_LONG", "TEXT")
            
        else: # for layers other than first floor, do not import facility
            arcpy.indoors.ImportCADToIndoorDataset(
                input_cad_datasets=os.path.join(CAD_output_dir, CAD_prefix+'.dwg' ),
                target_level_features=rf"{indoor_gdb_path}\Indoors\Levels",
                level_name=f"L{str(int(CAD_prefix[-2:]))}", #L1
                vertical_order=int(CAD_prefix[-2:])-1,
                level_elevation=str(int(CAD_prefix[-2:])-1)*5 + " Meters",
                target_facility_features=rf"{indoor_gdb_path}\Indoors\Facilities",
                facility_name=f"SAIT.{CAD_prefix[0]}", #SAIT.N
                target_unit_features=rf"{indoor_gdb_path}\Indoors\Units",
                target_detail_features=rf"{indoor_gdb_path}\Indoors\Details",
                allow_layers_from_cad="ALLOW_LAYERS_FROM_CAD",
                input_unit_layers_cad=f"{CAD_prefix}_ARC_UNITS",
                input_unit_feature_layers=None,
                input_level_layers_cad=f"{CAD_prefix}_ARC_LEVEL",
                input_level_feature_layers=None,
                input_door_layers_cad=None,
                input_door_feature_layers=None,
                input_detail_layers_cad=f"{CAD_prefix}_ARC_WALLS",
                input_detail_feature_layers=None,
                cad_annotation_mapping="Units USE_TYPE Text ANNOTATION_TYPE # # #;Units NAME Text ANNOTATION_NUMBER # # #",
                door_close_buffer="0.0001 InchesInt",
                input_unit_minimum_width="2 FeetInt",
                input_unit_minimum_area="2 SquareFeet"
            )
        
        # update Level_ID in Units to style like "SAIT.N.L1"
        level_fc = rf"{indoor_gdb_path}\Indoors\Levels"
        unit_fc = rf"{indoor_gdb_path}\Indoors\Units"
        detail_fc = rf"{indoor_gdb_path}\Indoors\Details"
        Level_ID = ""

        # Step 1: Populate the dictionary with values from the first feature class
        with arcpy.da.SearchCursor(level_fc, ['NAME', 'LEVEL_ID']) as cursor:
            for row in cursor:
                # Store the 'number' value with 'name' as key in the dictionary
                if row[0] == f"L{str(int(CAD_prefix[-2:]))}":
                    Level_ID = row[1]
                    
        with arcpy.da.UpdateCursor(unit_fc, ['LEVEL_ID']) as cursor:
            for row in cursor:
                # Check if the 'name' exists in the dictionary
                if row[0] == Level_ID:
                    # Update the 'number_field_to_populate' with the corresponding value from the dictionary
                    row[0] = f"SAIT.{CAD_prefix[0]}.L{str(int(CAD_prefix[-2:]))}"
                    cursor.updateRow(row)
                    
        with arcpy.da.UpdateCursor(detail_fc, ['LEVEL_ID']) as cursor:
            for row in cursor:
                # Check if the 'name' exists in the dictionary
                if row[0] == Level_ID:
                    # Update the 'number_field_to_populate' with the corresponding value from the dictionary
                    row[0] = f"SAIT.{CAD_prefix[0]}.L{str(int(CAD_prefix[-2:]))}"
                    cursor.updateRow(row)
        
        # update Facility_ID in Levels to style like "SAIT.N"
        arcpy.management.CalculateField(
            in_table=rf"{indoor_gdb_path}\Indoors\Levels",
            field="FACILITY_ID",
            expression=f'"SAIT.{CAD_prefix[0]}"',
            expression_type="PYTHON3",
            code_block="",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        
        # update Level_ID in Levels to style like "SAIT.N.L1"
        arcpy.management.CalculateField(
            in_table=rf"{indoor_gdb_path}\Indoors\Levels",
            field="LEVEL_ID",
            expression=f'"SAIT.{CAD_prefix[0]}.L" + str(!LEVEL_NUMBER!)',
            expression_type="PYTHON3",
            code_block="",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        print(f'import CAD of layer {CAD_prefix} to indoor database complete')
            
    except Exception as e:
        error_message = f"Error importing exported CAD layers to Indoor Database for {CAD_prefix}: {str(e)}"
        log_message_to_table(log_table, error_message, CAD_prefix)
        print(error_message)

def duplicate_empty_prelim_pathway():
    message = 'Create prelim dataset to save intermediate variables for prelim pathways repair'
    log_message_to_table(log_table, message, CAD_prefix)
    print(message)
    try:
        if not arcpy.Exists(rf"{indoor_gdb_path}\Prelims"):
            arcpy.management.CreateFeatureDataset(
                out_dataset_path=rf"{indoor_gdb_path}",
                out_name="Prelims",
                spatial_reference=z_coor_system
            )
        
        arcpy.conversion.ExportFeatures(
            in_features=rf"{indoor_gdb_path}\PrelimNetwork\PrelimPathways",
            out_features=rf"{indoor_gdb_path}\Prelims\Prelim_Backup",
            where_clause="",
            use_field_alias_as_name="NOT_USE_ALIAS",
            field_mapping=None,
            sort_field=None
        )
    except Exception as e:
        error_message = f"Error creating prelim dataset to save intermediate variables for prelim pathways repair: {str(e)}"
        log_message_to_table(log_table, error_message, CAD_prefix)
        print(error_message)

def create_pathways(CAD_prefix):
    arcpy.env.addOutputsToMap = False
    message = f'Create prelim pathways for layer {CAD_prefix}'
    log_message_to_table(log_table, message, CAD_prefix)
    print(message)
    try:
        arcpy.conversion.ExportFeatures(
            in_features=rf"{indoor_gdb_path}\Prelims\Prelim_Backup",
            out_features=rf"{indoor_gdb_path}\Prelims\Prelim",
            where_clause="",
            use_field_alias_as_name="NOT_USE_ALIAS",
            field_mapping=None,
            sort_field=None
        )
        
        arcpy.indoors.GenerateIndoorPathways(
            in_level_features=rf"{indoor_gdb_path}\Indoors\Levels",
            in_detail_features=rf"{indoor_gdb_path}\Indoors\Details",
            target_pathways=rf"{indoor_gdb_path}\Prelims\Prelim",
            lattice_rotation=0,
            lattice_density=1,
            restricted_unit_features=None,
            restricted_unit_exp="",
            detail_exp=f"USE_TYPE = '{CAD_prefix}_Arc_Walls'"
        )
        
        arcpy.management.FeatureVerticesToPoints(
            in_features=rf"{indoor_gdb_path}\Prelims\Prelim",
            out_feature_class=rf"{indoor_gdb_path}\Prelims\Prelim_Point",
            point_location="ALL"
        )
        
        arcpy.analysis.SpatialJoin(
            target_features=rf"{indoor_gdb_path}\Prelims\Prelim_Point",
            join_features=rf"{default_gdb}\{CAD_prefix}\{CAD_prefix}_Doors_All",
            out_feature_class=rf"{indoor_gdb_path}\Prelims\Prelim_Point_Door_Spatial",
            join_operation="JOIN_ONE_TO_ONE",
            join_type="KEEP_ALL",
            field_mapping=None,
            match_option="WITHIN_A_DISTANCE",
            search_radius="1 Meters",
            distance_field_name="",
            match_fields=None
        )
        
        arcpy.conversion.ExportFeatures(
            in_features=rf"{indoor_gdb_path}\Prelims\Prelim_Point_Door_Spatial",
            out_features=rf"{indoor_gdb_path}\Prelims\Prelim_Point_Near_Door",
            where_clause="Join_Count > 0",
            use_field_alias_as_name="NOT_USE_ALIAS",
            field_mapping=None,
            sort_field=None
        )
        
        arcpy.management.DeleteIdentical(
            in_dataset=rf"{indoor_gdb_path}\Prelims\Prelim_Point_Near_Door",
            fields="Shape",
            xy_tolerance="0.01 Meters",
            z_tolerance=0
        )
        
        arcpy.analysis.GenerateNearTable(
            in_features=rf"{indoor_gdb_path}\Prelims\Prelim_Point_Near_Door",
            near_features=rf"{indoor_gdb_path}\Prelims\Prelim_Point_Near_Door",
            out_table=rf"{indoor_gdb_path}\Prelim_Point_Pair",
            search_radius="1.3 Meters",
            location="LOCATION",
            angle="NO_ANGLE",
            closest="ALL",
            closest_count=10,
            method="PLANAR",
            distance_unit="Meters"
        )
        
        arcpy.management.XYToLine(
            in_table=rf"{indoor_gdb_path}\Prelim_Point_Pair",
            out_featureclass=rf"{indoor_gdb_path}\Prelims\Prelim_Extra",
            startx_field="FROM_X",
            starty_field="FROM_Y",
            endx_field="NEAR_X",
            endy_field="NEAR_Y",
            line_type="PLANAR",
            id_field=None,
            spatial_reference=z_coor_system,
            attributes="NO_ATTRIBUTES"
        )
        
        arcpy.analysis.SpatialJoin(
            target_features=rf"{indoor_gdb_path}\Prelims\Prelim_Extra",
            join_features=rf"{default_gdb}\{CAD_prefix}\{CAD_prefix}_Arc_Walls",
            out_feature_class=rf"{indoor_gdb_path}\Prelims\Prelim_Wall_Intersect",
            join_operation="JOIN_ONE_TO_ONE",
            join_type="KEEP_ALL",
            field_mapping=None,
            match_option="INTERSECT",
            search_radius=None,
            distance_field_name="",
            match_fields=None
        )
        
        arcpy.conversion.ExportFeatures(
            in_features=rf"{indoor_gdb_path}\Prelims\Prelim_Wall_Intersect",
            out_features=rf"{indoor_gdb_path}\Prelims\Prelim_NonIntersected",
            where_clause="",
            use_field_alias_as_name="NOT_USE_ALIAS",
            field_mapping=None,
            sort_field=None
        )
        
        arcpy.management.Append(
            inputs=rf"{indoor_gdb_path}\Prelims\Prelim_Extra",
            target=rf"{indoor_gdb_path}\Prelims\Prelim",
            schema_type="NO_TEST",
            field_mapping=None,
            subtype="",
            expression="",
            match_fields=None,
            update_geometry="NOT_UPDATE_GEOMETRY"
        )
        
        # Facility_ID = Facility_Name = SAIT.N
        # From_Level_Name = L1
        # Level_ID = SAIT.N.L1
        
        with arcpy.da.UpdateCursor(rf"{indoor_gdb_path}\Prelims\Prelim", ['FACILITY_ID', 'FACILITY_NAME', 'LEVEL_NAME_FROM', 'LEVEL_ID']) as cursor:
            for row in cursor:
                # Store the 'number' value with 'name' as key in the dictionary
                row[0] = f"SAIT.{CAD_prefix[0]}"
                row[1] = f"SAIT.{CAD_prefix[0]}"
                row[2] = f"L{str(int(CAD_prefix[-2:]))}"
                row[3] = f"SAIT.{CAD_prefix[0]}.L{str(int(CAD_prefix[-2:]))}"
                cursor.updateRow(row)
        
        arcpy.management.Append(
            inputs=rf"{indoor_gdb_path}\Prelims\Prelim",
            target=rf"{indoor_gdb_path}\PrelimNetwork\PrelimPathways",
            schema_type="NO_TEST",
            field_mapping=r'ANGLE "Angle" true true false 4 Long 0 0,First,#,C:\GIS\Capstone\SAIT_Indoor_0927\Indoor.gdb\Prelims\Prelim,ANGLE,-1,-1;DELAY "Delay" true true false 4 Long 0 0,First,#,C:\GIS\Capstone\SAIT_Indoor_0927\Indoor.gdb\Prelims\Prelim,DELAY,-1,-1;FACILITY_ID "Facility ID" true false false 255 Text 0 0,First,#,C:\GIS\Capstone\SAIT_Indoor_0927\Indoor.gdb\Prelims\Prelim,FACILITY_ID,0,254;FACILITY_NAME "Facility Name" true false false 100 Text 0 0,First,#,C:\GIS\Capstone\SAIT_Indoor_0927\Indoor.gdb\Prelims\Prelim,FACILITY_NAME,0,99;LENGTH_3D "Length in 3D" true false false 8 Double 0 0,First,#,C:\GIS\Capstone\SAIT_Indoor_0927\Indoor.gdb\Prelims\Prelim,LENGTH_3D,-1,-1;LEVEL_NAME_FROM "From Level Name" true false false 100 Text 0 0,First,#,C:\GIS\Capstone\SAIT_Indoor_0927\Indoor.gdb\Prelims\Prelim,LEVEL_NAME_FROM,0,99;LEVEL_NAME_TO "To Level Name" true true false 100 Text 0 0,First,#,C:\GIS\Capstone\SAIT_Indoor_0927\Indoor.gdb\Prelims\Prelim,LEVEL_NAME_TO,0,99;PATH_EDGE_DISTANCE "Pathway to Edge Distance" true true false 8 Double 0 0,First,#,C:\GIS\Capstone\SAIT_Indoor_0927\Indoor.gdb\Prelims\Prelim,PATH_EDGE_DISTANCE,-1,-1;PATHWAY_RANK "Pathway Rank" true true false 4 Long 0 0,First,#,C:\GIS\Capstone\SAIT_Indoor_0927\Indoor.gdb\Prelims\Prelim,PATHWAY_RANK,-1,-1;PATHWAY_TYPE "Pathway Type" true true false 4 Long 0 0,First,#,C:\GIS\Capstone\SAIT_Indoor_0927\Indoor.gdb\Prelims\Prelim,PATHWAY_TYPE,-1,-1;TRAVEL_DIRECTION "Travel Direction" true true false 4 Long 0 0,First,#,C:\GIS\Capstone\SAIT_Indoor_0927\Indoor.gdb\Prelims\Prelim,TRAVEL_DIRECTION,-1,-1;VERTICAL_ORDER "Vertical Order" true false false 4 Long 0 0,First,#,C:\GIS\Capstone\SAIT_Indoor_0927\Indoor.gdb\Prelims\Prelim,VERTICAL_ORDER,-1,-1;LEVEL_ID "Level ID" true true false 255 Text 0 0,First,#,C:\GIS\Capstone\SAIT_Indoor_0927\Indoor.gdb\Prelims\Prelim,LEVEL_ID,0,254',
            subtype="",
            expression="",
            match_fields=None,
            update_geometry="NOT_UPDATE_GEOMETRY"
        )
        print(f'prelim pathways for layer {CAD_prefix} completed')

    except Exception as e:
        error_message = f"Error creating prelim pathways for all the layers: {str(e)}"
        log_message_to_table(log_table, error_message, CAD_prefix)
        print(error_message)

def fill_database(CAD_prefix):
    create_log_table()
    create_annotations(CAD_prefix)
    create_Arc(CAD_prefix)
    export_CAD(CAD_prefix)
    import_CAD(CAD_prefix)
    print('Indoor database filled for', CAD_prefix)

# duplicate_empty_prelim_pathway()

def main():
    CAD_prefixs = ['N01', 'N02', 'N03']
    for CAD_prefix in CAD_prefixs:
        fill_database(CAD_prefix)
        create_pathways(CAD_prefix)








