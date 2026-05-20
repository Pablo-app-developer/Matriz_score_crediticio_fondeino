import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fondeino_web.settings')

application = get_wsgi_application()

# Aplicar migraciones pendientes al arrancar en Vercel
if os.environ.get('VERCEL') == '1':
    try:
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            from django.core.management import call_command
            call_command('migrate', '--noinput', verbosity=0)
    except Exception:
        pass

app = application
