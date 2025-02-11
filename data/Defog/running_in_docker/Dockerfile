# Dockerfile  
FROM python:3.11-slim  

# Install SQLite  
RUN apt-get update && apt-get install -y sqlite3  

# Install system dependencies  
RUN apt-get update && apt-get install -y \  
    git \  
    bash \  
    && rm -rf /var/lib/apt/lists/*  

# Set up the environment  
WORKDIR /app  

# Clone repositories  
RUN git clone https://github.com/defog-ai/sql-eval.git \  
    && git clone https://github.com/defog-ai/defog-data.git  

# Copy data to the correct structure  
RUN cp -r defog-data/* sql-eval/data/  

# Install dependencies for sql-eval  
WORKDIR /app/sql-eval  
RUN pip install --upgrade pip \  
    && pip install --no-deps -r requirements.txt  

# Install defog-data  
WORKDIR /app/defog-data  
RUN pip install --no-deps -r requirements.txt \  
    && pip install -e .  

# Install additional packages  
RUN pip install \  
    python-dateutil \  
    pytz \  
    typing_extensions \  
    pydantic \  
    httpx \  
    distro \  
    jiter \  
    requests  

# Configure SQLite from defog-data  
WORKDIR /app/defog-data  
RUN mkdir -p ../sql-eval/sqlite_dbs \  
    && python translate_ddl_dialect.py --dialects sqlite  

# Create SQLite databases from the corresponding SQL files  

# Replace with this corrected block:  
WORKDIR /app/sql-eval  
RUN mkdir -p sqlite_dbs && \  
    for db in academic advising atis broker car_dealership derm_treatment ewallet geography restaurants scholar yelp; do \  
    sqlite3 sqlite_dbs/${db}.db < ../defog-data/defog_data/${db}/${db}_sqlite.sql; \  
    done  

RUN chmod -R 777 /app/sql-eval/sqlite_dbs  
RUN chmod -R 777 /app/defog-data/defog_data  

# Create directory for the visualizer  
RUN mkdir -p ../sql-eval/eval-visualizer/public  

ENV DATABASE_PATH="/app/sql-eval/sqlite_dbs/"  
ENV HOME=/app  

# Main command  
CMD ["bash", "-c", "cd /app/sql-eval && python main.py -db sqlite -q data/questions_gen_sqlite.csv data/instruct_basic_sqlite.csv data/instruct_advanced_sqlite.csv -o results/openai_classic.csv results/openai_basic.csv results/openai_advanced.csv -g oa -f prompts/prompt_openai.json -m o3-mini -p 5 -c 2"]  
