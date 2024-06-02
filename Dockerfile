FROM python:3.9

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh .
RUN chmod +x ./entrypoint.sh
RUN echo ls -a

COPY . .
