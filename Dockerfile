FROM python:3.9

RUN pip install pipenv

# create environmental variables
ENV PROJECT_DIR=/usr/PolycadeChatbaseHelper/
ENV AM_I_IN_A_DOCKER_CONTAINER=True

# set our working directory to the value of our env variable (a filepath)
WORKDIR ${PROJECT_DIR}

# add our main.py and PCH.py files to the working directory (which we established above)
ADD main.py . 
ADD PCH.py .

COPY Pipfile Pipfile.lock ${PROJECT_DIR}
COPY credentials.json ${PROJECT_DIR}

RUN apt-get update && apt-get install -y wget unzip && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb && \
    apt-get clean

RUN pipenv install --system --deploy

CMD [ "python", "./main.py" ]

# docker run -v ~/Downloads:/downloads -it pch
