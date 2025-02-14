FROM gitpod/workspace-full:latest
USER gitpod

RUN pyenv install 3.11
RUN pyenv global 3.11

ARG PANDOC_VERSION=3.6.3-1
RUN sudo wget https://github.com/jgm/pandoc/releases/download/3.6.3/pandoc-${PANDOC_VERSION}-amd64.deb && \
    sudo dpkg -i pandoc-${PANDOC_VERSION}-amd64.deb

RUN sudo apt-get install -yq texlive-latex-base texlive-fonts-recommended \
         texlive-extra-utils texlive-latex-extra texlive-xetex
