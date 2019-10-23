## Структура репозитория

```plain
dissertation/
├───README.md
├───TODO.md
├───code/
└───thesis/
```

- `code` - директория с программной частью проекта;
- `thesis` - директория с документальной частью проекта;
- `README.md` - этот файл;
- `TODO.md` - список задач;

## Работа с репозиторием

#### Клонирование

```bash
git clone https://github.com/julbarys/dissertation.git
```

#### Коммит в `origin`/`<user>-dev`

```bash
git checkout <user>-dev
git pull
git add .
git commit -am "<commit text>"
git push -u origin <user>-dev # только при первом запуске
git push # при последующих запусках
```

#### Pull request из `origin`/`<user>-dev` в `origin`/`master`

После отправки изменений на сервер в свою ветку сделать `Pull request` в ветку `master`. Далее нужно принять этот `Pull request`. Сделать это можно потому, что мы оба являемся контрибьюторами этого репозитория.

#### Слияние из `origin`/`master`

```bash
git checkout master
git pull
git checkout <user>-dev
git merge master
```
