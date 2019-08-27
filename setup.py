import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aws_tool",
    version="0.0.1",
    author="John Akinyele",
    author_email="alphegasolutions@gmail.com",
    description="AWS Deployment Utility",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alphegasolutions/aws_tool.git",
    license="MIT",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    scripts=['bin/eks-vpc', 'bin/eks-bastion', 'bin/eks-cluster', 'bin/eks-bastion', 'bin/eks-nodes'],
    package_data={'aws_tool': ['../templates/**/**']},
    include_package_data=True,
    install_requires=[
        'boto3'
    ]
)
