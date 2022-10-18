from setuptools import find_packages
from setuptools import setup

setup(
    name="rung",
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
        'console_scripts': ['rung=rung.rung:main'],
    },
    zip_safe=False,
    tests_require=[],
)
