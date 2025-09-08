from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aivo-sdk-py",
    version="1.0.0",
    author="Aivo Team",
    author_email="api-support@aivo.com",
    description="Python SDK for Aivo API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/artpromedia/aivo",
    project_urls={
        "Bug Tracker": "https://github.com/artpromedia/aivo/issues",
        "Documentation": "https://docs.aivo.com",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "urllib3>=1.26.0",
        "python-dateutil>=2.8.0",
        "pydantic>=1.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ]
    },
)
