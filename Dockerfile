FROM python:3.8.5

RUN pip install fastapi uvicorn aiofiles fastapi-async-sqlalchemy python-multipart requests pymongo dnspython aiohttp colorama -i http://pypi.douban.com/simple/ --trusted-host pypi.douban.com

EXPOSE 8888

COPY . .

CMD ["python", "api/main.py"]
