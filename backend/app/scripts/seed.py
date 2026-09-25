import datetime as dt

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    AIAnalysis,
    Business,
    Client,
    Message,
    Request,
    RequestStatusHistory,
    Service,
    User,
)
from app.models.enums import (
    MessageDirection,
    MessageSource,
    RequestStatus,
    UserRole,
)
from app.services.ai import AIAnalysisService, MockProvider

SERVICES = [
    ("Стрижка", 60, 1500),
    ("Окрашивание", 120, 3800),
    ("Маникюр", 90, 1300),
    ("Педикюр", 90, 1400),
    ("Массаж", 60, 2200),
    ("Консультация", 30, 500),
    ("Чистка лица", 75, 2500),
    ("Коррекция бровей", 40, 700),
]

CLIENTS = [
    ("Анна Смирнова", "+7 912 345-67-01", 100001),
    ("Игорь Петров", "+7 912 345-67-02", 100002),
    ("Ольга Кузнецова", "+7 912 345-67-03", None),
    ("Дмитрий Волков", "+7 912 345-67-04", 100004),
    ("Екатерина Соколова", "+7 912 345-67-05", None),
    ("Сергей Морозов", "+7 912 345-67-06", 100006),
    ("Мария Лебедева", "+7 912 345-67-07", None),
    ("Алексей Николаев", "+7 912 345-67-08", 100008),
    ("Татьяна Орлова", "+7 912 345-67-09", None),
    ("Роман Захаров", "+7 912 345-67-10", 100010),
]

REQUEST_SAMPLES = [
    (MessageSource.TELEGRAM, "Здравствуйте! Хочу записаться на маникюр завтра в 15:00", RequestStatus.NEW),
    (MessageSource.TELEGRAM, "Сколько стоит окрашивание?", RequestStatus.NEW),
    (MessageSource.WEB, "Хочу записаться на стрижку на субботу", RequestStatus.IN_PROGRESS),
    (MessageSource.TELEGRAM, "Отмените мою запись на массаж, пожалуйста", RequestStatus.CANCELLED),
    (MessageSource.WEB, "Подскажите, есть ли у вас свободное время на следующей неделе?", RequestStatus.IN_PROGRESS),
    (MessageSource.TELEGRAM, "Перенесите мою запись на другой день, пожалуйста", RequestStatus.IN_PROGRESS),
    (MessageSource.WEB, "Хочу записаться на массаж послезавтра в 18:00", RequestStatus.CONFIRMED),
    (MessageSource.TELEGRAM, "Сколько стоит маникюр и педикюр вместе?", RequestStatus.COMPLETED),
    (MessageSource.TELEGRAM, "Крайне недовольна обслуживанием, хочу оставить жалобу", RequestStatus.COMPLETED),
    (MessageSource.WEB, "Хочу записаться на консультацию", RequestStatus.IN_PROGRESS),
    (MessageSource.TELEGRAM, "а вы в воскресенье работаете?", RequestStatus.COMPLETED),
    (MessageSource.WEB, "Хочу записаться на укладку завтра", RequestStatus.CONFIRMED),
    (MessageSource.TELEGRAM, "Отменю свою запись, заболела", RequestStatus.CANCELLED),
    (MessageSource.TELEGRAM, "Добрый день!", RequestStatus.NEW),
    (MessageSource.WEB, "Хочу записаться к вам на окрашивание в пятницу в 12:00", RequestStatus.CONFIRMED),
    (MessageSource.TELEGRAM, "Сколько стоит стрижка?", RequestStatus.COMPLETED),
    (MessageSource.WEB, "Нужен перенос моей записи на чистку лица, не смогу прийти", RequestStatus.IN_PROGRESS),
    (MessageSource.TELEGRAM, "Запишите меня на массаж в 19:00", RequestStatus.COMPLETED),
    (MessageSource.WEB, "Ужасная работа, испортили волосы, подаю претензию", RequestStatus.CANCELLED),
    (MessageSource.TELEGRAM, "Хочу записаться на коррекцию бровей завтра", RequestStatus.NEW),
]


def main() -> None:
    db = SessionLocal()
    try:
        if db.scalars(select(Business)).first() is not None:
            print("Демо-данные уже загружены. Seed пропущен.")
            return
        ai_service = AIAnalysisService(MockProvider())

        business = Business(name="Студия красоты «Луна»")
        db.add(business)
        db.flush()

        admin = User(
            business_id=business.id,
            email="admin@luna.ru",
            password_hash=hash_password("admin12345"),
            full_name="Иван Иванов",
            role=UserRole.ADMIN,
        )
        manager = User(
            business_id=business.id,
            email="maria@luna.ru",
            password_hash=hash_password("manager12345"),
            full_name="Мария Лебедева",
            role=UserRole.MANAGER,
        )
        db.add_all([admin, manager])
        db.flush()

        services = [
            Service(business_id=business.id, name=name, duration_minutes=duration, price=price)
            for name, duration, price in SERVICES
        ]
        db.add_all(services)
        db.flush()

        clients = [
            Client(business_id=business.id, name=name, phone=phone, telegram_user_id=tg_id)
            for name, phone, tg_id in CLIENTS
        ]
        db.add_all(clients)
        db.flush()

        now = dt.datetime.now(dt.timezone.utc)
        for index, (source, text, status) in enumerate(REQUEST_SAMPLES):
            client = clients[index % len(clients)]
            result = ai_service.analyze(text)
            service = next(
                (
                    item
                    for item in services
                    if result.service_name and item.name.lower() == result.service_name.lower()
                ),
                None,
            )
            created_at = now - dt.timedelta(days=13 - (index * 14) // 20, hours=(index * 5) % 24)
            request = Request(
                business_id=business.id,
                client_id=client.id,
                service_id=service.id if service else None,
                status=RequestStatus.NEW,
                source=source,
                summary=text[:200],
                preferred_date=result.preferred_date,
                preferred_time=result.preferred_time,
                requires_manual_review=result.confidence < 0.60,
            )
            db.add(request)
            db.flush()

            message = Message(
                business_id=business.id,
                client_id=client.id,
                request_id=request.id,
                direction=MessageDirection.IN,
                source=source,
                text=text,
                telegram_update_id=500000 + index if source == MessageSource.TELEGRAM else None,
            )
            db.add(message)

            analysis = AIAnalysis(
                request_id=request.id,
                intent=result.intent,
                confidence=result.confidence,
                service_name=result.service_name,
                preferred_date=result.preferred_date,
                preferred_time=result.preferred_time,
                requires_manual_review=result.requires_manual_review,
            )
            db.add(analysis)

            request.created_at = created_at
            request.updated_at = created_at
            message.created_at = created_at
            analysis.created_at = created_at

            if status != RequestStatus.NEW:
                history = RequestStatusHistory(
                    request_id=request.id,
                    old_status=RequestStatus.NEW,
                    new_status=status,
                    changed_by_user_id=manager.id,
                )
                db.add(history)
                history.created_at = created_at + dt.timedelta(hours=2)
                request.status = status
                request.updated_at = created_at + dt.timedelta(hours=2)

        db.commit()
        print(
            f"Готово: бизнес «{business.name}», 2 пользователя, {len(services)} услуг, "
            f"{len(clients)} клиентов, {len(REQUEST_SAMPLES)} заявок."
        )
        print("Вход: admin@luna.ru / admin12345 (админ), maria@luna.ru / manager12345 (менеджер)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
