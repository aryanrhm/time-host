# Use the alpine image as the base image
FROM alpine:3.18.2

# Install Python and pip
RUN apk add --no-cache python3 py3-pip

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Install the project dependencies
RUN pip install -r requirements.txt

# Copy the Django project code to the container
COPY . .
# Expose the port on which your Django app runs (default is 8000)
EXPOSE 8000
# Run the Django development server
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
