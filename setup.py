from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="repeat-runner",
    version="1.0.0",
    author="Repeat-Runner Team",
    author_email="",
    description="Run your repetitive dev workflows with a single command.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Nom-nom-hub/repeat-runner",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
    install_requires=[
        "PyYAML>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "runner=repeat_runner.runner:main",
        ],
    },
)