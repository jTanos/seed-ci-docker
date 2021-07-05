FROM python:3.8.6
WORKDIR /app
RUN pip install pipenv
COPY Pipfile ./
RUN pipenv lock --keep-outdated --requirements > requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]