from setuptools import setup, find_packages

setup(
    name="adkdocs",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "google-adk",
        "python-dotenv",
    ],
) 