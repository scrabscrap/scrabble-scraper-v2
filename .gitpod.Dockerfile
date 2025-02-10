FROM gitpod/workspace-full:latest
USER gitpod

RUN pyenv install 3.11
RUN pyenv global 3.11

RUN sudo apt-get install -yq pandoc texlive-latex-base texlive-fonts-recommended \
         texlive-extra-utils texlive-latex-extra texlive-xetex
