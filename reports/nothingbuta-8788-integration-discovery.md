# NothingButA 8788 Integration Discovery

Generated: 2026-05-20T09:11:53-04:00

## Status

PREPARED

## Created / Verified

- data/nothingbuta_review_queue.json
- nothingbuta/previews/nba-util-0001/index.html

## Required Integration Target

Patch the existing port 8788 dashboard, not a separate server.

## Likely Route Files

- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\dependencies\models.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\dependencies\utils.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\openapi\docs.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\openapi\models.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\openapi\utils.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\security\api_key.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\security\base.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\security\http.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\security\oauth2.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\security\open_id_connect_url.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\applications.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\background.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\cli.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\datastructures.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\encoders.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\exceptions.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\exception_handlers.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\logger.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\params.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\param_functions.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\responses.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\routing.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\templating.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\utils.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\_compat.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\__init__.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\fastapi\__main__.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\async_utils.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\bccache.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\compiler.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\debug.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\environment.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\exceptions.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\ext.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\filters.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\lexer.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\loaders.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\meta.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\nodes.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\parser.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\runtime.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\sandbox.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\tests.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\utils.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\jinja2\__init__.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\pip\_vendor\pygments\lexers\_mapping.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\pydantic\_internal\_generate_schema.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\pydantic\_internal\_validators.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\pydantic\config.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\pydantic\fields.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\pydantic\type_adapter.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\pydantic\version.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\starlette\templating.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\lifespan\off.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\lifespan\on.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\loops\asyncio.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\loops\auto.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\middleware\asgi2.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\middleware\message_logger.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\middleware\proxy_headers.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\middleware\wsgi.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\protocols\http\auto.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\protocols\http\flow_control.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\protocols\http\h11_impl.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\protocols\http\httptools_impl.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\protocols\websockets\auto.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\protocols\websockets\websockets_impl.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\protocols\websockets\wsproto_impl.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\protocols\utils.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\supervisors\basereload.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\supervisors\multiprocess.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\supervisors\statreload.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\supervisors\watchfilesreload.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\supervisors\__init__.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\config.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\main.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\server.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\workers.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\_subprocess.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\__init__.py
- C:\Users\dmchris\OpenClawOps\dashboard\.venv\Lib\site-packages\uvicorn\__main__.py
- C:\Users\dmchris\OpenClawOps\dashboard\app\main.py

## Likely Dashboard Templates

- C:\Users\dmchris\OpenClawOps\dashboard\app\templates\index.html
- C:\Users\dmchris\OpenClawOps\nothingbuta\previews\nba-util-0001\index.html

## Next Patch

Add a NothingButA tab/card to the discovered dashboard template and add local-only action routes to the discovered 8788 app route file.
