SELECT SUM(p.price * o.quantity) AS total_sales
FROM orders AS o
JOIN customers AS c ON o.customer_id = c.customer_id
JOIN products AS p ON o.product_id = p.product_id
WHERE o.order_date BETWEEN '2024-01-01' AND '2024-03-31' 
AND c.age >= 20 
AND c.gender = 'Female'