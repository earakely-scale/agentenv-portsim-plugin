# Replays the runs in earakely-scale/PortSimEnv-AgentEnv on PortSimEnv's 3D viewer, through agent-env portsim view.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN useradd --create-home --uid 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH
WORKDIR /home/user/app
RUN pip install --user "huggingface_hub>=1,<2" \
    "agentenv-portsim @ https://github.com/earakely-scale/agentenv-portsim-plugin/archive/refs/tags/v0.4.0.tar.gz"
COPY --chown=user start.sh .
EXPOSE 7860
CMD ["sh", "start.sh"]
