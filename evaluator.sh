#!/bin/bash
# evaluator.sh
# This script runs a series of queries against the running API to check for correctness.

# wait for the API to be available
echo "Waiting for API to become available..."
until $(curl --output /dev/null --silent --head --fail http://localhost:8000/docs); do
    printf '.'
    sleep 5
done

echo ""
echo "API is up!"

queries=(
    "Top 3 customers by order count"
    "Average order value by region"
    "Monthly revenue for 2024"
    "Products that have never been ordered"
    "Total spend by customer segment"
)

SUCCESS_COUNT=0

for q in "${queries[@]}"; do
    echo "Testing query: $q"
    # Make the API call and check if the 'results' array is not empty
    response=$(curl -s -X POST http://localhost:8000/query \
        -H "Content-Type: application/json" \
        -d "{\"question\": \"$q\"}")
    
    # Extract results length using jq if available, otherwise python fallback
    if command -v jq >/dev/null 2>&1; then
        result_length=$(echo "$response" | jq '.results | length // 0' 2>/dev/null || echo 0)
    else
        result_length=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('results', [])))" 2>/dev/null || echo 0)
    fi
    
    if [ "$result_length" -gt 0 ]; then
        echo "✓ SUCCESS (returned $result_length rows)"
        SUCCESS_COUNT=$((SUCCESS_COUNT+1))
    else
        echo "X FAILED - No results returned"
        echo "Response was: $response"
    fi
done

echo ""
echo "$SUCCESS_COUNT / ${#queries[@]} queries succeeded."

if [ "$SUCCESS_COUNT" -ne "${#queries[@]}" ]; then
    exit 1
fi

echo "All queries verified successfully!"
exit 0
