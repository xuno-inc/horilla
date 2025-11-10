FROM python:3.10-slim-bullseye

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y libcairo2-dev gcc gettext


WORKDIR /app/

COPY . .

RUN chmod +x /app/entrypoint.sh

RUN pip install -r requirements.txt

EXPOSE 8000

RUN ./manage.py compilemessages

# CMD ["python3", "manage.py", "runserver"]

ENTRYPOINT [ "./entrypoint.sh" ]
