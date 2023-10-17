FROM python:3.8
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
ENTRYPOINT [ "python" ]
EXPOSE 5050
CMD [ "users.py" ]