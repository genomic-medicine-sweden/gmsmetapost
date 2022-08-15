FROM continuumio/miniconda3:4.12.0 AS condabuild
LABEL authors="Lauri Mesilaakso" \
    description="Docker image containing all requirements for local download_genomes module"

COPY conf/environments/download_genomes/environment.yml /environment.yml
RUN /opt/conda/bin/conda update conda && \
    /opt/conda/bin/conda install mamba -c conda-forge && \
    /opt/conda/bin/conda update mamba -c conda-forge && \
    /opt/conda/bin/mamba env create -f /environment.yml

FROM debian:buster-slim
RUN apt-get clean -y
COPY --from=condabuild /opt/conda/envs/download_genomes /opt/conda/envs/download_genomes
ENV PATH=/opt/conda/envs/download_genomes/bin:$PATH
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
