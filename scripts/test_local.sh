#!/bin/bash
# Quick local test script
echo "🧪 Starting PMGuru v7 locally..."
cd backend && pip install -r requirements.txt && python main.py &
BRAIN_PID=$!
sleep 3
echo "✅ Brain server running on http://localhost:8000"
echo "Test it: curl http://localhost:8000/health"
echo ""
echo "Now in another terminal:"
echo "  cd frontend && npm install --legacy-peer-deps && BRAIN_URL=http://localhost:8000 npm run dev"
wait $BRAIN_PID
