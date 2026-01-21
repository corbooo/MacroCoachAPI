# MacroCoachAPI

MacroCoachAPI is a FastAPI-based backend application for tracking daily body weight and macronutrient intake. The API allows users to log historical data, analyze trends, and generate future calorie recommendations based on real consumption patterns.

This project was built to create a practical, data-driven fitness tool while gaining hands-on experience designing and implementing a real-world REST API.

---

## Features

- Log daily body weight entries  
- Track calories, protein, carbohydrates, and fat  
- Retrieve historical trends  
- Generate future intake suggestions based on recent data  
- Fully RESTful API architecture  

---

## Tech Stack

- Python  
- FastAPI  
- SQLAlchemy  
- SQLite  
- Pydantic  

---

## API Endpoints (Example)

| Method | Endpoint | Description |
|-------|----------|-------------|
| POST | `/weights` | Log daily body weight |
| POST | `/macros` | Log daily macro intake |
| GET | `/weights` | Retrieve weight history |
| GET | `/macros` | Retrieve macro history |
| GET | `/insights` | Analyze recent trends |
| GET | `/future/suggestions` | Generate future intake recommendations |

*(Exact endpoints may vary based on implementation.)*

---

## Motivation

Most fitness apps provide static calorie goals with little personalization.  
This project was created to experiment with **data-driven recommendations** using real historical data and to strengthen backend engineering skills in:

- API design  
- Database modeling  
- Business logic abstraction  
- Clean software structure  

---

## Local Setup

```bash
pip install fastapi uvicorn sqlalchemy pydantic
uvicorn main:app --reload
