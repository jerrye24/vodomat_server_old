FROM python:3.6

WORKDIR /vodomat_server_old
COPY . .

RUN pip install -r requirements.txt

RUN chmod +x start.sh

ENTRYPOINT [ "./start.sh" ]