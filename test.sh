#!/bin/bash -e

echo "Testing..."
coverage run -m pytest tests && coverage report -m
