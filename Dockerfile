FROM python:3.9

RUN pip install pipenv

# create environmental variable
ENV PROJECT_DIR=/usr/PolycadeChatbaseHelper/

# set our working directory to the value of our env variable (a filepath)
WORKDIR ${PROJECT_DIR}

# add our PCH.py file to the working directory (which we established above)
ADD PCH.py .

COPY Pipfile Pipfile.lock ${PROJECT_DIR}
COPY credentials.json ${PROJECT_DIR}

RUN apt-get update && apt-get install -y wget unzip && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb && \
    apt-get clean

RUN pipenv install --system --deploy

CMD [ "python", "./PCH.py" ]
