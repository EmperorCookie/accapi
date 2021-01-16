from setuptools import setup, find_packages
import os

# Get PWD for external information
pwd = os.path.abspath(os.path.dirname(__file__))

# README.md
with open(os.path.join(pwd, "README.md"), "r") as f:
    readme = f.read()

# Requirements
with open(os.path.join(pwd, "requirements.txt"), "r") as f:
    requirements = f.read().splitlines()

setup(
    name="accapi",
    version=os.environ.get("ACCAPI_VERSION", "0.0.1"),
    license="GPLv3",
    description="Assetto Corsa Competizione UDP broadcast API wrapper.",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Fred Dufresne",
    author_email="frederick.dufresne@gmail.com",
    url="https://github.com/EmperorCookie",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
    ],
    project_urls={
        "Source": "https://github.com/EmperorCookie/accapi",
    },
    python_requires=">=3.8",
    install_requires=requirements,
    tests_require=[
        # eg: "aspectlib==1.1.1", "six>=1.7",
    ],
    extras_require={
        # eg:
        #   "rst": ["docutils>=0.11"],
        #   ":python_version=="2.6"": ["argparse"],
    },
    entry_points={
        # eg:
        # "console_scripts":
        # [
        #     "cthun = cthun.commandline:main",
        # ]
    },
)
