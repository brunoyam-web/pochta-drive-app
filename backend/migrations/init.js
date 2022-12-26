db = db.getSiblingDB('gshare');
db.createCollection("users");
db.createCollection("service_accounts");

db.service_accounts.createIndex({email: 1}, {unique: true})

db.service_accounts.insertMany([
    {
        email: "INSERT_EMAIL",
        refresh_token: "INSERT_REFRESH_TOKEN",
        storage_limit: 16106127360, // дефолтное значение - 15ГБ
    }
])
