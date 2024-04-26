from __future__ import print_function

import setuptools

def readme():
    with open('README.md') as f:
        return f.read()

setuptools.setup(
    name='edtf',
    use_scm_version={'version_scheme': 'post-release'},
    url='https://github.com/ixc/python-edtf',
    author='Greg Turner',
    author_email='greg@interaction.net.au',
    description='Python implementation of Library of Congress EDTF (Extended '
                'Date Time Format) specification',
    long_description=readme(),
    long_description_content_type="text/markdown",
    license='MIT',
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        'python-dateutil',
        'pyparsing',
        'six'
    ],
    extras_require={
        'test': [
            'django',
            'nose',
            'tox',
        ],
    },
    setup_requires=[
        'setuptools_scm',
    ],
    keywords=[
        'edtf',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],
)
