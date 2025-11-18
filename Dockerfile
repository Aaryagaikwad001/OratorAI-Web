# 1. Start with the right Python version (Python 3.11, which works for your app)
FROM python:3.11-slim

# 2. Tell the box where your code will live
WORKDIR /app

# 3. Install the system tool needed for audio (ffmpeg)
# This uses the 'packages.txt' you already made!
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

# 4. Install all the other app ingredients (from requirements.txt)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 5. Put the main app code in the box
COPY streamlit_app.py /app/streamlit_app.py

# 6. Tell the box which door to use (port 7860) and how to start the app
EXPOSE 7860
ENV PORT=7860
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=7860", "--server.address=0.0.0.0"]
