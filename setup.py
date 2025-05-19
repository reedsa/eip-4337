from setuptools import find_packages, setup

setup(
    name="eip-4337",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    author="Stuart Reed",
    author_email="stuart.reed@ethereum.org",
    description="A development tool for learning about EIP-4337 Account Abstraction",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/reedsa/eip-4337-cli",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)
