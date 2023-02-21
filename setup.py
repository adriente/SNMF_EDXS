import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='pyESM',
    version='0.1.1',
    description='Electron Spectro-Microscopy Python Library',
    url='https://github.com/adriente/pyesm',
    author='Adrien Teurtie, Nathanael Perraudin',
    author_email='nathanael.perraudin@sdsc.ethz.ch',
    license='MIT',
    packages=setuptools.find_packages(),
    zip_safe=False,
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={'hyperspy.extensions': 'pyesm = pyesm'},
    extras_require={'dev': [
        'flake8', 'pytest', 'jupyterlab', 'twine', 'setuptools', 'wheel', 
        'sphinx','numpydoc','sphinxcontrib-bibtex','sphinx-gallery',
        'memory_profiler','sphinx-rtd-theme','sphinx-copybutton', 'nbsphinx'
        ]},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers', 'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux', 'Programming Language :: C',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering'
    ],
    install_requires=[
        'hyperspy', 'tqdm', 'lmfit', 'scikit-learn'
    ],
    python_requires='>=3.7',
)