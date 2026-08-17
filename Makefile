prod:
	cd app && yarn
	cd app && yarn build


%.sql: %
	pg_restore -f $@ $<


restore: b001.sql latest.dump.sql
