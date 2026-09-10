SET NAMES utf8mb4;

USE cafe_order;

-- 기본 조회 where, order by, limit 포함 4개 이상

SELECT id, name, type, category, price
FROM product
WHERE price >= 6000
ORDER BY price DESC, name;

SELECT id, name, category, price
FROM product
WHERE is_sold_out = TRUE; -- BOOLEAN은 MySQL 내부적으로는 TINYINT(1)이므로 TRUE 대신 1로 비교해도 동일하게 동작한다.

SELECT id, customer_id, ordered_at, status, order_type
FROM orders
ORDER BY ordered_at DESC LIMIT 5;

SELECT id, customer_id, ordered_at, status, order_type
FROM orders
WHERE ordered_at >= '2026-07-01' AND ordered_at < '2026-08-01'
ORDER BY ordered_at;

-- join. inner join 2개, left join 1개 이상 포함

-- [INNER JOIN] 주문내역 + 회원 정보 (비회원 x)
SELECT o.id AS order_id,
	c.name AS customer_name,
	c.grade,
	o.ordered_at,
	o.order_type,
	o.status
FROM orders o
INNER JOIN customer c ON c.id = o.customer_id
ORDER BY o.ordered_at;

-- [INNER JOIN] 특정 주문의 상세 내역
SELECT o.id AS order_id,
	o.ordered_at,
	p.name AS product_name,
	i.size,
	i.temperature,
	i.quantity,
	i.unit_price,
	i.quantity * i.unit_price AS amount
FROM order_item i
INNER JOIN orders o ON o.id = i.order_id
INNER JOIN product p ON p.id = i.product_id
WHERE o.id = 1;

-- [LEFT JOIN] 회원별 주문 건수 (주문이력 x 회원 포함)
SELECT c.id,
	c.name,
	c.grade,
	COUNT(o.id) AS order_count
FROM customer c
LEFT JOIN orders o ON o.customer_id = c.id
GROUP BY c.id, c.name, c.grade
ORDER BY order_count DESC, c.id;

-- [LEFT JOIN] 판매 이력x 상품
SELECT p.id,
	p.name,
	p.category,
	p.price
FROM product p
LEFT JOIN order_item i ON i.product_id = p.id
WHERE i.id IS NULL;


-- 집계 count, sum, avg 중 2개 이상 + group by

-- [집계] 상품별 판매 수량, 매출
SELECT p.id,
	p.name,
	SUM(i.quantity) AS total_quantity,
	SUM(i.quantity * i.unit_price) AS total_revenue
FROM order_item i
INNER JOIN product p ON p.id = i.product_id
INNER JOIN orders o ON o.id = i.order_id
WHERE o.status <> 'CANCELLED'
GROUP BY p.id, p.name
ORDER BY total_revenue DESC;

-- [집계] 월별 주문 건수, 매출
SELECT DATE_FORMAT(o.ordered_at, '%Y-%m') AS order_month, -- MySQL 전용 문법: DATE_FORMAT (표준 SQL은 EXTRACT)
	COUNT(DISTINCT o.id) AS order_count,
	SUM(i.quantity * i.unit_price) AS revenue
FROM orders o
INNER JOIN order_item i ON i.order_id = o.id
WHERE o.status <> 'CANCELLED'
GROUP BY order_month
ORDER BY order_month;

-- [집계] 상품 분류별 개수, 평균 가격
SELECT type,
	category,
	COUNT(*) AS product_count,
	ROUND(AVG(price)) AS avg_price
FROM product
GROUP BY type, category
ORDER BY type, category;


-- [서브쿼리] 평균 주문 금액보다 많이 결제한 주문 조회
SELECT o.id AS order_id,
	o.ordered_at,
	SUM(i.quantity * i.unit_price) AS order_total
FROM orders o
INNER JOIN order_item i ON i.order_id = o.id
WHERE o.status <> 'CANCELLED'
GROUP BY o.id, o.ordered_at
HAVING SUM(i.quantity * i.unit_price) > (
	SELECT AVG(t.order_total)
	FROM (
	SELECT SUM(i2.quantity * i2.unit_price) AS order_total
	FROM orders o2
	INNER JOIN order_item i2 ON i2.order_id = o2.id
	WHERE o2.status <> 'CANCELLED'
	GROUP BY o2.id
	) AS t
)
ORDER BY order_total DESC;


-- 데이터 수정 및 삭제 2개 이상 update, delete 포함

-- [UPDATE] 배송완료 주문 -> 완료 처리
UPDATE orders SET status = 'COMPLETED' WHERE id = 12;

UPDATE delivery SET status = 'DELIVERED' WHERE order_id = 12;

-- 변경 결과 확인
SELECT o.id, o.status AS order_status, o.updated_at, d.status AS delivery_status
FROM orders o
INNER JOIN delivery d ON d.order_id = o.id
WHERE o.id = 12;


-- [DELETE] 취소된 주문 삭제

-- 삭제 전 상태
SELECT
	(SELECT COUNT(*) FROM orders WHERE status = 'CANCELLED') AS cancelled_orders,
	(SELECT COUNT(*) FROM order_item WHERE order_id = 5) AS items_of_order_5,
	(SELECT COUNT(*) FROM delivery WHERE order_id = 5) AS delivery_of_order_5;

DELETE FROM orders WHERE status = 'CANCELLED';

-- 삭제 후 상태 확인
SELECT
	(SELECT COUNT(*) FROM orders WHERE status = 'CANCELLED') AS cancelled_orders,
	(SELECT COUNT(*) FROM order_item WHERE order_id = 5) AS items_of_order_5,
	(SELECT COUNT(*) FROM delivery WHERE order_id = 5) AS delivery_of_order_5;


-- 인덱스 1개 이상 (create index + 적용 이유 1줄)

-- [CREATE INDEX] orders.ordered_at에 인덱스 생성
-- 이유: 기간별 조회(Q04)와 월별 집계(Q10)에서 ordered_at이 WHERE·GROUP BY 조건으로 쓰이는데, 인덱스가 없으면 orders 전체를 처음부터 끝까지 훑어야 함.


-- 인덱스 생성 전 실행 계획
EXPLAIN
SELECT id, ordered_at, status
FROM orders
WHERE ordered_at >= '2026-07-01' AND ordered_at < '2026-08-01';

CREATE INDEX idx_orders_ordered_at ON orders (ordered_at);

-- 인덱스 생성 후 실행 계획
-- type이 ALL(전체 스캔)에서 range(범위 스캔)로 바뀌는지 확인한다.
EXPLAIN
SELECT id, ordered_at, status
FROM orders
WHERE ordered_at >= '2026-07-01' AND ordered_at < '2026-08-01';

-- 생성된 인덱스 확인
SHOW INDEX FROM orders;