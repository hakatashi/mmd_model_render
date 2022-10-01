import os
import sys
import bpy
from mmd_tools.core.pmx.importer import PMXImporter
from mmd_tools.core.vpd.importer import VPDImporter
from mmd_tools.utils import makePmxBoneMap


def example_function(model_path):
    render_path = os.getcwd() + '/render.png'
    scene_path = os.getcwd() + '/blend/project.blend'
    # scene_path = os.getcwd() + '/project.blend'
    bpy.ops.wm.open_mainfile(filepath=scene_path)

    PMXImporter().execute(
        filepath=model_path,
        types=set(['MESH', 'ARMATURE', 'PHYSICS', 'MORPHS', 'DISPLAY']),
        clean_model=True,
    )

    model_object = bpy.context.active_object
    for object in bpy.context.scene.collection.children.get('Collection').objects:
        if object.type == 'ARMATURE':
            model_object = object

    for material in bpy.data.materials:
        if '白目' in material.name:
            mmd_base_tex = material.node_tree.nodes.get('mmd_base_tex')
            material_output = material.node_tree.nodes.get('Material Output')

            emission = material.node_tree.nodes.new('ShaderNodeEmission')
            emission.inputs.get('Strength').default_value = 0.8

            material.node_tree.links.new(
                emission.outputs.get('Emission'),
                material_output.inputs.get('Surface')
            )
            material.node_tree.links.new(
                mmd_base_tex.outputs.get('Color'),
                emission.inputs.get('Color')
            )
            material.node_tree.links.new(
                mmd_base_tex.outputs.get('Alpha'),
                emission.inputs.get('Strength')
            )

            mmd_shader = material.node_tree.nodes.get('mmd_shader')
            if mmd_shader is None:
                continue

            diffuse_input = mmd_shader.inputs.get('Diffuse Color')
            if diffuse_input is None:
                continue

            diffuse_input.default_value = (1.0, 0.0, 0.0, 1.0)

    importer = VPDImporter(
        filepath=os.path.join(os.getcwd(), 'poses/stand1.vpd'),
        bone_mapper=makePmxBoneMap,
    )
    importer.assign(model_object)

    bpy.ops.wm.save_as_mainfile(filepath='project_dump.blend')

    render = bpy.context.scene.render
    render.use_file_extension = True
    render.filepath = render_path
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    example_function(sys.argv[5])