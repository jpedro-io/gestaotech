FROM python:3.12-slim

# LibreOffice converte o DOCX em PDF; fontconfig registra as fontes do certificado
RUN apt-get update && apt-get install -y --no-install-recommends \
      libreoffice-writer fontconfig fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY fontes/ /usr/share/fonts/truetype/certificado/
RUN fc-cache -f

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
RUN chmod +x entrypoint.sh

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["./entrypoint.sh"]
