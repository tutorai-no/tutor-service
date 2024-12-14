# Database Backup and Recovery
This document describes how to backup and restore the database of tutor-service.

## Backup

To get the backup of the database, you can use the following commands:

```bash
docker ps
```
Choose the container id of the database container. The image should be postgres:latest.

Then run the following command to get the backup of the database:

```bash
docker exec -t your-db-container pg_dumpall -c -U tutoraiuser > dump_$(date +%Y-%m-%d_%H_%M_%S).sql
```


This command will create a dump file in the current directory with the name dump_<current_date_time>.sql.

### Verify the backup

To verify the backup, you can use the following command:

```bash
head -n 10 your_dump.sql
```


The output should look like this:
```txt
--
-- PostgreSQL database cluster dump
--

SET default_transaction_read_only = off;

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
--
```

## Restore

To restore the database from the backup, you can use the following commands:

```bash
cat your_dump.sql | docker exec -i your-db-container psql -U tutoraiuser -d tutoraidb
```