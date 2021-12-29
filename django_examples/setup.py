import setuptools

setuptools.setup(
    name="ajax-examples",
    version="0.0.2",
    author="Ian Jones",
    description="Ajax examples",
    include_package_data = True,
    packages=['ajax_examples'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=['openpyxl>=3.0.7'],
)
