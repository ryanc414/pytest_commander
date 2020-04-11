"""Setup script for PyTest web UI."""
import setuptools


def main():
    with open("README.md") as f:
        long_description = f.read()

    setuptools.setup(
        name="pytest_web_ui",
        version="0.0.1",
        author="Ryan Collingham",
        author_email="ryanc118@gmail.com",
        description="An interactive web UI test runner for PyTest",
        long_description=long_description,
        long_description_content_type="test/markdown",
        url="https://github.com/ryanc414/pytest_web_ui",
        packages=setuptools.find_packages(),
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
        python_requires=">=3.6",
        install_requires=[
            "pytest>=5.0.0",
            "marshmallow>=3.0.0",
            "marshmallow-enum",
            "flask>=1.0",
            "flask-socketio>=4.0.0",
            "eventlet",
        ],
        include_package_data=True,
        entry_points={
            "console_scripts": ["pytest_web_ui = pytest_web_ui.__main__:main"]
        },
    )


if __name__ == "__main__":
    main()
