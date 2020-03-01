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

## Структура aprcp документа:

```
Ключевое слово | Версия arpcp  
Заголовок : Значение  
Заголовок : Значение  
Заголовок : Значение    
...
```

`Ключевое слово (purpose_word)` - (ATASK, TASK, GET, ECHO, SIGNAL)

`Версия arpcp (p_version)` - (ARPCP/1.0)

`Заголовок : Значение` - (  
    remote-func <func_name>
    remote-func-arg <index> <arg>
    task-id <task_id>
    task-status <task_status>
    ...  
)


## Async Task

request

```
ATASK arpcp/1.0
remote-func <func_name>
remote-func-arg 0 <arg>
remote-func-arg 1 <arg>
remote-func-arg 2 <arg>
```

response

```
code <code>
task-id <task_id>
```

## SIGNAL

request

```
SIGNAL arpcp/1.0
task-id <task_id>
task-status <task_status>
```

response

```
code <code>
???
```

## GET

request

```
ATASK arpcp/1.0
task-id <task_id>
```

response

```
code <code>
result <result>
```


## Sync Task

request

```
ATASK arpcp/1.0
remote_func <func_name>
remote_func_arg 0 <arg>
remote_func_arg 1 <arg>
remote_func_arg 2 <arg>
```

response

```
code <code>
result <result>
```

## Sync Task

request

```
ECHO arpcp/1.0
ping
mac_addr ???
```

response

```
code <code>
pong
mac_addr ???
```