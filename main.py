import csv
import time
from datetime import datetime
import asyncio
import uvicorn
from fastapi import FastAPI, UploadFile, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from db import engine, Sessionlocal
from models import *

app = FastAPI()

Base.metadata.create_all(bind=engine)

# ------------------FASTAPI-------------

templates = Jinja2Templates(directory="templates")


def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("insert_data.html", {"request": request})


async def process_csv_row(row, db):
    try:
        # Перевірка коректності дати місяця
        month = datetime.strptime(row["period"], "%d.%m.%Y").date()

        # Перевірка, чи вказано перше число місяця
        if month.day != 1:
            raise HTTPException(status_code=400, detail="Month should start from the first day")

        # Перевірка суми на пусте значення чи нуль
        if not row["sum"] or int(row["sum"]) <= 0:
            raise HTTPException(status_code=400, detail="Amount should be a positive non-zero integer")

        # Пошук у БД
        existing_plan = db.query(Plans).filter(Plans.period == month,
                                               Plans.category_id == row["category_id"]).first()

        if existing_plan:
            raise HTTPException(status_code=400, detail="Plan already exists for the given month and category")

        # Якщо всі перевірки успішно пройдені, можна додати дані до бази даних
        new_plan = Plans(period=month, sum=int(row["sum"]), category_id=row["category_id"])
        db.add(new_plan)
        db.commit()

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format")


@app.post("/credits_insert")
async def credit_insert(file: UploadFile, request: Request, db: Session = Depends(get_db)):
    try:
        file_content = await file.read()

        decoded_content = file_content.decode("utf-8").splitlines()

        all_decoded_content = csv.reader(decoded_content, delimiter='\t')
        next(all_decoded_content)
        for row in all_decoded_content:
            id_credit = row[0]
            user_id = row[1]
            issuance_date = row[2]
            return_date = row[3]
            actual_return_date = row[4]
            body = row[5]
            percent = row[6]

            if actual_return_date:
                actual_return_date = datetime.strptime(actual_return_date, "%d.%m.%Y").date()
                issuance_date = datetime.strptime(issuance_date, "%d.%m.%Y").date()
                return_date = datetime.strptime(return_date, "%d.%m.%Y").date() if return_date else None
                db.query(Credits).filter(Credits.id == id_credit).update(
                    {
                        Credits.issuance_date: issuance_date,
                        Credits.return_date: return_date,
                        Credits.actual_return_date: actual_return_date,
                        Credits.body: body,
                        Credits.percent: percent
                    }
                )
            db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.post("/plans_insert")
async def plans_insert(file: UploadFile, request: Request, db: Session = Depends(get_db)):
    try:
        file_content = await file.read()

        decoded_content = file_content.decode("utf-8").splitlines()

        tasks = []
        for row in csv.DictReader(decoded_content, delimiter='\t'):
            task = asyncio.ensure_future(process_csv_row(row, db))
            tasks.append(task)
        await asyncio.gather(*tasks)

        return {"message": "Data successfully inserted into Plans table"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.get("/user_credits/{user_id}")
async def user_credits(user_id, db: Session = Depends(get_db)):
    user_credits = db.query(Credits).filter(Credits.user_id == user_id).all()
    output_user_info = {}
    for credit in user_credits:
        if bool(credit.actual_return_date):
            output_user_info[credit.id] = {
                'actual_return_date': credit.actual_return_date,
                'sum_body': credit.body,
                'percent': credit.percent,
                'summ_vuplat': sum(
                    [num_sum[0] for num_sum in db.query(Payments.sum).filter(Payments.credit_id == credit.id).all()]),
            }
        else:
            output_user_info[credit.id] = {
                'return_date': credit.return_date,
                'actual_return_date': credit.actual_return_date,
                'sum_body': credit.body,
                'accrued_percent': credit.percent,
                'calculate_body_payments': calculate_body(user_id, 1),
                'Calculate_payment_by_percents': calculate_body(user_id, 2),
            }
    return {'issuance_date': credit.issuance_date, 'close_or_open': bool(credit.actual_return_date)} | output_user_info


def calculate_body(user_id, body_type_id, db: Session = Depends(get_db)):
    return db.query(func.sum(Payments.sum)).join(Credits, Payments.credit_id == Credits.id).filter(
        Payments.type_id == body_type_id).filter(Credits.user_id == user_id).scalar()


@app.get("/plans_performance/{date}")
async def plans_performance(date, db: Session = Depends(get_db)):
    try:
        plans_category_3 = db.query(Plans).filter(Plans.period == date, Plans.category_id == 3).all()
        plans_category_4 = db.query(Plans).filter(Plans.period == date, Plans.category_id == 4).all()

        if plans_category_3 and plans_category_4:
            sum_category_3 = sum(plan.sum for plan in plans_category_3)

            sum_category_4 = sum(plan.sum for plan in plans_category_4)

            percent_completion = (sum_category_4 / sum_category_3) * 100

            date_obj = datetime.strptime(date, "%Y-%m-%d")

            return {
                'month': date_obj.strftime("%B"), # or if you need number date_obj.strftime("%m")
                'category_id': 3,  # Припускаємо, що category_id 3 відповідає "Видача"
                'sum_plan': sum_category_3,
                'total_issued_credits': sum_category_4,
                'percent_completion': f"{percent_completion}%"
            }
        else:
            raise HTTPException(status_code=404, detail="Плани не знайдено для вказаної дати та категорій.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка обробки запиту: {str(e)}")


@app.get("/year_performance/{year}")
async def year_performance(year: int, db: Session = Depends(get_db)):
    loans_summary = {}
    plans_summary = {}

    loans_data = db.query(Credits.issuance_date, Credits.body, Credits.percent).filter(
        func.extract('year', Credits.issuance_date) == year)

    plans_data = db.query(Plans.period, Plans.sum).filter(func.extract('year', Plans.period) == year)

    # Обробка даних про кредити
    for row in loans_data:
        issuance_date, body, percent = row
        month_year = (issuance_date.month, issuance_date.year)
        month_key = f"{month_year[0]}/{month_year[1]}"
        if month_key not in loans_summary:
            loans_summary[month_key] = {'loans_count': 0, 'loans_sum': 0}
        loans_summary[month_key]['loans_count'] += 1
        loans_summary[month_key]['loans_sum'] += body

    # Обробка даних про плани
    for row in plans_data:
        period, sum = row
        month_year = (period.month, period.year)
        month_key = f"{month_year[0]}/{month_year[1]}"
        if month_key not in plans_summary:
            plans_summary[month_key] = {
                'plan_sum': 0,
            }
        plans_summary[month_key]['plan_sum'] += sum

    # Розрахунок додаткової сумарної інформації
    summary_by_month = {}
    for month_key in loans_summary.keys():
        loans_count = loans_summary[month_key]['loans_count']
        loans_sum = loans_summary[month_key]['loans_sum']
        plan_sum = plans_summary.get(month_key, {}).get('plan_sum', 0)

        if plan_sum > 0:
            plan_execution = (loans_sum / plan_sum) * 100
        else:
            plan_execution = 0

        summary_by_month[month_key] = {
            'month_year': month_key,
            'loans_count': loans_count,
            'plan_sum': plan_sum,
            'loans_sum': loans_sum,
            'plan_execution': plan_execution,
        }

    return summary_by_month


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000, loop="asyncio")
