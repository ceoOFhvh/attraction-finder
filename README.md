# Город рядом — ПР9 Django ORM

Продолжение существующего проекта ПР3–ПР7. Сайт читает данные через модели
Django и QuerySet. Старые страницы сохранены, добавлены поиск по описанию,
фильтр платных мест, сортировка и пагинация. Работа ведётся в main.

## Запуск на этом компьютере

База уже создана, миграции применены, пять мест перенесены, включая Парк Победы.

.\.venv\Scripts\python.exe manage.py runserver

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Открыть http://127.0.0.1:8000/.

## После клонирования проекта на другой компьютер

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe -X utf8 manage.py loaddata data/pr9_initial.json
.\.venv\Scripts\python.exe manage.py runserver
```

Локальная рабочая база **db.sqlite3** исключена из Git. В репозитории есть
миграции и UTF-8 фикстура `data/pr9_initial.json` с пятью местами и двумя
категориями. `loaddata` нужен для первого заполнения: повторная загрузка
заменяет совпадающие ID значениями фикстуры.

## Что где находится

| Файл | Назначение |
| --- | --- |
| web/categories/models.py | Category: название и уникальный ключ категории |
| web/catalog/models.py | Attraction: название, описание, часы, цена и ForeignKey |
| web/categories/migrations, web/catalog/migrations | Начальные миграции моделей |
| web/services.py | Все ORM-запросы сайта, агрегаты и Paginator |
| web/catalog/forms.py | Проверка GET-параметров и разрешённые сортировки |
| web/catalog/views.py | Каталог, карточка, поиск, бесплатные места, статистика |
| templates/includes/pagination.html | Навигация с сохранением GET-параметров |
| web/catalog/management/commands/import_legacy.py | Перенос старой SQLite в ORM |
| web/catalog/management/commands/demo_orm.py | Безопасная демонстрация CRUD |
| docs/DEFENSE_PR9.md | Короткий порядок показа и ответы для защиты |
| docs/REPORT_PR9.docx | Отчёт Word, Войкин Вадим, ЭФБО-14-24 |
| docs/VERIFICATION_PR9.txt | Фактические результаты проверок |

## Модели и ограничения

Category содержит `id`, `name`, `name_key`. Attraction содержит `id`, `name`,
`description`, `category`, `open_hour`, `close_hour`, `price` и поисковые поля.
Цена — DecimalField, а не float. Описание допускает NULL. Интервал часов —
от 0 до 24, закрытие позже открытия. Цена неотрицательна, название непустое.

ForeignKey `category` связывает много мест с одной категорией. `PROTECT`
запрещает удалять категорию с местами. `related_name="attractions"` позволяет
писать `category.attractions.all()`. Ограничения присутствуют в миграциях
и в базе, а не только в форме. `full_clean()` проверяет модель; `save()`
автоматически его не вызывает.

`save()` обновляет поисковые поля через casefold: это обеспечивает поиск
русских названий и описаний без учёта регистра в SQLite. При ручном изменении
названия или описания используйте экземпляр модели и save(), а не
QuerySet.update(): update() обходит метод save(). bulk_create() также обходит
save(). Это ограничение документировано, тесты проверяют обычное сохранение.

## Переход с ПР7

Старая база `data/attractions.sqlite` остаётся источником и не изменяется.
Перед работой её содержимое сохранено отдельным коммитом и резервной копией.
Новая база `db.sqlite3` создаётся миграциями; `--fake` и подмена файла не нужны.

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py import_legacy
```

Команда читает старую SQLite в режиме только чтения. Категории и места
записываются через ORM внутри transaction.atomic(), ID и связи сохраняются.
Повторный запуск не создаёт дубликаты, но обновляет совпадающие ID значениями
старой базы. Не запускайте импорт повторно, если хотите сохранить новые правки
этих объектов в ORM. Объекты с другими ID не удаляются. Ошибка переноса
откатывает всю операцию. Можно передать `--source путь/к/старой.sqlite`.

SQL-файлы, `db/` и их тесты оставлены как исторический слой ПР7. Изменённое
пользователем условие старого free_places сохранено в истории и исходном SQL.
Сайт к этому слою больше не обращается; бесплатные места теперь выбираются
через ORM `filter(price=0)`. Единственный новый прямой sqlite3 — чтение источника
в import_legacy, поскольку старая схема не принадлежит Django.
Консоль ПР3 по-прежнему использует JSON; автоматической синхронизации нет.

## Реализованные ORM-выражения

Каждая строка — самостоятельная выборка или операция для реального сценария,
а не подсчёт методов в одной цепочке. Функции находятся в web/services.py.

| № | Функция | Применение |
| --- | --- | --- |
| 1 | get_attractions | Список с select_related и сортировкой по имени |
| 2 | get_attraction | get(pk) для карточки, обработка DoesNotExist |
| 3 | category_list | all() для категорий на главной |
| 4 | get_category | Категория по уникальному name_key |
| 5 | category_places | Обратная связь category.attractions |
| 6 | free_places | filter(price=0), бесплатные места |
| 7 | paid_places | exclude(price=0), платные места в поиске |
| 8 | by_category | Фильтр по category__name_key связанной модели |
| 9 | within_budget | filter(price__lte), бюджет |
| 10 | open_at | Несколько условий по часам |
| 11 | search_name | icontains по названию |
| 12 | search_text | Q с OR по названию и описанию |
| 13 | get_attractions с price | Сортировка по цене, имени и ID |
| 14 | get_attractions с category | Сортировка по связанной категории |
| 15 | overview | aggregate: Count, Sum, Avg, Min, Max |
| 16 | free_count | Подсчёт бесплатных мест |
| 17 | category_stats | annotate: число мест и цены; пустые категории остаются |
| 18 | popular_categories | Фильтр после annotate, SQL HAVING |
| 19 | price_groups | values и annotate: группировка по платности |
| 20 | opening_hours | F, разность часов и имя категории, вывод через values |
| 21 | home_preview | Ограничение [:3] с устойчивой сортировкой |
| 22 | paginate | Paginator и ограничение QuerySet на текущую страницу |

CRUD дополнительно демонстрируется командой demo_orm: create, get, save,
delete и защита PROTECT. Все её изменения откатываются.

## Проверка и демонстрация

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py showmigrations
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m flake8 .
.\.venv\Scripts\python.exe manage.py demo_orm
```

93 теста проверяют старую логику, новый ORM, перенос и откат, constraints,
поиск, пагинацию, пустые выборки, PROTECT и выгрузку/загрузку фикстур.
Автоматически сгенерированные миграции исключены только из проверки длины
строк E501; остальные проверки flake8 к ним применяются.

Для просмотра SQL в браузере (локальная отладка):
```powershell
$env:DJANGO_TOOLBAR="1"
.\.venv\Scripts\python.exe manage.py runserver
```
Откройте карточку → справа SQL. Благодаря select_related категория и место
загружаются одним запросом. Панель можно свернуть кнопкой «Скрыть».
Чтобы выключить: остановить сервер, выполнить
`Remove-Item Env:DJANGO_TOOLBAR` и запустить его снова.

Экспорт актуальной ORM-базы (UTF-8 важен для русского текста в Windows):
```powershell
.\.venv\Scripts\python.exe -X utf8 manage.py dumpdata categories catalog --indent 2 --output data/export.json
```

Пагинация: 3 места на странице, размер CATALOG_PAGE_SIZE в settings.py.
Нечисловой page даёт первую страницу, отрицательный/слишком большой — последнюю.
Ссылки используют querystring и сохраняют фильтры. Недопустимый фильтр возвращает
400 с пояснением; пустой результат — 200; неизвестное место — обычную страницу 404.
Неизвестная сортировка каталога заменяется на name; в форме поиска — ошибка 400.
JS-фильтр «открытые сейчас» действует на текущую страницу; серверный фильтр
по часу на странице поиска применяется ко всей выборке до пагинации.
