from setuptools import setup, find_packages
import os
import spygame as spyg


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()

setup(
    name="spygame",
    version=spyg.RELEASE_,
    packages=find_packages(),
    url="http://www.github.com/sven1977/spygame",
    download_url="https://github.com/sven1977/spygame/archive/spygame-"+spyg.VERSION_+".zip",
    license="MIT",
    author="Sven Mika",
    author_email="sven.mika@ducandu.com",
    description="2D game engine based on pygame and level-tmx files (soon to be: fully openAI gym integrated)",
    long_description=read("README.rst"),
    install_requires=["pygame", "pytmx", "numpy"],
    keywords=["python-3", "pygame", "2d-game-engine", "tmx-files", "game-engine-library", "reinforcement-learning",
              "openai-gym", "openai-rllab", "game-engine", "the-lost-vikings", "lost-viking-game"],
)
