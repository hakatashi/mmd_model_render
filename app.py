import os
import sys
import bpy
from mmd_tools.core.pmx.importer import PMXImporter
from mmd_tools.core.vpd.importer import VPDImporter
from mmd_tools.utils import makePmxBoneMap
from pathlib import Path


cloth_names = ['スカート', 'ワンピース', 'フリル', '腕カバー', '袖', '下着', 'パンツ', 'ネックカバー', '上着', 'サラシ', '帯', '艤装', '胸飾り', '服', '新規材質']
skin_names = ['の中', '中身', '肌', '体']


def example_function(model_path):
    scene_path = os.getcwd() + '/blend/project.blend'
    # scene_path = os.getcwd() + '/project.blend'
    bpy.ops.wm.open_mainfile(filepath=scene_path)

    PMXImporter().execute(
        filepath=model_path,
        types=set(['MESH', 'ARMATURE', 'PHYSICS', 'MORPHS', 'DISPLAY']),
        clean_model=True,
    )

    arm_object = bpy.context.active_object
    for object in bpy.context.scene.collection.children.get('Collection').objects:
        if object.type == 'ARMATURE':
            arm_object = object

    bpy.ops.wm.save_as_mainfile(filepath='project_dump1.blend')

    for material in bpy.data.materials:
        if '白目' in material.name:
            mmd_base_tex = material.node_tree.nodes.get('mmd_base_tex')
            material_output = material.node_tree.nodes.get('Material Output')

            emission = material.node_tree.nodes.new('ShaderNodeEmission')
            emission.inputs.get('Strength').default_value = 0.8

            if material_output is not None:
                material.node_tree.links.new(
                    emission.outputs.get('Emission'),
                    material_output.inputs.get('Surface')
                )

            if mmd_base_tex is not None:
                material.node_tree.links.new(
                    mmd_base_tex.outputs.get('Color'),
                    emission.inputs.get('Color')
                )
                material.node_tree.links.new(
                    mmd_base_tex.outputs.get('Alpha'),
                    emission.inputs.get('Strength')
                )

        is_cloth = any(cloth_name in material.name for cloth_name in cloth_names)
        is_skin = any(skin_name in material.name for skin_name in skin_names)
        if is_cloth:
            material.mmd_material.alpha = 0.0
            pass
        if is_skin:
            material.mmd_material.alpha = 1.0
            pass

    bpy.ops.wm.save_as_mainfile(filepath='project_dump.blend')

    Path('outputs').mkdir(parents=True, exist_ok=True)

    pose_files = os.listdir('poses')
    for pose_file in pose_files:
        pose_name = pose_file[:-4]

        importer = VPDImporter(
            filepath=os.path.join(os.getcwd(), f'poses/{pose_name}.vpd'),
            bone_mapper=makePmxBoneMap,
        )
        importer.assign(arm_object)

        bpy.context.scene.camera = bpy.context.scene.objects[f'{pose_name}_camera']

        render = bpy.context.scene.render
        render.use_file_extension = True
        render.filepath = os.getcwd() + f'/outputs/render_{pose_name}.png'
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    example_function(sys.argv[5])