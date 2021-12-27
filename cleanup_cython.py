"""
simple helper script to remove all Cython-generated files and directories generated
"""

import os
import shutil


def get_generated_files(basedir):
    """
    remove all generated .c/.so/.html files
    """

    generated_files = []

    for root, dirs, files in os.walk(basedir):

        # print('FILES: ---------')
        # print('\n'.join(files))
        # print()

        for f in files:

            # e.g. file LICENSE doesn't have an extension at all
            if len(f.split('.')) < 2:
                continue

            fpath = os.path.join(root, f)
            fname, ext = f.split('.')[0], f.split('.')[-1]

            py_file_path = os.path.join(root, fname + '.py')

            if ext in ['c', 'so', 'html'] and os.path.exists(py_file_path):
                generated_files.append(fpath)

    return generated_files


def cleanup():

    os.chdir(os.path.dirname(__file__))

    print('UNINSTALLING RYVENCORE')

    os.system('pip uninstall ryvencore --yes')

    remove_files = get_generated_files('./ryvencore/')

    print('REMOVING FILES\n', '\n'.join(remove_files))

    for f in remove_files:
        os.remove(f)

    print('REMOVING DIRECTORIES')

    dirs = [
        'ryvencore/build',
        'ryvencore/dist',
        'ryvencore/ryvencore.egg-info',
    ]

    for d in dirs:
        print(d)
        shutil.rmtree(d)


if __name__ == '__main__':
    cleanup()
