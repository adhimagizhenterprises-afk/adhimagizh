-- Initialize all microservice databases
CREATE DATABASE auth_db;
CREATE DATABASE booking_db;
CREATE DATABASE tracking_db;
CREATE DATABASE operations_db;
CREATE DATABASE agent_db;
CREATE DATABASE notification_db;
CREATE DATABASE payment_db;

GRANT ALL PRIVILEGES ON DATABASE auth_db TO swiftship;
GRANT ALL PRIVILEGES ON DATABASE booking_db TO swiftship;
GRANT ALL PRIVILEGES ON DATABASE tracking_db TO swiftship;
GRANT ALL PRIVILEGES ON DATABASE operations_db TO swiftship;
GRANT ALL PRIVILEGES ON DATABASE agent_db TO swiftship;
GRANT ALL PRIVILEGES ON DATABASE notification_db TO swiftship;
GRANT ALL PRIVILEGES ON DATABASE payment_db TO swiftship;
