SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS cafe_order
	DEFAULT CHARACTER SET utf8mb4
	DEFAULT COLLATE utf8mb4_unicode_ci;

USE cafe_order;

DROP TABLE IF EXISTS delivery;
DROP TABLE IF EXISTS order_item;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS customer;

CREATE TABLE customer (
	id	INT	NOT NULL AUTO_INCREMENT,	-- MySQL 전용 문법: AUTO_INCREMENT
	name	VARCHAR(100)	NOT NULL,
	phone	VARCHAR(20)	NOT NULL,
	grade	ENUM('WHITE', 'BLACK', 'RED')	NOT NULL DEFAULT 'WHITE', -- MySQL 전용 문법: ENUM
	joined_at	DATETIME	NOT NULL,

	PRIMARY KEY (id),
	UNIQUE KEY uk_customer_phone (phone)
) ENGINE = InnoDB
DEFAULT CHARSET = utf8mb4
COMMENT = '회원만 저장한다.';


CREATE TABLE product (
	id	INT	NOT NULL AUTO_INCREMENT,
	name	VARCHAR(100)	NOT NULL,
	type	ENUM('DRINK', 'DESSERT')	NOT NULL,
	category	ENUM('COFFEE', 'NON_COFFEE', 'WHOLE_CAKE', 'SLICE_CAKE', 'BAKED_GOODS', 'BREAD')	NOT NULL,
	price	INT	NOT NULL,
	is_sold_out	BOOLEAN	NOT NULL DEFAULT FALSE,	-- MySQL 전용 문법: BOOLEAN은 TINYINT(1)로 구현됨

	PRIMARY KEY (id),
	UNIQUE KEY uk_product_name (name),
	CONSTRAINT chk_product_category CHECK (
		(type = 'DRINK' AND category IN ('COFFEE', 'NON_COFFEE')) OR
		(type = 'DESSERT' AND category IN ('WHOLE_CAKE', 'SLICE_CAKE', 'BAKED_GOODS', 'BREAD'))
	),
	CONSTRAINT chk_product_price CHECK (price >= 0)
) ENGINE = InnoDB
DEFAULT CHARSET = utf8mb4
COMMENT = '상품. 음료/디저트 공통.';


CREATE TABLE orders (
	id	INT	NOT NULL AUTO_INCREMENT,
	customer_id	INT	NULL,
	ordered_at	DATETIME	NOT NULL,
	status	ENUM('PENDING', 'PREPARING', 'COMPLETED', 'CANCELLED')	NOT NULL DEFAULT 'PENDING',
	order_type ENUM('IN', 'TOGO', 'DELIVERY')	NOT NULL,
	updated_at	DATETIME	NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, -- MySQL 전용 문법: ON UPDATE CURRENT_TIMESTAMP

	PRIMARY KEY (id),

	-- 회원 탈퇴 후에도 주문 기록과 매출은 남겨야 함 (ON DELETE SET NULL)
	CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customer(id) ON DELETE SET NULL
) ENGINE = InnoDB
DEFAULT CHARSET = utf8mb4
COMMENT = '주문. 총액은 order_item.unit_price * order_item.quantity의 합으로 계산한다.';

CREATE TABLE order_item (
	id	INT	NOT NULL AUTO_INCREMENT,
	order_id	INT	NOT NULL,
	product_id	INT	NOT NULL,
	quantity	INT	NOT NULL,
	unit_price	INT	NOT NULL, -- 주문 시점의 단가. product.price와 다를 수 있음
	size	ENUM('REGULAR', 'LARGE', 'MAX')	NULL, -- 음료만 해당
	temperature	ENUM('ICE', 'HOT')	NULL, -- 음료만 해당

	PRIMARY KEY (id),
	-- 주문이 삭제되면 그 주문 항목도 존재 이유 없음 (ON DELETE CASCADE)
	CONSTRAINT fk_order_item_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,

	-- 이미 판매된 상품은 삭제 불가 (ON DELETE RESTRICT)
	CONSTRAINT fk_order_item_product FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE RESTRICT,

	CONSTRAINT chk_order_item_unit_price CHECK (unit_price >= 0),
	CONSTRAINT chk_order_item_quantity CHECK (quantity > 0)
) ENGINE = InnoDB
DEFAULT CHARSET = utf8mb4
COMMENT = '주문 항목. 주문 시점의 단가와 수량을 저장';


CREATE TABLE delivery (
	id	INT	NOT NULL AUTO_INCREMENT,
	order_id	INT	NOT NULL,
	recipient_name	VARCHAR(100)	NOT NULL,
	recipient_phone	VARCHAR(20)	NOT NULL,
	address	VARCHAR(255)	NOT NULL,
	request	VARCHAR(255)	NULL,
	status	ENUM('WAITING', 'DELIVERING', 'DELIVERED')	NOT NULL DEFAULT 'WAITING',

	PRIMARY KEY (id),
	UNIQUE KEY uk_delivery_order (order_id), -- 주문 1건 : 배달 정보 1건

	-- 주문이 삭제되면 배달 정보도 존재 이유 없음 (ON DELETE CASCADE)
	CONSTRAINT fk_delivery_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
) ENGINE = InnoDB
DEFAULT CHARSET = utf8mb4
COMMENT = '배달 정보. 주문이 DELIVERY인 경우에만 생성';


SHOW TABLES;