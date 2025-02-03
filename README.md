# gpt-data-insights
# GPT Data Insights - Django Project

GPT Data Insights is a web-based application built using Django that allows users to upload CSV files, visualize the data, and interact with an AI chatbot (powered by Groq) for data-related queries.

## Features
- **User Authentication**: Register and Login to access features.
- **CSV Upload & Visualization**: Upload a CSV file to generate interactive visualizations.
- **AI Chatbot Support**: Get assistance from an AI chatbot for data insights.

---

## Installation & Setup

### 1. Clone the Repository
```sh
   git clone https://github.com/your-username/gpt-data-insights.git
   cd gpt-data-insights
```

### 2. Create a Virtual Environment
```sh
   python -m venv .venv
```
Activate the virtual environment:
- **Windows**:
  ```sh
  .venv\Scripts\activate
  ```
- **Mac/Linux**:
  ```sh
  source .venv/bin/activate
  ```

### 3. Install Dependencies
```sh
   pip install -r requirements.txt
```

### 4. Apply Migrations
```sh
   python manage.py makemigrations
   python manage.py migrate
```

### 5. Create Superuser (Optional)
```sh
   python manage.py createsuperuser
```

### 6. Run the Development Server
```sh
   python manage.py runserver
```
The server will start at `http://127.0.0.1:8000/`

---

## How to Use

### 1. Register & Login
- Open `http://127.0.0.1:8000/` in your browser.
- Register a new user or login if you already have an account.

### 2. Upload CSV File
- Navigate to the **Upload CSV** section.
- Select a CSV file and upload it.
- The system will process and visualize the data automatically.

### 3. Explore Data Visualizations
- Once the file is processed, interactive charts and graphs will be displayed.

### 4. Chat with AI (Groq)
- Use the built-in chatbot to ask questions related to your data.
- The AI will provide insights and help with data interpretation.

---

## Deployment
### Deploying to a Cloud Server (Optional)
To deploy the project, use platforms like **Heroku, AWS, or DigitalOcean**. Ensure you set up a production-ready database like PostgreSQL.

### Collect Static Files
```sh
   python manage.py collectstatic
```

### Use Gunicorn for Production
```sh
   pip install gunicorn
   gunicorn gpt_data_insights.wsgi:application --bind 0.0.0.0:8000
```

---

## Technologies Used
- **Backend**: Django, Django REST Framework
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite (default) / PostgreSQL (for production)
- **Visualization**: Matplotlib, Seaborn
- **AI Chatbot**: Groq API

---

## Contributors
- Your Name - [GitHub Profile](https://github.com/Annpurna-0103)

---

## License
This project is licensed under the MIT License.

---

## Support
For any issues or feature requests, open an issue on GitHub.

