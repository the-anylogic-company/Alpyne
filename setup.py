from setuptools import setup, find_packages

with open("README.md") as f:
    long_description = f.read()

setup(
    name="anylogic-alpyne",
    version="1.2.0",
    author="Tyler Wolfe-Adam",
    author_email="t.wolfeadam@anylogic.com",
    description="Run AnyLogic models exported from the RL Experiment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/t-wolfeadam/Alpyne",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License"
    ],
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.10',
    install_requires=[
        "gymnasium",
        "numpy",
        "psutil",
        "requests"
    ],
    extras_require={
        'examples': [
            "pandas",
            "bayesian-optimization",
            "stable-baselines3",
            "openpyxl",
            "tabulate"
        ]
    }
)
