from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="silkaj",
    version="0.7.5",
    author="Moul",
    author_email="moul@moul.re",
    description="Command line client for Duniter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.duniter.org/clients/python/silkaj",
    license="GNU AGPLv3",
    packages=find_packages(),
    keywords="g1 duniter cryptocurrency librecurrency RTM",
    classifiers=(
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3 :: Only",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Natural Language :: English",
    ),
    install_requires=[
        "Click",
        "duniterpy==0.54.3",
        "ipaddress",
        "texttable",
        "tabulate",
        "pynacl",
    ],
    scripts=["bin/silkaj"],
)
