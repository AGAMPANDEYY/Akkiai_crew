# To run docker go to CLI type docker build -t image-name . (or other tag that you wish) 
# docker run -p 8501:8501 image-name  #port 8501 for streamlit st_app.py and 8000 for fastapi app main.py

# Use the official Python image as a base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Copy the rest of the application code into the container
COPY . .

# Expose the port that the application runs on (if you are running a FastAPI server, for example)
# for FastAPI use port 8000 while for Streamlit use port 8501
EXPOSE 8000

# Define environment variables (optional, if you need any specific configs) 
#ENV ANTHROPIC_API_KEY=
# 127.0.0.1 for local access while for outside access as well use 0.0.0.0 
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]