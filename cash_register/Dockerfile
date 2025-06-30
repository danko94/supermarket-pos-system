FROM python:3.11
WORKDIR /app
COPY cash_register/ .
COPY shared/ shared/
COPY supermarkets.csv .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]