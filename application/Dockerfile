# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /webapp

# Copy the current directory contents into the container at /webapp
ADD . /webapp

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Expose port 8080
EXPOSE 8080

# Run web_app.py when the container launches
CMD ["python3", "web_app.py"]
