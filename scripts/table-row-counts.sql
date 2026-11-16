SELECT format(
    'SELECT %L, %L, count(*)::text FROM %I.%I',
    schemaname,
    tablename,
    schemaname,
    tablename
)
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename
\gexec
