FROM ubuntu

RUN sudo apt-get update -y

RUN sudo apt-get install -y python

RUN python --version

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD streamlit run ./home.py --server.maxUploadSize 20000