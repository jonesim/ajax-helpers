import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django-ajax-helpers",
    version="0.0.17",
    author="Ian Jones",
    description="Django app to assist with posting Ajax and receiving commands from django",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jonesim/ajax-helpers",
    include_package_data = True,
    packages=['ajax_helpers'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
