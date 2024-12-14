# Database Backup and Recovery
This document describes how to backup and restore the database of tutor-service.

## Automated Backup and Recovery scripts

The backup and recovery scripts are available in the `automation-service/scripts` directory. The scripts are:

- `backup-tutor-service-database.sh`: This script takes the backup of the database and stores it in the `tutor-service/backup` directory.
- `restore-tutor-service-database.sh`: This script restores the database from the backup file.
These must be run from the `automation-service` `root` folder.


You need for both scripts to provide the container id of the database container as an argument. You can get the container id by running the following command:

```bash
docker ps
```
Then choose the container id of the database container. The image should be postgres:latest. So choose the container id of the postgres:latest image.

Example:
```bash
source scripts/backup-tutor-service-database.sh database-container-id
```

For the restore script, you need to provide the container id of the database container and the name of the dump file as an argument. The dump file should be in the `tutor-service/backup` directory.
```bash
source scripts/restore-tutor-service-database.sh database-container-id dump-timestamp.sql
```

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