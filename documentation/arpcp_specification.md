## arpcp методы (заголовки пакетов):
* async task ->
* result <-

* signal ->

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
* возвращение результатов выполнения контроллеру
* выключение

---

## Структура aprcp сообщения:

Структура протокола сделана по аналогии с json

`Ключевое слово (purpose_word)` - (ATASK, TASK, SIGNAL, ID, RESULT)

`Версия arpcp (p_version)` - (1.0)

```json
Все существующие заголовки

request
{
    "method": "<purpose_word>",
    "version": "<p_version>",  
    "task_id": "<task_id>",
    "task_status": "<task_status>",
    "remote_procedure": "<remote-func>",
    "remote_procedure_args" : ["<arg1>","<arg2>",...],
}

response
{
    "code": "<code>",
    "description": "<result>",
    "data": "<data>"
}
```
Плюс (+) рядом с кодом значит он реализован и используется

## Описание кодов состояния `"code"`
* 1xx - Успешные коды
    * 100 - Создана асинхронная задача                              +
* 2xx - Коды ошибки клиента
    * 200 - Испорченный запрос (Не правильная структура запроса)
    * 201 - Не верный метод                                         +
    * 202 - Нет необходимого заголовка                              +
    * 203 - Вызываемая удаленная функция не существует              +
    * 204 - Не верные аргументы для вызываемой удаленной функции    
    * 205 - Не верный id запрашиваемой задачи
    * 206 - Другая версия arpcp протокола
* 3xx - Коды ошибки сервера
    * 300 - Внутреняя ошибка сервера
* 4xx - Коды ошибки сигнала
    * 400 - Ошибка при выполнении удаленной процедуры



## Async Task

request

```json
{
    "method": "ATASK",
    "version": "<p_version>",  
    "task_id": "<task_id>",
    "remote_procedure": "<remote-func>",
    "remote_procedure_args" : ["<arg1>","<arg2>",...],
}
```

response

```json
{
    "code": "<code>",
    "data": "<data>",
    "description": "<result>",
}
```

## Result
 
request

```json
{
    
    "method": "RESULT",
    "version": "<p_version>",  
    "task_id": "<task_id>",
    "task_result": "<task_result>",
    "task_status": "<task_status>",
}
```
### Atask_status

```python
'created' - задача создана.
'sended_to_agent' - задача отправлена агенту.
'successfully_registered' - агент принял задачу.
'unregistered' - агент не принял задачу.
'executing' - выполнение задачи на агенте.
'done' - задача выполнена #В случае метод ничего не возвращает, то result = None
'execution_error' - исключение во время выполнения
'unknown_error' - неизвестная ошибка (агент не отвечает и т.д.)
```

response

```json
{
    "code": "<code>",
    "data": "<data>", //None
    "description": "<result>",
}
```

## Signal

request

```json
{
    "method": "SIGNAL",
    "version": "ARPCP/<p_version>",
    "atask_id": "<task-id>",
}
```

response

```json
{
    "code": "<code>",
    "data": "<data>", //результат процедуры
    "description": "<result>",
}
```


## Sync Task

request

```json
{
    "method": "TASK",
    "version": "<p_version>",  
    "remote_procedure": "<remote-func>",
    "remote_procedure_args" : ["<arg1>","<arg2>",...],
    "task_id": "<task_id>", //не обязательно
}
```

response

```json
{
    "code": "<code>",
    "data": "<data>", //результат задачи
    "description": "<result>",
}
```

## Id

request

```json
{
    "method": "id",
    "version": "<p_version>",
    "controller_info": "<controller_info>", //controller_mac, controller_ip
}
```

response

```json
{
    "code": "<code>",
    "data": "<data>", //agent_mac, agent_ip
    "description": "<result>",
}
```

## Procedures

request

```json
{
    "method": "procedures",
    "version": "<p_version>",  
}
```

response

```json
{
    "code": "<code>",
    "data": "<data>", //список процедур
    "description": "<result>",
}
```