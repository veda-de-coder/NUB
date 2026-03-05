from setuptools import setup, find_packages

setup(
    name="nub-vcs",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # curses is built-in on Linux/macOS, Windows users need:
        "windows-curses; platform_system=='Windows'",
    ],
    entry_points={
        "console_scripts": [
            "nub=nub.cli:main",
        ],
    },
    author="Veda Narasimhan",
    author_email="vedanarasimhan08@gmail.com",
    description="NUB: The Personal Version Vault (Beta)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/veda-de-coder/NUB",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
