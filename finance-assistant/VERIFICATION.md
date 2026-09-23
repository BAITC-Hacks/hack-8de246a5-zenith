# Результаты проверки · 23 сентября 2026

- Backend: `python -m pytest tests -q` — **13 passed**.
- Frontend: `npm run build` — TypeScript и Vite production build завершены успешно.
- Браузер: Edge headless, 1440×1100 и 390×844; ошибок JavaScript и горизонтального переполнения нет.
- Проверены: загрузка демо, повторный импорт без дублей, отображение диаграмм и локальных инсайтов, выбор месяца, переключение KZT/RUB, невалидный CSV, понятная ошибка чата без ключа.
- Скриншоты: `preview-desktop.png`, `preview-mobile.png`.
- Реальный Claude API не вызывался: ключ не задан. Пакетирование, JSON-модели, сопоставление ID и fallback проверены тестами с подменой ответов.
- Docker Compose подготовлен, но не запускался: Docker отсутствует в среде проверки. Приложение проверено при прямом запуске FastAPI и Vite.

Проверенные основные версии backend: Python 3.12.10, FastAPI 0.141.1, SQLAlchemy 2.0.54, Anthropic SDK 1.8.0. Версии frontend зафиксированы в `package-lock.json`.
