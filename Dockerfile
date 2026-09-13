FROM python:3.8.5

COPY requirements.txt .

RUN python -m pip install pip==23.3.2 && \
pip install -r requirements.txt

EXPOSE 8888

COPY . .

CMD ["python", "api/main.py"]
