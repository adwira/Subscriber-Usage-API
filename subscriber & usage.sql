-- 1. Insert a new subscriber named Fajar, Basic plan, activated 24 January 2024
INSERT INTO subscribers (id, name, plan, activation_date)
VALUES ('SUB07', 'Fajar', 'Basic', '2024-01-24');

-- 2. Update Fajar's plan to Premium.
UPDATE subscribers SET plan = 'Premium' WHERE id = 'SUB07'; 

-- 3. Calculate the total data usage (sum of dataUsageMB across all snapshots) for all Premium plan subscribers.
SELECT SUM(data_usage_mb) AS total_data_usage_mb
FROM usages u
JOIN subscribers s ON u.subscriber_id = s.id
WHERE s.plan = 'Premium';

-- 4. Sort and display the top 3 subscribers by total data usage across all snapshots.
SELECT s.id, s.name, s.plan, COALESCE(SUM(u.data_usage_mb), 0) as total_data_usage_mb
FROM subscribers s
LEFT JOIN usages u ON s.id = u.subscriber_id
GROUP BY s.id, s.name, s.plan
ORDER BY  total_data_usage_mb DESC
LIMIT 3;

-- 5. Write a subquery to find subscribers whose average call minutes per snapshot is less than or equal to 30.
SELECT s.id, s.name, s.plan FROM subscribers s
WHERE s.id IN (
  SELECT subscriber_id FROM usages
  GROUP BY subscriber_id
  HAVING AVG(call_minutes) <= 30
);