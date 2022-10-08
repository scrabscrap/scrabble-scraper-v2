FROM gitpod/workspace-full:latest
USER gitpod

RUN pyenv install 3.9.14
RUN pyenv global 3.9.14
RUN sudo apt-get update -q && \
    sudo apt-get install -yq libopencv-dev python3-opencv
