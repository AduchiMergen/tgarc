# tgarc
A command line tool for archiving Telegram JSON
#### Установка
    pipx install git+https://github.com/AduchiMergen/tgarc.git
  или 
  
    pip install git+https://github.com/AduchiMergen/tgarc.git

#### Настройка

1. Создать приложение на https://my.telegram.org/apps
2. Выполнить tgarc configure
3. Ввести App api_id и App api_hash
4. Если все верно ввести номер телефона зарегистрированного пользователя и код подтверждения

#### Команды:
    configure  Настроить ключи подключения, логин и пароль
    logout     Завершение сессии текущего пользователя
    save       сохранение группы чатов и каналов по их имени или по ссылкам

##### Опции save:
tgarc save [OPTIONS] [SRC]...

    --video / --no-video        не выгружать видео медиа-файлы
    --pictures / --no-pictures  не выгружать фотографии
    --files / --no-files        не выгружать остальные типы файлов (audio, document, sticker, animation, voice, video_note)
    --max-size INTEGER          максимальный размер одного выгружаемого файла в МБ
    --update                    обновить ранее выгруженные данные
    --private                   выгрузить приватный чат/канал
    --format [csv|json]         формат сохранения сообщений CSV или JSON(l) формат.  [default: json]
                                * CSV не имплементировано
    --input FILENAME            файл со списком названий чатов и каналов или ссылок на них если у них нет названия и они приватные.
                                идентификатор, юзернейм или ссылка вида t.me/joinchat/
    -o, --output TEXT           путь для сохранения файлов и данных, если не задан то создается папка tgarc-<датазапуска>
