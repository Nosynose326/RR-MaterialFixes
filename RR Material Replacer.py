bl_info = {
    "name": "RR Material Replacement",
    "author": "Nosynose326",
    "version": (1, 7),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > RR Material Replacement",
    "description": "Replaces materials based on a user-defined file path.",
    "category": "Material",
}

import bpy
import os

# --- COLOR DATA & CONVERSION ---

def hex_to_linear_rgba(hex_str):
    hex_str = hex_str.lstrip('#')
    rgba = [int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4, 6)]
    for i in range(3):
        if rgba[i] <= 0.04045: rgba[i] = rgba[i] / 12.92
        else: rgba[i] = ((rgba[i] + 0.055) / 1.055) ** 2.4
    return tuple(rgba)

COLOR_LIST = {
    "salmon": "#DF5350FF", "red": "#D11F2CFF", "garnet": "#7F192AFF",
    "venetian": "#843439FF", "cantaloupe": "#E97F50FF", "orange": "#ED5F2EFF",
    "topaz": "#C23D29FF", "sienna": "#874739FF", "pineapple": "#F0CF64FF",
    "yellow": "#EEBF2DFF", "amber": "#B66627FF", "ochre": "#8B633FFF",
    "sage": "#92AC51FF", "chartreuse": "#749F2CFF", "peridot": "#335129FF",
    "terre verte": "#4B5637FF", "mint": "#73B872FF", "green": "#006732FF",
    "emerald": "#00402AFF", "viridian": "#384F3FFF", "hydrangea": "#73D2BAFF",
    "teal": "#00997FFF", "turquoise": "#00534BFF", "aegean": "#3C5A53FF",
    "cornflower": "#71C1D5FF", "cyan": "#00A8D3FF", "sapphire": "#005A6EFF",
    "prussian": "#385F66FF", "periwinkle": "#709EDDFF", "blue": "#0C6CC9FF",
    "lapis": "#003D77FF", "ultramarine": "#385372FF", "lilac": "#AB85DBFF",
    "violet": "#5920C9FF", "tanzanite": "#322071FF", "indigo": "#604D71FF",
    "lavender": "#DD93DBFF", "purple": "#81477AFF", "amethyst": "#481F4BFF",
    "mauve": "#62425BFF", "rose": "#E779A3FF", "pink": "#E43450FF",
    "ruby": "#8A1945FF", "alizarin": "#713D4FFF", "caramel": "#86452CFF",
    "chocolate": "#4D2D2DFF", "mocha": "#45252AFF", "espresso": "#261926FF",
    "tawny": "#C58459FF", "leather": "#966549FF", "brown": "#64453BFF",
    "burnt umber": "#26252DFF", "white": "#EFE4D2FF", "mist": "#C1B7A9FF",
    "fog": "#9F9487FF", "gray": "#857970FF", "slate": "#6C6562FF",
    "smoke": "#524D4FFF", "charcoal": "#2D353BFF", "black": "#08202DFF"
}

# --- OPERATOR ---

class MATERIAL_OT_RRReplace(bpy.types.Operator):
    bl_idname = "material.rr_replace"
    bl_label = "Replace Materials"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Get the path from the UI text box
        raw_path = context.scene.rr_material_path
        filepath = bpy.path.abspath(raw_path)
        
        if not filepath or not os.path.exists(filepath):
            self.report({'ERROR'}, f"Invalid Path: '{filepath}' does not exist.")
            return {'CANCELLED'}

        # Append Node Groups
        try:
            with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
                data_to.node_groups = data_from.node_groups
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load file: {e}")
            return {'CANCELLED'}

        converted_count = 0
        for mat in bpy.data.materials:
            if "_" not in mat.name: continue
            parts = mat.name.split("_")
            if len(parts) < 2: continue
            
            color_part = parts[0].strip().lower()
            group_part = parts[1].strip().lower()

            matching_group = next((ng for ng in bpy.data.node_groups if ng.name.lower() == group_part), None)
            
            if matching_group:
                mat.use_nodes = True
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                nodes.clear()
                
                group_node = nodes.new(type='ShaderNodeGroup')
                group_node.node_tree = matching_group
                output_node = nodes.new(type='ShaderNodeOutputMaterial')
                output_node.location = (300, 0)
                
                if group_node.outputs and output_node.inputs:
                    links.new(group_node.outputs[0], output_node.inputs[0])

                if color_part in COLOR_LIST:
                    rgba = hex_to_linear_rgba(COLOR_LIST[color_part])
                    for inp in group_node.inputs:
                        if "color" in inp.name.lower():
                            inp.default_value = rgba
                converted_count += 1

        self.report({'INFO'}, f"Processed {converted_count} materials using: {filepath}")
        return {'FINISHED'}

# --- PANEL ---

class MATERIAL_PT_RRPanel(bpy.types.Panel):
    bl_label = "RR Material Tools"
    bl_idname = "MATERIAL_PT_rr_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RR Material Replacement'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.label(text="RRObjects.blend File Path:")
        layout.prop(scene, "rr_material_path", text="")
        
        layout.separator()
        layout.operator("material.rr_replace", text="Replace Materials", icon='NODE_MATERIAL')

# --- REGISTRATION ---

def register():
    # Adding a string property to the scene to store the path
    bpy.types.Scene.rr_material_path = bpy.props.StringProperty(
        name="File Path",
        description="Path to the RRObjects.blend file",
        default="",
        subtype='FILE_PATH' # This adds a folder icon to the text box
    )
    bpy.utils.register_class(MATERIAL_OT_RRReplace)
    bpy.utils.register_class(MATERIAL_PT_RRPanel)

def unregister():
    bpy.utils.unregister_class(MATERIAL_OT_RRReplace)
    bpy.utils.unregister_class(MATERIAL_PT_RRPanel)
    del bpy.types.Scene.rr_material_path

if __name__ == "__main__":
    register()
