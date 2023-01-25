# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.10-slim

# Copy local code to the container image.
ENV APP_HOME /datamanager
WORKDIR $APP_HOME
COPY . ./

# Install production dependencies.
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 50054
CMD ["python", "datamanager_server.py"]