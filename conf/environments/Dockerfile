FROM continuumio/miniconda3:4.12.0 AS condabuild
LABEL authors="Lauri Mesilaakso" \
    description="Docker image containing all requirements for general use with gmsmetapost"

COPY conf/environments/environment.yml /environment.yml
RUN /opt/conda/bin/conda update conda && \
    /opt/conda/bin/conda install mamba -c conda-forge && \
    /opt/conda/bin/conda update mamba -c conda-forge && \
    /opt/conda/bin/mamba env create -f /environment.yml

FROM debian:buster-slim
RUN apt-get clean -y
COPY --from=condabuild /opt/conda/envs/general /opt/conda/envs/general
ENV PATH=/opt/conda/envs/general/bin:$PATH
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
