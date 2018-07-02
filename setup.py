import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="silkaj",
    version="0.6.0",
    author="Moul",
    author_email="moul@moul.re",
    description="Command line client for Duniter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.duniter.org/clients/python/silkaj",
    license='GNU AGPLv3',
    packages=setuptools.find_packages(),
    keywords='g1 duniter cryptocurrency librecurrency RTM',
    classifiers=(
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3 :: Only',
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        "commandlines",
        "ipaddress",
        "tabulate",
        "pynacl",
        "scrypt",
        "pyaes",
    ],
    scripts=[
        'bin/silkaj',
    ],
)
