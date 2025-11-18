#!/bin/bash
# Script để debug upload process

echo "🔍 Checking latest documents..."
cd /Users/camhm/Project/VeritasAI_Python
source venv/bin/activate

python manage.py shell -c "
from app.models import Document
docs = Document.objects.all().order_by('-id')[:3]
for doc in docs:
    print(f'📄 ID {doc.id}: {doc.name} - {doc.status} (chunks: {doc.num_chunks})')
"

echo ""
echo "📝 Checking process logs..."
if [ -d storage/logs ] && [ "$(ls -A storage/logs)" ]; then
    ls -lh storage/logs/
    echo ""
    echo "📄 Latest log content:"
    tail -50 storage/logs/process_*.log 2>/dev/null || echo "No logs yet"
else
    echo "No logs found yet. Upload a file first!"
fi

echo ""
echo "🔄 Checking running processes..."
ps aux | grep -E "(python.*process_document|python.*manage)" | grep -v grep || echo "No background processes"

