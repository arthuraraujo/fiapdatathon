#!/bin/bash

API_URL=${1:-http://localhost:5050/api/predict}
EXAMPLES_FILE="docs/payload_examples.json"

if ! command -v jq &> /dev/null; then
  echo "Por favor, instale o jq para rodar este script (https://stedolan.github.io/jq/)"
  exit 1
fi

COUNT=$(jq length $EXAMPLES_FILE)
echo "Testando $COUNT exemplos do arquivo $EXAMPLES_FILE na URL $API_URL"

for i in $(seq 0 $((COUNT-1))); do
  DESC=$(jq -r ".[$i].description" $EXAMPLES_FILE)
  PAYLOAD=$(jq -c ".[$i].payload" $EXAMPLES_FILE)
  echo -e "\n---\nExemplo $i: $DESC"
  echo "Payload: $PAYLOAD"
  RESPONSE=$(curl -s -X POST "$API_URL" -H "Content-Type: application/json" -d "{\"payload\":$PAYLOAD}")
  echo "Resposta: $RESPONSE"
done 