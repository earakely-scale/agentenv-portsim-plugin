# The PortSim env: the berth-planning MCP server with the dock-v1 task packs, on port 18765.
#   Build: agent-env portsim setup   (docker build -t agentenv-portsim-env .)
FROM python:3.12-slim
LABEL org.opencontainers.image.source="https://github.com/earakely-scale/agentenv-portsim-plugin" \
      org.opencontainers.image.licenses="Apache-2.0 AND CC-BY-SA-4.0" \
      org.opencontainers.image.description="PortSimEnv as an AgentEnv environment. Contains data from the Port de Barcelona open data portal. Contains modified ECMWF open data (CC BY 4.0, © ECMWF) and wind windows derived from the Servei Meteorològic de Catalunya's (Meteocat) XEMA station Y7."
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    BERTH_TASKS_DIR=/app/data/dock-v1-eval:/app/data/dock-v1-train
RUN pip install "agentenv-framework-protocol==0.1.290" "fastmcp==3.4.8" "mcp==1.30.0" "pydantic==2.13.5" \
    "berth-core @ https://github.com/adithya-s-k/FineEnvs/archive/b0f4c2f9526e3c45d608b4f92f6ec6c71fecc152.tar.gz#subdirectory=07-simulation-environments/portsim-v1/envs/berth_planning/core"
WORKDIR /app
COPY LICENSE NOTICE /app/
COPY data /app/data
COPY src/agentenv_portsim /app/agentenv_portsim
RUN useradd --create-home --uid 1000 portsim
USER portsim
EXPOSE 18765
CMD ["python", "-m", "agentenv_portsim.server"]
