## Работа с репозиторием

#### Клонирование

```
git clone https://github.com/julbarys/dissertation.git
```

#### Коммит в удалённую ветку

```bash
git checkout <user>-dev
git pull
git add .
git commit -am "<commit text>"
git push -u origin <user>-dev # только при первом запуске
git push # при последующих запусках
```

#### Слияние веток (из `master`)

```
git checkout <user>-dev
git merge master
```

#### Pull request

После отправки изменений на сервер в свою ветку сделать `Pull request` в ветку `master`. Далее нужно принять этот `Pull request`. Сделать это можно потому, что мы оба являемся контрибьюторами этого репозитория.
