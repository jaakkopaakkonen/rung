from setuptools import find_packages
from setuptools import setup

setup(
    name="nurmi",
    description="Runs steps",
    author="jaakko.t.paakkonen@gmail.com",
    version=1,
    requires=[],
    install_requires=["gitpython"],
    packages=find_packages(
        exclude=[]
    ),
    scripts=[],
    entry_points={
        'console_scripts': ['nurmi=nurmi.nrmi:main'],
    },
    zip_safe=False,
    tests_require=[]
)
