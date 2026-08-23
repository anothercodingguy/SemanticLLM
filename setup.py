from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="semantic-llm",
    version="2.0.0",
    author="Semantic LLM Team",
    author_email="hello@semanticllm.ai",
    description="Query-Aware Neural Context Compression, Semantic Vector Caching & Complexity Routing Gateway for LLMs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anothercodingguy/SemanticLLM",
    packages=find_packages(include=["api*", "core*", "schemas*", "services*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "httpx>=0.24.0",
        "groq>=0.4.0",
        "qdrant-client>=1.7.0",
        "redis>=5.0.0",
        "python-dotenv>=1.0.0",
        "fastembed>=0.2.0",
    ],
    entry_points={
        "console_scripts": [
            "semantic-gateway=main:app",
        ],
    },
)
