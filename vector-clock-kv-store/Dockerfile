
FROM python:3.10-slim
WORKDIR /app
COPY src/node.py .
RUN pip install flask requests
EXPOSE 5000
CMD ["python", "node.py"]
