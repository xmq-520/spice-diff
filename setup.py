"""M0 兼容层：本机 setuptools 为 58.1.0（无 PEP 643、缺 bdist_wheel），
无法直接吃 pyproject 的 [project] 表。此文件把同一份元数据以经典 setup()
形式再声明一遍，供 pip --no-build-isolation 使用。

⚠️ 单一事实来源仍是 pyproject.toml。Codex 若要改构建配置，请在群里提意见
（PLAN.md 第 1 节：pyproject.toml 归 dsh）。等陛下允许联网装新 setuptools/wheel
后，本文件即可删除。
"""

from setuptools import find_packages, setup

setup(
    name="spice-diff",
    version="0.1.0",
    description="Structural change report between two SPICE netlists (revision review, not LVS).",
    long_description=open("README.md", encoding="utf-8").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    python_requires=">=3.9",
    license="MIT",
    author="XMQ",
    keywords="spice, ngspice, netlist, diff, eda",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[],
    entry_points={"console_scripts": ["spdiff = spice_diff.cli:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
)
