#!/usr/bin/env python3
"""
Sensory Music System - Setup Script
Sistema de visualização musical para deficientes auditivos
"""

from setuptools import setup, find_packages
from pathlib import Path

# Ler README
README = Path("README.md").read_text(
    encoding="utf-8") if Path("README.md").exists() else ""

# Ler requirements
REQUIREMENTS = []
if Path("requirements.txt").exists():
    REQUIREMENTS = Path("requirements.txt").read_text().strip().split('\n')
    # Filtrar comentários e linhas vazias
    REQUIREMENTS = [req.strip() for req in REQUIREMENTS
                    if req.strip() and not req.startswith('#')]

setup(
    name="sensory-music-system",
    version="1.0.0",
    author="Seu Nome",
    author_email="seu.email@exemplo.com",
    description="Sistema de visualização musical para deficientes auditivos",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/seuusuario/sensory-music-system",

    # Pacotes
    packages=find_packages(),
    include_package_data=True,

    # Dependências
    install_requires=REQUIREMENTS,

    # Dependências opcionais
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "pytest-cov>=4.1.0"
        ],
        "ai": [
            "tensorflow>=2.13.0",
            "scikit-learn>=1.3.0",
            "opencv-python>=4.8.0"
        ],
        "advanced": [
            "librosa>=0.10.1",
            "numba>=0.57.1",
            "soundfile>=0.12.1"
        ]
    },

    # Classificadores
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Education",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],

    # Versão Python
    python_requires=">=3.8",

    # Scripts de linha de comando
    entry_points={
        "console_scripts": [
            "sensory-music=core.main_visualizer:main",
            "sensory-config=visualization.config_visual:main",
        ],
    },

    # Dados do pacote
    package_data={
        "": ["*.json", "*.md", "*.txt", "*.ino"],
        "data": ["presets/*.json", "calibration/*.json"],
        "docs": ["*.md", "*.pdf"],
        "arduino": ["**/*.ino"],
    },

    # Metadados adicionais
    keywords="audio visualization accessibility music deaf hard-of-hearing arduino",
    project_urls={
        "Bug Reports": "https://github.com/palomaflsette/sensory-translation/issues",
        "Source": "https://github.com/palomaflsette/sensory-translation",
        "Documentation": "https://sensory-translation.readthedocs.io/",
    },
)
