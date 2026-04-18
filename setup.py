from setuptools import setup, find_packages

setup(
    name="gitspy",
    version="1.0.0",
    packages=find_packages(),
    py_modules=["main"],
    install_requires=[
        "git_index_parser==1.0.0",
        "Requests==2.32.3",
        "tqdm==4.66.5",
        "urllib3==2.2.3",
    ],
    entry_points={
        "console_scripts": [
            "gitspy=main:main",
        ],
    },
    author="nikitacontreras",
    description="GitSpy - Extract .git folders from websites",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    python_requires=">=3.6",
)
