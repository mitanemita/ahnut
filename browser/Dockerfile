# Браузер для самопроверки открыток. Пакет ставится при сборке — во время работы сеть наружу не нужна.
FROM mcr.microsoft.com/playwright:v1.63.0-noble
RUN npm install -g playwright@1.63.0 && npm cache clean --force
USER pwuser
WORKDIR /home/pwuser
EXPOSE 3000
CMD ["playwright", "run-server", "--port", "3000", "--host", "0.0.0.0"]
