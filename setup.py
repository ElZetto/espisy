import setuptools
import os 
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="espisy",
    version="0.3.1",
    author="ElZetto",
    author_email="scooby-online@gmx.de",
    description="A tool to access and control ESPEasy devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ElZetto/espisy",
    packages=setuptools.find_packages(),
    package_data={'espisy':['esp.ini']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    scripts=['scripts/espisy_setup.py'],
    install_requires=['requests','pyyaml','colorama'],
    python_requires='>=3.5',
)