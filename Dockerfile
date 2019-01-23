FROM python:3.6-slim-jessie

################################################################################
## setup container
################################################################################

RUN apt-get update -qq \
    && apt-get -qq --yes --force-yes install gcc \
    && pip install --upgrade pip

################################################################################
## install app
## copy files one by one and split commands to use docker cache
################################################################################

WORKDIR /code

COPY ./conf /code/conf
RUN pip install -r /code/conf/requirements.txt

COPY ./ /code

################################################################################
## last setup steps
################################################################################

# create user to run container (avoid root user)
RUN useradd -ms /bin/false aether
RUN chown -R aether: /code

ENTRYPOINT ["python","/code/entrypoint.py"]