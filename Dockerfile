FROM ubuntu

RUN apt-get update -y

RUN apt-get install -y python3

RUN python --version

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD streamlit run ./home.py --server.maxUploadSize 20000