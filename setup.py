from setuptools import Extension, setup

setup(
    name="gaussian-blur-cpp",
    version="0.1.0",
    ext_modules=[Extension("gaussian_blur_cpp", ["gaussian_blur.cpp"], language="c++")],
)