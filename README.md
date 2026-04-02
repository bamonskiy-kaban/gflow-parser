# TMP README
## Тестовый запуск с локальным хранилищем

### 1. Клон репы
```commandline
git clone https://github.com/bamonskiy-kaban/gflow
cd gflow/docker/test
```

### 2. Копирование шаблонного .env-файла и установка переменных окружения
```commandline
cp example.env .env
```

В файле .env установить значение переменных окружения:
- LOGSTASH_HOST - хост, на котором развернут Logstash
- OPENSEARCH_HOST - хост, на котором развернут OpenSearch
- LOCAL_TARGETS_DIR - директория с триажами

### 3. Запуск 
Запуск ELK-стека
```commandline
cd docker/e2e/elk
docker-compose up -d
```

Запуск приложения
```commandline
cd docker/test/
docker-compose up --build
```


## Формат триаж-копии
Все передаваемые триаж-копии должны быть представлены в .TAR-архиве. Пока конфигурация настроена только для виндовых триажей, поэтому ниже представлена информация только по ним.
TAR-архив триаж-копии должен иметь следующую структуру:

```commandline
triage.tar
    |_fs/
        |_<DISK_LABEL_1>:/
            |_<triage_files>
        |_<DISK_LABEL_2>:/
            |_<triage_files>
```

Пример:
```commandline
triage.tar
    |_fs/
        |_C:/
            |_<triage_files>
```

## Запуск обработки триажа и получение результатов
Инициирование обработки триажа выполняется посредством POST-запроса, с указанием расположения .TAR-файла триажа и префикса:

```commandline
curl -X POST http://localhost:8000/evidence -H 'Content-Type: application/json' -d '{"prefix": "fulltest", "relative_file_path": "term-4.tar"}'
```
Данный запрос вернет идентификатор триажа, взятого в работу.
Префикс - произвольная строка. Результаты парсинга сохраняются в OpenSearch в индекс, имя которого соответствует правилу <prefix>-<evidence_id>.

Для получения результатов рекомендуется использовать скрипт `test.py`, запуская его следующим образом:
```commandline
python3 test.py <evidence_id>
```