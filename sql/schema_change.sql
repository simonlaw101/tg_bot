-- alerts table
CREATE TABLE IF NOT EXISTS alerts (
    fromid integer NOT NULL,
	name text,
    types text NOT NULL,
	code text NOT NULL,
	operators text NOT NULL,
	amount text NOT NULL,
    chatid integer NOT NULL,
	PRIMARY KEY (fromid, types, code, operators)
);
-- currencies table
CREATE TABLE IF NOT EXISTS currencies (
    code text PRIMARY KEY,
	descs text NOT NULL
);