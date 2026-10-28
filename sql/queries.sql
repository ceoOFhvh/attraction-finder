-- name: catalog_name
-- 01. Список мест по названию. Параметры: текущий час, час.
SELECT a.id, a.name, c.name AS category, a.category_id,
       a.open_hour, a.close_hour, a.price, a.description,
       (a.open_hour <= ? AND ? < a.close_hour) AS is_open_now
FROM attractions AS a
JOIN categories AS c ON c.id = a.category_id
ORDER BY a.search_name, a.id;

-- name: catalog_price
-- 02. Список мест по цене. Параметры: текущий час, час.
SELECT a.id, a.name, c.name AS category, a.category_id,
       a.open_hour, a.close_hour, a.price, a.description,
       (a.open_hour <= ? AND ? < a.close_hour) AS is_open_now
FROM attractions AS a
JOIN categories AS c ON c.id = a.category_id
ORDER BY a.price, a.search_name, a.id;

-- name: category_list
-- 03. Список категорий для главной страницы и поиска.
SELECT id, name FROM categories ORDER BY name_key, id;

-- name: detail
-- 04. Карточка с названием связанной категории (JOIN). Час, час, id.
SELECT a.id, a.name, c.name AS category, a.category_id,
       a.open_hour, a.close_hour, a.price, a.description,
       (a.open_hour <= ? AND ? < a.close_hour) AS is_open_now
FROM attractions AS a
JOIN categories AS c ON c.id = a.category_id
WHERE a.id = ?;

-- name: free_places
-- 05. Бесплатные места (WHERE). Час, час.
SELECT a.id, a.name, c.name AS category, a.category_id,
       a.open_hour, a.close_hour, a.price, a.description,
       (a.open_hour <= ? AND ? < a.close_hour) AS is_open_now
FROM attractions AS a
JOIN categories AS c ON c.id = a.category_id
WHERE a.price = 0
ORDER BY a.search_name, a.id;

-- name: search
-- 06. Поиск: час сейчас (дважды), название (дважды), категория (дважды),
-- бюджет (дважды), час посещения (трижды). NULL отключает фильтр.
SELECT a.id, a.name, c.name AS category, a.category_id,
       a.open_hour, a.close_hour, a.price, a.description,
       (a.open_hour <= ? AND ? < a.close_hour) AS is_open_now
FROM attractions AS a
JOIN categories AS c ON c.id = a.category_id
WHERE (? = '' OR instr(a.search_name, ?) > 0)
  AND (? IS NULL OR a.category_id = ?)
  AND (? IS NULL OR a.price <= ?)
  AND (? IS NULL OR (a.open_hour <= ? AND ? < a.close_hour))
ORDER BY a.price, a.search_name, a.id;

-- name: category_detail
-- 07. Категория по нормализованному имени. Параметр: name.casefold().
SELECT id, name FROM categories WHERE name_key = ?;

-- name: category_places
-- 08. Все места категории, связанной по FK (JOIN). Час, час, category_id.
SELECT a.id, a.name, c.name AS category, a.category_id,
       a.open_hour, a.close_hour, a.price, a.description,
       (a.open_hour <= ? AND ? < a.close_hour) AS is_open_now
FROM attractions AS a
JOIN categories AS c ON c.id = a.category_id
WHERE c.id = ?
ORDER BY a.search_name, a.id;

-- name: overview
-- 09. Агрегаты всех мест. COUNT(*) и COUNT(description) различаются при NULL.
SELECT COUNT(*) AS total, COUNT(description) AS described,
       MIN(price) AS min_price, MAX(price) AS max_price,
       AVG(price) AS avg_price, COALESCE(SUM(price), 0) AS total_price
FROM attractions;

-- name: free_count
-- 10. Отдельный агрегат бесплатных мест.
SELECT COUNT(*) AS total FROM attractions WHERE price = 0;

-- name: category_stats
-- 11. Статистика по категориям (LEFT JOIN, GROUP BY), включая пустые.
SELECT c.id, c.name, COUNT(a.id) AS places_count,
       MIN(a.price) AS min_price, MAX(a.price) AS max_price,
       AVG(a.price) AS avg_price
FROM categories AS c
LEFT JOIN attractions AS a ON a.category_id = c.id
GROUP BY c.id, c.name
ORDER BY places_count DESC, c.id;

-- name: price_groups
-- 12. Группировка по платному/бесплатному посещению.
SELECT CASE WHEN price = 0 THEN 'Бесплатно' ELSE 'Платно' END AS label,
       COUNT(*) AS places_count, AVG(price) AS avg_price
FROM attractions
GROUP BY CASE WHEN price = 0 THEN 'Бесплатно' ELSE 'Платно' END
ORDER BY avg_price, label;

-- name: popular_categories
-- 13. Категории с количеством мест больше порога (HAVING). Параметр: порог.
SELECT c.id, c.name, COUNT(a.id) AS places_count
FROM categories AS c
LEFT JOIN attractions AS a ON a.category_id = c.id
GROUP BY c.id, c.name
HAVING COUNT(a.id) > ?
ORDER BY places_count DESC, c.id;

-- name: home_preview
-- 14. Первые места для главной: ORDER BY, LIMIT, OFFSET. Час, час, лимит, сдвиг.
SELECT a.id, a.name, c.name AS category, a.category_id,
       a.open_hour, a.close_hour, a.price, a.description,
       (a.open_hour <= ? AND ? < a.close_hour) AS is_open_now
FROM attractions AS a
JOIN categories AS c ON c.id = a.category_id
ORDER BY a.id
LIMIT ? OFFSET ?;
