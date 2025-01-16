# Use uma imagem base do Python
FROM python:3.9

# Configura o diretório de trabalho na imagem
WORKDIR /app

# Copia os arquivos necessários para a imagem
COPY ./src /app

# Instala as dependências do sistema necessárias
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Configura a variável de ambiente para a API da OpenAI
# (Substitua "your_api_key_here" pela sua chave de API)
ENV OPENAI_API_KEY=your_api_key_here

# Expõe a porta usada pelo Flask
EXPOSE 5000

# Comando para iniciar a aplicação
CMD ["python", "app.py"]
