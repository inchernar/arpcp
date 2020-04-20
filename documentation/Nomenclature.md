- `arpcp (asynchronous remote procedure call protocol)` - текстовый протокол прикладного уровня, реализующий технологию асинхронного вызова удалённой процедуры (асинхронный RPC).

- `arpcp cluster` - централизованная группа компьютеров, объединённых единой сетью, взаимодействие между которыми реализуется по протоколу ***arpcp***.

- `arpcp controller` - центральный управляющий компьютер в ***arpcp cluster***'е.

- `arpcp controller-app` - приложение, устанавливаемое на ***arpcp controller***.

- `arpcp agent` - управляемый компьютер в ***arpcp cluster***'е.

- `arpcp agent-app` - приложение, устанавливаемое на ***arpcp agent***.

- `arpcp client` - приложение, которое реализует клиентскую сторону протокола ***arpcp***.

- `arpcp controller-server` - приложение, которое реализует серверную сторону протокола ***arpcp*** на ***arpcp controller***'е.

- `arpcp agent-server` - приложение, которое реализует серверную сторону протокола ***arpcp*** на ***arpcp agent***'е.

- `echo-request` - широковещательный запрос в локальной сети, который отправляет ***arpcp controller***, нацеленный на обнаружение действующих ***arpcp agent***'ов.

- `echo-response` - ответ на запрос ***echo-request*** от ***arpcp agent***'а, содержащий информацию об ***arpcp agent***'е.

- `arpcp controller-storage` - хранилище данных, необходимое для совместного функционирования компонентов ***arpcp controller***'а.

- `arpcp agent-storage` - хранилище данных, необходимое для совместного функционирования компонентов ***arpcp agent***'а.

- `arpcp controller-daemon` - приложение, выполняющее задачи в фоновом режиме на ***arpcp controller***'е.

- `arpcp agent-daemon` - приложение, выполняющее задачи в фоновом режиме на ***arpcp agent***'е.
