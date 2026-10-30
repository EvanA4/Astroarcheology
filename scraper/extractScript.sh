#!/usr/bin/env bash

count=20
for ((i = 1; i <= count; i++)); do
  python extractor.py cross-verified-database.csv 1.csv 1
done