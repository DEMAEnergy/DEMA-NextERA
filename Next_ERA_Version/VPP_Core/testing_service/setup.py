from setuptools import setup, find_packages

setup(
    name="vpp-testing-service",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.68.0,<0.69.0",
        "pydantic>=1.8.2,<2.0.0",
        "httpx>=0.23.0,<0.24.0",
        "uvicorn>=0.15.0",
        "pytest>=7.0.0",
        "pytest-asyncio>=0.18.0",
        "pytest-cov>=3.0.0",
        "aioresponses>=0.7.0",
        "pytest-mock>=3.7.0",
        "pytest-env>=0.6.0",
        "pytest-xdist>=2.5.0",
        "starlette>=0.14.2,<0.15.0",
    ],
) 