from setuptools import setup, find_packages

setup(
    name="NVLib",
    version="0.1.0",
    author="Sai Neela",
    author_email="saiathulithn@gmail.com",
    description="A Python Library that makes everything easy to code for Anyone and Everyone",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/saineela/NVLib",
    packages=find_packages(),
    license="CC0-1.0",
    install_requires=open("requirements.txt").read().splitlines(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires=">=3.6",
)
