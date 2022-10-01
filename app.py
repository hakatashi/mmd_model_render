import os
import sys
import bpy
from mmd_tools.core.pmx.importer import PMXImporter


def example_function(model_path):
    render_path = os.getcwd() + '/render.png'
    scene_path = os.getcwd() + '/blend/scene.blend'
    bpy.ops.wm.open_mainfile(filepath=scene_path)
    bpy.ops.wm.save_as_mainfile(filepath='project.blend')

    PMXImporter().execute(
        filepath=model_path,
        types=set(['MESH', 'ARMATURE', 'PHYSICS', 'MORPHS', 'DISPLAY']),
        clean_model=True,
    )

    scene = bpy.context.scene

    bpy.ops.wm.save_as_mainfile(filepath='project.blend')

    render = scene.render
    render.use_file_extension = True
    render.filepath = render_path
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    example_function(sys.argv[4])