FROM apache/airflow:2.8.4-python3.10

ENV AIRFLOW_HOME=/opt/airflow
ENV JAVA_HOME=/usr/lib/jvm/jdk1.8.0_401
ENV PATH="$PATH:${AIRFLOW_HOME}/bin:${JAVA_HOME}/bin"

USER root

RUN mkdir /usr/lib/jvm && mkdir ./.kube
COPY jdk-11.0.0.1.tar.gz /opt/airflow
RUN tar xvf jdk-11.0.0.1.tar.gz -C /usr/lib/jvm \
	&& rm jdk-11.0.0.1.tar.gz

RUN sudo curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        vim \
        wget \
        net-tools \
        dnsutils \
        iputils-ping \
        netcat-openbsd \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

USER airflow
COPY ./requirements.txt /
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt
