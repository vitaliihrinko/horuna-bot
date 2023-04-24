FROM python:3.9

WORKDIR /Users/vitaliihrinko/pythonProject

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "telegram_bot.py"]
