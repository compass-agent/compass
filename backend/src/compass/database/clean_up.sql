SELECT caption, COUNT(*) as count
FROM templates
GROUP BY caption;
