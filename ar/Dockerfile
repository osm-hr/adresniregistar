FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    osmium-tool \
    build-essential \
    curl \
    rustc \
    cargo \
    pkg-config \
    cmake \
    libsqlite3-dev \
    sqlite3 \
    unzip \
    wget \
    make \
    git \
    libosmium2-dev \
    libboost-python-dev \
    libexpat1-dev \
    zlib1g-dev \
    libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    osmium \
    requests-oauthlib \
    shapely \
    geopandas

WORKDIR /app

RUN git clone --depth 1 https://codeberg.org/ihabunek/dgu-parse.git; \
     cd dgu-parse; \
     cargo build --release

RUN curl -L -o duckdb.zip https://github.com/duckdb/duckdb/releases/download/v1.4.4/duckdb_cli-linux-amd64.zip \
    && unzip duckdb.zip -d /usr/local/bin \
    && rm duckdb.zip


COPY . .

RUN git clone --depth 1 https://github.com/osm-hr/adresniregistar-ispravci.git; \
     mv adresniregistar-ispravci/curated_streets.csv ./curated_streets.csv; \
     mv adresniregistar-ispravci/curated_streets_per_naselje.csv ./curated_streets_per_opstina.csv; \
     rm -rf adresniregistar-ispravci

ENTRYPOINT ["make"]