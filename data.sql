USE cafe_order;

-- DELETE FROM delivery;
-- DELETE FROM order_item;
-- DELETE FROM orders;
-- DELETE FROM product;
-- DELETE FROM customer;

-- ALTER TABLE delivery AUTO_INCREMENT = 1;	-- MySQL 전용 문법: AUTO_INCREMENT 초기화
-- ALTER TABLE order_item AUTO_INCREMENT = 1;
-- ALTER TABLE orders AUTO_INCREMENT = 1;
-- ALTER TABLE product AUTO_INCREMENT = 1;
-- ALTER TABLE customer AUTO_INCREMENT = 1;

INSERT INTO customer (name, phone, grade, joined_at) VALUES
	('김서연', '010-2431-8890', 'BLACK', '2026-01-14 10:22:00'),
	('박도윤', '010-3782-1145', 'WHITE', '2026-02-03 15:40:00'),
	('이하은', '010-9014-6672', 'RED', '2025-11-22 09:05:00'),
	('최우진', '010-5528-3301', 'WHITE', '2026-03-18 18:33:00'),
	('정민서', '010-8846-9027', 'BLACK', '2026-01-30 12:11:00'),
	('강지호', '010-6193-4458', 'WHITE', '2026-04-02 11:47:00'),
	('윤채원', '010-7350-2284', 'WHITE', '2026-05-21 16:02:00'),
	('임건우', '010-4467-7719', 'RED', '2025-12-09 08:58:00'),
	('한소율', '010-2085-5536', 'BLACK', '2026-02-27 14:20:00'),
	('신예린', '010-3319-8842', 'WHITE', '2026-07-08 13:30:00');	-- 주문 이력 없음

INSERT INTO product (name, type, category, price, is_sold_out) VALUES
	('아메리카노', 'DRINK', 'COFFEE', 4000, FALSE),	-- id 1  2026-08-01 가격 인상 (3500 -> 4000)
	('카페라떼', 'DRINK', 'COFFEE', 4500, FALSE),
	('에스프레소', 'DRINK', 'COFFEE', 3500, FALSE),
	('딸기스무디', 'DRINK', 'NON_COFFEE', 6000, FALSE),
	('망고스무디', 'DRINK', 'NON_COFFEE', 6000, FALSE),
	('블루베리스무디','DRINK', 'NON_COFFEE', 6000, TRUE),	-- id 6  품절, 판매 이력 없음
	('초코케이크', 'DESSERT', 'SLICE_CAKE', 7000, FALSE),
	('치즈케이크', 'DESSERT', 'SLICE_CAKE', 7500, FALSE),
	('마카롱세트', 'DESSERT', 'BAKED_GOODS', 12000, FALSE),
	('베이글', 'DESSERT', 'BREAD', 3800, FALSE);

INSERT INTO orders (customer_id, ordered_at, status, order_type) VALUES	-- 비회원 1 / 취소 1
	(1, '2026-06-05 09:20:00', 'COMPLETED', 'IN'),
	(3, '2026-06-12 14:10:00', 'COMPLETED', 'DELIVERY'),
	(NULL, '2026-06-27 11:35:00', 'COMPLETED', 'DELIVERY'),	-- 비회원
	(5, '2026-07-03 16:45:00', 'COMPLETED', 'DELIVERY'),
	(2, '2026-07-09 10:15:00', 'CANCELLED', 'DELIVERY'),
	(8, '2026-07-16 13:50:00', 'COMPLETED', 'DELIVERY'),
	(4, '2026-07-24 18:05:00', 'COMPLETED', 'TOGO'),
	(1, '2026-07-30 08:40:00', 'COMPLETED', 'DELIVERY'),
	(9, '2026-08-06 15:25:00', 'COMPLETED', 'DELIVERY'),
	(6, '2026-08-14 17:10:00', 'COMPLETED', 'DELIVERY'),
	(7, '2026-08-27 14:20:00', 'COMPLETED', 'DELIVERY'),
	(3, '2026-09-03 11:40:00', 'PREPARING', 'DELIVERY');

INSERT INTO order_item (order_id, product_id, quantity, unit_price, size, temperature) VALUES
	(1, 1, 2, 3500, 'REGULAR', 'HOT'),	-- 아메리카노 (인상 전)
	(1, 7, 1, 7000, NULL, NULL),
	(2, 2, 1, 4500, 'LARGE', 'ICE'),
	(2, 8, 1, 7500, NULL, NULL),
	(3, 1, 1, 3500, 'REGULAR', 'ICE'),
	(4, 4, 2, 6000, 'LARGE', 'ICE'),
	(4, 9, 1, 12000, NULL, NULL),
	(5, 2, 1, 4500, 'REGULAR', 'HOT'),
	(6, 3, 1, 3500, 'REGULAR', 'HOT'),
	(6, 10, 2, 3800, NULL, NULL),
	(7, 5, 1, 6000, 'MAX', 'ICE'),
	(8, 1, 3, 3500, 'LARGE', 'ICE'),
	(9, 2, 2, 4500, 'REGULAR', 'ICE'),
	(9, 8, 1, 7500, NULL, NULL),
	(10, 4, 1, 6000, 'REGULAR', 'ICE'),
	(10, 7, 1, 7000, NULL, NULL),
	(11, 1, 2, 4000, 'MAX', 'ICE'),	-- 아메리카노 (인상 후 단가)
	(11, 10, 1, 3800, NULL, NULL),
	(12, 5, 1, 6000, 'LARGE', 'ICE'),
	(12, 9, 1, 12000, NULL, NULL);

INSERT INTO delivery (order_id, recipient_name, recipient_phone, address, request, status) VALUES
	(2, '이하은', '010-9014-6672', '서울시 강남구 테헤란로 123', '문 앞에 두고 가주세요.', 'DELIVERED'),
	(3, '홍길동', '010-0001-0333', '서울시 서초구 서초대로 456', NULL, 'DELIVERED'),
	(4, '정민서', '010-8846-9027', '서울시 송파구 올림픽로 789', '벨 누르지 말아주세요.', 'DELIVERED'),
	(5, '박도윤', '010-3782-1145', '서울시 강동구 천호대로 101', NULL, 'WAITING'),
	(6, '임건우', '010-4467-7719', '서울시 마포구 월드컵북로 101', '경비실에 맡겨주세요.', 'DELIVERED'),
	(8, '김서연', '010-2431-8890', '서울시 용산구 한강대로 202', NULL, 'DELIVERED'),
	(9, '한소율', '010-2085-5536', '서울시 동작구 상도로 303', '도착 10분 전 연락 주세요.', 'DELIVERED'),
	(10, '강지호', '010-6193-4458', '서울시 강서구 공항대로 505', NULL, 'DELIVERED'),
	(11, '윤채원', '010-7350-2284', '서울시 관악구 관악로 404', '공동현관 1234', 'DELIVERED'),
	(12, '이하은', '010-9014-6672', '서울시 금천구 가산디지털1로 606', NULL, 'DELIVERING');

SELECT 'customer' AS table_name, COUNT(*) AS row_count FROM customer
UNION ALL SELECT 'product', COUNT(*) FROM product
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_item', COUNT(*) FROM order_item
UNION ALL SELECT 'delivery', COUNT(*) FROM delivery;