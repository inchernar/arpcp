## arpcp методы (заголовки пакетов):
* async task ->
* signal <-
* get results ->

* sync task ->

* echolocation -> -> ->

---

## Режимы работы контроллера:

* включение
* планировщик задач
    * синхронизация состава кластера
        * периодические эхо-запросы
        * проверка наличия агента в кластере
        * регистрация новых агентов в кластере
            * получение ip и mac от агентов
            * назначение уникальных идентификаторов агентам
            * составление списка агентов (в БД)
        * удаление агента из кластера
* постановка задач (есть возможность вызвать клиентский код)
* ожидание синхронных запросов от агентов (работает сервер)
* выключение

---

## Режимы работы агента:

* включение
* ожидание постановки задач
* сигнализирование контроллеру
* выключение

---

## Структура aprcp сообщения:

Структура протокола сделана по аналогии с json

`Ключевое слово (purpose_word)` - (ATASK, TASK, GET, ECHO, SIGNAL)

`Версия arpcp (p_version)` - (ARPCP/1.0)

```json
request
{
    "purpose_word": "<purpose_word>",
    "p_version": "ARPCP/<p_version>",  
    "remote-func": "<remote-func>",
    "task-id": "<task-id>",
    "task-status": "<task-status>",
    "remote-func-arg" : {
        "0": "<arg1>", 
        "1": "<arg2>",
        ...
        "<i>": "<arg<i>>"
        }
}

response
{
    "code": "<code>",
    "result": "<result>"
}
```
Плюс (+) рядом с кодом значит он реализован и используется

## Описание кодов состояния `"code"`
* 1xx - Информационные коды
    * 100 - Возвращает mac-аддрес компьютера (для Echo)             +
* 2xx - Успешные коды
    * 200 - Создана асинхронная задача                              +
    * 201 - Выполнена синхронная задача с результатом               +
    * 202 - Выполнена синхронная задача без результатом
* 3xx - Коды ошибки клиента
    * 300 - Испорченный запрос (Не правильная структура запроса)
    * 301 - Не верный метод                                         +
    * 302 - Нет необходимого заголовка
    * 303 - Вызываемая удаленная функция не существует              +
    * 304 - Не верные аргументы для вызываемой удаленной функции
    * 305 - Не верный id запрашиваемой задачи
    * 306 - Другая версия arpcp протокола
* 4xx - Коды ошибки сервера
    * 400 - 



## Async Task

request

```json
{
    "purpose_word": "ATASK",
    "p_version": "ARPCP/1.0",  
    "remote-func": "<remote-func>",
    "remote-func-arg" : {
        "0": "<arg1>", 
        "1": "<arg2>",
        ...
        "<i>": "<arg<i>>"
        }
}
```

response

```
code <code>
task-id <task_id>
```

## SIGNAL

request

```json
{
    "purpose_word": "SIGNAL",
    "p_version": "ARPCP/1.0",  
    "task-id": "<task-id>",
    "task-status": "<task-status>",
}
```

response

```
code <code>
???
```

## GET

request

```json
{
    "purpose_word": "GET",
    "p_version": "ARPCP/<p_version>",  
    "task-id": "<task-id>",
}
```

response

```
code <code>
result <result>
```


## Sync Task

request

```json
{
    "purpose_word": "TASK",
    "p_version": "ARPCP/<p_version>",  
    "remote-func": "<remote-func>",
    "remote-func-arg" : {
        "0": "<arg1>", 
        "1": "<arg2>",
        ...
        "<i>": "<arg<i>>"
        }
}
```

response

```
code <code>
result <result>
```

## Sync Task

request

```json
{
    "purpose_word": "ECHO",
    "p_version": "ARPCP/<p_version>",  
    ...
    maybe mac_addr
}
```

response

```
code <code>
pong
mac_addr ???
```