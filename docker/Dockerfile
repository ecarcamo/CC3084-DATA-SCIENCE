FROM python:3.11-slim-bookworm

# Java 17 y utilidades requeridas por Spark.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openjdk-17-jdk-headless \
        ca-certificates \
        curl \
        tini \
        procps && \
    JAVA_INSTALLATION="$(dirname "$(dirname "$(readlink -f "$(command -v java)")")")" && \
    ln -s "$JAVA_INSTALLATION" /opt/java-home && \
    rm -rf /var/lib/apt/lists/*

# Ruta estable que funciona tanto en arm64 como en amd64.
ENV JAVA_HOME=/opt/java-home
ENV PATH="${JAVA_HOME}/bin:${PATH}"
ENV PYSPARK_PYTHON=/usr/local/bin/python

WORKDIR /opt/app

# PySpark, Jupyter y librerias de Data Science.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        pyspark==3.5.1 \
        notebook \
        jupyterlab \
        ipykernel \
        findspark \
        pandas \
        pyarrow \
        matplotlib \
        seaborn

# Lectura de .xlsx/.sav y conversion del notebook (lab 7).
RUN pip install --no-cache-dir openpyxl pyreadstat jupytext nbconvert

# Ejecutar Jupyter con un usuario sin privilegios.
RUN useradd -ms /bin/bash spark && \
    chown -R spark:spark /opt/app

USER spark

EXPOSE 8888

CMD ["bash"]
