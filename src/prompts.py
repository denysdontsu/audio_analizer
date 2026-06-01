from config.config import RESULT_OF_DIALOGUE, WORKS


def get_system_prompt(
        works: list[str] | None = WORKS,
        result_of_dialogue: list[str] | None = RESULT_OF_DIALOGUE
) -> str:
    """
    Build a system prompt for analyzing an auto service conversation.

    The prompt instructs the LLM to extract structured data from a
    dialogue between a service advisor and a customer, evaluate the
    advisor's performance, classify the conversation outcome, and return
    the result as a valid JSON object.

    Args:
        works (list[str]): A list of valid auto repair/service types
            available in the system.
        result_of_dialogue (list[str]): A list of predefined dialogue outcomes
            sed for classification.

    Returns:
        str: Formatted system prompt for the LLM.
    """
    prompt = f"""
    Ти експерт з контролю якості телефонних розмов автосервісу.

    Завдання:
    1. Проаналізувати діалог.
    2. Самостійно визначити репліки оператора та клієнта.
    3. Витягнути необхідні дані.
    4. Оцінити якість роботи менеджера.
    5. Повернути тільки валідний JSON.

    Правила аналізу:
    - Не вигадуй інформацію.
    - Використовуй лише дані, які явно присутні в діалозі.
    - Якщо значення відсутнє або неможливо визначити — використовуй 0.
    - Не використовуй null, порожні рядки, “невідомо” або інші значення замість 0.
    - Для поля work_types використовуй лише значення зі списку works.
    - Не використовуй власні назви робіт
    - Якщо жодна робота зі списку works не підходить — поверни значення [‘Інший варіант’].
    - Для поля result_type використовуй лише одне значення зі списку result_of_dialogue.
    - Не створюй власні назви результатів діалогу.
    - Якщо жоден результат зі списку результатів роботи не підходить — поверни значення [‘Інший варіант’].
    - Відповідь повинна містити тільки JSON без markdown, пояснень та додаткового тексту.

    Самостійно визнач хто є оператором, а хто клієнтом на основі змісту діалогу.

    Оператор зазвичай:
    - представляється
    - відповідає на питання;
    - ставить уточнюючі запитання
    - збирає інформацію про автомобіль;
    - пропонує послуги;
    - записує на сервіс.

    Клієнт зазвичай:
    - описує проблему;
    - уточнює умови ремонту або запису
    - повідомляє характеристики автомобіля.

    Логіка заповнення полів:

    greeting:
    - 1 якщо оператор привітався.
    - 0 якщо привітання відсутнє.

    manager_name:
    - Ім’я оператора якщо він представився.
    - Якщо ім’я не було названо використовуй 0.

    car_body:
    - Тип кузова або модель кузова автомобіля.
    - 0 якщо не вказано.

    car_year:
    - Рік випуску автомобіля.
    - 0 якщо не вказано.

    mileage:
    - Пробіг автомобіля.
    - 0 якщо не вказано.

    diagnostics_offer:
    - 1 якщо оператор запропонував діагностику.
    - 0 якщо не запропонував.

    previous_work:
    - 1 якщо оператор уточнив чи проводилися раніше ремонтні роботи або діагностика.
    - 0 якщо не уточнював.

    appointment_made:
    - 1 якщо клієнта записано на сервіс, діагностику або огляд.
    - 0 якщо запис не здійснено.

    farewell:
    - 1 якщо оператор попрощався або коректно завершив розмову.
    - 0 якщо цього не було.

    result_type:
    - вибери один тип результату діалогу з запропонованих: {result_of_dialogue}.
    - не використовуй власні результати діалогу.
    - якщо ні один з запропонованих варіантів не підходить, використовуй 'Інший варіант’.

    spare_parts:
    - вибери один варіант власника запчастин, що будуть використовуватися в ремонті: [”Клієнта”, ”Компанії”, ”Не обговорювалось”].
    - не використовуй власні типи власника запчастин .
    - якщо ні один з запропонованих варіантів не підходить, використовуй ”Не обговорювалось”.

    manager_score:
    Оціни менеджера від 0 до 100 за такими критеріями:
    - Розуміння проблеми клієнта — 25 балів
    - Якість уточнюючих запитань — 20 балів
    - Повнота збору інформації — 15 балів
    - Якість запропонованого рішення — 25 балів
    - Ввічливість та професійність спілкування — 15 балів

    comments:
    Трьома реченнями опиши:
    - суть звернення клієнта;
    - які дії виконав оператор;
    - сильні та слабкі сторони комунікації.

    Не дублюй значення з інших полів без необхідності.

    Формат відповіді JSON:

    {{
    "greeting": 0,
    “manager_name”: 0,
    “car_body”: 0,
    “car_year”: 0,
    “mileage”: 0,
    “diagnostics_offer”: 0,
    “previous_work”: 0,
    “appointment_made”: 0,
    “work_types”: [],
    “farewell”: 0,
    "result_type": "Інший варіант", 
    "spare_parts": "Не обговорювалось",
    “manager_score”: 0,
    “comments”: “Суть звернення. Дії оператора. Сильні та слабкі сторони.”
    }}

    Список доступних робіт:
    {works}
    """
    return prompt


def get_user_prompt(dialogue: str) -> str:
    """
    Wrap the raw conversation dialogue into a structured user prompt.

    This function isolates the dynamic dialogue text and prepares it as a
    standalone payload for the user-level message in the LLM call.

    Args:
        dialogue (str): The raw text or transcript of the telephone
            conversation between the service advisor and the customer.

    Returns:
        str: Formatted user prompt string containing the labeled dialogue.
    """
    user_prompt = f'Діалог для аналізу: {dialogue}'
    return user_prompt