from setuptools import setup, find_packages


setup(
    name='ryvencore',
    version='0.0.1',
    description='PySide-based library for creating flow-based visual programming editors',
    py_modules=['ryvencore'],
    package_dir={'': 'src'}
)

# setup(
#     name='ryvencore',
#     version='0.1',
#     license='MIT',
#     description='ryvencore description',
#     # packages=find_packages(),
#     py_modules=['rc'],
#     classifiers=[
#         "Programming Language :: Python :: 3"
#     ],
#     python_requires='>=3.6',
#     author='Leon Thomm',
#     author_email='l.thomm@mailbox.org'
# )