import io
import os

from setuptools import setup, find_packages

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


install_requires = [
    "influxdb",
]

setup(
    name='jmon',
    version='0.260',
    py_modules = ['jmon'],  
    packages=find_packages(exclude=['tests']),
    install_requires=install_requires,
    include_package_data=True,
    url='https://github.com/jjeaby/CudaInfo2InfluxDB',
    license='Apache 2.0',
    author='Lee Yong Jin',
    author_email='jjeaby@gmail.com',
    long_description=open('README.md').read(),
    zip_safe=False,
    classifiers      = [
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ]
)
