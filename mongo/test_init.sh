mongo -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD -authenticationDatabase admin <<EOF

    use $MONGO_TEST_INITDB_DATABASE;

    var user = '$MONGO_USER';
    var passwd = '$MONGO_PASSWORD';
    db.createUser({user: user, pwd: passwd, roles: [{
            "role" : "dbAdmin",
            "db" : "$MONGO_TEST_INITDB_DATABASE"
        },{
            "role" : "readWrite",
            "db" : "$MONGO_TEST_INITDB_DATABASE"
        }]});   
EOF