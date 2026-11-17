# ПР9 — короткий сценарий защиты

## С чего начать

Скажи: «В ПР7 я писал SQL вручную. В ПР9 описал таблицы моделями Django,
создал миграции и перевёл страницы на ORM. SQLite осталась СУБД».

1. Открой web/categories/models.py и web/catalog/models.py: две модели,
   category = ForeignKey, on_delete=PROTECT, related_name=attractions.
2. В терминале: `.\.venv\Scripts\python.exe manage.py showmigrations`.
   `[X]` означает, что миграция применена.
3. Запусти сайт: `.\.venv\Scripts\python.exe manage.py runserver`.
4. Открой /attractions/search/: бюджет 300, час 12 → три места
   (два парка и галерея). «Название или описание» = ПРОГУЛОК → Парк Победы.
5. Сбрось фильтры. Выбери «Сначала дороже», час 12, нажми «Найти места».
   Затем «Далее»: фильтр и сортировка остаются в адресной строке.
6. /attractions/statistics/: 5 мест, 2 бесплатных, средняя цена 320,
   сумма цен 1600. Порог 2 оставляет музеи; порог 3 — пустой список.
7. Во втором терминале: `.\.venv\Scripts\python.exe manage.py demo_orm`.
   Команда показывает создание, чтение, изменение, удаление и PROTECT.
   Все демонстрационные изменения откатываются, исходные места остаются.

## Что где показывать и как отвечать

| Вопрос преподавателя | Где открыть | Короткий ответ и действие |
| --- | --- | --- |
| Модель и таблица | models.py обоих приложений | Класс модели описывает таблицу, объект — строку, поле — столбец |
| Поля и типы | Attraction | CharField — текст, DecimalField — точная десятичная цена, Integer — часы |
| blank и null | description | blank разрешает пустой ввод, null разрешает NULL в базе |
| Первичный ключ | миграции, поле id | Django автоматически добавил BigAutoField, ID уникален |
| Связь | Attraction.category | Много мест относятся к одной категории |
| on_delete | PROTECT | Категорию с местами удалить нельзя; demo_orm показывает ProtectedError |
| related_name | Category и services.category_places | category.attractions — места этой категории |
| Миграции | migrations/0001_initial.py | makemigrations создаёт описание изменения, migrate применяет к базе |
| Где база | config/settings.py | Новая db.sqlite3; старая data/attractions.sqlite — источник ПР7 |
| Как перенёс | management/commands/import_legacy.py | Только чтение sqlite3 → объекты моделей → save внутри atomic |
| Повторный импорт | import_legacy | ID сохраняются, совпадающие записи обновляются, дубликатов нет |
| Что при ошибке импорта | transaction.atomic | Вся операция откатывается, часть записей не остаётся |
| Все объекты и один объект | services.get_attractions/get_attraction | QuerySet для списка, get(pk) для одного; get может вызвать DoesNotExist |
| 404 | catalog/views.py, attraction_detail | Ловим DoesNotExist, показываем шаблон и статус 404; /attractions/999/ |
| Фильтрация | services.free_places/within_budget/open_at | filter задаёт условия; несколько условий объединяются AND |
| Связанное поле | services.by_category | category__name_key обращается к полю другой таблицы |
| Исключение | services.paid_places | exclude(price=0) исключает бесплатные; выбрать «Платно» в поиске |
| Поиск | services.search_name/search_text | icontains — вхождение; Q с OR ищет в имени или описании |
| Русский регистр | модели, save | Сохраняются casefold-поля, чтобы SQLite находила русский текст в любом регистре |
| Проверка ввода | catalog/forms.py, SearchForm | Формы преобразуют строки и проверяют границы; hour=25 → 400 с сообщением |
| Сортировка | forms.SORTS, services.get_attractions | Только разрешённые поля; минус перед price означает убывание |
| Несколько полей сортировки | SORTS[price] | Сначала цена, затем имя и ID для устойчивого порядка |
| values | services.opening_hours | Возвращает словари с выбранными полями, а не объекты моделей |
| annotate и F | opening_hours | F берёт поле из БД; close_hour - open_hour считает часы работы |
| aggregate | services.overview | Возвращает общую статистику одним словарём: Count, Sum, Avg, Min, Max |
| Группировка | category_stats/price_groups | annotate считает показатели каждой категории или группы цен |
| Пустая категория | category_stats | LEFT JOIN сохраняет её, Count(attractions) даёт 0 |
| HAVING | popular_categories | Фильтрует уже подсчитанное places_count |
| select_related | get_attraction/get_attractions | Категория приходит вместе с местом одним JOIN, нет отдельного запроса на каждую карточку |
| Ограничение | home_preview | [:3] превращается в LIMIT, главная показывает три места |
| Paginator | services.paginate | Делит результат на страницы; размер в CATALOG_PAGE_SIZE |
| Ссылки страниц | includes/pagination.html | has_next/has_previous управляют стрелками; querystring сохраняет фильтры |
| Порядок обработки | search_places → paginate | Сначала фильтрация и сортировка, потом выбор страницы |
| Передача в шаблон | views.search и search.html | Контекст attractions содержит объекты; шаблон читает attraction.name |
| CRUD | demo_orm.py | create создаёт, get читает, save сохраняет, delete удаляет |
| Выгрузка | README, dumpdata/loaddata | JSON-фикстура переносит данные; миграции отдельно создают структуру |
| Старый SQL | папки sql и db | Оставлен для ПР7, страницы его больше не используют |

## Если попросят команды руками

Открой Django shell:
```powershell
.\.venv\Scripts\python.exe manage.py shell
```
Вводи по одной строке:
```python
from web.catalog.models import Attraction
from web.categories.models import Category
list(Attraction.objects.values("id", "name", "price"))
Attraction.objects.filter(price=0)
Attraction.objects.exclude(price=0)
Attraction.objects.filter(category__name_key="парк")
Attraction.objects.order_by("-price", "id")
Category.objects.get(name_key="парк").attractions.all()
print(Attraction.objects.select_related("category").query)
exit()
```

Для изменения записи удобнее demo_orm: он безопасен и повторяем.
Если меняешь настоящий объект, save() НЕ вызывает full_clean() автоматически.
Сначала вызови obj.full_clean(), затем obj.save(). Запрос update() обходит save().

## Посмотреть SQL в браузере

Останови сервер Ctrl+C и запусти:
```powershell
$env:DJANGO_TOOLBAR="1"
.\.venv\Scripts\python.exe manage.py runserver
```
Открой карточку места → панель справа → SQL: один запрос с INNER JOIN.
Если панель мешает, нажми «Скрыть». Отключить после остановки сервера:
`Remove-Item Env:DJANGO_TOOLBAR`.

## Полная проверка
```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m flake8 .
```
Ожидается 93 passed, отсутствие ошибок Django и замечаний flake8.
Тесты используют временные базы и не меняют рабочую.
