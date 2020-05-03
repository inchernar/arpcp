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

`Ключевое слово (purpose_word)` - (ATASK, TASK, GET, ID, SIGNAL)

`Версия arpcp (p_version)` - (1.0)

```json
request
{
    "method": "<purpose_word>",
    "version": "<p_version>",  
    "remote_procedure": "<remote-func>",
    "atask_id": "<atask_id>",
    "atask_status": "<atask_status>",
    "remote_procedure_args" : ["<arg1>","<arg2>",...]
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
    "remote_procedure": "<remote-func>",
    "remote_procedure_args" : ["<arg1>","<arg2>",...]
}
```

response

```json
{
    "code": "<code>",
    "description": "<result>",
    "data": "<data>"
}
```

## SIGNAL

request

```json
{
    
    "method": "SIGNAL",
    "version": "<p_version>",  
    "atask_id": "<atask_id>",
    "atask_status": "<atask_status>",
}
```
### atask_status

```python
'accepted' - Задача принята и скоро должна начнать выполняться
'interrupted' - Выполнение задачи было прервано
'done' - Задача выполнена #В случае метод ничего не возвращает, то result = None
'client_error' - Неправильные данные от клиента #Равносильно terminate
'terminate' - Всю информацию об этой задаче следует удалить из хранилища
```

response

```json
{
    "code": "<code>",
    "description": "<result>",
    "data": "<data>"
}
```

## GET

request

```json
{
    "method": "GET",
    "version": "ARPCP/<p_version>",  
    "atask_id": "<task-id>",
}
```

response

```json
{
    "code": "<code>",
    "description": "<result>",
    "data": "<data>"
}
```


## Sync Task

request

```json
{
    "method": "TASK",
    "version": "<p_version>",  
    "remote_procedure": "<remote-func>",
    "remote_procedure_args" : ["<arg1>","<arg2>",...]
}
```

response

```json
{
    "code": "<code>",
    "description": "<result>",
    "data": "<data>"
}
```

## Id

request

```json
{
    "method": "id",
    "version": "<p_version>",  
}
```

response

```json
{
    "code": "<code>",
    "description": "<result>",
    "data": "<data>"
}
```