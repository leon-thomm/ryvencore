from setuptools import setup



setup(
    name='ryvencore',
    version='0.0.0',
    license='MIT',
    description='Qt based library for making flow-based visual programming editors',
    author='Leon Thomm',
    author_email='l.thomm@mailbox.org',
    packages=[
        'ryvencore',
        'ryvencore.resources',
        'ryvencore.src',
        'ryvencore.src.custom_list_widgets',
        'ryvencore.src.logging',
        'ryvencore.src.node_selection_widget',
        'ryvencore.src.script_variables',
    ],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    python_requires='>=3.8',
    install_requires=['PySide2'],
)
