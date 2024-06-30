FROM python:3.8.5

RUN python -m pip install pip==23.3.2 && \
pip install fastapi==0.68.0 && \
pip install uvicorn==0.14.0 && \
pip install aiofiles==23.2.1 && \
pip install fastapi-async-sqlalchemy==0.6.1 && \
pip install python-multipart==0.0.9 && \
pip install requests==2.31.0 && \
pip install pymongo==4.0.1 && \
pip install dnspython==2.2.0 && \
pip install aiohttp==3.9.0rc0 && \
colorama -i http://pypi.douban.com/simple/ --trusted-host pypi.douban.com

EXPOSE 8888

COPY . .

CMD ["python", "api/main.py"]
