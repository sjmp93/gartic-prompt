# Use an official Python runtime as a parent image
# bullseye is a good option for wider platform compatibility (incl. ARM)
FROM python:3.9-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Add --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
# This includes the genie_app directory and potentially other root files like README.md
COPY genie_app/ ./genie_app/
COPY README.md . 
# If leaderboard.json should be part of the initial image (e.g., with default data or as a template),
# copy it too. Otherwise, it will be created by the app or could be managed by a volume.
# For now, let's assume it's created by the app if it doesn't exist.

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define the command to run the application
# Run Flask on 0.0.0.0 to make it accessible from outside the container
CMD ["python", "-u", "genie_app/app.py"]
