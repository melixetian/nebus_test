#!/bin/bash

API_URL="http://localhost:8000/api/v1/payments"
API_KEY="secret_api_key"
IDEMP_KEY="test-key-$(date +%s)"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PASS="${GREEN}PASS${NC}"
FAIL="${RED}FAIL${NC}"

echo "Starting API tests..."
echo "========================================"

# 1. Успешное создание платежа
echo "1. Test: Create payment (POST /api/v1/payments)..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL" \
  -H "X-API-Key: $API_KEY" \
  -H "Idempotency-Key: $IDEMP_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 150.00,
    "currency": "RUB",
    "description": "Test payment",
    "webhook_url": "https://httpbin.org/post"
  }')

HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_STATUS" -eq 202 ]; then
    echo -e "$PASS: HTTP Status 202 Accepted"
    PAYMENT_ID=$(echo $BODY | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    echo "      Payment ID: $PAYMENT_ID"
else
    echo -e "$FAIL: Expected status 202, got $HTTP_STATUS"
    echo "      Response: $BODY"
    exit 1
fi
echo "----------------------------------------"

# 2. Проверка идемпотентности
echo "2. Test: Idempotency (repeat POST with same key)..."
RESPONSE2=$(curl -s -w "\n%{http_code}" -X POST "$API_URL" \
  -H "X-API-Key: $API_KEY" \
  -H "Idempotency-Key: $IDEMP_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 150.00,
    "currency": "RUB",
    "description": "Test payment",
    "webhook_url": "https://httpbin.org/post"
  }')

HTTP_STATUS2=$(echo "$RESPONSE2" | tail -n1)
if [ "$HTTP_STATUS2" -eq 202 ]; then
    echo -e "$PASS: HTTP Status 202 Accepted (Existing payment returned)"
else
    echo -e "$FAIL: Expected status 202, got $HTTP_STATUS2"
    exit 1
fi
echo "----------------------------------------"

# 3. Ошибка валидации
echo "3. Test: Validation error (negative amount)..."
RESPONSE3=$(curl -s -w "\n%{http_code}" -X POST "$API_URL" \
  -H "X-API-Key: $API_KEY" \
  -H "Idempotency-Key: new-key-$(date +%s)" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": -50.00,
    "currency": "RUB",
    "webhook_url": "https://httpbin.org/post"
  }')

HTTP_STATUS3=$(echo "$RESPONSE3" | tail -n1)
if [ "$HTTP_STATUS3" -eq 422 ]; then
    echo -e "$PASS: HTTP Status 422 Unprocessable Entity"
else
    echo -e "$FAIL: Expected status 422, got $HTTP_STATUS3"
    exit 1
fi
echo "----------------------------------------"

# 4. Ошибка авторизации
echo "4. Test: Authorization error (invalid API key)..."
RESPONSE4=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/$PAYMENT_ID" \
  -H "X-API-Key: wrong_key")

HTTP_STATUS4=$(echo "$RESPONSE4" | tail -n1)
if [ "$HTTP_STATUS4" -eq 401 ]; then
    echo -e "$PASS: HTTP Status 401 Unauthorized"
else
    echo -e "$FAIL: Expected status 401, got $HTTP_STATUS4"
    exit 1
fi
echo "----------------------------------------"

# 5. Проверка работы Consumer'а
echo "5. Waiting for Consumer to process payment (10 seconds)..."
sleep 10

echo "   Checking payment status (GET /api/v1/payments/{id})..."
RESPONSE5=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/$PAYMENT_ID" \
  -H "X-API-Key: $API_KEY")

HTTP_STATUS5=$(echo "$RESPONSE5" | tail -n1)
BODY5=$(echo "$RESPONSE5" | sed '$d')
STATUS=$(echo $BODY5 | grep -o '"status":"[^"]*' | cut -d'"' -f4)

if [ "$HTTP_STATUS5" -eq 200 ]; then
    echo -e "$PASS: HTTP Status 200 OK"
    echo "      Current payment status: $STATUS"
    if [ "$STATUS" != "pending" ]; then
        echo -e "$PASS: Payment successfully processed by Consumer!"
    else
        echo -e "$FAIL: Payment is still 'pending'. Consumer might be slow or not running."
    fi
else
    echo -e "$FAIL: HTTP Status: $HTTP_STATUS5"
    exit 1
fi

echo "========================================"
echo "All tests passed successfully!"
