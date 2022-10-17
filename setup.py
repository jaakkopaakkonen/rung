from setuptools import find_packages
from setuptools import setup

setup(
    name="glu",
    description="Framework for running and integrating tasks together",
    author="jaakko.t.paakkonen@gmail.com",
    version=1,
    requires=[
        "colorama",
        "gitpython",
    ],
    install_requires=[
        "gitpython",
        "colorama",
    ],
    packages=find_packages(
        exclude=[]
    ),
    scripts=[],
    entry_points={
        'console_scripts': ['glu=glu.glu:main'],
    },
    zip_safe=False,
    tests_require=[],
)
