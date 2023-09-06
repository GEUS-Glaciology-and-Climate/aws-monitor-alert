import setuptools

setuptools.setup(
    name="aws-monitor-alert",
    version="0.1.0",
    author="GEUS Glaciology and Climate",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.8",
    requires=[]
)