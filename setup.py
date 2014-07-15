import os

from setuptools import find_packages
from setuptools import setup


def parse_requirements_txt():
    root = os.path.dirname(os.path.abspath(__file__))
    requirements = []
    with open(os.path.join(root, 'requirements.txt'), 'r') as f:
        for line in f.readlines():
            line = line.rstrip()
            if not line or line.startswith('#'):
                continue
            requirements.append(line)
    return requirements


setup(
    name='launchpad_report',
    version='0.0.1',
    description='Find inconsistencies in launchpad blueprints and bugs',
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Utilities"
    ],
    author='Mirantis Inc.',
    author_email='dpyzhov@mirantis.com',
    url='http://wiki.openstack.org/wiki/Fuel',
    packages=find_packages(),
    zip_safe=False,
    install_requires=parse_requirements_txt(),
    include_package_data=True,
    package_data={'': ['*.yaml']},
    entry_points={'console_scripts': ['l-report = launchpad_report.cli:main']}
)
