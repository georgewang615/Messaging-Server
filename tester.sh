#!/bin/bash
single=("register" "login" "create" "joinchan" "say1" "say2" "say3" "channels" "utf8")
multi=("multi_register" "multi_login" "multi_create" "multi_joinchan")

port=5555
port1=8888

echo [ > text.json

chmod 777 text.json

for test in "${single[@]}"
do
    coverage run -a server.py $port &
    sleep 1s

    if [ `python3 client.py $port ./single_client/$test.txt | diff - ./single_client/$test.out | wc -l` == 0 ]
    then
        echo "  {\"$test\": \"Passed\" }," >> text.json
    else
        echo "  {\"$test\": \"Failed\" }," >> text.json
    fi
    pkill -f server.py
done

for test in "${multi[@]}"
do
    coverage run -a server.py $port &
    sleep 1s

    python3 client.py $port ./multi_client/"$test"1.txt > t1.out &
    python3 client.py $port ./multi_client/"$test"2.txt > t2.out

    if [ `diff t1.out ./multi_client/"$test"1.out | wc -l` == 0 ] && [ `diff t2.out ./multi_client/"$test"2.out | wc -l` == 0 ]
    then
        echo "  {\"$test\": \"Passed\" }," >> text.json
    else
        echo "  {\"$test\": \"Failed\" }," >> text.json
    fi
    pkill -f server.py
    rm t1.out
    rm t2.out
done

sleep 5s

coverage report -i

sed '$ s/,$//g' text.json > results.json
rm text.json
echo ] >> results.json