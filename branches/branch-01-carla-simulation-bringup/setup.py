import os
from glob import glob
from setuptools import setup

package_name = 'pothole_simulation_bringup'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name] if os.path.exists(package_name) else [],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name] if os.path.exists('resource/' + package_name) else []),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.*')),
        (os.path.join('share', package_name, 'scripts'), glob('scripts/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Person 1 - Simulation Architect',
    maintainer_email='engineer@antigravity.internal',
    description='Person 1 Module: CARLA Digital Twin & Sensor Rig',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'telemetry_health_monitor = scripts.telemetry_health_monitor:main',
            'weather_and_pothole_spawner = scripts.weather_and_pothole_spawner:main',
        ],
    },
)
