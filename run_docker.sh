#!/bin/bash

pip freeze > requirements.txt

if docker-compose up --build; then
    echo "Build and launch successful."
else
    echo "Build or launch failed."
    exit 1
fi



