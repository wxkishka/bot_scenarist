# Бот-сценарист

## Перед тем, как начать.
1. Копируем каталог bot_gpt к себе на сервер.
2. Активируем виртуальное окружение.
3. Устанавливаем программыне зависимости 
   из файла requirements.txt.
4. В файле config.py заполняем параментры настройки бота
   и параметры подключения к серверу GPT и модели GPT.
5. Запускаем бота из файла bot.py

## Начало работы с ботом.
      Бот работает в связке с сервером Yandex GPT и создан для того,
   чтобы писать сценарии кино, мультфильмам и играм совместно с тобой.
   Пишите история по-очереди с ботом, но помни, что количество токенов
   ограничено.
      Бот позволяет работать нескольким пользователям одновременно.
      Для того чтобы начать работу напиши в строке мессенджера
      Telegram команду "/start". Бот поприветстует тебя и задаст тебе
   ряд вопросов для того, чтобы начать твою историю. Тебе придётся 
   выбрать главного героя, жанр, и вселенную твоей истории. 
   Нажми "new_story", и нейросеть начнёт придумывать истрию. Каждые
   три предложения тебе будет предложено внести свой вклад в сценарий,
   пиши, и получай продолжение.
   Для того чтобы завершить, нажми кнопку "end."
   Для того, чтобы вывести на экран всю историю нажми кнопку, или введи
   команду "whole_story".
   Чтоби проверить сколько токенов ты израсходовал в последней сессии,
   нажми кнопку или введи команду "all_tokens".
   
## Сервисные функции бота.
   Введите команду "/debug", бот отправить в мессенджер файл
 с информацией об ошибках во время запуска и работы.
   