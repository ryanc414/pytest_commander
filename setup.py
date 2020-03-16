import setuptools


def main():
    setuptools.setup(
        name="pytest_web_ui",
        version="0.0.1",
        author="Ryan Collingham",
        author_email="ryanc118@gmail.com",
        description="An interactive web UI test runner for PyTest",
        packages=setuptools.find_packages(),
        python_requires=">=3.6",
    )


if __name__ == "__main__":
    main()
