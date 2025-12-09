

-- 1. DEPOSIT (Successful)
BEGIN;

UPDATE Account
SET Balance = Balance + 5000
WHERE AccountNo = 101;

COMMIT;

-- 2. WITHDRAWAL (Error → ROLLBACK)
BEGIN;

UPDATE Account
SET Balance = Balance - 20000
WHERE AccountNo = 101;

-- Simulate error: insufficient balance
-- Trigger ROLLBACK
ROLLBACK;

-- 3. TRANSFER
BEGIN;

-- Debit Sender
UPDATE Account
SET Balance = Balance - 1000
WHERE AccountNo = 101;

-- Credit Receiver
UPDATE Account
SET Balance = Balance + 1000
WHERE AccountNo = 102;

COMMIT;

-- 4. SAVEPOINT Demo
BEGIN;

INSERT INTO Customer (Name, CNIC, Contact)
VALUES ('Ali Khan', '35202-1234567-8', '03001234567');

SAVEPOINT A;

INSERT INTO Customer (Name, CNIC, Contact)
VALUES ('Test User', '99999-9999999-9', '00000000000');

-- Undo last insert only
ROLLBACK TO A;

COMMIT;
