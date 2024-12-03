SELECT c.customer_name, SUM(p.price * o.quantity) AS total_purchase
FROM orders AS o
JOIN customers AS c ON o.customer_id = c.customer_id
JOIN products AS p ON o.product_id = p.product_id
WHERE o.order_date BETWEEN '2025-01-01' AND '2025-06-30' 
GROUP BY c.customer_id, c.customer_name
ORDER BY total_purchase DESC 
LIMIT 3;