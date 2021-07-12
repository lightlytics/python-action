/* eslint-disable no-undef */

// This is a MongoDB seed script, it will be used by the mongo docker, the syntax is JS MongoDB shell
// The Database used is set by MONGO_INITDB_DATABASE

// db.auth('admin', 'lightlytics2017')
db = db.getSiblingDB('lightlytics')
let res = [
  db.customers.insertOne(
    {
      _id: ObjectId('5063114bd386d8fadbd6b004'),
      customer_name: 'lightlytics',
      default_mail_address: 'superuser@lightlytics.com'
    }
  ),

  // ADMIN == SUPER USER FOR THE SYSTEM
  db.users.insertOne({
    _id: ObjectId('5f8844206af0a5fa2b5e27cc'),
    admin_user: true,
    change_password_next_login: false,
    default_customer_id: null,
    email: 'admin@lightlytics.com',
    full_name: 'Lightlytics Admin',
    hashed_password: BinData(0, 'MTE4MTdlYmJjMjJlZjMxZGRjZWZjN2M3'),
    password_expiration_date: ISODate('2021-12-24T13:54:27.414Z'),
    salt: BinData(0, 'ODlhZDI2YjA0NjIyZTA3MzUwMjI4MTUzMmZkZTk4MWVkM2I5NDEzMWI5MjI3ZDhiNjVkOTVhZTVlMWUzODRkYQ=='),
    status: 'ACTIVE'
  }),

  db.users.insertOne({
    _id: ObjectId('5f88449f6af0a5fa2b5e27cf'),
    admin_user: false,
    change_password_next_login: false,
    default_customer_id: '5063114bd386d8fadbd6b004',
    email: 'superuser@lightlytics.com',
    full_name: 'Lightlytics Superuser',
    hashed_password: BinData(0, 'NTk0MTljN2Y5Y2RmNmNmMzE5OTFmMGE0'),
    password_expiration_date: ISODate('2021-12-24T13:54:27.414Z'),
    salt: BinData(0, 'YTQwM2Y0MzE5YmFmZDI0ODA2Y2E5ODY5ZmZjMWE3ZWE0Y2NkNjY4NDMwNmNlNjg1MDBlZDk4MDBjYTU4NDA2Nw=='),
    status: 'ACTIVE'
  }),

  db.permissions.insertOne({
    customer_id: '5063114bd386d8fadbd6b004',
    role: 'SUPERUSER',
    user_id: '5f88449f6af0a5fa2b5e27cf'
  }),

  db.setLogLevel(0)
]

printjson(res)
