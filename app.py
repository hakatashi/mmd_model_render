from hashlib import sha256
import os
from random import choice, randrange, shuffle
import re
import sys
from tempfile import TemporaryDirectory
import unicodedata
import bpy
from mmd_tools.core.pmx.importer import PMXImporter
from mmd_tools.core.vpd.importer import VPDImporter
from mmd_tools.utils import makePmxBoneMap
from mathutils import Vector
from pathlib import Path
from wand.image import Image
import patoolib


reference_head_positions = {
    'back_and_forward_legs': (0.8624, -0.1238, 5.5022),
    'cross_leg': (-0.0700, 0.7380, 14.7587),
    'doggy': (1.0683, -7.6694, 3.5086),
    'doggy_open_legs': (-0.5452, -0.8008, 3.7815),
    'doggy_with_v_sign': (0.4210, -0.4429, 3.4392),
    'facing_upward': (-2.8695, 4.6703, 1.9988),
    'finger_pointing_up': (0.0082, -0.0161, 14.8805),
    'folding_arms_behind_head': (-3.1672, -2.3526, 7.1577),
    'folding_arm_behind_head': (0.5661, 0.1667, 14.9525),
    'goodbye_sengen': (0.5967, -1.2710, 15.2204),
    'holding_leg_upward': (2.4233, -6.7610, 4.4834),
    'jumping': (4.9189, 0.9622, 15.4107),
    'lean_against_desk': (-2.9818, -0.3486, 11.4029),
    'looking_back_with_finger_on_mouth': (-0.0915, -0.7889, 15.0663),
    'lying': (-3.0498, -0.1696, 5.9243),
    'lying_with_v_sign': (-2.8374, 2.4108, 1.6016),
    'm_open': (0.3915, 8.9699, 4.0739),
    'raising_both_hands': (0.0021, 0.0137, 14.3010),
    'shhh': (0.5501, -4.9801, 15.1046),
    'showing_hip': (-0.3387, -4.2471, 4.7365),
    'side_m_open': (10.4957, 8.4770, 4.8509),
    'sitting_bending_backward': (2.2346, -0.2189, 4.4127),
    'sitting_crossing_arms': (0.6635, -0.3354, 7.4524),
    'sitting_self_massage': (0.0000, 0.1768, 8.0641),
    'sitting_with_looking_at_sky': (0.0000, 1.1520, 7.4179),
    'stand1': (0.2857, -0.4290, 15.6331),
    'stand2': (0.0000, -0.6633, 15.2251),
    'stand_back_hand_on_breast': (0.5838, 0.6195, 14.9025),
    'stand_picking_skirt': (-0.4807, -0.5364, 15.7269),
    'waving_hand': (0.3578, -1.1006, 14.8919),
}


expressions = [
    ['笑い', 'にやり'],
    ['じと目', 'う'],
    ['びっくり', 'え', '涙１'],
    ['てへぺろ', '赤面', 'じと目２']
]


expressions_elements = set(sum(expressions, []))


cloth_names = ['スカート', 'ワンピース', 'フリル', '腕カバー', '袖', '下着', 'パンツ', 'ネックカバー', '上着', 'サラシ', '帯', '艤装', '胸飾り', '服', 'ネクタイ', 'スパッツ', 'ドロワ', 'タンクトップ', '水着', 'シャツ', '新規材質', 'boot', 'belt', 'pants', 'swet', 'bakkcle', 'bikini', 'skrt', 'wear', 'stkg', 'cm3d2', 'cos_tex', 'gb_cos']
skin_names = ['の中', '中身', '肌', '体', 'skin', 'nip']


def example_function(model_path, file_hash, skin_mode):
    scene_path = os.getcwd() + '/blend/project.blend'
    # scene_path = os.getcwd() + '/project_dump1.blend'
    bpy.ops.wm.open_mainfile(filepath=scene_path)

    PMXImporter().execute(
        filepath=str(model_path),
        types=set(['MESH', 'ARMATURE', 'PHYSICS', 'MORPHS', 'DISPLAY']),
        clean_model=True,
    )

    empty_images = set()
    for i in bpy.data.images:
        if len(i.pixels) == 0:
            empty_images.add(i.name)

    arm_object = bpy.context.active_object
    for object in bpy.context.scene.collection.children.get('Collection').objects:
        if object.type == 'ARMATURE':
            arm_object = object
    head_bone = arm_object.pose.bones.get('頭')

    bpy.ops.wm.save_as_mainfile(filepath='project_dump1.blend')

    for material in bpy.data.materials:
        if '白目' in material.name or '目白' in material.name:
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

        if skin_mode:
            material_name = unicodedata.normalize('NFKC', material.name)
            is_cloth = any(re.search(cloth_name, material_name, re.IGNORECASE) for cloth_name in cloth_names)
            is_skin = any(re.search(skin_name, material_name, re.IGNORECASE) for skin_name in skin_names)
            if is_cloth:
                material.mmd_material.alpha = 0.0
                pass
            if is_skin:
                material.mmd_material.alpha = 1.0
                pass

        if material.node_tree is not None:
            for node in material.node_tree.nodes:
                if node.name in ['mmd_base_tex', 'mmd_toon_tex', 'mmd_sphere_tex']:
                    if node.image.name in empty_images:
                        material.node_tree.nodes.remove(node)

    bpy.ops.wm.save_as_mainfile(filepath='project_dump.blend')

    Path('outputs').mkdir(parents=True, exist_ok=True)

    pose_files = os.listdir('poses')
    for pose_file in pose_files:
        pose_name = pose_file[:-4]

        i = randrange(10)
        if i < 4:
            expression = expressions[i]
        else:
            expression = []
        
        shape_key = bpy.data.shape_keys.get('Key')
        if shape_key is not None:
            for expressions_element in expressions_elements:
                key_block = shape_key.key_blocks.get(expressions_element)
                if key_block is not None:
                    if expressions_element in expression:
                        key_block.value = 1.0
                    else:
                        key_block.value = 0.0
            for material in bpy.data.materials:
                if material.name == '赤面':
                    if '赤面' in expression:
                        material.mmd_material.alpha = 1.0
                    else:
                        material.mmd_material.alpha = 0.0

        importer = VPDImporter(
            filepath=os.path.join(os.getcwd(), f'poses/{pose_name}.vpd'),
            bone_mapper=makePmxBoneMap,
        )
        importer.assign(arm_object)

        target_camera = bpy.context.scene.objects[f'{pose_name}_camera']

        if head_bone is not None:
            head_position = arm_object.location + head_bone.head
            reference_head_position = reference_head_positions.get(pose_name)

            if 'Rushia' in str(model_path):
                file_object = open('sample.txt', 'a')
                file_object.write(f"    '{pose_name}': {head_position},\n")
                file_object.close()
            if reference_head_position is not None:
                target_camera.location += head_position - Vector(reference_head_position)

        bpy.context.scene.camera = target_camera

        mode = 'original' if skin_mode == False else 'nude'
        png_filename = os.getcwd() + f'/outputs/{file_hash}/{mode}/render_{pose_name}.png'
        webp_filename = os.getcwd() + f'/outputs/{file_hash}/{mode}/render_{pose_name}.webp'

        render = bpy.context.scene.render
        render.use_file_extension = True
        render.filepath = png_filename
        bpy.ops.render.render(write_still=True)

        with Image(filename=png_filename) as img:
            img.format = 'webp'
            img.compression_quality = 90
            img.save(filename=webp_filename)

        Path(png_filename).unlink()


if __name__ == "__main__":
    # example_function(sys.argv[5])
    models_dir = Path('Z:\\Data\\Models')
    model_files = list(models_dir.iterdir())
    shuffle(model_files)

    for model_file in model_files:
        model_file = choice(model_files)
        model_file_name = bytes(model_file.relative_to(models_dir))
        print(model_file.absolute())

        with TemporaryDirectory() as tmpdir:
            patoolib.extract_archive(str(model_file.absolute()), outdir=tmpdir)
            try:
                for f in Path(tmpdir).rglob('*'):
                    filename = bytes(f.relative_to(tmpdir))
                    if filename.decode().endswith('.pmx'):
                        print(f'Processing {filename.decode()}...')
                        file_hash_key = model_file_name + b'\\' + filename
                        file_hash = sha256()
                        file_hash.update(file_hash_key)
                        with open('hashes.txt', 'a') as hashes_file:
                            hashes_file.write(f"    {file_hash_key}: '{file_hash.hexdigest()}',\n")
                        for skin_mode in [True, False]:
                            example_function(f, file_hash=file_hash.hexdigest(), skin_mode=skin_mode)
            except Exception as e:
                print(e)
