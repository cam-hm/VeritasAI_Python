#!/bin/bash
# Monitor upload status in realtime

cd /Users/camhm/Project/VeritasAI_Python
source venv/bin/activate

echo "🔍 Monitoring document uploads..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "📊 Document Status ($(date +%H:%M:%S))"
    echo "========================================"
    
    python manage.py shell -c "
from app.models import Document
from django.utils import timezone

docs = Document.objects.all().order_by('-id')[:5]
for doc in docs:
    age = (timezone.now() - doc.created_at).total_seconds()
    age_str = f'{int(age)}s' if age < 60 else f'{int(age/60)}m'
    
    status_emoji = {
        'pending': '⏳',
        'processing': '⚙️',
        'completed': '✅',
        'failed': '❌'
    }.get(doc.status, '❓')
    
    print(f'{status_emoji} [{doc.id}] {doc.name[:40]:40} | {doc.status:10} | {doc.num_chunks:2} chunks | {age_str:5}')
    if doc.error_message and doc.status == 'failed':
        print(f'     Error: {doc.error_message[:60]}...')

pending_count = Document.objects.filter(status='pending').count()
processing_count = Document.objects.filter(status='processing').count()
if pending_count > 0 or processing_count > 0:
    print(f'\n⚠️  {pending_count} pending, {processing_count} processing')
" 2>/dev/null
    
    echo ""
    echo "📝 Latest logs:"
    if ls storage/logs/process_*.log >/dev/null 2>&1; then
        tail -n 3 storage/logs/process_*.log 2>/dev/null | tail -3
    else
        echo "   No logs yet"
    fi
    
    sleep 2
done

